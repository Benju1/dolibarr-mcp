"""System tools for Dolibarr MCP Server."""

from typing import Any, Dict

from fastmcp import FastMCP
from pydantic import Field

from ..dolibarr_client import DolibarrClient


def _require_client() -> DolibarrClient:
    from ..state import get_client
    return get_client()


def register_system_tools(mcp: FastMCP) -> None:
    """Register all system-related tools."""
    
    @mcp.tool()
    async def get_status() -> Dict[str, Any]:
        """Get Dolibarr system status and version information."""
        client = _require_client()
            
        return await client.get_status()
