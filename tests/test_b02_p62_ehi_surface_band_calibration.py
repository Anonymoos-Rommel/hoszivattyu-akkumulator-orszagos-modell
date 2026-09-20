import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BAND = ROOT / "registry" / "b02_p62_ehi_surface_presence_band.csv"
SOURCES = ROOT / "registry" / "sources.csv"
AUDIT = ROOT / "registry" / "b02_public_emitter_evidence_audit.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P62_EHI_SURFACE_BAND_CALIBRATION.md"


class B02P62EhiSurfaceBandCalibrationTests(unittest.TestCase):
    def test_houses_and_apartments_share_exact_ehi_band(self):
        with BAND.open(encoding="utf-8", newline="") as handle:
            rows = {row["constraint_id"]: row for row in csv.DictReader(handle)}
        for cid in ("B02-P62-C01", "B02-P62-C02"):
            self.assertEqual(rows[cid]["lower_bound"], "0.33")
            self.assertEqual(rows[cid]["upper_bound"], "0.66")
            self.assertEqual(rows[cid]["evidence_status"], "DER")
            self.assertEqual(rows[cid]["population_use"], "VALIDATION_BAND_ONLY")
            self.assertEqual(rows[cid]["programme_use_allowed"], "YES_SENSITIVITY_ONLY")
            self.assertIn("POINT_ESTIMATE", rows[cid]["forbidden_inference"])
            self.assertIn("RADIATOR_COMPLEMENT", rows[cid]["forbidden_inference"])

    def test_no_midpoint_is_materialized(self):
        text = BAND.read_text(encoding="utf-8")
        self.assertNotIn("0.495", text)
        self.assertNotIn("49.5", text)
        self.assertNotIn("0.50", text)

    def test_temperature_references_have_no_population_weight(self):
        with BAND.open(encoding="utf-8", newline="") as handle:
            rows = {row["constraint_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02-P62-C03"]["lower_bound"], "35")
        self.assertEqual(rows["B02-P62-C03"]["upper_bound"], "28")
        self.assertEqual(rows["B02-P62-C04"]["upper_bound"], "55")
        self.assertEqual(rows["B02-P62-C05"]["lower_bound"], "70")
        self.assertEqual(rows["B02-P62-C05"]["upper_bound"], "80")
        for cid in ("B02-P62-C03", "B02-P62-C04", "B02-P62-C05"):
            self.assertEqual(rows[cid]["population_use"], "NO_POPULATION_WEIGHT")
            self.assertIn("DESIGN_TEMP_POPULATION_WEIGHTS", rows[cid]["residual_gap"])

    def test_q_b02_004_remains_open_and_is_narrower(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        q4 = rows["Q-B02-004"]
        self.assertEqual(q4["status"], "OPEN")
        self.assertIn("33–66%", q4["evidence_needed"])
        self.assertIn("KSH/P21", q4["evidence_needed"])
        self.assertIn("MIXED_SYSTEM_OVERLAP", q4["notes"])
        self.assertIn("OTHER_EMITTER_SHARE", q4["notes"])
        self.assertIn("DESIGN_TEMP_POPULATION_WEIGHTS", q4["notes"])
        self.assertIn("2026-08-22", q4["notes"])
        self.assertIn("record-level evidence", q4["notes"])

    def test_ehi_source_and_audit_are_registered(self):
        with SOURCES.open(encoding="utf-8", newline="") as handle:
            sources = {row["source_id"]: row for row in csv.DictReader(handle)}
        src = sources["SRC-B02-EHI-HMR-2024-SURFACE-PENETRATION"]
        self.assertEqual(src["evidence_status"], "DER")
        self.assertEqual(src["reliability"], "HIGH")
        self.assertIn("33%-66%", src["notes"])

        with AUDIT.open(encoding="utf-8", newline="") as handle:
            audits = {row["audit_id"]: row for row in csv.DictReader(handle)}
        a = audits["B02-P62-A13"]
        self.assertEqual(a["status"], "QUALIFIED_BINNED_CONTROL")
        self.assertEqual(a["published_numeric_emitter_assignment"], "YES")
        self.assertIn("NO_MIXED_OVERLAP", a["blockers"])

    def test_module_readiness_does_not_increase(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02"]["readiness_percent"], "55")
        self.assertIn("33–66%", rows["B02"]["gate_note"])
        self.assertIn("Q-B02-004 OPEN", rows["B02"]["gate_note"])

    def test_source_pack_freezes_key_non_equivalences(self):
        text = SOURCE_PACK.read_text(encoding="utf-8")
        for boundary in (
            "BINNED CLASSIFICATION != POINT ESTIMATE",
            "SURFACE_PRESENT != SURFACE_ONLY",
            "RADIATOR_SHARE != 1 - SURFACE_PRESENT",
            "TEMPERATURE CLASS EXISTS != HUNGARIAN POPULATION WEIGHT KNOWN",
            "KSH_DENOMINATOR_BRIDGE",
            "MIXED_SYSTEM_OVERLAP",
            "OTHER_EMITTER_SHARE",
            "DESIGN_TEMP_POPULATION_WEIGHTS",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
