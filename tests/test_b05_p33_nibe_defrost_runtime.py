import csv
import unittest
from pathlib import Path

from modules.B05.defrost_runtime_state import (
    ACTIVE,
    ACTIVE_DUE,
    TIMER_PENDING,
    OFF,
    PASSIVE,
    PASSIVE_DUE,
    REQUIREMENT_PENDING,
    Q_EVENT_ENERGY,
    active_defrost_termination,
    classify_nibe_controller_state,
    decode_nibe_modbus_defrost_status,
    defrost_requirement_accumulating,
    observe_nibe_modbus_defrost_state,
    p33_boundary,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p33_nibe_defrost_runtime.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
CHANNELS = ROOT / "data" / "processed" / "b05_p33_nibe_s2125_modbus_channels.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P33_NIBE_DEFROST_STATE_TELEMETRY.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P33NibeDefrostRuntimeTests(unittest.TestCase):
    def test_bt16_plus_compressor_only_marks_requirement_accumulation(self):
        self.assertTrue(
            defrost_requirement_accumulating(
                bt16_evaporator_c=-4.0,
                start_threshold_bt16_c=-3.0,
                compressor_running=True,
            )
        )
        self.assertFalse(
            defrost_requirement_accumulating(
                bt16_evaporator_c=-4.0,
                start_threshold_bt16_c=-3.0,
                compressor_running=False,
            )
        )
        self.assertFalse(
            defrost_requirement_accumulating(
                bt16_evaporator_c=-2.0,
                start_threshold_bt16_c=-3.0,
                compressor_running=True,
            )
        )

    def test_pending_timer_is_not_synthesized_into_event_frequency(self):
        pending = classify_nibe_controller_state(
            bt16_evaporator_c=-4.0,
            bt28_outdoor_c=1.0,
            compressor_running=True,
            compressor_demand_fulfilled=False,
            time_until_active_defrost_min=20.0,
            start_threshold_bt16_c=-3.0,
            passive_cutout_bt28_c=4.0,
        )
        self.assertEqual(pending.state, TIMER_PENDING)
        self.assertTrue(pending.requirement_accumulating)
        self.assertFalse(pending.energy_ready)
        self.assertIsNone(pending.heat_penalty_kwh)
        self.assertIsNone(pending.electricity_penalty_kwh)

        not_accumulating = classify_nibe_controller_state(
            bt16_evaporator_c=-2.0,
            bt28_outdoor_c=1.0,
            compressor_running=True,
            compressor_demand_fulfilled=False,
            time_until_active_defrost_min=20.0,
            start_threshold_bt16_c=-3.0,
            passive_cutout_bt28_c=4.0,
        )
        self.assertEqual(not_accumulating.state, TIMER_PENDING)
        self.assertFalse(not_accumulating.requirement_accumulating)

    def test_due_requirement_selects_passive_only_with_all_source_conditions(self):
        passive = classify_nibe_controller_state(
            bt16_evaporator_c=-4.0,
            bt28_outdoor_c=5.0,
            compressor_running=False,
            compressor_demand_fulfilled=True,
            time_until_active_defrost_min=0.0,
            start_threshold_bt16_c=-3.0,
            passive_cutout_bt28_c=4.0,
        )
        self.assertEqual(passive.state, PASSIVE_DUE)

        active_cold = classify_nibe_controller_state(
            bt16_evaporator_c=-4.0,
            bt28_outdoor_c=4.0,
            compressor_running=True,
            compressor_demand_fulfilled=False,
            time_until_active_defrost_min=0.0,
            start_threshold_bt16_c=-3.0,
            passive_cutout_bt28_c=4.0,
        )
        self.assertEqual(active_cold.state, ACTIVE_DUE)

    def test_configured_passive_cutout_is_not_silently_replaced_by_factory_default(self):
        custom = classify_nibe_controller_state(
            bt16_evaporator_c=-4.0,
            bt28_outdoor_c=5.0,
            compressor_running=True,
            compressor_demand_fulfilled=True,
            time_until_active_defrost_min=0.0,
            start_threshold_bt16_c=-3.0,
            passive_cutout_bt28_c=6.0,
        )
        self.assertEqual(custom.state, ACTIVE_DUE)

    def test_active_defrost_termination_uses_literal_longer_than_15_minutes(self):
        at_15 = active_defrost_termination(
            elapsed_minutes=15.0,
            evaporator_stop_value_reached=False,
            bt3_return_c=12.0,
            bp8_below_permitted_minimum=False,
        )
        self.assertFalse(at_15.terminate)

        after_15 = active_defrost_termination(
            elapsed_minutes=15.01,
            evaporator_stop_value_reached=False,
            bt3_return_c=12.0,
            bp8_below_permitted_minimum=False,
        )
        self.assertTrue(after_15.terminate)
        self.assertIn("ACTIVE_DEFROST_LONGER_THAN_15_MIN", after_15.reasons)

    def test_other_active_termination_paths_are_exact(self):
        result = active_defrost_termination(
            elapsed_minutes=5.0,
            evaporator_stop_value_reached=True,
            bt3_return_c=9.9,
            bp8_below_permitted_minimum=True,
        )
        self.assertTrue(result.terminate)
        self.assertEqual(
            set(result.reasons),
            {
                "EVAPORATOR_STOP_VALUE_REACHED",
                "BT3_RETURN_BELOW_10C",
                "BP8_BELOW_PERMITTED_MINIMUM",
            },
        )

    def test_modbus_defrost_state_is_direct_obs_and_energy_stays_q(self):
        self.assertEqual(decode_nibe_modbus_defrost_status(0), OFF)
        self.assertEqual(decode_nibe_modbus_defrost_status(1), ACTIVE)
        self.assertEqual(decode_nibe_modbus_defrost_status(2), PASSIVE)
        with self.assertRaises(ValueError):
            decode_nibe_modbus_defrost_status(3)

        obs = observe_nibe_modbus_defrost_state(1)
        self.assertEqual(obs.state, ACTIVE)
        self.assertEqual(obs.evidence_status, "OBS")
        self.assertFalse(obs.energy_ready)
        self.assertIsNone(obs.electricity_penalty_kwh)
        self.assertIn(Q_EVENT_ENERGY, obs.residual_gaps)

    def test_exact_slave1_channels_are_materialized(self):
        channels = {r["function"]: r for r in rows(CHANNELS)}
        self.assertEqual(channels["Outdoor temperature (BT28)"]["register_id"], "1621")
        self.assertEqual(channels["Evaporator in (BT16)"]["register_id"], "1622")
        self.assertEqual(channels["Current compressor frequency"]["register_id"], "1803")
        self.assertEqual(channels["Defrost"]["register_id"], "1805")
        self.assertIn("0=off", channels["Defrost"]["notes"])
        self.assertTrue(all(r["slave"] == "1" for r in channels.values()))

    def test_question_is_narrowed_but_event_energy_and_weather_mapping_stay_open(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("OPEN_NARROWED_TO_EVENT_ENERGY_AND_WEATHER_TO_EVAPORATOR_STATE", q["notes"])
        self.assertIn("NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED", q["notes"])
        self.assertIn("WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED", q["notes"])

        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["PRODUCT_SPECIFIC_WEATHER_DRIVEN_DEFROST_MODEL_REQUIRED"]["status"],
            "PARTIAL_RESOLVED_TO_EXACT_CONTROLLER_STATE_AND_TELEMETRY",
        )
        self.assertEqual(reg["NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED"]["status"], "OPEN")
        self.assertEqual(reg["WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED"]["status"], "OPEN")

    def test_readiness_uplift_does_not_close_generic_penalty(self):
        readiness = {r["component_id"]: r for r in rows(READINESS)}["DEFROST"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(readiness["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-DEFROST-MODEL-STATUS"]["status"], "Q")
        self.assertEqual(variables["VAR-B05-DEFROST-RUNTIME-PENALTY"]["status"], "Q")
        self.assertEqual(variables["VAR-B05-NIBE-DEFROST-CONTROLLER-STATE"]["status"], "DER")
        self.assertEqual(variables["VAR-B05-NIBE-DEFROST-TELEMETRY"]["status"], "OBS")
        self.assertEqual(variables["VAR-B05-NIBE-DEFROST-EVENT-ENERGY"]["status"], "Q")

    def test_sources_docs_and_fail_closed_boundaries_are_pinned(self):
        sources = {r["source_id"]: r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-NIBE-S2125-IHB", sources)
        self.assertIn("SRC-B05-NIBE-S2125-MODBUS-DEFROST-2026", sources)
        self.assertEqual(
            sources["SRC-B05-NIBE-S2125-MODBUS-DEFROST-2026"]["retrieved_at"],
            "2026-09-25",
        )

        text = PACK.read_text(encoding="utf-8")
        self.assertIn("EXACT DEFROST STATE", text)
        self.assertIn("WEATHER-ONLY EVENT FREQUENCY", text)
        self.assertIn("DEFROST: 5% -> 20%", text)
        self.assertIn("B05 overall: 64% -> 64%", text)

        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P33", readme)

        boundary = p33_boundary()
        self.assertIn("AMBIENT_T_RH != BT16_WITHOUT_PRODUCT_MAPPING_OR_TELEMETRY", boundary)
        self.assertIn("NO_UNIVERSAL_DEFROST_PERCENT", boundary)


if __name__ == "__main__":
    unittest.main()
