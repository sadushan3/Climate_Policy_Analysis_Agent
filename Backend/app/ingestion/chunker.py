"""Structure-aware chunking.

Naive fixed-window chunking splits a policy target away from the sentence that
qualifies it ("...by 2030" / "...relative to 2005 levels"), which is exactly the
kind of error that shows up as a wrong answer at demo time. This chunker packs
whole sentences up to a token budget, never crosses a detected section heading,
and carries a sentence-aligned overlap so a target and its qualifier co-occur in
at least one chunk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ingestion.extractors import ExtractedDocument

# Matches the numbering conventions policy documents actually use:
# "3.2 Mitigation", "ARTICLE IV - Finance", "CHAPTER 2:", "Annex B".
_HEADING = re.compile(
    r"""^(
        (?:\d+(?:\.\d+)*[.)]?\s+[A-Z][^\n]{2,80})          # 3.2 Mitigation targets
        | (?:(?:CHAPTER|SECTION|PART|ARTICLE|ANNEX|APPENDIX)\s+[\dIVXLC]+[^\n]{0,80})
        | (?:[A-Z][A-Z \-&/,']{6,70})                       # ALL CAPS HEADING
    )$""",
    re.VERBOSE,
)

# Candidate sentence boundary: terminal punctuation followed by whitespace and
# something that could open a sentence.
_BOUNDARY = re.compile(r"[.!?]['\")\]]?\s+(?=[A-Z\"'(\[])")

# Abbreviations whose trailing period is not a sentence end. Python's `re` only
# supports fixed-width lookbehind, so these are checked against the preceding
# token in code rather than encoded in the pattern.
_ABBREVIATIONS = frozenset(
    ["no", "art", "arts", "sec", "secs", "fig", "figs", "dr", "mr", "mrs", "ms", "prof", "st", "vs", "etc", "eg", "ie", "approx", "cf", "al", "para", "paras", "ch", "chap", "vol", "ed", "eds", "inc", "ltd", "co", "dept", "govt", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec"]
)

_TRAILING_TOKEN = re.compile(r"([A-Za-z\.]+)\.['\")\]]?$")


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (~4 chars/token) that avoids loading a tokenizer.

    Used only for chunk budgeting, where being within ~15% is sufficient.
    """
    return max(1, len(text) // 4)


def _is_real_boundary(text: str, end: int) -> bool:
    """Decide whether the period at `end` actually ends a sentence.

    Rejects two cases that otherwise shred policy text: a known abbreviation
    ("Act No. 12 of 2021") and a single-letter initial or dotted acronym
    ("U.S. Government", "J. Smith").
    """
    match = _TRAILING_TOKEN.search(text[:end])
    if not match:
        return True
    token = match.group(1)
    if token.lower().strip(".") in _ABBREVIATIONS:
        return False
    # "U.S", "U", "N.G.O" -- an acronym or initial, not a sentence end.
    return not all(len(part) <= 1 for part in token.split(".") if part)


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    start = 0
    for match in _BOUNDARY.finditer(text):
        if not _is_real_boundary(text, match.start() + 1):
            continue
        piece = text[start : match.start() + 1].strip()
        if piece:
            sentences.append(piece)
        start = match.end()

    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


@dataclass
class Chunk:
    index: int
    text: str
    page_start: int
    page_end: int
    section: str = ""
    char_start: int = 0
    char_end: int = 0
    token_estimate: int = 0
    meta: dict = field(default_factory=dict)

    @property
    def citation(self) -> str:
        pages = (
            f"p. {self.page_start}"
            if self.page_start == self.page_end
            else f"pp. {self.page_start}-{self.page_end}"
        )
        return f"{self.section} ({pages})" if self.section else pages


@dataclass
class _Segment:
    """A run of text under one heading."""

    section: str
    text: str
    char_start: int


def _segment_by_heading(doc: ExtractedDocument) -> list[_Segment]:
    segments: list[_Segment] = []
    current_section = ""
    buffer: list[str] = []
    buffer_start = 0
    cursor = 0

    for line in doc.text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped and _HEADING.match(stripped) and len(stripped) < 100:
            if buffer:
                segments.append(_Segment(current_section, "".join(buffer), buffer_start))
            current_section = stripped
            buffer, buffer_start = [], cursor + len(line)
        else:
            if not buffer:
                buffer_start = cursor
            buffer.append(line)
        cursor += len(line)

    if buffer:
        segments.append(_Segment(current_section, "".join(buffer), buffer_start))
    return [s for s in segments if s.text.strip()]


def _flush(
    chunks: list[Chunk],
    doc: ExtractedDocument,
    section: str,
    sentence_buf: list[str],
    start_offset: int,
    min_chars: int,
) -> None:
    """Emit the buffered sentences as a chunk, or merge them into the previous one.

    A module-level function rather than a closure over the segment loop: a
    closure would capture the loop variable by reference, so any future change
    that defers the call (batching, async) would silently attribute chunks to the
    wrong section.
    """
    body = " ".join(sentence_buf).strip()
    if not body:
        return

    if len(body) < min_chars and chunks and chunks[-1].section == section:
        # Too small to stand alone: merge into the previous chunk rather than
        # emitting a fragment that pollutes retrieval.
        prev = chunks[-1]
        prev.text = f"{prev.text} {body}".strip()
        prev.char_end = start_offset + len(body)
        prev.page_end = doc.page_for_offset(prev.char_end - 1)
        prev.token_estimate = estimate_tokens(prev.text)
        return

    end_offset = start_offset + len(body)
    chunks.append(
        Chunk(
            index=len(chunks),
            text=body,
            page_start=doc.page_for_offset(start_offset),
            page_end=doc.page_for_offset(max(start_offset, end_offset - 1)),
            section=section,
            char_start=start_offset,
            char_end=end_offset,
            token_estimate=estimate_tokens(body),
        )
    )


def chunk_document(
    doc: ExtractedDocument,
    target_tokens: int = 320,
    overlap_tokens: int = 64,
    min_chars: int = 120,
) -> list[Chunk]:
    chunks: list[Chunk] = []

    for segment in _segment_by_heading(doc):
        sentences = split_sentences(segment.text)
        if not sentences:
            continue

        buf: list[str] = []
        buf_tokens = 0

        def flush(sentence_buf: list[str], start_offset: int, _section=segment.section) -> None:
            _flush(chunks, doc, _section, sentence_buf, start_offset, min_chars)

        chunk_start = doc.text.find(sentences[0], segment.char_start)
        if chunk_start < 0:
            chunk_start = segment.char_start

        for sentence in sentences:
            sentence_tokens = estimate_tokens(sentence)

            if buf and buf_tokens + sentence_tokens > target_tokens:
                flush(buf, chunk_start)

                # Carry back whole trailing sentences as overlap so a numeric
                # target keeps the sentence that qualifies it.
                carry: list[str] = []
                carried = 0
                for prev_sentence in reversed(buf):
                    prev_tokens = estimate_tokens(prev_sentence)
                    if carried + prev_tokens > overlap_tokens:
                        break
                    carry.insert(0, prev_sentence)
                    carried += prev_tokens

                buf = carry
                buf_tokens = carried
                anchor = carry[0] if carry else sentence
                found = doc.text.find(anchor, chunk_start)
                chunk_start = found if found >= 0 else chunk_start

            buf.append(sentence)
            buf_tokens += sentence_tokens

        if buf:
            flush(buf, chunk_start)

    # Re-index after any merges so `index` stays dense and usable as a key.
    for i, chunk in enumerate(chunks):
        chunk.index = i
    return chunks
