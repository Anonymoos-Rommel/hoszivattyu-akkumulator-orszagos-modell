import csv
import unittest
from pathlib import Path

from modules.B02.response_reweighting import (
    ResponseInterval,
    crosswalk_eoh_emitter_measure_count,
    current_p67_transfer_sensitivity,
    p21_building_type_weights,
    reweight_building_type_intervals,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p68_reweighting_crosswalk.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"


def read_rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P68HungarianReweightingActionCrosswalkTests(unittest.TestCase):
    def test_p21_weights_reconcile_exact_occupied_universe(self):
        w = p21_building_type_weights()
        self.assertEqual(w.occupied_dwellings, 4_008_541)
        self.assertEqual(w.family_dwellings, 2_423_136)
        self.assertEqual(w.multi_dwellings, 1_585_405)
        self.assertAlmostEqual(w.family_weight + w.multi_weight, 1.0)
        self.assertEqual(w.evidence_status, "ASS")

    def test_interval_reweighting_uses_hungarian_weights(self):
        out = reweight_building_type_intervals(
            metric="x",
            family=ResponseInterval(1.0, 3.0),
            multi=ResponseInterval(2.0, 4.0),
        )
        w = p21_building_type_weights()
        self.assertAlmostEqual(out.lower, w.family_weight * 1.0 + w.multi_weight * 2.0)
        self.assertAlmostEqual(out.upper, w.family_weight * 3.0 + w.multi_weight * 4.0)
        self.assertEqual(out.evidence_status, "ASS")

    def test_current_p67_transfer_envelopes_match_registry_contract(self):
        out = current_p67_transfer_sensitivity()
        self.assertAlmostEqual(out["emitter_units"].lower, 2.5820269769, places=6)
        self.assertAlmostEqual(out["emitter_units"].upper, 11.8359460462, places=6)
        self.assertAlmostEqual(out["mean_sh_flow_c"].lower, 33.0460082020, places=6)
        self.assertAlmostEqual(out["mean_sh_flow_c"].upper, 45.3889623586, places=6)
        self.assertAlmostEqual(out["spfh4"].lower, 1.9570339500, places=6)
        self.assertAlmostEqual(out["spfh4"].upper, 3.4846316533, places=6)

    def test_positive_measure_means_new_emitter_installation_not_room_action(self):
        out = crosswalk_eoh_emitter_measure_count(1)
        self.assertEqual(out.status, "QUALIFIED_NEW_EMITTER_INSTALLATION_PRESENT")
        self.assertTrue(out.new_emitter_installation_present)
        self.assertIn("ROOM_GRAIN_ACTION_SUBTYPE_NOT_IDENTIFIED", out.blockers)

    def test_zero_measure_means_no_new_emitter_installation(self):
        out = crosswalk_eoh_emitter_measure_count(0)
        self.assertEqual(out.status, "QUALIFIED_NO_NEW_EMITTER_INSTALLATION")
        self.assertFalse(out.new_emitter_installation_present)
        self.assertEqual(out.blockers, ())

    def test_negative_measure_fails_closed(self):
        out = crosswalk_eoh_emitter_measure_count(-1)
        self.assertEqual(out.status, "Q")
        self.assertIsNone(out.new_emitter_installation_present)
        self.assertIn("EMITTER_MEASURE_COUNT_INVALID", out.blockers)

    def test_registry_keeps_reweighting_but_marks_old_crosswalk_superseded(self):
        rows = read_rows(REG, "item_id")
        self.assertEqual(rows["B02-P68-R05"]["status"], "RESOLVED_EXECUTABLE")
        self.assertEqual(rows["B02-P68-R09"]["status"], "SUPERSEDED_BY_P69")
        self.assertEqual(rows["B02-P68-R10"]["status"], "SUPERSEDED_BY_P69")
        self.assertEqual(rows["B02-P68-R11"]["status"], "SUPERSEDED_BY_P69")

    def test_q_b02_004_remains_open_and_readiness_fixed(self):
        q = read_rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P69", q["notes"])
        self.assertIn("ACTION_LAYER_SEMANTIC_REPAIR", q["notes"])
        b02 = read_rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P69", b02["gate_note"])


if __name__ == "__main__":
    unittest.main()
