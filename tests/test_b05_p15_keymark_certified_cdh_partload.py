import csv
import unittest
from pathlib import Path

from modules.B05.part_load_degradation_contract import (
    EXACT_DEFAULT,
    NONDEFAULT,
    classify_certified_cdh,
    runtime_boundary,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b05_p15_vaillant_keymark_partload.csv"
REG = ROOT / "registry" / "b05_p15_keymark_certified_cdh_partload.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P15_KEYMARK_CERTIFIED_CDH_PARTLOAD.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P15KeymarkCertifiedCdhPartLoadTests(unittest.TestCase):
    def test_nondefault_cdh_classification_and_default_ambiguity(self):
        for value in (0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0):
            c = classify_certified_cdh(value)
            self.assertEqual(c.classification, NONDEFAULT)
            self.assertTrue(c.usable_as_product_specific_nondefault_evidence)
            self.assertFalse(c.usable_as_direct_hourly_runtime_multiplier)

        d = classify_certified_cdh(0.9)
        self.assertEqual(d.classification, EXACT_DEFAULT)
        self.assertFalse(d.usable_as_product_specific_nondefault_evidence)

    def test_materialized_vaillant_rows_are_exact_and_nondefault(self):
        materialized = rows(DATA)
        self.assertEqual(len(materialized), 8)
        self.assertEqual(
            {row["application_temperature"] for row in materialized},
            {"low", "medium"},
        )
        self.assertEqual(
            {float(row["outdoor_temperature_C"]) for row in materialized},
            {-7.0, 2.0, 7.0, 12.0},
        )
        self.assertTrue(all(float(row["Cdh_Tj"]) != 0.9 for row in materialized))
        self.assertTrue(
            all(
                row["cdh_classification"]
                == "CERTIFIED_NONDEFAULT_MEASUREMENT_DETERMINED_CDH"
                for row in materialized
            )
        )

    def test_exact_average_climate_values(self):
        by_key = {
            (row["application_temperature"], float(row["outdoor_temperature_C"])): row
            for row in rows(DATA)
        }
        expected = {
            ("low", -7.0): (6.38, 2.93, 0.99),
            ("low", 2.0): (3.83, 4.73, 0.97),
            ("low", 7.0): (3.21, 6.33, 0.95),
            ("low", 12.0): (3.72, 7.79, 0.94),
            ("medium", -7.0): (5.66, 2.17, 0.99),
            ("medium", 2.0): (3.49, 3.32, 0.97),
            ("medium", 7.0): (3.06, 4.67, 0.96),
            ("medium", 12.0): (3.62, 6.23, 0.95),
        }
        for key, triple in expected.items():
            row = by_key[key]
            self.assertAlmostEqual(float(row["Pdh_kW"]), triple[0])
            self.assertAlmostEqual(float(row["COP_Tj"]), triple[1])
            self.assertAlmostEqual(float(row["Cdh_Tj"]), triple[2])

    def test_registry_resolves_product_cdh_branch_only(self):
        registry = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            registry["PRODUCT_SPECIFIC_CDH_EVIDENCE_REQUIRED"]["status"],
            "RESOLVED_FOR_ADMITTED_PRODUCT",
        )
        self.assertEqual(
            registry["Q-B05-004"]["status"],
            "OPEN_NARROWED_TO_RUNTIME_APPLICATION_AND_MODULATION_COVERAGE",
        )
        self.assertIn(
            "CDH_TO_B05_RUNTIME_APPLICATION_CONTRACT_REQUIRED",
            registry["Q-B05-004"]["residual_gap"],
        )

    def test_live_variable_is_product_specific_evidence_not_runtime_formula(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-CDH-MEASURED"]["status"], "OBS")
        self.assertEqual(variables["VAR-B05-CYCLING-PENALTY-RUNTIME"]["status"], "Q")

    def test_readiness_not_minted_and_live_question_stays_open(self):
        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(
            readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45"
        )
        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        self.assertEqual(questions["Q-B05-004"]["status"], "OPEN")
        self.assertIn("B05-P15", questions["Q-B05-004"]["notes"])
        self.assertIn(
            "OPEN_NARROWED_TO_RUNTIME_APPLICATION_AND_MODULATION_COVERAGE",
            questions["Q-B05-004"]["notes"],
        )

    def test_sources_and_document_boundaries(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        self.assertIn("SRC-B05-EN14825-CDH-2022", sources)
        self.assertIn("SRC-B05-HPKEYMARK-VAILLANT-PLUS-M-2026", sources)
        self.assertIn("CERTIFIED_CDH_NOT_DIRECT_HOURLY_MULTIPLIER", runtime_boundary())

        text = PACK.read_text(encoding="utf-8")
        for phrase in (
            "CERTIFIED NON-DEFAULT CDH != REGULATORY DEFAULT 0.9",
            "CERTIFIED CDH FIELD != INDEPENDENT RAW LAB MEASUREMENT AT EACH TJ",
            "Pdh != MINIMUM_STABLE_MODULATION",
            "B05 remains **64%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
