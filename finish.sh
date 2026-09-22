#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$root_dir"

.venv/bin/pytest -q
docker compose build

if [[ "${1:-}" == "--deploy-home-server" ]]; then
  ./scripts/backup.sh
  docker compose -f compose.yaml -f compose.home-server.yaml up -d --build dis-mevzuat
  curl --fail --silent --show-error http://127.0.0.1:${DM_PORT:-8000}/readyz
  echo
  .venv/bin/python scripts/mcp_smoke.py http://127.0.0.1:${DM_PORT:-8000}/mcp
  if [[ -n "${DM_PUBLIC_BASE_URL:-}" ]]; then
    curl --fail --silent --show-error "$DM_PUBLIC_BASE_URL/readyz"
    echo
    .venv/bin/python scripts/mcp_smoke.py "$DM_PUBLIC_BASE_URL/mcp"
  fi
fi
