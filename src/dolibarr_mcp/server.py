"""FastMCP Server implementation for Dolibarr MCP.

This is the main entry point that initializes the MCP server and registers
all tools from the tools/ module.
"""

import sys
from typing import Optional
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .config import Config
from .dolibarr_client import DolibarrClient
from .state import set_client

# Tool modules
from .tools.proposals import register_proposal_tools
from .tools.projects import register_project_tools
from .tools.customers import register_customer_tools
from .tools.users import register_user_tools
from .tools.contacts import register_contact_tools
from .tools.invoices import register_invoice_tools
from .tools.orders import register_order_tools
from .tools.products import register_product_tools
from .tools.system import register_system_tools


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Manage server lifecycle and API client session."""
    client: Optional[DolibarrClient] = None
    
    # Load configuration
    try:
        config = Config()
        
        # Check if environment variables are set properly
        if not config.dolibarr_url or "your-dolibarr-instance" in config.dolibarr_url:
            raise RuntimeError("DOLIBARR_URL not configured properly")
        
        if not config.api_key or "your_dolibarr_api_key" in config.api_key:
            raise RuntimeError("DOLIBARR_API_KEY not configured properly")
            
        # Initialize client
        client = DolibarrClient(config)
        await client.start_session()
        set_client(client)
        
        # Test connection
        try:
            status = await client.get_status()
            version = status.get("dolibarr_version", "Unknown")
            print(f"✅ Connected to Dolibarr API (Version: {version})", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Connection test failed: {e}", file=sys.stderr)
            
        yield
        
    finally:
        # Cleanup
        if client:
            try:
                await client.close_session()
                print("👋 Dolibarr client session closed", file=sys.stderr)
            finally:
                set_client(None)


# Initialize FastMCP server
# Note: dependencies are configured in fastmcp.json (schema, transports, etc.)
mcp = FastMCP(
    "dolibarr-mcp",
    instructions="Professional Dolibarr ERP/CRM integration via Model Context Protocol",
    lifespan=server_lifespan
)


# Register all tool modules
register_proposal_tools(mcp)
register_project_tools(mcp)
register_customer_tools(mcp)
register_user_tools(mcp)
register_contact_tools(mcp)
register_invoice_tools(mcp)
register_order_tools(mcp)
register_product_tools(mcp)
register_system_tools(mcp)


if __name__ == "__main__":
    mcp.run()
