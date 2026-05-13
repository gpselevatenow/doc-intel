"""Ground-truth benchmark harness for the extraction pipeline.

Loads tests/fixtures/ground_truth.json (hand-labeled), runs the full
extraction pipeline on each listed document, compares field-by-field,
and writes two artifacts:

  tests/benchmark_results.json       — machine-readable
  docs/benchmarks/ground_truth_YYYY-MM-DD.md  — human-readable report

Usage:
  python tests/benchmark_ground_truth.py [options]

Options:
  --doc FILENAME        Benchmark a single document by filename (for debugging)
  --verbose             Print per-field detail to stdout during the run
  --force-template      Use expected_form_id from ground truth instead of classifier
                        (counterfactual: isolates classifier vs template accuracy)
                        Writes to benchmark_results_forced_template.json
  --label LABEL         Override output filename suffix: ground_truth_{LABEL}_{date}.md
                        and benchmark_results_{LABEL}.json
  --help                Show this message and exit
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────
# Resolve paths relative to this file so the script works from any cwd.
_TESTS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _TESTS_DIR.parent
_REPO_DIR = _BACKEND_DIR.parent

sys.path.insert(0, str(_BACKEND_DIR))

import pdfplumber
from core.document_model import Document
from core.form_classifier import classify_form
from core.orchestrator_integration import run_orchestrator

_GROUND_TRUTH_PATH = _TESTS_DIR / "fixtures" / "ground_truth.json"
_RESULTS_PATH = _TESTS_DIR / "benchmark_results.json"
_RESULTS_FORCED_PATH = _TESTS_DIR / "benchmark_results_forced_template.json"
_BENCHMARKS_DIR = _REPO_DIR / "docs" / "benchmarks"

_LIST_FIELD_IDS = {"vehicles", "parties", "witnesses"}

# Characters stripped from leading/trailing edges in trim comparison
_PUNCT_STRIP_RE = re.compile(r'^[\s,—–\-:;.!?]+|[\s,—–\-:;.!?]+$')

# ── Normalization ─────────────────────────────────────────────────────────────

def _norm_string(v: str) -> str:
    return re.sub(r"\s+", " ", v.lower().strip())


def _norm_string_trimmed(v: str) -> str:
    """Normalize then strip leading/trailing punctuation noise."""
    return _PUNCT_STRIP_RE.sub("", _norm_string(v))


def _parse_datetime(v: str):
    """Return a datetime object or None if unparseable."""
    try:
        from dateutil import parser as du_parser
        return du_parser.parse(v, fuzzy=True)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(v)
    except Exception:
        return None


def _dates_equal(a: str, b: str) -> bool:
    """True if both strings parse to datetimes whose date parts are equal,
    OR whose timestamps differ by less than 1 hour."""
    dt_a = _parse_datetime(a)
    dt_b = _parse_datetime(b)
    if dt_a is None or dt_b is None:
        return False
    if dt_a.date() == dt_b.date():
        return True
    return abs((dt_a - dt_b).total_seconds()) < 3600


def _norm_list(v: str) -> frozenset[str]:
    return frozenset(_norm_string(item) for item in v.split(",") if item.strip())


def values_match(field_id: str, gt: str | None, extracted: str | None) -> str | bool:
    """Return 'exact', 'trim', 'containment', or False.

    Classification order (first match wins):
      exact       — normalized strings are equal (or dates match)
      trim        — equal only after leading/trailing punctuation strip
      containment — one trimmed value is a substring of the other (min 4 chars each)
      False       — no match
    List fields use frozenset comparison only; containment is not applied.
    """
    if gt is None and extracted is None:
        return "exact"
    if gt is None or extracted is None:
        return False
    if field_id == "date_time":
        if _dates_equal(gt, extracted):
            return "exact"
    if field_id in _LIST_FIELD_IDS:
        return "exact" if _norm_list(gt) == _norm_list(extracted) else False
    if _norm_string(gt) == _norm_string(extracted):
        return "exact"
    gt_t = _norm_string_trimmed(gt)
    ex_t = _norm_string_trimmed(extracted)
    if gt_t == ex_t:
        return "trim"
    if len(gt_t) >= 4 and len(ex_t) >= 4:
        if gt_t in ex_t or ex_t in gt_t:
            return "containment"
    return False


# ── Status classification ─────────────────────────────────────────────────────

def classify_result(
    field_id: str,
    gt: str | None,
    extracted: str | None,
    confidence: float,
) -> dict[str, Any]:
    if gt is None and (extracted is None or extracted == ""):
        status = "TRUE_NEGATIVE"
    elif gt is not None and (extracted is None or extracted == ""):
        status = "MISSED"
    elif gt is None and extracted not in (None, ""):
        status = "SPURIOUS"
    else:
        match = values_match(field_id, gt, extracted)
        if match == "exact":
            status = "CORRECT"
        elif match == "trim":
            status = "CORRECT_AFTER_TRIM"
        elif match == "containment":
            status = "CORRECT_BY_CONTAINMENT"
        else:
            status = "INCORRECT"
    return {
        "status":     status,
        "confidence": confidence,
    }


# ── Pipeline runner ───────────────────────────────────────────────────────────

def _resolve_doc_path(filename: str, declared_path: str | None) -> Path:
    """Resolve document path: try declared_path, then sample documents/, then tests/fixtures/."""
    if declared_path:
        p = Path(declared_path)
        if not p.is_absolute():
            p = _BACKEND_DIR / p
        if p.exists():
            return p

    candidates = [
        _REPO_DIR / "sample documents" / filename,
        _TESTS_DIR / "fixtures" / filename,
        Path(filename),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"Cannot locate document '{filename}'. "
        f"Declare an explicit 'path' in ground_truth.json or place it in 'sample documents/'."
    )


def run_extraction(doc_path: Path, forced_form_id: str | None = None) -> tuple[dict, str | None]:
    """Run the full pipeline on one document.

    Args:
        doc_path:        Path to the PDF.
        forced_form_id:  When set, bypasses the classifier and uses this form_id directly.

    Returns:
        (record, all_candidates, form_id).
    """
    with pdfplumber.open(str(doc_path)) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages[:3])

    if forced_form_id:
        form_id = forced_form_id
    else:
        form_id, _ = classify_form(text)

    canonical = Document(
        document_id=doc_path.name,
        source_path=str(doc_path),
        n_pages=1,
        markdown=text,
    )
    result = run_orchestrator(canonical, doc_path.name, "police_report", form_id=form_id)
    return result["record"], result["all_candidates"], form_id


def _best_confidence(field_id: str, all_candidates: list) -> float:
    non_rejected = [c for c in all_candidates if c.field_id == field_id and not c.rejected]
    if not non_rejected:
        return 0.0
    return max(c.confidence for c in non_rejected)


# ── Metrics helpers ───────────────────────────────────────────────────────────

def _safe_div(a: int, b: int) -> float:
    return round(a / b, 4) if b else 0.0


def _mean(vals: list[float]) -> float | None:
    return round(sum(vals) / len(vals), 4) if vals else None


def compute_metrics(detail: list[dict]) -> dict:
    counts = {
        "CORRECT": 0, "CORRECT_AFTER_TRIM": 0, "CORRECT_BY_CONTAINMENT": 0,
        "INCORRECT": 0, "MISSED": 0, "SPURIOUS": 0, "TRUE_NEGATIVE": 0,
    }
    for row in detail:
        counts[row["status"]] += 1

    # All three CORRECT variants count as TP for precision/recall
    tp  = counts["CORRECT"] + counts["CORRECT_AFTER_TRIM"] + counts["CORRECT_BY_CONTAINMENT"]
    fp  = counts["SPURIOUS"] + counts["INCORRECT"]
    fn  = counts["MISSED"]   + counts["INCORRECT"]

    precision = _safe_div(tp, tp + fp)
    recall    = _safe_div(tp, tp + fn)
    f1        = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
    total_ex  = tp + fp + fn
    accuracy  = _safe_div(tp, total_ex) if total_ex else 1.0

    return {
        **counts,
        "total_correct":    tp,
        "trim_corrections": counts["CORRECT_AFTER_TRIM"],
        "precision": precision,
        "recall":    recall,
        "f1":        round(f1, 4),
        "accuracy":  accuracy,
    }


def per_field_metrics(detail: list[dict]) -> dict:
    fields: dict[str, dict] = {}
    for row in detail:
        fid = row["field"]
        if fid not in fields:
            fields[fid] = {
                "CORRECT": 0, "CORRECT_AFTER_TRIM": 0, "CORRECT_BY_CONTAINMENT": 0,
                "INCORRECT": 0, "MISSED": 0, "SPURIOUS": 0, "TRUE_NEGATIVE": 0,
            }
        fields[fid][row["status"]] += 1

    result = {}
    for fid, c in fields.items():
        tp = c["CORRECT"] + c["CORRECT_AFTER_TRIM"] + c["CORRECT_BY_CONTAINMENT"]
        fp = c["SPURIOUS"] + c["INCORRECT"]
        fn = c["MISSED"]   + c["INCORRECT"]
        precision = _safe_div(tp, tp + fp)
        recall    = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
        result[fid] = {
            "correct":                c["CORRECT"],
            "correct_after_trim":     c["CORRECT_AFTER_TRIM"],
            "correct_by_containment": c["CORRECT_BY_CONTAINMENT"],
            "incorrect":              c["INCORRECT"],
            "missed":                 c["MISSED"],
            "spurious":               c["SPURIOUS"],
            "true_negative":          c["TRUE_NEGATIVE"],
            "precision":              precision,
            "recall":                 recall,
            "f1":                     round(f1, 4),
        }
    return result


def per_doc_metrics(detail: list[dict], doc_form_results: dict) -> dict:
    docs: dict[str, dict] = {}
    for row in detail:
        dn = row["doc"]
        if dn not in docs:
            docs[dn] = {
                "fields_correct": 0, "fields_total": 0,
                "conf_correct": [], "conf_incorrect": [],
                "form_id_correct": doc_form_results.get(dn, None),
            }
        if row["status"] not in ("TRUE_NEGATIVE",):
            docs[dn]["fields_total"] += 1
        if row["status"] in ("CORRECT", "CORRECT_AFTER_TRIM", "CORRECT_BY_CONTAINMENT"):
            docs[dn]["fields_correct"] += 1
            docs[dn]["conf_correct"].append(row["confidence"])
        elif row["status"] in ("INCORRECT", "MISSED", "SPURIOUS"):
            docs[dn]["conf_incorrect"].append(row["confidence"])

    result = {}
    for dn, d in docs.items():
        result[dn] = {
            "form_id_correct":              d["form_id_correct"],
            "fields_correct":               d["fields_correct"],
            "fields_total":                 d["fields_total"],
            "confidence_when_correct_mean":   _mean(d["conf_correct"]),
            "confidence_when_incorrect_mean": _mean(d["conf_incorrect"]),
        }
    return result


# ── Markdown report ───────────────────────────────────────────────────────────

def _md_table(headers: list[str], rows: list[list]) -> str:
    col_w = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
             for i, h in enumerate(headers)]
    sep = "|" + "|".join("-" * (w + 2) for w in col_w) + "|"
    hdr = "|" + "|".join(f" {str(h):<{w}} " for h, w in zip(headers, col_w)) + "|"
    body = "\n".join(
        "|" + "|".join(f" {str(r[i] if i < len(r) else ''):<{w}} " for i, w in enumerate(col_w)) + "|"
        for r in rows
    )
    return "\n".join([hdr, sep, body])


def build_markdown(summary: dict, pf: dict, pd_: dict, detail: list[dict], run_date: str,
                   forced: bool = False) -> str:
    mode = " [FORCED TEMPLATE]" if forced else ""
    lines = [f"# Ground Truth Benchmark — {run_date}{mode}", ""]

    # Headline numbers
    lines += [
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Precision | {summary['precision']:.4f} |",
        f"| Recall | {summary['recall']:.4f} |",
        f"| F1 | {summary['f1']:.4f} |",
        f"| Accuracy | {summary['accuracy']:.4f} |",
        f"| Total Correct | {summary['total_correct']} |",
        f"| — Exact | {summary['CORRECT']} |",
        f"| — After Trim | {summary['CORRECT_AFTER_TRIM']} |",
        f"| — By Containment | {summary['CORRECT_BY_CONTAINMENT']} |",
        f"| Incorrect | {summary['INCORRECT']} |",
        f"| Missed | {summary['MISSED']} |",
        f"| Spurious | {summary['SPURIOUS']} |",
        f"| True Negative | {summary['TRUE_NEGATIVE']} |",
        "",
    ]

    # Per-field table
    lines += ["## Per-Field Results", ""]
    pf_rows = sorted(pf.items())
    pf_table_rows = [
        [fid, d["correct"], d["correct_after_trim"], d["correct_by_containment"],
         d["incorrect"], d["missed"], d["spurious"],
         f"{d['precision']:.3f}", f"{d['recall']:.3f}", f"{d['f1']:.3f}"]
        for fid, d in pf_rows
    ]
    lines.append(_md_table(
        ["Field", "Exact", "Trim", "Contain", "Incorrect", "Missed", "Spurious", "Precision", "Recall", "F1"],
        pf_table_rows,
    ))
    lines.append("")

    # Per-doc table
    lines += ["## Per-Document Results", ""]
    pd_rows = [
        [dn,
         "yes" if d["form_id_correct"] else ("no" if d["form_id_correct"] is False else "—"),
         d["fields_correct"],
         d["fields_total"],
         f"{d['confidence_when_correct_mean']:.4f}" if d["confidence_when_correct_mean"] is not None else "—",
         f"{d['confidence_when_incorrect_mean']:.4f}" if d["confidence_when_incorrect_mean"] is not None else "—",
        ]
        for dn, d in sorted(pd_.items())
    ]
    lines.append(_md_table(
        ["Document", "Form ID", "Correct", "Total", "Conf (correct)", "Conf (incorrect)"],
        pd_rows,
    ))
    lines.append("")

    # Confidence calibration
    correct_confs = [r["confidence"] for r in detail
                     if r["status"] in ("CORRECT", "CORRECT_AFTER_TRIM", "CORRECT_BY_CONTAINMENT")]
    incorrect_confs = [r["confidence"] for r in detail if r["status"] in ("INCORRECT", "MISSED", "SPURIOUS")]
    lines += ["## Confidence Calibration", ""]
    lines.append(
        f"Mean confidence on **correct** extractions:   "
        f"**{_mean(correct_confs):.4f}** (n={len(correct_confs)})"
    )
    lines.append(
        f"Mean confidence on **incorrect** extractions: "
        f"**{_mean(incorrect_confs):.4f}** (n={len(incorrect_confs)})"
        if incorrect_confs else
        "Mean confidence on **incorrect** extractions: — (none)"
    )
    lines.append("")

    # Top 10 failures — INCORRECT only (containment cases are not failures)
    failures = [r for r in detail if r["status"] in ("INCORRECT", "MISSED", "SPURIOUS")]
    failures.sort(key=lambda r: r["confidence"], reverse=True)
    lines += ["## Top 10 Failures (by confidence)", ""]
    if not failures:
        lines.append("None.")
    else:
        fail_rows = [
            [r["doc"], r["field"],
             str(r["ground_truth"])[:40] if r["ground_truth"] else "—",
             str(r["extracted"])[:40] if r["extracted"] else "—",
             f"{r['confidence']:.4f}", r["status"]]
            for r in failures[:10]
        ]
        lines.append(_md_table(
            ["Document", "Field", "Ground Truth", "Extracted", "Confidence", "Status"],
            fail_rows,
        ))
    lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main(args: argparse.Namespace) -> int:
    # Load ground truth
    if not _GROUND_TRUTH_PATH.exists():
        print(f"ERROR: Ground truth file not found: {_GROUND_TRUTH_PATH}", file=sys.stderr)
        return 1

    with open(_GROUND_TRUTH_PATH, encoding="utf-8") as f:
        gt_data = json.load(f)

    documents = gt_data.get("documents", [])
    if not documents:
        print("Ground truth file contains no documents. Add entries to 'documents' array.", file=sys.stderr)
        return 1

    # Filter to single doc if --doc specified
    if args.doc:
        documents = [d for d in documents if Path(d["filename"]).name == args.doc]
        if not documents:
            print(f"No ground truth entry found for filename '{args.doc}'.", file=sys.stderr)
            return 1

    run_date = date.today().isoformat()
    detail:          list[dict] = []
    doc_form_results: dict[str, bool | None] = {}

    for doc_entry in documents:
        filename = doc_entry["filename"]
        declared_path = doc_entry.get("path")
        expected_form_id = doc_entry.get("expected_form_id")
        gt_fields: dict[str, str | None] = doc_entry.get("fields", {})

        forced_form_id = expected_form_id if args.force_template else None

        print(f"[{filename}] ", end="", flush=True)

        try:
            doc_path = _resolve_doc_path(filename, declared_path)
            record, all_candidates, actual_form_id = run_extraction(doc_path, forced_form_id)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            continue

        form_correct = (actual_form_id == expected_form_id) if expected_form_id else None
        doc_form_results[filename] = form_correct

        if args.force_template:
            print(f"form_id={actual_form_id} [forced]")
        else:
            print(f"form_id={actual_form_id}" + (f" (expected {expected_form_id})" if expected_form_id else ""))

        for field_id, gt_value in gt_fields.items():
            extracted_value = record.get(field_id)
            confidence = _best_confidence(field_id, all_candidates)

            classified = classify_result(field_id, gt_value, extracted_value, confidence)
            row = {
                "doc":          filename,
                "field":        field_id,
                "ground_truth": gt_value,
                "extracted":    extracted_value,
                "status":       classified["status"],
                "confidence":   classified["confidence"],
            }
            detail.append(row)

            if args.verbose:
                marker = {
                    "CORRECT": "OK", "CORRECT_AFTER_TRIM": "TRIM",
                    "CORRECT_BY_CONTAINMENT": "CONT",
                    "INCORRECT": "WRONG", "MISSED": "MISS",
                    "SPURIOUS": "SPUR", "TRUE_NEGATIVE": "TN",
                }.get(row["status"], "?")
                print(f"  [{marker}] {field_id}: gt={repr(str(gt_value)[:60])} "
                      f"extracted={repr(str(extracted_value)[:60])} conf={confidence:.4f}")

    if not detail:
        print("No field comparisons produced. Check document paths and ground truth entries.")
        return 1

    # Compute metrics
    summary = compute_metrics(detail)
    pf      = per_field_metrics(detail)
    pd_     = per_doc_metrics(detail, doc_form_results)

    # Write JSON result
    output = {
        "run_date":               run_date,
        "forced_template":        args.force_template,
        "docs_evaluated":         len(set(r["doc"] for r in detail)),
        "fields_per_doc":         len(set(r["field"] for r in detail)),
        "total_field_comparisons":len(detail),
        "summary":                summary,
        "per_field":              pf,
        "per_doc":                pd_,
        "detail":                 detail,
    }
    label = args.label or ("forced" if args.force_template else "")
    if label:
        results_path = _TESTS_DIR / f"benchmark_results_{label}.json"
    else:
        results_path = _RESULTS_PATH
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nWrote {results_path}")

    # Write markdown report
    md = build_markdown(summary, pf, pd_, detail, run_date, forced=args.force_template)
    _BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)
    md_name = f"ground_truth_{label}_{run_date}.md" if label else f"ground_truth_{run_date}.md"
    md_path = _BENCHMARKS_DIR / md_name
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {md_path}")

    # Print summary to stdout
    print(f"\nPrecision={summary['precision']:.4f}  Recall={summary['recall']:.4f}  "
          f"F1={summary['f1']:.4f}  Accuracy={summary['accuracy']:.4f}")
    print(f"TotalCorrect={summary['total_correct']}  "
          f"(Exact={summary['CORRECT']}  Trim={summary['CORRECT_AFTER_TRIM']}  "
          f"Contain={summary['CORRECT_BY_CONTAINMENT']})  "
          f"Incorrect={summary['INCORRECT']}  Missed={summary['MISSED']}  "
          f"Spurious={summary['SPURIOUS']}  TrueNeg={summary['TRUE_NEGATIVE']}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="benchmark_ground_truth",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--doc",
        metavar="FILENAME",
        default=None,
        help="Benchmark a single document by filename (e.g. sample_full_report.pdf).",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-field detail to stdout during the run.",
    )
    p.add_argument(
        "--force-template",
        action="store_true",
        default=False,
        help="Bypass classifier; use expected_form_id from ground truth as the template. "
             "Writes to benchmark_results_forced_template.json.",
    )
    p.add_argument(
        "--label",
        metavar="LABEL",
        default=None,
        help="Override output filename: ground_truth_{LABEL}_{date}.md and "
             "benchmark_results_{LABEL}.json (e.g. --label path1).",
    )
    return p


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(main(args))
