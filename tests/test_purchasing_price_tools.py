"""Tests for Purchasing Price MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import PurchasingPriceResult
from dolibarr_mcp.tools.purchasing_prices import register_purchasing_price_tools


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def pp_tools():
    """Register purchasing price tools so the inner functions are accessible."""
    mcp = AsyncMock()
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_purchasing_price_tools(mcp)
    return registered


PURCHASING_PRICE_API_RESPONSE = [
    {
        "id": 1,
        "fk_product": 42,
        "fk_soc": 10,
        "ref_fourn": "SUP-REF-001",
        "price": "25.50",
        "fourn_qty": "1",
        "tva_tx": "20.000",
        "remise_percent": "0",
        "multicurrency_code": "EUR",
        "multicurrency_unitprice": "25.50",
        "delivery_time_days": 5,
        "datec": "2025-01-15 10:00:00",
        "tms": "2025-06-01 08:30:00",
    },
    {
        "id": 2,
        "fk_product": 42,
        "fk_soc": 20,
        "ref_fourn": "OTHER-REF",
        "price": "22.00",
        "fourn_qty": "10",
        "tva_tx": "20.000",
        "remise_percent": "5.000",
        "multicurrency_code": None,
        "multicurrency_unitprice": None,
        "delivery_time_days": None,
        "datec": "2025-03-01 12:00:00",
        "tms": "2025-03-01 12:00:00",
    },
]


# --- get_product_purchasing_prices ---


@pytest.mark.asyncio
async def test_get_purchasing_prices_returns_list(mock_client, pp_tools):
    """Returns a list of PurchasingPriceResult for a product with multiple suppliers."""
    mock_client.get_product_purchasing_prices.return_value = PURCHASING_PRICE_API_RESPONSE

    result = await pp_tools["get_product_purchasing_prices"](product_id=42)

    mock_client.get_product_purchasing_prices.assert_awaited_once_with(42)
    assert len(result) == 2
    assert all(isinstance(r, PurchasingPriceResult) for r in result)
    assert result[0].fk_soc == 10
    assert result[1].fk_soc == 20


@pytest.mark.asyncio
async def test_get_purchasing_prices_empty(mock_client, pp_tools):
    """Returns an empty list when no supplier prices exist."""
    mock_client.get_product_purchasing_prices.return_value = []

    result = await pp_tools["get_product_purchasing_prices"](product_id=99)

    assert result == []


@pytest.mark.asyncio
async def test_get_purchasing_prices_fields_parsed(mock_client, pp_tools):
    """Verify individual fields are correctly parsed into the model."""
    mock_client.get_product_purchasing_prices.return_value = [PURCHASING_PRICE_API_RESPONSE[0]]

    result = await pp_tools["get_product_purchasing_prices"](product_id=42)

    entry = result[0]
    assert entry.id == 1
    assert entry.fk_product == 42
    assert entry.fk_soc == 10
    assert entry.ref_fourn == "SUP-REF-001"
    assert float(entry.price) == 25.50
    assert float(entry.quantity) == 1
    assert float(entry.tva_tx) == 20.0
    assert entry.multicurrency_code == "EUR"
    assert entry.delivery_time_days == 5


# --- add_product_purchasing_price ---


def _add_defaults(**overrides):
    """Build kwargs for add_product_purchasing_price with explicit defaults."""
    base = dict(
        product_id=42,
        supplier_id=10,
        price=25.50,
        quantity=1,
        supplier_ref=None,
        tva_tx=20.0,
        delivery_time_days=None,
        multicurrency_code=None,
        multicurrency_unitprice=None,
    )
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_add_purchasing_price_minimal(mock_client, pp_tools):
    """Minimal add: only required fields in payload."""
    mock_client.add_product_purchasing_price.return_value = 1

    result = await pp_tools["add_product_purchasing_price"](**_add_defaults())

    mock_client.add_product_purchasing_price.assert_awaited_once()
    product_id, payload = mock_client.add_product_purchasing_price.call_args[0]
    assert product_id == 42
    assert payload["fourn_id"] == 10
    assert payload["buyprice"] == 25.5
    assert payload["qty"] == 1
    assert payload["price_base_type"] == "HT"
    assert payload["availability"] == 0
    assert payload["tva_tx"] == 20.0
    assert payload["ref_fourn"] == ""
    assert "delivery_time_days" not in payload
    assert "multicurrency_code" not in payload
    assert result == 1


@pytest.mark.asyncio
async def test_add_purchasing_price_all_fields(mock_client, pp_tools):
    """All optional fields set — every field should appear in the payload."""
    mock_client.add_product_purchasing_price.return_value = 5

    result = await pp_tools["add_product_purchasing_price"](**_add_defaults(
        supplier_ref="SUP-X-100",
        delivery_time_days=7,
        multicurrency_code="USD",
        multicurrency_unitprice=28.00,
    ))

    _, payload = mock_client.add_product_purchasing_price.call_args[0]
    assert payload["ref_fourn"] == "SUP-X-100"
    assert payload["delivery_time_days"] == 7
    assert payload["multicurrency_code"] == "USD"
    assert payload["multicurrency_buyprice"] == 28.0
    assert result == 5


@pytest.mark.asyncio
async def test_add_purchasing_price_quantity_tier(mock_client, pp_tools):
    """Quantity tier: same supplier, different quantity = different price entry."""
    mock_client.add_product_purchasing_price.return_value = 6

    await pp_tools["add_product_purchasing_price"](**_add_defaults(
        quantity=100,
        price=18.00,
    ))

    _, payload = mock_client.add_product_purchasing_price.call_args[0]
    assert payload["qty"] == 100
    assert payload["buyprice"] == 1800.0


@pytest.mark.asyncio
async def test_add_purchasing_price_returns_id(mock_client, pp_tools):
    """add_product_purchasing_price returns the new entry ID."""
    mock_client.add_product_purchasing_price.return_value = 77

    result = await pp_tools["add_product_purchasing_price"](**_add_defaults())

    assert result == 77


# --- delete_product_purchasing_price ---


@pytest.mark.asyncio
async def test_delete_purchasing_price(mock_client, pp_tools):
    """delete calls client and returns confirmation dict."""
    mock_client.delete_product_purchasing_price.return_value = None

    result = await pp_tools["delete_product_purchasing_price"](product_id=42, price_id=1)

    mock_client.delete_product_purchasing_price.assert_awaited_once_with(42, 1)
    assert result == {"status": "deleted", "product_id": 42, "price_id": 1}


# --- Model tests ---


def test_purchasing_price_result_model():
    """PurchasingPriceResult parses all fields correctly."""
    data = {
        "id": 3,
        "fk_product": 42,
        "fk_soc": 15,
        "ref_fourn": "ABC-123",
        "price": "30.00",
        "fourn_qty": "5",
        "tva_tx": "10.000",
        "remise_percent": "2.500",
        "multicurrency_code": "USD",
        "multicurrency_unitprice": "33.00",
        "delivery_time_days": 3,
        "datec": "2025-06-01",
        "tms": "2025-06-15",
    }
    result = PurchasingPriceResult(**data)
    assert result.id == 3
    assert result.fk_product == 42
    assert result.fk_soc == 15
    assert result.ref_fourn == "ABC-123"
    assert float(result.price) == 30.0
    assert float(result.quantity) == 5
    assert float(result.tva_tx) == 10.0
    assert float(result.remise_percent) == 2.5
    assert result.multicurrency_code == "USD"
    assert result.delivery_time_days == 3


def test_purchasing_price_result_extra_fields_ignored():
    """Unknown API fields are silently ignored (extra='ignore')."""
    data = {
        "id": 1,
        "fk_product": 1,
        "fk_soc": 1,
        "some_unknown_field": "should be ignored",
    }
    result = PurchasingPriceResult(**data)
    assert result.id == 1
    assert not hasattr(result, "some_unknown_field")


# ---------------------------------------------------------------------------
# REST path: Dolibarr exposes {id}/purchase_prices (api_products.class.php),
# not purchasing_prices (404, RP-04 angebot-agent run PRJ000292).
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_client_uses_purchase_prices_path():
    from unittest.mock import MagicMock

    from dolibarr_mcp.dolibarr_client import DolibarrClient

    client = DolibarrClient(MagicMock())
    client.request = AsyncMock(return_value=[])

    await client.get_product_purchasing_prices(42)
    assert client.request.call_args.args[:2] == ("GET", "products/42/purchase_prices")

    client.request = AsyncMock(return_value=7)
    await client.add_product_purchasing_price(42, {"price": 1})
    assert client.request.call_args.args[:2] == ("POST", "products/42/purchase_prices")

    client.request = AsyncMock(return_value={})
    await client.delete_product_purchasing_price(42, 7)
    assert client.request.call_args.args[:2] == ("DELETE", "products/42/purchase_prices/7")


# ---------------------------------------------------------------------------
# Live response shape of GET products/{id}/purchase_prices (ProductFournisseur):
# fourn_* keys, id = product ID, dates as Unix timestamps. Values are synthetic.
# ---------------------------------------------------------------------------

LIVE_SHAPE_RESPONSE = [
    {
        "id": "42",
        "product_fourn_price_id": "901",
        "fourn_id": "7",
        "fourn_name": "Example Supplier GmbH",
        "fourn_ref": "EX-1",
        "fourn_price": "100.00000000",
        "fourn_unitprice": "100.00000000",
        "fourn_qty": "1",
        "fourn_tva_tx": "20.0000",
        "fourn_remise_percent": "0",
        "fourn_multicurrency_code": "",
        "fourn_multicurrency_unitprice": None,
        "fourn_date_creation": 1767225600,
        "fourn_date_modification": 1767225600,
        "fk_product": None,
        "delivery_time_days": None,
    }
]


@pytest.mark.asyncio
async def test_get_purchasing_prices_maps_live_response_shape(mock_client, pp_tools):
    mock_client.get_product_purchasing_prices.return_value = LIVE_SHAPE_RESPONSE

    result = await pp_tools["get_product_purchasing_prices"](product_id=42)

    assert len(result) == 1
    entry = result[0]
    assert entry.id == 901
    assert entry.fk_product == 42
    assert entry.fk_soc == 7
    assert entry.supplier_name == "Example Supplier GmbH"
    assert entry.ref_fourn == "EX-1"
    assert str(entry.price) == "100.00000000"
    assert entry.multicurrency_code is None
    assert entry.tms == "2026-01-01T00:00:00+00:00"
