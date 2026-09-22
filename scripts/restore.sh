#!/usr/bin/env bash
set -euo pipefail

[[ $# -eq 1 ]] || { echo "Usage: $0 /path/to/backup-directory" >&2; exit 2; }
backup_dir=$(realpath "$1")
root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
data_dir=${DM_DATA_DIR:-$root_dir/data}
cd "$root_dir"
compose=(docker compose -f compose.yaml)
if docker network inspect home-server-backend >/dev/null 2>&1; then
  compose+=(-f compose.home-server.yaml)
fi

sha256sum -c "$backup_dir/SHA256SUMS"
echo "This replaces the regulation database and raw-source archive in $data_dir."
read -r -p "Type RESTORE to continue: " answer
[[ "$answer" == "RESTORE" ]] || { echo "Cancelled."; exit 1; }

"${compose[@]}" stop dis-mevzuat 2>/dev/null || true
mkdir -p "$data_dir/raw" "$data_dir/staging"
cp "$backup_dir/dis_mevzuat.sqlite3" "$data_dir/dis_mevzuat.sqlite3"
if [[ -f "$backup_dir/raw-sources.tar.gz" ]]; then
  tar -C "$data_dir" -xzf "$backup_dir/raw-sources.tar.gz"
fi
"${compose[@]}" up -d dis-mevzuat
echo "Restore completed. Check /readyz before serving traffic."
