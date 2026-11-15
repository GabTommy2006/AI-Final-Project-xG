# Deployment verification — 16 November 2026

Live URL: https://phuc-hung-xg-studio.streamlit.app/

- Source: `codex/week-5-streamlit`, entrypoint `week5/app.py`, Python 3.11.
- App sharing: **public and searchable**, explicitly approved by the owner. An independent browser session without Streamlit sign-in loaded the app successfully. Repository visibility was not changed.
- Default shot: (108,40), Right Foot, Open Play, Regular Play, Normal. Hosted JSON export returned **0.28847610029653536**, model `logistic_context_C10`, matching local inference within floating-point tolerance.
- Numeric x=100 produced **9.29%**; pitch keyboard adjustment to x=99 synchronised the numeric field and produced **8.09%**. Local browser testing additionally verified pointer pitch selection, reset and goalpost error recovery.
- Hosted Model evidence loaded the recorded comparisons. Selecting test displayed the explicit retrospective-evaluation caveat.
- The hosted **Download this estimate** button produced a valid JSON file containing the selected shot, model ID, features, probability and provenance hash.
- Seven Week 5 inference/UI tests passed after pinning PyArrow 24.0.0. Seven Week 4 regression tests passed during integration. Desktop and mobile captures were reviewed; Impeccable reviewer disposition was **ship** after header/contrast corrections, with the documented capture scope.
- Self-hosted Manrope and responsive native controls were checked locally; mobile viewport 390×844 had no horizontal document overflow.

This verifies app integration and deployment, not all academic deliverables. Actual work-hour records, final presentation/submission, and clarification of the teacher's “deep learning” wording remain separate obligations. The integrated model is Logistic Regression, not a neural network. Test results remain retrospective because Week 3 had already inspected the same test split.
