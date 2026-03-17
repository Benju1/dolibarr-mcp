"""Invoice tools for Dolibarr MCP Server."""

from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import InvoiceResult, InvoiceLine


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


def register_invoice_tools(mcp: FastMCP) -> None:
    """Register all invoice-related tools."""
    
    @mcp.tool()
    async def create_invoice(
        customer_id: int = Field(..., description="Customer ID (socid)"),
        date: str = Field(..., description="Invoice date (YYYY-MM-DD)"),
        lines: Optional[List[InvoiceLine]] = Field(None, description="Invoice lines"),
        project_id: Optional[int] = Field(None, description="Project ID"),
        payment_mode_id: Optional[int] = Field(None, description="Payment mode ID"),
        note_public: Optional[str] = Field(None, description="Public note (visible on PDF)"),
        note_private: Optional[str] = Field(None, description="Private note (internal only)")
    ) -> int:
        """Create a new invoice (draft). Returns the new invoice ID."""
        client = _require_client()

        # 1. Create invoice header
        payload = {
            "socid": customer_id,
            "date": date,
            "type": 0,  # Standard invoice
            "statut": 0  # Draft
        }

        if project_id:
            payload["fk_project"] = project_id
        if payment_mode_id:
            payload["mode_reglement_id"] = payment_mode_id
        if note_public is not None:
            payload["note_public"] = note_public
        if note_private is not None:
            payload["note_private"] = note_private

        invoice_id = await client.create_invoice(payload)

        # 2. Add lines individually
        if lines:
            try:
                for line in lines:
                    line_data = line.model_dump(exclude_none=True)
                    # Decimal → str for JSON serialization
                    for key in ("subprice", "qty", "tva_tx"):
                        if key in line_data:
                            line_data[key] = str(line_data[key])
                    await client.add_invoice_line(invoice_id, line_data)
            except Exception:
                # Rollback: delete the invoice if line addition fails
                await client.delete_invoice(invoice_id)
                raise

        return invoice_id

    @mcp.tool()
    async def add_invoice_line(
        invoice_id: int = Field(..., description="Invoice ID"),
        description: str = Field(..., description="Line description"),
        unit_price: float = Field(..., description="Unit price (net)"),
        quantity: float = Field(..., description="Quantity"),
        vat_rate: float = Field(20.0, description="VAT rate (%)"),
        product_id: Optional[int] = Field(None, description="Product ID (optional)")
    ) -> int:
        """Add a line to an invoice. Returns the created line ID."""
        client = _require_client()
        
        line_data = {
            "desc": description,
            "subprice": str(unit_price),
            "qty": str(quantity),
            "tva_tx": str(vat_rate)
        }
        
        if product_id:
            line_data["fk_product"] = product_id
            
        result = await client.add_invoice_line(invoice_id, line_data)
        # Dolibarr returns int (line_id) or dict with id
        if isinstance(result, (int, str)):
            return int(result)
        if isinstance(result, dict):
            return int(result.get("id", 0))
        return 0

    @mcp.tool()
    async def get_invoices(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of invoices"),
        page: int = Field(0, ge=0, description="Page number (starts at 0)"),
        status: Optional[str] = Field(None, description="Filter by status (draft, unpaid, paid)")
    ) -> List[InvoiceResult]:
        """Get a paginated list of invoices."""
        client = _require_client()

        result = await client.get_invoices(limit=limit, page=page, status=status)
        return [InvoiceResult(**item) for item in result]

    STATUS_MAP = {
        "draft": 0,
        "unpaid": 1,
        "paid": 2,
        "abandoned": 3,
    }

    @mcp.tool()
    async def search_invoices(
        customer_id: Optional[int] = Field(None, description="Filter by customer ID"),
        status: Optional[str] = Field(None, description="Filter by status (draft, unpaid, paid, abandoned)"),
        limit: int = Field(20, ge=1, le=100, description="Maximum number of results"),
    ) -> List[InvoiceResult]:
        """Search invoices with server-side filtering.

        Uses Dolibarr Universal Search Filter (USF) syntax.
        Can combine both customer_id and status filters."""
        client = _require_client()

        filters = []
        if customer_id is not None:
            filters.append(f"(t.fk_soc:=:{customer_id})")
        if status and status in STATUS_MAP:
            filters.append(f"(t.fk_statut:=:{STATUS_MAP[status]})")
        sqlfilters = " and ".join(filters) if filters else ""

        result = await client.search_invoices(sqlfilters=sqlfilters, limit=limit)
        return [InvoiceResult(**item) for item in result]

    @mcp.tool()
    async def get_invoice_by_id(
        invoice_id: int = Field(..., description="Invoice ID")
    ) -> InvoiceResult:
        """Get details of a specific invoice."""
        client = _require_client()
            
        result = await client.get_invoice_by_id(invoice_id)
        return InvoiceResult(**result)

    @mcp.tool()
    async def update_invoice(
        invoice_id: int = Field(..., description="Invoice ID to update"),
        date: Optional[str] = Field(None, description="Invoice date (YYYY-MM-DD)"),
        payment_mode_id: Optional[int] = Field(None, description="Payment mode ID"),
        note_public: Optional[str] = Field(None, description="Public note (visible on PDF)"),
        note_private: Optional[str] = Field(None, description="Private note (internal only)")
    ) -> int:
        """Update an existing invoice (draft only)."""
        client = _require_client()

        payload = {}
        if date:
            payload["date"] = date
        if payment_mode_id:
            payload["mode_reglement_id"] = payment_mode_id
        if note_public is not None:
            payload["note_public"] = note_public
        if note_private is not None:
            payload["note_private"] = note_private

        if not payload:
            return invoice_id

        return await client.update_invoice(invoice_id, payload)

    @mcp.tool()
    async def validate_invoice(
        invoice_id: int = Field(..., description="Invoice ID to validate")
    ) -> int:
        """Validate a draft invoice."""
        client = _require_client()
            
        return await client.validate_invoice(invoice_id)

    @mcp.tool()
    async def set_invoice_to_draft(
        invoice_id: int = Field(..., description="Invoice ID to set back to draft")
    ) -> InvoiceResult:
        """Set a validated invoice back to draft status.

        After setting to draft, you can update/delete lines and re-validate.
        """
        client = _require_client()
        await client.set_invoice_to_draft(invoice_id)
        result = await client.get_invoice_by_id(invoice_id)
        return InvoiceResult(**result)

    @mcp.tool()
    async def add_payment_to_invoice(
        invoice_id: int = Field(..., description="Invoice ID"),
        date: str = Field(..., description="Payment date (YYYY-MM-DD)"),
        payment_mode_id: int = Field(..., description="Payment mode ID (paymentid)"),
        account_id: int = Field(..., ge=1, description="Bank account ID (accountid)"),
        num_payment: Optional[str] = Field(None, description="Payment reference number"),
        close_paid: bool = Field(False, description="Close invoice as paid if fully paid")
    ) -> int:
        """Add a payment to an invoice (full remainder).
        
        This tool pays the remaining unpaid amount of the invoice.
        For partial payments, please use the Dolibarr UI or check API capabilities.
        """
        client = _require_client()
            
        payload = {
            "datepaye": date,
            "paymentid": payment_mode_id,
            "closepaidinvoices": "yes" if close_paid else "no",
            "accountid": account_id,
            "num_payment": num_payment or "",
        }
        
        return await client.add_payment_to_invoice(invoice_id, payload)

    @mcp.tool()
    async def delete_invoice(
        invoice_id: int = Field(..., description="Invoice ID to delete")
    ) -> int:
        """Delete an invoice (draft only). Returns the deleted invoice ID."""
        client = _require_client()
        await client.delete_invoice(invoice_id)
        return invoice_id

    @mcp.tool()
    async def update_invoice_line(
        invoice_id: int = Field(..., description="Invoice ID"),
        line_id: int = Field(..., description="Line ID"),
        description: Optional[str] = Field(None, description="Line description"),
        unit_price: Optional[float] = Field(None, description="Unit price (net)"),
        quantity: Optional[float] = Field(None, description="Quantity"),
        vat_rate: Optional[float] = Field(None, description="VAT rate (%)")
    ) -> int:
        """Update a line in an invoice (draft only). Returns the line ID."""
        client = _require_client()

        if all(v is None for v in (description, unit_price, quantity, vat_rate)):
            raise ValueError("At least one field must be provided for update")

        # Fetch current line data to preserve unprovided fields
        invoice_data = await client.get_invoice_by_id(invoice_id)
        current_line = None
        for line in invoice_data.get("lines", []):
            if int(line.get("id", 0)) == line_id:
                current_line = line
                break
        if current_line is None:
            raise ValueError(f"Line {line_id} not found in invoice {invoice_id}")

        # Build payload from current values, override with provided values
        payload = {
            "desc": current_line.get("desc", ""),
            "subprice": str(current_line.get("subprice", 0)),
            "qty": str(current_line.get("qty", 0)),
            "tva_tx": str(current_line.get("tva_tx", 0)),
            "product_type": current_line.get("product_type", 0),
        }
        if current_line.get("fk_product"):
            payload["fk_product"] = current_line["fk_product"]

        if description is not None:
            payload["desc"] = description
        if unit_price is not None:
            payload["subprice"] = str(unit_price)
        if quantity is not None:
            payload["qty"] = str(quantity)
        if vat_rate is not None:
            payload["tva_tx"] = str(vat_rate)

        await client.update_invoice_line(invoice_id, line_id, payload)
        return line_id

    @mcp.tool()
    async def delete_invoice_line(
        invoice_id: int = Field(..., description="Invoice ID"),
        line_id: int = Field(..., description="Line ID to delete")
    ) -> int:
        """Delete a line from an invoice (draft only). Returns the deleted line ID."""
        client = _require_client()
        await client.delete_invoice_line(invoice_id, line_id)
        return line_id
