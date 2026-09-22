# Home Server operasyonu

Kanonik Home Server stack:

```text
/home/yigit/Documents/Codex/2026-09-17/ama-bu-lenovo-laptopu-7-24/outputs/home-server-stack
```

Servis `home-server-backend` ağına bağlanır ve mevcut remotely managed
`lenovo-home-server` Cloudflare Tunnel tarafından container adı üzerinden
erişilir. Router/modem portu açılmaz.

## Deploy

Repository kökünde:

```bash
pytest
docker compose -f compose.yaml -f compose.home-server.yaml up -d --build dis-mevzuat
curl http://127.0.0.1:8000/readyz
python scripts/mcp_smoke.py http://127.0.0.1:8000/mcp
```

Tunnel published-application eşlemesi:

```text
mevzuat.sorgunbogaz.com -> http://health-tourism-regulations-mcp:8000
```

## Update

```bash
git pull --ff-only
./scripts/update.sh
```

`update.sh` ve `restore.sh`, `home-server-backend` ağı mevcutsa Home Server
Compose overlay'ini otomatik kullanır.

## Backup ve restore

```bash
./scripts/backup.sh
./scripts/restore.sh /path/to/backup-directory
```

Restore kullanıcıdan `RESTORE` onayı ister. Production güncellemesinden önce
backup dizininin sunucu dışına kopyalandığını doğrulayın.

## Health

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
curl https://mevzuat.sorgunbogaz.com/readyz
```

## Rollback

1. Önceki çalışan Git commit'ine ayrı bir worktree veya checkout hazırlayın.
2. `docker compose -f compose.yaml -f compose.home-server.yaml up -d --build dis-mevzuat`
   ile yalnız bu servisi rebuild edin.
3. Database değiştiyse doğrulanmış backup'ı `scripts/restore.sh` ile geri alın.
4. Local ve public `readyz` ile MCP smoke testini tekrar çalıştırın.

Başka Home Server container, secret, database veya route'u değiştirmeyin.
