"""Request/response models.

Typed responses give the OpenAPI docs real value and turn a frontend contract
break into a 422 at the boundary instead of `undefined` deep in a React render.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DocumentSummary(BaseModel):
    id: str
    name: str
    status: Literal["pending", "processing", "ready", "failed"]
    page_count: int = 0
    word_count: int = 0
    chunk_count: int = 0
    created_at: str
    error: str | None = None


class UploadResponse(BaseModel):
    document: DocumentSummary
    job_id: str | None = None
    deduplicated: bool = Field(
        default=False,
        description="True when an identical file was already analysed and was reused.",
    )


class JobState(BaseModel):
    job_id: str
    kind: str
    status: Literal["queued", "running", "succeeded", "failed"]
    progress: float
    stage: str
    error: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    elapsed_s: float


class CompareRequest(BaseModel):
    doc_id_a: str
    doc_id_b: str

    @field_validator("doc_id_b")
    @classmethod
    def _distinct(cls, v: str, info):
        if v == info.data.get("doc_id_a"):
            raise ValueError("Choose two different documents to compare.")
        return v


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    doc_ids: list[str] = Field(min_length=1, max_length=10)
    top_k: int | None = Field(default=None, ge=1, le=20)


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    doc_ids: list[str] = Field(min_length=1, max_length=20)
    top_k: int = Field(default=8, ge=1, le=50)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    llm_enabled: bool
    llm_model: str | None
    models_loaded: bool
    document_count: int
