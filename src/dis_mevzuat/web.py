from __future__ import annotations

import asyncio
import hashlib
import html
import os
import time
from collections import defaultdict, deque
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response

from .config import Settings
from .service import ComplianceService, utc_now


class PublicSecurityMiddleware(BaseHTTPMiddleware):
    """Small origin-side guard; Cloudflare remains the outer traffic boundary."""

    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._rate_limit_salt = os.urandom(32)

    def _rate_limit_key(self, request: Request) -> str:
        address = request.headers.get("cf-connecting-ip")
        if not address:
            address = request.client.host if request.client else "unknown"
        return hashlib.blake2s(
            address.encode("utf-8", errors="replace"),
            key=self._rate_limit_salt,
            digest_size=16,
        ).hexdigest()

    def _expire_rate_limit_key(self, key: str) -> None:
        bucket = self._requests.get(key)
        if bucket is None:
            return
        cutoff = time.monotonic() - 60
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if not bucket:
            self._requests.pop(key, None)
            return
        asyncio.get_running_loop().call_later(61, self._expire_rate_limit_key, key)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.settings.max_request_bytes:
                    return self._secure(
                        JSONResponse({"error": "request_too_large"}, status_code=413), request
                    )
            except ValueError:
                return self._secure(
                    JSONResponse({"error": "invalid_content_length"}, status_code=400), request
                )

        if request.url.path not in {"/healthz", "/readyz"}:
            now = time.monotonic()
            key = self._rate_limit_key(request)
            is_new_key = key not in self._requests
            bucket = self._requests[key]
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= self.settings.rate_limit_per_minute:
                response = JSONResponse(
                    {"error": "rate_limit_exceeded", "retry_after_seconds": 60},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
                return self._secure(response, request)
            bucket.append(now)
            if is_new_key:
                asyncio.get_running_loop().call_later(
                    61, self._expire_rate_limit_key, key
                )

        try:
            async with asyncio.timeout(self.settings.tool_timeout):
                response = await call_next(request)
        except TimeoutError:
            response = JSONResponse({"error": "request_timeout"}, status_code=504)
        return self._secure(response, request)

    @staticmethod
    def _secure(response: Response, request: Request) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        )
        if request.headers.get("x-forwarded-proto") == "https":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        if request.url.path in {"/mcp", "/healthz", "/readyz"}:
            response.headers.setdefault("Cache-Control", "no-store")
        return response


def middleware_options(settings: Settings) -> dict:
    return {"settings": settings}


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
:root{{--ink:#13211b;--muted:#52645c;--accent:#087f5b;--paper:#f7faf8;--line:#dbe8e1}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:17px/1.65 system-ui,sans-serif}}
main{{max-width:900px;margin:auto;padding:64px 24px}} h1{{font-size:clamp(2rem,6vw,4.5rem);line-height:1.03;letter-spacing:-.04em}}
h2{{margin-top:2.4rem}} p,li{{max-width:74ch}} .eyebrow{{color:var(--accent);font-weight:700;text-transform:uppercase;letter-spacing:.08em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;margin:32px 0}}
.card{{background:white;border:1px solid var(--line);border-radius:16px;padding:22px}} .pending{{color:#8a5a00}}
a{{color:var(--accent)}} code{{background:#eaf2ee;padding:.15em .35em;border-radius:5px}} nav a{{margin-right:18px}}
</style></head><body><main>{body}<hr><nav><a href="/">Ana sayfa</a><a href="/privacy">Gizlilik</a><a href="/terms">Koşullar</a><a href="/support">Destek</a></nav></main></body></html>"""


def register_public_routes(mcp, service: ComplianceService, settings: Settings) -> None:
    base = settings.public_base_url or "bu sunucunun HTTPS adresi"

    @mcp.custom_route("/", methods=["GET"], include_in_schema=False)
    async def landing(_: Request) -> Response:
        mcp_url = f"{base}/mcp" if base.startswith("https://") else "/mcp"
        body = f"""
<p class="eyebrow">Resmî kaynaklara dayalı araştırma altyapısı</p>
<h1>Türkiye Sağlık Turizmi Mevzuatı</h1>
<p>Sağlık turizmi, sağlık hizmetlerinde tanıtım, sosyal medya ve mahremiyet kurallarını AI araçlarında kaynaklarıyla araştırın.</p>
<div class="grid">
<section class="card"><h2>ChatGPT</h2><p class="pending">Plugin Directory incelemesi bekleniyor.</p></section>
<section class="card"><h2>Claude ve MCP</h2><p>Provider-neutral remote MCP adresi: <code>{html.escape(mcp_url)}</code></p></section>
<section class="card"><h2>Kendi sunucunda</h2><p>MIT lisanslı backend'i Docker veya Python ile çalıştırın.</p></section>
</div>
<p>Servis bilgi ve araştırma amaçlıdır; hukuki danışmanlık, yayın izni, tıbbi teşhis veya tedavi planı vermez.</p>"""
        return HTMLResponse(_layout("Türkiye Sağlık Turizmi Mevzuatı", body))

    @mcp.custom_route("/privacy", methods=["GET"], include_in_schema=False)
    async def privacy(_: Request) -> Response:
        embedding = (
            "Semantik arama etkin olduğunda sorgu metni yapılandırılan embedding sağlayıcısına gönderilir."
            if service.embedder.enabled
            else "Bu production yapılandırmasında semantik arama kapalıdır; sorgular bir embedding sağlayıcısına gönderilmez."
        )
        body = f"""<h1>Gizlilik Politikası</h1><p>Son güncelleme: 22 Eylül 2026</p>
<h2>Servis ne yapar?</h2><p>Bu read-only servis, kamuya açık mevzuat indeksinde arama yapar ve kaynak kanıtı döndürür.</p>
<h2>Sorgular ve loglar</h2><p>Uygulama sorgu içeriğini veya MCP sonuçlarını kalıcı olarak kaydetmez. Uygulama erişim logları kapalıdır. IP adresi hız sınırlama anahtarı üretildikten sonra ham biçimde tutulmaz; süreç başına rastgele anahtarla türetilen geçici değer yaklaşık bir dakika içinde bellekten silinir. Uygulama düzeyindeki log saklama süresi {settings.log_retention_days} gündür.</p>
<h2>Altyapı</h2><p>HTTPS ve trafik koruması için Cloudflare Tunnel kullanılabilir. Cloudflare ağ metadatasını kendi sözleşme ve politikalarına göre işleyebilir; Cloudflare tarafındaki gerçek saklama süresi bu uygulama tarafından belirlenmez.</p>
<h2>Semantik arama</h2><p>{html.escape(embedding)} Sağlayıcı etkinleştirilirse seçilen sağlayıcı ve veri işleme koşulları sunucu işletmecisinin sorumluluğundadır.</p>
<h2>Hasta verisi</h2><p>Hasta fotoğrafı, video, CRM kaydı, tıbbi dosya veya başka kişisel sağlık verisi göndermeyin. Bu veriler mevzuat indeksine eklenmez. Kişisel veriler satılmaz.</p>
<h2>İletişim</h2><p>Gizlilik soruları için <a href="https://github.com/yigitcanural/dis-mevzuat/issues">GitHub Issues</a> kullanın ve kişisel sağlık verisi paylaşmayın.</p>"""
        return HTMLResponse(_layout("Gizlilik Politikası", body))

    @mcp.custom_route("/terms", methods=["GET"], include_in_schema=False)
    async def terms(_: Request) -> Response:
        body = """<h1>Kullanım Koşulları</h1><p>Son güncelleme: 22 Eylül 2026</p>
<p>Servis yalnız bilgi ve araştırma amaçlıdır. Hukuki danışmanlık, tıbbi tavsiye, yayın izni veya uygunluk onayı vermez.</p>
<ul><li>Resmî kurumların güncel ve yayımlanmış metinleri her zaman esas alınmalıdır.</li>
<li>Kaynaklar ve yürürlük durumu zaman içinde değişebilir; kullanıcı tarih ve statü bilgisini doğrulamalıdır.</li>
<li>Nihai yayın, tedavi, veri işleme ve ticari kararların sorumluluğu kullanıcıya aittir.</li>
<li>Servisin kesintisiz, hatasız veya her konuyu eksiksiz kapsayacağı garanti edilmez.</li></ul>"""
        return HTMLResponse(_layout("Kullanım Koşulları", body))

    @mcp.custom_route("/support", methods=["GET"], include_in_schema=False)
    async def support(_: Request) -> Response:
        body = """<h1>Destek</h1><p>Hata bildirmek, kaynak güncelliğiyle ilgili uyarı yapmak veya özellik önermek için <a href="https://github.com/yigitcanural/dis-mevzuat/issues">GitHub Issues</a> kullanın.</p>
<p>Bildirimlere hasta verisi, kimlik bilgisi, API anahtarı veya başka bir secret eklemeyin.</p>"""
        return HTMLResponse(_layout("Destek", body))

    @mcp.custom_route("/healthz", methods=["GET"], include_in_schema=False)
    async def health(_: Request) -> Response:
        with service.db.connection() as conn:
            conn.execute("SELECT 1").fetchone()
        return JSONResponse({"status": "ok", "checked_at": utc_now()})

    @mcp.custom_route("/readyz", methods=["GET"], include_in_schema=False)
    async def ready(_: Request) -> Response:
        stats = service.db.stats()
        ready_state = stats["active_sources"] > 0 and stats["chunks"] > 0
        return JSONResponse(
            {"status": "ready" if ready_state else "not_ready", **stats},
            status_code=200 if ready_state else 503,
        )

    @mcp.custom_route(
        "/.well-known/openai-apps-challenge", methods=["GET"], include_in_schema=False
    )
    async def openai_challenge(_: Request) -> Response:
        if not settings.openai_challenge_token:
            return PlainTextResponse("not configured", status_code=404)
        return PlainTextResponse(settings.openai_challenge_token)
