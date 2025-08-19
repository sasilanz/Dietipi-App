#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "▶ git pull"; git pull
[ -f web/.env ] || { echo "❌ web/.env fehlt"; exit 1; }
echo "▶ compose check"; docker compose -f compose.yml -f compose.prod.yml config >/dev/null
echo "▶ deploy"; docker compose -f compose.yml -f compose.prod.yml up -d --build
echo "✅ done"; docker compose -f compose.yml -f compose.prod.yml ps
