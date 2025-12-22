"""Tests for proposal/quote operations."""

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal

from dolibarr_mcp.models import ProposalResult
from dolibarr_mcp.dolibarr_client import DolibarrClient


@pytest.mark.asyncio
async def test_client_get_proposals():
    """Test client.get_proposals() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = [
            {
                "id": 1,
                "ref": "PROP-001",
                "socid": 1,
                "date": 1703000000,
                "total_ht": Decimal("1000.00"),
                "total_tva": Decimal("200.00"),
                "total_ttc": Decimal("1200.00"),
                "status": 1,
                "project_id": 5
            }
        ]
        
        result = await client.get_proposals(limit=100, status=None)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["ref"] == "PROP-001"
        mock_request.assert_called_once_with("GET", "proposals", params={"limit": 100})


@pytest.mark.asyncio
async def test_client_get_proposals_with_filter():
    """Test client.get_proposals() with filters."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = [
            {
                "id": 2,
                "ref": "PROP-002",
                "socid": 2,
                "date": 1703000000,
                "total_ht": Decimal("5000.00"),
                "total_tva": Decimal("1000.00"),
                "total_ttc": Decimal("6000.00"),
                "status": 2,
                "project_id": 10
            }
        ]
        
        result = await client.get_proposals(
            limit=50, 
            status="2",
            sqlfilters="(t.fk_projet:=:10)"
        )
        
        assert len(result) == 1
        assert result[0]["project_id"] == 10
        
        # Verify the call included all filters
        call_args = mock_request.call_args
        assert call_args[0] == ("GET", "proposals")
        assert call_args[1]["params"]["limit"] == 50
        assert call_args[1]["params"]["status"] == "2"
        assert call_args[1]["params"]["sqlfilters"] == "(t.fk_projet:=:10)"


@pytest.mark.asyncio
async def test_client_get_proposal_by_id():
    """Test client.get_proposal_by_id() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "id": 1,
            "ref": "PROP-001",
            "socid": 1,
            "date": 1703000000,
            "total_ht": Decimal("1000.00"),
            "total_tva": Decimal("200.00"),
            "total_ttc": Decimal("1200.00"),
            "status": 1,
            "project_id": 5
        }
        
        result = await client.get_proposal_by_id(1)
        
        assert result["id"] == 1
        assert result["ref"] == "PROP-001"
        assert result["total_ttc"] == Decimal("1200.00")
        mock_request.assert_called_once_with("GET", "proposals/1")


@pytest.mark.asyncio
async def test_proposal_result_model():
    """Test ProposalResult model validation."""
    data = {
        "id": 1,
        "ref": "PROP-001",
        "socid": 1,
        "date": 1703000000,
        "total_ht": Decimal("1000.00"),
        "total_tva": Decimal("200.00"),
        "total_ttc": Decimal("1200.00"),
        "status": 1,
        "project_id": 5
    }
    
    result = ProposalResult(**data)
    
    assert result.id == 1
    assert result.ref == "PROP-001"
    assert result.total_ht == Decimal("1000.00")
    assert result.total_tva == Decimal("200.00")
    assert result.total_ttc == Decimal("1200.00")


@pytest.mark.asyncio
async def test_proposal_result_model_without_project():
    """Test ProposalResult model with optional project_id."""
    data = {
        "id": 1,
        "ref": "PROP-001",
        "socid": 1,
        "date": 1703000000,
        "total_ht": Decimal("1000.00"),
        "total_tva": Decimal("200.00"),
        "total_ttc": Decimal("1200.00"),
        "status": 0
    }
    
    result = ProposalResult(**data)
    
    assert result.id == 1
    assert result.project_id is None


@pytest.mark.asyncio
async def test_proposal_result_model_extra_fields_ignored():
    """Test ProposalResult ignores extra fields (DolibarrBaseModel behavior)."""
    data = {
        "id": 1,
        "ref": "PROP-001",
        "socid": 1,
        "date": 1703000000,
        "total_ht": Decimal("1000.00"),
        "total_tva": Decimal("200.00"),
        "total_ttc": Decimal("1200.00"),
        "status": 1,
        "project_id": 5,
        "extra_unknown_field": "ignored"
    }
    
    # Should not raise an error
    result = ProposalResult(**data)
    assert result.id == 1


@pytest.mark.asyncio
async def test_client_create_proposal():
    """Test client.create_proposal() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"id": 5, "ref": "PROP-005"}
        
        result = await client.create_proposal(
            socid=1,
            date="2024-01-15",
            lines=[],
            statut=0
        )
        
        # _extract_identifier returns the ID
        assert result == 5
        
        call_args = mock_request.call_args
        assert call_args[0] == ("POST", "proposals")
        assert call_args[1]["data"]["socid"] == 1
        assert call_args[1]["data"]["date"] == "2024-01-15"


@pytest.mark.asyncio
async def test_client_create_proposal_with_customer_id_mapping():
    """Test that customer_id is mapped to socid."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"id": 5}
        
        await client.create_proposal(
            customer_id=2,  # Using customer_id instead of socid
            date="2024-01-15"
        )
        
        call_args = mock_request.call_args
        assert call_args[1]["data"]["socid"] == 2
        assert "customer_id" not in call_args[1]["data"]


@pytest.mark.asyncio
async def test_client_update_proposal():
    """Test client.update_proposal() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": 1}
        
        result = await client.update_proposal(
            proposal_id=5,
            data={"date": "2024-01-20"}
        )
        
        call_args = mock_request.call_args
        assert call_args[0] == ("PUT", "proposals/5")
        assert call_args[1]["data"]["date"] == "2024-01-20"


@pytest.mark.asyncio
async def test_client_delete_proposal():
    """Test client.delete_proposal() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": 1}
        
        await client.delete_proposal(proposal_id=5)
        
        call_args = mock_request.call_args
        assert call_args[0] == ("DELETE", "proposals/5")


@pytest.mark.asyncio
async def test_client_add_proposal_line():
    """Test client.add_proposal_line() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"id": 10}
        
        await client.add_proposal_line(
            proposal_id=5,
            desc="Test Line",
            qty=2,
            subprice=Decimal("50.00"),
            product_id=99
        )
        
        call_args = mock_request.call_args
        assert call_args[0] == ("POST", "proposals/5/lines")
        assert call_args[1]["data"]["desc"] == "Test Line"
        assert call_args[1]["data"]["fk_product"] == 99
        assert "product_id" not in call_args[1]["data"]


@pytest.mark.asyncio
async def test_client_update_proposal_line():
    """Test client.update_proposal_line() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": 1}
        
        await client.update_proposal_line(
            proposal_id=5,
            line_id=10,
            qty=3
        )
        
        call_args = mock_request.call_args
        assert call_args[0] == ("PUT", "proposals/5/lines/10")
        assert call_args[1]["data"]["qty"] == 3


@pytest.mark.asyncio
async def test_client_delete_proposal_line():
    """Test client.delete_proposal_line() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": 1}
        
        await client.delete_proposal_line(proposal_id=5, line_id=10)
        
        call_args = mock_request.call_args
        assert call_args[0] == ("DELETE", "proposals/5/lines/10")


@pytest.mark.asyncio
async def test_client_validate_proposal():
    """Test client.validate_proposal() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": 1, "status": 1}
        
        result = await client.validate_proposal(proposal_id=5)
        
        call_args = mock_request.call_args
        assert call_args[0] == ("POST", "proposals/5/validate")


@pytest.mark.asyncio
async def test_client_convert_proposal_to_order():
    """Test client.convert_proposal_to_order() method."""
    config_mock = AsyncMock()
    client = DolibarrClient(config_mock)
    
    with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"id": 20, "ref": "CMD-020"}
        
        result = await client.convert_proposal_to_order(proposal_id=5)
        
        call_args = mock_request.call_args
        assert call_args[0] == ("POST", "proposals/5/convert")
