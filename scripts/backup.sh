#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
data_dir=${DM_DATA_DIR:-$root_dir/data}
backup_root=${BACKUP_DIR:-$root_dir/backups}
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
destination="$backup_root/$timestamp"

mkdir -p "$destination"
chmod 700 "$destination"

python3 - "$data_dir/dis_mevzuat.sqlite3" "$destination/dis_mevzuat.sqlite3" <<'PY'
import sqlite3
import sys

source = sqlite3.connect(sys.argv[1])
target = sqlite3.connect(sys.argv[2])
with target:
    source.backup(target)
source.close()
target.close()
PY

if [[ -d "$data_dir/raw" ]]; then
  tar -C "$data_dir" -czf "$destination/raw-sources.tar.gz" raw
fi
sha256sum "$destination"/* > "$destination/SHA256SUMS"
echo "Backup created: $destination"
