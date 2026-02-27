"""Tests for invoice note_public / note_private support."""

import pytest
from unittest.mock import AsyncMock, patch

from dolibarr_mcp.config import Config
from dolibarr_mcp.dolibarr_client import DolibarrClient
from dolibarr_mcp.models import InvoiceResult


# ---------------------------------------------------------------------------
# Minimal valid data shared across model tests
# ---------------------------------------------------------------------------
_BASE_INVOICE = {
    "id": 1,
    "ref": "FA2401-0001",
    "socid": 10,
    "date": 1700000000,
    "total_ht": "100.00",
    "total_tva": "19.00",
    "total_ttc": "119.00",
    "paye": 0,
    "status": 0,
}


# ---------------------------------------------------------------------------
# Model tests (synchronous)
# ---------------------------------------------------------------------------
class TestInvoiceResultNotes:

    def test_invoice_with_notes(self):
        """InvoiceResult correctly parses note_public and note_private."""
        data = {
            **_BASE_INVOICE,
            "note_public": "Reverse Charge §13b",
            "note_private": "Internal: project X",
        }
        inv = InvoiceResult(**data)
        assert inv.note_public == "Reverse Charge §13b"
        assert inv.note_private == "Internal: project X"

    def test_invoice_without_notes(self):
        """Fields default to None when not present in response."""
        inv = InvoiceResult(**_BASE_INVOICE)
        assert inv.note_public is None
        assert inv.note_private is None

    def test_invoice_with_empty_notes(self):
        """Empty string is preserved (used to clear a note)."""
        data = {**_BASE_INVOICE, "note_public": "", "note_private": ""}
        inv = InvoiceResult(**data)
        assert inv.note_public == ""
        assert inv.note_private == ""


# ---------------------------------------------------------------------------
# Client tests (async) – verify payload passthrough
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestUpdateInvoiceNotes:

    @pytest.fixture
    def client(self):
        config = Config(
            dolibarr_url="https://test.dolibarr.com/api/index.php",
            api_key="test_key",
        )
        return DolibarrClient(config)

    @patch("aiohttp.ClientSession.request")
    async def test_update_invoice_passes_notes(self, mock_request, client):
        """update_invoice forwards note_public/note_private in the payload."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "1"
        mock_request.return_value.__aenter__.return_value = mock_response

        async with client:
            await client.update_invoice(
                1,
                {
                    "note_public": "Reverse Charge §13b",
                    "note_private": "Internal note",
                },
            )

        _, kwargs = mock_request.call_args
        assert kwargs["json"]["note_public"] == "Reverse Charge §13b"
        assert kwargs["json"]["note_private"] == "Internal note"

    @patch("aiohttp.ClientSession.request")
    async def test_update_invoice_empty_string_clears_note(self, mock_request, client):
        """Empty string is forwarded (used to clear a note)."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "1"
        mock_request.return_value.__aenter__.return_value = mock_response

        async with client:
            await client.update_invoice(1, {"note_public": ""})

        _, kwargs = mock_request.call_args
        assert kwargs["json"]["note_public"] == ""
