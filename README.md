# Dolibarr MCP Server

Dolibarr MCP is a lean Model Context Protocol (MCP) server that surfaces the most
useful Dolibarr ERP/CRM operations to AI copilots. The repository now mirrors the
clean layout of [`prestashop-mcp`](https://github.com/latinogino/prestashop-mcp):
a single production-ready server, a concise async HTTP client, and a
self-contained documentation bundle.

## Documentation

All user and contributor guides live in [`docs/`](docs/README.md):

- [Quickstart](docs/quickstart.md) – installation and first run instructions for Linux, macOS, and Windows
- [Configuration](docs/configuration.md) – environment variables and secrets consumed by the server
- [Development](docs/development.md) – test workflow, linting, and Docker helpers
- [API Reference](docs/api-reference.md) – Dolibarr REST resources and corresponding MCP tools

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/dolibarr_mcp/` | MCP server implementation, async Dolibarr client, configuration helpers, and CLI entry point |
| `tests/` | Pytest-based automated test-suite covering configuration, client behaviour, and MCP tool registration |
| `docs/` | Markdown documentation mirroring the structure used by `prestashop-mcp` |
| `docker/` | Optional container assets for local experimentation or deployment |

## Installation

### Linux / macOS

```bash
git clone https://github.com/latinogino/dolibarr-mcp.git
cd dolibarr-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Install development extras (pytest, formatting, type-checking) when needed:

```bash
pip install -e '.[dev]'
```

### Windows (Visual Studio `vsenv`)

1. Launch the **x64 Native Tools Command Prompt for VS** or **Developer PowerShell for VS** (`vsenv`).
2. Create a virtual environment: `py -3 -m venv .venv`.
3. Activate it: `call .venv\\Scripts\\activate.bat` (Command Prompt) or `.\.venv\\Scripts\\Activate.ps1` (PowerShell).
4. Install the package: `pip install -e .`.
5. Install development extras when required: `pip install -e .[dev]` (PowerShell requires escaping brackets: ``pip install -e .`[dev`]``).

## Configuration

Set the following environment variables (they may live in a `.env` file):

- `DOLIBARR_URL` – Dolibarr API endpoint, e.g. `https://example.com/api/index.php`
- `DOLIBARR_API_KEY` – personal Dolibarr API token
- `LOG_LEVEL` – optional logging verbosity (defaults to `INFO`)

[`Config`](src/dolibarr_mcp/config.py) is built with `pydantic-settings` and supports loading from the environment, `.env` files, and CLI overrides. See the [configuration guide](docs/configuration.md) for a full matrix and troubleshooting tips.

## Running the server

Dolibarr MCP communicates with hosts over STDIO. Once configured, launch the server with:

```bash
python -m dolibarr_mcp.cli serve
```

You can validate credentials and connectivity using the built-in test command before wiring it into a host:

```bash
python -m dolibarr_mcp.cli test --url https://example.com/api/index.php --api-key YOUR_TOKEN
```

## Available tools

`dolibarr_mcp_server` registers MCP tools that map to common Dolibarr workflows:

- **System** – `test_connection`, `get_status`
- **Users** – CRUD helpers for Dolibarr users
- **Customers / Third Parties** – CRUD helpers for partners
- **Products** – CRUD helpers for product catalogue entries
- **Invoices** – CRUD helpers for invoices
- **Orders** – CRUD helpers for customer orders
- **Contacts** – CRUD helpers for contact records
- **Raw API access** – `dolibarr_raw_api` for direct REST operations

The async implementation in [`dolibarr_client.py`](src/dolibarr_mcp/dolibarr_client.py) handles request signing, pagination, and error handling. The [API reference](docs/api-reference.md) summarises the exposed REST coverage.

## Development workflow

- Run the test-suite with `pytest` (see [development docs](docs/development.md) for coverage flags and Docker helpers).
- Editable installs rely on the `src/` layout and expose the `dolibarr-mcp` console entry point.
- Contributions follow the same structure and documentation conventions as `prestashop-mcp` to keep the twin projects in sync.

## License

This project is released under the [MIT License](LICENSE).
