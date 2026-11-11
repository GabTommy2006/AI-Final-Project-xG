# Week 4 — Model Development & Evaluation

This stage extends Week 3's non-penalty pre-shot xG baseline. It retains the same 2,411 matches, 59,519 shots and chronological whole-match split. Scope and pinned source revision are inherited from `week3/data/COVERAGE.md`. No new raw download is needed when the committed Week 3 prepared CSV is available.

## Run on Windows

From the repository root, use Python 3.11 (the verified environment):

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install -r week4/requirements.txt
.\.venv311\Scripts\python.exe week4/train.py
.\.venv311\Scripts\python.exe week4/validate.py
.\.venv311\Scripts\python.exe week4/report.py
```

If `.venv311` already exists, skip its creation. Training overwrites Week 4 results; it does not change Week 3 data or results. On Linux/macOS use `python3.11 -m venv .venv311` and `.venv311/bin/python`. Seeds, versions and source hashes are saved in `results/experiment_plan.json`; numerical results can vary slightly across platforms. Script runtime is not student working hours.

To check the committed results without retraining, install dependencies, then run `week4/validate.py`. To regenerate Week 3 from raw events, follow `week3/README.md` first.

## What is compared?

- Frozen Week 3 Logistic Regression: distance and viewing angle.
- Contextual Logistic Regression: the same geometry plus body part, shot type, play pattern and technique; C = 0.1, 1, 10.
- Random Forest with geometry only, and with context: 200 trees; depth 6, 10 or unlimited; minimum leaf size 20 or 50.

There are 15 candidate configurations. Preprocessing is fitted on training data only. Logistic Regression minimizes regularized binary negative log likelihood. Forests use Gini impurity for splits and average tree probabilities. No CNN/LSTM is needed for this tabular experiment. Provider xG, outcome, shot end location and identities are excluded from model inputs.

Selection uses validation Log Loss, with Brier Score and model ID as tie breakers. The baseline can win. `selection.json` is written before candidate test evaluation, and the selected model is not refitted on train plus validation. ROC-AUC measures ranking; Log Loss and Brier evaluate probability predictions. Accuracy/F1 at 0.5 are supplementary.

The Week 3 test was already inspected: these are retrospective test comparisons, not an untouched final holdout. Do not switch the selected model because another configuration happens to look better on test.

## Current result

Validation selects **contextual Logistic Regression, C=10**. Its test Log Loss/Brier/ROC-AUC are **0.287017 / 0.082283 / 0.775094**, versus **0.303657 / 0.086991 / 0.731592** for Week 3. Contextual Random Forest achieves **0.287425 / 0.082469 / 0.772797** on test. These are descriptive results on this fixed dataset, without a statistical significance claim.

Read `results/SUMMARY.md` first, then `comparison.csv`, `validation_search.json`, calibration and generalization-gap plots, and `group_errors.csv`. Small groups and sparse high-xG bins are uncertain; competition coverage is unbalanced.

## Predict one shot

```powershell
.\.venv311\Scripts\python.exe week4/predict.py --x 108 --y 40 --body-part "Right Foot" --shot-type "Open Play" --play-pattern "Regular Play" --technique "Normal"
```

Expected xG: approximately **0.288476** (28.85%). Coordinates use StatsBomb's 120-by-80 convention, attacking the goal at (120,40). Distance is in StatsBomb coordinate units; angle is in radians. Use the actual observed shot context and exact category spelling. Penalties and out-of-range coordinates are rejected. Unseen category values produce a notice and are ignored by the encoder. Only load trusted joblib artifacts.

## Code and teacher requirements

| Requirement | Implementation/evidence |
|---|---|
| Model architecture | `core.py`, `results/selected_explanation.json`, SUMMARY |
| Training, hyperparameters and objectives | `train.py`, `experiment_plan.json`, `validation_search.json` |
| Evaluation metrics | `core.py`, `comparison.csv`, `metrics.json` |
| Baseline versus improvement | Frozen baseline, geometry-only forest, contextual models and C=1 matched control |
| Error analysis and improvement plan | Calibration/gap plots, group errors and SUMMARY |
| Verified trained model | `selected_model.joblib`, `validate.py` and seven meaningful tests |

Weekly WBS owner: Phuc Hung (one contributor). Planned Week 4 budget: 14 hours; actual hours and teacher feedback have not been supplied. Record them honestly before preparing the progress slides. The source document's “Third Week” title is treated as the teacher's confirmed typo for Week 4.

Week 5 remains integration and reporting: build the input/output demo around the selected model, validate inputs and prepare final documentation. Further tuning or calibration requires a specified validation protocol; the reported test scores must not become tuning targets.
