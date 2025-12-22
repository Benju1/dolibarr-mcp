"""Global state management for Dolibarr MCP Server.

This module holds the singleton instance of the DolibarrClient to avoid
circular imports between the server module and tool modules.
"""

from typing import Optional
from .dolibarr_client import DolibarrClient

# Global client instance
_client: Optional[DolibarrClient] = None


def get_client() -> DolibarrClient:
    """Get the global client instance. Used by tool modules."""
    if not _client:
        raise RuntimeError("Server not initialized - client is not available")
    return _client


def set_client(client: Optional[DolibarrClient]) -> None:
    """Set the global client instance."""
    global _client
    _client = client
