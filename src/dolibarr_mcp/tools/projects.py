"""Project tools for Dolibarr MCP Server."""

import re
from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient
from ..models import ProjectSearchResult


def _require_client() -> DolibarrClient:
    from ..server import _get_client
    return _get_client()


def _sanitize_search(s: str) -> str:
    """Sanitize search input to prevent SQL injection."""
    s = s.strip()
    s = re.sub(r"[^0-9A-Za-z äöüÄÖÜß._\-@/+,&#()]", "", s)
    return s[:80]


def register_project_tools(mcp: FastMCP) -> None:
    """Register all project-related tools."""
    
    @mcp.tool()
    async def search_projects(
        query: Optional[str] = Field(None, description="Search term for project ref or title"),
        filter_customer_id: Optional[int] = Field(None, description="Filter by customer ID (socid)"),
        limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    ) -> List[ProjectSearchResult]:
        """Search projects by reference, title, or customer.
        
        Use filter_customer_id to find all projects of a specific customer.
        Can combine both query and filter_customer_id.
        """
        client = _require_client()

        filters = []
        
        if query:
            query_sanitized = _sanitize_search(query)
            filters.append(f"((t.ref=like:'%{query_sanitized}%') or (t.title=like:'%{query_sanitized}%'))")
        
        if filter_customer_id:
            filters.append(f"(t.socid={filter_customer_id})")
        
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
