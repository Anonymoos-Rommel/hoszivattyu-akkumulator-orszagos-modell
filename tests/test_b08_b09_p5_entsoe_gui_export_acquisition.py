import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b08_b09_p5_entsoe_gui_export_acquisition.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
PACK = ROOT / "docs" / "source_packs" / "B08_B09_P5_ENTSOE_GUI_EXPORT_ACQUISITION.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B08B09P5EntsoeGuiExportAcquisitionTests(unittest.TestCase):
    def test_raw_files_are_external_only_with_exact_hashes(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        self.assertEqual(
            "1712362093a2957a8870bff5c8758f53a3358587bc7fa9a54e8ee3ba6ecf301d",
            r["B08B09-P5-R01"]["sha256"],
        )
        self.assertEqual(
            "c7b332bb63d927730a84082571ad8d1e2f143e10de7b497825d45ca74bbbc05d",
            r["B08B09-P5-R03"]["sha256"],
        )
        self.assertTrue(all(row["raw_storage_policy"] == "EXTERNAL_ONLY" for row in r.values()))

    def test_b08_real_load_panel_is_complete(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        load = r["B08B09-P5-R01"]
        self.assertEqual("35040", load["data_rows"])
        self.assertEqual("0", load["missing_value_cells"])
        self.assertEqual("35040", load["complete_intervals"])
        self.assertEqual("100.000000", load["complete_interval_pct"])
        self.assertEqual("QUALIFIED_E2_MODEL_USE", load["model_use_status"])

    def test_b08_local_year_stitch_has_real_companion_export(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        companion = r["B08B09-P5-R02"]
        self.assertEqual("35136", companion["data_rows"])
        self.assertEqual("0", companion["missing_value_cells"])
        self.assertIn("2024-12-31 23:00 UTC", companion["notes"])

    def test_b09_manifest_resolves_numeric_vs_structural_ne_categories(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        generation = r["B08B09-P5-R03"]
        manifest = r["B08B09-P5-R04"]
        self.assertEqual("14", generation["expected_numeric_series"])
        self.assertEqual("7", generation["structural_ne_series"])
        self.assertEqual("14", manifest["expected_numeric_series"])
        self.assertEqual("7", manifest["structural_ne_series"])

    def test_b09_source_gaps_remain_fail_closed(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        generation = r["B08B09-P5-R03"]
        self.assertEqual("4820", generation["affected_intervals"])
        self.assertEqual("30220", generation["complete_intervals"])
        self.assertEqual("86.244292", generation["complete_interval_pct"])
        self.assertEqual(
            "ACTIVE_PRODUCTION_TYPE_SOURCE_MISSINGNESS_TREATMENT_REQUIRED",
            generation["residual_gap"],
        )
        self.assertEqual("2", r["B08B09-P5-R05"]["missing_value_cells"])
        self.assertEqual("4817", r["B08B09-P5-R06"]["missing_value_cells"])
        self.assertEqual("1", r["B08B09-P5-R07"]["missing_value_cells"])

    def test_b08_blocker_is_e2_validation_debt_but_b09_remains_e3(self):
        audit = {row["blocker_id"]: row for row in rows(AUDIT)}
        b08 = audit["Q-B08-001"]
        self.assertEqual("E2", b08["evidence_tier"])
        self.assertEqual("VALIDATION_BLOCKER", b08["blocker_class"])
        self.assertEqual("no", b08["model_blocker"])
        self.assertEqual("MODEL_CONTINUE", b08["canonical_use"])
        b09 = audit["Q-B09-001"]
        self.assertEqual("E3", b09["evidence_tier"])
        self.assertEqual("MODEL_BLOCKER", b09["blocker_class"])
        self.assertEqual("yes", b09["model_blocker"])
        self.assertIn("ACTIVE_SINGLE_SPACE_CELLS_NOT_ZERO", b09["canonical_base_rule"])

    def test_open_questions_preserve_current_residuals(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}
        self.assertIn("E2 / VALIDATION_BLOCKER", q["Q-B08-001"]["notes"])
        self.assertIn(
            "ACTIVE_PRODUCTION_TYPE_SOURCE_MISSINGNESS_TREATMENT_REQUIRED",
            q["Q-B09-001"]["notes"],
        )

    def test_source_pack_freezes_no_blank_to_zero_rule(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("BLANK != ZERO", text)
        self.assertIn("EXTERNAL_ONLY", text)
        self.assertIn("30,220 / 35,040", text)


if __name__ == "__main__":
    unittest.main()
