"""Purchasing price (supplier price) tools for Dolibarr MCP Server."""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient, DolibarrAPIError
from ..models import PurchasingPriceResult


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


def register_purchasing_price_tools(mcp: FastMCP) -> None:
    """Register all purchasing-price-related tools."""

    @mcp.tool()
    async def get_product_purchasing_prices(
        product_id: int = Field(..., description="Product ID"),
    ) -> List[PurchasingPriceResult]:
        """Get all supplier purchasing prices for a product.

        Returns a list of price entries — one per supplier/quantity combination.
        A product can have multiple prices from different suppliers or
        quantity-based price tiers from the same supplier.
        """
        client = _require_client()
        try:
            result = await client.get_product_purchasing_prices(product_id)
            return [PurchasingPriceResult(**item) for item in result]
        except DolibarrAPIError as e:
            raise RuntimeError(f"Dolibarr API Error: {e.message}")

    @mcp.tool()
    async def add_product_purchasing_price(
        product_id: int = Field(..., description="Product ID"),
        supplier_id: int = Field(..., description="Supplier thirdparty ID"),
        price: float = Field(..., description="Purchase unit price (HT, excluding tax)"),
        quantity: int = Field(1, ge=1, description="Minimum quantity for this price"),
        supplier_ref: Optional[str] = Field(None, description="Supplier's product reference/SKU"),
        tva_tx: float = Field(20.0, description="VAT rate (%)"),
        delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery time in days"),
        multicurrency_code: Optional[str] = Field(None, description="Currency code (e.g. EUR, USD). Defaults to Dolibarr main currency."),
        multicurrency_unitprice: Optional[float] = Field(None, description="Unit price in foreign currency (required if multicurrency_code is set)"),
    ) -> int:
        """Add a supplier purchasing price to a product. Returns the new price entry ID.

        Use this to record what a supplier charges for a product at a given
        quantity tier. Multiple entries per product are normal — different
        suppliers or quantity breakpoints.
        """
        client = _require_client()

        payload: Dict[str, Any] = {
            "fourn_id": supplier_id,
            "fourn_price": str(price),
            "fourn_qty": quantity,
            "tva_tx": str(tva_tx),
        }
        if supplier_ref is not None:
            payload["fourn_ref"] = supplier_ref
        if delivery_time_days is not None:
            payload["delivery_time_days"] = delivery_time_days
        if multicurrency_code is not None:
            payload["multicurrency_code"] = multicurrency_code
        if multicurrency_unitprice is not None:
            payload["multicurrency_unitprice"] = str(multicurrency_unitprice)

        return await client.add_product_purchasing_price(product_id, payload)

    @mcp.tool()
    async def delete_product_purchasing_price(
        product_id: int = Field(..., description="Product ID"),
        price_id: int = Field(..., description="Purchasing price entry ID to delete"),
    ) -> Dict[str, Any]:
        """Delete a supplier purchasing price entry from a product. Returns confirmation."""
        client = _require_client()

        await client.delete_product_purchasing_price(product_id, price_id)
        return {"status": "deleted", "product_id": product_id, "price_id": price_id}
