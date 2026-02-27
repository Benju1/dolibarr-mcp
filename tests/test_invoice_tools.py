"""Tests for Invoice MCP Tools (delete_invoice, update_invoice_line, delete_invoice_line)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
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
        },
    )


@pytest.mark.asyncio
async def test_update_invoice_line_partial_update(mock_client, invoice_tools):
    """update_invoice_line sends only the provided fields."""
    mock_client.update_invoice_line.return_value = None

    result = await invoice_tools["update_invoice_line"](
        invoice_id=10, line_id=7,
        description=None, unit_price=None, quantity=5.0, vat_rate=None,
    )

    assert result == 7
    mock_client.update_invoice_line.assert_awaited_once_with(
        10, 7, {"qty": "5.0"}
    )


@pytest.mark.asyncio
async def test_update_invoice_line_no_fields_raises(mock_client, invoice_tools):
    """update_invoice_line raises ValueError when no optional fields are given."""
    with pytest.raises(ValueError, match="At least one field"):
        await invoice_tools["update_invoice_line"](
            invoice_id=10, line_id=7,
            description=None, unit_price=None, quantity=None, vat_rate=None,
        )
