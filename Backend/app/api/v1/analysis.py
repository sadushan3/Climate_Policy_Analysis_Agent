"""Comparison, retrieval and question answering endpoints."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.v1.schemas import CompareRequest, QuestionRequest, SearchRequest
from app.core.jobs import get_job_manager
from app.nlp.taxonomy import TAXONOMY
from app.services import comparison_service, qa_service
from app.store import repository as repo

log = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])


@router.post("/compare", status_code=202)
async def compare(request: CompareRequest, user: dict = Depends(get_current_user)):
    """Start a two-document comparison. Poll or stream the returned job."""
    # Ownership is checked here, before the job is queued -- the background job
    # runs unscoped, so this is the authorisation boundary.
    repo.get_document(request.doc_id_a, user["id"])
    repo.get_document(request.doc_id_b, user["id"])

    async def run(handle):
        return await comparison_service.compare_documents(
            handle, request.doc_id_a, request.doc_id_b
        )

    job = get_job_manager().submit(
        "compare",
        run,
        meta={
            "doc_id_a": request.doc_id_a,
            "doc_id_b": request.doc_id_b,
            "owner_id": user["id"],
        },
    )
    return {"job_id": job.id, "status": "queued"}


@router.post("/search")
async def search(request: SearchRequest, user: dict = Depends(get_current_user)):
    """Hybrid retrieval with no generation -- useful on its own, and the honest
    fallback when no LLM key is configured."""
    retriever = qa_service.build_retriever(request.doc_ids, user["id"])
    hits = await retriever.search(request.query, top_k=request.top_k)
    return {"query": request.query, "results": [h.to_dict() for h in hits]}


@router.post("/ask")
async def ask(request: QuestionRequest, user: dict = Depends(get_current_user)):
    """Grounded answer with resolved citations."""
    return await qa_service.answer_question(
        request.question, request.doc_ids, user["id"], request.top_k
    )


@router.post("/ask/stream")
async def ask_stream(request: QuestionRequest, user: dict = Depends(get_current_user)):
    """Token-streamed answer. Sources arrive first so the UI can render them
    while the text is still being generated."""

    async def events():
        try:
            async for kind, payload in qa_service.stream_answer(
                request.question, request.doc_ids, user["id"], request.top_k
            ):
                yield f"data: {json.dumps({'type': kind, 'payload': payload})}\n\n"
        except Exception as exc:
            log.exception("Streaming answer failed")
            yield f"data: {json.dumps({'type': 'error', 'payload': str(exc)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/taxonomy")
async def taxonomy():
    """The dimension taxonomy the classifier scores against.

    Exposed so the UI can render labels and descriptions without hardcoding
    them, and so the classification scheme is inspectable rather than implicit.
    """
    return {
        "dimensions": [
            {
                "key": d.key,
                "label": d.label,
                "description": d.description,
                "prototype_count": len(d.prototypes),
            }
            for d in TAXONOMY
        ]
    }
