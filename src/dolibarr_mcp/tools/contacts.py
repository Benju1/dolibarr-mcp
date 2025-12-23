"""Contact tools for Dolibarr MCP Server."""

from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import ContactResult


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


def register_contact_tools(mcp: FastMCP) -> None:
    """Register all contact-related tools."""
    
    @mcp.tool()
    async def get_contacts(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of contacts"),
        page: int = Field(0, ge=0, description="Page number (starts at 0)"),
        customer_id: Optional[int] = Field(None, description="Filter by customer ID (socid)")
    ) -> List[ContactResult]:
        """Get a paginated list of contacts."""
        client = _require_client()
            
        sqlfilters = None
        if customer_id:
            sqlfilters = f"(t.socid:'{customer_id}')"
                
        result = await client.get_contacts(limit=limit, page=page, sqlfilters=sqlfilters)
        return [ContactResult(**item) for item in result]

    @mcp.tool()
    async def create_contact(
        lastname: str = Field(..., description="Last name"),
        firstname: str = Field(..., description="First name"),
        socid: int = Field(..., description="Associated customer ID"),
        email: Optional[str] = Field(None, description="Email address"),
        phone_pro: Optional[str] = Field(None, description="Professional phone"),
        poste: Optional[str] = Field(None, description="Job position")
    ) -> int:
        """Create a new contact."""
        client = _require_client()
            
        payload = {
            "lastname": lastname,
            "firstname": firstname,
            "socid": socid
        }
        if email:
            payload["email"] = email
        if phone_pro:
            payload["phone_pro"] = phone_pro
        if poste:
            payload["poste"] = poste
                
        return await client.create_contact(payload)
