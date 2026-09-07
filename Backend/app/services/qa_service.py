"""Grounded question answering over the document library (RAG).

Every answer is built from retrieved passages and must cite them. Citations are
parsed back out of the response and resolved to real page numbers, so the UI can
show the exact source next to each claim -- and so an unsupported answer is
*detectable* rather than indistinguishable from a supported one.
"""
from __future__ import annotations

import logging
import re

from app.nlp import llm
from app.nlp.retrieval import HybridRetriever
from app.store import repository as repo

log = logging.getLogger(__name__)

_CITATION = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def build_retriever(doc_ids: list[str], owner_id: str) -> HybridRetriever:
    """Build a retriever over the caller's documents only.

    `owner_id` is required rather than optional. Retrieval is the one place a
    tenancy bug would be invisible: an unscoped index silently mixes another
    user's passages into the answer, and the response looks entirely normal.
    Passing the owner through `repo.get_document` makes a foreign id a 404 here,
    before any text is loaded.
    """
    records: list[dict] = []
    for doc_id in doc_ids:
        document = repo.get_document(doc_id, owner_id)
        for chunk in repo.get_chunks(doc_id):
            records.append({**chunk, "document_name": document["name"]})
    vectors = repo.load_vectors_many(doc_ids)
    if len(records) != len(vectors):
        raise ValueError(
            f"Index is out of sync: {len(records)} chunks but {len(vectors)} vectors. "
            "Re-run analysis on the affected documents."
        )
    return HybridRetriever(records, vectors)


_ANSWER_PROMPT = """Context passages from the policy library:

{context}

---

Question: {question}

Answer using only the passages above. Cite the passage number in square brackets \
after each claim, e.g. [2] or [1, 4]. If the passages do not contain the answer, \
say exactly what is missing rather than answering from general knowledge."""


async def answer_question(
    question: str, doc_ids: list[str], owner_id: str, top_k: int | None = None
) -> dict:
    retriever = build_retriever(doc_ids, owner_id)
    hits = await retriever.search(question, top_k=top_k)

    sources = [h.to_dict() for h in hits]
    for source, hit in zip(sources, hits, strict=True):
        record = next(
            (
                r
                for r in retriever.records
                if r["doc_id"] == hit.doc_id and r["chunk_index"] == hit.chunk_index
            ),
            {},
        )
        source["document_name"] = record.get("document_name", "")

    if not hits:
        return {
            "question": question,
            "answer": "No passages in the selected documents are relevant to this question.",
            "sources": [],
            "cited_source_indices": [],
            "grounded": False,
            "answer_source": "retrieval_empty",
        }

    if not llm.is_available():
        # Without a key, return the retrieval result honestly rather than
        # stitching passages together and calling it an answer.
        return {
            "question": question,
            "answer": (
                "Answer generation requires an ANTHROPIC_API_KEY. "
                "The most relevant passages are listed below."
            ),
            "sources": sources,
            "cited_source_indices": [],
            "grounded": False,
            "answer_source": "retrieval_only",
        }

    context = llm.format_context(
        [{**h.to_dict(), "document_name": s.get("document_name", "")} for h, s in zip(hits, sources, strict=True)]
    )
    answer = await llm.complete(
        _ANSWER_PROMPT.format(context=context, question=question), max_tokens=2500
    )

    cited: set[int] = set()
    for match in _CITATION.finditer(answer):
        for part in match.group(1).split(","):
            index = int(part.strip())
            if 1 <= index <= len(sources):
                cited.add(index - 1)

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "cited_source_indices": sorted(cited),
        # An answer that cites nothing is not grounded, whatever it claims.
        "grounded": bool(cited),
        "answer_source": "claude",
    }


async def stream_answer(
    question: str, doc_ids: list[str], owner_id: str, top_k: int | None = None
):
    """Yields ('sources', payload) once, then ('delta', text) repeatedly."""
    retriever = build_retriever(doc_ids, owner_id)
    hits = await retriever.search(question, top_k=top_k)
    sources = [h.to_dict() for h in hits]

    yield "sources", sources

    if not hits or not llm.is_available():
        yield "delta", (
            "No relevant passages found."
            if not hits
            else "Answer generation requires an ANTHROPIC_API_KEY; see the retrieved passages."
        )
        return

    context = llm.format_context([h.to_dict() for h in hits])
    async for delta in llm.stream_text(
        _ANSWER_PROMPT.format(context=context, question=question), max_tokens=2500
    ):
        yield "delta", delta
