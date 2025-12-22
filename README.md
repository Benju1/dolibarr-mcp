# Dolibarr MCP Server

Dolibarr MCP delivers a Model Context Protocol (MCP) interface for the Dolibarr
ERP/CRM—an async API client, a production-ready STDIO server, and comprehensive
documentation optimized for Dolibarr workflows.

**Design Philosophy:** This server implements **specialized search tools** (e.g., `search_products_by_ref`, `resolve_product_ref`) optimized specifically for Dolibarr instead of a single unified `get_` tool. This design choice ensures efficient server-side filtering via Dolibarr's SQL API, preventing the agent from accidentally loading thousands of records and exceeding context limits.

Claude Desktop and other MCP-aware tools can use the server to
manage customers, products, invoices, orders, and contacts in a Dolibarr
instance.

Consult the bundled [documentation index](docs/README.md) for deep dives into
configuration, API coverage, and contributor workflows.

## ✨ Features

- **Full ERP coverage** – CRUD tools for users, customers, products, proposals, invoices,
  orders, contacts, projects, and raw API access.
- **Advanced Search** – Server-side filtering for products, customers, and projects to minimize token usage and costs.
- **Async/await HTTP client** – Efficient Dolibarr API wrapper with structured
  error handling.
- **Ready for MCP hosts** – STDIO transport compatible with Claude Desktop out
  of the box.
- **Beta status** – Active development with comprehensive test coverage. Ready for experimentation and feedback.

## ✅ Prerequisites

- Python 3.10 or newer.
- Access to a Dolibarr installation with the REST API enabled and a personal API
  token.

## 📦 Installation

### Using uv (Recommended)

This project uses `uv` for dependency management.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/latinogino/dolibarr-mcp.git
cd dolibarr-mcp

# Install dependencies
uv sync
```

### Docker (optional)

```bash
docker compose up -d
# or
docker build -t dolibarr-mcp .
docker run -d \
  -e DOLIBARR_URL=https://your-dolibarr.example.com/api/index.php \
  -e DOLIBARR_API_KEY=YOUR_API_KEY \
  dolibarr-mcp
```

## ⚙️ Configuration

### Environment variables

The server reads configuration from the environment or a `.env` file. Both
`DOLIBARR_URL` and `DOLIBARR_SHOP_URL` are accepted for the base API address.

| Variable | Description |
| --- | --- |
| `DOLIBARR_URL` / `DOLIBARR_SHOP_URL` | Base Dolibarr API endpoint, e.g. `https://example.com/api/index.php`. Trailing slashes are handled automatically. |
| `DOLIBARR_API_KEY` | Personal Dolibarr API token. |
| `LOG_LEVEL` | Optional logging verbosity (`INFO`, `DEBUG`, `WARNING`, …). |

Example `.env`:

```env
DOLIBARR_URL=https://your-dolibarr.example.com/api/index.php
DOLIBARR_API_KEY=YOUR_API_KEY
LOG_LEVEL=INFO
```

### Claude Desktop configuration

Add the following block to `claude_desktop_config.json`, replacing the paths and
credentials with your own values:

```json
{
  "mcpServers": {
    "dolibarr": {
      "command": "uv",
      "args": ["run", "dolibarr-mcp", "serve"],
      "cwd": "/absolute/path/to/dolibarr-mcp",
      "env": {
        "DOLIBARR_SHOP_URL": "https://your-dolibarr.example.com",
        "DOLIBARR_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

Restart Claude Desktop after saving the configuration.

## ▶️ Usage

### Start the MCP server

The server communicates over STDIO by default:

```bash
uv run dolibarr-mcp serve
```

You can also start an HTTP server (SSE):

```bash
uv run dolibarr-mcp serve --transport http --port 8000
```

### Test the Dolibarr credentials

Use the CLI to test connectivity:

```bash
uv run dolibarr-mcp test --url https://your-dolibarr.example.com/api/index.php --api-key YOUR_API_KEY
```

When the environment variables are already set, omit the overrides and run
`uv run dolibarr-mcp test`.

## 🧪 Development

- Run the test-suite with `pytest` (see [`docs/development.md`](docs/development.md)
  for coverage options and Docker helpers).
- Editable installs rely on the `src/` layout and expose the `dolibarr-mcp`
  console entry point for backwards compatibility.

## 📄 License

Released under the [MIT License](LICENSE).

