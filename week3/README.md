# Week 3 — Data Preparation & Modeling Approach

## Deliverable and actual scope

This implements the Week 3 baseline pipeline WBS package, not the Week 4 model improvement or Week 5 application. One student owns all tasks. Actual hours, planned hours and tutor feedback have not been supplied; they must be recorded honestly before presenting.

Project purpose: estimate P(goal | observed pre-shot features) for an already attempted, non-penalty shot. Output is a probability between 0 and 1, not a guaranteed outcome. Summed shot xG describes expected goals for those shots; it is not a complete match score forecasting model.

The project scope is men's European competitions from 2001 onward plus men's FIFA World Cup. **The actual checked run remains the pinned 100-match EPL 2015/16 pilot**, August 8–October 25, 2015. This is an end-to-end baseline implementation, not a completed collection of the broader project dataset. The CLI can accept another curated match manifest and event cache, but broader coverage must be collected, pinned and audited separately. The European country allowlist is a supported subset, not an exhaustive geographic classification.

## Run on Windows

From the project root, using the existing Python 3.11 environment:

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
.\.venv311\Scripts\python.exe week3/pipeline.py
.\.venv311\Scripts\python.exe -m unittest discover -s week3 -v
.\.venv311\Scripts\python.exe week3/predict.py --x 108 --y 40
```

If the raw cache is missing, run `download_data.py` first as described in the root README. The pipeline itself runs offline. It writes only `week3/results/`, keeping the Week 2 root outputs intact. Running it again replaces its Week 3 outputs.

## Teacher's specials mapped to implementation

1. **Cleaning:** extract Shot events from JSON; fail on duplicate Shot IDs; exclude missing IDs, periods outside 1–4, penalties, missing shot type/outcome and invalid/out-of-range coordinates. Exclusion counts use the first applicable reason, so they reconcile with retained shots. No arbitrary outlier removal: valid long-distance shots remain. No label or coordinate imputation. Own Goal events are not Shot events.
2. **Transformation and features:** goal label is 1 when `shot.outcome.name == Goal`, otherwise 0 for recorded outcomes. Goal centre is (120,40), posts (120,36) and (120,44). Distance is `hypot(120-x,y-40)`; angle is the angle subtended by both posts, in radians. Distances are StatsBomb coordinate units, not metres. Both attacking directions are already normalized in StatsBomb event coordinates. Two features are standardized using training means and population standard deviations only. Zero-variance scales become 1.
3. **Splitting:** order whole matches by `(match_date, match_id)` and allocate 60/20/20 by match count. Every shot in one match stays in the same split. Same dates may cross a boundary; this is an ordered retrospective holdout, not strict day-separated prospective validation. No shuffling, oversampling or class weights. Validation is reserved for Week 4 decisions; test must not guide feature selection or tuning.
4. **Model selection:** compare the training goal-rate constant with L2 logistic regression using distance and angle. Tabular low-dimensional data and a five-week solo project favour a transparent, inexpensive probabilistic baseline. CNN/LSTM inputs are not present in this baseline. Fixed L2=1 on standardized slopes, unpenalized intercept; summed negative log likelihood plus half the squared slope norm, Newton optimization with backtracking. This fixes the meaning of regularization independently of library conventions. No hyperparameter search was performed. Fitted model and preprocessing parameters are saved together.
5. **Metrics:** report log loss and Brier score (lower is better), ROC-AUC (higher is better; ranking, not accuracy) and calibration bins. Both probability scores mix discrimination and calibration. Accuracy is not the main metric for rare goals. Inspect bin counts before interpreting calibration.
6. **Week 4 plan:** curate and pin the broader in-scope dataset; revise split boundaries before evaluating models on that dataset; add body part and shot/play context with train-fitted encoders and explicit missing-category handling; compare logistic variants and a tree model on validation; inspect calibration and competition-level error; freeze the selected model before a final test evaluation. Do not claim broader performance from the pilot test. Week 5 remains integration, demonstration and final reporting.

## Actual results from this implementation

- Input: 342,950 events, 2,647 shots. Removed: 19 penalties. Retained: 2,628 shots, 249 goals.
- Train: 60 matches, 1,586 shots, 131 goals.
- Validation: 20 matches, 556 shots, 67 goals.
- Test: 20 matches, 486 shots, 51 goals.
- Test constant: log loss 0.338855; Brier 0.094425; ROC-AUC 0.500000.
- Test logistic: log loss 0.273940; Brier 0.080473; ROC-AUC 0.811449.
- Example (108,40): xG 0.133537. Interpreted as approximately 13.35% estimated goal probability for an eligible shot with these two features, not an individual guarantee.

These intentionally reproduce Week 2's pilot; Week 3 adds a reusable callable pipeline, explicit cleaning checks, serialized inference, tests and documented modeling decisions. They do not constitute a new performance improvement. Mean predicted test xG is 0.08842 versus observed goal rate 0.10494; calibration is imperfect and the highest probability bins are very small. No statistical superiority or transfer to other competitions is established.

## Evidence files

- `pipeline.py`: extraction → cleaning → geometry → split → train-only scaling → fit → evaluate/save.
- `predict.py`: loads the saved baseline and outputs one eligible shot's xG using x/y only. Do not use for penalties or shootouts. The baseline averages over omitted factors such as goalkeeper and defender positions, body part and shooter skill.
- `test_pipeline.py`: analytic geometry and metric examples, match separation, train-only scaling, saved-model prediction reconstruction and regression against retained Week 2 metrics.
- `results/data_audit.json`: counts, dates, source hashes and runtime versions. Pilot hashes are checked before fitting. Additional source hashes are recorded but require a separately trusted manifest before claiming pinned provenance.
- `results/split_matches.json`: match membership; `model.json`: weights/scaler; `metrics.json`: all split scores/calibration; `predictions.csv`: per-shot traceability.

Leakage exclusions: provider xG, outcome, end location, goal label, shot-on-target and future events never enter the feature matrix. Goal is used only as a supervised target. Optional pressure qualifiers are not coerced into observed false values or used as baseline inputs.

## Reporting and risks

Deliver the code, audit, split diagram, feature geometry diagram, baseline comparison and Week 4 plan for the Week 3 presentation. Use the numeric results files as evidence. Main risks remain single-league sample bias, sparse goals, imperfect calibration and broader-source coverage. No tutor-requested scope changes or actual time totals are known. Record actual work time and compare it to your own planned hours; do not substitute generated estimates for real hours.

Source: Hudl/StatsBomb Open Data, repository revision and file hashes retained in the project manifests. Follow its licensing and attribution requirements when redistributing data or results.
