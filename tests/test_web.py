import asyncio
from dataclasses import replace

import httpx
import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from dis_mevzuat.server import mcp, settings
from dis_mevzuat.web import PublicSecurityMiddleware


def make_app(max_request_bytes: int = 1_048_576, rate_limit_per_minute: int = 60):
    configured = replace(
        settings,
        max_request_bytes=max_request_bytes,
        rate_limit_per_minute=rate_limit_per_minute,
    )
    return mcp.http_app(
        path="/mcp",
        stateless_http=True,
        json_response=True,
        middleware=[Middleware(PublicSecurityMiddleware, settings=configured)],
    )


@pytest.mark.asyncio
async def test_health_policy_and_landing_routes():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=make_app()), base_url="http://test"
    ) as client:
        health = await client.get("/healthz")
        landing = await client.get("/")
        privacy = await client.get("/privacy")
        terms = await client.get("/terms")
        support = await client.get("/support")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert "incelemesi bekleniyor" in landing.text.lower()
    assert "kalıcı olarak kaydetmez" in privacy.text
    assert "hukuki danışmanlık" in terms.text.lower()
    assert "GitHub Issues" in support.text
    assert landing.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_request_size_limit_and_malformed_mcp_request():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=make_app(max_request_bytes=16)),
        base_url="http://test",
    ) as client:
        oversized = await client.post("/mcp", content=b"x" * 17)
    assert oversized.status_code == 413
    assert oversized.json()["error"] == "request_too_large"

    app = make_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            malformed = await client.post(
                "/mcp", content=b"not-json", headers={"content-type": "application/json"}
            )
    assert malformed.status_code in {400, 406}


@pytest.mark.asyncio
async def test_rate_limit_returns_429():
    app = make_app(rate_limit_per_minute=2)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/")).status_code == 200
        assert (await client.get("/privacy")).status_code == 200
        limited = await client.get("/terms")
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"


@pytest.mark.asyncio
async def test_request_timeout_returns_504():
    async def slow_endpoint(_):
        await asyncio.sleep(0.05)
        return JSONResponse({"status": "late"})

    configured = replace(settings, tool_timeout=0.01)
    app = Starlette(
        routes=[Route("/slow", slow_endpoint)],
        middleware=[Middleware(PublicSecurityMiddleware, settings=configured)],
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/slow")
    assert response.status_code == 504
    assert response.json()["error"] == "request_timeout"
