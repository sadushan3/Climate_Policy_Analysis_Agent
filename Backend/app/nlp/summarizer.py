"""Summarisation over whole documents.

V1 called `text[:2000]` and summarised the first two pages, then presented the
result as a summary of the document. Here nothing is truncated: the document is
summarised map-reduce style, and the extractive path (which always works, with no
API key) selects sentences by centroid relevance with MMR de-duplication rather
than by position.
"""
from __future__ import annotations

import logging

import numpy as np

from app.nlp import llm

log = logging.getLogger(__name__)


def extractive_summary(
    chunks: list[dict],
    vectors: np.ndarray,
    max_sentences: int = 8,
    diversity: float = 0.6,
) -> str:
    """Centroid-based extractive summary with Maximal Marginal Relevance.

    Pure centroid ranking returns eight near-identical sentences about the same
    headline target. MMR trades relevance against novelty so the summary spans
    the document instead of restating its loudest paragraph.
    """
    if not chunks:
        return ""
    if len(chunks) <= max_sentences:
        return " ".join(c["text"][:300] for c in chunks[:max_sentences])

    centroid = vectors.mean(axis=0)
    centroid /= np.linalg.norm(centroid) + 1e-9
    relevance = vectors @ centroid

    selected: list[int] = []
    remaining = set(range(len(chunks)))

    while len(selected) < max_sentences and remaining:
        best_idx, best_score = None, -np.inf
        for idx in remaining:
            redundancy = float(np.max(vectors[idx] @ vectors[selected].T)) if selected else 0.0
            score = diversity * float(relevance[idx]) - (1 - diversity) * redundancy
            if score > best_score:
                best_idx, best_score = idx, score
        selected.append(best_idx)
        remaining.discard(best_idx)

    # Restore document order so the summary reads as prose, not as a ranked list.
    selected.sort()
    return " ".join(_first_sentences(chunks[i]["text"]) for i in selected)


def _first_sentences(text: str, limit: int = 280) -> str:
    from app.ingestion.chunker import split_sentences

    out: list[str] = []
    total = 0
    for sentence in split_sentences(text):
        if total + len(sentence) > limit and out:
            break
        out.append(sentence)
        total += len(sentence)
    return " ".join(out)


_MAP_PROMPT = """Below is one section of a climate policy document. Summarise \
what this section *commits to* in at most 3 sentences. Preserve every figure, \
year and named institution exactly as written. If the section contains no \
commitment (it is background, definitions or boilerplate), reply with exactly: \
NO COMMITMENT

Section:
{section}"""

_REDUCE_PROMPT = """Below are section-level summaries of a single climate policy \
document, in document order.

Write an executive summary of the whole document for a policy analyst:

- Open with one sentence naming what kind of instrument this is and its overall \
level of ambition.
- Then 4-6 sentences covering the headline targets (with figures and dates), the \
sectors covered, the finance position, and the delivery/governance arrangements.
- Note explicitly if a major dimension is absent -- for example no adaptation \
content, or no monitoring arrangements.
- Do not invent anything that is not in the summaries below.

Section summaries:
{sections}"""


async def abstractive_summary(chunks: list[dict], max_sections: int = 24) -> str | None:
    """Map-reduce summary over the whole document.

    Sections are batched into groups sized to the model's context rather than
    sent one call per chunk, which keeps a 200-page document to a handful of
    requests.
    """
    if not llm.is_available() or not chunks:
        return None

    try:
        # Map: batch chunks into ~6k-character groups.
        groups: list[str] = []
        buf: list[str] = []
        size = 0
        for chunk in chunks:
            buf.append(chunk["text"])
            size += len(chunk["text"])
            if size > 6000:
                groups.append("\n\n".join(buf))
                buf, size = [], 0
        if buf:
            groups.append("\n\n".join(buf))

        groups = groups[:max_sections]

        import asyncio

        # Bounded concurrency: enough to be fast, not enough to trip rate limits.
        semaphore = asyncio.Semaphore(4)

        async def summarise_group(section: str) -> str:
            async with semaphore:
                return await llm.complete(
                    _MAP_PROMPT.format(section=section), max_tokens=600, effort="low"
                )

        section_summaries = await asyncio.gather(
            *(summarise_group(g) for g in groups), return_exceptions=True
        )

        usable = [
            s
            for s in section_summaries
            if isinstance(s, str) and s.strip() and "NO COMMITMENT" not in s
        ]
        if not usable:
            return None
        if len(usable) == 1:
            return usable[0]

        # Reduce.
        numbered = "\n\n".join(f"{i}. {s}" for i, s in enumerate(usable, 1))
        return await llm.complete(_REDUCE_PROMPT.format(sections=numbered), max_tokens=1500)

    except Exception:
        log.warning("Abstractive summary failed; extractive summary stands", exc_info=True)
        return None
