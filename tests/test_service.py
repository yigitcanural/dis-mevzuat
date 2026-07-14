import pytest

from dis_mevzuat.config import Settings
from dis_mevzuat.service import ComplianceService


@pytest.fixture
def service(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        enable_admin_tools=True,
        max_source_bytes=1_000_000,
        request_timeout=5,
        embedding_api_key=None,
        embedding_api_base="https://example.invalid/api/v1",
        embedding_model="test-model",
        transport="stdio",
        host="127.0.0.1",
        port=8000,
    )
    (tmp_path / "raw").mkdir()
    (tmp_path / "staging").mkdir()
    return ComplianceService(settings)


@pytest.mark.asyncio
async def test_preview_approve_and_keyword_search(service):
    preview = service.preview_text(
        text=(
            "MADDE 1- Sağlık hizmetlerinde örtülü veya açık reklam yapılamaz.\n\n"
            "MADDE 2- Tanıtımlarda fiyat, indirim ve kampanya bilgisine yer verilemez."
        ),
        title="Örnek Sağlık Yönetmeliği",
        authority="Test Bakanlığı",
        source_type="mevzuat",
    )
    assert preview["estimated_chunks"] == 2
    approved = await service.approve_stage(preview["stage_id"])
    assert approved["chunks_indexed"] == 2
    result = await service.search("fiyat kampanya", top_k=3)
    assert result["retrieval_mode"] == "keyword"
    assert result["result_count"] >= 1
    assert "fiyat" in result["results"][0]["text"].lower()


@pytest.mark.asyncio
async def test_archive_removes_from_active_search(service):
    preview = service.preview_text(
        text="MADDE 1- Hasta memnuniyeti üzerinden reklam yapılamaz." * 3,
        title="Arşiv Testi",
        authority="Test",
        source_type="kilavuz",
    )
    approved = await service.approve_stage(preview["stage_id"])
    service.db.archive_source(approved["source_id"], "2026-01-01T00:00:00+00:00")
    result = await service.search("hasta memnuniyeti", active_only=True)
    assert result["result_count"] == 0


@pytest.mark.asyncio
async def test_same_content_is_not_indexed_twice(service):
    text = "MADDE 1- Sağlık hizmetlerinde açık ve örtülü reklam yapılamaz. " * 2
    first = service.preview_text(text, "İlk Başlık", "Test", "mevzuat")
    first_result = await service.approve_stage(first["stage_id"])

    duplicate = service.preview_text(text, "İkinci Başlık", "Test", "mevzuat")
    duplicate_result = await service.approve_stage(duplicate["stage_id"])

    assert duplicate_result["duplicate"] is True
    assert duplicate_result["source_id"] == first_result["source_id"]
    assert service.db.stats()["sources"] == 1
    assert service.db.stats()["pending_stages"] == 0
