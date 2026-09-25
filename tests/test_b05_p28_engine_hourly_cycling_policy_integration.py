import csv
import unittest
from datetime import datetime
from pathlib import Path

from modules.B05.engine import (
    HourlyDemand,
    OperatingConfig,
    PerformanceMap,
    PerformancePoint,
    simulate_hourly,
)
from modules.B05.hourly_onoff_parameter_policy import (
    FAN_COIL,
    HEM_DEFAULT_SCENARIO,
    RADIATOR_OR_UFH_WET,
)
from modules.B05.minimum_point_surface import MinimumPoint, MinimumPointSurface

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p28_engine_hourly_cycling_policy_integration.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARS = ROOT / "registry" / "heat_pump_variables.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"

def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

def mitsubishi_map():
    return PerformanceMap(
        "PUZ-WM50VHA(-BS)",
        "air_to_water",
        [
            PerformancePoint(
                7.0,
                35.0,
                thermal_capacity_kw=5.0,
                electrical_input_kw=1.0,
                cop=5.0,
                min_modulation_kw=1.8,
                evidence_status="OBS",
                source_id="SRC-B05-MITSUBISHI-PUZ-WM-MINNOMMAX-2024",
            )
        ],
    )

def mitsubishi_minimum_surface():
    return MinimumPointSurface(
        "PUZ-WM50VHA(-BS)",
        [
            MinimumPoint(
                7.0,
                35.0,
                1.8,
                5.46,
                "SRC-B05-MITSUBISHI-DATABOOK-WM50-MIN-GRID-2020",
            )
        ],
    )

def demand(load_kw=1.0):
    return HourlyDemand(datetime(2026, 1, 1, 0, 0), 7.0, load_kw, 35.0)

class B05P28EngineHourlyCyclingPolicyIntegrationTests(unittest.TestCase):
    def test_real_mitsubishi_exact_point_applies_explicit_hem_default_cycling_energy(self):
        config = OperatingConfig(
            cycling_parameter_policy=HEM_DEFAULT_SCENARIO,
            cycling_emitter_class=RADIATOR_OR_UFH_WET,
        )
        result = simulate_hourly(
            mitsubishi_map(),
            [demand(1.0)],
            config,
            mitsubishi_minimum_surface(),
        )
        hour = result.hourly[0]
        minimum_input_kw = 1.8 / 5.46
        expected_inertia_power_kw = minimum_input_kw * 140.0 * 0.2 * 0.8 / 1370.0
        expected_inertia_energy_kwh = expected_inertia_power_kw * 1.0
        self.assertEqual(result.status, "VALID")
        self.assertEqual(result.cycling_runtime_status, "QUALIFIED_HOURLY_ONOFF_METHOD")
        self.assertEqual(hour.cycling_runtime_status, "QUALIFIED_HOURLY_ONOFF_METHOD")
        self.assertEqual(hour.cycling_runtime_evidence_status, "POL")
        self.assertAlmostEqual(hour.cycling_inertia_energy_kwh, expected_inertia_energy_kwh, places=12)
        self.assertAlmostEqual(hour.heat_pump_electricity_kwh, 1.0 / 5.0 + expected_inertia_energy_kwh, places=12)
        self.assertAlmostEqual(result.seasonal_heat_pump_electricity_kwh, hour.heat_pump_electricity_kwh, places=12)

    def test_same_product_surface_without_explicit_policy_fails_closed(self):
        result = simulate_hourly(
            mitsubishi_map(),
            [demand(1.0)],
            OperatingConfig(),
            mitsubishi_minimum_surface(),
        )
        hour = result.hourly[0]
        self.assertEqual(result.status, "Q")
        self.assertEqual(hour.status, "Q / CYCLING_RUNTIME_POLICY_REQUIRED")
        self.assertEqual(hour.cycling_runtime_evidence_status, "Q")
        self.assertIsNone(hour.cycling_inertia_energy_kwh)
        self.assertAlmostEqual(hour.heat_pump_electricity_kwh, 1.0 / 5.0)

    def test_explicit_policy_without_minimum_point_surface_fails_closed(self):
        config = OperatingConfig(
            cycling_parameter_policy=HEM_DEFAULT_SCENARIO,
            cycling_emitter_class=RADIATOR_OR_UFH_WET,
        )
        result = simulate_hourly(mitsubishi_map(), [demand(1.0)], config)
        self.assertEqual(result.status, "Q")
        self.assertEqual(result.hourly[0].status, "Q / MINIMUM_POINT_RUNTIME_SURFACE_REQUIRED")
        self.assertIsNone(result.hourly[0].cycling_inertia_energy_kwh)

    def test_fan_coil_divergence_propagates_q_through_engine(self):
        config = OperatingConfig(
            cycling_parameter_policy=HEM_DEFAULT_SCENARIO,
            cycling_emitter_class=FAN_COIL,
        )
        result = simulate_hourly(
            mitsubishi_map(),
            [demand(1.0)],
            config,
            mitsubishi_minimum_surface(),
        )
        self.assertEqual(result.status, "Q")
        self.assertEqual(
            result.hourly[0].status,
            "Q / HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED",
        )
        self.assertIsNone(result.hourly[0].cycling_inertia_energy_kwh)

    def test_continuous_hour_does_not_require_or_apply_cycling_policy(self):
        result = simulate_hourly(
            mitsubishi_map(),
            [demand(2.0)],
            OperatingConfig(),
            mitsubishi_minimum_surface(),
        )
        hour = result.hourly[0]
        self.assertEqual(result.status, "VALID")
        self.assertEqual(hour.operating_state, "CONTINUOUS_MODULATION")
        self.assertEqual(hour.cycling_runtime_status, "NOT_APPLICABLE")
        self.assertIsNone(hour.cycling_inertia_energy_kwh)
        self.assertAlmostEqual(hour.heat_pump_electricity_kwh, 2.0 / 5.0)

    def test_irrelevant_uncovered_minimum_surface_does_not_block_proven_continuous_hour(self):
        uncovered = MinimumPointSurface(
            "PUZ-WM50VHA(-BS)",
            [
                MinimumPoint(
                    2.0,
                    35.0,
                    2.5,
                    3.42,
                    "SRC-B05-MITSUBISHI-DATABOOK-WM50-MIN-GRID-2020",
                )
            ],
        )
        result = simulate_hourly(
            mitsubishi_map(),
            [demand(2.0)],
            OperatingConfig(),
            uncovered,
        )
        self.assertEqual(result.status, "VALID")
        self.assertEqual(result.hourly[0].operating_state, "CONTINUOUS_MODULATION")
        self.assertEqual(result.hourly[0].cycling_runtime_status, "NOT_APPLICABLE")

    def test_minimum_surface_identity_must_match_performance_map(self):
        wrong = MinimumPointSurface(
            "OTHER-MODEL",
            [MinimumPoint(7.0, 35.0, 1.8, 5.46, "SRC-B05-MITSUBISHI-DATABOOK-WM50-MIN-GRID-2020")],
        )
        with self.assertRaises(ValueError):
            simulate_hourly(mitsubishi_map(), [demand(1.0)], OperatingConfig(), wrong)

    def test_registry_and_readiness_keep_bounded_semantics(self):
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(reg["ENGINE_HOURLY_CYCLING_POLICY_INTEGRATION"]["status"], "QUALIFIED_EXPLICIT_POLICY_PATH")
        self.assertEqual(reg["MITSUBISHI_A7_W35_ENGINE_CYCLING_PATH"]["status"], "QUALIFIED_EXACT_REAL_PRODUCT_POINT")
        self.assertEqual(reg["PRODUCT_OBS_TRANSIENT_ENGINE_PATH"]["status"], "OPEN")
        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45")
        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        self.assertEqual(questions["Q-B05-004"]["status"], "OPEN")
        variables = {row["variable_id"]: row for row in rows(VARS)}
        self.assertEqual(variables["VAR-B05-HEM-DEFAULT-ONOFF-INERTIA-ENERGY"]["status"], "DER")
        self.assertIn("P28", variables["VAR-B05-HEM-DEFAULT-ONOFF-INERTIA-ENERGY"]["notes"])

if __name__ == "__main__":
    unittest.main()
