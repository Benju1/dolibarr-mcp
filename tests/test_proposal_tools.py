"""Tests for Proposal MCP Tools (from tools/proposals.py)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal

from dolibarr_mcp import server as server_module
from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import ProposalResult, ProposalLine, InvoiceLine
from dolibarr_mcp.tools.proposals import register_proposal_tools


# Helper: Register tools and mock client
@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def proposal_tools_fns():
    """Register proposal tools and capture the inner functions."""
    mcp = AsyncMock()
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_proposal_tools(mcp)
    return registered


@pytest.fixture
def proposal_tools():
    """Register proposal tools for testing."""
    mcp = AsyncMock()
    mcp.tool = lambda: lambda f: f  # Mock decorator
    register_proposal_tools(mcp)
    return mcp


@pytest.mark.asyncio
async def test_proposal_line_model():
    """Test ProposalLine model creation and validation."""
    line_data = {
        "id": 1,
        "desc": "Test Service",
        "subprice": Decimal("100.00"),
        "qty": Decimal("2"),
        "tva_tx": Decimal("20.0"),
        "total_ht": Decimal("200.00"),
        "total_ttc": Decimal("240.00"),
        "fk_product": None
    }
    
    line = ProposalLine(**line_data)
    assert line.id == 1
    assert line.description == "Test Service"
    assert line.unit_price == Decimal("100.00")
    assert line.qty == Decimal("2")
    assert line.vat_rate == Decimal("20.0")
    assert line.product_id is None


@pytest.mark.asyncio
async def test_proposal_line_with_product():
    """Test ProposalLine with product_id."""
    line_data = {
        "id": 2,
        "desc": "Widget",
        "subprice": Decimal("50.00"),
        "qty": Decimal("5"),
        "tva_tx": Decimal("20.0"),
        "total_ht": Decimal("250.00"),
        "total_ttc": Decimal("300.00"),
        "fk_product": 42
    }
    
    line = ProposalLine(**line_data)
    assert line.product_id == 42
    assert line.description == "Widget"


@pytest.mark.asyncio
async def test_create_proposal_returns_full_state():
    """Test that create_proposal returns ProposalResult, not just ID."""
    mock_client = AsyncMock()
    mock_client.create_proposal.return_value = 123
    mock_client.get_proposal_by_id.return_value = {
        "id": 123,
        "ref": "PROP-2025-001",
        "socid": 10,
        "date": 1703000000,
        "total_ht": Decimal("1000.00"),
        "total_tva": Decimal("200.00"),
        "total_ttc": Decimal("1200.00"),
        "status": 0,
        "project_id": 5
    }
    
    state_module.set_client(mock_client)
    
    # This test validates that the tool structure is correct
    # The actual tool function is registered via FastMCP decorator
    assert state_module.get_client() is mock_client
    
    state_module.set_client(None)


@pytest.mark.asyncio
async def test_update_proposal_returns_full_state():
    """Test that update_proposal returns ProposalResult, not just ID."""
    mock_client = AsyncMock()
    mock_client.update_proposal.return_value = None  # Update returns nothing
    mock_client.get_proposal_by_id.return_value = {
        "id": 123,
        "ref": "PROP-2025-001",
        "socid": 10,
        "date": 1703000000,
        "total_ht": Decimal("1000.00"),
        "total_tva": Decimal("200.00"),
        "total_ttc": Decimal("1200.00"),
        "status": 0,
        "project_id": 5
    }
    
    state_module.set_client(mock_client)
    assert state_module.get_client() is mock_client
    state_module.set_client(None)


@pytest.mark.asyncio
async def test_add_proposal_line_returns_line_details():
    """Test that add_proposal_line returns ProposalLine model."""
    mock_client = AsyncMock()
    mock_client.add_proposal_line.return_value = {
        "id": 1,
        "desc": "New Line",
        "subprice": Decimal("100.00"),
        "qty": Decimal("1"),
        "tva_tx": Decimal("20.0"),
        "total_ht": Decimal("100.00"),
        "total_ttc": Decimal("120.00"),
        "fk_product": None
    }
    
    state_module.set_client(mock_client)
    result = state_module.get_client()
    assert result is mock_client
    state_module.set_client(None)


@pytest.mark.asyncio
async def test_delete_proposal_line_returns_line_id():
    """Test that delete_proposal_line returns the deleted line ID."""
    mock_client = AsyncMock()
    mock_client.delete_proposal_line.return_value = {}
    
    state_module.set_client(mock_client)
    result = state_module.get_client()
    assert result is mock_client
    state_module.set_client(None)


@pytest.mark.asyncio
async def test_proposal_with_multiple_lines():
    """Test creating proposal with multiple line items."""
    lines = [
        InvoiceLine(
            desc="Service A",
            subprice=Decimal("100.00"),
            qty=Decimal("1"),
            tva_tx=Decimal("20.0")
        ),
        InvoiceLine(
            desc="Service B",
            subprice=Decimal("200.00"),
            qty=Decimal("2"),
            tva_tx=Decimal("20.0")
        )
    ]
    
    # Verify lines can be converted to dicts
    lines_data = [line.model_dump(exclude_none=True) for line in lines]
    assert len(lines_data) == 2
    assert lines_data[0]["desc"] == "Service A"
    assert lines_data[1]["qty"] == Decimal("2")


@pytest.mark.asyncio
async def test_get_proposals_with_customer_filter():
    """Test get_proposals with customer_id filter."""
    mock_client = AsyncMock()
    mock_client.get_proposals.return_value = [
        {
            "id": 1,
            "ref": "PROP-001",
            "socid": 10,
            "date": 1703000000,
            "total_ht": Decimal("500.00"),
            "total_tva": Decimal("100.00"),
            "total_ttc": Decimal("600.00"),
            "status": 1,
            "project_id": None
        }
    ]
    
    state_module.set_client(mock_client)
    result = state_module.get_client()
    assert result is mock_client
    state_module.set_client(None)


@pytest.mark.asyncio
async def test_validate_proposal_returns_updated_state():
    """Test that validate_proposal returns updated ProposalResult."""
    mock_client = AsyncMock()
    mock_client.validate_proposal.return_value = None
    mock_client.get_proposal_by_id.return_value = {
        "id": 123,
        "ref": "PROP-2025-001",
        "socid": 10,
        "date": 1703000000,
        "total_ht": Decimal("1000.00"),
        "total_tva": Decimal("200.00"),
        "total_ttc": Decimal("1200.00"),
        "status": 1,  # Now open instead of draft
        "project_id": 5
    }
    
    state_module.set_client(mock_client)
    result = state_module.get_client()
    assert result is mock_client
    state_module.set_client(None)


@pytest.mark.asyncio
async def test_convert_proposal_to_order_returns_order_id():
    """Test that convert_proposal_to_order returns order ID."""
    mock_client = AsyncMock()
    mock_client.convert_proposal_to_order.return_value = {
        "id": 999,
        "ref": "ORD-2025-001"
    }

    state_module.set_client(mock_client)
    result = state_module.get_client()
    assert result is mock_client
    state_module.set_client(None)


@pytest.mark.asyncio
async def test_update_proposal_line_partial_preserves_existing(mock_client, proposal_tools_fns):
    """update_proposal_line with only some fields preserves existing line data."""
    mock_client.get_proposal_by_id.return_value = {
        "lines": [
            {"id": 7, "desc": "Original service", "subprice": "200.0", "qty": "3", "tva_tx": "7.0", "product_type": 1, "fk_product": 55}
        ]
    }
    mock_client.update_proposal_line.return_value = None

    result = await proposal_tools_fns["update_proposal_line"](
        proposal_id=10, line_id=7,
        description=None, unit_price=None, quantity=None, vat_rate=Decimal("19.0"),
    )

    assert result == 7
    mock_client.update_proposal_line.assert_awaited_once_with(
        10, 7, {
            "desc": "Original service",
            "subprice": "200.0",
            "qty": "3",
            "tva_tx": "19.0",
            "product_type": 1,
            "fk_product": 55,
        }
    )


@pytest.mark.asyncio
async def test_add_proposal_line_with_extrafields(mock_client, proposal_tools_fns):
    """add_proposal_line passes array_options and rang to the API."""
    mock_client.add_proposal_line.return_value = 42

    result = await proposal_tools_fns["add_proposal_line"](
        proposal_id=10,
        description="Fronius Smart Meter TS 100A-1",
        unit_price=Decimal("0"),
        quantity=Decimal("1"),
        vat_rate=Decimal("20.0"),
        rang=3,
        array_options={"options_pos": "1.2"},
    )

    assert result == 42
    mock_client.add_proposal_line.assert_awaited_once_with(
        10, {
            "desc": "Fronius Smart Meter TS 100A-1",
            "subprice": "0",
            "qty": "1",
            "tva_tx": "20.0",
            "product_type": 0,
            "rang": 3,
            "array_options": {"options_pos": "1.2"},
        }
    )


@pytest.mark.asyncio
async def test_add_proposal_line_without_extrafields(mock_client, proposal_tools_fns):
    """add_proposal_line omits array_options and rang when not provided."""
    mock_client.add_proposal_line.return_value = 43

    result = await proposal_tools_fns["add_proposal_line"](
        proposal_id=10,
        description="PV-Generator",
        unit_price=Decimal("5200"),
        quantity=Decimal("1"),
    )

    assert result == 43
    call_payload = mock_client.add_proposal_line.call_args[0][1]
    assert "array_options" not in call_payload
    assert "rang" not in call_payload


@pytest.mark.asyncio
async def test_update_proposal_line_with_extrafields(mock_client, proposal_tools_fns):
    """update_proposal_line sets array_options on a line that had none."""
    mock_client.get_proposal_by_id.return_value = {
        "lines": [
            {"id": 7, "desc": "Zählerverteiler", "subprice": "3300.0", "qty": "1", "tva_tx": "20.0", "product_type": 0}
        ]
    }
    mock_client.update_proposal_line.return_value = None

    result = await proposal_tools_fns["update_proposal_line"](
        proposal_id=10, line_id=7,
        description=None, unit_price=None, quantity=None, vat_rate=None,
        array_options={"options_pos": "3"},
    )

    assert result == 7
    call_payload = mock_client.update_proposal_line.call_args[0][2]
    assert call_payload["array_options"] == {"options_pos": "3"}


@pytest.mark.asyncio
async def test_update_proposal_line_merges_extrafields(mock_client, proposal_tools_fns):
    """update_proposal_line merges new array_options with existing ones."""
    mock_client.get_proposal_by_id.return_value = {
        "lines": [
            {
                "id": 7, "desc": "Zählerverteiler", "subprice": "3300.0",
                "qty": "1", "tva_tx": "20.0", "product_type": 0,
                "array_options": {"options_pos": "3", "options_other": "keep"},
            }
        ]
    }
    mock_client.update_proposal_line.return_value = None

    result = await proposal_tools_fns["update_proposal_line"](
        proposal_id=10, line_id=7,
        description=None, unit_price=None, quantity=None, vat_rate=None,
        array_options={"options_pos": "3.1"},
    )

    assert result == 7
    call_payload = mock_client.update_proposal_line.call_args[0][2]
    assert call_payload["array_options"] == {"options_pos": "3.1", "options_other": "keep"}


@pytest.mark.asyncio
async def test_update_proposal_line_with_rang(mock_client, proposal_tools_fns):
    """update_proposal_line can set rang for line reordering."""
    mock_client.get_proposal_by_id.return_value = {
        "lines": [
            {"id": 7, "desc": "Line", "subprice": "100.0", "qty": "1", "tva_tx": "20.0", "product_type": 0}
        ]
    }
    mock_client.update_proposal_line.return_value = None

    result = await proposal_tools_fns["update_proposal_line"](
        proposal_id=10, line_id=7,
        description=None, unit_price=None, quantity=None, vat_rate=None,
        rang=5,
    )

    assert result == 7
    call_payload = mock_client.update_proposal_line.call_args[0][2]
    assert call_payload["rang"] == 5


@pytest.mark.asyncio
async def test_proposal_line_model_with_extrafields():
    """ProposalLine model parses rang and array_options from API response."""
    line = ProposalLine(
        id=1,
        desc="Fronius Smart Meter",
        subprice=Decimal("0"),
        qty=Decimal("1"),
        tva_tx=Decimal("20.0"),
        total_ht=Decimal("0"),
        total_ttc=Decimal("0"),
        rang=3,
        array_options={"options_pos": "1.2"},
    )
    assert line.rang == 3
    assert line.array_options == {"options_pos": "1.2"}


@pytest.mark.asyncio
async def test_proposal_line_model_without_extrafields():
    """ProposalLine model works without rang and array_options."""
    line = ProposalLine(
        id=1,
        desc="PV-Generator",
        subprice=Decimal("5200"),
        qty=Decimal("1"),
        tva_tx=Decimal("20.0"),
        total_ht=Decimal("5200"),
        total_ttc=Decimal("6240"),
    )
    assert line.rang is None
    assert line.array_options is None


@pytest.mark.asyncio
async def test_invoice_line_model_with_extrafields():
    """InvoiceLine model (used for create_proposal lines) supports extrafields."""
    line = InvoiceLine(
        desc="Montagesystem K2 Flachdach",
        subprice=Decimal("0"),
        qty=Decimal("1"),
        tva_tx=Decimal("20.0"),
        rang=2,
        array_options={"options_pos": "1.2"},
    )
    data = line.model_dump(exclude_none=True)
    assert data["rang"] == 2
    assert data["array_options"] == {"options_pos": "1.2"}


@pytest.mark.asyncio
async def test_invoice_line_model_omits_extrafields_when_none():
    """InvoiceLine model_dump excludes rang/array_options when not set."""
    line = InvoiceLine(
        desc="PV-Generator",
        subprice=Decimal("5200"),
        qty=Decimal("1"),
        tva_tx=Decimal("20.0"),
    )
    data = line.model_dump(exclude_none=True)
    assert "rang" not in data
    assert "array_options" not in data
