"""Product tools for Dolibarr MCP Server."""

import re
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient, DolibarrAPIError
from ..models import ProductResult


def _require_client() -> DolibarrClient:
    from ..server import _get_client
    return _get_client()


def _sanitize_search(s: str) -> str:
    """Sanitize search input to prevent SQL injection."""
    s = s.strip()
    s = re.sub(r"[^0-9A-Za-z äöüÄÖÜß._\-@/+,&#()]", "", s)
    return s[:80]


def register_product_tools(mcp: FastMCP) -> None:
    """Register all product-related tools."""
    
    @mcp.tool()
    async def search_products_by_ref(
        ref_prefix: str = Field(..., min_length=1, max_length=40, description="Prefix of the product reference"),
        limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    ) -> List[ProductResult]:
        """Search products by (partial) reference."""
        client = _require_client()
            
        ref_sanitized = _sanitize_search(ref_prefix)
        sqlfilters = f"(t.ref=like:'{ref_sanitized}%')"
        
        try:
            result = await client.search_products(sqlfilters=sqlfilters, limit=limit)
            return [ProductResult(**item) for item in result]
        except DolibarrAPIError as e:
            raise RuntimeError(f"Dolibarr API Error: {e.message}")

    @mcp.tool()
    async def search_products_by_label(
        label_search: str = Field(..., description="Search term in product label"),
        limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    ) -> List[ProductResult]:
        """Search products by label/description text."""
        client = _require_client()
            
        label_sanitized = _sanitize_search(label_search)
        sqlfilters = f"(t.label:like:'%{label_sanitized}%')"
        
        try:
            result = await client.search_products(sqlfilters=sqlfilters, limit=limit)
            return [ProductResult(**item) for item in result]
        except DolibarrAPIError as e:
            raise RuntimeError(f"Dolibarr API Error: {e.message}")

    @mcp.tool()
    async def resolve_product_ref(
        ref: str = Field(..., description="Exact product reference")
    ) -> Dict[str, Any]:
        """Resolve an exact product reference to a product ID."""
        client = _require_client()
            
        ref_sanitized = _sanitize_search(ref)
        sqlfilters = f"(t.ref={ref_sanitized})"
        
        try:
            products = await client.search_products(sqlfilters=sqlfilters, limit=2)
        except DolibarrAPIError as e:
            raise RuntimeError(f"Dolibarr API Error: {e.message}") from e
        
        if not products:
            return {"status": "not_found", "ref": ref_sanitized}
        elif len(products) > 1:
            return {"status": "ambiguous", "ref": ref_sanitized, "count": len(products)}
        else:
            product = products[0]
            return {
                "status": "ok",
                "product_id": product.get("id"),
                "ref": product.get("ref"),
                "label": product.get("label"),
                "price": product.get("price")
            }

    @mcp.tool()
    async def get_products(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of products"),
        page: int = Field(0, ge=0, description="Page number (starts at 0)"),
        category_id: Optional[int] = Field(None, description="Filter by category ID")
    ) -> List[ProductResult]:
        """Get a paginated list of products."""
        client = _require_client()
            
        result = await client.get_products(limit=limit, page=page, category_id=category_id)
        return [ProductResult(**item) for item in result]

    @mcp.tool()
    async def get_product_by_id(
        product_id: int = Field(..., description="Product ID")
    ) -> ProductResult:
        """Get details of a specific product."""
        client = _require_client()
            
        result = await client.get_product_by_id(product_id)
        return ProductResult(**result)

    @mcp.tool()
    async def create_product(
        ref: str = Field(..., description="Product reference"),
        label: str = Field(..., description="Product label"),
        price: float = Field(..., description="Selling price"),
        type: int = Field(0, description="Type (0=Product, 1=Service)"),
        description: Optional[str] = Field(None, description="Product description"),
        tva_tx: float = Field(20.0, description="VAT rate")
    ) -> int:
        """Create a new product. Returns the new product ID."""
        client = _require_client()
            
        payload = {
            "ref": ref,
            "label": label,
            "price": str(price),
            "type": type,
            "tva_tx": str(tva_tx)
        }
        if description:
            payload["description"] = description
                
        return await client.create_product(payload)
