from pathlib import Path
import csv
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAYERS = ROOT / "registry/b02_eligibility_layer_contract.csv"
VARIABLES = ROOT / "registry/variables.csv"
TECHNICAL_GATE = ROOT / "registry/b02_technical_eligibility_gate.csv"
DOC = ROOT / "docs/source_packs/B02_P3_ELIGIBILITY_LAYER_HARMONIZATION.md"


class B02P3EligibilityLayerHarmonizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with LAYERS.open(encoding="utf-8", newline="") as handle:
            cls.layers = {row["layer_id"]: row for row in csv.DictReader(handle)}
        with VARIABLES.open(encoding="utf-8", newline="") as handle:
            cls.variables = {row["variable_id"]: row for row in csv.DictReader(handle)}
        with TECHNICAL_GATE.open(encoding="utf-8", newline="") as handle:
            cls.technical_rows = list(csv.DictReader(handle))

    def test_exact_layer_set_is_explicit(self):
        self.assertEqual(
            {
                "PHYSICAL_SCREENING_SCOPE",
                "TECHNICAL_ELIGIBILITY",
                "S2_TRANSITION_READINESS",
                "LEGAL_PROGRAMME_ELIGIBILITY",
                "ECONOMIC_ELIGIBILITY",
                "FINAL_PROGRAMME_ELIGIBILITY",
            },
            set(self.layers),
        )

    def test_only_physical_layer_has_current_numeric_count(self):
        physical = self.layers["PHYSICAL_SCREENING_SCOPE"]
        self.assertEqual("3389817", physical["current_count"])
        self.assertEqual("DER_FROM_OBS_WBL011_CELLS", physical["current_status"])
        for layer_id, row in self.layers.items():
            if layer_id == "PHYSICAL_SCREENING_SCOPE":
                continue
            self.assertEqual("", row["current_count"])

    def test_technical_layer_points_to_p2_canonical_output(self):
        technical = self.layers["TECHNICAL_ELIGIBILITY"]
        self.assertEqual("B02", technical["owner_module"])
        self.assertEqual(
            "registry/b02_technical_eligibility_gate.csv:technical_eligible_dwellings",
            technical["canonical_output_ref"],
        )
        self.assertEqual("Q", technical["current_status"])
        self.assertIn("THERMAL_DISTRIBUTION", technical["required_gates"])
        self.assertIn("HYDRAULIC", technical["required_gates"])
        self.assertIn("ELECTRICAL", technical["required_gates"])
        self.assertIn("PERMIT", technical["required_gates"])

    def test_s2_remains_separate_from_technical_eligibility(self):
        row = self.layers["S2_TRANSITION_READINESS"]
        self.assertEqual("S2_Q", row["current_status"])
        self.assertIn("S1_demand_reduction_measured_or_not_required", row["required_gates"])

    def test_legacy_global_variable_is_blank_q_and_not_technical_authority(self):
        legacy = self.variables["VAR-B02-ELIGIBLE-DWELLINGS"]
        self.assertEqual("", legacy["default_value"])
        self.assertEqual("Q", legacy["status"])
        final_layer = self.layers["FINAL_PROGRAMME_ELIGIBILITY"]
        self.assertEqual(
            "VAR-B02-ELIGIBLE-DWELLINGS:DEPRECATED_UMBRELLA_ONLY",
            final_layer["legacy_variable_binding"],
        )
        self.assertNotEqual(
            "VAR-B02-ELIGIBLE-DWELLINGS",
            self.layers["TECHNICAL_ELIGIBILITY"]["canonical_output_ref"],
        )

    def test_p2_gate_and_p3_registry_agree_on_current_unknown(self):
        self.assertEqual(1, len(self.technical_rows))
        p2 = self.technical_rows[0]
        self.assertEqual("3389817", p2["physical_screening_reference_households"])
        self.assertEqual("", p2["technical_eligible_dwellings"])
        self.assertEqual("Q", p2["technical_eligibility_status"])
        self.assertEqual("S2_Q", p2["s2_transition_status"])

    def test_document_freezes_non_equivalence_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "PHYSICAL SCREENING != TECHNICAL ELIGIBILITY != S2 READINESS != LEGAL ELIGIBILITY != ECONOMIC ELIGIBILITY != FINAL PROGRAMME ELIGIBILITY",
            "DEPRECATED_UMBRELLA_ONLY",
            "3,389,817",
            "Q-B02-001",
            "Q-B02-004",
            "Q-B01-001",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
