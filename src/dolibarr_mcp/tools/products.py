"""Product tools for Dolibarr MCP Server."""

import re
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient, DolibarrAPIError
from ..models import ProductResult


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


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
        sqlfilters = f"(t.ref:like:'{ref_sanitized}%')"
        
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
        sqlfilters = f"(t.ref:'{ref_sanitized}')"
        
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
        label: str = Field(..., description="Product label"),
        ref: Optional[str] = Field(None, description="Product reference (auto-generated if omitted)"),
        price: float = Field(0.0, description="Selling price"),
        type: int = Field(0, description="Type (0=Product, 1=Service)"),
        description: Optional[str] = Field(None, description="Product description"),
        tva_tx: float = Field(20.0, description="VAT rate"),
        cost_price: Optional[float] = Field(None, description="Cost/purchase price"),
        barcode: Optional[str] = Field(None, description="Barcode value"),
        barcode_type_code: Optional[str] = Field(None, description="Barcode type code (e.g. EAN13, UPC)"),
        status: Optional[int] = Field(None, description="Selling status (0=Not for sale, 1=For sale)"),
        status_buy: Optional[int] = Field(None, description="Buying status (0=Not for purchase, 1=For purchase)"),
        note_public: Optional[str] = Field(None, description="Public note"),
        note_private: Optional[str] = Field(None, description="Private note"),
    ) -> int:
        """Create a new product. Returns the new product ID."""
        client = _require_client()

        payload = {
            "label": label,
            "price": str(price),
            "type": type,
            "tva_tx": str(tva_tx),
        }
        if ref is not None:
            payload["ref"] = ref
        if description is not None:
            payload["description"] = description
        if cost_price is not None:
            payload["cost_price"] = str(cost_price)
        if barcode is not None:
            payload["barcode"] = barcode
        if barcode_type_code is not None:
            payload["barcode_type_code"] = barcode_type_code
        if status is not None:
            payload["status"] = status
        if status_buy is not None:
            payload["status_buy"] = status_buy
        if note_public is not None:
            payload["note_public"] = note_public
        if note_private is not None:
            payload["note_private"] = note_private

        return await client.create_product(payload)

    @mcp.tool()
    async def update_product(
        product_id: int = Field(..., description="Product ID to update"),
        label: Optional[str] = Field(None, description="Product label"),
        price: Optional[float] = Field(None, description="Selling price"),
        description: Optional[str] = Field(None, description="Product description"),
        tva_tx: Optional[float] = Field(None, description="VAT rate"),
        cost_price: Optional[float] = Field(None, description="Cost/purchase price"),
        barcode: Optional[str] = Field(None, description="Barcode value"),
        barcode_type_code: Optional[str] = Field(None, description="Barcode type code (e.g. EAN13, UPC)"),
        status: Optional[int] = Field(None, description="Selling status (0=Not for sale, 1=For sale)"),
        status_buy: Optional[int] = Field(None, description="Buying status (0=Not for purchase, 1=For purchase)"),
        note_public: Optional[str] = Field(None, description="Public note"),
        note_private: Optional[str] = Field(None, description="Private note"),
    ) -> ProductResult:
        """Update an existing product. Only provided fields are modified (sparse update). Returns the updated product."""
        client = _require_client()

        payload: Dict[str, Any] = {}
        if label is not None:
            payload["label"] = label
        if price is not None:
            payload["price"] = str(price)
        if description is not None:
            payload["description"] = description
        if tva_tx is not None:
            payload["tva_tx"] = str(tva_tx)
        if cost_price is not None:
            payload["cost_price"] = str(cost_price)
        if barcode is not None:
            payload["barcode"] = barcode
        if barcode_type_code is not None:
            payload["barcode_type_code"] = barcode_type_code
        if status is not None:
            payload["status"] = status
        if status_buy is not None:
            payload["status_buy"] = status_buy
        if note_public is not None:
            payload["note_public"] = note_public
        if note_private is not None:
            payload["note_private"] = note_private

        if not payload:
            raise ValueError("At least one field must be provided for update")

        await client.update_product(product_id, payload)
        result = await client.get_product_by_id(product_id)
        return ProductResult(**result)

    @mcp.tool()
    async def delete_product(
        product_id: int = Field(..., description="Product ID to delete"),
    ) -> Dict[str, Any]:
        """Delete a product. Returns confirmation."""
        client = _require_client()

        await client.delete_product(product_id)
        return {"status": "deleted", "product_id": product_id}
