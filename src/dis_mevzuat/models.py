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
    status: str
    heading: str | None
    article_no: str | None
    text: str
    score: float
    matched_by: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
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
        }
