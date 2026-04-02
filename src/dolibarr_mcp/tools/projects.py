"""Project tools for Dolibarr MCP Server."""

import re
from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import ProjectContactResult, ProjectSearchResult


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


def _sanitize_search(s: str) -> str:
    """Sanitize search input to prevent SQL injection."""
    s = s.strip()
    s = re.sub(r"[^0-9A-Za-z äöüÄÖÜß._\-@/+,&#()]", "", s)
    return s[:80]


def _build_usf_like_filter(field: str, value: str) -> str:
    """Build a Universal Search Filter (USF) like-filter.
    
    Format: (field:like:'%value%')
    See: docs/developer/DOLIBARR_USF_SYNTAX.md
    
    Args:
        field: Database field with table alias (e.g., 't.ref', 't.title')
        value: Search value (will be wrapped in wildcards)
    
    Returns:
        USF-formatted filter string
    """
    return f"({field}:like:'%{value}%')"


def _build_usf_eq_filter(field: str, value: int | str) -> str:
    """Build a Universal Search Filter (USF) equality filter.
    
    Format: (field:=:value)
    See: docs/developer/DOLIBARR_USF_SYNTAX.md
    
    Args:
        field: Database field with table alias (e.g., 't.fk_soc')
        value: Exact value (int or str, will not be quoted)
    
    Returns:
        USF-formatted filter string
    """
    return f"({field}:=:{value})"


def register_project_tools(mcp: FastMCP) -> None:
    """Register all project-related tools."""
    
    @mcp.tool()
    async def search_projects(
        query: Optional[str] = Field(None, description="Search term for project ref or title"),
        filter_customer_id: Optional[int] = Field(None, description="Filter by customer ID (fk_soc)"),
        limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    ) -> List[ProjectSearchResult]:
        """Search projects by reference, title, or customer.
        
        Uses Dolibarr Universal Search Filter (USF) syntax.
        See: docs/developer/DOLIBARR_USF_SYNTAX.md for filter syntax reference.
        
        Use filter_customer_id to find all projects of a specific customer.
        Can combine both query and filter_customer_id.
        """
        client = _require_client()

        filters = []
        
        if query:
            query_sanitized = _sanitize_search(query)
            # Build USF filters for ref and title searches
            filters.append(f"({_build_usf_like_filter('t.ref', query_sanitized)} or {_build_usf_like_filter('t.title', query_sanitized)})")
        
        if filter_customer_id:
            # Use fk_soc (foreign key to societe) with USF equality filter :=:
            filters.append(_build_usf_eq_filter("t.fk_soc", filter_customer_id))
        
        sqlfilters = " and ".join(filters) if filters else ""
        
        result = await client.search_projects(sqlfilters=sqlfilters, limit=limit)
        return [ProjectSearchResult(**item) for item in result]

    @mcp.tool()
    async def get_projects(
        limit: int = Field(100, ge=1, le=100, description="Maximum number of projects"),
        page: int = Field(0, ge=0, description="Page number (starts at 0)"),
        status: Optional[int] = Field(None, description="Project status filter")
    ) -> List[ProjectSearchResult]:
        """Get a paginated list of projects."""
        client = _require_client()
            
        result = await client.get_projects(limit=limit, page=page, status=status)
        return [ProjectSearchResult(**item) for item in result]

    @mcp.tool()
    async def get_project_by_id(
        project_id: int = Field(..., description="Exact numeric Dolibarr project ID")
    ) -> ProjectSearchResult:
        """Get details of a specific project."""
        client = _require_client()
            
        result = await client.get_project_by_id(project_id)
        return ProjectSearchResult(**result)

    @mcp.tool()
    async def create_project(
        title: str = Field(..., description="Project title"),
        ref: Optional[str] = Field(None, description="Project reference (auto-generated if empty)"),
        socid: Optional[int] = Field(None, description="Customer ID"),
        description: Optional[str] = Field(None, description="Project description"),
        status: int = Field(1, description="Initial status (0=Draft, 1=Open)")
    ) -> int:
        """Create a new project. Returns the new project ID."""
        client = _require_client()
            
        payload = {
            "title": title,
            "status": status
        }
        if ref:
            payload["ref"] = ref
        if socid:
            payload["socid"] = socid
        if description:
            payload["description"] = description
            
        return await client.create_project(payload)

    @mcp.tool()
    async def add_project_contact(
        project_id: int = Field(..., description="Project ID"),
        contact_id: int = Field(..., description="Contact ID (from get_contacts)"),
        type_contact: str = Field(..., description="Contact type code, e.g. 'PROJECTCONTRIBUTOR', 'PROJECTLEADER'"),
        source: str = Field(..., description="'internal' (Dolibarr user) or 'external' (third-party contact)")
    ) -> int:
        """Add a contact to a project. Returns the contact link ID."""
        client = _require_client()
        payload = {
            "fk_socpeople": contact_id,
            "type_contact": type_contact,
            "source": source,
        }
        return await client.add_project_contact(project_id, payload)

    @mcp.tool()
    async def get_project_contacts(
        project_id: int = Field(..., description="Project ID"),
    ) -> List[ProjectContactResult]:
        """Get all contacts assigned to a project."""
        client = _require_client()
        result = await client.get_project_contacts(project_id)
        return [ProjectContactResult(**item) for item in result]

    @mcp.tool()
    async def remove_project_contact(
        project_id: int = Field(..., description="Project ID"),
        contact_id: int = Field(..., description="Contact ID to remove"),
        type_contact: str = Field(..., description="Contact type code (e.g. 'PROJECTCONTRIBUTOR')"),
    ) -> bool:
        """Remove a contact from a project."""
        client = _require_client()
        await client.remove_project_contact(project_id, contact_id, type_contact)
        return True
