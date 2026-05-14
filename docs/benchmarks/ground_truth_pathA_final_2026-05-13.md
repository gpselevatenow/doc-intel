# Ground Truth Benchmark — 2026-05-13

## Summary

| Metric | Value |
|--------|-------|
| Precision | 0.8333 |
| Recall | 0.7639 |
| F1 | 0.7971 |
| Accuracy | 0.6627 |
| Total Correct | 55 |
| — Exact | 22 |
| — After Trim | 6 |
| — By Containment | 27 |
| Incorrect | 11 |
| Missed | 6 |
| Spurious | 0 |
| True Negative | 3 |

## Per-Field Results

| Field                | Exact | Trim | Contain | Incorrect | Missed | Spurious | Precision | Recall | F1    |
|----------------------|-------|------|---------|-----------|--------|----------|-----------|--------|-------|
| accident_type        | 0     | 1    | 4       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| agency               | 1     | 0    | 2       | 0         | 2      | 0        | 1.000     | 0.600  | 0.750 |
| contributing_factors | 0     | 0    | 1       | 0         | 1      | 0        | 1.000     | 0.500  | 0.667 |
| date_time            | 4     | 0    | 0       | 0         | 1      | 0        | 1.000     | 0.800  | 0.889 |
| ems_agency           | 0     | 0    | 5       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| light_condition      | 2     | 0    | 2       | 1         | 0      | 0        | 0.800     | 0.800  | 0.800 |
| location             | 0     | 0    | 4       | 1         | 0      | 0        | 0.800     | 0.800  | 0.800 |
| officer              | 0     | 5    | 0       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| parties              | 3     | 0    | 0       | 2         | 0      | 0        | 0.600     | 0.600  | 0.600 |
| property_damage      | 0     | 0    | 4       | 1         | 0      | 0        | 0.800     | 0.800  | 0.800 |
| report_number        | 5     | 0    | 0       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| road_surface         | 2     | 0    | 2       | 0         | 1      | 0        | 1.000     | 0.800  | 0.889 |
| vehicles             | 3     | 0    | 0       | 2         | 0      | 0        | 0.600     | 0.600  | 0.600 |
| weather              | 1     | 0    | 3       | 1         | 0      | 0        | 0.800     | 0.800  | 0.800 |
| witnesses            | 1     | 0    | 0       | 3         | 1      | 0        | 0.250     | 0.200  | 0.222 |

## Per-Document Results

| Document                           | Form ID | Correct | Total | Conf (correct) | Conf (incorrect) |
|------------------------------------|---------|---------|-------|----------------|------------------|
| sample_24_rain_ped_nyc.pdf         | no      | 13      | 14    | 0.8280         | 0.6548           |
| sample_25_dui_wrongway_la.pdf      | no      | 14      | 15    | 0.8056         | 0.0000           |
| sample_27_tropical_moto_tampa.pdf  | no      | 7       | 14    | 0.8444         | 0.4056           |
| sample_33_ice_ped_philadelphia.pdf | no      | 12      | 14    | 0.8365         | 0.6548           |
| sample_full_report.pdf             | yes     | 9       | 15    | 0.8808         | 0.4728           |

## Confidence Calibration

Mean confidence on **correct** extractions:   **0.8349** (n=55)
Mean confidence on **incorrect** extractions: **0.4495** (n=17)

## Top 10 Failures (by confidence)

| Document                           | Field           | Ground Truth                             | Extracted                                | Confidence | Status    |
|------------------------------------|-----------------|------------------------------------------|------------------------------------------|------------|-----------|
| sample_27_tropical_moto_tampa.pdf  | weather         | heavy rain                               | Tropical Storm Conditions                | 0.9295     | INCORRECT |
| sample_full_report.pdf             | property_damage | I-35W NB overhead guidance sign support  | Rear bumper assembly crushed and deforme | 0.8898     | INCORRECT |
| sample_full_report.pdf             | vehicles        | LMK-4421 (TX), MRY-8820 (TX), CMV-3319 ( | LMK-4421, MRY-8820, CMV-3319             | 0.6548     | INCORRECT |
| sample_full_report.pdf             | parties         | Karen L. Whitfield, Marcus J. Reyna, Bob | Karen L. Whitfield, Marcus J. Reyna, Bob | 0.6548     | INCORRECT |
| sample_27_tropical_moto_tampa.pdf  | vehicles        | FL-PKT-4418, FL-QRX-8821, FL-RTW-3319, F | FL-PKT-4418, FL-QRX-8821, FL-RTW-3319, F | 0.6548     | INCORRECT |
| sample_27_tropical_moto_tampa.pdf  | witnesses       | Harold W. Freeman, Patricia M. Cruz, FHP | Harold W. Freeman, Patricia M. Cruz, FHP | 0.6548     | INCORRECT |
| sample_24_rain_ped_nyc.pdf         | witnesses       | Calvin R. Moore, Maria T. Santos, David  | Calvin R. Moore, Maria T. Santos, David  | 0.6548     | INCORRECT |
| sample_33_ice_ped_philadelphia.pdf | parties         | Eileen C. Murphy, Miguel A. Gonzalez, Sh | Eileen C. Murphy, Miguel A. Gonzalez, Sh | 0.6548     | INCORRECT |
| sample_33_ice_ped_philadelphia.pdf | witnesses       | Franklin T. Booker, Denise P. Rawlins, A | Franklin T. Booker, Denise P. Rawlins, A | 0.6548     | INCORRECT |
| sample_full_report.pdf             | light_condition | Night                                    | , reduced                                | 0.6376     | INCORRECT |

## Flattening Applied (14 extractions)

| Document                           | Field     | Status    | Flattened Value                                         |
|------------------------------------|-----------|-----------|---------------------------------------------------------|
| sample_full_report.pdf             | vehicles  | INCORRECT | LMK-4421, MRY-8820, CMV-3319                            |
| sample_full_report.pdf             | parties   | INCORRECT | Karen L. Whitfield, Marcus J. Reyna, Bobby R. Hastings, |
| sample_25_dui_wrongway_la.pdf      | vehicles  | CORRECT   | CA-7HKR441, CA-8LTX224, CA-6PKW881, CA-9MXP112, CA-4TNW |
| sample_25_dui_wrongway_la.pdf      | parties   | CORRECT   | Marco A. Torres, Keiko L. Nakamura, David B. Greenberg, |
| sample_25_dui_wrongway_la.pdf      | witnesses | CORRECT   | Felix R. Dominguez, Priscilla T. Wan, LAPD Air-7 Crew,  |
| sample_27_tropical_moto_tampa.pdf  | vehicles  | INCORRECT | FL-PKT-4418, FL-QRX-8821, FL-RTW-3319, FL-SXM-7723      |
| sample_27_tropical_moto_tampa.pdf  | parties   | CORRECT   | Elena B. Santos, Charles T. Walters, Yuna S. Kim, Preet |
| sample_27_tropical_moto_tampa.pdf  | witnesses | INCORRECT | Harold W. Freeman, Patricia M. Cruz, FHP Trooper R., Ke |
| sample_24_rain_ped_nyc.pdf         | vehicles  | CORRECT   | NY-HKR-4418, NY-JLX-8821, NY-KBW-3319, NY-LCM-7723      |
| sample_24_rain_ped_nyc.pdf         | parties   | CORRECT   | Roberto E. Castillo, Ji-Young Kim, Tariq B. Ahmed, Bles |
| sample_24_rain_ped_nyc.pdf         | witnesses | INCORRECT | Calvin R. Moore, Maria T. Santos, David K. Owner, Julia |
| sample_33_ice_ped_philadelphia.pdf | vehicles  | CORRECT   | PA-APX-4418, PA-BKR-8821, PA-CTX-3319, PA-DLM-7723, PA- |
| sample_33_ice_ped_philadelphia.pdf | parties   | INCORRECT | Eileen C. Murphy, Miguel A. Gonzalez, Sharon Y. Chen, C |
| sample_33_ice_ped_philadelphia.pdf | witnesses | INCORRECT | Franklin T. Booker, Denise P. Rawlins, Alonzo W. Coffee |
