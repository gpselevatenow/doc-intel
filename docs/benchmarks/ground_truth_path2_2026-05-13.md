# Ground Truth Benchmark — Path 2 (Trim + Containment + Flattening) — 2026-05-13

## Comparison Table

| Run | Normalization | Classifier | F1 | Exact | After-Trim | By-Containment | Incorrect | Missed |
|-----|---------------|------------|-----|-------|------------|----------------|-----------|--------|
| A | strict | as-is | 0.2000 | 13 | — | — | 45 | 14 |
| B | trim | as-is | 0.2923 | 13 | 6 | — | 39 | 14 |
| Path 1 | trim + containment | as-is | 0.5846 | 13 | 6 | 19 | 20 | 14 |
| Path 2 | trim + containment + flatten | as-is | **0.6307** | 16 | 6 | 19 | 17 | 14 |

Flattening promoted 3 additional CORRECT (vehicles: CA, NY, PA now score exact match after
plate extraction). Exact count rises from 13 → 16. Missed stays flat at 14.
Total correct: 41/72.

---

## Summary

| Metric | Value |
|--------|-------|
| Precision | 0.7069 |
| Recall | 0.5694 |
| F1 | **0.6307** |
| Accuracy | 0.4607 |
| Total Correct | 41 |
| — Exact | 16 |
| — After Trim | 6 |
| — By Containment | 19 |
| Incorrect | 17 |
| Missed | 14 |
| Spurious | 0 |
| True Negative | 3 |
| Flattening Applied | 14 |

---

## Per-Field F1 Table

| Field | Exact | Trim | Contain | Incorrect | Missed | F1 | Notes |
|-------|-------|------|---------|-----------|--------|----|-------|
| accident_type | 0 | 1 | 4 | 0 | 0 | **1.000** | |
| officer | 0 | 5 | 0 | 0 | 0 | **1.000** | |
| report_number | 5 | 0 | 0 | 0 | 0 | **1.000** | |
| date_time | 4 | 0 | 0 | 0 | 1 | 0.889 | |
| agency | 1 | 0 | 2 | 0 | 2 | 0.750 | |
| **vehicles** | **3** | 0 | 0 | **2** | 0 | **0.600** | Flattened. CA/NY/PA correct. TX missing state suffix "(TX)"; FL wrong. |
| light_condition | 2 | 0 | 2 | 1 | 0 | 0.800 | |
| location | 0 | 0 | 4 | 1 | 0 | 0.800 | |
| property_damage | 0 | 0 | 4 | 1 | 0 | 0.800 | |
| weather | 1 | 0 | 3 | 1 | 0 | 0.800 | |
| contributing_factors | 0 | 0 | 0 | 1 | 1 | 0.000 | |
| ems_agency | 0 | 0 | 0 | 1 | 4 | 0.000 | |
| **parties** | 0 | 0 | 0 | **5** | 0 | **0.000** | Flattened but still incorrect. See below. |
| road_surface | 0 | 0 | 0 | 0 | 5 | 0.000 | Never extracted. |
| **witnesses** | 0 | 0 | 0 | **4** | 1 | **0.000** | Flattened but name field includes address/description. |

### vehicles detail
Three of five documents now score CORRECT after plate extraction:
- CA (`ca_chp555`): `CA-7HKR441, CA-8LTX224, CA-6PKW881, CA-9MXP112, CA-...` — exact match
- NY (`ny_mv104a`): `NY-HKR-4418, NY-JLX-8821, NY-KBW-3319, NY-LCM-7723` — exact match
- PA (`pa_aa600`): `PA-APX-4418, PA-BKR-8821, PA-CTX-3319, PA-DLM-7723, ...` — exact match

Two still incorrect:
- TX (`tx_cr3`): extracted `LMK-4421, MRY-8820, CMV-3319` — missing `(TX)` state suffix from ground truth
- FL (`fl_hsmv`): plates present but only 4 of 5 extracted (wrong template applied, `il_sr1`)

### parties detail
Flattening runs but parties still score 0/5:
- TX: extractor produces only 1 operator record (`Karen L. Whitfield`); ground truth has 3 parties
- CA–PA: names extracted but counts differ from ground truth (extractor may be omitting
  pedestrians/passengers that aren't tagged as operators, or name keys don't match)

### witnesses detail
Flattened names include embedded address/description concatenated into the name field (e.g.,
`"Felix R. Dominguez Motorist, pulled to shoulder..."`, `"Calvin R. Moore 6912 Queens Blvd..."`).
The extractor is writing full narrative into the name field — the flattener extracts it verbatim
and the comparison fails.

---

## Per-Document Results

| Document | Form ID | Correct / Total | Delta vs Path 1 |
|----------|---------|-----------------|-----------------|
| sample_full_report.pdf (TX) | tx_cr3 ✓ | 6 / 15 | 0 |
| sample_24_rain_ped_nyc.pdf (NY) | generic_mmucc ✗ | 10 / 14 | +1 |
| sample_25_dui_wrongway_la.pdf (CA) | generic_mmucc ✗ | 10 / 15 | +1 |
| sample_27_tropical_moto_tampa.pdf (FL) | il_sr1 ✗ | 5 / 14 | 0 |
| sample_33_ice_ped_philadelphia.pdf (PA) | generic_mmucc ✗ | 10 / 14 | +1 |

TX unchanged (vehicles INCORRECT due to missing state suffix; parties still 1/3 names).
FL unchanged (wrong template, no vehicle plates extracted cleanly).

---

## Top 5 Remaining INCORRECT Failures

| Document | Field | Ground Truth | Extracted | Conf |
|----------|-------|-------------|-----------|------|
| sample_27 (FL) | weather | `"heavy rain"` | `"Tropical Storm Conditions"` | 0.929 |
| sample_full (TX) | property_damage | `"I-35W NB overhead guidance sign..."` | `"Rear bumper assembly crushed..."` | 0.851 |
| sample_27 (FL) | ems_agency | `"Tampa Fire Rescue — Rescue 1..."` | `"TPD — Case TPD-26-09-28-1441..."` | 0.685 |
| sample_full (TX) | vehicles | `"LMK-4421 (TX), MRY-8820 (TX), CMV-3319 (TX)"` | `"LMK-4421, MRY-8820, CMV-3319"` | 0.655 |
| sample_full (TX) | parties | `"Karen L. Whitfield, Marcus J. Reyna, Bobby R. Hastings"` | `"Karen L. Whitfield"` | 0.655 |

**Failure analysis:**
- **weather (FL)**: Completely wrong semantic value. No substring overlap possible.
- **property_damage (TX)**: Extractor capturing vehicle damage section, not infrastructure.
- **ems_agency (FL)**: Extractor hitting case summary line instead of EMS agency name.
- **vehicles (TX)**: Flattener works — plates extracted correctly — but ground truth includes `(TX)` state suffix that the extractor omits from the plate field.
- **parties (TX)**: Only 1 of 3 parties extracted — extractor produces a single-operator record; the other two vehicle operators are missing from the JSON output.

---

## Flattening Applied Audit

14 extractions used flattening across 5 docs × 3 fields (vehicles, parties, witnesses).

| Document | Field | Status | Flattened Value |
|----------|-------|--------|-----------------|
| sample_full_report.pdf | vehicles | INCORRECT | `LMK-4421, MRY-8820, CMV-3319` |
| sample_full_report.pdf | parties | INCORRECT | `Karen L. Whitfield` |
| sample_25_dui_wrongway_la.pdf | vehicles | CORRECT | `CA-7HKR441, CA-8LTX224, CA-6PKW881, ...` |
| sample_25_dui_wrongway_la.pdf | parties | INCORRECT | `Marco A. Torres, Keiko L. Nakamura, ...` |
| sample_25_dui_wrongway_la.pdf | witnesses | INCORRECT | `Felix R. Dominguez Motorist, pulled to...` |
| sample_27_tropical_moto_tampa.pdf | vehicles | INCORRECT | `FL-PKT-4418, FL-QRX-8821, FL-RTW-3319, ...` |
| sample_27_tropical_moto_tampa.pdf | parties | INCORRECT | `Elena B. Santos, Charles T. Walters, ...` |
| sample_27_tropical_moto_tampa.pdf | witnesses | INCORRECT | `Harold W. Freeman Motorist, safely...` |
| sample_24_rain_ped_nyc.pdf | vehicles | CORRECT | `NY-HKR-4418, NY-JLX-8821, NY-KBW-3319, ...` |
| sample_24_rain_ped_nyc.pdf | parties | INCORRECT | `Roberto E. Castillo, Tariq B. Ahmed, ...` |
| sample_24_rain_ped_nyc.pdf | witnesses | INCORRECT | `Calvin R. Moore 6912 Queens Blvd, ...` |
| sample_33_ice_ped_philadelphia.pdf | vehicles | CORRECT | `PA-APX-4418, PA-BKR-8821, PA-CTX-3319, ...` |
| sample_33_ice_ped_philadelphia.pdf | parties | INCORRECT | `Eileen C. Murphy, Miguel A. Gonzalez, ...` |
| sample_33_ice_ped_philadelphia.pdf | witnesses | INCORRECT | `Franklin T. Booker Southeast corner...` |
