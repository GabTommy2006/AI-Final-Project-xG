# Final integration report

## Objective and demonstrated pipeline

Estimate the probability that an attempted **non-penalty** shot becomes a goal, conditional on location and recorded context. This supports comparing chance quality; it does not guarantee outcomes, predict a full match score, or assess finishing skill by itself.

**StatsBomb shot events → prepared training rows → train-only preprocessing → fitted Logistic Regression → xG probability → Streamlit interface / JSON export.**

The app loads the committed Week 4 selected model without refitting. Numeric entry, pitch click/drag and arrow-key entry share the same inference service. Distance and goal opening angle are calculated from StatsBomb coordinates (120 × 80 units, not metres), with the attacking goal at (120,40). Body part, shot type, play pattern and technique provide contextual features.

## Data and evaluation

The fixed public snapshot includes 2,411 eligible senior men's matches from selected European competitions after 2000 and FIFA World Cup: 59,519 non-penalty shots and 6,074 goals. It is selective public coverage, not complete competition seasons. Training / validation / test contain 1,446 / 482 / 483 matches and 35,559 / 11,909 / 12,051 shots. Matches do not overlap across splits.

Selection uses validation Log Loss. Context Logistic Regression C=10 is the saved winner. Exact values are traceable to `week4/results/metrics.json` and `selection.json`.

| Model / split | Log Loss ↓ | Brier ↓ | ROC-AUC ↑ |
|---|---:|---:|---:|
| Selected contextual logistic / validation | 0.272375 | 0.078371 | 0.790266 |
| Selected contextual logistic / test | 0.287017 | 0.082283 | 0.775094 |
| Week 3 geometry logistic / test | 0.303657 | 0.086991 | 0.731592 |

Test performance improved descriptively on all three measures relative to Week 3. Because this test set was already inspected in Week 3, it is a **retrospective comparison**, not a fresh untouched evaluation. No statistical significance or generalisation to all football is claimed. ROC-AUC measures ranking, while Log Loss and Brier evaluate probability quality; none alone proves perfect calibration.

Default demo: (108,40), Right Foot, Open Play, Regular Play, Normal → xG ≈ 0.288477. About 29 goals per 100 comparable shots is an interpretation of the estimated probability, not a measured subgroup success rate or a guarantee.

## Limitations and risks

- Selective competition/season coverage can create sampling and domain bias; the model is not validated for women's football or penalties.
- No defender/goalkeeper geometry, tracking, video, or player identity; identical listed inputs receive the same probability.
- Rare category combinations and extreme locations may extrapolate poorly even if valid coordinates.
- Goal outcome, provider xG and shot end location are excluded as predictors to prevent direct target leakage.
- Scikit-learn artifact compatibility depends on the pinned library versions. Only repository-trusted joblib is loaded.
- The teacher's sheet says **“Full deep learning pipeline demonstration.”** Logistic Regression and Random Forest are **not deep learning**. This deliverable demonstrates an end-to-end machine learning pipeline; if deep learning is mandatory, tutor agreement or a separately trained/evaluated neural model remains necessary. Do not describe this app as satisfying that wording without clarification.

## Future work

Evaluate on a genuinely new time/competition holdout; examine calibration and uncertainty using an evaluation design fixed before seeing its outcomes; investigate freeze-frame context when coverage permits; compare a neural tabular baseline only if academically required and under the same leakage controls; add batch inference and additional usability validation.

## Delivery and responsibility

Owner: Phuc Hung (solo). Week 3: baseline pipeline. Week 4: model improvement/comparison. Week 5: integration and reporting. This branch adds the app, inference validation, tests and deployment documentation. Earlier training results are preserved.

Actual hours, planned-versus-actual gap, tutor feedback and any changes after presentation: **not provided; student must update with real records**. The final presentation and tutor submission are separate artefacts; this report does not assert that they have been submitted.

## Reproducibility and final review

Use the Python 3.11 commands in `week5/README.md`. The saved-model demo requires no new data download or API key. Full training/data provenance and prior experiment details remain in Week 3 and Week 4 documentation. Review code, documented scope, metric records, tests, model artifact and deployment settings together. Confirm the live URL through a real deployment before reporting deployment complete.
