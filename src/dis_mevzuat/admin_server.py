from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .config import Settings
from .service import ComplianceService, utc_now


settings = Settings.from_env()
service = ComplianceService(settings)
mcp = FastMCP(
    "Türkiye Sağlık Turizmi Mevzuat — Local Admin",
    instructions=(
        "Yalnız güvenilir yerel yönetim için kaynakları önizler, açık insan onayıyla "
        "aktif eder ve eski sürümü arşivler. Bu sunucuyu internete açmayın."
    ),
)

STAGE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True
)
MUTATE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
)
ARCHIVE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False
)


@mcp.tool(annotations=STAGE)
async def preview_source(
    url: Annotated[str, Field(description="Eklenecek resmî HTTPS web/PDF bağlantısı")],
    institution: Annotated[str, Field(description="Kaynağı yayımlayan kurum")],
    source_type: Annotated[str, Field(description="Kaynak türü")],
    title: str | None = None,
    publication_date: str | None = None,
    effective_date: str | None = None,
    jurisdiction: str = "TR",
    category: str = "healthcare",
    subcategory: str | None = None,
    version: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """URL'yi SSRF ve boyut kontrolleriyle indirip insan onayı için staging'e alır."""
    return await service.preview_url(
        url,
        institution,
        source_type,
        title,
        publication_date,
        effective_date,
        jurisdiction=jurisdiction,
        category=category,
        subcategory=subcategory,
        version=version,
        tags=tags,
    )


@mcp.tool(annotations=MUTATE)
def preview_text_source(
    text: Annotated[str, Field(min_length=80, description="Eklenecek resmî kaynak metni")],
    title: str,
    institution: str,
    source_type: str,
    official_url: str | None = None,
    publication_date: str | None = None,
    effective_date: str | None = None,
    jurisdiction: str = "TR",
    category: str = "healthcare",
    subcategory: str | None = None,
    version: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Yapıştırılmış resmî metni doğrudan yayımlamadan staging'e alır."""
    return service.preview_text(
        text,
        title,
        institution,
        source_type,
        official_url,
        publication_date,
        effective_date,
        jurisdiction=jurisdiction,
        category=category,
        subcategory=subcategory,
        version=version,
        tags=tags,
    )


@mcp.tool(annotations=MUTATE)
async def approve_source(stage_id: Annotated[str, Field(description="Onaylanacak stage_id")]) -> dict:
    """İnsan tarafından kontrol edilmiş staging kaydını indeksler ve önceki sürümü arşivler."""
    return await service.approve_stage(stage_id)


@mcp.tool(annotations=STAGE)
async def check_source_update(source_id: str) -> dict:
    """Resmî URL'de hash değişikliği arar; değişikliği onaysız yayımlamaz."""
    return await service.refresh_source(source_id)


@mcp.tool(annotations=ARCHIVE)
def archive_source(source_id: str) -> dict:
    """Kaynağı silmeden aktif arama havuzundan arşive taşır."""
    changed = service.db.archive_source(source_id, utc_now())
    return {"source_id": source_id, "archived": changed}
