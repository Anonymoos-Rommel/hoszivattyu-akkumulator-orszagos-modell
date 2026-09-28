import csv
import math
import unittest
from pathlib import Path

from modules.B05.fcu_state_dependent_response import (
    DER_STATE_TIME_CONSTANT,
    EXPERIMENT_STEP_DURATION_S,
    HEM_TAU_OUT_NOT_ADMITTED,
    MODEL_VALIDATION_NRMSE_UPPER_PERCENT,
    Q_WATER_MASS_REQUIRED,
    THERMODYNAMIC_IDENTIFICATION_RUNS,
    heat_transfer_coefficient_w_per_k,
    p56_boundaries,
    resolve_water_state_time_constant_s,
)

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
SOURCES = ROOT / "registry" / "sources.csv"
HP_SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
REG = ROOT / "registry" / "b05_p56_fcc06_state_dependent_response.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P56FCC06StateDependentResponseTests(unittest.TestCase):
    def test_source_protocol_is_not_promoted_to_480s_tau(self):
        self.assertEqual(480, EXPERIMENT_STEP_DURATION_S)
        self.assertEqual(32, THERMODYNAMIC_IDENTIFICATION_RUNS)
        self.assertEqual(6.0, MODEL_VALIDATION_NRMSE_UPPER_PERCENT)
        self.assertIn(
            "EIGHT_MINUTE_EXPERIMENT_WINDOW != RESPONSE_TIME_480_SECONDS",
            p56_boundaries(),
        )

    def test_identified_heating_surface_is_state_dependent(self):
        q = 0.027
        low = heat_transfer_coefficient_w_per_k("L", q)
        medium = heat_transfer_coefficient_w_per_k("M", q)
        high = heat_transfer_coefficient_w_per_k("H", q)
        self.assertGreater(low, 0)
        self.assertGreater(medium, 0)
        self.assertGreater(high, 0)
        self.assertFalse(math.isclose(low, medium))
        self.assertFalse(math.isclose(medium, high))
        self.assertFalse(math.isclose(low, high))

    def test_numeric_time_constant_fails_closed_without_water_mass(self):
        r = resolve_water_state_time_constant_s(
            fan_speed="M",
            water_flow_kg_s=0.027,
            water_mass_kg=None,
            water_heat_capacity_j_per_kg_k=4180.0,
        )
        self.assertEqual(Q_WATER_MASS_REQUIRED, r.status)
        self.assertIsNone(r.value_s)

    def test_physical_water_state_tau_is_not_hem_tau_out(self):
        r = resolve_water_state_time_constant_s(
            fan_speed="M",
            water_flow_kg_s=0.027,
            water_mass_kg=1.0,
            water_heat_capacity_j_per_kg_k=4180.0,
        )
        self.assertEqual(DER_STATE_TIME_CONSTANT, r.status)
        self.assertGreater(r.value_s, 0)
        self.assertIn(
            "FCC06_WATER_STATE_TIME_CONSTANT != HEM_EN15316_TAU_OUT",
            p56_boundaries(),
        )
        self.assertEqual(
            "HEM_TAU_OUT_NOT_ADMITTED_FROM_FCC06_STATE_SURFACE",
            HEM_TAU_OUT_NOT_ADMITTED,
        )

    def test_new_source_is_registered_in_both_source_registries(self):
        source_id = "SRC-B05-FCU-FCC06-CONTROL-DYNAMIC-2019"
        self.assertIn(source_id, {r["source_id"] for r in rows(SOURCES)})
        self.assertIn(source_id, {r["source_id"] for r in rows(HP_SOURCES)})

    def test_p56_narrows_record_but_keeps_scalar_response_q(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            "RESOLVED_TO_EXACT_STATE_DEPENDENT_RECORD",
            reg["FANCOIL_HEATING_DYNAMIC_RECORD"]["status"],
        )
        self.assertEqual(
            "NOT_ADMITTED",
            reg["FANCOIL_OBS_SCALAR_RESPONSE_TIME"]["status"],
        )
        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual("Q", variables["VAR-B05-FANCOIL-OBS-EMITTER-RESPONSE-TIME"]["status"])
        self.assertIn("P56", variables["VAR-B05-FANCOIL-OBS-EMITTER-RESPONSE-TIME"]["notes"])

    def test_q_b05_004_stays_open_with_narrowed_fcu_residual(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual("OPEN", q["status"])
        self.assertIn("B05-P56", q["notes"])
        self.assertIn(
            "STATE_DEPENDENT_FCU_RESPONSE_TO_HEM_TAU_OUT_MAPPING_OR_DIRECT_RUNTIME_PATH_REQUIRED",
            q["notes"],
        )

    def test_no_mechanical_readiness_uplift(self):
        ready = {r["component_id"]: r for r in rows(READINESS)}
        self.assertGreaterEqual(int(ready["PART_LOAD_MODULATION"]["readiness_percent"]), 45)
        self.assertIn("P56", ready["PART_LOAD_MODULATION"]["notes"])
        modules = {r["module_id"]: r for r in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
