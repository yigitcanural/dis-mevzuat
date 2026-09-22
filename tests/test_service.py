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


@pytest.mark.asyncio
async def test_new_version_archives_previous_and_current_search_excludes_it(service):
    url = "https://www.saglik.gov.tr/example"
    first = service.preview_text(
        "MADDE 1- Sağlık turizmi tanıtımı yalnız bilgilendirme amacı taşır. " * 2,
        "İlk Sürüm",
        "Sağlık Bakanlığı",
        "saglik_turizmi_mevzuati",
        source_url=url,
        version="1",
    )
    first_result = await service.approve_stage(first["stage_id"])
    second = service.preview_text(
        "MADDE 1- Sağlık turizmi tanıtımı güncel koşullara uygun yürütülür. " * 2,
        "İkinci Sürüm",
        "Sağlık Bakanlığı",
        "saglik_turizmi_mevzuati",
        source_url=url,
        supersedes_source_id=first_result["source_id"],
        version="2",
        category="health_tourism",
        tags=["tanıtım", "yetkilendirme"],
    )
    second_result = await service.approve_stage(second["stage_id"])

    assert service.db.get_source(first_result["source_id"])["status"] == "archived"
    assert service.db.get_source(second_result["source_id"])["status"] == "active"
    result = await service.search("güncel koşullara", active_only=True)
    assert {item["source_id"] for item in result["results"]} == {
        second_result["source_id"]
    }
    assert result["results"][0]["meta"]["version"] == "2"
    assert result["results"][0]["evidence"]["official_url"] == url


@pytest.mark.asyncio
async def test_sql_metacharacters_do_not_escape_fts_query(service):
    result = await service.search("' OR 1=1; DROP TABLE sources; --")
    assert isinstance(result["results"], list)
    assert service.db.stats()["sources"] == 0


def test_database_persists_across_service_instances(service):
    service.preview_text(
        "MADDE 1- Kalıcı staging kaydı güvenli biçimde saklanır. " * 2,
        "Kalıcılık",
        "Test",
        "mevzuat",
    )
    reopened = ComplianceService(service.settings)
    assert reopened.db.stats()["pending_stages"] == 1


@pytest.mark.asyncio
async def test_hybrid_search_combines_lexical_and_semantic_results(service):
    preview = service.preview_text(
        "MADDE 1- Uluslararası sağlık turizmi aracı kuruluş yetki belgesi alır. " * 2,
        "Semantik Test",
        "Sağlık Bakanlığı",
        "saglik_turizmi_mevzuati",
    )
    approved = await service.approve_stage(preview["stage_id"])
    with service.db.connection() as conn:
        conn.execute(
            "UPDATE chunks SET embedding_model = ?, embedding_json = ? WHERE source_id = ?",
            ("test-model", "[1.0, 0.0]", approved["source_id"]),
        )

    class FakeEmbedder:
        enabled = True

        async def embed(self, texts, input_type=None):
            return [[1.0, 0.0] for _ in texts]

    service.embedder = FakeEmbedder()
    result = await service.search("yetki belgesi", top_k=3)
    assert result["retrieval_mode"] == "hybrid"
    assert set(result["results"][0]["matched_by"]) == {"keyword", "semantic"}
