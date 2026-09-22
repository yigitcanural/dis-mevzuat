from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from .config import Settings
from .service import ComplianceService


async def _seed(manifest_path: Path) -> None:
    settings = Settings.from_env()
    service = ComplianceService(settings)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = 0
    for item in manifest["sources"]:
        print(f"Önizleniyor: {item['title']}")
        try:
            previous = service.db.get_active_source_by_url(item["url"])
            preview = await service.preview_url(
                item["url"],
                item["authority"],
                item["source_type"],
                item.get("title"),
                item.get("published_at"),
                item.get("effective_from"),
                supersedes_source_id=previous["id"] if previous else None,
                jurisdiction=item.get("jurisdiction", "TR"),
                category=item.get("category", "healthcare"),
                subcategory=item.get("subcategory"),
                version=item.get("version"),
                tags=item.get("tags", []),
            )
            result = await service.approve_stage(preview["stage_id"])
            label = "Zaten vardı" if result.get("duplicate") else "Eklendi"
            print(f"{label}: {result['source_id']} ({result['chunks_indexed']} yeni parça)")
        except Exception as exc:
            failures += 1
            print(f"HATA: {item['title']}: {exc}")
    if failures:
        raise SystemExit(f"{failures} kaynak eklenemedi; diğer kaynaklar işlendi.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Türkiye Sağlık Turizmi Mevzuat MCP")
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve = subparsers.add_parser("serve", help="MCP sunucusunu çalıştır")
    serve.add_argument("--transport", choices=["stdio", "http"], default=None)
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)
    admin = subparsers.add_parser(
        "serve-admin", help="Yalnız yerel kaynak yönetimi MCP sunucusunu çalıştır"
    )
    admin.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    admin.add_argument("--host", default="127.0.0.1")
    admin.add_argument("--port", type=int, default=8001)
    seed = subparsers.add_parser("seed", help="Kaynak manifestini indir ve indexle")
    seed.add_argument("manifest", type=Path)
    subparsers.add_parser("status", help="Index durumunu göster")
    args = parser.parse_args()

    if args.command == "seed":
        asyncio.run(_seed(args.manifest))
        return
    if args.command == "status":
        service = ComplianceService(Settings.from_env())
        print(json.dumps(service.db.stats(), ensure_ascii=False, indent=2))
        return

    if args.transport:
        os.environ["DM_TRANSPORT"] = args.transport
    if args.host:
        os.environ["DM_HOST"] = args.host
    if args.port:
        os.environ["DM_PORT"] = str(args.port)
    if args.command == "serve-admin":
        if args.transport == "http" and args.host not in {"127.0.0.1", "::1", "localhost"}:
            parser.error("Admin HTTP sunucusu yalnız loopback adresine bağlanabilir.")
        from .admin_server import mcp as admin_mcp

        if args.transport == "http":
            admin_mcp.run(
                transport="http",
                host=args.host,
                port=args.port,
                path="/mcp",
                stateless_http=True,
                json_response=True,
                uvicorn_config={"access_log": False},
            )
        else:
            admin_mcp.run()
        return

    from .server import mcp, settings

    if settings.transport == "http":
        from starlette.middleware import Middleware

        from .web import PublicSecurityMiddleware

        mcp.run(
            transport="http",
            host=settings.host,
            port=settings.port,
            path="/mcp",
            stateless_http=True,
            json_response=True,
            middleware=[Middleware(PublicSecurityMiddleware, settings=settings)],
            allowed_hosts=list(settings.allowed_hosts) or None,
            uvicorn_config={"access_log": False},
        )
    else:
        mcp.run()
