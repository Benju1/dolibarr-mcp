"""Command line interface for Dolibarr MCP Server."""

import asyncio
import sys
from typing import Optional

import click

from .server import mcp
from .testing import test_connection as run_test_connection


@click.group()
@click.version_option(version="1.1.0", prog_name="dolibarr-mcp")
def cli():
    """Dolibarr MCP Server - Professional ERP integration via Model Context Protocol."""
    pass


@cli.command()
@click.option("--url", help="Dolibarr API URL")
@click.option("--api-key", help="Dolibarr API key")
def test(url: Optional[str], api_key: Optional[str]):
    """Test the connection to Dolibarr API."""
    exit_code = run_test_connection(url=url, api_key=api_key)
    if exit_code != 0:
        sys.exit(exit_code)


@cli.command()
@click.option("--transport", default="stdio", type=click.Choice(["stdio", "http"]), help="Transport protocol")
@click.option("--host", default="0.0.0.0", help="Host to bind to (HTTP only)")
@click.option("--port", default=8000, help="Port to bind to (HTTP only)")
def serve(transport: str, host: str, port: int):
    """Start the Dolibarr MCP server."""
    if transport == "http":
        click.echo(f"🚀 Starting Dolibarr MCP server (Transport: {transport})")
        click.echo(f"📡 Listening on http://{host}:{port}")
        click.echo("🔧 Configure your environment variables in .env file")
    
    # Run the FastMCP server
    mcp.run(transport=transport, host=host, port=port)


@cli.command()
def version():
    """Show version information."""
    click.echo("Dolibarr MCP Server v1.1.0")
    click.echo("Professional ERP integration via Model Context Protocol")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
