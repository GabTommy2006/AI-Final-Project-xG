# Week 5 — integration and reporting

The Streamlit app uses the **committed Week 4 contextual Logistic Regression** artifact. It supports both numeric coordinates and direct pitch selection, explains xG, exports a JSON estimate, and exposes the recorded model comparisons. It performs inference, not training.

## Run locally (PowerShell)

From the repository root, with Python 3.11 installed:

```powershell
py -3.11 -m venv .venv5
.\.venv5\Scripts\python.exe -m pip install -r week5/requirements.txt
.\.venv5\Scripts\python.exe -m streamlit run week5/app.py
```

Open the localhost URL printed by Streamlit. Stop with Ctrl+C. No paid API key or raw-data download is needed for the saved-model demo. Keep `week3/results/model.json` and the committed `week4/results/` artifacts in place.

Vietnamese quick start: chọn điểm bằng chuột trên sân hoặc nhập **Position x/y**. Chọn bốn thông số ngữ cảnh; kết quả tự cập nhật. Nút **Reset example** khôi phục ví dụ `(108,40)` và cho kết quả **28.85%**, tức khoảng **0.288 xG**. Tab **Model evidence** đối chiếu kết quả tuần 4; **Project guide** giải thích cách mô hình hoạt động.

## Test

```powershell
.\.venv5\Scripts\python.exe -m unittest week5.test_service week5.test_app -v
.\.venv5\Scripts\python.exe -m unittest discover -s week4 -p test_week4.py -v
```

The inference tests compare outputs against historical saved predictions and check geometry, invalid inputs, provenance and metric records. AppTest checks error recovery, reset, categorical consistency and navigation. Browser QA is additionally required for pointer/keyboard pitch interaction and responsive layout.

## Deploy on Streamlit Community Cloud

1. Push this branch to the existing GitHub repository.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app from repository `GabTommy2006/AI-Final-Project-xG`.
3. Select branch `codex/week-5-streamlit`, entrypoint `week5/app.py`, and **Python 3.11** in Advanced settings.
4. The app-directory `week5/requirements.txt` is selected before root requirements. Its includes retain the model's numerical-library versions. No secrets are required.
5. Deploy and check the default example, click/numeric synchronization, and Model evidence page. Record the actual live URL after verification; no live URL is implied by this document.

Private-repository deployment may require the owner to sign in and approve Streamlit's GitHub access. Do not make the repository public merely to bypass authentication. Review app visibility before sharing with the tutor.

Official deployment references: [dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), [deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Files and data flow

- `app.py`: native Streamlit controls, inference display, evaluation and guide.
- `pitch.py`: accessible SVG geometry with Components v2; pointer selection and arrow keys send coordinates to Python.
- `service.py`: validates input, derives distance/angle, loads the trusted saved model once, and returns JSON-safe probabilities.
- `.streamlit/config.toml` and `static/`: theme and self-hosted Manrope, distributed under its included SIL Open Font License.
- `test_service.py`, `test_app.py`: inference and UI integration checks.
- `REPORT.md`: final integration summary, measured results and outstanding academic requirements.

The same Week 4 preprocessing is used for inference. Do not load joblib/pickle files supplied by app visitors. No visitor uploads or project-side input database are implemented. Hosting providers may still maintain ordinary operational logs.
