"""Hybrid retrieval: dense + lexical, fused, then reranked.

Why hybrid rather than pure vector search? Dense retrieval generalises across
wording ("cut emissions" ~ "reduce GHG") but is unreliable on the rare literal
tokens that matter most in policy work -- "Article 6.4", "LULUCF", "2005 levels",
a specific fund name. BM25 nails those and fails at paraphrase. Each covers the
other's blind spot.

The two ranked lists are combined with Reciprocal Rank Fusion, which needs no
score calibration between retrievers (their scores are on incomparable scales),
then the fused head is re-scored by a cross-encoder.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import numpy as np

from app.config import get_settings
from app.nlp import embeddings

log = logging.getLogger(__name__)

_TOKEN = re.compile(r"[a-z0-9][a-z0-9\-\.]*")

# Keeping digits and units is deliberate: "2030" and "45%" are the highest-value
# query tokens in this domain.
_STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their", "there", "these", "this", "to", "was", "were", "will", "with", "which", "while", "shall", "may", "can"]
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


@dataclass
class ScoredChunk:
    doc_id: str
    chunk_index: int
    text: str
    page_start: int
    page_end: int
    section: str
    score: float
    dense_rank: int | None = None
    lexical_rank: int | None = None
    rerank_score: float | None = None

    @property
    def citation(self) -> str:
        pages = (
            f"p. {self.page_start}"
            if self.page_start == self.page_end
            else f"pp. {self.page_start}-{self.page_end}"
        )
        return f"{self.section} ({pages})" if self.section else pages

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "section": self.section,
            "citation": self.citation,
            "score": round(self.score, 4),
            "rerank_score": round(self.rerank_score, 4) if self.rerank_score is not None else None,
        }


class HybridRetriever:
    """Retrieval over the chunks of one or more documents.

    Built per-query from the store rather than held as long-lived global state,
    which keeps it correct when documents are added or deleted concurrently.
    """

    def __init__(self, records: list[dict], vectors: np.ndarray):
        self.records = records
        self.vectors = vectors
        self._bm25 = None
        self._corpus_tokens: list[list[str]] | None = None

    @property
    def bm25(self):
        if self._bm25 is None:
            from rank_bm25 import BM25Okapi

            self._corpus_tokens = [tokenize(r["text"]) for r in self.records]
            # BM25Okapi divides by average document length; guard the empty case.
            self._bm25 = BM25Okapi(self._corpus_tokens or [[""]])
        return self._bm25

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        candidates: int | None = None,
        use_reranker: bool = True,
    ) -> list[ScoredChunk]:
        settings = get_settings()
        top_k = top_k or settings.rerank_top_k
        candidates = candidates or settings.retrieval_top_k

        if not self.records:
            return []

        # --- dense arm ---
        query_vec = (await embeddings.embed([query]))[0]
        dense_scores = self.vectors @ query_vec
        dense_order = np.argsort(-dense_scores)[:candidates]

        # --- lexical arm ---
        lexical_scores = np.asarray(self.bm25.get_scores(tokenize(query)), dtype=np.float32)
        lexical_order = np.argsort(-lexical_scores)[:candidates]

        # --- Reciprocal Rank Fusion ---
        # RRF(d) = sum over retrievers of 1 / (k + rank(d)). The constant damps
        # the influence of any single retriever's top hit, so one confident but
        # wrong retriever cannot dominate the fused list.
        k = settings.rrf_k
        fused: dict[int, float] = {}
        dense_rank_of: dict[int, int] = {}
        lexical_rank_of: dict[int, int] = {}

        for rank, idx in enumerate(dense_order):
            idx = int(idx)
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank + 1)
            dense_rank_of[idx] = rank + 1

        for rank, idx in enumerate(lexical_order):
            idx = int(idx)
            if lexical_scores[idx] <= 0:
                continue  # no lexical overlap at all; contributes nothing
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank + 1)
            lexical_rank_of[idx] = rank + 1

        ranked = sorted(fused.items(), key=lambda kv: -kv[1])[: max(top_k * 3, top_k)]

        results = [
            ScoredChunk(
                doc_id=self.records[i]["doc_id"],
                chunk_index=self.records[i]["chunk_index"],
                text=self.records[i]["text"],
                page_start=self.records[i]["page_start"],
                page_end=self.records[i]["page_end"],
                section=self.records[i].get("section", ""),
                score=float(score),
                dense_rank=dense_rank_of.get(i),
                lexical_rank=lexical_rank_of.get(i),
            )
            for i, score in ranked
        ]

        # --- cross-encoder rerank of the fused head ---
        if use_reranker and results:
            scores = await embeddings.rerank(query, [r.text for r in results])
            if any(scores):
                for chunk, score in zip(results, scores, strict=True):
                    chunk.rerank_score = score
                results.sort(key=lambda c: -(c.rerank_score or 0.0))

        return results[:top_k]
