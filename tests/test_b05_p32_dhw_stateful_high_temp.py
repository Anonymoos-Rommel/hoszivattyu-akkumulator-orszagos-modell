import csv
import unittest
from pathlib import Path

from modules.B05.dhw_stateful_high_temp import (
    MAX_LEVEL,
    MIN_LEVEL,
    Q_W65_AMBIENT_POINT_REQUIRED,
    Q_W65_LEVEL_REQUIRED,
    Q_W65_TARGET_REQUIRED,
    evaluate_dimplex_dhw_w65_runtime,
    lookup_dimplex_w65_point,
    p32_boundary,
    resolve_dimplex_dhw_request,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b05_p32_dimplex_w65_performance.csv"
REG = ROOT / "registry" / "b05_p32_dhw_stateful_w65_runtime.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P32_DHW_STATEFUL_W65_RUNTIME.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P32DhwStatefulHighTempTests(unittest.TestCase):
    def test_dhw_request_starts_below_target_minus_hysteresis(self):
        state = resolve_dimplex_dhw_request(
            tank_temperature_c=57.0,
            dhw_set_temperature_c=65.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=False,
            flange_heater_reheat_enabled=False,
        )
        self.assertTrue(state.request_active)
        self.assertEqual(state.request_on_threshold_c, 58.0)
        self.assertEqual(state.effective_hp_target_c, 65.0)

    def test_active_request_holds_in_deadband_but_idle_does_not_start(self):
        active = resolve_dimplex_dhw_request(
            tank_temperature_c=61.0,
            dhw_set_temperature_c=65.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=True,
            flange_heater_reheat_enabled=False,
        )
        idle = resolve_dimplex_dhw_request(
            tank_temperature_c=61.0,
            dhw_set_temperature_c=65.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=False,
            flange_heater_reheat_enabled=False,
        )
        self.assertTrue(active.request_active)
        self.assertFalse(idle.request_active)

    def test_hp_max_caps_heat_pump_target_and_auxiliary_reheat_is_separate(self):
        state = resolve_dimplex_dhw_request(
            tank_temperature_c=50.0,
            dhw_set_temperature_c=75.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=False,
            flange_heater_reheat_enabled=True,
        )
        self.assertEqual(state.effective_hp_target_c, 65.0)
        self.assertTrue(state.auxiliary_reheat_required)
        self.assertTrue(state.heat_pump_cannot_reach_requested_setpoint)

    def test_w65_grid_is_exact_and_has_no_interpolation(self):
        point = lookup_dimplex_w65_point(outdoor_temperature_c=7.0, performance_level=MIN_LEVEL)
        self.assertIsNotNone(point)
        self.assertEqual(point.thermal_capacity_kw, 6.41)
        self.assertEqual(point.electrical_input_kw, 2.60)
        self.assertEqual(point.cop, 2.47)

        self.assertIsNone(lookup_dimplex_w65_point(outdoor_temperature_c=-12.0, performance_level=MIN_LEVEL))
        self.assertIsNone(lookup_dimplex_w65_point(outdoor_temperature_c=-22.0, performance_level=MAX_LEVEL))

    def test_materialized_w65_grid_has_18_source_native_points(self):
        data = rows(DATA)
        self.assertEqual(len(data), 18)
        self.assertEqual({r["water_outlet_temperature_c"] for r in data}, {"65"})
        self.assertEqual({r["performance_level"] for r in data}, {"MIN", "MAX"})
        self.assertEqual(
            {float(r["outdoor_temperature_c"]) for r in data},
            {-15.0, -10.0, -7.0, 2.0, 7.0, 12.0, 20.0, 30.0, 40.0},
        )
        self.assertNotIn("-22", {r["outdoor_temperature_c"] for r in data})

    def test_source_table_internal_ratios_are_consistent_with_rounded_cop(self):
        for row in rows(DATA):
            qh = float(row["thermal_capacity_kw"])
            pel = float(row["electrical_input_kw"])
            cop = float(row["cop"])
            self.assertAlmostEqual(qh / pel, cop, delta=0.03)

    def test_bounded_w65_runtime_point_is_ready(self):
        result = evaluate_dimplex_dhw_w65_runtime(
            tank_temperature_c=50.0,
            dhw_set_temperature_c=65.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=False,
            flange_heater_reheat_enabled=False,
            space_heating_request=True,
            outdoor_temperature_c=7.0,
            performance_level=MIN_LEVEL,
        )
        self.assertEqual(result.status, "QUALIFIED_DIMPLEX_W65_DHW_RUNTIME_POINT")
        self.assertEqual(result.active_mode, "DHW")
        self.assertTrue(result.performance_ready)
        self.assertEqual(result.performance_point.thermal_capacity_kw, 6.41)
        self.assertEqual(result.performance_point.electrical_input_kw, 2.60)

    def test_non_w65_target_fails_closed(self):
        result = evaluate_dimplex_dhw_w65_runtime(
            tank_temperature_c=45.0,
            dhw_set_temperature_c=60.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=False,
            flange_heater_reheat_enabled=False,
            space_heating_request=False,
            outdoor_temperature_c=7.0,
            performance_level=MIN_LEVEL,
        )
        self.assertEqual(result.status, Q_W65_TARGET_REQUIRED)
        self.assertFalse(result.performance_ready)

    def test_missing_runtime_level_fails_closed(self):
        result = evaluate_dimplex_dhw_w65_runtime(
            tank_temperature_c=50.0,
            dhw_set_temperature_c=65.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=False,
            flange_heater_reheat_enabled=False,
            space_heating_request=False,
            outdoor_temperature_c=7.0,
            performance_level=None,
        )
        self.assertEqual(result.status, Q_W65_LEVEL_REQUIRED)
        self.assertEqual(result.residual_gap, "DIMPLEX_W65_RUNTIME_PERFORMANCE_LEVEL_REQUIRED")

    def test_missing_exact_ambient_point_fails_closed(self):
        result = evaluate_dimplex_dhw_w65_runtime(
            tank_temperature_c=50.0,
            dhw_set_temperature_c=65.0,
            hysteresis_k=7.0,
            hp_max_temperature_c=65.0,
            previous_request_active=False,
            flange_heater_reheat_enabled=False,
            space_heating_request=False,
            outdoor_temperature_c=-12.0,
            performance_level=MAX_LEVEL,
        )
        self.assertEqual(result.status, Q_W65_AMBIENT_POINT_REQUIRED)

    def test_q_b05_005_is_narrowed_not_falsely_resolved(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-005"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P32", q["notes"])
        self.assertIn("RESOLVED_FOR_DIMPLEX_WPM_TOUCH_HYSTERESIS_STATE", q["notes"])
        self.assertIn("RESOLVED_FOR_DIMPLEX_W65_EXACT_SOURCE_GRID", q["notes"])
        self.assertIn("DIMPLEX_W65_RUNTIME_PERFORMANCE_LEVEL_REQUIRED", q["notes"])

    def test_readiness_uplift_is_bounded_and_generic_variables_remain_q(self):
        readiness = {r["component_id"]: r for r in rows(READINESS)}["DHW_MODE"]
        self.assertEqual(readiness["readiness_percent"], "60")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-DHW-CONTROLLER-STATE"]["status"], "Q")
        self.assertEqual(variables["VAR-B05-DHW-HIGH-TEMP-PERFORMANCE"]["status"], "Q")
        self.assertEqual(variables["VAR-B05-DIMPLEX-DHW-REQUEST-STATE"]["status"], "DER")
        self.assertEqual(variables["VAR-B05-DIMPLEX-W65-DHW-PERFORMANCE"]["status"], "OBS")

    def test_registry_source_pack_and_boundaries_are_pinned(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["STATEFUL_DHW_CONTROLLER_RUNTIME_REQUIRED"]["status"],
            "RESOLVED_FOR_DIMPLEX_WPM_TOUCH_HYSTERESIS_STATE",
        )
        self.assertEqual(
            reg["DHW_HIGH_TEMP_PRODUCT_PERFORMANCE_REQUIRED"]["status"],
            "RESOLVED_FOR_DIMPLEX_W65_EXACT_SOURCE_GRID",
        )
        self.assertEqual(reg["DIMPLEX_W65_RUNTIME_PERFORMANCE_LEVEL_REQUIRED"]["status"], "OPEN")

        sources = {r["source_id"]: r for r in rows(SOURCES)}
        source = sources["SRC-B05-DIMPLEX-LA2030CP-W65-PERFORMANCE-2026"]
        self.assertEqual(source["retrieved_at"], "2026-09-25")
        self.assertIn("section 3.10.4", source["reference_period"])

        text = PACK.read_text(encoding="utf-8")
        self.assertIn("No interpolation is introduced in P32", text)
        self.assertIn("DHW_MODE: 45% -> 60%", text)

        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P32", readme)

        boundary = p32_boundary()
        self.assertIn("NO_GRAPH_DIGITIZATION", boundary)
        self.assertIn("NO_RUNTIME_INVERTER_LEVEL_INFERENCE", boundary)


if __name__ == "__main__":
    unittest.main()
