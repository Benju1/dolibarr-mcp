"""Tests for Contact MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
from dolibarr_mcp.models import ContactResult
from dolibarr_mcp.tools.contacts import register_contact_tools


@pytest.fixture
def mock_client():
    """Create a mock client and inject it into global state."""
    client = AsyncMock()
    state_module.set_client(client)
    yield client
    state_module.set_client(None)


@pytest.fixture
def contact_tools():
    """Register contact tools so the inner functions are accessible."""
    mcp = AsyncMock()
    registered = {}

    def tool_decorator():
        def wrapper(fn):
            registered[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_contact_tools(mcp)
    return registered


CONTACT_API_RESPONSE = {
    "id": 77,
    "lastname": "Mueller",
    "firstname": "Hans",
    "email": "hans@example.com",
    "socid": 10,
    "poste": "Projektleiter",
    "phone_pro": "+43 5522 12345",
    "phone_mobile": "+43 664 9876543",
}


def _update_defaults(**overrides):
    """Build kwargs for update_contact with explicit defaults."""
    base = dict(
        contact_id=77,
        lastname=None,
        firstname=None,
        email=None,
        phone_pro=None,
        phone_mobile=None,
        poste=None,
        socid=None,
    )
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_get_contact_by_id(mock_client, contact_tools):
    """get_contact_by_id returns ContactResult."""
    mock_client.get_contact_by_id.return_value = CONTACT_API_RESPONSE

    result = await contact_tools["get_contact_by_id"](contact_id=77)

    mock_client.get_contact_by_id.assert_awaited_once_with(77)
    assert isinstance(result, ContactResult)
    assert result.id == 77
    assert result.lastname == "Mueller"
    assert result.phone_mobile == "+43 664 9876543"


@pytest.mark.asyncio
async def test_update_contact_basic(mock_client, contact_tools):
    """update_contact sends payload and returns re-read result."""
    mock_client.update_contact.return_value = None
    mock_client.get_contact_by_id.return_value = {
        **CONTACT_API_RESPONSE,
        "lastname": "Meier",
    }

    result = await contact_tools["update_contact"](**_update_defaults(
        lastname="Meier",
        email="meier@example.com",
    ))

    mock_client.update_contact.assert_awaited_once_with(77, {
        "lastname": "Meier",
        "email": "meier@example.com",
    })
    assert isinstance(result, ContactResult)
    assert result.lastname == "Meier"


@pytest.mark.asyncio
async def test_update_contact_phone_mobile(mock_client, contact_tools):
    """update_contact passes phone_mobile to client."""
    mock_client.update_contact.return_value = None
    mock_client.get_contact_by_id.return_value = {
        **CONTACT_API_RESPONSE,
        "phone_mobile": "+43 660 1111111",
    }

    result = await contact_tools["update_contact"](**_update_defaults(
        phone_mobile="+43 660 1111111",
    ))

    payload = mock_client.update_contact.call_args[0][1]
    assert payload["phone_mobile"] == "+43 660 1111111"
    assert result.phone_mobile == "+43 660 1111111"


@pytest.mark.asyncio
async def test_update_contact_empty_payload_skips_put(mock_client, contact_tools):
    """update_contact with no fields skips PUT, only re-reads."""
    mock_client.get_contact_by_id.return_value = CONTACT_API_RESPONSE

    result = await contact_tools["update_contact"](**_update_defaults())

    mock_client.update_contact.assert_not_awaited()
    mock_client.get_contact_by_id.assert_awaited_once_with(77)
    assert result.lastname == "Mueller"


@pytest.mark.asyncio
async def test_update_contact_poste(mock_client, contact_tools):
    """update_contact passes poste to client."""
    mock_client.update_contact.return_value = None
    mock_client.get_contact_by_id.return_value = {
        **CONTACT_API_RESPONSE,
        "poste": "Geschäftsführer",
    }

    await contact_tools["update_contact"](**_update_defaults(
        poste="Geschäftsführer",
    ))

    payload = mock_client.update_contact.call_args[0][1]
    assert payload["poste"] == "Geschäftsführer"


@pytest.mark.asyncio
async def test_create_contact_with_phone_mobile(mock_client, contact_tools):
    """create_contact passes phone_mobile to client."""
    mock_client.create_contact.return_value = 88

    result = await contact_tools["create_contact"](
        lastname="Neu", firstname="Test", socid=10,
        email=None, phone_pro=None,
        phone_mobile="+43 660 2222222",
        poste=None,
    )

    payload = mock_client.create_contact.call_args[0][0]
    assert payload["phone_mobile"] == "+43 660 2222222"
    assert result == 88


@pytest.mark.asyncio
async def test_delete_contact(mock_client, contact_tools):
    """delete_contact calls client and returns confirmation."""
    mock_client.delete_contact.return_value = None

    result = await contact_tools["delete_contact"](contact_id=77)

    mock_client.delete_contact.assert_awaited_once_with(77)
    assert result == {"status": "deleted", "contact_id": 77}
