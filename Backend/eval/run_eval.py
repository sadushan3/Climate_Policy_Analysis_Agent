"""Evaluation harness.

    python -m eval.run_eval              # report test-split results
    python -m eval.run_eval --sweep      # calibrate on dev, report on test
    python -m eval.run_eval --ablate     # is hybrid retrieval worth it?

Three evaluations:

  1. Dimension classification -- multi-label precision / recall / F1.
  2. Target extraction -- field-level accuracy, plus false positives on prose
     that contains numbers but states no commitment.
  3. Retrieval -- recall@k and MRR, reported separately for paraphrase and
     rare-literal queries, which is the evidence that hybrid retrieval earns
     its complexity rather than being cargo-culted in.

**Methodology.** Every dataset is split into `dev` and `test`. All tuning --
thresholds, cue weights, fusion constants -- is done against `dev` only; `test`
is scored once and is what gets reported. An earlier version of this harness
calibrated the threshold on the same sentences it reported F1 on, which
overstated performance; the split exists to make that mistake impossible rather
than merely discouraged.

**Limits, stated plainly.** The labels are written by one annotator (the
author), and the same author wrote the taxonomy prototypes the classifier scores
against. That circularity means these numbers measure internal consistency and
guard against regression -- they are not an unbiased estimate of accuracy on
documents from the wild. A second annotator and text sampled from real published
NDCs are what would turn this into a benchmark.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).parent / "dataset"

DIM_F1_FLOOR = 0.65        # CI fails below these; set just under current, as a
                           # regression guard rather than an aspiration.
TARGET_DETECTION_FLOOR = 0.85
RETRIEVAL_RECALL_FLOOR = 0.80


def load_jsonl(path: Path, split: str | None = None) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    return [r for r in rows if split is None or r.get("split") == split]


def _rule(title: str, subtitle: str = "") -> None:
    print(f"\n{'=' * 72}\n{title}" + (f"  ({subtitle})" if subtitle else "") + f"\n{'=' * 72}")


# ==========================================================================
# 1. dimension classification
# ==========================================================================

def evaluate_dimensions(threshold, scores, gold, keys) -> dict:
    tp = fp = fn = 0
    per_dimension: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for row, truth in enumerate(gold):
        predicted = {keys[col] for col in range(len(keys)) if scores[row, col] >= threshold}
        for key in predicted & truth:
            tp += 1
            per_dimension[key]["tp"] += 1
        for key in predicted - truth:
            fp += 1
            per_dimension[key]["fp"] += 1
        for key in truth - predicted:
            fn += 1
            per_dimension[key]["fn"] += 1

    def prf(t, f_p, f_n):
        precision = t / (t + f_p) if (t + f_p) else 0.0
        recall = t / (t + f_n) if (t + f_n) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return precision, recall, f1

    micro_p, micro_r, micro_f1 = prf(tp, fp, fn)

    # Negatives (rows labelled with no dimension) are scored separately: on this
    # kind of taxonomy a model can look strong on micro-F1 while tagging every
    # paragraph of boilerplate, and that failure is invisible in the micro score.
    negative_rows = [i for i, truth in enumerate(gold) if not truth]
    clean_negatives = sum(
        1
        for i in negative_rows
        if not any(scores[i, col] >= threshold for col in range(len(keys)))
    )

    return {
        "threshold": round(float(threshold), 3),
        "micro": {"precision": micro_p, "recall": micro_r, "f1": micro_f1, "tp": tp, "fp": fp, "fn": fn},
        "negative_rejection": {
            "correct": clean_negatives,
            "total": len(negative_rows),
            "rate": clean_negatives / len(negative_rows) if negative_rows else 1.0,
        },
        "per_dimension": {
            key: dict(
                zip(("precision", "recall", "f1"), prf(v["tp"], v["fp"], v["fn"]), strict=True),
                support=v["tp"] + v["fn"],
            )
            for key, v in sorted(per_dimension.items())
        },
    }


def fit_per_dimension_thresholds(dev_rows: list[dict], keys: tuple[str, ...]) -> dict[str, float]:
    """Fit one threshold per dimension on the dev split.

    Each dimension is a separate binary decision, so each gets its own F1-optimal
    cut. Where a dimension has too little dev support for the optimum to mean
    anything (fewer than 4 positives), it keeps the global default rather than
    inheriting a threshold fitted on two examples.
    """
    from app.config import get_settings
    from app.nlp.classifier import score_matrix

    default = get_settings().dimension_threshold
    scores = score_matrix([r["text"] for r in dev_rows])
    gold = [set(r["labels"]) for r in dev_rows]

    fitted: dict[str, float] = {}
    for col, key in enumerate(keys):
        positives = [i for i, truth in enumerate(gold) if key in truth]
        if len(positives) < 4:
            fitted[key] = default
            continue

        best_threshold, best_f1 = default, -1.0
        for threshold in np.arange(0.30, 0.71, 0.01):
            tp = sum(1 for i in range(len(gold)) if scores[i, col] >= threshold and key in gold[i])
            fp = sum(1 for i in range(len(gold)) if scores[i, col] >= threshold and key not in gold[i])
            fn = len(positives) - tp
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
            if f1 > best_f1:
                best_threshold, best_f1 = round(float(threshold), 2), f1
        fitted[key] = best_threshold

    return fitted


def evaluate_dimensions_calibrated(scores, gold, keys, thresholds: dict[str, float]) -> dict:
    """Same metrics as `evaluate_dimensions`, with a per-dimension cut.

    Implemented by re-centring each column on its own threshold, so a single
    comparison against 0.5 reproduces the per-dimension decision and both code
    paths share one metric implementation.
    """
    cuts = np.array([thresholds[k] for k in keys], dtype=np.float32)
    result = evaluate_dimensions(0.5, scores - cuts + 0.5, gold, keys)
    result["threshold"] = "per-dimension"
    result["thresholds"] = thresholds
    return result


def run_dimension_eval(sweep: bool, write_calibration: bool = False) -> dict:
    from app.config import get_settings
    from app.nlp.classifier import score_matrix
    from app.nlp.taxonomy import DIMENSION_KEYS

    path = DATA_DIR / "dimension_labels.jsonl"
    dev, test = load_jsonl(path, "dev"), load_jsonl(path, "test")
    configured = get_settings().dimension_threshold

    _rule("1. DIMENSION CLASSIFICATION", f"{len(dev)} dev / {len(test)} test sentences")

    chosen = configured
    if sweep:
        dev_scores = score_matrix([r["text"] for r in dev])
        dev_gold = [set(r["labels"]) for r in dev]

        print(f"\n  Calibrating on the DEV split only.\n\n  {'thresh':>7}{'P':>8}{'R':>8}{'F1':>8}{'neg rej':>10}")
        print("  " + "-" * 41)
        best = None
        for threshold in np.arange(0.20, 0.66, 0.01):
            result = evaluate_dimensions(threshold, dev_scores, dev_gold, DIMENSION_KEYS)
            micro = result["micro"]
            if best is None or micro["f1"] > best["micro"]["f1"]:
                best = result
            if round(float(threshold) * 100) % 3 == 0:
                print(
                    f"  {threshold:7.2f}{micro['precision']:8.3f}{micro['recall']:8.3f}"
                    f"{micro['f1']:8.3f}{result['negative_rejection']['rate']:10.2f}"
                )
        chosen = best["threshold"]
        print(f"\n  Best dev F1 {best['micro']['f1']:.3f} at threshold {chosen:.2f}")
        if abs(chosen - configured) > 0.005:
            print(f"  ** config.py has {configured:.2f}; update it to {chosen:.2f} **")
        else:
            print(f"  config.py threshold ({configured:.2f}) matches the dev optimum.")

    # Fit per-dimension thresholds on dev, then freeze them for the test report.
    from app.nlp.classifier import _thresholds, threshold_vector  # noqa: F401

    fitted = fit_per_dimension_thresholds(dev, DIMENSION_KEYS)
    if sweep:
        print("\n  Per-dimension thresholds fitted on DEV:")
        for key, value in sorted(fitted.items()):
            marker = "  (default — too few dev positives)" if abs(value - configured) < 1e-9 else ""
            print(f"    {key:<16}{value:.2f}{marker}")

    if write_calibration:
        target = Path(__file__).resolve().parent.parent / "app" / "nlp" / "calibration.json"
        target.write_text(
            json.dumps(
                {
                    "_comment": "Fitted on the dev split by `python -m eval.run_eval --sweep "
                    "--write-calibration`. Do not hand-edit; re-fit instead.",
                    "global_default": configured,
                    "thresholds": fitted,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"\n  Wrote calibration to {target}")

    test_scores = score_matrix([r["text"] for r in test])
    test_gold = [set(r["labels"]) for r in test]

    global_result = evaluate_dimensions(configured, test_scores, test_gold, DIMENSION_KEYS)
    result = evaluate_dimensions_calibrated(test_scores, test_gold, DIMENSION_KEYS, fitted)

    print(
        f"\n  Single global threshold ({configured:.2f}) on test: "
        f"F1 {global_result['micro']['f1']:.3f}  "
        f"(P {global_result['micro']['precision']:.3f} / R {global_result['micro']['recall']:.3f})"
    )

    micro = result["micro"]
    negatives = result["negative_rejection"]

    print("\n  HELD-OUT TEST RESULTS (per-dimension thresholds fitted on dev only)")
    print(f"    micro precision {micro['precision']:.3f}   recall {micro['recall']:.3f}   F1 {micro['f1']:.3f}")
    print(f"    tp={micro['tp']}  fp={micro['fp']}  fn={micro['fn']}")
    print(
        f"    negatives correctly rejected: {negatives['correct']}/{negatives['total']} "
        f"({negatives['rate']:.0%})"
    )

    print(f"\n    {'dimension':<16}{'P':>7}{'R':>7}{'F1':>7}{'n':>5}")
    print("    " + "-" * 42)
    for key, stats in result["per_dimension"].items():
        print(f"    {key:<16}{stats['precision']:7.3f}{stats['recall']:7.3f}{stats['f1']:7.3f}{stats['support']:5d}")

    return result


# ==========================================================================
# 2. target extraction
# ==========================================================================

def run_target_eval() -> dict:
    from app.nlp.extraction import extract_targets_rule_based

    path = DATA_DIR / "target_labels.jsonl"
    test = load_jsonl(path, "test")
    fields = ("target_type", "value", "unit", "target_year", "base_year")

    positives = [r for r in test if r["expected"]]
    negatives = [r for r in test if not r["expected"]]

    _rule("2. TARGET EXTRACTION", f"{len(positives)} positive / {len(negatives)} negative (test split)")

    correct: dict[str, int] = defaultdict(int)
    attempted: dict[str, int] = defaultdict(int)
    found = 0

    for row in positives:
        expected = row["expected"]
        candidates = [{"text": row["text"], "page": 1, "section": "", "chunk_index": 0}]
        targets = extract_targets_rule_based(candidates)
        match = next((t for t in targets if t.target_type == expected["target_type"]), None)

        if match is None:
            print(f"    MISS  {row['text'][:62]}...")
            for field in fields:
                if field in expected:
                    attempted[field] += 1
            continue

        found += 1
        wrong = []
        for field in fields:
            if field not in expected:
                continue
            attempted[field] += 1
            actual = getattr(match, field)
            ok = (
                abs(actual - expected[field]) < max(1e-6, abs(expected[field]) * 1e-6)
                if isinstance(expected[field], float) and isinstance(actual, int | float)
                else actual == expected[field]
            )
            if ok:
                correct[field] += 1
            else:
                wrong.append(f"{field}: got {actual!r}, want {expected[field]!r}")

        if wrong:
            print(f"    PART  {row['text'][:62]}...")
            for issue in wrong:
                print(f"          {issue}")

    # False positives matter as much as recall: a pipeline that reports the
    # census population as an emissions target is worse than one that reports
    # nothing, because it looks authoritative.
    false_positives = []
    for row in negatives:
        candidates = [{"text": row["text"], "page": 1, "section": "", "chunk_index": 0}]
        if extract_targets_rule_based(candidates):
            false_positives.append(row["text"])

    detection = found / len(positives) if positives else 0.0
    print(f"\n    Detected (correct type): {found}/{len(positives)} = {detection:.1%}")
    print(f"    False positives on non-commitment prose: {len(false_positives)}/{len(negatives)}")
    for text in false_positives:
        print(f"      FP: {text[:66]}...")

    print(f"\n    {'field':<14}{'accuracy':>10}")
    print("    " + "-" * 24)
    field_scores = {}
    for field in fields:
        if attempted[field]:
            accuracy = correct[field] / attempted[field]
            field_scores[field] = accuracy
            print(f"    {field:<14}{accuracy:>9.1%}  ({correct[field]}/{attempted[field]})")

    return {
        "detection_rate": detection,
        "false_positive_rate": len(false_positives) / len(negatives) if negatives else 0.0,
        "field_accuracy": field_scores,
    }


# ==========================================================================
# 3. retrieval
# ==========================================================================

def _metrics(ranked_ids: list[str], relevant: set[str], ks=(1, 3, 5, 10)) -> dict:
    out = {f"recall@{k}": len(set(ranked_ids[:k]) & relevant) / len(relevant) for k in ks}
    rank = next((i + 1 for i, doc_id in enumerate(ranked_ids) if doc_id in relevant), None)
    out["rr"] = 1.0 / rank if rank else 0.0
    return out


async def _rank(retriever, query: str, mode: str, top_k: int = 10) -> list[str]:
    """Rank the corpus by one retrieval strategy. `mode` selects the ablation arm."""
    import numpy as np

    from app.nlp import embeddings
    from app.nlp.retrieval import tokenize

    if mode == "dense":
        query_vec = (await embeddings.embed([query]))[0]
        order = np.argsort(-(retriever.vectors @ query_vec))[:top_k]
        return [retriever.records[int(i)]["doc_id"] for i in order]

    if mode == "bm25":
        scores = np.asarray(retriever.bm25.get_scores(tokenize(query)), dtype=np.float32)
        order = np.argsort(-scores)[:top_k]
        return [retriever.records[int(i)]["doc_id"] for i in order]

    hits = await retriever.search(query, top_k=top_k, use_reranker=(mode == "hybrid_rerank"))
    return [h.doc_id for h in hits]


def run_retrieval_eval(ablate: bool) -> dict:
    import asyncio

    from app.nlp import embeddings
    from app.nlp.retrieval import HybridRetriever

    data = json.loads((DATA_DIR / "retrieval.json").read_text(encoding="utf-8"))
    corpus, queries = data["corpus"], data["queries"]

    _rule("3. RETRIEVAL", f"{len(corpus)} passages, {len(queries)} queries")

    records = [
        {
            "doc_id": passage["id"],
            "chunk_index": i,
            "text": passage["text"],
            "page_start": 1,
            "page_end": 1,
            "section": "",
        }
        for i, passage in enumerate(corpus)
    ]
    vectors = embeddings.embed_sync([r["text"] for r in records])
    retriever = HybridRetriever(records, vectors)

    modes = ["dense", "bm25", "hybrid", "hybrid_rerank"] if ablate else ["hybrid_rerank"]

    async def evaluate(mode: str) -> dict:
        by_kind: dict[str, list[dict]] = defaultdict(list)
        overall: list[dict] = []
        for item in queries:
            ranked = await _rank(retriever, item["query"], mode)
            scores = _metrics(ranked, set(item["relevant"]))
            overall.append(scores)
            by_kind[item["kind"]].append(scores)

        mean = lambda rows, key: float(np.mean([r[key] for r in rows])) if rows else 0.0  # noqa: E731
        return {
            "mode": mode,
            "recall@1": mean(overall, "recall@1"),
            "recall@3": mean(overall, "recall@3"),
            "recall@5": mean(overall, "recall@5"),
            "mrr": mean(overall, "rr"),
            "by_kind": {
                kind: {"recall@3": mean(rows, "recall@3"), "mrr": mean(rows, "rr"), "n": len(rows)}
                for kind, rows in by_kind.items()
            },
        }

    results = [asyncio.run(evaluate(mode)) for mode in modes]

    print(f"\n    {'strategy':<16}{'R@1':>7}{'R@3':>7}{'R@5':>7}{'MRR':>7}")
    print("    " + "-" * 44)
    for row in results:
        print(
            f"    {row['mode']:<16}{row['recall@1']:7.3f}{row['recall@3']:7.3f}"
            f"{row['recall@5']:7.3f}{row['mrr']:7.3f}"
        )

    if ablate:
        print("\n    Where each retriever earns its keep (recall@3 / MRR):\n")
        kinds = sorted({k for row in results for k in row["by_kind"]})
        print(f"    {'strategy':<16}" + "".join(f"{kind:>22}" for kind in kinds))
        print("    " + "-" * (16 + 22 * len(kinds)))
        for row in results:
            cells = "".join(
                f"{row['by_kind'][kind]['recall@3']:>13.3f} /{row['by_kind'][kind]['mrr']:>7.3f}"
                if kind in row["by_kind"]
                else f"{'-':>22}"
                for kind in kinds
            )
            print(f"    {row['mode']:<16}{cells}")
        print(
            "\n    Read this as the justification for the hybrid design: dense should\n"
            "    lead on paraphrase queries, BM25 on rare-literal ones, and the fused\n"
            "    retriever should match or beat the better arm on both."
        )

    return results[-1]


# ==========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the analysis pipeline.")
    parser.add_argument("--sweep", action="store_true", help="Calibrate thresholds on the dev split.")
    parser.add_argument("--write-calibration", action="store_true",
                        help="Write the fitted per-dimension thresholds to app/nlp/calibration.json.")
    parser.add_argument("--ablate", action="store_true", help="Compare retrieval strategies.")
    parser.add_argument("--json", type=Path, help="Write results to a JSON file.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if a quality floor is breached.")
    args = parser.parse_args()

    dimensions = run_dimension_eval(args.sweep, args.write_calibration)
    targets = run_target_eval()
    retrieval = run_retrieval_eval(args.ablate)

    _rule("SUMMARY (held-out test splits)")
    rows = [
        ("dimension micro-F1", dimensions["micro"]["f1"], DIM_F1_FLOOR),
        ("negative rejection", dimensions["negative_rejection"]["rate"], None),
        ("target detection", targets["detection_rate"], TARGET_DETECTION_FLOOR),
        ("target false-positive rate", targets["false_positive_rate"], None),
        ("retrieval recall@3", retrieval["recall@3"], RETRIEVAL_RECALL_FLOOR),
        ("retrieval MRR", retrieval["mrr"], None),
    ]
    breaches = []
    for label, value, floor in rows:
        note = ""
        if floor is not None:
            ok = value >= floor
            note = f"  (floor {floor:.2f}{'' if ok else ' — BREACHED'})"
            if not ok:
                breaches.append(f"{label} {value:.3f} < {floor:.2f}")
        print(f"    {label:<28}{value:6.3f}{note}")

    print(
        "\n    Labels are single-annotator and share an author with the taxonomy;\n"
        "    treat these as regression guards and internal consistency, not as an\n"
        "    unbiased benchmark. See the module docstring."
    )

    if args.json:
        args.json.write_text(
            json.dumps({"dimensions": dimensions, "targets": targets, "retrieval": retrieval}, indent=2),
            encoding="utf-8",
        )
        print(f"\n    Wrote {args.json}")

    if args.check and breaches:
        raise SystemExit("\nQUALITY REGRESSION: " + "; ".join(breaches))


if __name__ == "__main__":
    main()
