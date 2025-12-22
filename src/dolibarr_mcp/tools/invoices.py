"""Invoice tools for Dolibarr MCP Server."""

from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import InvoiceResult, InvoiceLine


def _require_client() -> DolibarrClient:
    from ..server import _get_client
    return _get_client()


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
            
        # Convert Pydantic models to dicts
        lines_data = [line.model_dump(exclude_none=True) for line in lines]
        
        payload = {
            "socid": customer_id,
            "date": date,
            "lines": lines_data,
            "type": 0,  # Standard invoice
            "statut": 0  # Draft
        }
        
        if project_id:
            payload["fk_project"] = project_id
        if payment_mode_id:
            payload["mode_reglement_id"] = payment_mode_id
                
        return await client.create_invoice(payload)

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
