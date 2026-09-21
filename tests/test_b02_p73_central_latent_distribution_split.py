import csv
import unittest
from pathlib import Path

from modules.B02.central_distribution_split import (
    assess_point_assignment_requirement,
    central_split_endpoint_envelope,
    p72_floor_reproduced,
    project_central_distribution_split,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p73_central_latent_distribution_split.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P73_CENTRAL_LATENT_DISTRIBUTION_SPLIT.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P73CentralLatentDistributionSplitTests(unittest.TestCase):
    def test_zero_endpoint_reproduces_p72(self):
        out = project_central_distribution_split(0.0)
        self.assertEqual(out.central_nonreuse_dwellings, 0.0)
        self.assertEqual(out.central_reuse_dwellings, 2_216_178.0)
        self.assertEqual(out.total_nonreuse_dwellings, 1_173_639.0)
        self.assertEqual(out.total_reuse_dwellings, 2_216_178.0)
        self.assertAlmostEqual(out.total_nonreuse_share, 1_173_639 / 3_389_817)
        self.assertAlmostEqual(out.total_reuse_share, 2_216_178 / 3_389_817)
        self.assertTrue(p72_floor_reproduced())

    def test_one_endpoint_is_all_nonreuse(self):
        out = project_central_distribution_split(1.0)
        self.assertEqual(out.central_nonreuse_dwellings, 2_216_178.0)
        self.assertEqual(out.central_reuse_dwellings, 0.0)
        self.assertEqual(out.total_nonreuse_dwellings, 3_389_817.0)
        self.assertEqual(out.total_reuse_dwellings, 0.0)
        self.assertEqual(out.total_nonreuse_share, 1.0)
        self.assertEqual(out.total_reuse_share, 0.0)

    def test_arbitrary_latent_split_conserves_population(self):
        out = project_central_distribution_split(0.371)
        self.assertAlmostEqual(
            out.total_nonreuse_dwellings + out.total_reuse_dwellings,
            3_389_817.0,
        )
        self.assertAlmostEqual(out.total_nonreuse_share + out.total_reuse_share, 1.0)
        self.assertEqual(out.evidence_status, "SET_LATENT")

    def test_invalid_latent_split_fails_closed(self):
        for value in (-0.01, 1.01, float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                project_central_distribution_split(value)

    def test_endpoint_envelope_is_exact_p72_set(self):
        low, high = central_split_endpoint_envelope()
        self.assertAlmostEqual(low.total_nonreuse_share, 0.3462248847061656)
        self.assertAlmostEqual(high.total_nonreuse_share, 1.0)
        self.assertAlmostEqual(low.total_reuse_share, 0.6537751152938345)
        self.assertAlmostEqual(high.total_reuse_share, 0.0)

    def test_point_assignment_not_required_when_path_outcomes_complete(self):
        out = assess_point_assignment_requirement(
            reuse_path_outcome_bounds_complete=True,
            nonreuse_path_outcome_bounds_complete=True,
        )
        self.assertEqual(
            out.status,
            "POINT_ASSIGNMENT_NOT_REQUIRED_FOR_BOUNDED_PROPAGATION",
        )
        self.assertFalse(out.point_assignment_required)
        self.assertEqual(out.blockers, ())

    def test_missing_path_outcome_is_the_blocker_not_point_assignment(self):
        out = assess_point_assignment_requirement(
            reuse_path_outcome_bounds_complete=True,
            nonreuse_path_outcome_bounds_complete=False,
        )
        self.assertEqual(out.status, "Q_PATH_OUTCOME_BOUNDS_REQUIRED")
        self.assertFalse(out.point_assignment_required)
        self.assertIn("NONREUSE_PATH_OUTCOME_BOUNDS_INCOMPLETE", out.blockers)

    def test_registry_retires_central_point_assignment_blocker(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P73-C08"]["status"],
            "RETIRED_AS_POINT_BLOCKER",
        )
        self.assertEqual(reg["B02-P73-C02"]["status"], "SET_LATENT")
        self.assertIn(
            "REUSE_PATH_OUTCOME_BOUNDS",
            reg["B02-P73-C08"]["residual_gap"],
        )

    def test_q_b02_004_moves_to_path_outcomes(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P73", q["notes"])
        self.assertIn("RETIRED_AS_POINT_BLOCKER", q["notes"])
        self.assertIn("REUSE_PATH_OUTCOME_BOUNDS", q["notes"])
        self.assertIn("NONREUSE_PATH_OUTCOME_BOUNDS", q["notes"])

    def test_readiness_remains_55(self):
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P73", b02["gate_note"])

    def test_source_pack_forbids_midpoint_promotion(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "POINT ESTIMATE NOT IDENTIFIED != MODEL BLOCKED",
            "CENTRAL_HEATING != HYDRONIC_REUSE_READY",
            "RETIRED_AS_POINT_BLOCKER",
            "x = 0.5",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
