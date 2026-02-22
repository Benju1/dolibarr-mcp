"""Tests for new features: Invoice Lines, Pagination, search_invoices, Proposal Lines.

Covers issues #4, #5, #6, #7.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from dolibarr_mcp.models import (
    InvoiceResult,
    InvoiceLineResult,
    ProposalResult,
    ProposalLine,
)
from dolibarr_mcp.dolibarr_client import DolibarrClient


# ---------------------------------------------------------------------------
# Feature 1: InvoiceLineResult model + lines in InvoiceResult (#4)
# ---------------------------------------------------------------------------

class TestInvoiceLineResult:
    """Tests for InvoiceLineResult model."""

    def test_basic_line(self):
        data = {
            "id": 527,
            "desc": "Montage - Techniker",
            "qty": "5.5",
            "subprice": "87.00000000",
            "total_ht": "478.50000000",
            "total_tva": "0E-8",
            "total_ttc": "478.50000000",
            "tva_tx": "0.0000",
            "product_type": 1,
            "product_ref": "000906",
            "product_label": "Techniker",
            "fk_product": 2,
        }
        line = InvoiceLineResult(**data)
        assert line.id == 527
        assert line.desc == "Montage - Techniker"
        assert line.qty == Decimal("5.5")
        assert line.subprice == Decimal("87")
        assert line.total_ht == Decimal("478.5")
        assert line.product_ref == "000906"
        assert line.fk_product == 2

    def test_line_without_product(self):
        data = {
            "id": 536,
            "desc": "Inbetriebnahme",
            "qty": "3.25",
            "subprice": "87.00000000",
            "total_ht": "282.75000000",
            "total_tva": "0E-8",
            "total_ttc": "282.75000000",
            "tva_tx": "0.0000",
            "product_type": 0,
            "product_ref": None,
            "product_label": None,
            "fk_product": None,
        }
        line = InvoiceLineResult(**data)
        assert line.product_ref is None
        assert line.fk_product is None

    def test_line_with_scientific_notation(self):
        data = {
            "id": 1,
            "desc": "Test",
            "qty": "1",
            "subprice": "100.00",
            "total_ht": "100.00",
            "total_tva": "0E-8",
            "total_ttc": "100.00",
            "tva_tx": "0.0000",
        }
        line = InvoiceLineResult(**data)
        assert line.total_tva == Decimal("0")


class TestInvoiceResultWithLines:
    """Tests for InvoiceResult with optional lines field."""

    def _base_invoice(self):
        return {
            "id": 155,
            "ref": "000408",
            "socid": 42,
            "date": 1721001600,
            "total_ht": "7036.50",
            "total_tva": "0E-8",
            "total_ttc": "7036.50",
            "paye": 1,
            "status": 2,
        }

    def test_invoice_with_lines(self):
        data = self._base_invoice()
        data["lines"] = [
            {
                "id": 527,
                "desc": "Montage",
                "qty": "5.5",
                "subprice": "87.00",
                "total_ht": "478.50",
                "total_tva": "0.00",
                "total_ttc": "478.50",
                "tva_tx": "0.0",
                "product_type": 1,
                "product_ref": "000906",
                "product_label": "Techniker",
                "fk_product": 2,
            }
        ]
        inv = InvoiceResult(**data)
        assert inv.lines is not None
        assert len(inv.lines) == 1
        assert inv.lines[0].id == 527

    def test_invoice_without_lines(self):
        """List endpoint returns no lines — should parse as None."""
        inv = InvoiceResult(**self._base_invoice())
        assert inv.lines is None

    def test_invoice_with_empty_lines(self):
        data = self._base_invoice()
        data["lines"] = []
        inv = InvoiceResult(**data)
        assert inv.lines == []

    def test_invoice_with_multiple_lines(self):
        data = self._base_invoice()
        data["lines"] = [
            {
                "id": i,
                "desc": f"Line {i}",
                "qty": "1",
                "subprice": "100.00",
                "total_ht": "100.00",
                "total_tva": "20.00",
                "total_ttc": "120.00",
                "tva_tx": "20.0",
            }
            for i in range(5)
        ]
        inv = InvoiceResult(**data)
        assert len(inv.lines) == 5


# ---------------------------------------------------------------------------
# Feature 2: Pagination for get_invoices (#6)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestInvoicePagination:

    async def test_get_invoices_passes_page(self):
        client = DolibarrClient(MagicMock())
        with_request = AsyncMock(return_value=[])
        client.request = with_request

        await client.get_invoices(limit=10, page=3)

        with_request.assert_called_once()
        call_args = with_request.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params")
        assert params["page"] == 3
        assert params["limit"] == 10

    async def test_get_invoices_default_page_zero(self):
        client = DolibarrClient(MagicMock())
        client.request = AsyncMock(return_value=[])

        await client.get_invoices(limit=5)

        params = client.request.call_args.kwargs.get("params") or client.request.call_args[1].get("params")
        assert params["page"] == 0


# ---------------------------------------------------------------------------
# Feature 3: search_invoices (#5)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestSearchInvoices:

    async def test_search_invoices_by_customer(self):
        client = DolibarrClient(MagicMock())
        client.request = AsyncMock(return_value=[])

        await client.search_invoices(sqlfilters="(t.fk_soc:=:42)", limit=20)

        client.request.assert_called_once()
        args = client.request.call_args
        params = args.kwargs.get("params") or args[1].get("params")
        assert params["sqlfilters"] == "(t.fk_soc:=:42)"
        assert params["limit"] == 20
        assert params["sortfield"] == "t.rowid"
        assert params["sortorder"] == "DESC"

    async def test_search_invoices_no_filter(self):
        client = DolibarrClient(MagicMock())
        client.request = AsyncMock(return_value=[])

        await client.search_invoices()

        params = client.request.call_args.kwargs.get("params") or client.request.call_args[1].get("params")
        assert "sqlfilters" not in params

    async def test_search_invoices_returns_list(self):
        client = DolibarrClient(MagicMock())
        client.request = AsyncMock(return_value=[{"id": 1, "ref": "INV-001"}])

        result = await client.search_invoices(sqlfilters="(t.fk_soc:=:42)")
        assert isinstance(result, list)
        assert len(result) == 1

    async def test_search_invoices_non_list_response(self):
        """API might return non-list on error — should return empty list."""
        client = DolibarrClient(MagicMock())
        client.request = AsyncMock(return_value={"error": "not found"})

        result = await client.search_invoices(sqlfilters="(t.fk_soc:=:999)")
        assert result == []


# ---------------------------------------------------------------------------
# Feature 4: Proposal Lines in ProposalResult (#7)
# ---------------------------------------------------------------------------

class TestProposalResultWithLines:

    def _base_proposal(self):
        return {
            "id": 6,
            "ref": "000127",
            "socid": 11,
            "date": 1692316800,
            "total_ht": "2577.82",
            "total_tva": "515.56",
            "total_ttc": "3093.38",
            "status": 4,
        }

    def test_proposal_with_lines(self):
        data = self._base_proposal()
        data["lines"] = [
            {
                "id": 19,
                "desc": "Zählerverteiler",
                "subprice": "3811.25",
                "qty": "1",
                "tva_tx": "20.0",
                "total_ht": "2972.78",
                "total_ttc": "3567.33",
                "fk_product": 20,
            }
        ]
        prop = ProposalResult(**data)
        assert prop.lines is not None
        assert len(prop.lines) == 1
        assert prop.lines[0].id == 19

    def test_proposal_without_lines(self):
        prop = ProposalResult(**self._base_proposal())
        assert prop.lines is None

    def test_proposal_lines_use_aliases(self):
        """ProposalLine uses aliases (desc→description, subprice→unit_price)."""
        data = self._base_proposal()
        data["lines"] = [
            {
                "id": 1,
                "desc": "Service",
                "subprice": "100.00",
                "qty": "2",
                "tva_tx": "20.0",
                "total_ht": "200.00",
                "total_ttc": "240.00",
            }
        ]
        prop = ProposalResult(**data)
        line = prop.lines[0]
        # Verify alias access works
        assert line.description == "Service"
        assert line.unit_price == Decimal("100")
        assert line.vat_rate == Decimal("20")
