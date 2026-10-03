"""Shared assertions for the current unassessed PART_LOAD_MODULATION score."""

from modules.B05.part_load_readiness_recalibration import (
    GATES,
    HISTORICAL_READINESS_SCORE,
    READINESS_SCORE,
    READINESS_STATUS,
    SUPPORTED_EARNED_SUBTOTAL,
    UNASSESSED_GATE_ID,
    UNASSESSED_WEIGHT,
)


def assert_part_load_readiness_unassessed(case, row):
    """Preserve current Q, supported credit, and historical score separately."""
    case.assertEqual("PART_LOAD_MODULATION", row["component_id"])
    case.assertEqual("Q", row["status"])
    case.assertEqual("", row["readiness_percent"])
    case.assertIsNone(READINESS_SCORE)
    case.assertEqual("Q", READINESS_STATUS)
    case.assertEqual(75, HISTORICAL_READINESS_SCORE)
    case.assertEqual(67, SUPPORTED_EARNED_SUBTOTAL)
    case.assertEqual(8, UNASSESSED_WEIGHT)
    case.assertEqual("EN14825_STANDARD_BIN_CYCLING_METHOD", UNASSESSED_GATE_ID)
    gate = next(g for g in GATES if g.gate_id == UNASSESSED_GATE_ID)
    case.assertEqual(8, gate.weight)
    case.assertIsNone(gate.earned)
    case.assertEqual("UNASSESSED", gate.status)
    markers = {part.strip().rstrip(".") for part in row["notes"].split(";")}
    for marker in (
        "CURRENT_SCORE_UNASSESSED",
        "HISTORICAL_P59_SCORE=75",
        "SUPPORTED_UNAFFECTED_SUBTOTAL=67",
        "UNASSESSED_GATE_WEIGHT=8",
        "UNASSESSED_GATE=EN14825_STANDARD_BIN_CYCLING_METHOD",
    ):
        case.assertIn(marker, markers)
