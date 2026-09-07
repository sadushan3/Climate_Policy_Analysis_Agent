"""Zero-shot classification of policy text into the dimension taxonomy.

Method: embed each dimension's natural-language prototypes once, then score each
*sentence* by its maximum cosine similarity to any prototype of that dimension
(max-pooling, not mean-pooling -- a sentence need only match *one* facet of a
dimension to belong to it; averaging over six prototypes washes that signal out).
Sentence scores are then max-pooled up to the passage.

Lexical cues from the taxonomy contribute a small bounded bonus. They can promote
a borderline passage but cannot by themselves clear the threshold, which is what
keeps this from degenerating into the V1 keyword matcher.

Multi-label by construction: a sentence committing finance to coastal defences
is genuinely both Finance and Adaptation, and forcing a single winner loses
information the comparison layer needs.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.nlp import embeddings
from app.nlp.taxonomy import DIMENSION_KEYS, DIMENSIONS_BY_KEY, TAXONOMY

log = logging.getLogger(__name__)

# Per-dimension decision thresholds, fitted on the dev split by
# `python -m eval.run_eval --sweep --write-calibration`.
#
# A single global threshold assumes every dimension's similarity scores live on
# the same scale, and they do not: "Sectoral Coverage" is a broad cross-cutting
# attribute whose passages sit closer to the decision boundary than a narrow,
# distinctive dimension like "Technology & Innovation". One global cut therefore
# either floods the broad dimensions with false positives or starves them of
# recall. Fitting one threshold per dimension costs nothing at inference and is
# the standard fix.
_CALIBRATION_PATH = Path(__file__).parent / "calibration.json"


@lru_cache(maxsize=1)
def _thresholds() -> dict[str, float]:
    """Load fitted per-dimension thresholds, falling back to the global default.

    A missing or malformed file is not fatal: the system degrades to the single
    configured threshold, which is a valid (if blunter) operating point.
    """
    default = get_settings().dimension_threshold
    try:
        data = json.loads(_CALIBRATION_PATH.read_text(encoding="utf-8"))
        fitted = data.get("thresholds", {})
        return {key: float(fitted.get(key, default)) for key in DIMENSION_KEYS}
    except (OSError, ValueError, TypeError):
        log.warning("No usable calibration at %s; using global threshold %.2f", _CALIBRATION_PATH, default)
        return dict.fromkeys(DIMENSION_KEYS, default)


def threshold_vector() -> np.ndarray:
    """Thresholds in taxonomy column order, for vectorised comparison."""
    thresholds = _thresholds()
    return np.array([thresholds[key] for key in DIMENSION_KEYS], dtype=np.float32)

# Cap on the lexical contribution. Both values are the measured optimum from
# `python -m eval.run_eval --sweep`, and the cap is deliberately well below the
# 0.54 decision threshold so cue hits alone can never clear it: a passage still
# has to be semantically close to a prototype to be assigned a dimension.
_CUE_WEIGHT = 0.10
_CUE_MAX = 0.20


@dataclass
class DimensionHit:
    key: str
    label: str
    score: float
    chunk_indices: list[int]
    evidence: list[dict]
    # Sentences matching this dimension, and sentences in the document overall.
    # `share` is derived from these rather than from chunk counts: chunk counts
    # are an artefact of the chunker's token budget, so a short document lands in
    # one chunk and every dimension it touches reports 100% coverage. Sentence
    # counts are a property of the document and stay comparable across lengths.
    sentence_count: int = 0
    total_sentences: int = 0

    @property
    def share(self) -> float:
        return self.sentence_count / self.total_sentences if self.total_sentences else 0.0

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "score": round(self.score, 4),
            "chunk_count": len(self.chunk_indices),
            "sentence_count": self.sentence_count,
            "share": round(self.share, 4),
            "evidence": self.evidence,
        }


def _cue_bonus(text_lower: str, cues: tuple[str, ...]) -> float:
    hits = sum(1 for cue in cues if cue in text_lower)
    return min(hits * _CUE_WEIGHT, _CUE_MAX)


def score_matrix(texts: list[str], vectors: np.ndarray | None = None) -> np.ndarray:
    """Return an (n_texts, n_dimensions) score matrix in taxonomy order."""
    if not texts:
        return np.zeros((0, len(TAXONOMY)), dtype=np.float32)

    if vectors is None:
        vectors = embeddings.embed_sync(texts)

    prototypes, owners = embeddings.prototype_matrix()
    # (n_texts, n_prototypes) cosine similarities -- both sides are normalised.
    similarity = vectors @ prototypes.T

    scores = np.zeros((len(texts), len(TAXONOMY)), dtype=np.float32)
    owners_array = np.asarray(owners)
    for col, dimension in enumerate(TAXONOMY):
        mask = owners_array == dimension.key
        # Max-pool over this dimension's prototypes.
        scores[:, col] = similarity[:, mask].max(axis=1)

    for row, text in enumerate(texts):
        lowered = text.lower()
        for col, dimension in enumerate(TAXONOMY):
            scores[row, col] = min(1.0, scores[row, col] + _cue_bonus(lowered, dimension.cues))

    return scores


def classify_chunks(
    chunks: list[dict],
    vectors: np.ndarray | None = None,
    threshold: float | None = None,
    max_evidence: int = 4,
) -> list[DimensionHit]:
    """Aggregate dimension scores into a document-level profile.

    Scoring happens at *sentence* level, then max-pools up to the chunk. Two
    reasons, and the second is the important one:

      - A 300-word passage that contains one finance commitment and four
        sentences of background averages out to "not about finance". The
        sentence is the unit at which a commitment is actually made.
      - The threshold is calibrated on single labelled sentences
        (`eval/dataset/dimension_labels.jsonl`). Scoring passages with a
        sentence-calibrated threshold would be a train/serve domain shift.
        Scoring sentences keeps calibration and inference on the same
        distribution, so the reported F1 is the F1 you actually get.

    `vectors` (the chunk embeddings used for retrieval) are therefore not reused
    here -- they are the wrong granularity.
    """
    from app.ingestion.chunker import split_sentences

    if not chunks:
        return []

    # An explicit `threshold` (used by the eval harness) overrides calibration
    # uniformly; otherwise each dimension uses its own fitted cut.
    cuts = (
        np.full(len(TAXONOMY), threshold, dtype=np.float32)
        if threshold is not None
        else threshold_vector()
    )

    sentences: list[str] = []
    owner_rows: list[int] = []
    for row, chunk in enumerate(chunks):
        for sentence in split_sentences(chunk["text"]) or [chunk["text"]]:
            if len(sentence) < 25:
                continue  # headings and fragments carry no commitment
            sentences.append(sentence)
            owner_rows.append(row)

    if not sentences:
        return []

    sentence_scores = score_matrix(sentences)

    # Max-pool sentence scores up to their parent chunk.
    scores = np.zeros((len(chunks), len(TAXONOMY)), dtype=np.float32)
    best_sentence: dict[tuple[int, int], str] = {}
    for i, row in enumerate(owner_rows):
        for col in range(len(TAXONOMY)):
            if sentence_scores[i, col] > scores[row, col]:
                scores[row, col] = sentence_scores[i, col]
                best_sentence[(row, col)] = sentences[i]

    per_dimension: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for row in range(len(chunks)):
        for col, dimension in enumerate(TAXONOMY):
            value = float(scores[row, col])
            if value >= cuts[col]:
                per_dimension[dimension.key].append((row, value))

    # Sentence-level counts drive `share`; see DimensionHit for why.
    sentences_per_dimension = (sentence_scores >= cuts).sum(axis=0)

    hits: list[DimensionHit] = []
    for key, matches in per_dimension.items():
        dimension = DIMENSIONS_BY_KEY[key]
        col = DIMENSION_KEYS.index(key)
        matches.sort(key=lambda m: -m[1])
        top = matches[:max_evidence]
        hits.append(
            DimensionHit(
                key=key,
                label=dimension.label,
                sentence_count=int(sentences_per_dimension[col]),
                total_sentences=len(sentences),
                # Document-level confidence is the strongest single passage, not
                # the mean: one unambiguous net-zero commitment is stronger
                # evidence than a hundred passages that vaguely mention energy.
                score=matches[0][1],
                chunk_indices=[row for row, _ in matches],
                evidence=[
                    {
                        # The sentence that actually triggered the match, not the
                        # whole surrounding passage -- this is what a reviewer
                        # needs to see to check the classifier's work.
                        "text": best_sentence.get((row, col)) or _trim(chunks[row]["text"]),
                        "context": _trim(chunks[row]["text"]),
                        "score": round(value, 4),
                        "page_start": chunks[row]["page_start"],
                        "page_end": chunks[row]["page_end"],
                        "section": chunks[row].get("section", ""),
                        "chunk_index": chunks[row]["chunk_index"],
                    }
                    for row, value in top
                ],
            )
        )

    hits.sort(key=lambda h: -h.score)
    return hits


def coverage_profile(hits: list[DimensionHit], total_chunks: int) -> dict[str, dict]:
    """Per-dimension coverage: is it present, and how much of the document is it?

    `share` is the fraction of the document's *sentences* assigned to the
    dimension. That is what makes two documents comparable regardless of length,
    and unlike a chunk-count share it does not collapse to 1.0 on a document
    short enough to fit in a single chunk.
    """
    by_key = {h.key: h for h in hits}
    profile: dict[str, dict] = {}
    for dimension in TAXONOMY:
        hit = by_key.get(dimension.key)
        profile[dimension.key] = {
            "label": dimension.label,
            "present": hit is not None,
            "score": round(hit.score, 4) if hit else 0.0,
            "chunk_count": len(hit.chunk_indices) if hit else 0,
            "sentence_count": hit.sentence_count if hit else 0,
            "share": round(hit.share, 4) if hit else 0.0,
        }
    return profile


def _trim(text: str, limit: int = 340) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[: stop + 1] if stop > limit * 0.5 else cut.rstrip()) + " ..."
