import csv
import unittest
from datetime import datetime
from pathlib import Path

from modules.B05.dhw_dispatch_contract import (
    DIMPLEX_LA2030CP_WPM_TOUCH,
    MITSUBISHI_WM50_FTC6,
    Q_MITSUBISHI_SIMULTANEOUS_SETTING,
    Q_SIMULTANEOUS_THERMAL_SPLIT,
    classify_simultaneous_dispatch,
    p29_boundary,
    resolve_controller_policy,
)
from modules.B05.engine import (
    HourlyDemand,
    OperatingConfig,
    PerformanceMap,
    PerformancePoint,
    simulate_hourly,
)

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
REG = ROOT / "registry" / "b05_p29_dhw_controller_dispatch.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P29_DHW_CONTROLLER_DISPATCH.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P29DhwControllerDispatchTests(unittest.TestCase):
    def test_exact_controller_bindings_are_bounded(self):
        m = resolve_controller_policy(MITSUBISHI_WM50_FTC6)
        d = resolve_controller_policy(DIMPLEX_LA2030CP_WPM_TOUCH)
        self.assertEqual(m.product_binding, "PUZ-WM50VHA(-BS)+EHPT20X-MHEDW/FTC6")
        self.assertEqual(d.product_binding, "LA2030CP+WPM_TOUCH")
        self.assertIsNone(resolve_controller_policy("UNKNOWN"))

    def test_dimplex_dhw_request_preempts_space_heating_circulation(self):
        decision = classify_simultaneous_dispatch(
            DIMPLEX_LA2030CP_WPM_TOUCH,
            space_heating_request=True,
            dhw_request=True,
        )
        self.assertEqual(
            decision.status,
            "QUALIFIED_DHW_PRIORITY_PREEMPTS_SPACE_HEATING_CIRCULATION",
        )
        self.assertEqual(decision.active_mode, "DHW")
        self.assertEqual(decision.evidence_status, "OBS")
        self.assertTrue(decision.requires_high_temp_performance)
        self.assertFalse(decision.energy_allocation_ready)

    def test_mitsubishi_requires_actual_controller_setting_and_state(self):
        missing = classify_simultaneous_dispatch(
            MITSUBISHI_WM50_FTC6,
            space_heating_request=True,
            dhw_request=True,
        )
        self.assertEqual(missing.status, Q_MITSUBISHI_SIMULTANEOUS_SETTING)

        simultaneous = classify_simultaneous_dispatch(
            MITSUBISHI_WM50_FTC6,
            space_heating_request=True,
            dhw_request=True,
            mitsubishi_simultaneous_operation_enabled=True,
        )
        self.assertEqual(simultaneous.status, Q_SIMULTANEOUS_THERMAL_SPLIT)
        self.assertEqual(simultaneous.active_mode, "SIMULTANEOUS_CONFIGURED")
        self.assertFalse(simultaneous.energy_allocation_ready)

        restriction = classify_simultaneous_dispatch(
            MITSUBISHI_WM50_FTC6,
            space_heating_request=True,
            dhw_request=True,
            mitsubishi_simultaneous_operation_enabled=False,
            mitsubishi_post_dhw_restriction_active=True,
        )
        self.assertEqual(
            restriction.status,
            "QUALIFIED_SPACE_HEATING_PRIORITY_POST_DHW_RESTRICTION",
        )
        self.assertEqual(restriction.active_mode, "SPACE_HEATING")
        self.assertTrue(restriction.energy_allocation_ready)

    def test_generic_engine_remains_fail_closed_without_controller_state(self):
        performance = PerformanceMap(
            "TEST",
            "air_to_water",
            [PerformancePoint(0.0, 35.0, 3.0, 1.0, 3.0, evidence_status="SCN")],
        )
        result = simulate_hourly(
            performance,
            [
                HourlyDemand(
                    datetime(2026, 1, 1),
                    0.0,
                    1.0,
                    35.0,
                    1.0,
                    55.0,
                )
            ],
            OperatingConfig(),
        )
        self.assertEqual(result.status, "Q")
        self.assertEqual(result.hourly[0].operating_state, "Q_DHW_PRIORITY")

    def test_question_and_readiness_are_narrowed_not_overclosed(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-005"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "OPEN_NARROWED_TO_STATEFUL_CONTROLLER_RUNTIME_AND_DHW_HIGH_TEMP_PERFORMANCE",
            q["notes"],
        )
        self.assertIn("STATEFUL_DHW_CONTROLLER_RUNTIME_REQUIRED", q["notes"])
        self.assertIn("DHW_HIGH_TEMP_PRODUCT_PERFORMANCE_REQUIRED", q["notes"])

        readiness = {r["component_id"]: r for r in rows(READINESS)}["DHW_MODE"]
        self.assertEqual(readiness["readiness_percent"], "45")
        self.assertIn("P29", readiness["notes"])
        self.assertIn("B05 remains 64%", readiness["notes"])

    def test_high_temperature_capability_does_not_become_performance(self):
        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-DHW-HIGH-TEMP-PERFORMANCE"]["status"], "Q")
        self.assertIn("CAPABILITY", p29_boundary())
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["DIMPLEX_LA2030CP_HIGH_TEMP_CAPABILITY"]["status"],
            "QUALIFIED_OPERATING_ENVELOPE_ONLY",
        )
        self.assertEqual(reg["DHW_HIGH_TEMP_PRODUCT_PERFORMANCE_REQUIRED"]["status"], "OPEN")

    def test_sources_and_documentation_are_pinned(self):
        sources = {r["source_id"]: r for r in rows(SOURCES)}
        for source_id in (
            "SRC-B05-MITSUBISHI-WM50-FTC6-DHW-CONTROL-2026",
            "SRC-B05-MITSUBISHI-WM50-FTC6-BINDING-2026",
            "SRC-B05-DIMPLEX-LA2030CP-WPMTOUCH-BINDING-2026",
            "SRC-B05-DIMPLEX-WPMTOUCH-DHW-CONTROL-2026",
            "SRC-B05-DIMPLEX-LA2030CP-HIGH-TEMP-2026",
        ):
            self.assertIn(source_id, sources)
            self.assertEqual(sources[source_id]["retrieved_at"], "2026-09-25")

        pack = PACK.read_text(encoding="utf-8")
        self.assertIn("CONTROLLER DISPATCH EVIDENCE", pack)
        self.assertIn("HIGH-TEMPERATURE CAPABILITY != HIGH-TEMPERATURE COP", pack)
        self.assertIn("B05 overall: 64% -> 64%", pack)
        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P29 qualifies bounded product/controller DHW dispatch", readme)


if __name__ == "__main__":
    unittest.main()
