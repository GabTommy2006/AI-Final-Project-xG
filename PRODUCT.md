# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Streamlit and Python, explicitly requested by the user. Reuse the committed Week 4 scikit-learn model; do not retrain during app use.

## Users

Phuc Hung, the sole student contributor, presenting the five-week xG project to a tutor. Visitors explore how a shot's position and observed context affect its estimated scoring probability.

## Product Purpose

Demonstrate Data → Model → Output for attempted non-penalty shots. A successful visit lets someone choose a position and shot context, see the saved model's xG, understand its interpretation, and inspect the recorded evaluation and limitations.

## Operating Context

English interface, consistent with the English reporting slides. Both a numeric input form and direct pitch positioning were confirmed by the user on 14 November 2026. Desktop classroom demonstration and mobile browser use. Local run and Streamlit Community Cloud deployment are in scope; cloud account access remains to be verified.

## Capabilities and Constraints

Use geometry plus body part, shot type, play pattern and technique. Keep penalties excluded and validate input combinations. Coordinates use StatsBomb's 120 × 80 scale, attacking (120, 40), not metres. The artifact is logistic_context_C10, selected on validation. Week 3 test was already inspected. This is traditional machine learning, not deep learning; teacher wording remains an open clarification. Preserve existing Week 2–4 files and the user's uncommitted rerun results.

## Brand Commitments

User requested attractive fonts, modern colors and use of Impeccable. No fixed palette or existing app interface was supplied.

## Evidence on Hand

Week 4 commit e2feaf0; selected_model.joblib, metrics.json, selection.json, preprocessing audit and saved reports. Pinned StatsBomb Open Data: 2,411 matches, 59,519 non-penalty shots and 6,074 goals. Do not invent deployment status, teacher feedback, working hours or stronger validation claims.

## Product Principles

Make the shot and its probability the primary task. Keep labels and uncertainty understandable. Use the same saved model and training preprocessing for every prediction. Keep evaluation clearly separate from individual-shot prediction.
