# Ground Truth Benchmark — Path 1 (Trim + Containment) — 2026-05-13

## Comparison Table

| Run | Normalization | Classifier | F1 | Exact | After-Trim | By-Containment | Incorrect | Missed |
|-----|---------------|------------|-----|-------|------------|----------------|-----------|--------|
| A | strict | as-is | 0.2000 | 13 | — | — | 45 | 14 |
| B | trim | as-is | 0.2923 | 13 | 6 | — | 39 | 14 |
| Path 1 | trim + containment | as-is | **0.5846** | 13 | 6 | 19 | 20 | 14 |

Containment check promoted 19 additional fields to CORRECT_BY_CONTAINMENT — the dominant
improvement. Missed count stays at 14 (fields never extracted). Total correct: 38/72.

---

## Summary

| Metric | Value |
|--------|-------|
| Precision | 0.6552 |
| Recall | 0.5278 |
| F1 | **0.5846** |
| Accuracy | 0.4130 |
| Total Correct | 38 |
| — Exact | 13 |
| — After Trim | 6 |
| — By Containment | 19 |
| Incorrect | 20 |
| Missed | 14 |
| Spurious | 0 |
| True Negative | 3 |

---

## Per-Field Results

| Field | Exact | Trim | Contain | Incorrect | Missed | F1 |
|-------|-------|------|---------|-----------|--------|----|
| accident_type | 0 | 1 | 4 | 0 | 0 | 1.000 |
| officer | 0 | 5 | 0 | 0 | 0 | 1.000 |
| report_number | 5 | 0 | 0 | 0 | 0 | 1.000 |
| date_time | 4 | 0 | 0 | 0 | 1 | 0.889 |
| light_condition | 2 | 0 | 2 | 1 | 0 | 0.800 |
| location | 0 | 0 | 4 | 1 | 0 | 0.800 |
| property_damage | 0 | 0 | 4 | 1 | 0 | 0.800 |
| weather | 1 | 0 | 3 | 1 | 0 | 0.800 |
| agency | 1 | 0 | 2 | 0 | 2 | 0.750 |
| contributing_factors | 0 | 0 | 0 | 1 | 1 | 0.000 |
| ems_agency | 0 | 0 | 0 | 1 | 4 | 0.000 |
| parties | 0 | 0 | 0 | 5 | 0 | 0.000 |
| road_surface | 0 | 0 | 0 | 0 | 5 | 0.000 |
| vehicles | 0 | 0 | 0 | 5 | 0 | 0.000 |
| witnesses | 0 | 0 | 0 | 4 | 1 | 0.000 |

**Zero-F1 fields remain three distinct categories:**

1. **Schema mismatch** (vehicles, parties): rich JSON vs flat string — containment cannot reconcile these.
   Awaiting path decision per `schema_mismatch_decision.md`.

2. **Never extracted** (road_surface): 0 extractions across all 5 docs. Missing template pattern.

3. **Mixed** (ems_agency, witnesses, contributing_factors): mostly MISSED (no extraction),
   one INCORRECT each. Real extraction gaps.

---

## Per-Document Results

| Document | Form ID | Correct / Total |
|----------|---------|-----------------|
| sample_full_report.pdf (TX) | tx_cr3 (correct) | 6 / 15 |
| sample_24_rain_ped_nyc.pdf (NY) | generic_mmucc (wrong) | 9 / 14 |
| sample_25_dui_wrongway_la.pdf (CA) | generic_mmucc (wrong) | 9 / 15 |
| sample_27_tropical_moto_tampa.pdf (FL) | il_sr1 (wrong) | 5 / 14 |
| sample_33_ice_ped_philadelphia.pdf (PA) | generic_mmucc (wrong) | 9 / 14 |

FL (sample_27) is the outlier at 5/14 while the other misclassified docs score 9/14.
The `il_sr1` template (wrongly applied) is more disruptive than `generic_mmucc`.

---

## Top 5 Remaining INCORRECT Failures

| Document | Field | Ground Truth | Extracted | Conf |
|----------|-------|-------------|-----------|------|
| sample_27 (FL) | weather | `"heavy rain"` | `"Tropical Storm Conditions"` | 0.929 |
| sample_full (TX) | property_damage | `"I-35W NB overhead guidance sign..."` | `"Rear bumper assembly crushed..."` | 0.851 |
| sample_27 (FL) | ems_agency | `"Tampa Fire Rescue — Rescue 1..."` | `"TPD — Case TPD-26-09-28-1441..."` | 0.685 |
| sample_full (TX) | vehicles | `"LMK-4421 (TX), MRY-8820 (TX)..."` | `[{"vin": "2T3RWRFV9NC123456"...}]` | 0.655 |
| sample_full (TX) | parties | `"Karen L. Whitfield, Marcus J..."` | `[{"role": "Operator"...}]` | 0.655 |

**Remaining real failures break into:**
- **weather (FL)**: completely wrong value — no substring overlap with "heavy rain".
- **property_damage (TX)**: extractor hit vehicle damage section instead of infrastructure damage.
- **ems_agency (FL)**: extracted a case summary line, not the EMS agency name.
- **vehicles / parties (TX)**: schema mismatch — rich JSON vs flat string; containment cannot help.
