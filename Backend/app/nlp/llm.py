"""Optional Claude layer.

Design rules, in priority order:

1. **Never required.** Every caller must work when `llm_enabled` is False. The
   local pipeline produces a complete result on its own; this layer adds
   narrative synthesis, target normalisation and grounded Q&A on top.
2. **Never trusted for facts it was not given.** Prompts carry numbered,
   page-cited context blocks and require the model to cite by block id. An
   answer citing nothing is surfaced as unsupported rather than shown as fact.
3. **Cheap by construction.** The taxonomy and instructions are a stable prefix
   marked with `cache_control`, so repeated calls read the prompt from cache
   instead of paying full input price for it.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from app.config import get_settings
from app.core.errors import LLMUnavailable

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_client = None
_client_lock = asyncio.Lock()


async def get_client():
    """Async Anthropic client, created once."""
    global _client
    settings = get_settings()
    if not settings.llm_enabled:
        raise LLMUnavailable("No ANTHROPIC_API_KEY configured; LLM features are disabled.")
    if _client is None:
        async with _client_lock:
            if _client is None:
                import anthropic

                _client = anthropic.AsyncAnthropic(
                    api_key=settings.anthropic_api_key,
                    timeout=settings.llm_timeout_s,
                    max_retries=settings.llm_max_retries,
                )
                log.info("Anthropic client ready (model=%s)", settings.llm_model)
    return _client


def is_available() -> bool:
    return get_settings().llm_enabled


ANALYST_SYSTEM = """You are a climate policy analyst. You read national climate \
policy documents -- NDCs, climate acts, national adaptation plans, sectoral \
strategies -- and report what they actually commit to.

Rules you follow without exception:

- Ground every factual claim in the numbered context blocks you are given. Cite \
the block id in square brackets, e.g. [3]. A sentence with a number in it must \
carry a citation.
- If the context does not support an answer, say so plainly. Do not fill gaps \
with general knowledge about climate policy, however confident you are.
- Distinguish an unconditional commitment from one that is conditional on \
international finance or support. This distinction is frequently the single most \
important fact about a target.
- Distinguish a binding target from an aspiration, a projection, or a statement \
of context.
- Quote figures exactly as written, including the base year for relative targets. \
"45% below 2005 levels" and "45%" are different claims.
- Write for a policy audience: direct, specific, no hedging filler, no \
restating the question."""


def _system_blocks() -> list[dict]:
    """System prompt as a cacheable block.

    This text is byte-identical on every request, so it forms a stable cache
    prefix. Volatile content (the retrieved context, the user question) goes into
    `messages`, after the breakpoint.
    """
    return [{"type": "text", "text": ANALYST_SYSTEM, "cache_control": {"type": "ephemeral"}}]


def format_context(chunks: list[dict]) -> str:
    """Render retrieved chunks as numbered, citable blocks."""
    lines: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        page = chunk.get("page_start")
        section = chunk.get("section") or ""
        header = f"[{i}] {chunk.get('document_name', 'document')}"
        if section:
            header += f" — {section}"
        if page:
            header += f" (p. {page})"
        lines.append(f"{header}\n{chunk['text']}")
    return "\n\n".join(lines)


async def complete(
    prompt: str,
    *,
    system: list[dict] | str | None = None,
    max_tokens: int | None = None,
    effort: str | None = None,
) -> str:
    """Single text completion. Streams, so long outputs cannot hit a timeout."""
    settings = get_settings()
    client = await get_client()

    async with client.messages.stream(
        model=settings.llm_model,
        max_tokens=max_tokens or settings.llm_max_tokens,
        system=system if system is not None else _system_blocks(),
        thinking={"type": "adaptive"},
        output_config={"effort": effort or settings.llm_effort},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = await stream.get_final_message()

    if message.stop_reason == "refusal":
        raise LLMUnavailable("The model declined to answer this request.")

    return "".join(b.text for b in message.content if b.type == "text").strip()


async def complete_structured(prompt: str, schema: type[T], *, max_tokens: int | None = None) -> T:
    """Completion constrained to a Pydantic schema.

    Uses `output_config.format`, so the response is guaranteed to be JSON that
    validates -- no defensive parsing of prose, no retry loop around a model that
    wrapped its JSON in a code fence.
    """
    settings = get_settings()
    client = await get_client()

    json_schema = schema.model_json_schema()
    json_schema["additionalProperties"] = False

    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=max_tokens or settings.llm_max_tokens,
        system=_system_blocks(),
        thinking={"type": "adaptive"},
        output_config={
            "effort": settings.llm_effort,
            "format": {"type": "json_schema", "schema": json_schema},
        },
        messages=[{"role": "user", "content": prompt}],
    )

    if message.stop_reason == "refusal":
        raise LLMUnavailable("The model declined to answer this request.")

    text = next((b.text for b in message.content if b.type == "text"), "")
    return schema.model_validate(json.loads(text))


async def stream_text(prompt: str, *, system: list[dict] | None = None, max_tokens: int | None = None):
    """Async generator of text deltas, for server-sent-event endpoints."""
    settings = get_settings()
    client = await get_client()

    async with client.messages.stream(
        model=settings.llm_model,
        max_tokens=max_tokens or settings.llm_max_tokens,
        system=system if system is not None else _system_blocks(),
        thinking={"type": "adaptive"},
        output_config={"effort": settings.llm_effort},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def safe_complete(prompt: str, fallback: Any = None, **kwargs) -> Any:
    """Best-effort completion.

    Used wherever the LLM is a bonus rather than the deliverable: an API outage
    degrades that one field to `fallback` instead of failing the whole analysis.
    """
    if not is_available():
        return fallback
    try:
        return await complete(prompt, **kwargs)
    except Exception:
        log.warning("LLM call failed; continuing without it", exc_info=True)
        return fallback
