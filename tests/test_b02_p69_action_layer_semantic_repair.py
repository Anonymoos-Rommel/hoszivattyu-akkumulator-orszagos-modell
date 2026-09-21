import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P66 = ROOT / "registry" / "b02_p66_transition_set_propagation.csv"
P68 = ROOT / "registry" / "b02_p68_reweighting_crosswalk.csv"
P69 = ROOT / "registry" / "b02_p69_action_layer_semantic_repair.csv"
SOURCES = ROOT / "registry" / "sources.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P69_ACTION_LAYER_SEMANTIC_REPAIR.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P69ActionLayerSemanticRepairTests(unittest.TestCase):
    def test_p66_false_simplex_is_superseded(self):
        p66 = rows(P66, "item_id")
        self.assertEqual(p66["B02-P66-A01"]["status"], "SUPERSEDED_BY_P69")
        self.assertEqual(p66["B02-P66-A02"]["status"], "SUPERSEDED_BY_P69")
        self.assertEqual(p66["B02-P66-A08"]["status"], "SUPERSEDED_BY_P69")

    def test_p68_crosswalk_rows_are_superseded(self):
        p68 = rows(P68, "item_id")
        for key in ("B02-P68-R09", "B02-P68-R10", "B02-P68-R11"):
            self.assertEqual(p68[key]["status"], "SUPERSEDED_BY_P69")

    def test_distribution_floor_is_on_correct_layer(self):
        p69 = rows(P69, "item_id")
        nonreuse = p69["B02-P69-L02"]
        self.assertEqual(nonreuse["status"], "SUPERSEDED_BY_P70")
        self.assertEqual(nonreuse["lower_bound"], "0.233")
        self.assertEqual(nonreuse["claim"], "NEW_OR_REPLACE_DISTRIBUTION_REQUIRED_SHARE")
        self.assertEqual(
            p69["B02-P69-L04"]["lower_bound"],
            "933990.053",
        )

    def test_emitter_action_axis_is_multi_label(self):
        p69 = rows(P69, "item_id")
        action = p69["B02-P69-L05"]
        self.assertEqual(action["status"], "MULTI_LABEL_ROOM_OR_UNIT")
        self.assertIn("ROOM_GRAIN_ACTION_DISTRIBUTION", action["residual_gap"])
        self.assertIn("KEEP;UPSIZE;CHANGE;ADD", action["notes"])

    def test_eoh_event_semantics_are_bounded_and_foreign(self):
        p69 = rows(P69, "item_id")
        positive = p69["B02-P69-L07"]
        zero = p69["B02-P69-L08"]
        self.assertEqual(positive["status"], "QUALIFIED_FOREIGN_COHORT_EVENT")
        self.assertEqual(positive["lower_bound"], "0.928571")
        self.assertIn("HUNGARIAN_PREVALENCE", positive["forbidden_use"])
        self.assertEqual(zero["lower_bound"], "0.071429")
        self.assertIn("HUNGARIAN_KEEP_RATE", zero["forbidden_use"])

    def test_install_report_source_is_registered(self):
        sources = rows(SOURCES, "source_id")
        src = sources["SRC-B02-DESNZ-EOH-INSTALL-REPORT-2022"]
        self.assertEqual(src["module_id"], "B02")
        self.assertEqual(src["reliability"], "HIGH")
        self.assertIn("Section 6.3.2", src["reference_period"])
        self.assertIn("anecdotal", src["notes"])

    def test_q_b02_004_uses_layered_residuals(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("ACTION_LAYER_SEMANTIC_REPAIR", q["notes"])
        self.assertIn("HUNGARIAN_DISTRIBUTION_NONREUSE_ASSIGNMENT", q["notes"])
        self.assertIn("ROOM_GRAIN_ACTION_DISTRIBUTION", q["notes"])

    def test_readiness_does_not_increase(self):
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P69", b02["gate_note"])
        self.assertIn("SUPERSEDED", b02["gate_note"])

    def test_source_pack_freezes_grain_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "DWELLING DISTRIBUTION PATH != ROOM/EMITTER ACTION",
            "ROOM/EMITTER ACTIONS ARE NOT A DWELLING SIMPLEX",
            "NEW_OR_REPLACE_DISTRIBUTION_REQUIRED >= 0.233",
            "NO_NEW_EMITTER_INSTALLATION",
            "NHEAT != PROVEN REPLACE_EXISTING_DISTRIBUTION",
            "HUNGARIAN_EMITTER_INTERVENTION_ASSIGNMENT",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
