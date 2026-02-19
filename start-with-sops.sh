#!/usr/bin/env bash
# Startet den Dolibarr MCP-Server mit SOPS-entschlüsselten Secrets

set -euo pipefail

cd "$(dirname "$0")"

# Cleanup-Funktion
cleanup() {
    if [ -f .env.encrypted.backup ]; then
        mv .env.encrypted.backup .env
    fi
}
trap cleanup EXIT INT TERM

# Backup der verschlüsselten .env
cp .env .env.encrypted.backup

# Entschlüssele .env und ersetze sie
sops -d .env > .env.tmp
mv .env.tmp .env

# Starte den MCP-Server
# Hinweis: Script endet nicht bis Server beendet wird (STDIO-Transport)
uv run dolibarr-mcp serve
