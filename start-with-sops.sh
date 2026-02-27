#!/usr/bin/env bash
# Startet den Dolibarr MCP-Server mit SOPS-entschlüsselten Secrets

set -euo pipefail

cd "$(dirname "$0")"

# Entschlüssele .env.enc → .env (überschreibt lokale .env)
sops -d .env.enc > .env

# Starte den MCP-Server
# Hinweis: Script endet nicht bis Server beendet wird (STDIO-Transport)
uv run dolibarr-mcp serve
