from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .chunking import chunk_legal_text, normalize_text
from .config import Settings
from .database import Database
from .embeddings import EmbeddingClient, cosine_similarity
from .extraction import extract_url
from .models import SearchHit


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class ComplianceService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db = Database(settings.db_path)
        self.embedder = EmbeddingClient(
            settings.embedding_api_key,
            settings.embedding_api_base,
            settings.embedding_model,
            settings.request_timeout,
        )

    async def preview_url(
        self,
        url: str,
        authority: str,
        source_type: str,
        title: str | None = None,
        published_at: str | None = None,
        effective_from: str | None = None,
        supersedes_source_id: str | None = None,
    ) -> dict[str, Any]:
        extracted = await extract_url(
            url, self.settings.max_source_bytes, self.settings.request_timeout
        )
        return self._stage(
            text=extracted.text,
            raw_bytes=extracted.raw_bytes,
            url=extracted.final_url or url,
            authority=authority,
            source_type=source_type,
            title=title or extracted.title or "Başlıksız kaynak",
            published_at=published_at,
            effective_from=effective_from,
            content_type=extracted.content_type,
            metadata=extracted.metadata,
            supersedes_source_id=supersedes_source_id,
        )

    def preview_text(
        self,
        text: str,
        title: str,
        authority: str,
        source_type: str,
        source_url: str | None = None,
        published_at: str | None = None,
        effective_from: str | None = None,
        supersedes_source_id: str | None = None,
    ) -> dict[str, Any]:
        return self._stage(
            text=text,
            raw_bytes=text.encode("utf-8"),
            url=source_url,
            authority=authority,
            source_type=source_type,
            title=title,
            published_at=published_at,
            effective_from=effective_from,
            content_type="text/plain",
            metadata={"pasted_text": True},
            supersedes_source_id=supersedes_source_id,
        )

    def _stage(
        self,
        *,
        text: str,
        raw_bytes: bytes,
        url: str | None,
        authority: str,
        source_type: str,
        title: str,
        published_at: str | None,
        effective_from: str | None,
        content_type: str,
        metadata: dict[str, Any],
        supersedes_source_id: str | None,
    ) -> dict[str, Any]:
        cleaned = normalize_text(text)
        if len(cleaned) < 80:
            raise ValueError("Kaynak metni anlamlı biçimde indexlemek için çok kısa.")
        stage_id = uuid.uuid4().hex
        digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
        raw_path = self.settings.data_dir / "staging" / f"{stage_id}.bin"
        text_path = self.settings.data_dir / "staging" / f"{stage_id}.txt"
        raw_path.write_bytes(raw_bytes)
        text_path.write_text(cleaned, encoding="utf-8")
        now = utc_now()
        stage = {
            "id": stage_id,
            "url": url,
            "title": title.strip(),
            "authority": authority.strip(),
            "source_type": source_type.strip(),
            "published_at": published_at,
            "effective_from": effective_from,
            "content_sha256": digest,
            "content_type": content_type,
            "raw_path": str(raw_path),
            "text_path": str(text_path),
            "supersedes_source_id": supersedes_source_id,
            "metadata_json": json.dumps(metadata, ensure_ascii=False),
            "created_at": now,
        }
        self.db.insert_stage(stage)
        chunks = chunk_legal_text(cleaned)
        return {
            "stage_id": stage_id,
            "title": title,
            "authority": authority,
            "source_type": source_type,
            "url": url,
            "published_at": published_at,
            "content_sha256": digest,
            "character_count": len(cleaned),
            "estimated_chunks": len(chunks),
            "preview": cleaned[:1200],
            "next_action": "İçeriği doğruladıktan sonra approve_source(stage_id) çağırın.",
        }

    async def approve_stage(self, stage_id: str) -> dict[str, Any]:
        stage = self.db.get_stage(stage_id)
        if not stage:
            raise ValueError("Bekleyen kaynak bulunamadı veya daha önce işlendi.")
        existing = self.db.get_active_source_by_hash(stage["content_sha256"])
        if existing:
            self._discard_stage(stage)
            return {
                "source_id": existing["id"],
                "title": existing["title"],
                "duplicate": True,
                "chunks_indexed": 0,
                "semantic_indexed": None,
                "message": "Aynı içerik zaten aktif indexte bulundu; kopya eklenmedi.",
            }
        text = Path(stage["text_path"]).read_text(encoding="utf-8")
        chunk_objects = chunk_legal_text(text)
        embeddings: list[list[float]] | None = None
        if self.embedder.enabled:
            embeddings = []
            batch_size = 32
            for start in range(0, len(chunk_objects), batch_size):
                batch = chunk_objects[start : start + batch_size]
                values = await self.embedder.embed(
                    [item.text for item in batch], input_type="search_document"
                )
                embeddings.extend(values)

        source_id = uuid.uuid4().hex
        now = utc_now()
        final_raw = self.settings.data_dir / "raw" / f"{source_id}.bin"
        shutil.move(stage["raw_path"], final_raw)
        source = {
            "id": source_id,
            "url": stage["url"],
            "title": stage["title"],
            "authority": stage["authority"],
            "source_type": stage["source_type"],
            "published_at": stage["published_at"],
            "effective_from": stage["effective_from"],
            "status": "active",
            "content_sha256": stage["content_sha256"],
            "content_type": stage["content_type"],
            "raw_path": str(final_raw),
            "supersedes_source_id": stage["supersedes_source_id"],
            "metadata_json": stage["metadata_json"],
            "created_at": now,
            "updated_at": now,
            "last_checked_at": now,
        }
        chunks: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunk_objects):
            chunks.append(
                {
                    "id": uuid.uuid4().hex,
                    "source_id": source_id,
                    "ordinal": chunk.ordinal,
                    "heading": chunk.heading,
                    "article_no": chunk.article_no,
                    "text": chunk.text,
                    "token_estimate": max(1, len(chunk.text) // 4),
                    "metadata_json": json.dumps(chunk.metadata, ensure_ascii=False),
                    "embedding_model": self.settings.embedding_model if embeddings else None,
                    "embedding_json": json.dumps(embeddings[idx]) if embeddings else None,
                }
            )
        supersedes = stage["supersedes_source_id"]
        if supersedes:
            self.db.archive_source(supersedes, now)
        self.db.insert_source(source, chunks)
        if source["url"]:
            self.db.archive_other_sources_for_url(source["url"], source_id, now)
        self.db.delete_stage(stage_id)
        Path(stage["text_path"]).unlink(missing_ok=True)
        return {
            "source_id": source_id,
            "title": stage["title"],
            "chunks_indexed": len(chunks),
            "semantic_indexed": bool(embeddings),
            "archived_previous_source": supersedes,
        }

    def _discard_stage(self, stage: dict[str, Any]) -> None:
        self.db.delete_stage(stage["id"])
        Path(stage["raw_path"]).unlink(missing_ok=True)
        Path(stage["text_path"]).unlink(missing_ok=True)

    async def refresh_source(self, source_id: str) -> dict[str, Any]:
        source = self.db.get_source(source_id)
        if not source:
            raise ValueError("Kaynak bulunamadı.")
        if not source.get("url"):
            raise ValueError("Bağlantısı olmayan yapıştırılmış kaynak otomatik yenilenemez.")
        preview = await self.preview_url(
            source["url"],
            source["authority"],
            source["source_type"],
            source["title"],
            source["published_at"],
            source["effective_from"],
            supersedes_source_id=source_id,
        )
        if preview["content_sha256"] == source["content_sha256"]:
            unchanged_stage = self.db.get_stage(preview["stage_id"])
            if unchanged_stage:
                self._discard_stage(unchanged_stage)
            return {"changed": False, "source_id": source_id, "message": "Kaynak değişmemiş."}
        preview["changed"] = True
        preview["previous_source_id"] = source_id
        return preview

    async def search(
        self,
        query: str,
        top_k: int = 8,
        source_type: str | None = None,
        authority: str | None = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        candidate_limit = max(top_k * 4, 20)
        keyword_rows = self.db.keyword_search(
            query, candidate_limit, source_type, authority, active_only
        )
        rankings: dict[str, dict[str, Any]] = {}
        rrf_k = 60.0
        for rank, row in enumerate(keyword_rows, start=1):
            rankings[row["id"]] = {
                "row": row,
                "score": 1.0 / (rrf_k + rank),
                "matched_by": ["keyword"],
            }

        semantic_used = False
        if self.embedder.enabled:
            embedded_rows = self.db.embedded_chunks(
                self.settings.embedding_model, source_type, authority, active_only
            )
            if embedded_rows:
                query_vector = (
                    await self.embedder.embed([query], input_type="search_query")
                )[0]
                scored = sorted(
                    (
                        (row, cosine_similarity(query_vector, json.loads(row["embedding_json"])))
                        for row in embedded_rows
                    ),
                    key=lambda item: item[1],
                    reverse=True,
                )[:candidate_limit]
                semantic_used = True
                for rank, (row, similarity) in enumerate(scored, start=1):
                    item = rankings.setdefault(
                        row["id"], {"row": row, "score": 0.0, "matched_by": []}
                    )
                    item["score"] += 1.0 / (rrf_k + rank)
                    item["score"] += max(0.0, similarity) * 0.002
                    item["matched_by"].append("semantic")

        ordered = sorted(rankings.values(), key=lambda item: item["score"], reverse=True)[:top_k]
        hits = []
        for item in ordered:
            row = item["row"]
            hit = SearchHit(
                chunk_id=row["id"],
                source_id=row["source_id"],
                source_title=row["source_title"],
                authority=row["authority"],
                source_type=row["source_type"],
                published_at=row["published_at"],
                status=row["status"],
                heading=row["heading"],
                article_no=row["article_no"],
                text=row["text"],
                score=item["score"],
                matched_by=item["matched_by"],
            )
            hits.append(hit.as_dict())
        return {
            "query": query,
            "retrieval_mode": "hybrid" if semantic_used else "keyword",
            "result_count": len(hits),
            "results": hits,
            "notice": "Sonuçlar kaynak metinleridir; hukuki görüş veya uygunluk kararı değildir.",
        }

    def source_detail(self, source_id: str, include_chunks: bool = False) -> dict[str, Any]:
        source = self.db.get_source(source_id)
        if not source:
            raise ValueError("Kaynak bulunamadı.")
        source["metadata"] = json.loads(source.pop("metadata_json"))
        source.pop("raw_path", None)
        if include_chunks:
            with self.db.connection() as conn:
                rows = conn.execute(
                    "SELECT id, ordinal, heading, article_no, text, token_estimate FROM chunks "
                    "WHERE source_id = ? ORDER BY ordinal",
                    (source_id,),
                ).fetchall()
                source["chunks"] = [dict(row) for row in rows]
        return source

    def chunk_detail(self, chunk_id: str) -> dict[str, Any]:
        chunk = self.db.get_chunk(chunk_id)
        if not chunk:
            raise ValueError("Metin parçası bulunamadı.")
        chunk["metadata"] = json.loads(chunk.pop("metadata_json"))
        chunk.pop("embedding_json", None)
        return chunk
