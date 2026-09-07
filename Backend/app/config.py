"""Application settings.

Single source of truth for every tunable in the system. Everything is
overridable via environment variables or a `.env` file, so the same image runs
in dev, test and prod without code changes.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------------- service ----------------
    app_name: str = "Climate Policy Intelligence API"
    version: str = "2.0.0"
    environment: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    log_json: bool = False

    # CORS: explicit allowlist. `*` with credentials is rejected by browsers and
    # is a real finding in any security review.
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # ---------------- storage ----------------
    data_dir: Path = BASE_DIR / "var"
    max_upload_mb: int = 40
    allowed_extensions: set[str] = Field(default_factory=lambda: {".pdf", ".docx", ".txt", ".md"})

    # ---------------- chunking ----------------
    chunk_target_tokens: int = 320
    chunk_overlap_tokens: int = 64
    min_chunk_chars: int = 120

    # ---------------- models ----------------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_reranker: bool = True
    device: str = "cpu"

    # ---------------- retrieval ----------------
    retrieval_top_k: int = 40          # candidates pulled from each retriever
    rerank_top_k: int = 8              # chunks that survive into the LLM context
    rrf_k: int = 60                    # Reciprocal Rank Fusion smoothing constant

    # ---------------- classification ----------------
    # Cosine floor for assigning a sentence to a policy dimension. This is the
    # measured F1 optimum from `python -m eval.run_eval --sweep`, not a guess.
    dimension_threshold: float = 0.54
    alignment_threshold: float = 0.55  # min cosine for a cross-document sentence pair

    # ---------------- LLM (optional) ----------------
    anthropic_api_key: str | None = None
    llm_model: str = "claude-opus-5"
    llm_effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"
    llm_max_tokens: int = 8000
    llm_timeout_s: float = 180.0
    llm_max_retries: int = 3

    # ---------------- jobs ----------------
    job_concurrency: int = 2
    job_ttl_seconds: int = 60 * 60

    # ---------------- auth ----------------
    # No usable default. A dev run generates an ephemeral secret (see the
    # validator below); production must supply one or the app refuses to start,
    # because a hardcoded fallback secret means anyone can mint valid tokens.
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "climate-policy-api"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    # Allow signup. Turning this off makes the deployment invite-only.
    allow_registration: bool = True
    # Brute-force protection on the login endpoint.
    login_max_attempts: int = 8
    login_window_seconds: int = 300

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def llm_enabled(self) -> bool:
        """The LLM layer is strictly additive: absent a key, every endpoint
        still returns a complete (local-model) result."""
        return bool(self.anthropic_api_key)

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "policy.db"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    for p in (s.data_dir, s.upload_dir, s.index_dir):
        p.mkdir(parents=True, exist_ok=True)

    if not s.jwt_secret:
        if s.environment == "prod":
            # Refusing to boot is the correct behaviour. A generated secret in
            # production would silently invalidate every token on restart, and a
            # hardcoded one would let anyone forge them.
            raise RuntimeError(
                "JWT_SECRET must be set in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        import logging
        import secrets

        s.jwt_secret = secrets.token_urlsafe(48)
        logging.getLogger(__name__).warning(
            "JWT_SECRET is unset; generated an ephemeral one for %s. "
            "Tokens will be invalidated on restart.",
            s.environment,
        )

    return s
