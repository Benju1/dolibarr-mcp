"""Customer tools for Dolibarr MCP Server."""

import re
from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient, DolibarrAPIError
from ..models import CustomerResult


def _require_client() -> DolibarrClient:
    from ..server import _get_client
    return _get_client()


def _sanitize_search(s: str) -> str:
    """Sanitize search input to prevent SQL injection."""
    s = s.strip()
    s = re.sub(r"[^0-9A-Za-z äöüÄÖÜß._\-@/+,&#()]", "", s)
    return s[:80]


def register_customer_tools(mcp: FastMCP) -> None:
    """Register all customer-related tools."""
    
    @mcp.tool()
    async def get_customers(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of customers"),
        page: int = Field(0, ge=0, description="Page number (starts at 0)")
    ) -> List[CustomerResult]:
        """Get a paginated list of customers/third parties."""
        client = _require_client()
            
        result = await client.get_customers(limit=limit, page=page)
        return [CustomerResult(**item) for item in result]

    @mcp.tool()
    async def search_customers(
        query: str = Field(..., description="Search term for name or alias"),
        limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    ) -> List[CustomerResult]:
        """Search customers by name or alias."""
        client = _require_client()
            
        query_sanitized = _sanitize_search(query)
        sqlfilters = f"((t.nom:like:'%{query_sanitized}%') or (t.name_alias:like:'%{query_sanitized}%'))"
        
        try:
            result = await client.search_customers(sqlfilters=sqlfilters, limit=limit)
            return [CustomerResult(**item) for item in result]
        except DolibarrAPIError as e:
            raise RuntimeError(f"Dolibarr API Error: {e.message}")

    @mcp.tool()
    async def get_customer_by_id(
        customer_id: int = Field(..., description="Customer ID")
    ) -> CustomerResult:
        """Get details of a specific customer."""
        client = _require_client()
            
        result = await client.get_customer_by_id(customer_id)
        return CustomerResult(**result)

    @mcp.tool()
    async def create_customer(
        name: str = Field(..., description="Customer name"),
        client_type: int = Field(1, description="Client type (1=Customer, 2=Prospect, 3=Both)"),
        email: Optional[str] = Field(None, description="Email address"),
        phone: Optional[str] = Field(None, description="Phone number"),
        address: Optional[str] = Field(None, description="Address"),
        town: Optional[str] = Field(None, description="City/Town"),
        zip_code: Optional[str] = Field(None, description="Postal code"),
        country_id: int = Field(1, description="Country ID (default: 1)")
    ) -> int:
        """Create a new customer/third party."""
        client = _require_client()
            
        payload = {
            "name": name,
            "client": client_type,
            "code_client": -1,  # Auto-generate code
            "country_id": country_id
        }
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if address:
            payload["address"] = address
        if town:
            payload["town"] = town
        if zip_code:
            payload["zip"] = zip_code
                
        return await client.create_customer(payload)

    @mcp.tool()
    async def update_customer(
        customer_id: int = Field(..., description="Customer ID to update"),
        name: Optional[str] = Field(None, description="Customer name"),
        email: Optional[str] = Field(None, description="Email address"),
        phone: Optional[str] = Field(None, description="Phone number"),
        address: Optional[str] = Field(None, description="Address"),
        town: Optional[str] = Field(None, description="City/Town"),
        zip_code: Optional[str] = Field(None, description="Postal code")
    ) -> int:
        """Update an existing customer."""
        client = _require_client()
            
        payload = {}
        if name:
            payload["name"] = name
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if address:
            payload["address"] = address
        if town:
            payload["town"] = town
        if zip_code:
            payload["zip"] = zip_code
                
        if not payload:
            return customer_id
                
        return await client.update_customer(customer_id, payload)
