"""Classification, extraction, alignment and retrieval behaviour."""
from __future__ import annotations

import numpy as np
import pytest

from app.nlp import alignment, classifier, extraction
from app.nlp.taxonomy import DIMENSION_KEYS


def _chunks(texts: list[str]) -> list[dict]:
    return [
        {"chunk_index": i, "text": t, "page_start": 1, "page_end": 1, "section": "", "doc_id": "d"}
        for i, t in enumerate(texts)
    ]


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------

def test_classifier_finds_paraphrased_dimension():
    """The point of the whole approach: no taxonomy keyword appears here.

    "Mitigation" is never written, yet the passage is unambiguously a mitigation
    commitment. V1's keyword matcher could not do this.
    """
    hits = classifier.classify_chunks(
        _chunks(["Unabated coal-fired generation will be retired from the grid before 2035."])
    )
    assert "mitigation" in {h.key for h in hits}


def test_classifier_is_multi_label():
    hits = classifier.classify_chunks(
        _chunks(
            [
                "USD 800 million will be allocated to coastal defences protecting "
                "communities from sea level rise and storm surge."
            ]
        )
    )
    keys = {h.key for h in hits}
    assert {"finance", "adaptation"} <= keys


def test_classifier_rejects_unrelated_text():
    hits = classifier.classify_chunks(
        _chunks(["The cafeteria will serve lunch between twelve and two o'clock on weekdays."])
    )
    assert not hits


def test_cue_bonus_alone_cannot_clear_threshold():
    """The invariant separating this from a keyword matcher.

    Cue hits are capped strictly below the decision threshold, so lexical
    evidence can promote a semantically-close passage but never carry one on
    its own.
    """
    from app.config import get_settings

    assert get_settings().dimension_threshold > classifier._CUE_MAX


def test_evidence_is_a_sentence_not_the_whole_passage():
    passage = (
        "This chapter provides background on national circumstances and describes "
        "the geography of the country. The Government commits to achieving net zero "
        "emissions by 2050. Further detail is provided in the annex to this document."
    )
    hits = classifier.classify_chunks(_chunks([passage]))
    mitigation = next(h for h in hits if h.key == "mitigation")
    evidence = mitigation.evidence[0]["text"]
    assert "net zero" in evidence
    assert "cafeteria" not in evidence
    assert len(evidence) < len(passage)


def test_coverage_profile_covers_every_dimension():
    hits = classifier.classify_chunks(_chunks(["Net zero emissions by 2050."]))
    profile = classifier.coverage_profile(hits, total_chunks=1)
    assert set(profile) == set(DIMENSION_KEYS)
    assert all("share" in v for v in profile.values())


# --------------------------------------------------------------------------
# target extraction
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sentence,expected_type,expected_value,expected_year",
    [
        ("We will reduce emissions by 45% below 2005 levels by 2030.", "emissions_reduction", 45.0, 2030),
        ("The country commits to net zero emissions by 2050.", "net_zero", None, 2050),
        ("Renewable energy will reach 70% of generation by 2030.", "renewable_share", 70.0, 2030),
        ("USD 12.6 billion will be invested by 2030.", "finance", 12_600_000_000.0, 2030),
    ],
)
def test_rule_extraction(sentence, expected_type, expected_value, expected_year):
    candidates = [{"text": sentence, "page": 3, "section": "Targets", "chunk_index": 0}]
    targets = extraction.extract_targets_rule_based(candidates)
    match = next((t for t in targets if t.target_type == expected_type), None)
    assert match is not None, f"no {expected_type} target found in: {sentence}"
    assert match.value == expected_value
    assert match.target_year == expected_year
    assert match.page == 3  # provenance survives


def test_conditional_targets_are_flagged():
    """Conditional vs unconditional is the single most consequential attribute of
    a target, and reporting a conditional pledge as firm is a real analytical
    error."""
    candidates = [
        {
            "text": (
                "We will reduce emissions by 20% by 2030, conditional on the provision "
                "of international climate finance."
            ),
            "page": 1,
            "section": "",
            "chunk_index": 0,
        }
    ]
    targets = extraction.extract_targets_rule_based(candidates)
    assert targets and all(t.conditional for t in targets)


def test_candidate_filter_ignores_prose_without_commitments():
    chunks = _chunks(["This chapter describes the geography and climate of the country."])
    assert extraction.find_candidate_sentences(chunks) == []


def test_duplicate_targets_collapse():
    """The same commitment restated in a summary and an annex is one target."""
    sentence = "We will reduce emissions by 45% below 2005 levels by 2030."
    candidates = [
        {"text": sentence, "page": 1, "section": "Summary", "chunk_index": 0},
        {"text": sentence, "page": 40, "section": "Annex", "chunk_index": 9},
    ]
    targets = extraction.extract_targets_rule_based(candidates)
    assert len([t for t in targets if t.target_type == "emissions_reduction"]) == 1


# --------------------------------------------------------------------------
# alignment
# --------------------------------------------------------------------------

def test_alignment_matches_paraphrases():
    from app.nlp import embeddings

    left = _chunks(["We will cut greenhouse gas emissions by 45% by 2030."])
    right = _chunks(["Emissions will be reduced 45 per cent by the year 2030."])
    lv = embeddings.embed_sync([c["text"] for c in left])
    rv = embeddings.embed_sync([c["text"] for c in right])

    result = alignment.align(left, right, lv, rv, threshold=0.5)
    assert len(result.pairs) == 1
    assert result.pairs[0].similarity > 0.5


def test_alignment_is_one_to_one():
    """Greedy matching lets one generic passage claim to be the counterpart of
    many; the Hungarian assignment forbids it, which is what keeps the reported
    overlap honest."""
    left = _chunks(["Renewable energy targets.", "Coastal adaptation measures.", "Green finance."])
    right = _chunks(["A general statement about climate policy."])
    lv = np.tile(np.array([[1.0, 0.0]], dtype=np.float32), (3, 1))
    rv = np.array([[1.0, 0.0]], dtype=np.float32)

    result = alignment.align(left, right, lv, rv, threshold=0.5)
    assert len(result.pairs) == 1
    assert len(result.unmatched_left) == 2


def test_alignment_handles_empty_side():
    result = alignment.align([], _chunks(["text"]), np.zeros((0, 2), dtype=np.float32), np.ones((1, 2), dtype=np.float32))
    assert result.pairs == []
    assert result.coverage_left == 0.0


def test_profile_divergence_flags_one_sided_coverage():
    profile_a = {"finance": {"label": "Finance", "present": True, "share": 0.3, "score": 0.8}}
    profile_b = {"finance": {"label": "Finance", "present": False, "share": 0.0, "score": 0.0}}
    rows = alignment.profile_divergence(profile_a, profile_b)
    assert rows[0]["verdict"] == "only_a"


def test_equal_share_but_stronger_confidence_breaks_the_tie():
    """Two documents can give a dimension the same volume while one addresses it
    squarely and the other only brushes past it; reporting that as "comparable"
    hides a real difference."""
    profile_a = {"equity": {"label": "Equity", "present": True, "share": 0.19, "score": 0.49}}
    profile_b = {"equity": {"label": "Equity", "present": True, "share": 0.23, "score": 0.83}}
    rows = alignment.profile_divergence(profile_a, profile_b)
    assert rows[0]["verdict"] == "stronger_b"


def test_matching_share_and_confidence_is_comparable():
    profile_a = {"finance": {"label": "Finance", "present": True, "share": 0.20, "score": 0.70}}
    profile_b = {"finance": {"label": "Finance", "present": True, "share": 0.22, "score": 0.74}}
    assert alignment.profile_divergence(profile_a, profile_b)[0]["verdict"] == "comparable"


def test_document_similarity_is_symmetric():
    a = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    b = np.array([[0.7, 0.7]], dtype=np.float32)
    assert alignment.document_similarity(a, b) == pytest.approx(
        alignment.document_similarity(b, a), abs=1e-6
    )
