#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root_dir"
compose=(docker compose -f compose.yaml)
if docker network inspect home-server-backend >/dev/null 2>&1; then
  compose+=(-f compose.home-server.yaml)
fi
git pull --ff-only
"${compose[@]}" up -d --build dis-mevzuat
base_url=${DM_PUBLIC_BASE_URL:-http://127.0.0.1:${DM_PORT:-8000}}
curl --fail --silent --show-error "$base_url/readyz"
echo
