import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
REAUDIT = ROOT / "registry" / "b02_p51_emitter_inference_reaudit.csv"
P43_ROUTES = ROOT / "registry" / "b02_p43_radiator_data_recovery_routes.csv"
P46_ROUTES = ROOT / "registry" / "b02_p46_radiator_data_provider_routes.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P51_NEER2_EMITTER_INFERENCE_REAUDIT.md"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"


class B02P51Neer2EmitterInferenceReauditTests(unittest.TestCase):
    def test_q_b02_004_remains_open_with_narrowed_residual(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        row = rows["Q-B02-004"]
        self.assertEqual(row["status"], "OPEN")
        self.assertIn("NON_DISTRICT_HYDRONIC_EMITTER_MIX", row["notes"])
        self.assertIn("DESIGN_TEMPERATURE_DISTRIBUTION", row["notes"])
        self.assertIn("2029", row["notes"])

    def test_reaudit_preserves_known_and_missing_surfaces(self):
        with REAUDIT.open(encoding="utf-8", newline="") as handle:
            rows = {row["surface_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02-P51-S01"]["current_status"], "QUALIFIED")
        self.assertEqual(rows["B02-P51-S03"]["current_status"], "QUALIFIED_CALIBRATION_SURFACE")
        self.assertEqual(rows["B02-P51-S05"]["current_status"], "Q")
        self.assertEqual(rows["B02-P51-S06"]["current_status"], "Q")
        self.assertEqual(rows["B02-P51-S07"]["current_status"], "OPEN")

    def test_neer2_route_uses_realised_2029_sample_and_no_false_recovery(self):
        with P43_ROUTES.open(encoding="utf-8", newline="") as handle:
            rows = {row["route_id"]: row for row in csv.DictReader(handle)}
        row = rows["NEER2_RAW_BUILDING_SURVEY"]
        self.assertIn("2029", row["exact_locator"])
        self.assertEqual(row["data_recovered"], "NO")
        self.assertEqual(row["p42_quantity_authority"], "NO")
        self.assertIn("emitter-class distribution", row["notes"])

    def test_current_provider_registry_exacts_neer2_sample(self):
        with P46_ROUTES.open(encoding="utf-8", newline="") as handle:
            rows = {row["route_id"]: row for row in csv.DictReader(handle)}
        row = rows["NEER2_2000_BUILDING_CALIBRATION"]
        self.assertIn("realised N=2029", row["exact_locator"])
        self.assertEqual(row["p42_national_authority"], "NO")
        self.assertIn("no national radiator/surface-heating/fan-coil distribution", row["notes"])

    def test_source_pack_freezes_non_equivalences(self):
        text = SOURCE_PACK.read_text(encoding="utf-8")
        for boundary in (
            "NO FULL-POPULATION DATA != BLOCKER",
            "HEAT PRODUCER != HEAT EMITTER",
            "BOILER != RADIATOR",
            "HYDRONIC SYSTEM != DESIGN TEMPERATURE",
            "NON_DISTRICT_HYDRONIC_EMITTER_MIX + DESIGN_TEMPERATURE_DISTRIBUTION",
            "POPULATION ESTIMATE != RECORD PASS/FAIL",
        ):
            self.assertIn(boundary, text)

    def test_b02_module_status_uses_narrowed_population_blocker(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        note = rows["B02"]["gate_note"]
        self.assertIn("NON_DISTRICT_HYDRONIC_EMITTER_MIX", note)
        self.assertIn("DESIGN_TEMPERATURE_DISTRIBUTION", note)
        self.assertIn("2029", note)


if __name__ == "__main__":
    unittest.main()
