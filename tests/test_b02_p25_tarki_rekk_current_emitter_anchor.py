from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "registry" / "b02_current_heating_device_controls.csv"
AUDIT = ROOT / "registry" / "b02_public_emitter_evidence_audit.csv"
GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
PACK = ROOT / "docs" / "source_packs" / "B02_P25_TARKI_REKK_CURRENT_EMITTER_ANCHOR.md"


class B02P25TarkiRekkCurrentEmitterAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with CONTROLS.open(encoding="utf-8", newline="") as handle:
            cls.controls = list(csv.DictReader(handle))
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            cls.audit = {row["audit_id"]: row for row in csv.DictReader(handle)}
        with GATE.open(encoding="utf-8", newline="") as handle:
            cls.gate = {row["claim_id"]: row for row in csv.DictReader(handle)}
        cls.pack = PACK.read_text(encoding="utf-8")

    def test_exact_published_gas_heating_device_controls_are_frozen(self) -> None:
        self.assertEqual(len(self.controls), 3)
        keyed = {row["device_category"]: row for row in self.controls}
        self.assertEqual(
            set(keyed),
            {"TRADITIONAL_GAS_BOILER", "CONDENSING_GAS_BOILER", "GAS_CONVECTOR"},
        )
        self.assertEqual(float(keyed["TRADITIONAL_GAS_BOILER"]["value_percent"]), 26.66)
        self.assertEqual(float(keyed["CONDENSING_GAS_BOILER"]["value_percent"]), 32.73)
        self.assertEqual(float(keyed["GAS_CONVECTOR"]["value_percent"]), 40.61)
        self.assertAlmostEqual(
            sum(float(row["value_percent"]) for row in self.controls), 100.0, places=9
        )
        self.assertTrue(all(row["sample_n"] == "657" for row in self.controls))
        self.assertTrue(all(row["evidence_status"] == "DER" for row in self.controls))

    def test_only_gas_convector_is_emitter_device_control(self) -> None:
        keyed = {row["device_category"]: row for row in self.controls}
        self.assertEqual(keyed["GAS_CONVECTOR"]["category_role"], "EMITTER_DEVICE_CONTROL")
        self.assertEqual(
            keyed["GAS_CONVECTOR"]["admission_effect"], "CURRENT_EMITTER_NUMERIC_CONTROL"
        )
        for category in ("TRADITIONAL_GAS_BOILER", "CONDENSING_GAS_BOILER"):
            self.assertEqual(keyed[category]["category_role"], "HEAT_GENERATOR_CONTROL")
            self.assertIn("HEAT_GENERATOR_NOT_EMITTER", keyed[category]["blockers"])
        self.assertIn("TRADITIONAL GAS BOILER != RADIATOR", self.pack)
        self.assertIn("CONDENSING GAS BOILER != RADIATOR", self.pack)

    def test_survey_control_is_not_wbl_assignment(self) -> None:
        for row in self.controls:
            self.assertEqual(row["wbl_direct_join"], "NO")
            self.assertEqual(row["current_stock_complete"], "NO")
            self.assertEqual(row["status"], "QUALIFIED_CONTROL_ONLY")
        convector = next(row for row in self.controls if row["device_category"] == "GAS_CONVECTOR")
        self.assertIn("SURVEY_AGGREGATE_NOT_WBL_BOUND", convector["blockers"])
        self.assertIn("HOUSEHOLD_TO_WBL_UNIVERSE_NOT_RECONCILED", convector["blockers"])
        self.assertIn("NO_CELL_LEVEL_ASSIGNMENT", convector["blockers"])
        self.assertIn("NATIONALLY REPRESENTATIVE SURVEY CONTROL != WBL CELL ASSIGNMENT", self.pack)
        self.assertIn(
            "GAS-CONVECTOR SHARE AMONG GAS-HEATING HOUSEHOLDS != SHARE AMONG ALL OCCUPIED DWELLINGS",
            self.pack,
        )

    def test_public_emitter_audit_records_numeric_current_control(self) -> None:
        row = self.audit["B02-P25-A07"]
        self.assertEqual(row["emitter_taxonomy_explicit"], "YES")
        self.assertEqual(row["published_numeric_emitter_assignment"], "YES")
        self.assertEqual(row["wbl_direct_join"], "NO")
        self.assertEqual(row["current_stock_complete"], "NO")
        self.assertEqual(row["admission_effect"], "CURRENT_EMITTER_NUMERIC_CONTROL")
        self.assertEqual(row["status"], "QUALIFIED_CONTROL_ONLY")
        self.assertIn("40.61%", row["notes"])
        self.assertIn("N=657", row["notes"])

    def test_full_sample_uncertainty_is_not_applied_to_conditional_subgroup(self) -> None:
        self.assertIn("N = 1,013", self.pack)
        self.assertIn("3.4%", self.pack)
        self.assertIn("N = 657", self.pack)
        self.assertIn(
            "FULL-SAMPLE MARGIN OF ERROR != CONDITIONAL SUBGROUP MARGIN OF ERROR",
            self.pack,
        )

    def test_stadat_update_year_is_not_data_reference_year(self) -> None:
        self.assertIn("displayed annual series ends at **2020**", self.pack)
        self.assertIn("PAGE UPDATE YEAR 2022 != DATA REFERENCE YEAR 2022", self.pack)

    def test_technical_readiness_remains_fail_closed_on_exact_two_blockers(self) -> None:
        row = self.gate["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )
        self.assertIn("P25", row["notes"])
        self.assertIn("40.61%", row["notes"])
        self.assertIn("both technical blockers stay open", row["notes"])
        self.assertIn("PUBLIC CURRENT GAS-CONVECTOR NUMERIC CONTROL = QUALIFIED_CONTROL_ONLY / DER", self.pack)


if __name__ == "__main__":
    unittest.main()
