"""
Dolibarr MCP Server Package

Professional Model Context Protocol server for complete Dolibarr ERP/CRM management.
"""

__version__ = "1.0.0"
__author__ = "Dolibarr MCP Team"

from .dolibarr_client import DolibarrClient
from .dolibarr_mcp_server import DolibarrMCPServer
from .config import Config

__all__ = [
    "DolibarrClient",
    "DolibarrMCPServer",
    "Config",
]
