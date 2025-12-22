"""Order tools for Dolibarr MCP Server."""

from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import OrderResult, InvoiceLine


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


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
            
        # 1. Create order header
        payload = {
            "socid": customer_id,
            "date_commande": date,
            "type": 0,
            "statut": 0  # Draft
        }
        
        if project_id:
            payload["fk_project"] = project_id
        if delivery_date:
            payload["date_livraison"] = delivery_date
                
        order_id = await client.create_order(payload)
        
        # 2. Add lines individually
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
                
            await client.add_order_line(order_id, api_line)
            
        return order_id

    @mcp.tool()
    async def add_order_line(
        order_id: int = Field(..., description="Order ID"),
        description: str = Field(..., description="Line description"),
        unit_price: float = Field(..., description="Unit price (net)"),
        quantity: float = Field(..., description="Quantity"),
        vat_rate: float = Field(20.0, description="VAT rate (%)"),
        product_id: Optional[int] = Field(None, description="Product ID (optional)")
    ) -> int:
        """Add a line to an order. Returns the created line ID."""
        client = _require_client()
        
        line_data = {
            "desc": description,
            "subprice": str(unit_price),
            "qty": str(quantity),
            "tva_tx": str(vat_rate)
        }
        
        if product_id:
            line_data["fk_product"] = product_id
            
        result = await client.add_order_line(order_id, line_data)
        # Dolibarr returns int (line_id) or dict with id
        if isinstance(result, (int, str)):
            return int(result)
        if isinstance(result, dict):
            return int(result.get("id", 0))
        return 0
