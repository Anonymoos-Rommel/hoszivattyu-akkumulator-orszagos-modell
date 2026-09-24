import csv
import unittest
from pathlib import Path

from modules.B05.defrost_accounting_contract import (
    ACCOUNTING_Q,
    DEFROST_EXCLUDED,
    EN14511,
    EXPLICIT_EXCLUSION,
    NO_EXTRA_UNIVERSAL_PENALTY,
    RUNTIME_Q,
    UNKNOWN,
    decide_defrost_accounting,
    point_test_basis,
)


ROOT = Path(__file__).resolve().parents[1]
POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"
APPLICABILITY = ROOT / "data" / "processed" / "b05_p14_defrost_point_applicability.csv"
REG = ROOT / "registry" / "b05_p14_en14511_defrost_accounting_boundary.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P14_EN14511_DEFROST_ACCOUNTING_BOUNDARY.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P14EN14511DefrostAccountingTests(unittest.TestCase):
    def test_en14511_policy_forbids_second_universal_penalty(self):
        decision = decide_defrost_accounting(EN14511)
        self.assertEqual(decision.point_accounting_status, NO_EXTRA_UNIVERSAL_PENALTY)
        self.assertFalse(decision.extra_universal_penalty_allowed)
        self.assertEqual(decision.runtime_model_status, RUNTIME_Q)

    def test_explicit_exclusion_and_unknown_remain_fail_closed(self):
        excluded = decide_defrost_accounting(EXPLICIT_EXCLUSION)
        self.assertEqual(excluded.point_accounting_status, DEFROST_EXCLUDED)
        self.assertFalse(excluded.extra_universal_penalty_allowed)

        unknown = decide_defrost_accounting(UNKNOWN)
        self.assertEqual(unknown.point_accounting_status, ACCOUNTING_Q)
        self.assertFalse(unknown.extra_universal_penalty_allowed)
        self.assertEqual(unknown.runtime_model_status, RUNTIME_Q)

    def test_current_canonical_en14511_tagged_point_count_is_exact(self):
        point_rows = rows(POINTS)
        tagged = [
            row for row in point_rows
            if point_test_basis(row["test_standard"]) == EN14511
        ]
        self.assertEqual(len(tagged), 36)
        self.assertEqual(
            {row["source_id"] for row in tagged},
            {
                "SRC-B05-VAILLANT-AROTHERM-SPLIT-2019",
                "SRC-B05-VAILLANT-AROTHERM-PLUS-2020",
                "SRC-B05-STIEBEL-HPA-O-CS-PLUS-2022",
                "SRC-B05-STIEBEL-HPA-O-P4-COLD-2025",
                "SRC-B05-WAMAK-AWK35-EVI-2026",
            },
        )

    def test_applicability_keeps_nibe_exclusion_and_unknown_sources_separate(self):
        applicability = {row["source_id"]: row for row in rows(APPLICABILITY)}
        self.assertEqual(
            applicability["SRC-B05-NIBE-S2125-IHB"]["test_basis_status"],
            "EXPLICIT_DEFROST_EXCLUSION",
        )
        for source_id in (
            "SRC-B05-TEKNOPOINT-ATHENA-R32-2025",
            "SRC-B05-ECPOWER-PMH-2023",
        ):
            self.assertEqual(
                applicability[source_id]["test_basis_status"],
                "TEST_BASIS_NOT_EXPLICITLY_BOUND",
            )
            self.assertEqual(applicability[source_id]["defrost_accounting_policy"], "Q")

    def test_registry_narrows_q_b05_003_but_does_not_close_runtime_model(self):
        registry = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            registry["EN14511_EFFECTIVE_INPUT_DEFROST_BOUNDARY"]["status"],
            "QUALIFIED_STANDARD_METHOD",
        )
        self.assertEqual(
            registry["EN14511_EXTRA_UNIVERSAL_DEFROST_PENALTY"]["status"],
            "FORBIDDEN",
        )
        self.assertEqual(
            registry["WEATHER_DRIVEN_DEFROST_RUNTIME_MODEL"]["status"],
            "OPEN",
        )
        self.assertEqual(
            registry["Q-B05-003"]["status"],
            "OPEN_NARROWED_TO_WEATHER_DRIVEN_RUNTIME_MODEL",
        )

    def test_live_variable_boundary_is_qualified_while_runtime_penalty_stays_q(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(
            variables["VAR-B05-DEFROST-ACCOUNTING-BOUNDARY"]["status"],
            "DER",
        )
        self.assertEqual(
            variables["VAR-B05-DEFROST-RUNTIME-PENALTY"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-DEFROST-MODEL-STATUS"]["status"],
            "Q",
        )

    def test_live_question_and_readiness_do_not_mint_uplift(self):
        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        q = questions["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("OPEN_NARROWED_TO_WEATHER_DRIVEN_RUNTIME_MODEL", q["notes"])
        self.assertIn("B05-P14", q["notes"])

        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(readiness["DEFROST"]["status"], "Q")
        self.assertEqual(readiness["DEFROST"]["readiness_percent"], "5")

    def test_document_preserves_double_count_and_runtime_boundaries(self):
        text = PACK.read_text(encoding="utf-8")
        for phrase in (
            "EN 14511 POINT ACCOUNTING != WEATHER-DRIVEN DEFROST RUNTIME MODEL",
            "NO EXTRA UNIVERSAL PENALTY != ZERO REAL-WORLD DEFROST LOSS",
            "MANUFACTURER DESIGN ALLOWANCE != HUNGARIAN RUNTIME OBSERVATION",
            "B05 remains **64%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
