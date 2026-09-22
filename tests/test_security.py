import socket

import httpx
import pytest

from dis_mevzuat import extraction
from dis_mevzuat.extraction import SourceError, _extract_pdf, _validate_public_url


def _dns(address: str):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://localhost/admin",
        "https://user:pass@saglik.gov.tr/secret",
        "https://saglik.gov.tr:8443/source",
        "https://example.com/source",
    ],
)
def test_source_url_policy_rejects_unsafe_shapes(url, monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: _dns("8.8.8.8"))
    with pytest.raises(SourceError):
        _validate_public_url(url, ("saglik.gov.tr",))


def test_source_url_policy_rejects_private_dns(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: _dns("127.0.0.1"))
    with pytest.raises(SourceError, match="Özel"):
        _validate_public_url("https://www.saglik.gov.tr/source", ("saglik.gov.tr",))


def test_source_url_policy_accepts_allowlisted_public_subdomain(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: _dns("8.8.8.8"))
    _validate_public_url("https://antalya.saglik.gov.tr/source", ("saglik.gov.tr",))


def test_malformed_pdf_is_rejected():
    with pytest.raises(SourceError, match="ayrıştırılamadı"):
        _extract_pdf(b"not-a-pdf")


@pytest.mark.asyncio
async def test_oversized_source_is_rejected(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: _dns("8.8.8.8"))
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, headers={"content-type": "text/html"}, content=b"x" * 32
        )
    )
    with pytest.raises(SourceError, match="bayt sınırını"):
        await extraction.extract_url(
            "https://www.saglik.gov.tr/source",
            16,
            2,
            ("saglik.gov.tr",),
            transport,
        )


@pytest.mark.asyncio
async def test_redirect_to_private_address_is_revalidated(monkeypatch):
    checked = []

    def validate(url, allowed_domains=()):
        checked.append(url)
        if "127.0.0.1" in url:
            raise SourceError("Özel, yerel veya ayrılmış ağ adreslerinden kaynak alınamaz.")

    monkeypatch.setattr(extraction, "_validate_public_url", validate)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})
    )
    with pytest.raises(SourceError):
        await extraction.extract_url(
            "https://www.saglik.gov.tr/source",
            1000,
            2,
            ("saglik.gov.tr",),
            transport,
        )
    assert checked == [
        "https://www.saglik.gov.tr/source",
        "http://127.0.0.1/admin",
    ]
