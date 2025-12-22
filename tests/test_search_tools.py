import pytest
from unittest.mock import AsyncMock, patch
from dolibarr_mcp.dolibarr_client import DolibarrClient


@pytest.mark.asyncio
async def test_search_products_by_ref():
    """Test searching products by reference."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = [
            {"id": 1, "ref": "PRJ-123", "label": "Project 123"}
        ]
        
        result = await client.search_products(sqlfilters="(t.ref:like:'PRJ%')")
        
        assert len(result) > 0
        assert result[0]["ref"] == "PRJ-123"
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_product_ref_exact():
    """Test resolving product by exact reference."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = [
            {"id": 1, "ref": "PRJ-123", "label": "Project 123"}
        ]
        
        result = await client.search_products(sqlfilters="(t.ref:like:'PRJ-123%')")
        
        assert len(result) > 0
        assert result[0]["ref"] == "PRJ-123"


@pytest.mark.asyncio
async def test_resolve_product_ref_ambiguous():
    """Test resolving product with multiple matches."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        # Return multiple matches
        mock_request.return_value = [
            {"id": 1, "ref": "PRJ-123-A", "label": "Project 123 A"},
            {"id": 2, "ref": "PRJ-123-B", "label": "Project 123 B"}
        ]
        
        result = await client.search_products(sqlfilters="(t.ref:like:'PRJ-123%')")
        
        assert len(result) == 2


@pytest.mark.asyncio
async def test_search_customers():
    """Test searching customers."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = [
            {"id": 1, "nom": "Acme Corp"}
        ]
        
        result = await client.search_customers(sqlfilters="(t.nom:like:'Acme%')")
        
        assert len(result) > 0
        assert result[0]["nom"] == "Acme Corp"
        mock_request.assert_called_once()
