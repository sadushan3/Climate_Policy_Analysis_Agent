"""Job status and live progress streaming."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.v1.schemas import JobState
from app.core.errors import NotFound
from app.core.jobs import get_job_manager

log = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


def _owned_job(job_id: str, user: dict):
    """Fetch a job the caller owns.

    Job results carry the full analysis of a document, so an unauthenticated or
    unscoped job endpoint would leak exactly what the document endpoints protect.
    A job belonging to someone else is reported as missing, not forbidden, for
    the same anti-enumeration reason as documents.
    """
    job = get_job_manager().get(job_id)
    if job is None or job.meta.get("owner_id") != user["id"]:
        raise NotFound(f"Job '{job_id}' does not exist or has expired.")
    return job


@router.get("/{job_id}", response_model=JobState)
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    return JobState(**_owned_job(job_id, user).to_dict())


@router.get("/{job_id}/result")
async def get_job_result(job_id: str, user: dict = Depends(get_current_user)):
    job = _owned_job(job_id, user)
    return {**job.to_dict(), "result": job.result}


@router.get("/{job_id}/stream")
async def stream_job(job_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Server-sent events carrying progress until the job finishes.

    SSE rather than WebSockets: the traffic is one-directional, it survives
    proxies that mangle WebSocket upgrades, and the browser reconnects on its own.

    Note the trade-off this endpoint now carries: it requires a bearer token, and
    the browser `EventSource` API cannot set request headers. Non-browser clients
    (curl, a worker) can stream it; the web UI polls `GET /jobs/{id}` instead
    rather than moving the token into a query string, where it would end up in
    access logs and browser history.
    """
    manager = get_job_manager()
    _owned_job(job_id, user)

    queue = await manager.subscribe(job_id)

    async def events():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    # Comment frame keeps intermediaries from closing an idle
                    # connection during a long embedding pass.
                    yield ": keep-alive\n\n"
                    continue

                yield f"data: {json.dumps(payload)}\n\n"
                if payload.get("status") in {"succeeded", "failed"}:
                    job = manager.get(job_id)
                    final = {"event": "result", "result": job.result if job else None}
                    yield f"data: {json.dumps(final)}\n\n"
                    break
        finally:
            manager.unsubscribe(job_id, queue)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
