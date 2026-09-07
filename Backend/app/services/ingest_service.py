"""Ingestion + analysis pipeline for a single document."""
from __future__ import annotations

import asyncio
import hashlib
import logging

from app.config import get_settings
from app.core.errors import FileTooLarge
from app.core.jobs import JobHandle
from app.ingestion import chunker, extractors
from app.nlp import classifier, embeddings, extraction, summarizer
from app.store import repository as repo

log = logging.getLogger(__name__)


def validate_upload(data: bytes, filename: str) -> None:
    settings = get_settings()
    limit = settings.max_upload_mb * 1024 * 1024
    if len(data) > limit:
        raise FileTooLarge(
            f"File is {len(data) / 1_048_576:.1f} MB; the limit is {settings.max_upload_mb} MB."
        )
    if not data:
        raise FileTooLarge("File is empty.")


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def ingest_document(handle: JobHandle, doc_id: str, data: bytes, filename: str) -> dict:
    """Extract -> chunk -> embed -> classify -> extract targets -> summarise.

    Every CPU-bound step runs in a worker thread so the event loop keeps serving
    other requests while a large document is processed.
    """
    settings = get_settings()

    await handle.progress(0.05, "extracting text")
    extracted = await asyncio.to_thread(extractors.extract, data, filename)

    await handle.progress(0.18, "segmenting document")
    chunks = await asyncio.to_thread(
        chunker.chunk_document,
        extracted,
        settings.chunk_target_tokens,
        settings.chunk_overlap_tokens,
        settings.min_chunk_chars,
    )
    chunk_dicts = [
        {
            "chunk_index": c.index,
            "text": c.text,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "section": c.section,
            "char_start": c.char_start,
            "char_end": c.char_end,
        }
        for c in chunks
    ]
    repo.save_chunks(doc_id, chunk_dicts)

    await handle.progress(0.35, f"embedding {len(chunk_dicts)} passages")
    vectors = await embeddings.embed([c["text"] for c in chunk_dicts])
    repo.save_vectors(doc_id, vectors)

    await handle.progress(0.55, "classifying policy dimensions")
    hits = await asyncio.to_thread(classifier.classify_chunks, chunk_dicts, vectors)
    profile = classifier.coverage_profile(hits, len(chunk_dicts))

    await handle.progress(0.68, "extracting quantified targets")
    candidates = await asyncio.to_thread(extraction.find_candidate_sentences, chunk_dicts)
    targets = await asyncio.to_thread(extraction.extract_targets_rule_based, candidates)

    await handle.progress(0.80, "summarising")
    extractive = await asyncio.to_thread(
        summarizer.extractive_summary, chunk_dicts, vectors
    )
    abstractive = await summarizer.abstractive_summary(chunk_dicts)

    await handle.progress(0.95, "saving")
    word_count = len(extracted.text.split())
    analysis = {
        "summary": abstractive or extractive,
        "summary_method": "abstractive" if abstractive else "extractive",
        "extractive_summary": extractive,
        "dimensions": [h.to_dict() for h in hits],
        "coverage_profile": profile,
        "targets": [t.model_dump() for t in targets],
        "statistics": {
            "page_count": len(extracted.pages),
            "word_count": word_count,
            "chunk_count": len(chunk_dicts),
            "target_count": len(targets),
            "dimensions_covered": sum(1 for v in profile.values() if v["present"]),
            "dimensions_total": len(profile),
            "conditional_target_count": sum(1 for t in targets if t.conditional),
        },
    }

    repo.update_document(
        doc_id,
        status="ready",
        page_count=len(extracted.pages),
        word_count=word_count,
        chunk_count=len(chunk_dicts),
        extractor=extracted.extractor,
        meta=extracted.meta,
        analysis=analysis,
    )

    log.info(
        "Ingested %s: %d pages, %d chunks, %d targets, %d/%d dimensions",
        filename,
        len(extracted.pages),
        len(chunk_dicts),
        len(targets),
        analysis["statistics"]["dimensions_covered"],
        len(profile),
    )
    return {"doc_id": doc_id, **analysis["statistics"]}
