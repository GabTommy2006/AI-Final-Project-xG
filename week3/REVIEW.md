# Week 3 implementation review

Reference: teacher's 3rd week of Artificial Intelligence Project.md and agreed WBS: Week 3 baseline pipeline, Week 4 improvement, Week 5 integration/reporting.

## Technical evidence

- Cleaning: source hashes, duplicate rejection, eligibility filters and reconciled counts.
- Transformation: binary target and training-only scaling saved with the model.
- Splitting: chronological whole-match 60/20/20; IDs, dates, counts and competition composition saved.
- Features: distance/goal-mouth angle; future categorical fields retained separately.
- Model justification: fixed regularized logistic baseline and constant comparator explained in README.
- Baseline metrics: train/validation/test log loss, Brier, AUC, calibration bins and group scores.
- Week 4 plan: validation-based comparisons, calibration and independent evaluation planning.
- Broader collection: all available senior men's Europe/World Cup matches since 2001 at the pinned revision. Evidence: data/coverage.json, source_manifest.json, download_status.json and results/validation.json.

Completeness means all eligible public matches at this revision, not complete real-world seasons. Download status must have zero failures and selected-match/event-manifest counts must agree. Expanded results are a new dataset baseline, not algorithmic improvement over the Week 2 pilot. Week 2 files remain intact.

## Presentation records

Code/README/results provide technical evidence and a solo owner. The teacher also asks what/when/why/who, planned versus actual hours and gap management, risks, changes and issues. Student-specific hours, feedback and timetable records must be completed truthfully. This repository does not claim those fields are finished.

## Holdout interpretation

Expanded match metadata establishes new split boundaries before performance is computed. Test is reported for the requested baseline. Week 4 selection must use validation. This inspected test cannot later be described as untouched; independent evaluation is needed for that claim. Multi-competition samples are unbalanced: inspect composition and sample sizes before generalizing.
