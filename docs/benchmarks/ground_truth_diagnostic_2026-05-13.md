# Ground Truth Diagnostic — 2026-05-13

Five documents. Three benchmark runs. Isolates what's broken and why.

---

## A vs B vs C — Summary

| Run | Classifier | Normalization | Precision | Recall | F1 | Correct | Trim | Incorrect | Missed |
|-----|-----------|---------------|-----------|--------|----|---------|------|-----------|--------|
| A — Original | as-is | strict | 0.2241 | 0.1806 | 0.2000 | 13 | — | 45 | 14 |
| B — Norm fix | as-is | +punct strip | 0.3276 | 0.2639 | 0.2923 | 13 | 6 | 39 | 14 |
| C — Norm fix + forced template | forced correct | +punct strip | 0.3148 | 0.2361 | 0.2698 | 11 | 6 | 37 | 18 |

**Key finding:** Forcing the correct state template (C) performs *worse* than the wrong
classifier output (B). F1 drops from 0.2923 → 0.2698. The state-specific templates for
CA, FL, NY, PA are currently less effective than the generic_mmucc fallback on these documents.
This means the classifier fix is necessary but not sufficient — the state templates need work too.

---

## Section A: Original Benchmark

Reference: `docs/benchmarks/ground_truth_2026-05-13.md` (pre-normalization run)

- F1: **0.2000**
- Established five failure modes: schema mismatch, trailing punctuation, truncation,
  wrong content, field never extracted.

---

## Section B: Normalization Fix Only (classifier as-is)

Run: `python backend/tests/benchmark_ground_truth.py`
Results: `backend/tests/benchmark_results.json`

F1: **0.2923** (+0.0923 vs A)

The normalization fix promoted 6 fields from INCORRECT → CORRECT_AFTER_TRIM:

| Field | What was trimmed |
|-------|-----------------|
| officer (all 5 docs) | trailing comma: `"Officer Daniel R. Fuentes,"` → match |
| accident_type (tx doc) | trailing em-dash: `"3-vehicle rear-end chain —"` → match |

### Per-Field Results (Section B)

| Field | Correct | Trim | Incorrect | Missed | F1 |
|-------|---------|------|-----------|--------|----|
| report_number | 5 | 0 | 0 | 0 | 1.000 |
| officer | 0 | 5 | 0 | 0 | 1.000 |
| date_time | 4 | 0 | 0 | 1 | 0.889 |
| light_condition | 2 | 0 | 3 | 0 | 0.400 |
| agency | 1 | 0 | 2 | 2 | 0.250 |
| weather | 1 | 0 | 4 | 0 | 0.200 |
| accident_type | 0 | 1 | 4 | 0 | 0.200 |
| date_time (missed) | — | — | — | — | — |
| contributing_factors | 0 | 0 | 1 | 1 | 0.000 |
| ems_agency | 0 | 0 | 1 | 4 | 0.000 |
| location | 0 | 0 | 5 | 0 | 0.000 |
| parties | 0 | 0 | 5 | 0 | 0.000 |
| property_damage | 0 | 0 | 5 | 0 | 0.000 |
| road_surface | 0 | 0 | 0 | 5 | 0.000 |
| vehicles | 0 | 0 | 5 | 0 | 0.000 |
| witnesses | 0 | 0 | 4 | 1 | 0.000 |

**Zero-F1 fields break into two groups:**
- **Schema mismatch** (vehicles, parties): extractor returns rich JSON, not flat string.
  See `schema_mismatch_decision.md`. Not addressable until path decision is made.
- **Real extraction failures** (location, road_surface, ems_agency, witnesses,
  contributing_factors, property_damage): field never extracted, truncated, or wrong content.

---

## Section C: Normalization Fix + Forced Correct Template

Run: `python backend/tests/benchmark_ground_truth.py --force-template`
Results: `backend/tests/benchmark_results_forced_template.json`

F1: **0.2698** (-0.0225 vs B)

### Per-Doc: Original Classifier vs Forced Template

| Document | Form ID | Classifier correct/total | Forced correct/total | Delta |
|----------|---------|--------------------------|----------------------|-------|
| sample_full_report.pdf (TX) | tx_cr3 | 5/15 | 5/15 | 0 |
| sample_25_dui_wrongway_la.pdf (CA) | ca_chp555 | 3/15 | 2/15 | −1 |
| sample_27_tropical_moto_tampa.pdf (FL) | fl_hsmv | 2/14 | 1/14 | −1 |
| sample_24_rain_ped_nyc.pdf (NY) | ny_mv104a | 4/14 | 4/14 | 0 |
| sample_33_ice_ped_philadelphia.pdf (PA) | pa_aa600 | 5/14 | 5/14 | 0 |

CA and FL are worse with their state templates than with the wrong generic template.
NY and PA are unchanged. This means ca_chp555 and fl_hsmv templates need pattern work
before fixing the classifier will help those documents.

### Top 10 Failures (Section C, by confidence)

| Document | Field | Ground Truth | Extracted | Conf | Status |
|----------|-------|-------------|-----------|------|--------|
| sample_25 (CA) | weather | `"Clear"` | `"Clear / Dry"` | 0.995 | INCORRECT |
| sample_27 (FL) | accident_type | `"4-vehicle chain collision"` | `"4-vehicle chain collision + motorcycle"` | 0.931 | INCORRECT |
| sample_24 (NY) | accident_type | `"4-vehicle collision + 2 pedestrians struck"` | `"4-vehicle collision + 2 pedestrians"` | 0.931 | INCORRECT |
| sample_33 (PA) | accident_type | `"5-vehicle intersection pileup + 2 pedestrians..."` | `"5-vehicle intersection pileup + 2"` | 0.931 | INCORRECT |
| sample_27 (FL) | weather | `"heavy rain"` | `"Tropical Storm Conditions"` | 0.929 | INCORRECT |
| sample_24 (NY) | weather | `"Thunderstorm"` | `"Heavy Rain / Thunderstorm"` | 0.929 | INCORRECT |
| sample_full (TX) | location | `"I-35W Northbound between Exit 54A (N. Tarrant..."` | `"I-35W Northbound between Exit 54A"` | 0.925 | INCORRECT |
| sample_25 (CA) | light_condition | `"Dark"` | `"Artificial (freeway lighting) / Dark"` | 0.894 | INCORRECT |
| sample_27 (FL) | light_condition | `"Dusk"` | `"Dusk / Storm-darkened"` | 0.894 | INCORRECT |
| sample_33 (PA) | location | `"Broad Street & Washington Avenue (intersectio..."` | `"Street & Washington Avenue TYPE OF 5-vehicle..."` | 0.874 | INCORRECT |

**Pattern in the top failures:** The extractor is capturing *more* than the ground truth
(compound values like `"Clear / Dry"` instead of `"Clear"`, `"Heavy Rain / Thunderstorm"`
instead of `"Thunderstorm"`). This is a ground truth granularity question as much as an
extraction accuracy question. The remaining failures are truncation and OCR bleed-through
(PA location: `"TYPE OF 5-vehicle"` leaked from an adjacent field).

---

## What to Do Next (not prescriptive — for discussion)

1. **Schema mismatch decision** (vehicles/parties/witnesses) — unblocks 3 zero-F1 fields.
   See `schema_mismatch_decision.md`.

2. **Ground truth granularity review** — top failures show GT uses atomic values
   (`"Clear"`, `"Dark"`) while the extractor captures compound values (`"Clear / Dry"`,
   `"Artificial (freeway lighting) / Dark"`). Decide: should GT match extractor verbosity,
   or should extractors be trimmed to atomic values?

3. **State template work (CA, FL)** — forced templates hurt these two docs. Patterns in
   ca_chp555.json and fl_hsmv90010.json need review before classifier fix delivers value.

4. **Zero-extraction fields** — road_surface (0 extractions across all docs), ems_agency,
   witnesses, contributing_factors. These are real missing patterns, not format issues.
