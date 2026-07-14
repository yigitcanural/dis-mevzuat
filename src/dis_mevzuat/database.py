from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    url TEXT,
    title TEXT NOT NULL,
    authority TEXT NOT NULL,
    source_type TEXT NOT NULL,
    published_at TEXT,
    effective_from TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    content_sha256 TEXT NOT NULL,
    content_type TEXT NOT NULL,
    raw_path TEXT,
    supersedes_source_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_checked_at TEXT NOT NULL,
    FOREIGN KEY(supersedes_source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    heading TEXT,
    article_no TEXT,
    text TEXT NOT NULL,
    token_estimate INTEGER NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    embedding_model TEXT,
    embedding_json TEXT,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE,
    UNIQUE(source_id, ordinal)
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED,
    source_id UNINDEXED,
    heading,
    text,
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS stages (
    id TEXT PRIMARY KEY,
    url TEXT,
    title TEXT NOT NULL,
    authority TEXT NOT NULL,
    source_type TEXT NOT NULL,
    published_at TEXT,
    effective_from TEXT,
    content_sha256 TEXT NOT NULL,
    content_type TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    text_path TEXT NOT NULL,
    supersedes_source_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_authority ON sources(authority);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row else None

    def insert_stage(self, stage: dict[str, Any]) -> None:
        columns = ", ".join(stage)
        placeholders = ", ".join(f":{key}" for key in stage)
        with self.connection() as conn:
            conn.execute(f"INSERT INTO stages ({columns}) VALUES ({placeholders})", stage)

    def get_stage(self, stage_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            return self._dict(conn.execute("SELECT * FROM stages WHERE id = ?", (stage_id,)).fetchone())

    def delete_stage(self, stage_id: str) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM stages WHERE id = ?", (stage_id,))

    def insert_source(self, source: dict[str, Any], chunks: list[dict[str, Any]]) -> None:
        with self.connection() as conn:
            columns = ", ".join(source)
            placeholders = ", ".join(f":{key}" for key in source)
            conn.execute(f"INSERT INTO sources ({columns}) VALUES ({placeholders})", source)
            for chunk in chunks:
                chunk_columns = ", ".join(chunk)
                chunk_placeholders = ", ".join(f":{key}" for key in chunk)
                conn.execute(
                    f"INSERT INTO chunks ({chunk_columns}) VALUES ({chunk_placeholders})", chunk
                )
                conn.execute(
                    "INSERT INTO chunks_fts(chunk_id, source_id, heading, text) VALUES (?, ?, ?, ?)",
                    (chunk["id"], chunk["source_id"], chunk.get("heading") or "", chunk["text"]),
                )

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            return self._dict(conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone())

    def get_active_source_by_hash(self, content_sha256: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sources WHERE content_sha256 = ? AND status = 'active' "
                "ORDER BY created_at DESC LIMIT 1",
                (content_sha256,),
            ).fetchone()
            return self._dict(row)

    def get_active_source_by_url(self, url: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sources WHERE url = ? AND status = 'active' "
                "ORDER BY created_at DESC LIMIT 1",
                (url,),
            ).fetchone()
            return self._dict(row)

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT c.*, s.title AS source_title, s.authority, s.source_type,
                       s.url, s.published_at, s.status
                FROM chunks c JOIN sources s ON s.id = c.source_id
                WHERE c.id = ?
                """,
                (chunk_id,),
            ).fetchone()
            return self._dict(row)

    def list_sources(self, status: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM sources"
        params: list[Any] = []
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY published_at DESC, created_at DESC"
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def archive_source(self, source_id: str, now: str) -> bool:
        with self.connection() as conn:
            cursor = conn.execute(
                "UPDATE sources SET status = 'archived', updated_at = ? WHERE id = ?",
                (now, source_id),
            )
            return cursor.rowcount > 0

    def archive_other_sources_for_url(self, url: str, keep_source_id: str, now: str) -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                "UPDATE sources SET status = 'archived', updated_at = ? "
                "WHERE url = ? AND id != ? AND status = 'active'",
                (now, url, keep_source_id),
            )
            return cursor.rowcount

    def keyword_search(
        self,
        query: str,
        limit: int,
        source_type: str | None,
        authority: str | None,
        active_only: bool,
    ) -> list[dict[str, Any]]:
        tokens = re.findall(r"[\wçğıöşüÇĞİÖŞÜ-]+", query, flags=re.UNICODE)
        if not tokens:
            return []
        fts_query = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens[:16])
        conditions = ["chunks_fts MATCH ?"]
        params: list[Any] = [fts_query]
        if source_type:
            conditions.append("s.source_type = ?")
            params.append(source_type)
        if authority:
            conditions.append("s.authority = ?")
            params.append(authority)
        if active_only:
            conditions.append("s.status = 'active'")
        params.append(limit)
        sql = f"""
            SELECT c.*, s.title AS source_title, s.authority, s.source_type,
                   s.published_at, s.status, bm25(chunks_fts) AS rank
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.chunk_id
            JOIN sources s ON s.id = c.source_id
            WHERE {' AND '.join(conditions)}
            ORDER BY rank
            LIMIT ?
        """
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def embedded_chunks(
        self,
        model: str,
        source_type: str | None,
        authority: str | None,
        active_only: bool,
    ) -> list[dict[str, Any]]:
        conditions = ["c.embedding_model = ?", "c.embedding_json IS NOT NULL"]
        params: list[Any] = [model]
        if source_type:
            conditions.append("s.source_type = ?")
            params.append(source_type)
        if authority:
            conditions.append("s.authority = ?")
            params.append(authority)
        if active_only:
            conditions.append("s.status = 'active'")
        sql = f"""
            SELECT c.*, s.title AS source_title, s.authority, s.source_type,
                   s.published_at, s.status
            FROM chunks c JOIN sources s ON s.id = c.source_id
            WHERE {' AND '.join(conditions)}
        """
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def stats(self) -> dict[str, Any]:
        with self.connection() as conn:
            source_count = conn.execute("SELECT count(*) FROM sources").fetchone()[0]
            active_count = conn.execute(
                "SELECT count(*) FROM sources WHERE status = 'active'"
            ).fetchone()[0]
            chunk_count = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
            embedded_count = conn.execute(
                "SELECT count(*) FROM chunks WHERE embedding_json IS NOT NULL"
            ).fetchone()[0]
            stage_count = conn.execute("SELECT count(*) FROM stages").fetchone()[0]
        return {
            "sources": source_count,
            "active_sources": active_count,
            "chunks": chunk_count,
            "embedded_chunks": embedded_count,
            "pending_stages": stage_count,
        }
