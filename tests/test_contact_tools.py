"""Tests for Contact MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
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


@pytest.mark.asyncio
async def test_delete_contact(mock_client, contact_tools):
    """delete_contact calls client and returns confirmation."""
    mock_client.delete_contact.return_value = None

    result = await contact_tools["delete_contact"](contact_id=77)

    mock_client.delete_contact.assert_awaited_once_with(77)
    assert result == {"status": "deleted", "contact_id": 77}
