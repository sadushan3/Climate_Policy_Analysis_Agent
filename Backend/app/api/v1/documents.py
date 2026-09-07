"""Document library endpoints: upload, list, inspect, delete."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.deps import get_current_user
from app.api.v1.schemas import DocumentSummary, UploadResponse
from app.config import get_settings
from app.core.errors import UnsupportedFileType
from app.core.jobs import get_job_manager
from app.services import ingest_service
from app.store import repository as repo

log = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


def _to_summary(doc: dict) -> DocumentSummary:
    return DocumentSummary(
        id=doc["id"],
        name=doc["name"],
        status=doc["status"],
        page_count=doc["page_count"],
        word_count=doc["word_count"],
        chunk_count=doc["chunk_count"],
        created_at=doc["created_at"],
        error=doc.get("error"),
    )


@router.post("", response_model=UploadResponse, status_code=202)
async def upload_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Accept a document and start analysis in the background.

    Returns 202 with a job id immediately rather than holding the connection for
    the length of the analysis.
    """
    settings = get_settings()
    filename = file.filename or "document"
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise UnsupportedFileType(
            f"'{suffix or filename}' is not supported.",
            details={"supported": sorted(settings.allowed_extensions)},
        )

    data = await file.read()
    ingest_service.validate_upload(data, filename)

    # Re-analysing a byte-identical file wastes 30 seconds of compute and an LLM
    # call, so return the existing analysis instead.
    digest = ingest_service.content_hash(data)
    existing = repo.find_by_hash(user["id"], digest)
    if existing:
        log.info("Duplicate upload of %s; reusing %s", filename, existing["id"])
        return UploadResponse(document=_to_summary(existing), job_id=None, deduplicated=True)

    doc_id = repo.create_document(
        owner_id=user["id"],
        name=Path(filename).stem,
        original_name=filename,
        content_hash=digest,
        byte_size=len(data),
    )
    repo.update_document(doc_id, status="processing")

    async def run(handle):
        try:
            return await ingest_service.ingest_document(handle, doc_id, data, filename)
        except Exception as exc:
            repo.update_document(doc_id, status="failed", error=str(exc))
            raise

    job = get_job_manager().submit(
        "ingest", run, meta={"doc_id": doc_id, "filename": filename, "owner_id": user["id"]}
    )
    return UploadResponse(document=_to_summary(repo.get_document(doc_id, user["id"])), job_id=job.id)


@router.get("", response_model=list[DocumentSummary])
async def list_documents(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    return [_to_summary(d) for d in repo.list_documents(user["id"], limit, offset)]


@router.get("/{doc_id}")
async def get_document(doc_id: str, user: dict = Depends(get_current_user)):
    """Full record including the complete analysis payload."""
    doc = repo.get_document(doc_id, user["id"])
    return {
        "id": doc["id"],
        "name": doc["name"],
        "original_name": doc["original_name"],
        "status": doc["status"],
        "error": doc.get("error"),
        "extractor": doc["extractor"],
        "meta": doc["meta"],
        "statistics": {
            "page_count": doc["page_count"],
            "word_count": doc["word_count"],
            "chunk_count": doc["chunk_count"],
            "byte_size": doc["byte_size"],
        },
        "analysis": doc.get("analysis"),
        "created_at": doc["created_at"],
    }


@router.get("/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    repo.get_document(doc_id, user["id"])  # 404s if absent or not the caller's
    chunks = repo.get_chunks(doc_id)
    return {"total": len(chunks), "chunks": chunks[offset : offset + limit]}


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    repo.delete_document(doc_id, user["id"])
