# Ground Truth Benchmark — 2026-05-13

## Summary

| Metric | Value |
|--------|-------|
| Precision | 0.3276 |
| Recall | 0.2639 |
| F1 | 0.2923 |
| Accuracy | 0.1712 |
| Correct | 13 |
| Correct After Trim | 6 |
| Incorrect | 39 |
| Missed | 14 |
| Spurious | 0 |
| True Negative | 3 |
| Trim Corrections | 6 |

## Per-Field Results

| Field                | Correct | Trim | Incorrect | Missed | Spurious | Precision | Recall | F1    |
|----------------------|---------|------|-----------|--------|----------|-----------|--------|-------|
| accident_type        | 0       | 1    | 4         | 0      | 0        | 0.200     | 0.200  | 0.200 |
| agency               | 1       | 0    | 2         | 2      | 0        | 0.333     | 0.200  | 0.250 |
| contributing_factors | 0       | 0    | 1         | 1      | 0        | 0.000     | 0.000  | 0.000 |
| date_time            | 4       | 0    | 0         | 1      | 0        | 1.000     | 0.800  | 0.889 |
| ems_agency           | 0       | 0    | 1         | 4      | 0        | 0.000     | 0.000  | 0.000 |
| light_condition      | 2       | 0    | 3         | 0      | 0        | 0.400     | 0.400  | 0.400 |
| location             | 0       | 0    | 5         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| officer              | 0       | 5    | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| parties              | 0       | 0    | 5         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| property_damage      | 0       | 0    | 5         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| report_number        | 5       | 0    | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| road_surface         | 0       | 0    | 0         | 5      | 0        | 0.000     | 0.000  | 0.000 |
| vehicles             | 0       | 0    | 5         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| weather              | 1       | 0    | 4         | 0      | 0        | 0.200     | 0.200  | 0.200 |
| witnesses            | 0       | 0    | 4         | 1      | 0        | 0.000     | 0.000  | 0.000 |

## Per-Document Results

| Document                           | Form ID | Correct | Total | Conf (correct) | Conf (incorrect) |
|------------------------------------|---------|---------|-------|----------------|------------------|
| sample_24_rain_ped_nyc.pdf         | no      | 4       | 14    | 0.9144         | 0.6113           |
| sample_25_dui_wrongway_la.pdf      | no      | 3       | 15    | 0.9213         | 0.5722           |
| sample_27_tropical_moto_tampa.pdf  | no      | 2       | 14    | 0.9592         | 0.5572           |
| sample_33_ice_ped_philadelphia.pdf | no      | 5       | 14    | 0.8448         | 0.6013           |
| sample_full_report.pdf             | yes     | 5       | 15    | 0.9568         | 0.4340           |

## Confidence Calibration

Mean confidence on **correct** extractions:   **0.9130** (n=19)
Mean confidence on **incorrect** extractions: **0.5551** (n=53)

## Top 10 Failures (by confidence)

| Document                           | Field         | Ground Truth                             | Extracted                              | Confidence | Status    |
|------------------------------------|---------------|------------------------------------------|----------------------------------------|------------|-----------|
| sample_24_rain_ped_nyc.pdf         | accident_type | 4-vehicle collision + 2 pedestrians stru | 4-vehicle collision + 2 pedestrians    | 0.9423     | INCORRECT |
| sample_33_ice_ped_philadelphia.pdf | accident_type | 5-vehicle intersection pileup + 2 pedest | 5-vehicle intersection pileup + 2      | 0.9423     | INCORRECT |
| sample_27_tropical_moto_tampa.pdf  | accident_type | 4-vehicle chain collision                | 4-vehicle chain collision + motorcycle | 0.9313     | INCORRECT |
| sample_27_tropical_moto_tampa.pdf  | weather       | heavy rain                               | Tropical Storm Conditions              | 0.9295     | INCORRECT |
| sample_25_dui_wrongway_la.pdf      | location      | I-405 Northbound, Mile Marker 38.2 (near | I-405 Northbound, Mile Marker 38.2     | 0.9252     | INCORRECT |
| sample_24_rain_ped_nyc.pdf         | location      | Queens Blvd & 69th Road (intersection),  | Queens Blvd & 69th Road                | 0.9252     | INCORRECT |
| sample_33_ice_ped_philadelphia.pdf | location      | Broad Street & Washington Avenue (inters | Broad Street & Washington Avenue       | 0.9252     | INCORRECT |
| sample_full_report.pdf             | location      | I-35W Northbound between Exit 54A (N. Ta | I-35W Northbound between Exit 54A      | 0.9250     | INCORRECT |
| sample_25_dui_wrongway_la.pdf      | weather       | Clear                                    | Clear / Dry                            | 0.8952     | INCORRECT |
| sample_24_rain_ped_nyc.pdf         | weather       | Thunderstorm                             | Heavy Rain / Thunderstorm              | 0.8952     | INCORRECT |
