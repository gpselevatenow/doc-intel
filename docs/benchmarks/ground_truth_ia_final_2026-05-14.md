# Ground Truth Benchmark — 2026-05-14

## Summary

| Metric | Value |
|--------|-------|
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1 | 1.0000 |
| Accuracy | 1.0000 |
| Total Correct | 16 |
| — Exact | 12 |
| — After Trim | 0 |
| — By Containment | 4 |
| Incorrect | 0 |
| Missed | 0 |
| Spurious | 0 |
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
| officials       | 1     | 0    | 1       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| payment_summary | 0     | 0    | 0       | 0         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| recommendations | 0     | 0    | 0       | 0         | 0      | 0        | 0.000     | 0.000  | 0.000 |
| settlement      | 1     | 0    | 1       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |
| subrogation     | 1     | 0    | 1       | 0         | 0      | 0        | 1.000     | 1.000  | 1.000 |

## Per-Document Results

| Document                      | Form ID | Correct | Total | Conf (correct) | Conf (incorrect) |
|-------------------------------|---------|---------|-------|----------------|------------------|
| IA_Report_High_Complexity.pdf | no      | 7       | 7     | 0.6454         | —                |
| IA_Report_Low_Complexity.pdf  | no      | 9       | 9     | 0.6449         | —                |

## Confidence Calibration

Mean confidence on **correct** extractions:   **0.6451** (n=16)
Mean confidence on **incorrect** extractions: — (none)

## Top 10 Failures (by confidence)

None.
