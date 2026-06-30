"""Tests for Order MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import OrderResult
from dolibarr_mcp.tools.orders import register_order_tools


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def order_tools():
    """Register order tools so the inner functions are accessible."""
    mcp = AsyncMock()
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_order_tools(mcp)
    return registered


ORDER_API_RESPONSE = {
    "id": 55,
    "ref": "CO2401-001",
    "socid": 10,
    "date_commande": 1700000000,
    "total_ht": 1000.0,
    "total_ttc": 1200.0,
    "statut": 0,
    "lines": [
        {
            "id": 101,
            "desc": "Wechselrichter",
            "subprice": "500.00",
            "qty": "2",
            "tva_tx": "20",
            "product_type": 0,
            "fk_product": 42,
        },
        {
            "id": 102,
            "desc": "Montage",
            "subprice": "80.00",
            "qty": "1",
            "tva_tx": "20",
            "product_type": 1,
        },
    ],
}


# ---------------------------------------------------------------------------
# update_order
# ---------------------------------------------------------------------------

class TestUpdateOrder:
    """Tests for the update_order MCP tool."""

    @pytest.mark.asyncio
    async def test_update_order_basic(self, mock_client, order_tools):
        """update_order sends payload and returns re-read result."""
        mock_client.update_order.return_value = None
        mock_client.get_order_by_id.return_value = ORDER_API_RESPONSE

        result = await order_tools["update_order"](
            order_id=55, date="2024-12-01",
            delivery_date=None, project_id=None, payment_mode_id=None,
        )

        mock_client.update_order.assert_awaited_once_with(55, {
            "date_commande": "2024-12-01",
        })
        assert isinstance(result, OrderResult)
        assert result.id == 55

    @pytest.mark.asyncio
    async def test_update_order_multiple_fields(self, mock_client, order_tools):
        """update_order sends all provided fields."""
        mock_client.update_order.return_value = None
        mock_client.get_order_by_id.return_value = ORDER_API_RESPONSE

        await order_tools["update_order"](
            order_id=55, date="2024-12-01",
            delivery_date="2024-12-15", project_id=300,
            payment_mode_id=2,
        )

        mock_client.update_order.assert_awaited_once_with(55, {
            "date_commande": "2024-12-01",
            "date_livraison": "2024-12-15",
            "fk_project": 300,
            "mode_reglement_id": 2,
        })

    @pytest.mark.asyncio
    async def test_update_order_empty_raises(self, mock_client, order_tools):
        """update_order with no fields raises ValueError."""
        with pytest.raises(ValueError, match="At least one field"):
            await order_tools["update_order"](
                order_id=55, date=None, delivery_date=None,
                project_id=None, payment_mode_id=None,
            )

        mock_client.update_order.assert_not_awaited()


# ---------------------------------------------------------------------------
# update_order_line
# ---------------------------------------------------------------------------

class TestUpdateOrderLine:
    """Tests for the update_order_line MCP tool."""

    @pytest.mark.asyncio
    async def test_update_order_line_partial(self, mock_client, order_tools):
        """update_order_line preserves existing fields when updating partially."""
        mock_client.get_order_by_id.return_value = ORDER_API_RESPONSE
        mock_client.update_order_line.return_value = None

        result = await order_tools["update_order_line"](
            order_id=55, line_id=101,
            description=None, unit_price=Decimal("550.00"),
            quantity=None, vat_rate=None,
        )

        payload = mock_client.update_order_line.call_args[0][2]
        assert payload["subprice"] == "550.00"
        assert payload["desc"] == "Wechselrichter"
        assert payload["qty"] == "2"
        assert payload["tva_tx"] == "20"
        assert payload["fk_product"] == 42
        assert result == 101

    @pytest.mark.asyncio
    async def test_update_order_line_all_fields(self, mock_client, order_tools):
        """update_order_line overrides all fields when all are provided."""
        mock_client.get_order_by_id.return_value = ORDER_API_RESPONSE
        mock_client.update_order_line.return_value = None

        await order_tools["update_order_line"](
            order_id=55, line_id=102,
            description="Montage vor Ort",
            unit_price=Decimal("95.00"),
            quantity=Decimal("3"),
            vat_rate=Decimal("20"),
        )

        payload = mock_client.update_order_line.call_args[0][2]
        assert payload["desc"] == "Montage vor Ort"
        assert payload["subprice"] == "95.00"
        assert payload["qty"] == "3"
        assert payload["tva_tx"] == "20"

    @pytest.mark.asyncio
    async def test_update_order_line_without_product(self, mock_client, order_tools):
        """Lines without fk_product don't include it in the payload."""
        mock_client.get_order_by_id.return_value = ORDER_API_RESPONSE
        mock_client.update_order_line.return_value = None

        await order_tools["update_order_line"](
            order_id=55, line_id=102,
            description="Updated", unit_price=None,
            quantity=None, vat_rate=None,
        )

        payload = mock_client.update_order_line.call_args[0][2]
        assert "fk_product" not in payload

    @pytest.mark.asyncio
    async def test_update_order_line_not_found(self, mock_client, order_tools):
        """update_order_line raises ValueError for unknown line_id."""
        mock_client.get_order_by_id.return_value = ORDER_API_RESPONSE

        with pytest.raises(ValueError, match="Line 999 not found"):
            await order_tools["update_order_line"](
                order_id=55, line_id=999,
                description="Ghost", unit_price=None,
                quantity=None, vat_rate=None,
            )

        mock_client.update_order_line.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_order_line_empty_raises(self, mock_client, order_tools):
        """update_order_line with no fields raises ValueError."""
        with pytest.raises(ValueError, match="At least one field"):
            await order_tools["update_order_line"](
                order_id=55, line_id=101,
                description=None, unit_price=None,
                quantity=None, vat_rate=None,
            )

        mock_client.get_order_by_id.assert_not_awaited()


# ---------------------------------------------------------------------------
# delete_order_line
# ---------------------------------------------------------------------------

class TestDeleteOrderLine:
    """Tests for the delete_order_line MCP tool."""

    @pytest.mark.asyncio
    async def test_delete_order_line(self, mock_client, order_tools):
        """delete_order_line calls client and returns line_id."""
        mock_client.delete_order_line.return_value = None

        result = await order_tools["delete_order_line"](order_id=55, line_id=101)

        mock_client.delete_order_line.assert_awaited_once_with(55, 101)
        assert result == 101


# ---------------------------------------------------------------------------
# delete_order (existing, kept for completeness)
# ---------------------------------------------------------------------------

class TestDeleteOrder:
    """Tests for the delete_order MCP tool."""

    @pytest.mark.asyncio
    async def test_delete_order(self, mock_client, order_tools):
        """delete_order calls client and returns confirmation."""
        mock_client.delete_order.return_value = None

        result = await order_tools["delete_order"](order_id=55)

        mock_client.delete_order.assert_awaited_once_with(55)
        assert result == {"status": "deleted", "order_id": 55}
