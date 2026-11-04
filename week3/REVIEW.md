# Week 3 implementation review

Reviewed against the teacher's `3rd week of Artificial Intelligence Project.md` and the agreed schedule: Week 3 baseline pipeline, Week 4 model improvement, Week 5 integration & reporting.

## Required technical evidence

- Cleaning: implemented with exclusion counts, input checks, source checksums and duplicate rejection; exercised on raw pilot data and synthetic invalid events.
- Transformation: implemented binary target and train-only standardization; scaler is saved for inference.
- Splitting strategy: implemented chronological match-disjoint 60/20/20 with reproducible match IDs.
- Feature engineering: implemented distance and goal-mouth angle; undefined angles at goalpost coordinates are rejected.
- Model choice: justified logistic regression and constant comparator in README; fixed regularization, no tuning claims.
- Baseline metrics: all three splits have log loss, Brier score, ROC-AUC and calibration bins in `results/metrics.json`.
- Week 4 tasks: documented in README; improvement and validation-based selection remain future work.

The Week 3 baseline package is complete **for the 100-match pilot dataset**. The broader European men's/World Cup collection has not been implemented or evaluated. This is an outstanding project scope item, not a completed WBS deliverable. Carry it into Week 4 explicitly; if the tutor requires the full project dataset in Week 3, this run alone does not satisfy that requirement. No statement here changes the agreed project scope.

## Presentation items still requiring student input

The teacher also asks what/when/why/who, planned versus actual hours and gap management, last week's risks, changes and issues. Code and README provide technical evidence and the solo owner, but do not replace the weekly presentation. Planned and actual hours, tutor feedback and any confirmed timetable changes must be supplied by the student. Do not report these fields as completed or fabricate values.

## Interpretation limits

Week 3 reproduces Week 2 scores because its baseline and dataset are unchanged. The contribution is an executable pipeline and reusable model with checks. Test results already inspected during the pilot cannot serve as an untouched holdout for repeated Week 4 model selection. Use validation for development and establish an independent final evaluation before making broader claims.
