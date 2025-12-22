# Development

This project uses lightweight, professional tooling with a clean structure.
The code lives under `src/`, tests under `tests/` and optional Docker assets are
kept separate in `docker/`.

For architectural details, see [Architecture Documentation](developer/architecture.md).

## Install development dependencies

This project uses `uv` for dependency management.

```bash
# Install uv (if you haven't already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

## Run the test suite

Once your virtual environment is active:

```bash
pytest
```

To gather coverage metrics:

```bash
pytest --cov=src/dolibarr_mcp --cov-report=term-missing
```

If you encounter "command not found" errors, ensure your virtual environment is activated or run via python module:

```bash
python3 -m pytest
```

## Formatting and linting

The project intentionally avoids heavy linting dependencies. Follow the coding
style already present in the repository and run the test-suite before opening a
pull request.

## Docker tooling

Container assets live in `docker/`:

- `Dockerfile` – production-ready image for the MCP server
- `docker-compose.yml` – local stack that spins up Dolibarr together with the MCP server

Build and run the container locally with:

```bash
docker compose -f docker/docker-compose.yml up --build
```
