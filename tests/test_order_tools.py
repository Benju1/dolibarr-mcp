"""Tests for Order MCP Tools."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock

from dolibarr_mcp import state as state_module
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


@pytest.mark.asyncio
async def test_delete_order(mock_client, order_tools):
    """delete_order calls client and returns confirmation."""
    mock_client.delete_order.return_value = None

    result = await order_tools["delete_order"](order_id=55)

    mock_client.delete_order.assert_awaited_once_with(55)
    assert result == {"status": "deleted", "order_id": 55}
