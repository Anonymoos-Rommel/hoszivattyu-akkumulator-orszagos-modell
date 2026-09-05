from pathlib import Path
import csv
import unittest


ROOT = Path(__file__).resolve().parents[1]
VARIABLES = ROOT / "registry/variables.csv"
ROLLOUT = ROOT / "registry/b01_national_rollout_policy_contract.csv"
DOC = ROOT / "docs/source_packs/B01_P4_CANONICAL_TARGET_VARIABLE_HARMONIZATION.md"


class B01P4CanonicalTargetVariableHarmonizationTests(unittest.TestCase):
    def test_global_target_variable_has_no_numeric_default_or_ceiling(self):
        with VARIABLES.open(encoding="utf-8", newline="") as handle:
            rows = [
                row
                for row in csv.DictReader(handle)
                if row["variable_id"] == "VAR-B01-TARGET-HOUSEHOLDS"
            ]

        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("household", row["unit"])
        self.assertEqual("", row["default_value"])
        self.assertEqual("0", row["min_value"])
        self.assertEqual("", row["max_value"])
        self.assertEqual("Q", row["status"])
        self.assertEqual("2026-09-05", row["updated_at"])
        self.assertIn("2 000 000", row["notes"])
        self.assertIn("2 500 000", row["notes"])
        self.assertIn("3 389 817", row["notes"])

    def test_rollout_contract_preserves_legacy_value_but_keeps_target_unset(self):
        with ROLLOUT.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("2000000", row["legacy_original_hypothesis_households"])
        self.assertEqual("3389817", row["exact_non_district_heated_occupied_dwellings_2022"])
        self.assertEqual("DER_FROM_OBS_WBL011_CELLS", row["exact_population_status"])
        self.assertEqual("", row["canonical_programme_target_households"])
        self.assertEqual("Q", row["canonical_programme_target_status"])

    def test_document_freezes_no_hidden_target_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "LEGACY TARGET HYPOTHESIS != PHYSICAL POPULATION REFERENCE != TECHNICALLY ELIGIBLE STOCK != PROGRAMME TARGET",
            "default_value = <blank>",
            "max_value = <blank>",
            "3,389,817",
            "must not substitute",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
