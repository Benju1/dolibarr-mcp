"""Order tools for Dolibarr MCP Server."""

from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import OrderResult, InvoiceLine


def _require_client() -> DolibarrClient:
    from ..server import _get_client
    return _get_client()


def register_order_tools(mcp: FastMCP) -> None:
    """Register all order-related tools."""
    
    @mcp.tool()
    async def get_orders(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of orders"),
        page: int = Field(0, ge=0, description="Page number (starts at 0)"),
        status: Optional[int] = Field(None, description="Filter by status")
    ) -> List[OrderResult]:
        """Get a paginated list of orders."""
        client = _require_client()
            
        result = await client.get_orders(limit=limit, page=page, status=status)
        return [OrderResult(**item) for item in result]

    @mcp.tool()
    async def get_order_by_id(
        order_id: int = Field(..., description="Order ID")
    ) -> OrderResult:
        """Get details of a specific order."""
        client = _require_client()
            
        result = await client.get_order_by_id(order_id)
        return OrderResult(**result)

    @mcp.tool()
    async def create_order(
        customer_id: int = Field(..., description="Customer ID (socid)"),
        date: str = Field(..., description="Order date (YYYY-MM-DD)"),
        lines: List[InvoiceLine] = Field(..., description="Order lines"),
        project_id: Optional[int] = Field(None, description="Project ID"),
        delivery_date: Optional[str] = Field(None, description="Delivery date (YYYY-MM-DD)")
    ) -> int:
        """Create a new order (draft). Returns the new order ID."""
        client = _require_client()
            
        # Convert Pydantic models to dicts
        lines_data = [line.model_dump(exclude_none=True) for line in lines]
        
        payload = {
            "socid": customer_id,
            "date_commande": date,
            "lines": lines_data,
            "type": 0,
            "statut": 0  # Draft
        }
        
        if project_id:
            payload["fk_project"] = project_id
        if delivery_date:
            payload["date_livraison"] = delivery_date
                
        return await client.create_order(payload)
