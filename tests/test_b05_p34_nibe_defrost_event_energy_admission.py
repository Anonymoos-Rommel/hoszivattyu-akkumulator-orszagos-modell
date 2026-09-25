import csv
import unittest
from pathlib import Path

from modules.B05.defrost_event_energy_admission import (
    ACTIVE,
    DIRECT_OFF_EVENT_OFF,
    INTERVAL_MEAN,
    OBS,
    THERMAL_POSITIVE_TO_BUILDING,
    DefrostIntervalSample,
    integrate_cotimed_defrost_event,
    p34_boundary,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p34_nibe_defrost_event_energy_admission.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p34_public_nibe_defrost_evidence_inventory.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P34_NIBE_DEFROST_EVENT_ENERGY_ADMISSION.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sample(
    start,
    end,
    electric_w,
    thermal_w,
    *,
    event_id="EVENT-1",
    system_id="NIBE-S2125-TEST",
    state=ACTIVE,
    boundary_status=DIRECT_OFF_EVENT_OFF,
    semantics=INTERVAL_MEAN,
    electric_boundary="WHOLE_HP_PLUS_ADDITION",
    thermal_boundary="BUILDING_HEATING_CIRCUIT",
    state_evidence_status=OBS,
    electric_evidence_status=OBS,
    thermal_evidence_status=OBS,
):
    return DefrostIntervalSample(
        event_id=event_id,
        system_id=system_id,
        start_epoch_s=start,
        end_epoch_s=end,
        direct_defrost_state=state,
        event_boundary_status=boundary_status,
        electric_power_w=electric_w,
        thermal_power_w=thermal_w,
        interval_semantics=semantics,
        electric_boundary=electric_boundary,
        thermal_boundary=thermal_boundary,
        thermal_sign_convention=THERMAL_POSITIVE_TO_BUILDING,
        state_source_id="OBS_DIRECT_DEFROST",
        electric_source_id="OBS_ELECTRIC_INTERVAL",
        thermal_source_id="OBS_THERMAL_INTERVAL",
        state_evidence_status=state_evidence_status,
        electric_evidence_status=electric_evidence_status,
        thermal_evidence_status=thermal_evidence_status,
    )


class B05P34NibeDefrostEventEnergyAdmissionTests(unittest.TestCase):
    def test_complete_transition_bound_cotimed_obs_can_be_integrated(self):
        result = integrate_cotimed_defrost_event(
            [
                sample(0, 60, 1000.0, -2000.0),
                sample(60, 120, 1200.0, -1800.0),
            ]
        )
        self.assertTrue(result.admitted)
        self.assertEqual(result.status, "DER_FROM_COMPLETE_COTIMED_OBS_INTERVAL_MEANS")
        self.assertEqual(result.event_id, "EVENT-1")
        self.assertEqual(result.system_id, "NIBE-S2125-TEST")
        self.assertEqual(result.defrost_state, ACTIVE)
        self.assertEqual(result.duration_seconds, 120)
        self.assertAlmostEqual(result.electricity_kwh, 0.0366666667)
        self.assertAlmostEqual(result.net_thermal_to_building_kwh, -0.0633333333)
        self.assertAlmostEqual(result.heat_removed_kwh, 0.0633333333)
        self.assertEqual(result.evidence_status, "DER")

    def test_system_or_event_identity_mismatch_fails_closed(self):
        system_mismatch = integrate_cotimed_defrost_event(
            [
                sample(0, 60, 1000.0, -1000.0, system_id="A"),
                sample(60, 120, 1000.0, -1000.0, system_id="B"),
            ]
        )
        self.assertFalse(system_mismatch.admitted)

        event_mismatch = integrate_cotimed_defrost_event(
            [
                sample(0, 60, 1000.0, -1000.0, event_id="E1"),
                sample(60, 120, 1000.0, -1000.0, event_id="E2"),
            ]
        )
        self.assertFalse(event_mismatch.admitted)

    def test_partial_window_without_direct_off_event_off_boundary_fails_closed(self):
        result = integrate_cotimed_defrost_event(
            [
                sample(
                    0,
                    60,
                    1000.0,
                    -1000.0,
                    boundary_status="PARTIAL_EVENT_WINDOW",
                )
            ]
        )
        self.assertFalse(result.admitted)
        self.assertIn("OFF-to-event-to-OFF", result.reason)

    def test_non_obs_input_stream_fails_closed(self):
        result = integrate_cotimed_defrost_event(
            [
                sample(
                    0,
                    60,
                    1000.0,
                    -1000.0,
                    thermal_evidence_status="DER",
                )
            ]
        )
        self.assertFalse(result.admitted)
        self.assertIn("must be OBS", result.reason)

    def test_gap_overlap_or_unsorted_input_fails_closed(self):
        gap = integrate_cotimed_defrost_event(
            [
                sample(0, 60, 1000.0, -1000.0),
                sample(61, 120, 1000.0, -1000.0),
            ]
        )
        self.assertFalse(gap.admitted)

        overlap = integrate_cotimed_defrost_event(
            [
                sample(0, 60, 1000.0, -1000.0),
                sample(59, 120, 1000.0, -1000.0),
            ]
        )
        self.assertFalse(overlap.admitted)

        unsorted = integrate_cotimed_defrost_event(
            [
                sample(60, 120, 1000.0, -1000.0),
                sample(0, 60, 1000.0, -1000.0),
            ]
        )
        self.assertFalse(unsorted.admitted)

    def test_instantaneous_point_semantics_are_not_silently_integrated(self):
        result = integrate_cotimed_defrost_event(
            [sample(0, 60, 1000.0, -1000.0, semantics="INSTANTANEOUS_POINT")]
        )
        self.assertFalse(result.admitted)
        self.assertIn("interval-mean", result.reason)

    def test_missing_measurement_or_boundary_fails_closed(self):
        missing = sample(0, 60, None, -1000.0)
        result = integrate_cotimed_defrost_event([missing])
        self.assertFalse(result.admitted)
        self.assertIsNone(result.electricity_kwh)

        no_boundary = sample(
            0,
            60,
            1000.0,
            -1000.0,
            electric_boundary="",
        )
        result2 = integrate_cotimed_defrost_event([no_boundary])
        self.assertFalse(result2.admitted)

    def test_mixed_active_passive_state_is_not_one_event(self):
        active = sample(0, 60, 1000.0, -1000.0, state="ACTIVE")
        passive = sample(60, 120, 100.0, -500.0, state="PASSIVE")
        result = integrate_cotimed_defrost_event([active, passive])
        self.assertFalse(result.admitted)
        self.assertIn("single directly observed", result.reason)

    def test_public_inventory_contains_no_numeric_event_energy_promotion(self):
        inventory = {row["record_id"]: row for row in rows(INVENTORY)}
        self.assertEqual(inventory["B05-P34-E01"]["system_id"], "HPM-252")
        self.assertEqual(inventory["B05-P34-E01"]["numeric_event_energy"], "NO")
        self.assertEqual(inventory["B05-P34-E02"]["cotimed_raw_state_electric_thermal"], "NO")
        self.assertEqual(inventory["B05-P34-E03"]["direct_event_identity"], "YES")
        self.assertEqual(inventory["B05-P34-E03"]["numeric_event_energy"], "NO")

    def test_registry_narrows_event_energy_to_exact_acquisition_residual(self):
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            reg["NIBE_DEFROST_EVENT_ENERGY_ADMISSION_GATE"]["status"],
            "RESOLVED_EXECUTABLE_CONTRACT",
        )
        self.assertIn(
            "DIRECT_OFF_EVENT_OFF",
            reg["NIBE_DEFROST_EVENT_ENERGY_ADMISSION_GATE"]["resolved_scope"],
        )
        self.assertEqual(
            reg["NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED"]["status"],
            "OPEN_NARROWED_TO_COTIMED_DIRECT_STATE_AND_ENERGY_SERIES",
        )
        self.assertIn(
            "NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED",
            reg["NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED"]["residual_gap"],
        )

    def test_generic_event_energy_remains_q_and_readiness_does_not_move(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-NIBE-DEFROST-EVENT-ENERGY"]["status"], "Q")
        self.assertEqual(
            variables["VAR-B05-NIBE-DEFROST-COTIMED-EVENT-SERIES"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-NIBE-DEFROST-EVENT-ENERGY-ADMISSION"]["status"],
            "DER",
        )

        readiness = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(readiness["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

    def test_question_preserves_lineage_and_current_p34_state(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "OPEN_NARROWED_TO_EVENT_ENERGY_AND_WEATHER_TO_EVAPORATOR_STATE",
            q["notes"],
        )
        self.assertIn(
            "OPEN_NARROWED_TO_COTIMED_EVENT_ENERGY_SERIES_WEATHER_TO_BT16_AND_CROSS_PRODUCT",
            q["notes"],
        )
        self.assertIn(
            "NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED",
            q["notes"],
        )

    def test_sources_and_documents_preserve_fail_closed_boundary(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-NIBE-S2125-MODBUS-DEFROST-2026",
            "SRC-B05-HEATPUMPMONITOR-API-2026",
            "SRC-B05-HEATPUMPMONITOR-S2125-SILKEBORG-252-2026",
            "SRC-B05-OEM-S2125-SILKEBORG-DEFROST-2026",
        ):
            self.assertIn(source_id, sources)

        text = PACK.read_text(encoding="utf-8")
        self.assertIn("EVENT SHAPE", text)
        self.assertIn("EVENT IDENTITY", text)
        self.assertIn("OFF -> ACTIVE/PASSIVE -> OFF", text)
        self.assertIn("DEFROST: 20% -> 20%", text)
        self.assertIn("B05 overall: 64% -> 64%", text)

        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P34", readme)
        self.assertIn("DEFROST=PARTIAL (20%)", readme)

        boundary = p34_boundary()
        self.assertIn("EVENT_SHAPE != EVENT_IDENTITY", boundary)
        self.assertIn("PARTIAL_EVENT_WINDOW != COMPLETE_EVENT_ENERGY", boundary)
        self.assertIn("NO_NUMERIC_EVENT_PENALTY_WITHOUT_ADMISSION", boundary)


if __name__ == "__main__":
    unittest.main()
