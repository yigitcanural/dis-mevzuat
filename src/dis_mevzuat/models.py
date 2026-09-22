from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractedSource:
    text: str
    title: str | None
    content_type: str
    final_url: str | None
    raw_bytes: bytes
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    ordinal: int
    text: str
    heading: str | None = None
    article_no: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchHit:
    chunk_id: str
    source_id: str
    source_title: str
    authority: str
    source_type: str
    published_at: str | None
    effective_from: str | None
    status: str
    official_url: str | None
    retrieved_at: str
    content_sha256: str
    jurisdiction: str
    category: str
    subcategory: str | None
    version: str | None
    tags: list[str]
    heading: str | None
    article_no: str | None
    text: str
    score: float
    matched_by: list[str]

    def as_dict(self) -> dict[str, Any]:
        structured = {
            "data": {
                "text": self.text,
                "relevant_section": self.heading,
                "article_or_chunk": self.article_no or self.chunk_id,
            },
            "meta": {
                "source_id": self.source_id,
                "chunk_id": self.chunk_id,
                "title": self.source_title,
                "institution": self.authority,
                "jurisdiction": self.jurisdiction,
                "category": self.category,
                "subcategory": self.subcategory,
                "source_type": self.source_type,
                "publication_date": self.published_at,
                "effective_date": self.effective_from,
                "version": self.version,
                "current_or_archived": "current" if self.status == "active" else "archive",
                "tags": self.tags,
            },
            "evidence": {
                "official_url": self.official_url,
                "retrieved_at": self.retrieved_at,
                "source_status": self.status,
                "sha256": self.content_sha256,
            },
            "retrieval": {
                "score": round(self.score, 6),
                "matched_by": self.matched_by,
            },
        }
        # Compatibility aliases for 0.x clients. New clients should use the
        # data/meta/evidence sections above.
        structured.update({
            "chunk_id": self.chunk_id,
            "source_id": self.source_id,
            "source_title": self.source_title,
            "authority": self.authority,
            "source_type": self.source_type,
            "published_at": self.published_at,
            "status": self.status,
            "heading": self.heading,
            "article_no": self.article_no,
            "text": self.text,
            "score": round(self.score, 6),
            "matched_by": self.matched_by,
        })
        return structured
