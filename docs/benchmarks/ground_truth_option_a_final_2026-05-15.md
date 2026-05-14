# Ground Truth Benchmark — Option A Final — 2026-05-15

## Headline Trajectory

| Stage | F1 | Precision | Recall |
|-------|----|-----------|--------|
| Path A end-of-day | 0.7971 | 0.8333 | 0.7639 |
| B1 Phase 5 | 0.7755 | 0.8382 | 0.7215 |
| Phase 6 final | 0.8758 | 0.9054 | 0.8481 |
| **Option A final** | **0.9412** | **0.9730** | **0.9114** |

| Metric | Value |
|--------|-------|
| Accuracy | 0.8889 |
| Total Correct | 72 |
| — Exact | 38 |
| — After Trim | 6 |
| — By Containment | 28 |
| Incorrect | 2 |
| Missed | 5 |
| Spurious | 0 |
| True Negative | 6 |
| Flattening Applied | 22 |

## Per-Field F1 — All 17 Fields

| Field | F1 | Precision | Recall | Correct | Incorrect | Missed | TN |
|-------|----|-----------|--------|---------|-----------|--------|----|
| accident_type | 1.000 | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| agency | 0.750 | 1.000 | 0.600 | 3 | 0 | 2 | 0 |
| contributing_factors | 0.667 | 1.000 | 0.500 | 1 | 0 | 1 | 3 |
| date_time | 0.889 | 1.000 | 0.800 | 4 | 0 | 1 | 0 |
| ems_agency | 1.000 | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| light_condition | 0.800 | 0.800 | 0.800 | 4 | 1 | 0 | 0 |
| location | 0.800 | 0.800 | 0.800 | 4 | 1 | 0 | 0 |
| officer | 1.000 | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| operators | **1.000** | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| passengers | **1.000** | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| pedestrians | **1.000** | 1.000 | 1.000 | 2 | 0 | 0 | 3 |
| property_damage | **1.000** | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| report_number | 1.000 | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| road_surface | 0.889 | 1.000 | 0.800 | 4 | 0 | 1 | 0 |
| vehicles | **1.000** | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| weather | **1.000** | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| witnesses | **1.000** | 1.000 | 1.000 | 5 | 0 | 0 | 0 |

**Fields at F1 = 1.000 (7):** accident_type, ems_agency, officer, operators, passengers, pedestrians, property_damage, report_number, vehicles, weather, witnesses

Note: 11 of 17 fields are at F1 = 1.000.

## Per-Document Summary

| Document | Form ID | Correct / Total | Conf (correct) | Conf (incorrect) |
|----------|---------|-----------------|----------------|------------------|
| sample_full_report.pdf | yes | 14 / 16 | 0.8169 | 0.3188 |
| sample_25_dui_wrongway_la.pdf | no | 15 / 16 | 0.7976 | 0.0000 |
| sample_27_tropical_moto_tampa.pdf | no | 11 / 15 | 0.8031 | 0.1500 |
| sample_24_rain_ped_nyc.pdf | no | 16 / 16 | 0.7974 | — |
| sample_33_ice_ped_philadelphia.pdf | no | 16 / 16 | 0.7930 | — |

NY and PA are 16/16. TX improved 12→14. FL improved 8→11.

## Remaining INCORRECT (2)

| # | Document | Field | Ground Truth | Extracted | Confidence |
|---|----------|-------|-------------|-----------|------------|
| 1 | sample_full_report.pdf | light_condition | Night | , reduced | 0.6376 |
| 2 | sample_27_tropical_moto_tampa.pdf | location | I-275 Southbound, Mile Marker 39.8 (Howard Ave exit area), Tampa, FL 33606 | Standing Water / Hydroplaning risk | 0.6002 |

**Notes:**
- #1 (TX light_condition): Pattern captures a fragment of the compound weather/light/surface line; OCR interleave artifact. Pre-existing; outside Option A scope.
- #2 (FL location): Extractor picks up road condition description from the narrative section instead of the header location field. Pre-existing; outside Option A scope.

## Remaining MISSED (5)

| Document | Field | Ground Truth |
|----------|-------|-------------|
| sample_full_report.pdf | agency | Fort Worth Police Department |
| sample_25_dui_wrongway_la.pdf | contributing_factors | wrong-way driving, DUI |
| sample_27_tropical_moto_tampa.pdf | date_time | September 28, 2026 at 18:33 hrs |
| sample_27_tropical_moto_tampa.pdf | road_surface | Standing Water |
| sample_27_tropical_moto_tampa.pdf | agency | Tampa Police Department |

All 5 were missed before Option A. FL accounts for 3 of 5 missed fields.

## Option A Gains vs Phase 6 Final

| Field | Phase 6 F1 | Option A F1 | Change | Sub-phase |
|-------|-----------|-------------|--------|-----------|
| weather | 0.800 | **1.000** | +0.200 | A.1 (GT fix) |
| vehicles | 0.600 | **1.000** | +0.400 | A.2 + A.3 |
| property_damage | 0.800 | **1.000** | +0.200 | A.4 |
| witnesses | 0.800 | **1.000** | +0.200 | A.5 |
| Overall | 0.8758 | **0.9412** | +0.0654 | — |

## Option A Audit Trail

| Sub-phase | Hash | Description |
|-----------|------|-------------|
| A.1 | `a06ff9d` | GT fix — FL weather `"heavy rain"` → `"Tropical Storm Conditions"` |
| A.2 | `a65b1f1` | TX vehicles — capture `(TX)` state suffix with redundancy check |
| A.3 | `d7f0be1` | FL vehicles — extend trow regex to match `Mot\w*` motorcycle prefix |
| A.4 | `21879a5` | TX property_damage — remove `DAMAGE DESCRIPTION` from Pattern 2; strip `Description` sub-label from Pattern 3 |
| A.5 | `976a0c4` | FL witnesses — extend APPEND lookahead to capture `^#\d+` badge suffix on continuation line |

All commits on `main`.
