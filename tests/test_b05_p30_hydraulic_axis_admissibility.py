import csv
import unittest
from pathlib import Path

from modules.B05.hydraulic_axis_admissibility import (
    ADMITTED,
    DELTA_T,
    DOUBLE_COUNT,
    FIXED_ONLY,
    NO_VALUES,
    RETURN_TEMPERATURE,
    HydraulicPerformancePoint,
    assess_hydraulic_axis,
    p30_boundary,
    validate_axis_selection,
)

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
REG = ROOT / "registry" / "b05_p30_hydraulic_axis_admissibility.csv"
SNAPSHOT = ROOT / "data" / "processed" / "b05_p30_hydraulic_axis_snapshot.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P30_HYDRAULIC_AXIS_ADMISSIBILITY.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def point(
    return_c=None,
    delta_k=None,
    *,
    outdoor=7.0,
    supply=35.0,
    capacity=5.0,
    electrical=1.0,
    cop=5.0,
):
    return HydraulicPerformancePoint(
        "PRODUCT-X",
        outdoor,
        supply,
        capacity,
        electrical,
        cop,
        return_temperature_c=return_c,
        delta_temperature_c=delta_k,
        source_id="SRC-X",
    )


class B05P30HydraulicAxisAdmissibilityTests(unittest.TestCase):
    def test_absent_axis_values_fail_closed(self):
        decision = assess_hydraulic_axis([point()], RETURN_TEMPERATURE)
        self.assertEqual(decision.status, NO_VALUES)
        self.assertFalse(decision.admissible)

    def test_fixed_test_condition_is_not_performance_axis(self):
        points = [
            point(return_c=30.0, outdoor=7.0, supply=35.0),
            point(return_c=40.0, outdoor=7.0, supply=45.0),
        ]
        decision = assess_hydraulic_axis(points, RETURN_TEMPERATURE)
        self.assertEqual(decision.status, FIXED_ONLY)
        self.assertFalse(decision.admissible)

    def test_source_native_matched_return_variation_is_admissible(self):
        points = [
            point(return_c=30.0, capacity=5.0, electrical=1.0, cop=5.0),
            point(return_c=28.0, capacity=4.8, electrical=1.0, cop=4.8),
        ]
        decision = assess_hydraulic_axis(points, RETURN_TEMPERATURE)
        self.assertEqual(decision.status, ADMITTED)
        self.assertTrue(decision.admissible)
        self.assertEqual(decision.qualifying_matched_coordinates, 1)

    def test_source_native_matched_delta_t_variation_is_admissible(self):
        points = [
            point(delta_k=5.0, capacity=5.0, electrical=1.0, cop=5.0),
            point(delta_k=7.0, capacity=4.7, electrical=1.0, cop=4.7),
        ]
        decision = assess_hydraulic_axis(points, DELTA_T)
        self.assertEqual(decision.status, ADMITTED)
        self.assertTrue(decision.admissible)

    def test_return_and_delta_t_cannot_be_double_counted_with_supply(self):
        self.assertEqual(
            validate_axis_selection(use_return_axis=True, use_delta_t_axis=True),
            DOUBLE_COUNT,
        )
        self.assertIn("NOT_TWO_INDEPENDENT_AXES", p30_boundary())

    def test_q_b05_006_is_resolved_as_contract_not_numeric_surface(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-006"]
        self.assertEqual(q["status"], "RESOLVED")
        self.assertIn("B05-P30 RESOLVED_CONTRACT", q["notes"])
        self.assertIn("53 OBS/DER", q["notes"])
        self.assertIn("Current V1 therefore remains outdoor x supply", q["notes"])

    def test_p30_snapshot_is_historical_and_zero_axis_coverage(self):
        snap = rows(SNAPSHOT)
        total = next(r for r in snap if r["equipment_id"] == "__TOTAL__")
        self.assertEqual(total["obs_der_point_count"], "53")
        self.assertEqual(total["return_temperature_nonblank_count"], "0")
        self.assertEqual(total["delta_temperature_nonblank_count"], "0")
        self.assertEqual(len([r for r in snap if r["equipment_id"] != "__TOTAL__"]), 11)

    def test_variables_and_readiness_preserve_current_v1(self):
        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-RETURN-TEMPERATURE"]["status"], "Q")
        self.assertEqual(variables["VAR-B05-DELTA-TEMPERATURE"]["status"], "Q")
        self.assertEqual(variables["VAR-B05-HYDRAULIC-PERFORMANCE-AXIS-STATUS"]["status"], "DER")

        readiness = {r["component_id"]: r for r in rows(READINESS)}["PERFORMANCE_MAP"]
        self.assertEqual(readiness["readiness_percent"], "80")
        self.assertIn("P30", readiness["notes"])
        self.assertIn("B05 remains 64%", readiness["notes"])

    def test_sources_and_docs_are_pinned(self):
        sources = {r["source_id"]: r for r in rows(SOURCES)}
        for sid in (
            "SRC-B05-DIMPLEX-LA2030CP-HYDRAULIC-TEST-CONDITIONS-2026",
            "SRC-B05-MITSUBISHI-WM50-FLOW-RETURN-INSTRUMENTATION-2026",
        ):
            self.assertIn(sid, sources)
            self.assertEqual(sources[sid]["retrieved_at"], "2026-09-25")

        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(reg["Q-B05-006"]["status"], "RESOLVED_CONTRACT")
        self.assertEqual(
            reg["RETURN_AND_DELTA_T_SIMULTANEOUS_INDEPENDENCE"]["status"],
            "FORBIDDEN_WITH_SUPPLY_RETAINED",
        )
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("FIXED TEST CONDITION / SENSOR / OPERATING LIMIT", text)
        self.assertIn("PERFORMANCE_MAP: 80% -> 80%", text)
        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P30 resolves Q-B05-006", readme)


if __name__ == "__main__":
    unittest.main()
