import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_archetype_linkage import (
    BUILDING_EVIDENCE_STATUS,
    BUILDING_MODEL_ID,
    ENERGY_EVIDENCE_STATUS,
    ENERGY_MODEL_ID,
    EXPECTED_OCCUPIED_DWELLINGS,
    EXPECTED_WBL_ROWS,
    build_calibrated_linkage,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
P9 = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P21_PUBLIC_KSH_CALIBRATED_ARCHETYPE.md"


class B02P21PublicCalibratedArchetypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows, cls.summary = build_calibrated_linkage()

    def test_exact_wbl_universe_is_bound(self):
        self.assertEqual(self.summary.row_count, EXPECTED_WBL_ROWS)
        self.assertEqual(self.summary.occupied_dwellings, EXPECTED_OCCUPIED_DWELLINGS)
        self.assertEqual(self.summary.family_target_dwellings, 2_423_136)
        self.assertEqual(self.summary.multi_target_dwellings, 1_585_405)
        self.assertAlmostEqual(self.summary.central_family_expected, 2_423_136, places=5)
        self.assertAlmostEqual(self.summary.flat_family_expected, 2_423_136, places=5)
        self.assertLessEqual(self.summary.maximum_settlement_reconciliation_residual, 1e-5)

    def test_model_output_semantics_remain_modelled(self):
        self.assertEqual(BUILDING_EVIDENCE_STATUS, "ASS")
        self.assertEqual(ENERGY_EVIDENCE_STATUS, "MODELLED")
        self.assertEqual(BUILDING_MODEL_ID, "B02-P21-PUBLIC-KSH-BUILDING-TYPE-LINKAGE")
        self.assertEqual(ENERGY_MODEL_ID, "B02-P21-PUBLIC-KSH-PRIMARY-ENERGY-LINKAGE")
        self.assertTrue(all(row["building_type_evidence_status"] == "ASS" for row in self.rows))
        self.assertTrue(all(row["primary_energy_evidence_status"] == "MODELLED" for row in self.rows))

    def test_probabilities_and_energy_envelopes_are_bounded(self):
        for row in self.rows:
            central = float(row["central_family_probability"])
            flat = float(row["flat_family_probability"])
            low = float(row["family_probability_low"])
            high = float(row["family_probability_high"])
            self.assertGreaterEqual(central, 0.0)
            self.assertLessEqual(central, 1.0)
            self.assertGreaterEqual(flat, 0.0)
            self.assertLessEqual(flat, 1.0)
            self.assertLessEqual(low, central)
            self.assertLessEqual(low, flat)
            self.assertGreaterEqual(high, central)
            self.assertGreaterEqual(high, flat)

            central_energy = float(row["central_primary_energy_kwh_m2_year"])
            flat_energy = float(row["flat_primary_energy_kwh_m2_year"])
            energy_low = float(row["primary_energy_low_kwh_m2_year"])
            energy_high = float(row["primary_energy_high_kwh_m2_year"])
            self.assertGreater(central_energy, 0.0)
            self.assertGreater(flat_energy, 0.0)
            self.assertLessEqual(energy_low, central_energy)
            self.assertLessEqual(energy_low, flat_energy)
            self.assertGreaterEqual(energy_high, central_energy)
            self.assertGreaterEqual(energy_high, flat_energy)

    def test_current_2022_age_shape_is_not_silently_flattened(self):
        self.assertTrue(
            any(
                abs(
                    float(row["central_family_probability"])
                    - float(row["flat_family_probability"])
                )
                > 1e-6
                for row in self.rows
            )
        )
        self.assertGreater(self.summary.dwelling_weighted_structural_energy_delta, 0.0)

    def test_p12_registry_records_explicit_joseph_approval(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            registry = {row["claim_id"]: row for row in csv.DictReader(handle)}
        building = registry["CALIBRATED_BUILDING_TYPE_LINKAGE"]
        primary = registry["CALIBRATED_PRIMARY_ENERGY_LINKAGE"]
        self.assertEqual(building["current_model_id"], BUILDING_MODEL_ID)
        self.assertEqual(primary["current_model_id"], ENERGY_MODEL_ID)
        for row in (building, primary):
            self.assertEqual(row["current_status"], "QUALIFIED")
            self.assertEqual(row["approval_status"], "APPROVED")
            self.assertEqual(row["approval_authority"], "JOSEPH")
            self.assertEqual(row["blockers"], "")
            self.assertEqual(row["target_grain_wbl_compatible"], "yes")
            self.assertEqual(row["representativeness_diagnostics"], "yes")
            self.assertEqual(row["validation_metrics"], "yes")
            self.assertEqual(row["marginal_reconciliation"], "yes")
            self.assertEqual(row["uncertainty_method"], "yes")
            self.assertEqual(row["uncertainty_propagation"], "yes")
            self.assertEqual(row["independence_assumption_controlled"], "yes")

    def test_approved_models_qualify_current_stock_but_not_technical_readiness(self):
        with P9.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        current = rows["CURRENT_STOCK_ARCHETYPE_ASSIGNMENT"]
        technical = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(current["current_status"], "QUALIFIED")
        self.assertEqual(current["current_blockers"], "")
        self.assertEqual(technical["current_status"], "Q")
        self.assertEqual(
            technical["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )

    def test_source_pack_freezes_public_model_boundaries_and_approval(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("PUBLIC KSH CALIBRATION != DIRECT OBSERVATION", text)
        self.assertIn("AGE-SHAPED CENTRAL != FLAT STRUCTURAL SENSITIVITY", text)
        self.assertIn("APPROVED / JOSEPH / QUALIFIED", text)
        self.assertIn("former `NO_JOSEPH_APPROVAL` blocker is closed", text)
        self.assertIn("2026-09-06 09:23 Europe/Budapest", text)
        self.assertIn("116 452", text)
        self.assertIn("4 008 541", text)
        self.assertIn("2 423 136", text)
        self.assertIn("1 585 405", text)


if __name__ == "__main__":
    unittest.main()
