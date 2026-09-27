import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b09_p6_generation_missingness_recovery_gate.csv"
ACQ = ROOT / "registry" / "b09_p6_mavir_operational_acquisition.csv"
VALIDATION = ROOT / "registry" / "b09_p6_dual_basis_overlap_validation.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
PACK = ROOT / "docs" / "source_packs" / "B09_P6_GENERATION_MISSINGNESS_RECOVERY_GATE.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B09P6GenerationMissingnessRecoveryGateTests(unittest.TestCase):
    def test_area_view_switching_is_exhausted(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        x = r["B09-P6-R01"]
        self.assertEqual("EXHAUSTED_NO_RECOVERY", x["current_state"])
        self.assertIn("09ede94527e3539", x["notes"])
        self.assertEqual("CONTENT_IDENTICAL_NO_NEW_VALUES", x["disqualifier"])

    def test_dual_basis_selection_chooses_net_operational(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        settlement = r["B09-P6-R02"]
        operational = r["B09-P6-R03"]
        semantics = r["B09-P6-R06"]
        self.assertEqual("ACQUIRED_SECONDARY_CROSSCHECK", settlement["current_state"])
        self.assertEqual("ACQUIRED_SELECTED_RECOVERY_BASIS", operational["current_state"])
        self.assertIn("üzemirányítási", operational["source_product"])
        self.assertIn("0.9999966663", operational["notes"])
        self.assertIn("4809 negative", operational["notes"])
        self.assertEqual("BLOCKED_BY_CURRENT_NONNEGATIVE_GENERATION_CONTRACT", semantics["current_state"])
        self.assertEqual("SIGNED_NET_GENERATION_RECOVERY_SEMANTICS_REQUIRED", semantics["residual_gap"])

    def test_a73_is_secondary_threshold_bound_not_complete_aggregate(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        x = r["B09-P6-R04"]
        self.assertEqual("SECONDARY_ONLY", x["current_state"])
        self.assertIn("GE_100MW", x["disqualifier"])
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("100 MW or more", text)
        self.assertIn("SUM(A73 PUBLISHED UNITS) != PROVEN COMPLETE A75 PRODUCTION_TYPE TOTAL", text)

    def test_blank_to_zero_remains_forbidden(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        x = r["B09-P6-R05"]
        self.assertEqual("ACTIVE", x["current_state"])
        self.assertIn("BLANK_TO_ZERO", x["disqualifier"])
        self.assertIn("Fossil Oil=4817", x["notes"])

    def test_blocker_remains_e3_until_recovery(self):
        audit = {row["blocker_id"]: row for row in rows(AUDIT)}
        x = audit["Q-B09-001"]
        self.assertEqual("E3", x["evidence_tier"])
        self.assertEqual("MODEL_BLOCKER", x["blocker_class"])
        self.assertEqual("yes", x["model_blocker"])
        self.assertIn("MAVIR_NET_OPERATIONAL_SELECTED_FOR_EXACT_MISSING_CELL_RECOVERY", x["canonical_base_rule"])
        self.assertIn("NO_NEGATIVE_TO_ZERO_CLAMP", x["canonical_base_rule"])

    def test_operational_raw_acquisition_is_exact_and_overlap_consistent(self):
        r = {row["record_id"]: row for row in rows(ACQ)}
        self.assertEqual(
            "2c1bfd1f4fe9a0fc0b1262a86376037a5ae8c17bc2e6a412e4f996afaa46cb8f",
            r["B09-P6-OP01"]["sha256"],
        )
        summary = r["B09-P6-OP05"]
        self.assertEqual("35040", summary["raw_data_rows"])
        self.assertIn("26,404", summary["notes"])
        self.assertIn("exactly identical", summary["notes"])

    def test_overlap_validation_selects_operational_for_all_three_types(self):
        r = rows(VALIDATION)
        selected = [row for row in r if row["selection"] == "SELECTED"]
        self.assertEqual(3, len(selected))
        self.assertTrue(all(row["basis"] == "NET_OPERATIONAL" for row in selected))
        gas = next(row for row in selected if row["production_type"] == "Fossil Gas")
        self.assertEqual("2", gas["recovered_missing_cells"])
        self.assertEqual("0.2305897311", gas["mae_mw"])

    def test_open_question_has_exact_new_residual(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}
        notes = q["Q-B09-001"]["notes"]
        self.assertIn("SIGNED_NET_GENERATION_RECOVERY_SEMANTICS_REQUIRED", notes)
        self.assertIn("No value is clamped", notes)


if __name__ == "__main__":
    unittest.main()
