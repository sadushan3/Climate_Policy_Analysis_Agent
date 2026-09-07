"""Application entrypoint.

Uses the lifespan protocol rather than the deprecated `@app.on_event("startup")`
V1 used, and warms models in a worker thread so the process starts serving
`/health` immediately instead of appearing dead for 30 seconds while torch loads.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import analysis, auth, documents, jobs
from app.api.v1.schemas import HealthResponse
from app.config import get_settings
from app.core.errors import register_error_handlers
from app.core.jobs import get_job_manager
from app.core.logging import configure_logging, request_id_var
from app.nlp import embeddings
from app.store import repository as repo
from app.store import users as user_store

log = logging.getLogger(__name__)

_state = {"models_loaded": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    log.info("Starting %s v%s (env=%s)", settings.app_name, settings.version, settings.environment)

    repo.init_db()
    user_store.init_user_tables()

    purged = user_store.purge_expired_tokens()
    if purged:
        log.info("Purged %d expired refresh tokens", purged)

    async def warm():
        try:
            await asyncio.to_thread(embeddings.warm_up)
            _state["models_loaded"] = True
        except Exception:
            # A model that fails to load is a real failure, but it should surface
            # through /health rather than crash the process before it can report.
            log.exception("Model warm-up failed; endpoints requiring models will error")

    warm_task = asyncio.create_task(warm())

    log.info("LLM layer: %s", "enabled" if settings.llm_enabled else "disabled (no API key)")
    yield

    warm_task.cancel()
    await get_job_manager().shutdown()
    log.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Analyse, compare and query climate policy documents. "
            "Hybrid retrieval over local embedding models, with an optional "
            "Claude layer for grounded synthesis."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        # An explicit allowlist -- `["*"]` with credentials is rejected by
        # browsers and fails any security review.
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.1f}"
        if not request.url.path.endswith(("/stream", "/health")):
            log.info("%s %s -> %s (%.0fms)", request.method, request.url.path, response.status_code, duration_ms)
        return response

    register_error_handlers(app)

    v1 = APIRouter(prefix="/api/v1")
    v1.include_router(auth.router)
    v1.include_router(documents.router)
    v1.include_router(jobs.router)
    v1.include_router(analysis.router)
    app.include_router(v1)

    @app.get("/health", response_model=HealthResponse, tags=["ops"])
    async def health():
        try:
            document_count = repo.count_documents()
        except Exception:
            document_count = -1
        return HealthResponse(
            status="ok" if _state["models_loaded"] else "warming",
            version=settings.version,
            environment=settings.environment,
            llm_enabled=settings.llm_enabled,
            llm_model=settings.llm_model if settings.llm_enabled else None,
            models_loaded=_state["models_loaded"],
            document_count=document_count,
        )

    @app.get("/", include_in_schema=False)
    async def root():
        return {"service": settings.app_name, "version": settings.version, "docs": "/docs"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
