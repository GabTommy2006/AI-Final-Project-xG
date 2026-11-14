"""Week 5 integration: streamlit run week5/app.py (from repository root)."""
from pathlib import Path
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from week5.service import Shot, artifacts, estimate, evaluation_rows
from week5.pitch import pitch

st.set_page_config(page_title="xG studio · Shot explorer", page_icon="⚽", layout="wide")
st.html('''<style>
  .stMainBlockContainer{max-width:1240px;padding-top:5rem;padding-bottom:3rem}
  h1{font-size:2.6rem!important;letter-spacing:-.03em!important;font-weight:700!important}
  h2{letter-spacing:-.02em!important}
  .brand{display:flex;justify-content:space-between;align-items:center;background:#123D34;color:#F5F5EF;padding:1rem 1.25rem;margin-bottom:1rem;border-radius:12px}
  .brand strong{font-size:1.4rem;letter-spacing:-.03em}.brand span{font-size:.85rem;color:#D8E6DB}
  [data-testid="stCaptionContainer"]{opacity:1!important;color:#466153!important}
  .result{display:flex;align-items:baseline;gap:1rem;margin-top:1rem;border-bottom:1px solid #BECBBF;padding-bottom:1rem}
  .result strong{font-size:3.4rem;font-weight:650;letter-spacing:-.035em;font-variant-numeric:tabular-nums}
  .result span{font-size:1rem}.stNumberInput input{font-variant-numeric:tabular-nums}
  ::selection{background:#D6F285;color:#123D34}input{caret-color:#123D34}
  a{text-underline-offset:3px}*:focus-visible{outline-color:#618522!important}
  @media(max-width:640px){.stMainBlockContainer{padding:4.5rem 1rem 1rem}h1{font-size:2rem!important}.brand span{max-width:135px;text-align:right}}
  @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>''')
st.html('<div class="brand"><strong>xG studio</strong><span>A closer look at chance quality</span></div>')
page = st.segmented_control("Navigation", ["Shot explorer", "Model evidence", "Project guide"],
                            default="Shot explorer", label_visibility="collapsed") or "Shot explorer"

try:
    data = artifacts()
except Exception:
    st.error("The saved model could not be loaded. Restore the committed Week 4 artifacts and install week5/requirements.txt.")
    st.stop()


def reset():
    for key, value in vars(Shot()).items():
        st.session_state[key] = value


def selected_position():
    result = st.session_state.get("pitch", {})
    value = result.get("position") if hasattr(result, "get") else getattr(result, "position", None)
    if value:
        st.session_state.x = float(value["x"])
        st.session_state.y = float(value["y"])


def context_changed():
    if st.session_state.shot_type == "Corner":
        st.session_state.play_pattern = "From Corner"
    elif st.session_state.shot_type == "Free Kick":
        st.session_state.play_pattern = "From Free Kick"
    if st.session_state.body_part == "Head" and st.session_state.technique not in ("Normal", "Diving Header"):
        st.session_state.technique = "Normal"
    if st.session_state.body_part != "Head" and st.session_state.technique == "Diving Header":
        st.session_state.technique = "Normal"


for key, value in vars(Shot()).items():
    st.session_state.setdefault(key, value)

if page == "Shot explorer":
    st.title("Understand the shot.")
    st.write("Choose a position and shot context to estimate the probability of a goal.")
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.subheader("Choose your position")
        pitch(key="pitch", data={"x": st.session_state.x, "y": st.session_state.y},
              on_position_change=selected_position)
        st.caption("Click or drag on the pitch. Keyboard: focus the pitch and use arrow keys. Goal is on the right.")
    with right:
        st.subheader("Describe the shot")
        a, b = st.columns(2)
        a.number_input("Position x", min_value=0.0, max_value=120.0, step=1.0, key="x")
        b.number_input("Position y", min_value=0.0, max_value=80.0, step=1.0, key="y")
        st.caption("StatsBomb coordinates: 120 × 80 units, not metres.")
        cats = data["categories"]
        st.selectbox("Body part", cats["body_part"], key="body_part", on_change=context_changed)
        st.selectbox("Shot type", cats["shot_type"], key="shot_type", on_change=context_changed)
        st.selectbox("Play pattern", cats["play_pattern"], key="play_pattern")
        techniques = [v for v in cats["technique"] if (v in ("Normal", "Diving Header") if st.session_state.body_part == "Head" else v != "Diving Header")]
        st.selectbox("Technique", techniques, key="technique")
        st.button("Reset example", on_click=reset, width="stretch")
    with left:
        try:
            result = estimate(Shot(**{k: st.session_state[k] for k in vars(Shot())}))
        except ValueError as exc:
            st.error(str(exc))
        else:
            p = result["xg"]
            st.html(f'<div class="result"><strong>{p:.2%}</strong><span>expected goals · {p:.3f} xG</span></div>')
            st.write(f"Roughly {p * 100:.0f} goals per 100 comparable shots, on average. An individual shot can still score or miss.")
            st.caption("Updates automatically. Non-penalty shots only · Week 4 contextual Logistic Regression.")
            if st.checkbox("Compare with the Week 3 geometry baseline"):
                st.write(f'Week 3: **{result["baseline_xg"]:.1%}** · Week 4: **{p:.1%}**')
                st.caption("Different fitted models; this difference does not isolate a causal effect of any feature.")
            with st.expander("See the model inputs"):
                st.write(f'Distance to goal centre: {result["features"]["distance_sb_units"]:.2f} units. '
                         f'Goal opening angle: {math.degrees(result["features"]["angle_rad"]):.2f}°.')
                st.json(result["features"])
            st.download_button("Download this estimate", json.dumps(result, indent=2),
                               file_name="xg-estimate.json", mime="application/json")
    st.divider()
    st.caption("Research prototype. Estimates apply to the public-data training scope; unusual locations or contexts may be unreliable.")

elif page == "Model evidence":
    st.title("Evidence behind the estimate.")
    st.write("Recorded Week 4 experiments on the fixed Week 3 match-level split. The app does not retrain the model.")
    split = st.radio("Evaluation split", ["validation", "test"], horizontal=True)
    if split == "test":
        st.warning("The test set was already inspected in Week 3. Treat these as retrospective comparisons, not a new untouched final evaluation.")
    st.write("**Selected model:** contextual Logistic Regression, C = 10; chosen by lowest validation Log Loss.")
    rows = evaluation_rows(split)
    st.dataframe([{k: v for k, v in row.items() if k != "id"} for row in rows],
                 hide_index=True, width="stretch", column_config={k: st.column_config.NumberColumn(format="%.4f") for k in ["Log Loss", "Brier", "ROC-AUC"]})
    st.subheader("Read the metrics")
    st.markdown("- **Log Loss ↓:** penalises incorrect probabilities, especially confident mistakes. Primary selection metric.\n- **Brier Score ↓:** mean squared error between predicted probability and the goal label.\n- **ROC-AUC ↑:** how well goals rank above non-goals; it does not measure probability calibration.")
    st.subheader("One shared data split")
    st.dataframe({"Split": ["Training", "Validation", "Test"], "Matches": [1446, 482, 483], "Shots": [35559,11909,12051]}, hide_index=True, width="stretch")
    st.write("59,519 non-penalty shots · 6,074 goals · 2,411 matches. Splitting by match keeps shots from the same match together.")
    st.caption("Random Forest was compared in Week 4. More complex models did not automatically produce better validation probabilities.")

else:
    st.title("From event data to xG.")
    st.write("This project estimates P(goal | shot position, shot context) for an attempted non-penalty shot.")
    st.subheader("Data → features → model → probability")
    st.markdown("1. **Data:** StatsBomb Open Data shot events, with goal / non-goal labels.\n2. **Features:** distance and goal opening angle from x/y, plus body part, shot type, play pattern and technique.\n3. **Model:** the saved Week 4 preprocessing pipeline and Logistic Regression. Scaling and categorical encoding were fitted on training data.\n4. **Output:** a probability between 0 and 1. Summing shot probabilities gives an expected goal total; it is not a guaranteed score.")
    st.subheader("Scope and limitations")
    st.write("Senior men's football: selected European competitions after 2000 and FIFA World Cup matches available in the fixed public-data snapshot. Coverage is selective, not every match or season.")
    st.write("Penalties and shoot-outs are excluded. Player identity, shot outcome, provider xG and end location are not model inputs. This version does not use video, tracking, goalkeeper position or defender positions.")
    st.write("Logistic Regression and Random Forest are machine learning models, not deep learning. This demo does not implement CNNs or LSTMs. The teacher's deep-learning wording should be clarified if it is a mandatory requirement.")
    st.subheader("Reproduce the demo")
    st.code("python -m pip install -r week5/requirements.txt\npython -m streamlit run week5/app.py", language="bash")
    st.markdown("[Project source](https://github.com/GabTommy2006/AI-Final-Project-xG/tree/codex/week-5-streamlit) · [StatsBomb Open Data](https://github.com/statsbomb/open-data)")
    st.caption("Data attribution: StatsBomb. Academic prototype by Phuc Hung. No shot inputs are written to a project database by this app.")
