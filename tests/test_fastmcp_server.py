"""Tests for FastMCP Server implementation.

Note: After refactoring to modular structure, tests focus on:
1. Client layer (dolibarr_client.py) - integration tests
2. Model validation (models.py) - unit tests  
3. Tool modules - tested via their functions with mocked clients
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock, patch
from dolibarr_mcp import server as server_module
from dolibarr_mcp import state as state_module


@pytest.mark.asyncio
async def test_server_get_client_uninitialized():
    """Test that get_client() raises error if server not initialized."""
    # Reset the global client
    state_module.set_client(None)
    
    with pytest.raises(RuntimeError, match="Server not initialized"):
        state_module.get_client()


@pytest.mark.asyncio
async def test_server_get_client_initialized():
    """Test that get_client() returns client when initialized."""
    mock_client = AsyncMock()
    state_module.set_client(mock_client)
    
    result = state_module.get_client()
    assert result is mock_client
    
    # Cleanup
    state_module.set_client(None)


def test_mcp_server_initialized():
    """Test that mcp server is properly initialized."""
    assert server_module.mcp is not None
    assert server_module.mcp.name == "dolibarr-mcp"
    # Verify it's a FastMCP instance
    assert hasattr(server_module.mcp, 'run')

