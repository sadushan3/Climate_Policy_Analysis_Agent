"""Document and chunk persistence (SQLite) + vector index (NumPy memmap-free).

Why not Chroma/pgvector? At this corpus size (hundreds of documents, tens of
thousands of chunks) an exact NumPy matmul is *faster* than an approximate index
and returns exact neighbours, with zero operational surface. The retriever is
behind an interface, so swapping in pgvector when the corpus outgrows RAM is a
one-file change -- and being able to say why you didn't reach for a vector DB is
worth more than having reached for one.

SQLite is opened per-operation with WAL enabled rather than held as a shared
connection, because FastAPI serves requests from a thread pool and a single
sqlite3 connection is not safe to share across threads.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.core.errors import NotFound

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,
    owner_id      TEXT NOT NULL DEFAULT '',
    name          TEXT NOT NULL,
    original_name TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    byte_size     INTEGER NOT NULL,
    page_count    INTEGER NOT NULL DEFAULT 0,
    word_count    INTEGER NOT NULL DEFAULT 0,
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    extractor     TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'pending',
    error         TEXT,
    meta          TEXT NOT NULL DEFAULT '{}',
    analysis      TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    doc_id      TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text        TEXT NOT NULL,
    page_start  INTEGER NOT NULL,
    page_end    INTEGER NOT NULL,
    section     TEXT NOT NULL DEFAULT '',
    char_start  INTEGER NOT NULL DEFAULT 0,
    char_end    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (doc_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_docs_owner ON documents(owner_id);
-- Deduplication is per owner, never global: matching on content hash alone
-- would let one tenant discover that another had uploaded the same file.
CREATE INDEX IF NOT EXISTS idx_docs_owner_hash ON documents(owner_id, content_hash);
CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    conn = sqlite3.connect(settings.db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # WAL lets reads proceed while a write is in flight -- without it, an upload
    # blocks every concurrent list/query call.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
    log.info("Database ready at %s", get_settings().db_path)


# --------------------------------------------------------------------------
# documents
# --------------------------------------------------------------------------

def create_document(
    *,
    owner_id: str,
    name: str,
    original_name: str,
    content_hash: str,
    byte_size: int,
    meta: dict | None = None,
) -> str:
    doc_id = uuid.uuid4().hex[:16]
    now = _now()
    with connect() as conn:
        conn.execute(
            """INSERT INTO documents (id, owner_id, name, original_name, content_hash,
                                      byte_size, meta, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
            (doc_id, owner_id, name, original_name, content_hash, byte_size,
             json.dumps(meta or {}), now, now),
        )
    return doc_id


def find_by_hash(owner_id: str, content_hash: str) -> dict | None:
    """Deduplicate within one owner only.

    A global hash lookup would leak across tenants: uploading a file and being
    told it already existed would reveal that another user holds it.
    """
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE owner_id = ? AND content_hash = ? AND status = 'ready' LIMIT 1",
            (owner_id, content_hash),
        ).fetchone()
    return _row_to_document(row) if row else None


def update_document(doc_id: str, **fields) -> None:
    if not fields:
        return
    if "meta" in fields and isinstance(fields["meta"], dict):
        fields["meta"] = json.dumps(fields["meta"])
    if "analysis" in fields and not isinstance(fields["analysis"], (str, type(None))):
        fields["analysis"] = json.dumps(fields["analysis"])

    fields["updated_at"] = _now()
    assignments = ", ".join(f"{key} = ?" for key in fields)
    with connect() as conn:
        cursor = conn.execute(
            f"UPDATE documents SET {assignments} WHERE id = ?", (*fields.values(), doc_id)
        )
        if cursor.rowcount == 0:
            raise NotFound(f"Document '{doc_id}' does not exist.")


def get_document(doc_id: str, owner_id: str | None = None) -> dict:
    """Fetch a document, scoped to an owner unless explicitly unscoped.

    A document belonging to someone else raises `NotFound`, not `Forbidden`:
    a 403 would confirm the id exists, which is an enumeration oracle.
    `owner_id=None` is for internal callers (background jobs) that have already
    established authorisation; every request path passes an owner.
    """
    with connect() as conn:
        if owner_id is None:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ? AND owner_id = ?", (doc_id, owner_id)
            ).fetchone()
    if row is None:
        raise NotFound(f"Document '{doc_id}' does not exist.")
    return _row_to_document(row)


def list_documents(owner_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE owner_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (owner_id, limit, offset),
        ).fetchall()
    return [_row_to_document(r) for r in rows]


def count_documents(owner_id: str | None = None) -> int:
    with connect() as conn:
        if owner_id is None:
            return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        return conn.execute(
            "SELECT COUNT(*) FROM documents WHERE owner_id = ?", (owner_id,)
        ).fetchone()[0]


def delete_document(doc_id: str, owner_id: str) -> None:
    with connect() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE id = ? AND owner_id = ?", (doc_id, owner_id)
        )
        if cursor.rowcount == 0:
            raise NotFound(f"Document '{doc_id}' does not exist.")
    vector_path(doc_id).unlink(missing_ok=True)


def _row_to_document(row: sqlite3.Row) -> dict:
    doc = dict(row)
    doc["meta"] = json.loads(doc.get("meta") or "{}")
    if doc.get("analysis"):
        try:
            doc["analysis"] = json.loads(doc["analysis"])
        except (TypeError, json.JSONDecodeError):
            doc["analysis"] = None
    return doc


# --------------------------------------------------------------------------
# chunks
# --------------------------------------------------------------------------

def save_chunks(doc_id: str, chunks: list[dict]) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        conn.executemany(
            """INSERT INTO chunks (doc_id, chunk_index, text, page_start, page_end,
                                   section, char_start, char_end)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    doc_id,
                    c["chunk_index"],
                    c["text"],
                    c["page_start"],
                    c["page_end"],
                    c.get("section", ""),
                    c.get("char_start", 0),
                    c.get("char_end", 0),
                )
                for c in chunks
            ],
        )


def get_chunks(doc_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index", (doc_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_chunks_many(doc_ids: list[str]) -> list[dict]:
    if not doc_ids:
        return []
    placeholders = ",".join("?" * len(doc_ids))
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM chunks WHERE doc_id IN ({placeholders}) ORDER BY doc_id, chunk_index",
            doc_ids,
        ).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# vectors
# --------------------------------------------------------------------------

def vector_path(doc_id: str) -> Path:
    return get_settings().index_dir / f"{doc_id}.npy"


def save_vectors(doc_id: str, vectors: np.ndarray) -> None:
    np.save(vector_path(doc_id), vectors.astype(np.float32))


def load_vectors(doc_id: str) -> np.ndarray:
    path = vector_path(doc_id)
    if not path.exists():
        raise NotFound(f"No vector index for document '{doc_id}'. Re-run analysis.")
    return np.load(path)


def load_vectors_many(doc_ids: list[str]) -> np.ndarray:
    arrays = [load_vectors(d) for d in doc_ids]
    return np.vstack(arrays) if arrays else np.zeros((0, 384), dtype=np.float32)
