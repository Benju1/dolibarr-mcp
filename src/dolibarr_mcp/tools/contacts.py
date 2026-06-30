"""Contact tools for Dolibarr MCP Server."""

from typing import Any, Dict, List, Optional

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
    async def get_contact_by_id(
        contact_id: int = Field(..., description="Contact ID"),
    ) -> ContactResult:
        """Get details of a specific contact."""
        client = _require_client()
        result = await client.get_contact_by_id(contact_id)
        return ContactResult(**result)

    @mcp.tool()
    async def create_contact(
        lastname: str = Field(..., description="Last name"),
        firstname: str = Field(..., description="First name"),
        socid: int = Field(..., description="Associated customer ID"),
        email: Optional[str] = Field(None, description="Email address"),
        phone_pro: Optional[str] = Field(None, description="Professional phone"),
        phone_mobile: Optional[str] = Field(None, description="Mobile phone"),
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
        if phone_mobile:
            payload["phone_mobile"] = phone_mobile
        if poste:
            payload["poste"] = poste

        return await client.create_contact(payload)

    @mcp.tool()
    async def update_contact(
        contact_id: int = Field(..., description="Contact ID to update"),
        lastname: Optional[str] = Field(None, description="Last name"),
        firstname: Optional[str] = Field(None, description="First name"),
        email: Optional[str] = Field(None, description="Email address"),
        phone_pro: Optional[str] = Field(None, description="Professional phone"),
        phone_mobile: Optional[str] = Field(None, description="Mobile phone"),
        poste: Optional[str] = Field(None, description="Job position"),
        socid: Optional[int] = Field(None, description="Associated customer ID"),
    ) -> ContactResult:
        """Update an existing contact. Only provided fields are changed."""
        client = _require_client()

        payload = {}
        if lastname is not None:
            payload["lastname"] = lastname
        if firstname is not None:
            payload["firstname"] = firstname
        if email is not None:
            payload["email"] = email
        if phone_pro is not None:
            payload["phone_pro"] = phone_pro
        if phone_mobile is not None:
            payload["phone_mobile"] = phone_mobile
        if poste is not None:
            payload["poste"] = poste
        if socid is not None:
            payload["socid"] = socid

        if payload:
            await client.update_contact(contact_id, payload)

        result = await client.get_contact_by_id(contact_id)
        return ContactResult(**result)

    @mcp.tool()
    async def delete_contact(
        contact_id: int = Field(..., description="Contact ID to delete"),
    ) -> Dict[str, Any]:
        """Delete a contact. Returns confirmation."""
        client = _require_client()
        await client.delete_contact(contact_id)
        return {"status": "deleted", "contact_id": contact_id}
