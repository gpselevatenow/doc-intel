# IA Report Baseline Benchmark — 2026-05-15

## Context

First IA adjuster report benchmark. 2 hand-labeled PDFs, 13 fields each = 26 field-level
comparisons. Template: `ia_report.json` (13 fields, all scalar). No form classifier —
`--no-classifier` flag used; `doc_type=ia_report` passed directly.

## Headline Metrics

| Metric | Value |
|--------|-------|
| F1 | **0.8387** |
| Precision | 0.8125 |
| Recall | 0.8667 |
| Accuracy | 0.7222 |
| Total Correct | 13 |
| — Exact | 10 |
| — After Trim | 0 |
| — By Containment | 3 |
| Incorrect | 2 |
| Missed | 0 |
| Spurious | 1 |
| True Negative | 10 |

## Per-Field F1 — All 13 Fields

| Field | F1 | Precision | Recall | Correct | Incorrect | Spurious | TN | Notes |
|-------|----|-----------|--------|---------|-----------|----------|----|-------|
| cause_of_loss | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | High: containment (over-captures prose suffix) |
| coverage_a | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | |
| coverage_b | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 | 1 | High=TN (no Cov B), Low=exact |
| coverage_c | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | |
| coverage_d | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 | 1 | High=TN (no Cov D), Low=exact |
| inspection_date | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | |
| settlement | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | High: containment ($85,500 in GT prose) |
| officials | 0.667 | 0.500 | 1.000 | 1 | 0 | 1 | 0 | High=containment; Low=spurious (see notes) |
| subrogation | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 | 0 | Both INCORRECT — keyword vs prose GT mismatch |
| coverages | n/a | — | — | 0 | 0 | 0 | 2 | All-TN: field not present in either doc |
| inspection_firm | n/a | — | — | 0 | 0 | 0 | 2 | All-TN: no firm label in either doc |
| payment_summary | n/a | — | — | 0 | 0 | 0 | 2 | All-TN: no payment summary in either doc |
| recommendations | n/a | — | — | 0 | 0 | 0 | 2 | All-TN: no recommendations section in either doc |

**Note:** `coverages`, `inspection_firm`, `payment_summary`, `recommendations` show F1=0.000 in
raw harness output (formula: 0/0 = 0) but are all correct true negatives — no extractable value
present in either document. They do not degrade overall F1.

**Fields at F1 = 1.000 (7):** cause_of_loss, coverage_a, coverage_b, coverage_c, coverage_d,
inspection_date, settlement.

**Failures (2):** officials (0.667), subrogation (0.000).

## Per-Document Summary

| Document | Correct / Total | Conf (correct) | Conf (incorrect) |
|----------|-----------------|----------------|------------------|
| IA_Report_High_Complexity.pdf | 6 / 7 | 0.6463 | 0.6923 |
| IA_Report_Low_Complexity.pdf | 7 / 9 | 0.6461 | 0.6673 |

**Form ID column:** Not applicable — `--no-classifier` was used; `form_id=None` throughout.
The harness displays "no" because `None != "ia_report"`. This is expected; the IA doc type
has no classifier fingerprint and routes via `--doc-type ia_report` flag directly.

**Confidence calibration anomaly:** Mean conf on incorrect (0.6756) > correct (0.6462).
Subrogation's keyword pattern fires at 0.6923 — the highest-confidence extractions in the run —
but both are incorrect because the pattern captures only a keyword token while GT expects prose.
High confidence on wrong output is a specific risk for the subrogation pattern.

## Failures — Root Cause Analysis

### 1. subrogation — INCORRECT × 2 (F1 = 0.000)

| Doc | GT | Extracted | Status |
|-----|----|-----------|--------|
| High | `We are investigating the manufacturer of the toaster oven.` | `Potential` | INCORRECT |
| Low | `No. No third party is responsible for this weather event.` | `No` | INCORRECT |

**Root cause:** The subrogation pattern uses a keyword enumeration:
```
(?P<value>yes|no|potential|possible|none|n/?a)
```
This correctly captures the keyword (`Potential`, `No`) but GT was labeled with the full
adjuster prose sentence. Two resolution paths:

- **(a) GT relabel** — change both GT values to the keyword form (`Potential`, `No`). The
  keyword IS semantically correct; the prose is context around the conclusion.
- **(b) Pattern extension** — extend the third pattern to capture a full prose continuation
  after the `Subrogation:` label anchor.

The Low doc `No` failure has an additional cause: `len('no') = 2 < 3`, which disqualifies it
from containment matching even though `'no'` appears at the start of the GT prose. This is
correct harness behavior (prevents trivial substring matches on short tokens).

**Recommendation: Option (a), GT relabel.** The subrogation *conclusion* is what claims
professionals act on; prose context belongs in a separate `subrogation_notes` field if needed.
Consistent with how `cause_of_loss: "Kitchen Fire"` is labeled — the conclusion, not the
surrounding prose.

### 2. officials (Low) — SPURIOUS (contributes to F1 = 0.667)

| Doc | GT | Extracted | Status |
|-----|----|-----------|--------|
| Low | `null` | `12345-LOW` | SPURIOUS |

**Root cause:** GT was explicitly set to `null` because `File Number: 12345-LOW` in the Low doc
is ambiguous — it may be an internal claim file reference, not an external officials report.
The new `File\s+Number` pattern (added in commit f1e9332) correctly finds the value, but GT is
null. This is a GT decision, not an extractor bug.

**Resolution paths:**
- **(a) Accept as spurious** — keep GT null; the ambiguity is real.
- **(b) GT relabel to `12345-LOW`** — if internal claim file numbers are a valid `officials`
  field value, correct the GT.

**Recommendation: leave as-is for now.** The GT note documents the ambiguity. Once the
Low doc labeling is confirmed, update GT in a follow-up.

## Baseline Summary

| Area | Status | Path to F1 = 1.000 |
|------|--------|-------------------|
| Coverage fields (a/b/c/d) | ✓ Perfect | — |
| Core identification (cause, date, settlement) | ✓ Perfect | — |
| officials | Partial (F1=0.667) | Resolve Low GT ambiguity (spurious or relabel) |
| subrogation | Failing (F1=0.000) | GT relabel to keyword form |
| All-TN fields | ✓ Correct | — |

If both fixes are applied (subrogation GT relabel + officials Low GT resolved), projected F1 ≈
**0.95+** with no code changes required.

## Extraction Command

```
python tests/benchmark_ground_truth.py \
  --gt tests/fixtures/ia_ground_truth.json \
  --doc-type ia_report \
  --no-classifier \
  --label ia_baseline
```
