"""Embedding and cross-encoder model management.

Models are expensive to load (seconds) and cheap to reuse, so they are loaded
once per process behind a lock and shared. All encoding runs in a worker thread
so a request never blocks the event loop -- V1 called `.encode()` directly inside
an async route, which stalled every other in-flight request.
"""
from __future__ import annotations

import os

# transformers probes for TensorFlow and Flax at import time, and on a machine
# with Keras 3 installed that probe raises and takes sentence-transformers down
# with it. This stack is torch-only, so skip the probe entirely -- it also cuts
# several seconds off startup. Must be set before transformers is imported.
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import asyncio
import logging
import threading
from functools import lru_cache

import numpy as np

from app.config import get_settings

log = logging.getLogger(__name__)

_lock = threading.Lock()
_embedder = None
_reranker = None


def get_embedder():
    global _embedder
    if _embedder is None:
        with _lock:
            if _embedder is None:
                from sentence_transformers import SentenceTransformer

                settings = get_settings()
                log.info("Loading embedding model %s", settings.embedding_model)
                _embedder = SentenceTransformer(settings.embedding_model, device=settings.device)
    return _embedder


def get_reranker():
    """Cross-encoder used to re-score retrieval candidates.

    A bi-encoder embeds query and passage independently, so it can only measure
    coarse topical overlap. A cross-encoder reads the pair jointly and is far
    better at rejecting a passage that is on-topic but does not answer the
    question. Too slow to run over a whole corpus, which is exactly why it runs
    only over the fused candidate set.
    """
    global _reranker
    settings = get_settings()
    if not settings.enable_reranker:
        return None
    if _reranker is None:
        with _lock:
            if _reranker is None:
                try:
                    from sentence_transformers import CrossEncoder

                    log.info("Loading reranker %s", settings.reranker_model)
                    _reranker = CrossEncoder(settings.reranker_model, device=settings.device)
                except Exception:
                    log.warning("Reranker unavailable; falling back to fusion order", exc_info=True)
                    _reranker = False  # sentinel: tried and failed, do not retry
    return _reranker or None


def embed_sync(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Encode to L2-normalised vectors, so cosine similarity is a dot product."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    vectors = get_embedder().encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype=np.float32)


async def embed(texts: list[str], batch_size: int = 32) -> np.ndarray:
    return await asyncio.to_thread(embed_sync, texts, batch_size)


def rerank_sync(query: str, passages: list[str]) -> list[float]:
    model = get_reranker()
    if model is None or not passages:
        return [0.0] * len(passages)
    scores = model.predict([(query, p) for p in passages], show_progress_bar=False)
    return [float(s) for s in scores]


async def rerank(query: str, passages: list[str]) -> list[float]:
    return await asyncio.to_thread(rerank_sync, query, passages)


@lru_cache(maxsize=1)
def _cached_prototype_matrix() -> tuple[np.ndarray, tuple[str, ...]]:
    """Embed the taxonomy prototypes once per process.

    Returns a (n_prototypes, dim) matrix plus the dimension key each row belongs
    to, so a chunk can be scored against every dimension with one matmul.
    """
    from app.nlp.taxonomy import TAXONOMY

    texts: list[str] = []
    owners: list[str] = []
    for dimension in TAXONOMY:
        for prototype in dimension.prototypes:
            texts.append(prototype)
            owners.append(dimension.key)
    return embed_sync(texts), tuple(owners)


def prototype_matrix() -> tuple[np.ndarray, tuple[str, ...]]:
    return _cached_prototype_matrix()


def warm_up() -> None:
    """Pay the model-loading cost at startup, not on the first user request."""
    embed_sync(["warm up"])
    prototype_matrix()
    get_reranker()
    log.info("Models warm")
