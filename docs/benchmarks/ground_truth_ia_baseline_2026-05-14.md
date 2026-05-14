# Ground Truth Benchmark — 2026-05-14

## Summary

| Metric | Value |
|--------|-------|
| Precision | 0.8125 |
| Recall | 0.8667 |
| F1 | 0.8387 |
| Accuracy | 0.7222 |
| Total Correct | 13 |
| — Exact | 10 |
| — After Trim | 0 |
| — By Containment | 3 |
| Incorrect | 2 |
| Missed | 0 |
| Spurious | 1 |
| True Negative | 10 |

## Per-Field Results

| Field           | Exact | Trim | Contain | Incorrect | Missed | Spurious | Precision | Recall | F1    |
|-----------------|-------|------|---------|-----------|--------|----------|-----------|--------|-------|
| cause_of_loss   | 1     | 0    | 1       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| coverage_a      | 2     | 0    | 0       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| coverage_b      | 1     | 0    | 0       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| coverage_c      | 2     | 0    | 0       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| coverage_d      | 1     | 0    | 0       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| coverages       | 0     | 0    | 0       | 0         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| inspection_date | 2     | 0    | 0       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| inspection_firm | 0     | 0    | 0       | 0         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| officials       | 0     | 0    | 1       | 0         | 0      | 1        | 0.500     | 1.000  | 0.667 |
| payment_summary | 0     | 0    | 0       | 0         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| recommendations | 0     | 0    | 0       | 0         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| settlement      | 1     | 0    | 1       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| subrogation     | 0     | 0    | 0       | 2         | 0      | 0        | 0.000     | 0.000  | 0.000 |

## Per-Document Results

| Document                      | Form ID | Correct | Total | Conf (correct) | Conf (incorrect) |
|-------------------------------|---------|---------|-------|----------------|------------------|
| IA_Report_High_Complexity.pdf | no      | 6       | 7     | 0.6463         | 0.6923           |
| IA_Report_Low_Complexity.pdf  | no      | 7       | 9     | 0.6461         | 0.6673           |

## Confidence Calibration

Mean confidence on **correct** extractions:   **0.6462** (n=13)
Mean confidence on **incorrect** extractions: **0.6756** (n=3)

## Top 10 Failures (by confidence)

| Document                      | Field       | Ground Truth                             | Extracted | Confidence | Status    |
|-------------------------------|-------------|------------------------------------------|-----------|------------|-----------|
| IA_Report_High_Complexity.pdf | subrogation | We are investigating the manufacturer of | Potential | 0.6923     | INCORRECT |
| IA_Report_Low_Complexity.pdf  | subrogation | No. No third party is responsible for th | No        | 0.6923     | INCORRECT |
| IA_Report_Low_Complexity.pdf  | officials   | —                                        | 12345-LOW | 0.6422     | SPURIOUS  |
