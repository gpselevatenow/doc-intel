# Ground Truth Benchmark — 2026-05-13 [FORCED TEMPLATE]

## Summary

| Metric | Value |
|--------|-------|
| Precision | 0.3148 |
| Recall | 0.2361 |
| F1 | 0.2698 |
| Accuracy | 0.1560 |
| Correct | 11 |
| Correct After Trim | 6 |
| Incorrect | 37 |
| Missed | 18 |
| Spurious | 0 |
| True Negative | 3 |
| Trim Corrections | 6 |

## Per-Field Results

| Field                | Correct | Trim | Incorrect | Missed | Spurious | Precision | Recall | F1    |
|----------------------|---------|------|-----------|--------|----------|-----------|--------|-------|
| accident_type        | 0       | 1    | 4         | 0      | 0        | 0.200     | 0.200  | 0.200 |
| agency               | 0       | 0    | 3         | 2      | 0        | 0.000     | 0.000  | 0.000 |
| contributing_factors | 0       | 0    | 1         | 1      | 0        | 0.000     | 0.000  | 0.000 |
| date_time            | 4       | 0    | 0         | 1      | 0        | 1.000     | 0.800  | 0.889 |
| ems_agency           | 0       | 0    | 1         | 4      | 0        | 0.000     | 0.000  | 0.000 |
| light_condition      | 2       | 0    | 3         | 0      | 0        | 0.400     | 0.400  | 0.400 |
| location             | 0       | 0    | 3         | 2      | 0        | 0.000     | 0.000  | 0.000 |
| officer              | 0       | 5    | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| parties              | 0       | 0    | 5         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| property_damage      | 0       | 0    | 5         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| report_number        | 3       | 0    | 0         | 2      | 0        | 1.000     | 0.600  | 0.750 |
| road_surface         | 0       | 0    | 0         | 5      | 0        | 0.000     | 0.000  | 0.000 |
| vehicles             | 0       | 0    | 5         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| weather              | 2       | 0    | 3         | 0      | 0        | 0.400     | 0.400  | 0.400 |
| witnesses            | 0       | 0    | 4         | 1      | 0        | 0.000     | 0.000  | 0.000 |

## Per-Document Results

| Document                           | Form ID | Correct | Total | Conf (correct) | Conf (incorrect) |
|------------------------------------|---------|---------|-------|----------------|------------------|
| sample_24_rain_ped_nyc.pdf         | yes     | 4       | 14    | 0.9325         | 0.5809           |
| sample_25_dui_wrongway_la.pdf      | yes     | 2       | 15    | 0.9587         | 0.4668           |
| sample_27_tropical_moto_tampa.pdf  | yes     | 1       | 14    | 0.9973         | 0.5106           |
| sample_33_ice_ped_philadelphia.pdf | yes     | 5       | 14    | 0.9316         | 0.4949           |
| sample_full_report.pdf             | yes     | 5       | 15    | 0.9568         | 0.4340           |

## Confidence Calibration

Mean confidence on **correct** extractions:   **0.9463** (n=17)
Mean confidence on **incorrect** extractions: **0.4965** (n=55)

## Top 10 Failures (by confidence)

| Document                           | Field           | Ground Truth                             | Extracted                                | Confidence | Status    |
|------------------------------------|-----------------|------------------------------------------|------------------------------------------|------------|-----------|
| sample_25_dui_wrongway_la.pdf      | weather         | Clear                                    | Clear / Dry                              | 0.9948     | INCORRECT |
| sample_27_tropical_moto_tampa.pdf  | accident_type   | 4-vehicle chain collision                | 4-vehicle chain collision + motorcycle   | 0.9313     | INCORRECT |
| sample_24_rain_ped_nyc.pdf         | accident_type   | 4-vehicle collision + 2 pedestrians stru | 4-vehicle collision + 2 pedestrians      | 0.9313     | INCORRECT |
| sample_33_ice_ped_philadelphia.pdf | accident_type   | 5-vehicle intersection pileup + 2 pedest | 5-vehicle intersection pileup + 2        | 0.9313     | INCORRECT |
| sample_27_tropical_moto_tampa.pdf  | weather         | heavy rain                               | Tropical Storm Conditions                | 0.9295     | INCORRECT |
| sample_24_rain_ped_nyc.pdf         | weather         | Thunderstorm                             | Heavy Rain / Thunderstorm                | 0.9295     | INCORRECT |
| sample_full_report.pdf             | location        | I-35W Northbound between Exit 54A (N. Ta | I-35W Northbound between Exit 54A        | 0.9250     | INCORRECT |
| sample_25_dui_wrongway_la.pdf      | light_condition | Dark                                     | Artificial (freeway lighting) / Dark     | 0.8936     | INCORRECT |
| sample_27_tropical_moto_tampa.pdf  | light_condition | Dusk                                     | Dusk / Storm-darkened                    | 0.8936     | INCORRECT |
| sample_33_ice_ped_philadelphia.pdf | location        | Broad Street & Washington Avenue (inters | Street & Washington Avenue TYPE OF 5-veh | 0.8740     | INCORRECT |
