"""Integration checks against the committed predictions and actual saved artifact."""
import csv
import json
import math
from pathlib import Path
import unittest

import numpy as np

from week5.service import Shot, artifacts, estimate, evaluation_rows, features, ROOT
from week4.core import bundle_probability


class InferenceTests(unittest.TestCase):
    def test_recorded_demo_and_geometry(self):
        result = estimate(Shot())
        self.assertAlmostEqual(result["xg"], .288476, places=6)
        self.assertEqual(result["features"]["distance_sb_units"], 12)
        self.assertAlmostEqual(result["features"]["angle_rad"], 2 * math.atan(4 / 12))
        self.assertEqual(result["model"], "logistic_context_C10")
        self.assertAlmostEqual(result["baseline_xg"], .157879, places=6)
        json.dumps(result, allow_nan=False)

    def test_geometry_matches_week3_prepared_shots(self):
        with (ROOT / "week4/results/predictions.csv").open(encoding="utf-8-sig") as f:
            saved = {r["event_id"]: float(r["logistic_context_C10"]) for r in csv.DictReader(f)}
        compared = 0
        with (ROOT / "week3/results/predictions.csv").open(encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.DictReader(f)):
                if i % 593 == 0:
                    shot = Shot(float(row["x"]), float(row["y"]), row["body_part"],
                                row["shot_type"], row["play_pattern"], row["technique"])
                    try:
                        result = estimate(shot)
                    except ValueError:
                        # App refuses physically contradictory historical annotations.
                        continue
                    self.assertAlmostEqual(result["features"]["distance_sb_units"],float(row["distance_sb_units"]))
                    self.assertAlmostEqual(result["features"]["angle_rad"],float(row["angle_rad"]))
                    self.assertAlmostEqual(result["xg"],saved[row["event_id"]],places=12)
                    compared += 1
        self.assertGreater(compared, 80)

    def test_invalid_input_and_inconsistent_context(self):
        invalid = [Shot(x=float("nan")), Shot(y=float("inf")), Shot(x=-1), Shot(y=81),
                   Shot(x=120,y=36), Shot(x=True), Shot(shot_type="Penalty"),
                   Shot(body_part="Unknown"), Shot(shot_type=None), Shot(technique="Diving Header"),
                   Shot(body_part="Head",technique="Backheel"), Shot(shot_type="Corner"),
                   Shot(shot_type="Free Kick")]
        for shot in invalid:
            with self.subTest(shot=shot), self.assertRaises(ValueError):
                estimate(shot)

    def test_valid_contexts_and_probabilities(self):
        examples = [Shot(body_part="Head"), Shot(body_part="Head",technique="Diving Header"),
                    Shot(shot_type="Free Kick",play_pattern="From Free Kick"),
                    Shot(x=120,y=40),Shot(x=0,y=0),
                    Shot(shot_type="Corner",play_pattern="From Corner")]
        for shot in examples:
            result = estimate(shot)
            self.assertTrue(0 <= result["xg"] <= 1)

    def test_evaluation_and_artifact_provenance(self):
        rows = evaluation_rows("test")
        selected = next(r for r in rows if r["id"] == "logistic_context_C10")
        self.assertAlmostEqual(selected["Log Loss"], .2870174755192558)
        self.assertAlmostEqual(selected["Brier"], .08228305325380478)
        self.assertAlmostEqual(selected["ROC-AUC"], .7750937260386367)
        self.assertFalse(artifacts()["selection"]["test_used_for_selection"])
        with self.assertRaises(ValueError): evaluation_rows("future")


if __name__ == "__main__":
    unittest.main(verbosity=2)
