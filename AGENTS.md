# Project instructions

- This is a managed, public read-only remote MCP backed by SQLite FTS5 and optional embeddings.
- Preserve the `dis-mevzuat` package and CLI for compatibility; the product name is Türkiye Sağlık Turizmi Mevzuatı.
- Public tools live in `src/dis_mevzuat/server.py`. Never add source mutation, URL fetch, reindex or admin tools there.
- Admin tools live only in `src/dis_mevzuat/admin_server.py`; HTTP admin binding must remain loopback-only.
- Preserve the source lifecycle: fetch/parse/hash -> staging -> explicit approval -> index -> archive prior version.
- Do not ingest patient photos, CRM data, patient files, medical records or other private clinical data.
- Primary source order: Resmî Gazete, Sağlık Bakanlığı, KVKK, USHAŞ/HealthTürkiye, other official primary institutions.
- Run `.venv/bin/pytest -q`, Docker build, local health and `scripts/mcp_smoke.py` before deployment.
- Home Server deployment uses `compose.yaml` plus `compose.home-server.yaml` and joins the existing `home-server-backend` network. Do not modify or restart unrelated Home Server services.
- Public hostname is `mevzuat.sorgunbogaz.com`; Cloudflare Tunnel origin is `http://health-tourism-regulations-mcp:8000`. Never open router ports.
- Backup before production changes that may touch the database. Use only project-specific files when staging commits.
- Keep privacy/terms/submission text aligned with actual logging, embedding and Cloudflare settings.
- Production completion order: tests -> backup -> build/deploy this service -> local health/smoke -> public health/smoke -> commit/push.
