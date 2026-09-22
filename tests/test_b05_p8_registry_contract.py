import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p8_extreme_weather_return_period.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
PROFILES = ROOT / "data" / "processed" / "heat_pump_weather_profiles.csv"
DOC = ROOT / "docs" / "source_packs" / "B05_P8_EMPIRICAL_COLD_RETURN_PERIOD.md"
TOOL = ROOT / "tools" / "materialize_b05_extreme_weather.py"


class B05P8RegistryContractTests(unittest.TestCase):
    def test_current_repository_state_remains_numeric_q(self):
        with REG.open(encoding="utf-8", newline="") as handle:
            rows = {row["item_id"]: row for row in csv.DictReader(handle)}
        current = rows["B05-P8-R06"]
        self.assertEqual(current["status"], "NO_MULTIYEAR_BLOCK_SERIES")
        self.assertEqual(current["lower_bound"], "0")
        self.assertEqual(current["upper_bound"], "0")
        self.assertEqual(current["evidence_status"], "Q")

        q = rows["B05-P8-R10"]
        self.assertEqual(q["status"], "OPEN_NARROWED")
        self.assertIn(
            "EXTERNAL_RAW_ARCHIVE_REACQUISITION",
            q["residual_gap"],
        )

    def test_cold_subgate_is_method_ready_but_module_readiness_not_inflated(self):
        with READINESS.open(encoding="utf-8", newline="") as handle:
            readiness = {row["component_id"]: row for row in csv.DictReader(handle)}
        cold = readiness["COLD_1_IN_10"]
        self.assertEqual(cold["status"], "PARTIAL")
        self.assertEqual(cold["readiness_percent"], "35")
        self.assertIn("not an official HungaroMet 1-in-10", cold["notes"])

        with MODULES.open(encoding="utf-8", newline="") as handle:
            modules = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(modules["B05"]["readiness_percent"], "64")
        self.assertIn("B05-P8", modules["B05"]["gate_note"])

    def test_open_question_is_narrowed_without_false_resolution(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        q = questions["Q-B05-002"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("OPEN_NARROWED", q["notes"])
        self.assertIn(
            "PROJECT-DERIVED EMPIRICAL RETURN PERIOD != OFFICIAL HUNGAROMET 1-IN-10",
            q["notes"],
        )

    def test_existing_profiles_do_not_form_multiyear_winter_series(self):
        with PROFILES.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        reference = [row for row in rows if row["profile_type"] == "OBSERVED_REFERENCE_YEAR"]
        extreme = [
            row for row in rows
            if row["profile_type"] == "OBSERVED_EXTREME_COLD_SPELL"
        ]
        self.assertEqual(len(reference), 5)
        self.assertEqual({row["period_start_utc"] for row in reference}, {"2025-01-01T00:00:00Z"})
        self.assertEqual({row["period_end_utc"] for row in reference}, {"2025-12-31T23:00:00Z"})
        self.assertEqual(len(extreme), 1)
        self.assertIn("-14.286 C", extreme[0]["notes"])

    def test_document_and_materializer_preserve_nonpromotion_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "PROJECT-DERIVED EMPIRICAL RETURN PERIOD != OFFICIAL HUNGAROMET 1-IN-10",
            "MULTI-STATION ENVELOPE != NATIONAL RETURN PERIOD",
            "B05 module readiness remains **64%**",
        ):
            self.assertIn(phrase, text)
        self.assertTrue(TOOL.exists())


if __name__ == "__main__":
    unittest.main()
