# Week 3 — Data Preparation & Modeling Approach

## Purpose, scope and schedule

Estimate P(goal | pre-shot features) for an already attempted non-penalty shot. Output is a probability in [0,1], not a guaranteed goal or match score forecast. Summing shot probabilities describes expected goals for those attempted shots.

Week 3 delivers the dataset pipeline and fixed baseline; Week 4 improves/selects models on validation; Week 5 integrates the model and prepares reporting. One student owns all tasks. Planned/actual hours and tutor feedback still require the student's own records.

The expanded dataset includes every publicly available senior men's match in scope at the pinned Hudl/StatsBomb revision: European competition region or FIFA World Cup, actual match date from 2001-01-01 onward. The date filter applies to World Cup too. Competition country/region defines Europe, not host country or participating teams. UEFA Euro and Champions League are included alongside domestic leagues. Women's, youth, other continents' competitions and pre-2001 matches are excluded.

This is complete relative to the selected open-data snapshot, not all matches played in Europe. Many seasons are partial samples. See [coverage](data/COVERAGE.md) and [actual expanded results](results/SUMMARY.md). Week 2 root pilot files remain unchanged. Expanded Week 3 results replace the earlier Week 3 pilot outputs; the earlier commit and root files retain the historical pilot evidence.

## Reproduce on Windows

From the project root using the existing Python 3.11 environment:

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
.\.venv311\Scripts\python.exe week3/download_scope.py
.\.venv311\Scripts\python.exe week3/pipeline.py
.\.venv311\Scripts\python.exe week3/validate.py
.\.venv311\Scripts\python.exe week3/summarize.py
.\.venv311\Scripts\python.exe week3/predict.py --x 108 --y 40
```

Download needs Internet, several GB of uncompressed events and potentially many minutes. Raw events are compressed in raw/week3/ and excluded from Git. Transient errors are retried. Reruns verify/reuse cache. Failed download is not a complete dataset: inspect data/download_status.json and rerun before fitting. The known 100-match pilot cache is reused where possible.

Pipeline and inference run offline after download. Source revision, URLs, SHA-256 checksums and compact selected-match metadata are committed. Every selected event file is checked against the manifest before fitting. Use download_scope.py --metadata-only for coverage without events. Pipeline CLI options support explicit match/raw/output paths and source manifest/snapshot paths; keep experiment outputs separate.

The historical pilot regression check re-executes the original 100-match model using the root raw/ cache when complete, otherwise the expanded compressed cache. A fresh clone therefore needs only the expanded download for the Week 3 validation suite.

## Teacher's specials and WBS mapping

1. Cleaning: extract Shot events; reject duplicate Shot IDs; exclude missing IDs, periods outside 1–4 (including shootouts), penalties, missing shot type/outcome, invalid coordinates and undefined viewing angles exactly at goalposts. Exclusions use the first applicable reason and reconcile with retained shots. Valid long-distance shots remain. No coordinate/target imputation. Own Goal events are not Shot events.
2. Transformation: target is 1 for Goal outcome, otherwise 0 for recorded non-goal outcomes. Standardization is fitted on training only. Store means/population standard deviations with weights; zero-variance scales become 1. Apply the same training transform to validation/test.
3. Splitting: order whole matches by (match_date, match_id), allocate 60/20/20 by match count. Every shot in one match stays in its split. Same dates may cross boundaries: retrospective ordered holdout, not strict day-separated prospective validation. Expanded boundaries come from the selected manifest before fitting. No random split, oversampling or class weights.
4. Features: distance to goal centre (120,40), angle subtended by posts (120,36)/(120,44). Distance is StatsBomb coordinate units, not metres; angle is radians. Formula: hypot(120-x,y-40) and atan2(8*(120-x),(120-x)^2+(y-40)^2-16). StatsBomb events normalize attacking direction. Body part, shot type, play pattern and technique are preserved for future work but are not baseline inputs.
5. Model choice: constant training goal-rate comparator and L2 logistic regression on two standardized features. Tabular inputs and five-week solo schedule favour an interpretable, inexpensive probabilistic baseline. CNN/LSTM inputs are not present. Fixed summed negative log likelihood plus half squared slope norm (L2=1), unpenalized intercept, Newton optimization with backtracking. No hyperparameter tuning. Saved parameters support identical inference.
6. Metrics: log loss/Brier (lower is better), ROC-AUC (ranking, higher is better), calibration bins and competition-level metrics. Probability scores mix calibration and discrimination; AUC is not accuracy. One-class group AUC is undefined (null). Inspect sample/bin counts before interpreting group metrics.
7. Week 4 plan: add categorical features with train-fitted encoders and explicit missing categories; compare logistic variants/tree model using validation log loss/Brier; inspect group errors/calibration; freeze selection before final reporting. Collect independent evaluation before claiming an untouched final test because baseline test labels have now been inspected. Do not directly compare expanded scores with the different Week 2 pilot population as model improvement.

Provider xG, outcome, goal label, end location, shot-on-target and future events never enter the feature matrix. Goal/outcome are supervised labels only. Optional pressure qualifiers are not coerced into observed false inputs.

## Evidence and code

- scope.py: shared geographic, gender, adult and date policy.
- download_scope.py: catalogue, match selection, concurrent compressed download, resume, checksums and status.
- data/: pinned catalogue, compact match metadata, source manifest, coverage and snapshot. Original season metadata is cached locally and ignored by Git.
- pipeline.py: cleaning, features, split, train-only scaling, training and evaluation.
- results/: audit, split IDs/counts/dates/composition, model/scaler, predictions, pooled/group metrics, validation result and generated summary.
- predict.py: saved baseline inference for one eligible shot. Omitted factors include body part, keeper/defender position and shooter identity.
- test_pipeline.py and validate.py: geometry, rank AUC versus independent pairwise calculation, scope boundaries, synthetic cleaning, gzip input, duplicate/hash failures, source coverage/counts, match separation, training transform, prediction reconstruction and pilot regression.

## Reporting limits and source

Present pipeline/split and goal-angle diagrams, actual coverage, metrics, risks and Week 4 plan. Pooling years/competitions creates selection bias and distribution shifts. Open data overrepresents selected teams, players, leagues and finals. Do not claim generalization to all European football or other populations. Mean prediction and observed rates alone do not establish calibration. Chronological splits have different competition compositions.

The presentation still needs the student's real hours, gap explanation, feedback, last week's risks/issues and confirmed changes. Do not fabricate progress records.

Source: Hudl/StatsBomb Open Data, https://github.com/hudl/open-data, pinned revision in data/snapshot.json. Follow source README and LICENSE.pdf attribution/use requirements. Raw event JSON is not uploaded to this repository.
