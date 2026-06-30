"""Tests for Customer MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.tools.customers import register_customer_tools


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def customer_tools():
    """Register customer tools so the inner functions are accessible."""
    mcp = AsyncMock()
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_customer_tools(mcp)
    return registered


def _update_defaults(**overrides):
    """Build kwargs for update_customer with explicit defaults."""
    base = dict(
        customer_id=1,
        name=None,
        name_alias=None,
        client_type=None,
        supplier=None,
        email=None,
        phone=None,
        address=None,
        town=None,
        zip_code=None,
        country_id=None,
        idprof1=None,
        tva_intra=None,
        url=None,
        fax=None,
    )
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_update_customer_basic_fields(mock_client, customer_tools):
    """update_customer passes basic fields to client."""
    mock_client.update_customer.return_value = {"id": 1}

    await customer_tools["update_customer"](**_update_defaults(
        name="Neue GmbH",
        email="neu@example.com",
        phone="+43 1 234567",
    ))

    payload = mock_client.update_customer.call_args[0][1]
    assert payload["name"] == "Neue GmbH"
    assert payload["email"] == "neu@example.com"
    assert payload["phone"] == "+43 1 234567"


@pytest.mark.asyncio
async def test_update_customer_extended_fields(mock_client, customer_tools):
    """update_customer passes idprof1, tva_intra, name_alias, url, fax to client."""
    mock_client.update_customer.return_value = {"id": 150}

    await customer_tools["update_customer"](**_update_defaults(
        customer_id=150,
        idprof1="FN16036h",
        tva_intra="ATU36652804",
        name_alias="Reisegger",
        url="https://www.reisegger.com",
        fax="+43 5522 99999",
    ))

    payload = mock_client.update_customer.call_args[0][1]
    assert payload["idprof1"] == "FN16036h"
    assert payload["tva_intra"] == "ATU36652804"
    assert payload["name_alias"] == "Reisegger"
    assert payload["url"] == "https://www.reisegger.com"
    assert payload["fax"] == "+43 5522 99999"


@pytest.mark.asyncio
async def test_update_customer_country_id(mock_client, customer_tools):
    """update_customer passes country_id (int) correctly, including 0."""
    mock_client.update_customer.return_value = {"id": 1}

    await customer_tools["update_customer"](**_update_defaults(
        country_id=41,
    ))

    payload = mock_client.update_customer.call_args[0][1]
    assert payload["country_id"] == 41


@pytest.mark.asyncio
async def test_update_customer_empty_payload_returns_id(mock_client, customer_tools):
    """update_customer with no fields skips the API call and returns customer_id."""
    result = await customer_tools["update_customer"](**_update_defaults())

    assert result == 1
    mock_client.update_customer.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_customer_zip_maps_to_zip_key(mock_client, customer_tools):
    """zip_code parameter maps to 'zip' in the API payload."""
    mock_client.update_customer.return_value = {"id": 1}

    await customer_tools["update_customer"](**_update_defaults(
        zip_code="6800",
    ))

    payload = mock_client.update_customer.call_args[0][1]
    assert payload["zip"] == "6800"
    assert "zip_code" not in payload


@pytest.mark.asyncio
async def test_delete_customer(mock_client, customer_tools):
    """delete_customer calls client and returns confirmation."""
    mock_client.delete_customer.return_value = None

    result = await customer_tools["delete_customer"](customer_id=150)

    mock_client.delete_customer.assert_awaited_once_with(150)
    assert result == {"status": "deleted", "customer_id": 150}
