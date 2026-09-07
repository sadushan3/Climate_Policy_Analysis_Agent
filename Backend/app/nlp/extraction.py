"""Structured extraction of quantified commitments.

The single most useful thing you can pull out of a climate policy is the set of
*quantified, dated commitments*: "45% below 2005 levels by 2030", "net zero by
2050", "USD 1.2 billion for adaptation by 2027". V1 returned none of these --
it reported that the word "billion" appeared in a sentence.

Two stages:

  1. A deterministic pass finds candidate sentences by numeric pattern and
     parses what it can with regex. Free, fast, and it always runs.
  2. When an API key is configured, those candidates are handed to Claude with a
     strict JSON schema to normalise the messy cases regex cannot reach
     (co-reference to a base year mentioned two sentences earlier, ranges,
     conditional targets contingent on international support).

Stage 2 is strictly a refinement of stage 1: it only ever sees sentences stage 1
already flagged, so the LLM cannot invent a target out of thin air, and every
record keeps the verbatim source sentence and page for verification.
"""
from __future__ import annotations

import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

TargetType = Literal[
    "emissions_reduction",
    "net_zero",
    "renewable_share",
    "finance",
    "energy_efficiency",
    "sectoral",
    "other",
]


class PolicyTarget(BaseModel):
    """One quantified commitment, always traceable to its source sentence."""

    target_type: TargetType = "other"
    description: str = Field(description="One-line plain-English statement of the commitment.")
    value: float | None = Field(default=None, description="The headline number.")
    unit: str | None = Field(default=None, description="%, MtCO2e, USD, GW, ...")
    target_year: int | None = None
    base_year: int | None = Field(default=None, description="Reference year for a relative target.")
    sector: str | None = None
    conditional: bool = Field(
        default=False,
        description="True if delivery is contingent on international finance or support.",
    )
    # Provenance -- populated by the pipeline, never by the model.
    source_text: str = ""
    page: int | None = None
    section: str = ""
    confidence: float = 0.5
    extractor: str = "rule"


class TargetExtractionResult(BaseModel):
    targets: list[PolicyTarget] = Field(default_factory=list)


# --- deterministic patterns -------------------------------------------------

_YEAR = r"(?:19|20)\d{2}"

# Policy prose states the same deadline a dozen ways: "by 2030", "by the year
# 2040", "by end-2035", "no later than 2050", "through to 2035", "over the period
# to 2030". The eval caught the narrow version silently dropping the deadline
# from a third of targets, then caught the next-narrowest version too.
_BY_YEAR = (
    # Deliberately no bare "to": it swallows the base year in "relative to 2005
    # by 2030" and reports the baseline as the deadline. Every legitimate "to"
    # form is spelled out instead.
    rf"\b(?:by|before|no\s+later\s+than|not\s+later\s+than|through\s+to|up\s+to"
    rf"|over\s+the\s+period\s+to|through)\s+"
    rf"(?:the\s+year\s+|end[\s\-]of[\s\-]|end[\s\-])?(?P<target_year>{_YEAR})"
)

# Percentages are 1-3 digits, but capacities (5000 MW) and volumes are not.
_NUMBER = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?"

_PATTERNS: list[tuple[TargetType, re.Pattern]] = [
    (
        "net_zero",
        re.compile(
            rf"\b(?:net[\s\-]?zero|carbon[\s\-]?neutral(?:ity)?|climate[\s\-]?neutral)\b"
            rf"[^.]{{0,80}}?{_BY_YEAR}",
            re.I,
        ),
    ),
    (
        "emissions_reduction",
        re.compile(
            rf"\b(?:reduc\w+|cut\w*|lower\w*|abat\w*|decreas\w+)\b[^.]{{0,60}}?"
            rf"\b(?P<value>{_NUMBER})\s?(?P<unit>%|per\s?cent)"
            rf"(?:[^.]{{0,60}}?\b(?:below|compared\s+to|relative\s+to|against|from)\s+(?:the\s+)?(?P<base_year>{_YEAR}))?"
            rf"(?:[^.]{{0,60}}?{_BY_YEAR})?",
            re.I,
        ),
    ),
    (
        "renewable_share",
        re.compile(
            # `renewable\b` cannot match the plural "Renewables", which is how
            # roughly half of real policy sentences open this clause.
            rf"\b(?:renewables?|clean|solar|wind|photovoltaic|non[\s\-]?fossil)\b[^.]{{0,60}}?"
            # The word-boundary anchor belongs only on the alphabetic units --
            # `%\b` cannot match in "70% of", which is the common case.
            rf"\b(?P<value>{_NUMBER})\s?(?P<unit>%|per\s?cent|\b(?:GW|MW|TWh)\b)"
            rf"(?:[^.]{{0,60}}?{_BY_YEAR})?",
            re.I,
        ),
    ),
    (
        "finance",
        re.compile(
            r"(?P<currency>US\$|USD|\$|EUR|€|LKR|Rs\.?|GBP|£)\s?"
            rf"(?P<value>{_NUMBER})\s?(?P<scale>billion|bn|million|mn|trillion|crore|lakh)?"
            rf"(?:[^.]{{0,80}}?{_BY_YEAR})?",
            re.I,
        ),
    ),
    (
        "energy_efficiency",
        re.compile(
            rf"\benergy\s+(?:efficiency|intensity)\b[^.]{{0,60}}?"
            rf"\b(?P<value>{_NUMBER})\s?(?P<unit>%|per\s?cent)"
            rf"(?:[^.]{{0,60}}?{_BY_YEAR})?",
            re.I,
        ),
    ),
]

_SCALE = {
    "trillion": 1e12,
    "billion": 1e9,
    "bn": 1e9,
    "crore": 1e7,
    "million": 1e6,
    "mn": 1e6,
    "lakh": 1e5,
}

_CANONICAL_UNITS = {"gw": "GW", "mw": "MW", "twh": "TWh", "kwh": "kWh", "mtco2e": "MtCO2e"}

_CURRENCY = {"us$": "USD", "usd": "USD", "$": "USD", "eur": "EUR", "€": "EUR", "£": "GBP", "gbp": "GBP", "rs": "LKR", "rs.": "LKR", "lkr": "LKR"}

_CONDITIONAL = re.compile(
    r"\b(?:conditional|subject\s+to|contingent\s+(?:up)?on|provided\s+that|"
    r"with\s+(?:adequate\s+)?international\s+(?:support|finance|assistance)|"
    r"if\s+(?:sufficient|adequate)\s+(?:support|finance))\b",
    re.I,
)

# A candidate sentence must contain a number or an explicit neutrality pledge --
# this is what keeps the LLM stage cheap and bounded.
_HAS_COMMITMENT = re.compile(r"\d|\bnet[\s\-]?zero\b|\bcarbon[\s\-]?neutral", re.I)

# A *strong* quantified signal qualifies a sentence on its own. Requiring a modal
# verb as well was silently dropping headline figures: "The total investment
# required ... is estimated at USD 12.6 billion over the period to 2030" states a
# commitment in the passive voice with no "will" anywhere in it, and the flagship
# finance number of the document was being discarded.
_STRONG_SIGNAL = re.compile(
    r"(?:US\$|USD|EUR|€|GBP|£|LKR|Rs\.?|\$)\s?\d"           # a currency amount
    r"|\d{1,3}(?:\.\d+)?\s?(?:%|per\s?cent)"                 # a percentage
    r"|\bnet[\s\-]?zero\b|\bcarbon[\s\-]?neutral"            # a neutrality pledge
    r"|\d+\s?(?:GW|MW|TWh|MtCO2e?|ktCO2e?|km)\b",            # a physical quantity
    re.I,
)

# Weaker numeric signals (a bare year, a count) additionally need a commitment
# verb, or every "Table 3 shows 12 districts" becomes a candidate.
_COMMITMENT_VERB = re.compile(
    r"\b(?:will|shall|commit\w*|target\w*|aim\w*|pledg\w*|plan\w*|seek\w*|"
    r"intend\w*|allocat\w*|mobilis\w*|mobiliz\w*|invest\w*|requir\w*|"
    r"estimat\w*|expect\w*|by\s+20\d\d)\b",
    re.I,
)


def find_candidate_sentences(chunks: list[dict]) -> list[dict]:
    """Sentences that plausibly contain a quantified commitment."""
    from app.ingestion.chunker import split_sentences

    candidates: list[dict] = []
    seen: set[str] = set()
    for chunk in chunks:
        for sentence in split_sentences(chunk["text"]):
            if len(sentence) < 30 or len(sentence) > 700:
                continue
            if not _HAS_COMMITMENT.search(sentence):
                continue
            # Strong signal alone is enough; a weak one needs a commitment verb.
            if not _STRONG_SIGNAL.search(sentence) and not _COMMITMENT_VERB.search(sentence):
                continue
            key = sentence.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "text": sentence.strip(),
                    "page": chunk["page_start"],
                    "section": chunk.get("section", ""),
                    "chunk_index": chunk["chunk_index"],
                }
            )
    return candidates


def _parse_year(value: str | None) -> int | None:
    if not value:
        return None
    year = int(value)
    return year if 1900 <= year <= 2100 else None


def extract_targets_rule_based(candidates: list[dict]) -> list[PolicyTarget]:
    targets: list[PolicyTarget] = []

    for candidate in candidates:
        sentence = candidate["text"]
        conditional = bool(_CONDITIONAL.search(sentence))
        matched_types: set[str] = set()

        for target_type, pattern in _PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue
            groups = match.groupdict()

            value = None
            unit = None
            if groups.get("value"):
                try:
                    value = float(groups["value"].replace(",", ""))
                except ValueError:
                    value = None

            if target_type == "finance" and value is not None:
                value *= _SCALE.get((groups.get("scale") or "").lower(), 1.0)
                unit = _CURRENCY.get((groups.get("currency") or "").lower().strip(), "USD")
            elif groups.get("unit"):
                raw_unit = groups["unit"].lower().replace(" ", "")
                if raw_unit in {"%", "percent"}:
                    unit = "%"
                else:
                    # Physical units have canonical casing: "TWh", not "TWH".
                    unit = _CANONICAL_UNITS.get(raw_unit, groups["unit"].strip())

            # A finance figure inside a sentence that is really an emissions
            # target would double-count; keep the more specific type only.
            if target_type == "finance" and matched_types - {"finance"}:
                continue

            targets.append(
                PolicyTarget(
                    target_type=target_type,
                    description=_summarise(sentence),
                    value=value,
                    unit=unit,
                    target_year=_parse_year(groups.get("target_year")),
                    base_year=_parse_year(groups.get("base_year")),
                    conditional=conditional,
                    source_text=sentence,
                    page=candidate["page"],
                    section=candidate.get("section", ""),
                    # Rule-based hits with both a value and a deadline are the
                    # ones that are almost always right.
                    confidence=0.85 if (value is not None and groups.get("target_year")) else 0.6,
                    extractor="rule",
                )
            )
            matched_types.add(target_type)

    return _deduplicate(targets)


def _summarise(sentence: str, limit: int = 160) -> str:
    text = " ".join(sentence.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _deduplicate(targets: list[PolicyTarget]) -> list[PolicyTarget]:
    """Collapse targets that are the same commitment stated once.

    Keyed on the semantic identity of the commitment rather than the sentence,
    so the same target restated in an executive summary and an annex collapses.
    """
    best: dict[tuple, PolicyTarget] = {}
    for target in targets:
        key = (target.target_type, target.value, target.unit, target.target_year, target.base_year)
        current = best.get(key)
        if current is None or target.confidence > current.confidence:
            best[key] = target
    return sorted(
        best.values(),
        key=lambda t: (-t.confidence, t.target_year or 9999),
    )
