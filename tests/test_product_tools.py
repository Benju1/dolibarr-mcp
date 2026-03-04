"""Tests for Product MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import ProductResult
from dolibarr_mcp.tools.products import register_product_tools


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def product_tools():
    """Register product tools so the inner functions are accessible."""
    mcp = AsyncMock()
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_product_tools(mcp)
    return registered


def _defaults(**overrides):
    """Build kwargs for create_product with explicit defaults (bypasses FieldInfo)."""
    base = dict(
        label="Default",
        ref=None,
        price=0.0,
        type=0,
        description=None,
        tva_tx=20.0,
        cost_price=None,
        barcode=None,
        barcode_type_code=None,
        status=None,
        status_buy=None,
        note_public=None,
        note_private=None,
    )
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_create_product_minimal(mock_client, product_tools):
    """Minimal create_product: only label, ref NOT in payload, price defaults to 0.0."""
    mock_client.create_product.return_value = 1

    result = await product_tools["create_product"](**_defaults(label="Test Product"))

    mock_client.create_product.assert_awaited_once()
    payload = mock_client.create_product.call_args[0][0]
    assert "ref" not in payload
    assert payload["price"] == "0.0"
    assert payload["label"] == "Test Product"
    assert result == 1


@pytest.mark.asyncio
async def test_create_product_with_ref(mock_client, product_tools):
    """When ref is provided, it should be in the payload."""
    mock_client.create_product.return_value = 2

    await product_tools["create_product"](**_defaults(label="With Ref", ref="PROD-001"))

    payload = mock_client.create_product.call_args[0][0]
    assert payload["ref"] == "PROD-001"


@pytest.mark.asyncio
async def test_create_product_all_fields(mock_client, product_tools):
    """All fields set — every field should appear in the payload."""
    mock_client.create_product.return_value = 3

    await product_tools["create_product"](**_defaults(
        label="Full Product",
        ref="FP-001",
        price=100.0,
        type=1,
        description="A full product",
        tva_tx=10.0,
        cost_price=50.0,
        barcode="1234567890123",
        barcode_type_code="EAN13",
        status=1,
        status_buy=1,
        note_public="Public info",
        note_private="Internal info",
    ))

    payload = mock_client.create_product.call_args[0][0]
    assert payload["label"] == "Full Product"
    assert payload["ref"] == "FP-001"
    assert payload["price"] == "100.0"
    assert payload["type"] == 1
    assert payload["description"] == "A full product"
    assert payload["tva_tx"] == "10.0"
    assert payload["cost_price"] == "50.0"
    assert payload["barcode"] == "1234567890123"
    assert payload["barcode_type_code"] == "EAN13"
    assert payload["status"] == 1
    assert payload["status_buy"] == 1
    assert payload["note_public"] == "Public info"
    assert payload["note_private"] == "Internal info"


@pytest.mark.asyncio
async def test_create_product_cost_price_and_status(mock_client, product_tools):
    """C-Artikel scenario: cost_price set, status=0 (not for sale), status_buy=1."""
    mock_client.create_product.return_value = 4

    await product_tools["create_product"](**_defaults(
        label="C-Artikel",
        cost_price=25.99,
        status=0,
        status_buy=1,
    ))

    payload = mock_client.create_product.call_args[0][0]
    assert payload["cost_price"] == "25.99"
    assert payload["status"] == 0
    assert payload["status_buy"] == 1
    assert "ref" not in payload


@pytest.mark.asyncio
async def test_create_product_barcode(mock_client, product_tools):
    """Barcode and barcode_type_code appear in the payload."""
    mock_client.create_product.return_value = 5

    await product_tools["create_product"](**_defaults(
        label="Barcoded",
        barcode="9876543210",
        barcode_type_code="UPC",
    ))

    payload = mock_client.create_product.call_args[0][0]
    assert payload["barcode"] == "9876543210"
    assert payload["barcode_type_code"] == "UPC"


@pytest.mark.asyncio
async def test_create_product_returns_id(mock_client, product_tools):
    """create_product returns the new product ID from the client."""
    mock_client.create_product.return_value = 42

    result = await product_tools["create_product"](**_defaults(label="Return ID Test"))

    assert result == 42


def test_product_result_model_new_fields():
    """ProductResult parses all new fields correctly."""
    data = {
        "id": 1,
        "ref": "TEST-001",
        "label": "Test",
        "type": "0",
        "price": "100.00",
        "price_ttc": "120.00",
        "tva_tx": "20.000",
        "stock_reel": 10.0,
        "cost_price": "50.00",
        "barcode": "1234567890123",
        "barcode_type_code": "EAN13",
        "status": 1,
        "status_buy": 1,
        "note_public": "Public",
        "note_private": "Private",
    }
    result = ProductResult(**data)
    assert result.cost_price == 50
    assert result.barcode == "1234567890123"
    assert result.barcode_type_code == "EAN13"
    assert result.status == 1
    assert result.status_buy == 1
    assert result.note_public == "Public"
    assert result.note_private == "Private"
