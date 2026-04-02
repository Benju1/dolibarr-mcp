"""
Contact Operations Tests for Dolibarr MCP Server.

Tests for get_contacts with page and sqlfilters parameters (Issue #31).
Run with: uv run pytest tests/test_contact_operations.py -v
"""

import pytest
from unittest.mock import patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dolibarr_mcp import DolibarrClient, Config


class TestGetContacts:
    """Test get_contacts with pagination and filtering."""

    @pytest.fixture
    def config(self):
        return Config(
            dolibarr_url="https://test.dolibarr.com",
            dolibarr_api_key="test_api_key",
            log_level="INFO",
        )

    @pytest.fixture
    def client(self, config):
        return DolibarrClient(config)

    @pytest.mark.asyncio
    async def test_get_contacts_default(self, client):
        """Default call sends limit=100 and page=0."""
        with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {"id": 1, "lastname": "Doe", "firstname": "John", "socid": 10}
            ]
            result = await client.get_contacts()
            mock_request.assert_called_once_with(
                "GET", "contacts", params={"limit": 100, "page": 0}
            )
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_contacts_with_page(self, client):
        """Page parameter is forwarded to API."""
        with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            await client.get_contacts(limit=50, page=2)
            mock_request.assert_called_once_with(
                "GET", "contacts", params={"limit": 50, "page": 2}
            )

    @pytest.mark.asyncio
    async def test_get_contacts_with_sqlfilters(self, client):
        """sqlfilters parameter is forwarded to API."""
        with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {"id": 5, "lastname": "Smith", "firstname": "Jane", "socid": 42}
            ]
            result = await client.get_contacts(sqlfilters="(t.socid:'42')")
            mock_request.assert_called_once_with(
                "GET",
                "contacts",
                params={"limit": 100, "page": 0, "sqlfilters": "(t.socid:'42')"},
            )
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_contacts_with_all_params(self, client):
        """All parameters work together."""
        with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            await client.get_contacts(limit=10, page=3, sqlfilters="(t.socid:'7')")
            mock_request.assert_called_once_with(
                "GET",
                "contacts",
                params={"limit": 10, "page": 3, "sqlfilters": "(t.socid:'7')"},
            )

    @pytest.mark.asyncio
    async def test_get_contacts_empty_result(self, client):
        """Non-list API response returns empty list."""
        with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"error": "not found"}
            result = await client.get_contacts()
            assert result == []
