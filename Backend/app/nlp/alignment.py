"""Cross-document semantic alignment.

Replaces V1's `set(a.split()) & set(b.split())`, whose "overlap" was dominated by
"the", "and", "of" and which could not see that "cut emissions 45% by 2030" and
"reduce GHG by 45% relative to 2005 by 2030" say the same thing.

Here both documents are embedded at passage level and matched with the Hungarian
algorithm on the cosine similarity matrix. That gives a *one-to-one* optimal
assignment, which matters: greedy nearest-neighbour matching lets one generic
paragraph in document A ("this plan supports sustainable development") claim to
be the counterpart of eight different paragraphs in B, producing an overlap score
that is far too high. The one-to-one constraint makes the score honest.

Three outputs, which is what a policy analyst actually wants:
  - aligned pairs above threshold      -> shared commitments
  - unmatched passages in A            -> unique to A / missing from B
  - unmatched passages in B            -> unique to B / gaps in A
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class AlignedPair:
    left_index: int
    right_index: int
    similarity: float
    left_text: str
    right_text: str
    left_page: int
    right_page: int
    relation: str  # "equivalent" | "related"

    def to_dict(self) -> dict:
        return {
            "similarity": round(self.similarity, 4),
            "relation": self.relation,
            "left": {"chunk_index": self.left_index, "text": self.left_text, "page": self.left_page},
            "right": {"chunk_index": self.right_index, "text": self.right_text, "page": self.right_page},
        }


@dataclass
class AlignmentResult:
    pairs: list[AlignedPair]
    unmatched_left: list[int]
    unmatched_right: list[int]
    coverage_left: float   # fraction of A that has a counterpart in B
    coverage_right: float
    mean_similarity: float

    def to_dict(self) -> dict:
        return {
            "pairs": [p.to_dict() for p in self.pairs],
            "unmatched_left_count": len(self.unmatched_left),
            "unmatched_right_count": len(self.unmatched_right),
            "coverage_left": round(self.coverage_left, 4),
            "coverage_right": round(self.coverage_right, 4),
            "mean_similarity": round(self.mean_similarity, 4),
        }


# Above this, two passages are treated as making the same commitment; between
# the alignment threshold and this, they are merely on the same topic.
_EQUIVALENT = 0.72


def align(
    left_chunks: list[dict],
    right_chunks: list[dict],
    left_vectors: np.ndarray,
    right_vectors: np.ndarray,
    threshold: float = 0.55,
    max_pairs: int = 60,
) -> AlignmentResult:
    if not left_chunks or not right_chunks:
        return AlignmentResult([], list(range(len(left_chunks))), list(range(len(right_chunks))), 0.0, 0.0, 0.0)

    # Vectors are L2-normalised, so the product is cosine similarity directly.
    similarity = left_vectors @ right_vectors.T

    from scipy.optimize import linear_sum_assignment

    # Hungarian algorithm minimises cost, so maximise similarity by negating.
    # It handles the rectangular case by matching min(n, m) pairs.
    row_idx, col_idx = linear_sum_assignment(-similarity)

    pairs: list[AlignedPair] = []
    matched_left: set[int] = set()
    matched_right: set[int] = set()

    for r, c in zip(row_idx, col_idx, strict=True):
        score = float(similarity[r, c])
        if score < threshold:
            continue
        matched_left.add(int(r))
        matched_right.add(int(c))
        pairs.append(
            AlignedPair(
                left_index=left_chunks[r]["chunk_index"],
                right_index=right_chunks[c]["chunk_index"],
                similarity=score,
                left_text=left_chunks[r]["text"],
                right_text=right_chunks[c]["text"],
                left_page=left_chunks[r]["page_start"],
                right_page=right_chunks[c]["page_start"],
                relation="equivalent" if score >= _EQUIVALENT else "related",
            )
        )

    pairs.sort(key=lambda p: -p.similarity)

    unmatched_left = [left_chunks[i]["chunk_index"] for i in range(len(left_chunks)) if i not in matched_left]
    unmatched_right = [right_chunks[i]["chunk_index"] for i in range(len(right_chunks)) if i not in matched_right]

    mean_similarity = float(np.mean([p.similarity for p in pairs])) if pairs else 0.0

    return AlignmentResult(
        pairs=pairs[:max_pairs],
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
        coverage_left=len(matched_left) / len(left_chunks),
        coverage_right=len(matched_right) / len(right_chunks),
        mean_similarity=mean_similarity,
    )


def document_similarity(left_vectors: np.ndarray, right_vectors: np.ndarray) -> float:
    """Whole-document similarity as the symmetric mean of best-match scores.

    Embedding the full text and comparing the two vectors (V1's approach) is
    dominated by generic policy register -- any two climate documents score ~0.85
    and the number carries no information. Averaging each passage's *best*
    counterpart is sensitive to what the documents actually commit to.
    """
    if left_vectors.size == 0 or right_vectors.size == 0:
        return 0.0
    similarity = left_vectors @ right_vectors.T
    left_to_right = float(similarity.max(axis=1).mean())
    right_to_left = float(similarity.max(axis=0).mean())
    return (left_to_right + right_to_left) / 2


# A dimension must differ by this much in share before the difference is called
# real rather than noise.
_SHARE_MARGIN = 0.05
# ...but two documents can devote the same *volume* to a dimension while one
# addresses it explicitly and the other only glances at it. A confidence gap this
# large is a genuine difference in how squarely the dimension is addressed, so it
# breaks a share tie rather than being reported as "comparable".
_SCORE_MARGIN = 0.15


def profile_divergence(profile_a: dict[str, dict], profile_b: dict[str, dict]) -> list[dict]:
    """Per-dimension gap analysis: where does one document invest and the other not?"""
    rows: list[dict] = []
    for key, a in profile_a.items():
        b = profile_b.get(key, {"share": 0.0, "present": False, "label": a["label"], "score": 0.0})
        delta = a["share"] - b["share"]
        score_delta = a["score"] - b["score"]

        if a["present"] and not b["present"]:
            verdict = "only_a"
        elif b["present"] and not a["present"]:
            verdict = "only_b"
        elif abs(delta) >= _SHARE_MARGIN:
            verdict = "stronger_a" if delta > 0 else "stronger_b"
        elif abs(score_delta) >= _SCORE_MARGIN:
            verdict = "stronger_a" if score_delta > 0 else "stronger_b"
        else:
            verdict = "comparable"
        rows.append(
            {
                "key": key,
                "label": a["label"],
                "share_a": a["share"],
                "share_b": b["share"],
                "score_a": a["score"],
                "score_b": b["score"],
                "delta": round(delta, 4),
                "score_delta": round(score_delta, 4),
                "verdict": verdict,
            }
        )
    rows.sort(key=lambda r: -abs(r["delta"]))
    return rows
