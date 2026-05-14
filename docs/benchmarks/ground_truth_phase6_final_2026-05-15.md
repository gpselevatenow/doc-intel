# Ground Truth Benchmark — Phase 6 Final — 2026-05-15

## Headline

| Metric | Path A end-of-day | B1 Phase 5 | Phase 6 final | Delta vs Path A |
|--------|-------------------|------------|---------------|-----------------|
| F1 | 0.7971 | 0.7755 | **0.8758** | +0.0787 |
| Precision | 0.8333 | 0.8382 | **0.9054** | +0.0721 |
| Recall | 0.7639 | 0.7215 | **0.8481** | +0.0842 |

| Metric | Value |
|--------|-------|
| Accuracy | 0.7791 |
| Total Correct | 67 |
| — Exact | 34 |
| — After Trim | 6 |
| — By Containment | 27 |
| Incorrect | 7 |
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
| property_damage | 0.800 | 0.800 | 0.800 | 4 | 1 | 0 | 0 |
| report_number | 1.000 | 1.000 | 1.000 | 5 | 0 | 0 | 0 |
| road_surface | 0.889 | 1.000 | 0.800 | 4 | 0 | 1 | 0 |
| vehicles | 0.600 | 0.600 | 0.600 | 3 | 2 | 0 | 0 |
| weather | 0.800 | 0.800 | 0.800 | 4 | 1 | 0 | 0 |
| witnesses | 0.800 | 0.800 | 0.800 | 4 | 1 | 0 | 0 |

## Per-Document Summary

| Document | Form ID | Correct / Total | Conf (correct) | Conf (incorrect) |
|----------|---------|-----------------|----------------|------------------|
| sample_full_report.pdf | yes | 12 / 16 | 0.8243 | 0.5455 |
| sample_25_dui_wrongway_la.pdf | no | 15 / 16 | 0.7956 | 0.0000 |
| sample_27_tropical_moto_tampa.pdf | no | 8 / 15 | 0.8207 | 0.4056 |
| sample_24_rain_ped_nyc.pdf | no | 16 / 16 | 0.7955 | 0.0000 |
| sample_33_ice_ped_philadelphia.pdf | no | 16 / 16 | 0.7911 | 0.0000 |

NY and PA are 16/16 (all fields correct). TX is 12/16 with form_id correctly identified.

## Top 5 Remaining INCORRECT Failures

| # | Document | Field | Ground Truth | Extracted | Confidence |
|---|----------|-------|-------------|-----------|------------|
| 1 | sample_27_tropical_moto_tampa.pdf | weather | heavy rain | Tropical Storm Conditions | 0.9295 |
| 2 | sample_full_report.pdf | property_damage | I-35W NB overhead guidance sign support post at MM 54.1 — minor side-panel contact from V3 trailer | Rear bumper assembly crushed and deformed; left tail lamp assembly shattered… | 0.8898 |
| 3 | sample_full_report.pdf | vehicles | LMK-4421 (TX), MRY-8820 (TX), CMV-3319 (TX) | LMK-4421, MRY-8820, CMV-3319 | 0.6548 |
| 4 | sample_27_tropical_moto_tampa.pdf | vehicles | FL-PKT-4418, FL-QRX-8821, FL-RTW-3319, FL-SXM-7723, FL-MCY-441 | FL-PKT-4418, FL-QRX-8821, FL-RTW-3319, FL-SXM-7723 | 0.6548 |
| 5 | sample_27_tropical_moto_tampa.pdf | witnesses | Harold W. Freeman, Patricia M. Cruz, FHP Trooper R. Melendez #144, Kevin T. Morrison | Harold W. Freeman, Patricia M. Cruz, FHP Trooper R. Melendez, Kevin T. Morrison | 0.6548 |

**Failure notes:**
- #1 (FL weather): Checkbox grid extractor reads "Tropical Storm" label from a weather checkbox; "heavy rain" is the narrative description. Extractor picks checkbox over narrative.
- #2 (TX property_damage): Extractor picks up V1 vehicle damage narrative instead of the non-vehicle infrastructure damage (Section 6 sign post). Section boundary parsing issue.
- #3 (TX vehicles): State suffix `(TX)` not included in plate extraction; frozenset comparison fails on format mismatch.
- #4 (FL vehicles): Motorcyclist V5 (FL-MCY-441) not extracted — `Moto-` prefix row not matched by vehicle extractor.
- #5 (FL witnesses): Continuation-line lookahead appends first word only; badge number `#144` is a non-name token and is not captured.

## Audit Trail — Phase 6 Commits

| Phase | Hash | Description |
|-------|------|-------------|
| 6b | `21817f7` | Strip parenthetical annotation from passenger names |
| 6c | `929ac04` | Add Veh-Name-DOB compact table parser for CA/FL/NY/PA |
| 6d | `1485f50` | Extend party-section boundary to fire on Section 5 / Witnesses |
| 6e.1 | `a7c01a2` | GT fix — add Fatima R. Ahmed to NY passengers |
| 6e.3 | `037e672` | Witness extractor — continuation-line handling + TX format variant |

All commits on `main`. No commits between 6e.1 and 6e.3 (6e.2 was a verification-only benchmark run, not committed).

## Phase 6 Coverage Gains (vs B1 Phase 5 baseline)

| Field | B1 Phase 5 F1 | Phase 6 Final F1 | Change |
|-------|---------------|------------------|--------|
| operators | 1.000 | 1.000 | — |
| passengers | 0.000 | **1.000** | +1.000 |
| pedestrians | 0.000 | **1.000** | +1.000 |
| witnesses | 0.222 | **0.800** | +0.578 |
| Overall | 0.7755 | **0.8758** | +0.1003 |
