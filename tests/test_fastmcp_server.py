"""Tests for FastMCP Server implementation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import AsyncMock, patch
from dolibarr_mcp.server import search_projects, get_customers, create_invoice, search_products_by_ref
from dolibarr_mcp.models import ProjectSearchResult, CustomerResult, ProductResult

@pytest.mark.asyncio
async def test_search_projects_tool():
    """Test search_projects tool with filters."""
    # Mock the global client
    mock_client = AsyncMock()
    mock_client.search_projects.return_value = [
        {
            "id": 1,
            "ref": "PRJ-001",
            "title": "Test Project",
            "socid": 10,
            "status": 1,
            "description": "Desc",
            "date_creation": 123456,
            "date_modification": 123456
        }
    ]
    
    # Patch the client in server module
    with patch("dolibarr_mcp.server.client", mock_client):
        results = await search_projects.fn(query="Test", filter_customer_id=10, limit=5)
        
        assert len(results) == 1
        assert isinstance(results[0], ProjectSearchResult)
        assert results[0].id == 1
        assert results[0].socid == 10
        
        # Verify call arguments
        mock_client.search_projects.assert_called_once()
        kwargs = mock_client.search_projects.call_args.kwargs
        
        assert kwargs["limit"] == 5
        assert "(t.socid:10)" in kwargs["sqlfilters"]
        assert "t.ref:like" in kwargs["sqlfilters"]

@pytest.mark.asyncio
async def test_get_customers_tool():
    """Test get_customers tool."""
    mock_client = AsyncMock()
    mock_client.get_customers.return_value = [
        {
            "id": 100,
            "name": "Test Customer",
            "client": "1",
            "fournisseur": "0",
            "status": "1"
        }
    ]
    
    with patch("dolibarr_mcp.server.client", mock_client):
        results = await get_customers.fn(limit=10, page=2)
        
        assert len(results) == 1
        assert isinstance(results[0], CustomerResult)
        assert results[0].id == 100
        
        mock_client.get_customers.assert_called_with(limit=10, page=2)

@pytest.mark.asyncio
async def test_server_uninitialized():
    """Test that tools raise error if server not initialized."""
    with patch("dolibarr_mcp.server.client", None):
        with pytest.raises(RuntimeError, match="Server not initialized"):
            await get_customers.fn()


@pytest.mark.asyncio
async def test_search_products_tool():
    """Test the search_products_by_ref tool."""
    # Mock client
    mock_client = AsyncMock()
    mock_client.get_products.return_value = [
        {
            "id": 10,
            "ref": "PROD-001",
            "label": "Test Product",
            "type": "0",
            "price": "100.00",
            "price_ttc": "120.00",
            "tva_tx": "20.00"
        }
    ]
    
    # Patch the global client in server module
    with patch("dolibarr_mcp.server.client", mock_client):
        # Call the tool function directly via .fn
        result = await search_products_by_ref.fn(ref_prefix="PROD", limit=5)
        
        # Verify client call
        mock_client.get_products.assert_called_once()
        call_args = mock_client.get_products.call_args
        assert "sqlfilters" in call_args.kwargs
        assert "(t.ref:like:'PROD%')" in call_args.kwargs["sqlfilters"]
        assert call_args.kwargs["limit"] == 5
        
        # Verify result
        assert len(result) == 1
        assert result[0].id == 10
        assert result[0].ref == "PROD-001"

