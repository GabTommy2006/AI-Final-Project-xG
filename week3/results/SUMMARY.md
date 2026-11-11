# Week 3 expanded baseline — actual results

Source revision: `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.

Selected 2,411 matches across 43 competition-seasons, 2003-08-16 to 2024-07-14.

Raw: 8,665,058 events and 60,375 shots. Retained: 59,519 non-penalty shots, 6,074 goals.

## Cleaning exclusions

- excluded_penalty: 684.
- excluded_period: 169.
- invalid_location: 3.

## Match-disjoint chronological split

- train: 1,446 matches, 35,559 shots, 3,598 goals; 2003-08-16 to 2016-02-28.
- validation: 482 matches, 11,909 shots, 1,197 goals; 2016-02-28 to 2017-01-08.
- test: 483 matches, 12,051 shots, 1,279 goals; 2017-01-14 to 2024-07-14.

## Baseline metrics

- train, constant: log loss 0.327677; Brier 0.090946; ROC-AUC 0.500000.
- train, logistic: log loss 0.288390; Brier 0.082156; ROC-AUC 0.748427.
- validation, constant: log loss 0.326209; Brier 0.090410; ROC-AUC 0.500000.
- validation, logistic: log loss 0.289832; Brier 0.082933; ROC-AUC 0.746072.
- test, constant: log loss 0.338484; Brier 0.094893; ROC-AUC 0.500000.
- test, logistic: log loss 0.303657; Brier 0.086991; ROC-AUC 0.731592.

## Coverage and interpretation limits

All available matches satisfying the scope at this source revision were downloaded. Open-data coverage is incomplete relative to real competition schedules: these are not all European matches since 2001. Champions League entries are selected finals, and many seasons are team/player-focused samples. World Cup coverage here is 2018 and 2022.

The expanded scores use a different population and split from the Week 2 pilot. Do not claim model improvement by comparing these scores directly with the old pilot. Training is still the same fixed distance/angle logistic baseline.

Chronological splitting changes competition composition over time. Inspect split_summary.json and competition_metrics.json before interpreting pooled scores. Sparse groups and calibration bins are uncertain; no confidence interval or statistical superiority claim is made.

With this split, both World Cup editions appear only in test, not training. Their scores measure transfer from the earlier European training sample rather than within-World-Cup validation.

This test has now been inspected for baseline reporting. Week 4 selection must use validation; an independent evaluation is needed for an untouched final performance claim.

Data attribution: StatsBomb Open Data (Hudl). Follow the source LICENSE.pdf and README when using or publishing data/results. Raw event JSON is not committed.
