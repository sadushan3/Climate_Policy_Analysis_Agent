"""Extraction and chunking.

The regressions guarded here are the ones that silently corrupted V1's output:
numbers being stripped by the sanitiser, and chunk boundaries losing the page a
passage came from.
"""
from __future__ import annotations

import pytest

from app.core.errors import NoTextExtracted, UnsupportedFileType
from app.ingestion import chunker, extractors


def test_normalise_preserves_figures():
    """The V1 sanitiser deleted %, $ and ° -- i.e. every target in the document."""
    raw = "Reduce emissions by 45% below 2005 levels, investing US$1.2 billion at 1.5°C."
    cleaned = extractors.normalise_whitespace(raw)
    for token in ("45%", "US$1.2", "1.5", "2005"):
        assert token in cleaned, f"{token} was destroyed by normalisation"


def test_normalise_dehyphenates_across_line_breaks():
    assert "emissions" in extractors.normalise_whitespace("The emis-\nsions target")


def test_normalise_keeps_paragraph_breaks():
    out = extractors.normalise_whitespace("Para one.\n\n\n\nPara two.")
    assert out.count("\n\n") == 1


def test_extract_text_assigns_pages(policy_a_text):
    doc = extractors.extract(policy_a_text.encode(), "policy.txt")
    assert doc.pages
    assert doc.pages[0].number == 1
    assert doc.text.strip()


def test_page_lookup_covers_every_offset(policy_a_text):
    doc = extractors.extract(policy_a_text.encode(), "policy.txt")
    for offset in range(0, len(doc.text), 97):
        assert doc.page_for_offset(offset) >= 1


def test_unsupported_extension_rejected():
    with pytest.raises(UnsupportedFileType):
        extractors.extract(b"data", "malware.exe")


def test_empty_document_rejected():
    with pytest.raises(NoTextExtracted):
        extractors.extract(b"   ", "empty.txt")


def test_chunks_carry_page_and_section(policy_a_text):
    doc = extractors.extract(policy_a_text.encode(), "policy.txt")
    chunks = chunker.chunk_document(doc, target_tokens=80, overlap_tokens=16)
    assert chunks
    for chunk in chunks:
        assert chunk.page_start >= 1
        assert chunk.page_end >= chunk.page_start
        assert chunk.text.strip()
        assert chunk.citation


def test_chunks_are_densely_indexed(policy_a_text):
    doc = extractors.extract(policy_a_text.encode(), "policy.txt")
    chunks = chunker.chunk_document(doc, target_tokens=60, overlap_tokens=12)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_chunking_loses_no_targets(policy_a_text):
    """Every quantified target in the source must survive into some chunk.

    This is the property that matters: a chunker that drops "45%" makes the whole
    downstream analysis wrong, and it fails silently.
    """
    doc = extractors.extract(policy_a_text.encode(), "policy.txt")
    chunks = chunker.chunk_document(doc, target_tokens=90, overlap_tokens=20)
    combined = " ".join(c.text for c in chunks)
    for figure in ("45%", "2050", "70%", "12.6 billion", "2027", "120 km"):
        assert figure in combined, f"chunking lost {figure}"


def test_section_headings_detected(policy_a_text):
    doc = extractors.extract(policy_a_text.encode(), "policy.txt")
    chunks = chunker.chunk_document(doc, target_tokens=90, overlap_tokens=20)
    sections = {c.section for c in chunks if c.section}
    assert sections, "no section headings were detected"


def test_sentence_splitter_handles_abbreviations():
    sentences = chunker.split_sentences(
        "Under Act No. 12 of 2021 the U.S. Government acted. A second sentence follows."
    )
    assert len(sentences) == 2


def test_repeated_headers_are_stripped():
    """A running header repeats on every page; the body does not.

    Detection is by cross-page frequency, so the body lines must genuinely vary
    -- which is what a real document looks like.
    """
    pages = [f"MINISTRY OF ENVIRONMENT\nSubstantive paragraph number {i}." for i in range(6)]
    cleaned = extractors._strip_repeated_lines(pages)
    assert all("MINISTRY OF ENVIRONMENT" not in page for page in cleaned)
    for i, page in enumerate(cleaned):
        assert f"Substantive paragraph number {i}." in page


def test_short_documents_keep_all_lines():
    """Frequency-based detection needs enough pages to be meaningful; below that
    it must not fire, or a 2-page document loses half its content."""
    pages = ["HEADER\nBody."] * 3
    assert extractors._strip_repeated_lines(pages) == pages
