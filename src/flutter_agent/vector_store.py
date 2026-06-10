"""Local vector database for semantic retrieval over skills + knowledge docs.

Design goals (mirroring the rest of this repo):

  * **Zero new dependencies, fully offline.** Embeddings come from a
    deterministic feature-hashing embedder (unigram words + CJK character
    bigrams, log-TF weighted, signed hashing trick, L2-normalised), and
    vectors persist in SQLite (stdlib). No model download, no network.
  * **Pluggable embedder.** Anything with ``embed(texts) -> List[List[float]]``
    and a ``dim`` attribute can replace :class:`HashingEmbedder` (e.g. an
    OpenAI-compatible ``/v1/embeddings`` client) without touching the store.
  * **Pure + testable.** Chunking and embedding are pure functions of their
    inputs; the store is a thin SQLite wrapper. Corpus size is small
    (tens of docs, hundreds of chunks), so search is exact brute-force
    cosine — no ANN index needed at this scale.
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
import sqlite3
import struct
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z0-9_]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


def _tokenize(text: str) -> List[str]:
    """ASCII words + CJK unigrams + CJK bigrams (matches skill_ranker's view)."""
    lowered = text.lower()
    tokens = _WORD_RE.findall(lowered)
    cjk = _CJK_RE.findall(lowered)
    tokens.extend(cjk)
    tokens.extend(a + b for a, b in zip(cjk, cjk[1:]))
    return tokens


class HashingEmbedder:
    """Deterministic signed feature-hashing embedder (offline, dependency-free).

    Each token hashes to a bucket and a sign; weights are ``1 + log(tf)``;
    the final vector is L2-normalised so dot product == cosine similarity.
    """

    name = "hashing-v1"

    def __init__(self, dim: int = 512):
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim

    def _bucket(self, token: str) -> tuple:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(digest[:4], "little") % self.dim
        sign = 1.0 if digest[4] & 1 else -1.0
        return idx, sign

    def embed_one(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        counts: dict = {}
        for tok in _tokenize(text):
            counts[tok] = counts.get(tok, 0) + 1
        for tok, tf in counts.items():
            idx, sign = self._bucket(tok)
            vec[idx] += sign * (1.0 + math.log(tf))
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [self.embed_one(t) for t in texts]


# ---------------------------------------------------------------------------
# Chunking (pure)
# ---------------------------------------------------------------------------

def chunk_markdown(text: str, *, max_chars: int = 1600, overlap: int = 160) -> List[str]:
    """Split markdown into chunks along heading boundaries, then by size.

    Headings keep semantically coherent sections together; oversized sections
    fall back to a sliding window with ``overlap`` chars of continuity.
    """
    if not text.strip():
        return []
    sections: List[str] = []
    current: List[str] = []
    for line in text.splitlines():
        if line.startswith("#") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())

    chunks: List[str] = []
    for sec in sections:
        if not sec:
            continue
        if len(sec) <= max_chars:
            chunks.append(sec)
            continue
        start = 0
        while start < len(sec):
            end = min(start + max_chars, len(sec))
            chunks.append(sec[start:end])
            if end >= len(sec):
                break
            start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

@dataclass
class VectorDoc:
    """One chunk to index."""

    doc_id: str
    kind: str  # "skill" | "knowledge"
    title: str
    source: str  # relative path on disk
    chunk_index: int
    text: str


@dataclass
class SearchHit:
    doc_id: str
    kind: str
    title: str
    source: str
    chunk_index: int
    score: float
    snippet: str


_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    doc_id      TEXT NOT NULL,
    kind        TEXT NOT NULL,
    title       TEXT NOT NULL,
    source      TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text        TEXT NOT NULL,
    vector      BLOB NOT NULL,
    dim         INTEGER NOT NULL,
    embedder    TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    PRIMARY KEY (doc_id, chunk_index)
);
"""


def _pack(vec: Sequence[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack(blob: bytes, dim: int) -> List[float]:
    return list(struct.unpack(f"{dim}f", blob))


class VectorStore:
    """SQLite-backed vector store with exact cosine search."""

    def __init__(self, path: Path, embedder: Optional[HashingEmbedder] = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder or HashingEmbedder()
        # FastAPI handlers may touch the store from worker threads; access is
        # serialised behind a lock, so cross-thread use of one connection is safe.
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def clear(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM chunks")
            self._conn.commit()

    def count(self) -> int:
        with self._lock:
            (n,) = self._conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        return int(n)

    def doc_count(self) -> int:
        with self._lock:
            (n,) = self._conn.execute(
                "SELECT COUNT(DISTINCT doc_id) FROM chunks"
            ).fetchone()
        return int(n)

    def add(self, docs: Iterable[VectorDoc]) -> int:
        docs = list(docs)
        if not docs:
            return 0
        vectors = self.embedder.embed([d.text for d in docs])
        now = int(time.time())
        rows = [
            (
                d.doc_id, d.kind, d.title, d.source, d.chunk_index, d.text,
                _pack(v), self.embedder.dim, self.embedder.name, now,
            )
            for d, v in zip(docs, vectors)
        ]
        with self._lock:
            self._conn.executemany(
                "INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?)", rows
            )
            self._conn.commit()
        return len(rows)

    def search(
        self, query: str, *, top_k: int = 5, kind: Optional[str] = None
    ) -> List[SearchHit]:
        qvec = self.embedder.embed_one(query)
        sql = "SELECT doc_id, kind, title, source, chunk_index, text, vector, dim FROM chunks"
        params: tuple = ()
        if kind:
            sql += " WHERE kind = ?"
            params = (kind,)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        hits: List[SearchHit] = []
        for row in rows:
            doc_id, knd, title, source, idx, text, blob, dim = row
            if dim != self.embedder.dim:
                continue
            vec = _unpack(blob, dim)
            score = sum(a * b for a, b in zip(qvec, vec))
            hits.append(
                SearchHit(
                    doc_id=doc_id, kind=knd, title=title, source=source,
                    chunk_index=idx, score=round(score, 6),
                    snippet=text[:240],
                )
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: max(1, top_k)]


# ---------------------------------------------------------------------------
# Corpus builders
# ---------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_TITLE_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)


def docs_from_skills(skills_dir: Path) -> List[VectorDoc]:
    """One VectorDoc per chunk of every ``SKILL.md`` under ``skills_dir``."""
    out: List[VectorDoc] = []
    skills_dir = Path(skills_dir)
    for path in sorted(skills_dir.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = _FRONT_MATTER_RE.match(raw)
        if not m:
            continue
        doc_id = path.parent.name if path.name == "SKILL.md" else path.stem
        tm = _TITLE_RE.search(m.group(1))
        title = tm.group(1).strip().strip('"').strip("'") if tm else doc_id
        body = raw[m.end():]
        # Index front-matter metadata alongside the first chunk so tag/trigger
        # vocabulary is searchable too.
        pieces = chunk_markdown(body)
        if pieces:
            pieces[0] = m.group(1) + "\n" + pieces[0]
        else:
            pieces = [m.group(1)]
        for i, piece in enumerate(pieces):
            out.append(
                VectorDoc(
                    doc_id=doc_id, kind="skill", title=title,
                    source=str(path.relative_to(skills_dir.parent)),
                    chunk_index=i, text=piece,
                )
            )
    return out


def docs_from_knowledge(knowledge_dir: Path) -> List[VectorDoc]:
    """One VectorDoc per chunk of every ``*.md`` under ``knowledge_dir``."""
    out: List[VectorDoc] = []
    knowledge_dir = Path(knowledge_dir)
    if not knowledge_dir.exists():
        return out
    for path in sorted(knowledge_dir.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        first_heading = next(
            (ln.lstrip("# ").strip() for ln in raw.splitlines() if ln.startswith("#")),
            path.stem,
        )
        for i, piece in enumerate(chunk_markdown(raw)):
            out.append(
                VectorDoc(
                    doc_id=path.stem, kind="knowledge", title=first_heading,
                    source=str(path.relative_to(knowledge_dir.parent)),
                    chunk_index=i, text=piece,
                )
            )
    return out


def semantic_skill_scores(
    store: VectorStore, query: str, *, limit: int = 20
) -> dict:
    """Best cosine score per skill id for a query (for ranker blending)."""
    scores: dict = {}
    for hit in store.search(query, top_k=limit, kind="skill"):
        if hit.score > scores.get(hit.doc_id, 0.0):
            scores[hit.doc_id] = hit.score
    return scores


def safe_semantic_scores(store: Optional[VectorStore], query: str) -> dict:
    """Like ``semantic_skill_scores`` but never raises: semantic recall is an
    optional enhancement, so callers degrade to keyword-only ranking."""
    if store is None:
        return {}
    try:
        return semantic_skill_scores(store, query)
    except Exception:  # noqa: BLE001
        logger.exception("semantic scoring failed; keyword-only ranking")
        return {}


def build_index(
    store: VectorStore, *, skills_dir: Path, knowledge_dir: Path
) -> dict:
    """(Re)build the full index. Returns stats for reporting."""
    store.clear()
    skill_docs = docs_from_skills(skills_dir)
    knowledge_docs = docs_from_knowledge(knowledge_dir)
    added = store.add(skill_docs) + store.add(knowledge_docs)
    return {
        "chunks": added,
        "documents": store.doc_count(),
        "skill_chunks": len(skill_docs),
        "knowledge_chunks": len(knowledge_docs),
        "dim": store.embedder.dim,
        "embedder": store.embedder.name,
    }
