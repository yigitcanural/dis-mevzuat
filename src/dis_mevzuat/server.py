from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .config import Settings
from .service import ComplianceService, utc_now
from .web import register_public_routes


settings = Settings.from_env()
service = ComplianceService(settings)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

SERVER_INSTRUCTIONS = """
Bu read-only servis Türkiye sağlık turizmi, sağlık hizmetlerinde tanıtım ve
bilgilendirme, sosyal medya, fiyat/kampanya, hasta yorumu, before/after,
KVKK, hasta görseli/açık rıza ve sağlık turizmi yetkilendirmesi hakkında
resmî ve birincil kaynaklarda araştırma yapar.

Bir mevzuat sorusunda önce search_regulations ile dar sorgular çalıştırın;
gerekirse get_chunk veya get_source ile kritik metni doğrulayın. Kaynak
bulunmadan kesin sonuç üretmeyin. current kaynakları archive kaynaklardan
önde tutun, yayın/yürürlük/toplanma tarihlerini kontrol edin. Kaynaklar
çelişiyorsa veya farklı dönemlere aitse bunu açıkça söyleyin. Kaynakta açıkça
yazan metin ile model yorumunu birbirinden ayırın ve resmî URL'yi kanıt olarak
koruyun.

Bu servis hukuki danışmanlık veya yayın izni vermez; tıbbi teşhis koymaz ve
tedavi planlamaz. Hastadan veya kullanıcıdan hasta fotoğrafı, video, CRM
verisi, hasta dosyası ya da tıbbi kayıt istemeyin ve bunları bu mevzuat
indeksine eklemeyin.
""".strip()

mcp = FastMCP("Türkiye Sağlık Turizmi Mevzuat", instructions=SERVER_INSTRUCTIONS)


@mcp.tool(
    title="Mevzuatta ara",
    description=(
        "Onaylanmış Türkiye sağlık turizmi ve sağlık hizmetleri mevzuatında "
        "FTS5, etkinse semantik, ardından hibrit sıralamayla arama yapar. "
        "Önce bunu çağırın; sonuçtaki chunk_id ile get_chunk kullanarak kritik "
        "kanıtı doğrulayın. Varsayılan olarak yalnız güncel kaynakları döndürür."
    ),
    annotations=READ_ONLY,
    timeout=settings.tool_timeout,
)
async def search_regulations(
    query: Annotated[
        str,
        Field(
            min_length=2,
            max_length=500,
            description="Türkçe doğal dil veya dar mevzuat anahtar kelime sorgusu",
        ),
    ],
    top_k: Annotated[int, Field(ge=1, le=20, description="Döndürülecek en iyi sonuç")] = 8,
    source_type: Annotated[
        str | None, Field(max_length=100, description="İsteğe bağlı kaynak türü filtresi")
    ] = None,
    institution: Annotated[
        str | None, Field(max_length=160, description="İsteğe bağlı yayımlayan kurum filtresi")
    ] = None,
    current_only: Annotated[
        bool, Field(description="Yalnız current/aktif kaynaklarda ara")
    ] = True,
) -> dict:
    return await service.search(query, top_k, source_type, institution, current_only)


@mcp.tool(
    title="Kaynakları listele",
    description=(
        "İndeksteki kaynakların kurum, kategori, tarih, sürüm, current/archive "
        "durumu ve resmî URL künyelerini listeler; metin içi arama yapmaz."
    ),
    annotations=READ_ONLY,
    timeout=settings.tool_timeout,
)
def list_sources(
    status: Annotated[
        str | None, Field(description="active, archived veya tümü için null")
    ] = "active",
) -> dict:
    return service.list_sources(status)


@mcp.tool(
    title="Kaynağı getir",
    description=(
        "Bir source_id için kaynak künyesi, resmî kanıt alanları ve istenirse "
        "tüm indekslenmiş parçaları getirir. Büyük belgelerde önce get_chunk tercih edin."
    ),
    annotations=READ_ONLY,
    timeout=settings.tool_timeout,
)
def get_source(
    source_id: Annotated[str, Field(min_length=8, max_length=64, description="Kaynak kimliği")],
    include_chunks: Annotated[bool, Field(description="Tüm metin parçalarını dahil et")] = False,
) -> dict:
    return service.source_detail(source_id, include_chunks)


@mcp.tool(
    title="Kanıt parçasını getir",
    description=(
        "search_regulations sonucundaki tek bir chunk_id için tam metni; madde/bölüm, "
        "kaynak sürümü, current/archive durumu ve resmî URL kanıtıyla getirir."
    ),
    annotations=READ_ONLY,
    timeout=settings.tool_timeout,
)
def get_chunk(
    chunk_id: Annotated[str, Field(min_length=8, max_length=64, description="Metin parçası kimliği")]
) -> dict:
    return service.chunk_detail(chunk_id)


@mcp.tool(
    title="Kaynak durumunu kontrol et",
    description=(
        "Bir source_id'nin current/archive durumunu, sürüm zincirini, tarihlerini, "
        "SHA-256 özetini ve resmî URL'sini metni indirmeden kontrol eder."
    ),
    annotations=READ_ONLY,
    timeout=settings.tool_timeout,
)
def get_source_status(
    source_id: Annotated[str, Field(min_length=8, max_length=64, description="Kaynak kimliği")]
) -> dict:
    return service.source_status(source_id)


@mcp.tool(
    title="Sistem durumunu göster",
    description=(
        "İndeks, aktif kaynak ve semantik retrieval durumunu gösterir. "
        "Hasta veya kullanıcı verisi almaz."
    ),
    annotations=READ_ONLY,
    timeout=settings.tool_timeout,
)
def system_status() -> dict:
    return {
        **service.db.stats(),
        "service": "turkiye-health-tourism-regulations",
        "service_version": "0.2.0",
        "public_read_only": True,
        "semantic_search_enabled": service.embedder.enabled,
        "embedding_model": settings.embedding_model if service.embedder.enabled else None,
        "admin_tools_exposed": False,
        "checked_at": utc_now(),
    }


register_public_routes(mcp, service, settings)
