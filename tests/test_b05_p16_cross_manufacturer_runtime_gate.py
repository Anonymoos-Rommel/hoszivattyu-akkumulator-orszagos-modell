import csv
import unittest
from pathlib import Path

from modules.B05.part_load_runtime_contract import (
    CAPACITY_SHORTFALL,
    CONTINUOUS,
    CYCLING,
    MODULATION_FLOOR_REQUIRED,
    NUMERIC_CYCLING_METHOD_REQUIRED,
    OFF,
    classify_part_load_runtime,
    runtime_boundary,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b05_p16_bosch_keymark_partload.csv"
REG = ROOT / "registry" / "b05_p16_runtime_partload_contract.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P16_CROSS_MANUFACTURER_RUNTIME_GATE.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P16CrossManufacturerRuntimeGateTests(unittest.TestCase):
    def test_bosch_certified_rows_are_exact_and_nondefault(self):
        materialized = rows(DATA)
        self.assertEqual(len(materialized), 6)
        self.assertEqual(
            {row["application_temperature"] for row in materialized},
            {"low", "medium"},
        )
        self.assertEqual(
            {float(row["outdoor_temperature_C"]) for row in materialized},
            {2.0, 7.0, 12.0},
        )
        self.assertTrue(all(float(row["Cdh_Tj"]) != 0.9 for row in materialized))
        self.assertTrue(
            all(
                row["cdh_classification"]
                == "CERTIFIED_NONDEFAULT_MEASUREMENT_DETERMINED_CDH"
                for row in materialized
            )
        )

        by_key = {
            (row["application_temperature"], float(row["outdoor_temperature_C"])): row
            for row in materialized
        }
        expected = {
            ("low", 2.0): (4.31, 3.21, 0.99),
            ("low", 7.0): (2.64, 4.95, 0.97),
            ("low", 12.0): (1.82, 6.72, 0.95),
            ("medium", 2.0): (3.92, 2.12, 0.99),
            ("medium", 7.0): (2.41, 3.09, 0.98),
            ("medium", 12.0): (1.79, 5.01, 0.96),
        }
        for key, triple in expected.items():
            row = by_key[key]
            self.assertAlmostEqual(float(row["Pdh_kW"]), triple[0])
            self.assertAlmostEqual(float(row["COP_Tj"]), triple[1])
            self.assertAlmostEqual(float(row["Cdh_Tj"]), triple[2])

    def test_runtime_gate_fails_closed_without_modulation_floor(self):
        state = classify_part_load_runtime(1.0, 6.0, None)
        self.assertEqual(state.state, MODULATION_FLOOR_REQUIRED)
        self.assertFalse(state.cdh_evidence_can_be_considered)
        self.assertFalse(state.direct_numeric_cdh_application_allowed)
        self.assertEqual(
            state.residual_gap, "MULTI_PRODUCT_MIN_MODULATION_COVERAGE_REQUIRED"
        )

    def test_continuous_and_cycling_state_ordering(self):
        continuous = classify_part_load_runtime(3.0, 6.0, 2.0)
        self.assertEqual(continuous.state, CONTINUOUS)
        self.assertAlmostEqual(continuous.load_ratio, 0.5)
        self.assertAlmostEqual(continuous.minimum_continuous_load_ratio, 1 / 3)
        self.assertFalse(continuous.cdh_evidence_can_be_considered)

        cycling = classify_part_load_runtime(1.0, 6.0, 2.0)
        self.assertEqual(cycling.state, CYCLING)
        self.assertTrue(cycling.cdh_evidence_can_be_considered)
        self.assertFalse(cycling.direct_numeric_cdh_application_allowed)
        self.assertEqual(cycling.residual_gap, NUMERIC_CYCLING_METHOD_REQUIRED)

    def test_off_and_capacity_shortfall_do_not_apply_cdh(self):
        off = classify_part_load_runtime(0.0, 6.0, 2.0)
        self.assertEqual(off.state, OFF)
        self.assertFalse(off.cdh_evidence_can_be_considered)

        short = classify_part_load_runtime(7.0, 6.0, 2.0)
        self.assertEqual(short.state, CAPACITY_SHORTFALL)
        self.assertFalse(short.cdh_evidence_can_be_considered)

    def test_cross_manufacturer_residual_is_resolved_but_q_remains_open(self):
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            reg["CROSS_MANUFACTURER_PART_LOAD_VALIDATION_REQUIRED"]["status"],
            "RESOLVED_FOR_TWO_CERTIFIED_MANUFACTURERS",
        )
        self.assertEqual(
            reg["CDH_TO_B05_RUNTIME_APPLICATION_CONTRACT_REQUIRED"]["status"],
            "NARROWED_TO_NUMERIC_METHOD_AUTHORITY",
        )
        self.assertEqual(
            reg["Q-B05-004"]["status"],
            "OPEN_NARROWED_TO_MIN_MOD_COVERAGE_AND_NUMERIC_CYCLING_METHOD",
        )
        self.assertNotIn(
            "CROSS_MANUFACTURER_PART_LOAD_VALIDATION_REQUIRED",
            reg["Q-B05-004"]["residual_gap"],
        )
        self.assertIn(
            "CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED",
            reg["Q-B05-004"]["residual_gap"],
        )

    def test_live_registry_and_readiness_keep_fail_closed_boundary(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        self.assertIn("SRC-B05-HPKEYMARK-BOSCH-CS5800I-2026", sources)
        self.assertIn("SRC-B05-UK-HEM-TP12-2026", sources)

        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-CDH-MEASURED"]["status"], "OBS")
        self.assertEqual(variables["VAR-B05-CYCLING-PENALTY-RUNTIME"]["status"], "Q")

        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(
            readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45"
        )

        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        self.assertEqual(questions["Q-B05-004"]["status"], "OPEN")
        self.assertIn("B05-P16", questions["Q-B05-004"]["notes"])
        self.assertIn(
            "OPEN_NARROWED_TO_MIN_MOD_COVERAGE_AND_NUMERIC_CYCLING_METHOD",
            questions["Q-B05-004"]["notes"],
        )

    def test_document_and_contract_forbid_direct_multiplier(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("CERTIFIED CDH != DIRECT HOURLY MULTIPLIER", text)
        self.assertIn("CYCLING STATE != NUMERIC CYCLING ENERGY CORRECTION", text)
        self.assertIn("B05 remains **64%**", text)
        self.assertIn("NO_COP_TIMES_CDH_SHORTCUT", runtime_boundary())


if __name__ == "__main__":
    unittest.main()
