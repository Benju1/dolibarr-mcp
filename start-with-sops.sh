#!/usr/bin/env bash
# Startet den Dolibarr MCP-Server mit SOPS-entschlüsselten Secrets

set -euo pipefail

cd "$(dirname "$0")"

# Prüfe ob .env.enc SOPS-verschlüsselt ist
if ! grep -q 'ENC\[AES256_GCM' .env.enc; then
  echo "ERROR: .env.enc is not SOPS-encrypted. Run: sops -e -i --input-type dotenv --output-type dotenv .env.enc" >&2
  exit 1
fi

# Entschlüssele .env.enc → .env (überschreibt lokale .env)
sops --input-type dotenv --output-type dotenv -d .env.enc > .env

# Starte den MCP-Server
# Hinweis: Script endet nicht bis Server beendet wird (STDIO-Transport)
uv run dolibarr-mcp serve
