"""Typed application errors mapped to HTTP responses.

Routes raise domain errors; a single handler turns them into a consistent JSON
envelope. No route ever leaks a raw stack trace to the client.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class UnsupportedFileType(AppError):
    status_code = 415
    code = "unsupported_file_type"


class FileTooLarge(AppError):
    status_code = 413
    code = "file_too_large"


class NoTextExtracted(AppError):
    status_code = 422
    code = "no_text_extracted"


class NotFound(AppError):
    status_code = 404
    code = "not_found"


class LLMUnavailable(AppError):
    status_code = 503
    code = "llm_unavailable"


def register_error_handlers(app: FastAPI) -> None:
    import logging

    log = logging.getLogger("app.errors")

    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        log.warning("%s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
        )
