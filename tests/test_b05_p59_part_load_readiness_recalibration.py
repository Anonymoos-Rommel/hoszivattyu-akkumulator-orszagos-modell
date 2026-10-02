import csv
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from tests.b05_readiness_assertions import assert_part_load_readiness_unassessed
from modules.B05 import part_load_readiness_recalibration as readiness_contract
from modules.B05.part_load_readiness_recalibration import (
    GATES,
    HISTORICAL_GATE_CREDITS,
    HISTORICAL_READINESS_SCORE,
    READINESS_SCORE,
    READINESS_STATUS,
    SUPPORTED_EARNED_SUBTOTAL,
    TOTAL_WEIGHT,
    UNASSESSED_GATE_ID,
    UNASSESSED_WEIGHT,
    ReadinessGate,
    open_gate_ids,
    unresolved_gate_ids,
    validate_scorecard,
)
from tools.validate_registry import validate_b05_readiness_row

ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
SCORECARD = ROOT / "registry" / "b05_p59_part_load_readiness_scorecard.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def unassessed_row():
    return {
        "component_id": "PART_LOAD_MODULATION",
        "status": "Q",
        "readiness_percent": "",
        "notes": (
            "CURRENT_SCORE_UNASSESSED; HISTORICAL_P59_SCORE=75; "
            "SUPPORTED_UNAFFECTED_SUBTOTAL=67; UNASSESSED_GATE_WEIGHT=8; "
            "UNASSESSED_GATE=EN14825_STANDARD_BIN_CYCLING_METHOD;"
        ),
    }


class B05P59PartLoadReadinessRecalibrationTests(unittest.TestCase):
    def test_current_total_is_unassessed_and_not_the_supported_subtotal(self):
        validate_scorecard()
        self.assertEqual(100, TOTAL_WEIGHT)
        self.assertEqual(75, HISTORICAL_READINESS_SCORE)
        self.assertEqual(67, SUPPORTED_EARNED_SUBTOTAL)
        self.assertEqual(8, UNASSESSED_WEIGHT)
        self.assertIsNone(READINESS_SCORE)
        self.assertEqual("Q", READINESS_STATUS)
        self.assertEqual(12, len(GATES))

    def test_original_criteria_weights_and_unaffected_points_are_preserved(self):
        self.assertEqual(
            (
                ("SOURCE_NATIVE_MINIMUM_MODULATION_SURFACES", 14, 14),
                ("POINT_PAIRED_MINIMUM_CAPACITY_COP", 8, 8),
                ("MULTI_MANUFACTURER_BOUNDED_PRODUCT_EVIDENCE", 8, 8),
                ("CERTIFIED_PART_LOAD_CDH_EVIDENCE", 10, 10),
                ("EN14825_STANDARD_BIN_CYCLING_METHOD", 8, None),
                ("HOURLY_CYCLING_METHOD_SEPARATION", 8, 8),
                ("EXPLICIT_BOUNDED_DEFAULT_RUNTIME_POLICY", 6, 6),
                ("COLD_HIGH_SUPPLY_COORDINATE_COVERAGE", 8, 5),
                ("DIRECT_FIELD_CYCLING_MODULATION_VALIDATION", 8, 5),
                ("EXACT_FCU_TRANSIENT_PHYSICS_AND_DIRECT_RUNTIME", 8, 3),
                ("PRODUCT_SPECIFIC_HEAT_PUMP_TRANSIENT_AUTHORITY", 8, 0),
                ("EXACT_FCC06_OBS_TRANSIENT_MASS_BINDING", 6, 0),
            ),
            tuple((g.gate_id, g.weight, g.earned) for g in GATES),
        )
        self.assertEqual((8, 8), HISTORICAL_GATE_CREDITS[UNASSESSED_GATE_ID])
        gate = next(g for g in GATES if g.gate_id == UNASSESSED_GATE_ID)
        self.assertEqual("UNASSESSED", gate.status)
        self.assertEqual(
            "EXACT_FIXED_WATER_MINIMUM_POINT_TO_CERTIFIED_CDH_PHYSICAL_JOIN_REQUIRED",
            gate.residual,
        )

    def test_open_zero_credit_gates_remain_distinct_from_unassessed_credit(self):
        self.assertEqual(
            (
                "PRODUCT_SPECIFIC_HEAT_PUMP_TRANSIENT_AUTHORITY",
                "EXACT_FCC06_OBS_TRANSIENT_MASS_BINDING",
            ),
            open_gate_ids(),
        )
        self.assertIn(UNASSESSED_GATE_ID, unresolved_gate_ids())
        self.assertIn("COLD_HIGH_SUPPLY_COORDINATE_COVERAGE", unresolved_gate_ids())
        self.assertIn("DIRECT_FIELD_CYCLING_MODULATION_VALIDATION", unresolved_gate_ids())

    def test_unassessed_gate_requires_null_credit_and_explicit_residual(self):
        for earned, status, residual in (
            (None, "RESOLVED", ""),
            (None, "PARTIAL", "debt"),
            (None, "OPEN", "debt"),
            (8, "UNASSESSED", "debt"),
            (0, "UNASSESSED", "debt"),
            (None, "UNASSESSED", ""),
            (-1, "PARTIAL", "debt"),
            (9, "PARTIAL", "debt"),
        ):
            with self.subTest(earned=earned, status=status, residual=residual):
                with self.assertRaises(ValueError):
                    ReadinessGate("EXAMPLE", 8, earned, status, residual).validate()

    def test_validator_rejects_offsetting_weight_or_credit_changes_and_criterion_renaming(self):
        variants = []
        altered = list(GATES)
        altered[7] = replace(altered[7], earned=4)
        altered[8] = replace(altered[8], earned=6)
        variants.append(altered)
        altered = list(GATES)
        altered[7] = replace(altered[7], weight=7)
        altered[8] = replace(altered[8], weight=9)
        variants.append(altered)
        altered = list(GATES)
        altered[4] = replace(altered[4], gate_id="CONDITIONAL_CYCLING_MATHEMATICS")
        variants.append(altered)
        for credit in (0, 4, 8):
            altered = list(GATES)
            altered[4] = replace(altered[4], earned=credit, status="PARTIAL")
            variants.append(altered)
        for gates in variants:
            with self.subTest(gates=gates), patch.object(readiness_contract, "GATES", tuple(gates)):
                with self.assertRaises(ValueError):
                    validate_scorecard()

    def test_validator_rejects_replacement_numeric_total_or_changed_historical_score(self):
        for field, value in (
            ("READINESS_SCORE", 67),
            ("READINESS_SCORE", 75),
            ("READINESS_STATUS", "PARTIAL"),
            ("HISTORICAL_READINESS_SCORE", 67),
            ("SUPPORTED_EARNED_SUBTOTAL", 75),
            ("UNASSESSED_WEIGHT", 0),
        ):
            with self.subTest(field=field, value=value), patch.object(readiness_contract, field, value):
                with self.assertRaises(ValueError):
                    validate_scorecard()

    def test_registry_scorecard_matches_every_gate_and_preserves_history(self):
        materialized = rows(SCORECARD)
        scorecard = {r["gate_id"]: r for r in materialized}
        self.assertEqual(13, len(materialized))
        self.assertEqual({g.gate_id for g in GATES} | {"TOTAL"}, set(scorecard))
        for gate in GATES:
            row = scorecard[gate.gate_id]
            with self.subTest(gate=gate.gate_id):
                self.assertEqual(str(gate.weight), row["weight"])
                self.assertEqual("" if gate.earned is None else str(gate.earned), row["earned"])
                self.assertEqual(str(HISTORICAL_GATE_CREDITS[gate.gate_id][1]), row["historical_earned"])
                self.assertEqual(gate.status, row["status"])
                self.assertEqual(gate.residual, row["residual"])
        self.assertEqual("100", scorecard["TOTAL"]["weight"])
        self.assertEqual("", scorecard["TOTAL"]["earned"])
        self.assertEqual("75", scorecard["TOTAL"]["historical_earned"])
        self.assertEqual("Q", scorecard["TOTAL"]["status"])
        self.assertEqual(UNASSESSED_GATE_ID, scorecard["TOTAL"]["residual"])
        self.assertIn("SUPPORTED_UNAFFECTED_SUBTOTAL=67", scorecard["TOTAL"]["notes"])
        self.assertIn("UNASSESSED_GATE_WEIGHT=8", scorecard["TOTAL"]["notes"])
        self.assertEqual("P18;P20;P22-P23", scorecard[UNASSESSED_GATE_ID]["evidence_basis"])
        self.assertTrue(scorecard[UNASSESSED_GATE_ID]["notes"].startswith(
            "The to-water standard-bin cycling equation is executable with same-point COP/capacity and exact certified Cdh."
        ))

    def test_part_load_component_is_explicitly_unassessed(self):
        ready = {r["component_id"]: r for r in rows(READINESS)}
        row = ready["PART_LOAD_MODULATION"]
        assert_part_load_readiness_unassessed(self, row)
        errors = []
        validate_b05_readiness_row(errors, row)
        self.assertEqual([], errors)
        self.assertIn("P59", row["notes"])
        self.assertIn(
            "EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED",
            row["notes"],
        )

    def test_registry_validator_accepts_only_explicit_null_contract_for_part_load(self):
        errors = []
        validate_b05_readiness_row(errors, unassessed_row())
        self.assertEqual([], errors)
        for status, value in (("PARTIAL", ""), ("Q", "75"), ("Q", "67"), ("Q", "0"), ("Q", "Q"), ("Q", " ")):
            with self.subTest(status=status, value=value):
                row = dict(unassessed_row(), status=status, readiness_percent=value)
                errors = []
                validate_b05_readiness_row(errors, row)
                self.assertTrue(errors)
        for old, new in (("HISTORICAL_P59_SCORE=75", "HISTORICAL_P59_SCORE=750"), ("CURRENT_SCORE_UNASSESSED", "")):
            row = unassessed_row()
            row["notes"] = row["notes"].replace(old, new)
            errors = []
            validate_b05_readiness_row(errors, row)
            self.assertTrue(errors)

    def test_registry_validator_keeps_numeric_contract_for_other_b05_components(self):
        for component in ("DEFROST", "COLD_1_IN_10", "OTHER_COMPONENT"):
            for value in ("", "Q", "None", "NaN", "inf", "67.0", "-1", "101"):
                with self.subTest(component=component, value=value):
                    row = dict(unassessed_row(), component_id=component, readiness_percent=value)
                    errors = []
                    validate_b05_readiness_row(errors, row)
                    self.assertTrue(errors)
            for value in ("0", "65", "100"):
                with self.subTest(component=component, value=value):
                    row = dict(unassessed_row(), component_id=component, status="PARTIAL", readiness_percent=value)
                    errors = []
                    validate_b05_readiness_row(errors, row)
                    self.assertEqual([], errors)

    def test_b05_module_readiness_is_not_mechanically_changed(self):
        modules = {r["module_id"]: r for r in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])
        self.assertIn("P59", modules["B05"]["gate_note"])

    def test_q_b05_004_remains_open_e2_validation_debt(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual("OPEN", q["status"])
        self.assertIn("B05-P59", q["notes"])
        audit = {r["blocker_id"]: r for r in rows(AUDIT)}["Q-B05-004"]
        self.assertEqual("E2", audit["evidence_tier"])
        self.assertEqual("VALIDATION_BLOCKER", audit["blocker_class"])
        self.assertEqual("MODEL_CONTINUE", audit["canonical_use"])
        self.assertIn(
            "EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING",
            audit["validation_debt"],
        )


if __name__ == "__main__":
    unittest.main()
