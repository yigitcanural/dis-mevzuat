from __future__ import annotations

import asyncio
import io
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from .models import ExtractedSource


class SourceError(ValueError):
    pass


def _validate_public_url(url: str, allowed_domains: tuple[str, ...] = ()) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SourceError("Yalnızca geçerli http/https bağlantıları kabul edilir.")
    host = parsed.hostname.lower()
    if parsed.username or parsed.password:
        raise SourceError("Kullanıcı bilgisi içeren kaynak bağlantıları kabul edilmez.")
    if parsed.port not in {None, 80, 443}:
        raise SourceError("Kaynak bağlantısı yalnız standart HTTP/HTTPS portlarını kullanabilir.")
    if host in {"localhost", "localhost.localdomain"}:
        raise SourceError("Yerel adreslerden kaynak alınamaz.")
    if allowed_domains and not any(
        host == domain or host.endswith(f".{domain}") for domain in allowed_domains
    ):
        raise SourceError("Kaynak alan adı yapılandırılmış resmî kurum allowlist'inde değil.")
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise SourceError(f"Kaynak alan adı çözümlenemedi: {host}") from exc
    for item in addresses:
        address = ipaddress.ip_address(item[4][0])
        if not address.is_global:
            raise SourceError("Özel, yerel veya ayrılmış ağ adreslerinden kaynak alınamaz.")


def _extract_pdf(data: bytes) -> tuple[str, dict]:
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise SourceError("PDF güvenli biçimde ayrıştırılamadı.") from exc
    if len(reader.pages) > 1000:
        raise SourceError("PDF izin verilen 1000 sayfa sınırını aşıyor.")
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n\n".join(pages).strip()
    if not text:
        raise SourceError(
            "PDF metni çıkarılamadı. Bu belge taranmış olabilir; OCR desteği gerekir."
        )
    return text, {"page_count": len(reader.pages)}


def _extract_html(data: bytes, encoding: str | None) -> tuple[str, str | None, dict]:
    soup = BeautifulSoup(data, "html.parser", from_encoding=encoding)
    # Bazı kamu siteleri (ASP.NET) tüm sayfayı tek bir <form> içine koyar. Formu
    # kaldırmak ana metni de yok edeceği için yalnız etkileşimli alanları temizleriz.
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "svg",
            "input",
            "button",
            "select",
            "textarea",
        ]
    ):
        tag.decompose()
    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    h1 = soup.find("h1")
    if h1 and h1.get_text(" ", strip=True):
        title = h1.get_text(" ", strip=True)
    # Kurum sitelerinin ortak içerik kapları. Birden fazla eşleşme olduğunda en
    # uzun okunabilir metni seçmek menü/sayaç gibi değişken sayfa kabuğunu dışarıda bırakır.
    candidates = []
    for selector in (
        "article",
        "main",
        ".page-content-body-hc",
        ".article-content",
        ".content-detail",
        ".news__detail-article",
        "div[style*='line-height:normal']",
        "div[style*='line-height: normal']",
    ):
        candidates.extend(soup.select(selector))
    candidates = [item for item in candidates if len(item.get_text(" ", strip=True)) >= 80]
    container = (
        max(candidates, key=lambda item: len(item.get_text(" ", strip=True)))
        if candidates
        else (soup.body or soup)
    )
    text = container.get_text("\n", strip=True)
    if not text:
        raise SourceError("Web sayfasından okunabilir metin çıkarılamadı.")
    return text, title, {}


async def extract_url(
    url: str,
    max_bytes: int,
    timeout: float,
    allowed_domains: tuple[str, ...] = (),
    transport: httpx.AsyncBaseTransport | None = None,
) -> ExtractedSource:
    headers = {
        "User-Agent": "HealthComplianceMCP/0.1 (+source retrieval; contact repository owner)"
    }
    current_url = url
    for redirect_count in range(6):
        # Her yönlendirmeyi yeni bir client açmadan önce doğrulamak, herkese açık
        # bir URL'nin sunucu içi bir adrese yönlendirilerek kullanılmasını engeller.
        _validate_public_url(current_url, allowed_domains)
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers=headers,
            transport=transport,
        ) as client:
            async with client.stream("GET", current_url) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise SourceError("Kaynak geçersiz bir yönlendirme yanıtı verdi.")
                    if redirect_count == 5:
                        raise SourceError("Kaynak çok fazla kez yönlendirme yaptı.")
                    current_url = str(response.url.join(location))
                    continue

                response.raise_for_status()
                chunks: list[bytes] = []
                total = 0
                async for block in response.aiter_bytes():
                    total += len(block)
                    if total > max_bytes:
                        raise SourceError(
                            f"Kaynak izin verilen {max_bytes} bayt sınırını aşıyor."
                        )
                    chunks.append(block)
                data = b"".join(chunks)
                content_type = (
                    response.headers.get("content-type", "").split(";", 1)[0].lower()
                )
                final_url = str(response.url)
                encoding = response.encoding
                break
    else:  # pragma: no cover - döngü üstte kontrollü biçimde sonlanır
        raise SourceError("Kaynak indirilemedi.")

    is_pdf = content_type == "application/pdf" or final_url.lower().endswith(".pdf")
    if is_pdf:
        text, metadata = await asyncio.to_thread(_extract_pdf, data)
        return ExtractedSource(text, None, "application/pdf", final_url, data, metadata)
    text, title, metadata = await asyncio.to_thread(_extract_html, data, encoding)
    return ExtractedSource(text, title, content_type or "text/html", final_url, data, metadata)


def extract_local_file(path: Path) -> ExtractedSource:
    data = path.read_bytes()
    if path.suffix.lower() == ".pdf":
        text, metadata = _extract_pdf(data)
        return ExtractedSource(text, path.stem, "application/pdf", None, data, metadata)
    text = data.decode("utf-8")
    return ExtractedSource(text, path.stem, "text/plain", None, data, {})
