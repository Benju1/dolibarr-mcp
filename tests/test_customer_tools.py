"""Tests for Customer MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import CustomerResult
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


def _create_defaults(**overrides):
    """Build kwargs for create_customer with explicit defaults."""
    base = dict(
        name="Test GmbH",
        client_type=1,
        supplier=0,
        email=None,
        phone=None,
        address=None,
        town=None,
        zip_code=None,
        country_id=1,
        idprof1=None,
    )
    base.update(overrides)
    return base


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


# ---------------------------------------------------------------------------
# create_customer
# ---------------------------------------------------------------------------

class TestCreateCustomer:

    @pytest.mark.asyncio
    async def test_create_customer_default_is_customer(self, mock_client, customer_tools):
        """Default create_customer creates a customer (client=1, fournisseur=0)."""
        mock_client.create_customer.return_value = 10

        result = await customer_tools["create_customer"](**_create_defaults())

        payload = mock_client.create_customer.call_args[0][0]
        assert payload["client"] == 1
        assert payload["fournisseur"] == 0
        assert payload["code_client"] == -1
        assert "code_fournisseur" not in payload
        assert result == 10

    @pytest.mark.asyncio
    async def test_create_supplier(self, mock_client, customer_tools):
        """create_customer with supplier=1 sets fournisseur and auto-generates code."""
        mock_client.create_customer.return_value = 11

        result = await customer_tools["create_customer"](**_create_defaults(
            client_type=0, supplier=1,
        ))

        payload = mock_client.create_customer.call_args[0][0]
        assert payload["client"] == 0
        assert payload["fournisseur"] == 1
        assert payload["code_fournisseur"] == -1
        assert "code_client" not in payload
        assert result == 11

    @pytest.mark.asyncio
    async def test_create_customer_and_supplier(self, mock_client, customer_tools):
        """create_customer with client_type=1, supplier=1 creates both roles."""
        mock_client.create_customer.return_value = 12

        await customer_tools["create_customer"](**_create_defaults(
            client_type=1, supplier=1,
        ))

        payload = mock_client.create_customer.call_args[0][0]
        assert payload["client"] == 1
        assert payload["fournisseur"] == 1
        assert payload["code_client"] == -1
        assert payload["code_fournisseur"] == -1

    @pytest.mark.asyncio
    async def test_create_prospect(self, mock_client, customer_tools):
        """create_customer with client_type=2 creates a prospect."""
        mock_client.create_customer.return_value = 13

        await customer_tools["create_customer"](**_create_defaults(
            client_type=2, supplier=0,
        ))

        payload = mock_client.create_customer.call_args[0][0]
        assert payload["client"] == 2
        assert payload["code_client"] == -1

    @pytest.mark.asyncio
    async def test_create_neither(self, mock_client, customer_tools):
        """client_type=0, supplier=0 creates a third-party with no role codes."""
        mock_client.create_customer.return_value = 14

        await customer_tools["create_customer"](**_create_defaults(
            client_type=0, supplier=0,
        ))

        payload = mock_client.create_customer.call_args[0][0]
        assert payload["client"] == 0
        assert payload["fournisseur"] == 0
        assert "code_client" not in payload
        assert "code_fournisseur" not in payload

    @pytest.mark.asyncio
    async def test_create_customer_no_type_field(self, mock_client, customer_tools):
        """Payload must NOT contain 'type' — client/fournisseur are set directly."""
        mock_client.create_customer.return_value = 15

        await customer_tools["create_customer"](**_create_defaults())

        payload = mock_client.create_customer.call_args[0][0]
        assert "type" not in payload


# ---------------------------------------------------------------------------
# search_suppliers
# ---------------------------------------------------------------------------

class TestSearchSuppliers:

    @pytest.mark.asyncio
    async def test_search_suppliers_filters_fournisseur(self, mock_client, customer_tools):
        """search_suppliers adds fournisseur>=1 filter."""
        mock_client.search_customers.return_value = [
            {"id": 20, "nom": "Lieferant AG", "status": 1, "client": 0, "fournisseur": 1},
        ]

        result = await customer_tools["search_suppliers"](query="Lieferant", limit=20)

        call_args = mock_client.search_customers.call_args
        sqlfilters = call_args[1]["sqlfilters"] if "sqlfilters" in call_args[1] else call_args[0][0]
        assert "t.fournisseur:>=:1" in sqlfilters
        assert len(result) == 1
        assert isinstance(result[0], CustomerResult)

    @pytest.mark.asyncio
    async def test_search_suppliers_sanitizes_query(self, mock_client, customer_tools):
        """search_suppliers strips dangerous characters via _sanitize_search."""
        mock_client.search_customers.return_value = []

        await customer_tools["search_suppliers"](query="Test; 'inject", limit=20)

        call_args = mock_client.search_customers.call_args
        sqlfilters = call_args[1]["sqlfilters"] if "sqlfilters" in call_args[1] else call_args[0][0]
        assert "Test" in sqlfilters
        assert "inject" in sqlfilters
        assert ";" not in sqlfilters


# ---------------------------------------------------------------------------
# search_customers
# ---------------------------------------------------------------------------

class TestSearchCustomers:

    @pytest.mark.asyncio
    async def test_search_customers_filters_client(self, mock_client, customer_tools):
        """search_customers adds client>=1 filter."""
        mock_client.search_customers.return_value = []

        await customer_tools["search_customers"](query="Test", limit=20)

        call_args = mock_client.search_customers.call_args
        sqlfilters = call_args[1]["sqlfilters"] if "sqlfilters" in call_args[1] else call_args[0][0]
        assert "t.client:>=:1" in sqlfilters


# ---------------------------------------------------------------------------
# update_customer
# ---------------------------------------------------------------------------

class TestUpdateCustomer:

    @pytest.mark.asyncio
    async def test_update_customer_basic_fields(self, mock_client, customer_tools):
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
    async def test_update_customer_extended_fields(self, mock_client, customer_tools):
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
    async def test_update_customer_country_id(self, mock_client, customer_tools):
        """update_customer passes country_id (int) correctly."""
        mock_client.update_customer.return_value = {"id": 1}

        await customer_tools["update_customer"](**_update_defaults(country_id=41))

        payload = mock_client.update_customer.call_args[0][1]
        assert payload["country_id"] == 41

    @pytest.mark.asyncio
    async def test_update_customer_empty_payload_returns_id(self, mock_client, customer_tools):
        """update_customer with no fields skips the API call and returns customer_id."""
        result = await customer_tools["update_customer"](**_update_defaults())

        assert result == 1
        mock_client.update_customer.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_customer_zip_maps_to_zip_key(self, mock_client, customer_tools):
        """zip_code parameter maps to 'zip' in the API payload."""
        mock_client.update_customer.return_value = {"id": 1}

        await customer_tools["update_customer"](**_update_defaults(zip_code="6800"))

        payload = mock_client.update_customer.call_args[0][1]
        assert payload["zip"] == "6800"
        assert "zip_code" not in payload

    @pytest.mark.asyncio
    async def test_update_customer_set_supplier(self, mock_client, customer_tools):
        """update_customer with supplier=1 sets fournisseur and auto-generates code."""
        mock_client.update_customer.return_value = {"id": 1}

        await customer_tools["update_customer"](**_update_defaults(supplier=1))

        payload = mock_client.update_customer.call_args[0][1]
        assert payload["fournisseur"] == 1
        assert payload["code_fournisseur"] == -1


# ---------------------------------------------------------------------------
# delete_customer
# ---------------------------------------------------------------------------

class TestDeleteCustomer:

    @pytest.mark.asyncio
    async def test_delete_customer(self, mock_client, customer_tools):
        """delete_customer calls client and returns confirmation."""
        mock_client.delete_customer.return_value = None

        result = await customer_tools["delete_customer"](customer_id=150)

        mock_client.delete_customer.assert_awaited_once_with(150)
        assert result == {"status": "deleted", "customer_id": 150}
