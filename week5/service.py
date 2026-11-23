"""Validated inference using the unchanged Week 4 artifact and preprocessing."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import joblib

from week4.core import CATEGORICAL, NUMERIC, bundle_probability, frozen_probability

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "week4" / "results"


@dataclass(frozen=True)
class Shot:
    x: float = 108.0
    y: float = 40.0
    body_part: str = "Right Foot"
    shot_type: str = "Open Play"
    play_pattern: str = "Regular Play"
    technique: str = "Normal"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


@lru_cache(maxsize=1)
def artifacts() -> dict[str, Any]:
    """Load only the trusted model shipped with this repository, never an upload."""
    path = RESULTS / "selected_model.joblib"
    bundle = joblib.load(path)
    selection = read_json(RESULTS / "selection.json")
    if bundle["selected_id"] != selection["selected_id"]:
        raise ValueError("The saved model and selection record do not match.")
    if bundle["numeric_features"] != NUMERIC or bundle["categorical_features"] != CATEGORICAL:
        raise ValueError("This app expects the six-field Week 4 contextual model.")
    if bundle["input_sha256"] != selection["baseline_input_sha256"]:
        raise ValueError("Model input provenance does not match the selection record.")
    encoder = bundle["model"].named_steps["preprocess"].named_transformers_["context"]
    categories = {field: tuple(str(value) for value in values)
                  for field, values in zip(CATEGORICAL, encoder.categories_)}
    return {
        "bundle": bundle,
        "selection": selection,
        "categories": categories,
        "metrics": read_json(RESULTS / "metrics.json"),
        "baseline": read_json(ROOT / "week3" / "results" / "model.json"),
        "model_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def features(shot: Shot, categories: dict[str, tuple[str, ...]] | None = None) -> dict:
    for label, value, maximum in [("x", shot.x, 120), ("y", shot.y, 80)]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"Position {label} must be a finite number.")
        if not 0 <= value <= maximum:
            raise ValueError(f"Position {label} must be between 0 and {maximum}.")
    if shot.x == 120 and shot.y in (36, 44):
        raise ValueError("The viewing angle is undefined exactly at a goalpost. Move the shot slightly.")
    if isinstance(shot.shot_type, str) and shot.shot_type.strip().casefold() == "penalty":
        raise ValueError("Penalties are outside this model's scope. Choose a non-penalty shot.")
    known = categories if categories is not None else artifacts()["categories"]
    for field in CATEGORICAL:
        value = getattr(shot, field)
        if not isinstance(value, str) or value not in known[field]:
            raise ValueError(f"Choose a known {field.replace('_', ' ')} from the available options.")
    # Restrict obvious physical contradictions, not rare but valid training contexts.
    if shot.technique == "Diving Header" and shot.body_part != "Head":
        raise ValueError("Diving Header needs Head as the body part.")
    if shot.body_part == "Head" and shot.technique not in ("Normal", "Diving Header"):
        raise ValueError("For a header, choose Normal or Diving Header technique.")
    if shot.shot_type == "Corner" and shot.play_pattern != "From Corner":
        raise ValueError("A direct corner shot needs From Corner as the play pattern.")
    if shot.shot_type == "Free Kick" and shot.play_pattern != "From Free Kick":
        raise ValueError("A direct free kick needs From Free Kick as the play pattern.")
    return {
        "distance_sb_units": math.hypot(120 - shot.x, shot.y - 40),
        "angle_rad": math.atan2(8 * (120 - shot.x), (120 - shot.x) ** 2 + (shot.y - 40) ** 2 - 16),
        **{field: getattr(shot, field) for field in CATEGORICAL},
    }


def estimate(shot: Shot) -> dict:
    data = artifacts()
    row = features(shot, data["categories"])
    probability = float(bundle_probability(data["bundle"], [row])[0])
    baseline = float(frozen_probability(data["baseline"], [row])[0])
    if not (math.isfinite(probability) and 0 <= probability <= 1):
        raise ValueError("The model did not return a valid probability.")
    return {
        "shot": asdict(shot),
        "features": row,
        "xg": probability,
        "baseline_xg": baseline,
        "model": data["bundle"]["selected_id"],
        "model_sha256": data["model_sha256"],
        "coordinate_system": "StatsBomb 120x80; attacking goal at (120,40); not metres",
        "interpretation": "Probability of a goal for this attempted non-penalty shot, not a guarantee.",
    }


def evaluation_rows(split: str = "validation") -> list[dict]:
    if split not in ("train", "validation", "test"):
        raise ValueError("Unknown evaluation split.")
    data = artifacts()
    names = {
        "constant_train_rate": "Constant goal rate",
        "week3_logistic_geometry": "Week 3 · geometry logistic",
        "logistic_context_C10": "Week 4 · context logistic C=10",
        "forest_geometry_depth6_leaf20": "Geometry random forest",
        "forest_context_depthNone_leaf20": "Context random forest",
        "logistic_context_C1": "Context logistic C=1 · control",
    }
    return [{"Model": names.get(mid, mid), "Log Loss": scores["log_loss"],
             "Brier": scores["brier_score"], "ROC-AUC": scores["roc_auc"], "id": mid}
            for mid, scores in data["metrics"][split].items()]
