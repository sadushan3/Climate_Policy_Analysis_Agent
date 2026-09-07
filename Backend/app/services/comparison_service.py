"""Two-document comparison.

This is the feature the product is named for, and in V1 it was a set
intersection over whitespace-split tokens of two halves of the *same* file. Here
it compares two genuinely separate documents along four independent axes:

  1. Semantic alignment  -- which passages make the same commitment (Hungarian).
  2. Dimension coverage  -- which policy areas each document invests in.
  3. Target-level diff   -- same quantified commitment, stronger, weaker, absent.
  4. Narrative synthesis -- an analyst-grade written comparison (LLM, optional).

Axes 1-3 are fully local and always available. Axis 4 is grounded in the output
of 1-3, so the narrative cannot drift from the computed evidence.
"""
from __future__ import annotations

import asyncio
import logging

from app.core.jobs import JobHandle
from app.nlp import alignment, llm
from app.store import repository as repo

log = logging.getLogger(__name__)


def _targets_by_type(targets: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for target in targets:
        grouped.setdefault(target["target_type"], []).append(target)
    return grouped


def diff_targets(targets_a: list[dict], targets_b: list[dict]) -> list[dict]:
    """Compare quantified commitments type by type.

    Ambition is directional and type-dependent: for an emissions cut a *bigger*
    percentage is more ambitious, but for a net-zero date an *earlier* year is.
    Getting that backwards is the kind of bug that survives a demo and fails an
    interview question, so the direction is explicit per type.
    """
    grouped_a = _targets_by_type(targets_a)
    grouped_b = _targets_by_type(targets_b)
    rows: list[dict] = []

    for target_type in sorted(set(grouped_a) | set(grouped_b)):
        list_a = grouped_a.get(target_type, [])
        list_b = grouped_b.get(target_type, [])

        best_a = _headline(target_type, list_a)
        best_b = _headline(target_type, list_b)

        if best_a and not best_b:
            verdict = "only_a"
        elif best_b and not best_a:
            verdict = "only_b"
        elif best_a and best_b:
            verdict = _compare(target_type, best_a, best_b)
        else:
            continue

        rows.append(
            {
                "target_type": target_type,
                "verdict": verdict,
                "a": best_a,
                "b": best_b,
                "a_count": len(list_a),
                "b_count": len(list_b),
            }
        )
    return rows


def _headline(target_type: str, targets: list[dict]) -> dict | None:
    """The single most representative target of a type."""
    if not targets:
        return None
    if target_type == "net_zero":
        dated = [t for t in targets if t.get("target_year")]
        return min(dated, key=lambda t: t["target_year"]) if dated else targets[0]
    valued = [t for t in targets if t.get("value") is not None]
    if valued:
        return max(valued, key=lambda t: (t["value"], t.get("confidence", 0)))
    return targets[0]


def _compare(target_type: str, a: dict, b: dict) -> str:
    if target_type == "net_zero":
        year_a, year_b = a.get("target_year"), b.get("target_year")
        if year_a and year_b:
            if year_a == year_b:
                return "equivalent"
            return "stronger_a" if year_a < year_b else "stronger_b"
        return "both"

    value_a, value_b = a.get("value"), b.get("value")
    if value_a is None or value_b is None:
        return "both"
    # Treat a <2% relative difference as noise rather than a real gap.
    if abs(value_a - value_b) <= max(value_a, value_b) * 0.02:
        return "equivalent"
    return "stronger_a" if value_a > value_b else "stronger_b"


_NARRATIVE_PROMPT = """Two climate policy documents have been compared \
computationally. Below are the computed results. Write the analyst's read of \
this comparison.

DOCUMENT A: {name_a}
DOCUMENT B: {name_b}

Overall semantic similarity: {similarity:.2f}
Passages in A with a counterpart in B: {coverage_a:.0%}
Passages in B with a counterpart in A: {coverage_b:.0%}

DIMENSION COVERAGE (share of each document devoted to each policy area):
{dimensions}

QUANTIFIED TARGET COMPARISON:
{targets}

STRONGEST ALIGNED PASSAGE PAIRS:
{pairs}

CONTENT PRESENT ONLY IN A:
{unique_a}

CONTENT PRESENT ONLY IN B:
{unique_b}

Write, in this order and with these exact headings:

## Verdict
Two or three sentences: which document is more ambitious overall, and on what basis.

## Where they agree
The substantive commitments both documents make.

## Where they diverge
The real differences, with the figures. Be specific about which document is \
stronger on each point and by how much.

## Gaps
What each document leaves out that the other covers. Flag any target that is \
conditional on international support.

Ground every claim in the data above. If the data does not support a judgement \
on some dimension, say so rather than speculating. Do not use the words \
"delve", "leverage", or "robust"."""


def _format_dimensions(rows: list[dict]) -> str:
    return "\n".join(
        f"- {r['label']}: A {r['share_a']:.0%} / B {r['share_b']:.0%} -> {r['verdict']}"
        for r in rows
    ) or "- (none detected)"


def _format_targets(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        a, b = row.get("a"), row.get("b")
        fmt = lambda t: (  # noqa: E731
            f"{t.get('value')}{t.get('unit') or ''} by {t.get('target_year') or 'n/a'}"
            f"{' (conditional)' if t.get('conditional') else ''}"
            if t
            else "none"
        )
        lines.append(f"- {row['target_type']}: A = {fmt(a)}; B = {fmt(b)} -> {row['verdict']}")
    return "\n".join(lines) or "- (no quantified targets found in either document)"


def _format_pairs(pairs: list[dict], limit: int = 8) -> str:
    return "\n".join(
        f"- ({p['similarity']:.2f}) A p.{p['left']['page']}: \"{p['left']['text'][:200]}\"\n"
        f"    B p.{p['right']['page']}: \"{p['right']['text'][:200]}\""
        for p in pairs[:limit]
    ) or "- (no passages aligned above threshold)"


def _format_unique(chunks: list[dict], indices: list[int], limit: int = 6) -> str:
    by_index = {c["chunk_index"]: c for c in chunks}
    picked = [by_index[i] for i in indices[:limit] if i in by_index]
    return "\n".join(f"- p.{c['page_start']}: \"{c['text'][:220]}\"" for c in picked) or "- (none)"


async def compare_documents(handle: JobHandle, doc_id_a: str, doc_id_b: str) -> dict:
    await handle.progress(0.1, "loading documents")
    doc_a = repo.get_document(doc_id_a)
    doc_b = repo.get_document(doc_id_b)

    for doc in (doc_a, doc_b):
        if doc["status"] != "ready":
            raise ValueError(f"Document '{doc['name']}' is not analysed yet (status={doc['status']}).")

    chunks_a = repo.get_chunks(doc_id_a)
    chunks_b = repo.get_chunks(doc_id_b)
    vectors_a = repo.load_vectors(doc_id_a)
    vectors_b = repo.load_vectors(doc_id_b)

    await handle.progress(0.3, "aligning passages")
    result = await asyncio.to_thread(alignment.align, chunks_a, chunks_b, vectors_a, vectors_b)
    similarity = alignment.document_similarity(vectors_a, vectors_b)

    await handle.progress(0.5, "comparing coverage")
    analysis_a = doc_a["analysis"] or {}
    analysis_b = doc_b["analysis"] or {}
    dimension_rows = alignment.profile_divergence(
        analysis_a.get("coverage_profile", {}), analysis_b.get("coverage_profile", {})
    )

    await handle.progress(0.6, "comparing targets")
    target_rows = diff_targets(analysis_a.get("targets", []), analysis_b.get("targets", []))

    payload = {
        "documents": {
            "a": {"id": doc_id_a, "name": doc_a["name"], "page_count": doc_a["page_count"]},
            "b": {"id": doc_id_b, "name": doc_b["name"], "page_count": doc_b["page_count"]},
        },
        "similarity": {
            "overall": round(similarity, 4),
            "coverage_a": round(result.coverage_left, 4),
            "coverage_b": round(result.coverage_right, 4),
            "mean_pair_similarity": round(result.mean_similarity, 4),
            "aligned_pair_count": len(result.pairs),
        },
        "alignment": result.to_dict(),
        "dimensions": dimension_rows,
        "targets": target_rows,
        "unique_to_a": _unique_payload(chunks_a, result.unmatched_left),
        "unique_to_b": _unique_payload(chunks_b, result.unmatched_right),
        "narrative": None,
        "narrative_source": "unavailable",
    }

    await handle.progress(0.75, "writing analysis")
    if llm.is_available():
        prompt = _NARRATIVE_PROMPT.format(
            name_a=doc_a["name"],
            name_b=doc_b["name"],
            similarity=similarity,
            coverage_a=result.coverage_left,
            coverage_b=result.coverage_right,
            dimensions=_format_dimensions(dimension_rows),
            targets=_format_targets(target_rows),
            pairs=_format_pairs(payload["alignment"]["pairs"]),
            unique_a=_format_unique(chunks_a, result.unmatched_left),
            unique_b=_format_unique(chunks_b, result.unmatched_right),
        )
        narrative = await llm.safe_complete(prompt, fallback=None, max_tokens=3000)
        if narrative:
            payload["narrative"] = narrative
            payload["narrative_source"] = "claude"

    return payload


def _unique_payload(chunks: list[dict], indices: list[int], limit: int = 20) -> list[dict]:
    by_index = {c["chunk_index"]: c for c in chunks}
    return [
        {
            "chunk_index": i,
            "text": by_index[i]["text"],
            "page": by_index[i]["page_start"],
            "section": by_index[i].get("section", ""),
        }
        for i in indices[:limit]
        if i in by_index
    ]
