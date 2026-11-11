# Week 4 — Model Development & Evaluation

Actual experiment results on the unchanged Week 3 non-penalty dataset. No CNN/LSTM was trained.

## Data and protocol

2,411 matches; 59,519 eligible shots; 6,074 goals. Same whole-match chronological split: train 35,559 shots, validation 11,909, test 12,051. No resampling or class weighting.

Pre-shot model inputs: distance and angle; contextual variants additionally use body part, shot type, play pattern and technique. Outcome is target only. Provider xG, end location, future events and match/player identities are not inputs.

Input CSV SHA-256: `02e4cbe6267022557de152fba687091c58372348254ac8572acb1531ea90687a`.

## Architecture, training and hyperparameters

Frozen baseline: Week 3 standardized two-feature logistic, unpenalized intercept and fixed L2=1. Library geometry logistic C=1 reproduces its predictions; see baseline_parity.json.

Context logistic: train-fitted numeric StandardScaler plus one-hot categorical encoding; unknown categories are ignored and missing values have an explicit marker. L2 logistic uses C in {0.1, 1, 10}; lbfgs, max_iter=2000, tol=1e-10. It optimizes regularized binary negative log likelihood; C is inverse regularization.

Random Forest: geometry-only and context variants. 200 bootstrap trees, sqrt features per split, Gini split criterion, depth in {6, 10, unlimited}, min_samples_leaf in {20, 50}, random_state=2026. Gini measures node impurity; it is not the logistic training objective. Forest probability averages class probabilities across trees.

Fifteen predeclared candidate configurations plus the frozen baseline compete on validation Log Loss; Brier then ID break ties. The plan is written before fitting, validation search is saved, and selection is locked before any new candidate test scores are computed. The selected model stays fitted on train only, preserving comparability. No post-hoc calibration model was fitted.

## Selected model

Selected: **logistic_context_C10**, parameters `{'C': 10.0}`.

Selection was made by validation performance, not by which model looks best on test. A contextual C=1 logistic is also reported as a matched-regularization control for the feature comparison.

## Validation and reported test metrics

- validation, constant_train_rate: Log Loss 0.326209; Brier 0.090410; ROC-AUC 0.500000.
- validation, week3_logistic_geometry: Log Loss 0.289832; Brier 0.082933; ROC-AUC 0.746072.
- validation, logistic_context_C10: Log Loss 0.272375; Brier 0.078371; ROC-AUC 0.790266.
- validation, forest_geometry_depth6_leaf20: Log Loss 0.287666; Brier 0.082658; ROC-AUC 0.748002.
- validation, forest_context_depthNone_leaf20: Log Loss 0.273626; Brier 0.078435; ROC-AUC 0.786098.
- validation, logistic_context_C1: Log Loss 0.272495; Brier 0.078369; ROC-AUC 0.789810.
- test, constant_train_rate: Log Loss 0.338484; Brier 0.094893; ROC-AUC 0.500000.
- test, week3_logistic_geometry: Log Loss 0.303657; Brier 0.086991; ROC-AUC 0.731592.
- test, logistic_context_C10: Log Loss 0.287017; Brier 0.082283; ROC-AUC 0.775094.
- test, forest_geometry_depth6_leaf20: Log Loss 0.301182; Brier 0.086670; ROC-AUC 0.736357.
- test, forest_context_depthNone_leaf20: Log Loss 0.287425; Brier 0.082469; ROC-AUC 0.772797.
- test, logistic_context_C1: Log Loss 0.286895; Brier 0.082249; ROC-AUC 0.775387.

Selected-minus-baseline validation Log Loss: -0.017457; Brier: -0.004562. Negative loss differences are improvements on this split.

Selected-minus-baseline test Log Loss: -0.016640; Brier: -0.004708. Negative loss differences are improvements on this split.

Accuracy and F1 are supplementary at fixed threshold 0.5 (see comparison.csv). No threshold was optimized; these are not the primary xG criteria. Log Loss clipping is 1e-12, matching Week 3. AUC is ranking, not accuracy; probability losses mix discrimination and calibration.

## Error analysis and observed challenges

- week3_logistic_geometry: validation-minus-train Log Loss gap +0.001442.
- logistic_context_C10: validation-minus-train Log Loss gap +0.002621.
- forest_geometry_depth6_leaf20: validation-minus-train Log Loss gap +0.006466.
- forest_context_depthNone_leaf20: validation-minus-train Log Loss gap +0.021453.
- validation selected model: mean xG 10.01%, observed goals 10.05%; 193 shots in bins at xG >= 0.5. Similar global means do not prove calibration.
- test selected model: mean xG 11.27%, observed goals 10.61%; 279 shots in bins at xG >= 0.5. Similar global means do not prove calibration.

Largest selected-minus-baseline validation Log Loss differences among groups with >=100 shots and >=10 goals:
- distance_band=20-<30: n=4189, goals=158, delta=-0.002733.
- distance_band=30+: n=1263, goals=18, delta=-0.005415.
- play_pattern=From Throw In: n=2109, goals=191, delta=-0.006606.
- body_part=Left Foot: n=3833, goals=375, delta=-0.010071.
- play_pattern=From Free Kick: n=2444, goals=257, delta=-0.011818.

These are overlapping descriptive groups, not independent hypothesis tests. Small groups are flagged in group_errors.csv. No significance or universal superiority claim is made.

Coverage is unbalanced and chronology changes competition composition. Both World Cups and Euros are only in test. There are no new missing-label or coordinate imputations; Week 3 cleaning is reused. Missing/unseen categorical values are audited. The contextual forest has a larger train–validation gap than the simple baseline; inspect the actual values rather than equating complexity with quality.

## Improvement plan and Week 5

Keep the validation-selected model for the demo. In Week 5, integrate input validation and contextual inputs, probability display and shot visualization; provide run instructions and final reporting. Consider interaction features or calibration only under a newly specified train/validation protocol; do not use reported test scores to select another candidate.

The Week 3 test was already inspected before this experiment. These test scores are transparent retrospective reporting, not an untouched final holdout. Independent data/protocol is required before an untouched-evaluation claim. No independent new dataset was collected in Week 4.

## Evidence and progress

See experiment_plan.json, validation_search.json, selection.json, comparison.csv, predictions.csv, error_analysis.json, preprocessing_audit.json, selected_model.joblib and validation.json. Plots are reproducibly generated by report.py.

Owner: Phuc Hung, sole contributor. Planned Week 4 budget: 14 hours from the prior WBS. Actual student hours: not supplied; gap cannot yet be calculated. runtime.json measures script execution time only, not student effort. Tutor feedback and personal issue/time logs must be recorded honestly.

Data source: StatsBomb Open Data (Hudl), pinned source manifest inherited from Week 3. This is a student model, not provider xG. Raw events and Python environments remain excluded from Git.
