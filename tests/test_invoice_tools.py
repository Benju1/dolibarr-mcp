"""Tests for Invoice MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import InvoiceLine
from dolibarr_mcp.tools.invoices import register_invoice_tools


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def invoice_tools():
    """Register invoice tools so the inner functions are accessible."""
    mcp = AsyncMock()
    # Capture registered functions
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_invoice_tools(mcp)
    return registered


@pytest.mark.asyncio
async def test_delete_invoice_calls_client(mock_client, invoice_tools):
    """delete_invoice calls client.delete_invoice and returns the invoice_id."""
    mock_client.delete_invoice.return_value = None

    result = await invoice_tools["delete_invoice"](invoice_id=42)

    assert result == 42
    mock_client.delete_invoice.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_delete_invoice_line_calls_client(mock_client, invoice_tools):
    """delete_invoice_line calls client.delete_invoice_line and returns the line_id."""
    mock_client.delete_invoice_line.return_value = None

    result = await invoice_tools["delete_invoice_line"](invoice_id=10, line_id=55)

    assert result == 55
    mock_client.delete_invoice_line.assert_awaited_once_with(10, 55)


@pytest.mark.asyncio
async def test_update_invoice_line_calls_client(mock_client, invoice_tools):
    """update_invoice_line maps fields correctly and calls client."""
    mock_client.get_invoice_by_id.return_value = {
        "lines": [{"id": 7, "desc": "Old desc", "subprice": "50.0", "qty": "1", "tva_tx": "7.0", "product_type": 0}]
    }
    mock_client.update_invoice_line.return_value = None

    result = await invoice_tools["update_invoice_line"](
        invoice_id=10,
        line_id=7,
        description="Updated desc",
        unit_price=99.50,
        quantity=3.0,
        vat_rate=19.0,
    )

    assert result == 7
    mock_client.update_invoice_line.assert_awaited_once_with(
        10,
        7,
        {
            "desc": "Updated desc",
            "subprice": "99.5",
            "qty": "3.0",
            "tva_tx": "19.0",
            "product_type": 0,
        },
    )


@pytest.mark.asyncio
async def test_update_invoice_line_partial_preserves_existing(mock_client, invoice_tools):
    """update_invoice_line with only some fields preserves existing line data."""
    mock_client.get_invoice_by_id.return_value = {
        "lines": [
            {"id": 7, "desc": "Original description", "subprice": "100.0", "qty": "2", "tva_tx": "7.0", "product_type": 1, "fk_product": 42}
        ]
    }
    mock_client.update_invoice_line.return_value = None

    result = await invoice_tools["update_invoice_line"](
        invoice_id=10, line_id=7,
        description=None, unit_price=None, quantity=None, vat_rate=19.0,
    )

    assert result == 7
    mock_client.update_invoice_line.assert_awaited_once_with(
        10, 7, {
            "desc": "Original description",
            "subprice": "100.0",
            "qty": "2",
            "tva_tx": "19.0",
            "product_type": 1,
            "fk_product": 42,
        }
    )


@pytest.mark.asyncio
async def test_update_invoice_line_no_fields_raises(mock_client, invoice_tools):
    """update_invoice_line raises ValueError when no optional fields are given."""
    with pytest.raises(ValueError, match="At least one field"):
        await invoice_tools["update_invoice_line"](
            invoice_id=10, line_id=7,
            description=None, unit_price=None, quantity=None, vat_rate=None,
        )


@pytest.mark.asyncio
async def test_create_invoice_without_lines(mock_client, invoice_tools):
    """create_invoice without lines creates header only, no add_invoice_line calls."""
    mock_client.create_invoice.return_value = 100

    result = await invoice_tools["create_invoice"](
        customer_id=1, date="2025-01-01", lines=None, cond_reglement_code=None
    )

    assert result == 100
    mock_client.create_invoice.assert_awaited_once()
    mock_client.add_invoice_line.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_invoice_with_lines(mock_client, invoice_tools):
    """create_invoice with lines creates header then adds each line."""
    mock_client.create_invoice.return_value = 200
    mock_client.add_invoice_line.return_value = 1

    lines = [
        InvoiceLine(desc="Line 1", subprice="10.00", qty="2", tva_tx="20.0"),
        InvoiceLine(desc="Line 2", subprice="5.00", qty="1", tva_tx="10.0"),
    ]

    result = await invoice_tools["create_invoice"](
        customer_id=1, date="2025-01-01", lines=lines, cond_reglement_code=None
    )

    assert result == 200
    mock_client.create_invoice.assert_awaited_once()
    assert mock_client.add_invoice_line.await_count == 2


@pytest.mark.asyncio
async def test_create_invoice_resolves_payment_terms(mock_client, invoice_tools):
    """create_invoice resolves cond_reglement_code to cond_reglement_id via dictionary."""
    mock_client.create_invoice.return_value = 300
    mock_client.get_payment_terms.return_value = [
        {"id": "1", "code": "RECEP"},
        {"id": "3", "code": "30D"},
    ]

    result = await invoice_tools["create_invoice"](
        customer_id=1, date="2025-01-01", lines=None, cond_reglement_code="30D"
    )

    assert result == 300
    payload = mock_client.create_invoice.await_args.args[0]
    assert payload["cond_reglement_id"] == 3


@pytest.mark.asyncio
async def test_create_invoice_unknown_payment_terms_raises(mock_client, invoice_tools):
    """create_invoice raises ValueError for an unknown cond_reglement_code."""
    mock_client.get_payment_terms.return_value = [{"id": "1", "code": "RECEP"}]

    with pytest.raises(ValueError, match="Unknown payment terms code"):
        await invoice_tools["create_invoice"](
            customer_id=1, date="2025-01-01", lines=None, cond_reglement_code="NOPE"
        )

    mock_client.create_invoice.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_invoice_resolves_payment_terms(mock_client, invoice_tools):
    """update_invoice resolves cond_reglement_code and forwards cond_reglement_id."""
    mock_client.update_invoice.return_value = 42
    mock_client.get_payment_terms.return_value = [
        {"id": "1", "code": "RECEP"},
        {"id": "3", "code": "30D"},
    ]

    result = await invoice_tools["update_invoice"](
        invoice_id=42, date=None, payment_mode_id=None,
        cond_reglement_code="30D", note_public=None, note_private=None
    )

    assert result == 42
    mock_client.update_invoice.assert_awaited_once_with(42, {"cond_reglement_id": 3})


@pytest.mark.asyncio
async def test_update_invoice_unknown_payment_terms_raises(mock_client, invoice_tools):
    """update_invoice raises ValueError for an unknown cond_reglement_code."""
    mock_client.get_payment_terms.return_value = [{"id": "1", "code": "RECEP"}]

    with pytest.raises(ValueError, match="Unknown payment terms code"):
        await invoice_tools["update_invoice"](
            invoice_id=42, cond_reglement_code="NOPE"
        )

    mock_client.update_invoice.assert_not_awaited()


@pytest.mark.asyncio
async def test_validate_invoice_returns_updated_state(mock_client, invoice_tools):
    """validate_invoice calls client and returns InvoiceResult."""
    mock_client.validate_invoice.return_value = None
    mock_client.get_invoice_by_id.return_value = {
        "id": 42, "ref": "FA2501-0001", "socid": 1,
        "total_ht": "100.0", "total_tva": "19.0", "total_ttc": "119.0",
        "statut": 1, "paye": 0, "status": 1, "date": 1700000000,
    }

    result = await invoice_tools["validate_invoice"](invoice_id=42)

    mock_client.validate_invoice.assert_awaited_once_with(42)
    mock_client.get_invoice_by_id.assert_awaited_once_with(42)
    assert result.id == 42
    assert result.status == 1


@pytest.mark.asyncio
async def test_set_invoice_to_draft_calls_client(mock_client, invoice_tools):
    """set_invoice_to_draft calls client and returns InvoiceResult."""
    mock_client.set_invoice_to_draft.return_value = None
    mock_client.get_invoice_by_id.return_value = {
        "id": 42, "ref": "FA2501-0001", "socid": 1,
        "total_ht": "100.0", "total_tva": "19.0", "total_ttc": "119.0",
        "statut": 0, "paye": 0, "status": 0, "date": 1700000000,
    }

    result = await invoice_tools["set_invoice_to_draft"](invoice_id=42)

    mock_client.set_invoice_to_draft.assert_awaited_once_with(42)
    mock_client.get_invoice_by_id.assert_awaited_once_with(42)
    assert result.id == 42
    assert result.status == 0
