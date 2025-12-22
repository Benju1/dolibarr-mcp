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
        lines: List[InvoiceLine] = Field(..., description="Invoice lines"),
        project_id: Optional[int] = Field(None, description="Project ID"),
        payment_mode_id: Optional[int] = Field(None, description="Payment mode ID")
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
                
        invoice_id = await client.create_invoice(payload)
        
        # 2. Add lines individually
        try:
            for line in lines:
                line_data = line.model_dump(exclude_none=True)
                
                # Map fields to Dolibarr API format
                api_line = {}
                if "description" in line_data:
                    api_line["desc"] = line_data["description"]
                if "unit_price" in line_data:
                    api_line["subprice"] = str(line_data["unit_price"])
                if "quantity" in line_data:
                    api_line["qty"] = str(line_data["quantity"])
                if "vat_rate" in line_data:
                    api_line["tva_tx"] = str(line_data["vat_rate"])
                if "product_id" in line_data:
                    api_line["fk_product"] = line_data["product_id"]
                if "product_type" in line_data:
                    api_line["product_type"] = line_data["product_type"]
                    
                await client.add_invoice_line(invoice_id, api_line)
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
        status: Optional[str] = Field(None, description="Filter by status (draft, unpaid, paid)")
    ) -> List[InvoiceResult]:
        """Get a list of invoices."""
        client = _require_client()
            
        result = await client.get_invoices(limit=limit, status=status)
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
        payment_mode_id: Optional[int] = Field(None, description="Payment mode ID")
    ) -> int:
        """Update an existing invoice (draft only)."""
        client = _require_client()
            
        payload = {}
        if date:
            payload["date"] = date
        if payment_mode_id:
            payload["mode_reglement_id"] = payment_mode_id
                
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
