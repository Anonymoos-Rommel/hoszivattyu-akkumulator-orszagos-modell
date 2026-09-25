import csv
import unittest
from pathlib import Path

from modules.B05.defrost_meter_export_contract import (
    CUMULATIVE_DELTA_ROUTE_ADMITTED,
    METER_EXPORT_ADMITTED,
    Q_DIRECT_STATE,
    READY_FOR_P34_EVENT_ENERGY_GATE,
    CotimedMeterExportEvidence,
    CumulativeDeltaEvidence,
    qualify_cotimed_meter_export,
    qualify_cumulative_delta_route,
    qualify_event_energy_handoff,
    p36_boundary,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p36_silkeborg_cotimed_meter_export.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p36_silkeborg_public_meter_export_inventory.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P36_SILKEBORG_COTIMED_METER_EXPORT.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def exact_meter():
    return CotimedMeterExportEvidence(
        exact_system_bound=True,
        public_app_binding_proven=True,
        electric_raw_timestamped_obs=True,
        thermal_raw_timestamped_obs=True,
        electric_unit_w=True,
        thermal_unit_w=True,
        electric_native_interval_s=10,
        thermal_native_interval_s=10,
        electric_nonnull_points=8297,
        thermal_nonnull_points=8297,
        common_nonnull_timestamps=8297,
    )


def exact_cumulative():
    return CumulativeDeltaEvidence(
        app_contract_electric_cumulative=True,
        app_contract_thermal_cumulative=True,
        app_contract_end_minus_start=True,
        exact_system_feed_binding=True,
        raw_timestamped_kwh_obs=True,
        common_four_feed_timestamps=68,
        negative_thermal_points_checked=42,
        negative_thermal_points_with_negative_kwh_delta=42,
        reset_like_steps=0,
    )


class B05P36SilkeborgCotimedMeterExportTests(unittest.TestCase):
    def test_exact_public_meter_export_is_admitted(self):
        result = qualify_cotimed_meter_export(exact_meter())
        self.assertTrue(result.admitted)
        self.assertEqual(result.status, METER_EXPORT_ADMITTED)
        self.assertEqual(result.evidence_status, "OBS")
        self.assertEqual(result.common_nonnull_timestamps, 8297)

    def test_meter_export_fails_closed_without_common_timebase(self):
        evidence = CotimedMeterExportEvidence(
            **{**exact_meter().__dict__, "thermal_native_interval_s": 30}
        )
        self.assertFalse(qualify_cotimed_meter_export(evidence).admitted)

    def test_exact_cumulative_delta_route_is_admitted(self):
        result = qualify_cumulative_delta_route(exact_cumulative())
        self.assertTrue(result.admitted)
        self.assertEqual(result.status, CUMULATIVE_DELTA_ROUTE_ADMITTED)
        self.assertEqual(result.evidence_status, "DER")
        self.assertEqual(result.residual_gaps, ())

    def test_cumulative_route_fails_if_signed_reverse_is_not_proven(self):
        evidence = CumulativeDeltaEvidence(
            **{
                **exact_cumulative().__dict__,
                "negative_thermal_points_with_negative_kwh_delta": 41,
            }
        )
        self.assertFalse(qualify_cumulative_delta_route(evidence).admitted)

    def test_cumulative_route_fails_on_reset_like_jump(self):
        evidence = CumulativeDeltaEvidence(
            **{**exact_cumulative().__dict__, "reset_like_steps": 1}
        )
        self.assertFalse(qualify_cumulative_delta_route(evidence).admitted)

    def test_current_p36_state_is_blocked_only_by_direct_state(self):
        meter = qualify_cotimed_meter_export(exact_meter())
        cumulative = qualify_cumulative_delta_route(exact_cumulative())
        result = qualify_event_energy_handoff(
            meter_export=meter,
            cumulative_delta=cumulative,
            direct_state_raw_admitted=False,
            complete_direct_off_event_off_boundary=False,
        )
        self.assertFalse(result.ready)
        self.assertEqual(result.residual_gaps, (Q_DIRECT_STATE,))

    def test_hypothetical_direct_state_hands_off_to_p34(self):
        meter = qualify_cotimed_meter_export(exact_meter())
        cumulative = qualify_cumulative_delta_route(exact_cumulative())
        result = qualify_event_energy_handoff(
            meter_export=meter,
            cumulative_delta=cumulative,
            direct_state_raw_admitted=True,
            complete_direct_off_event_off_boundary=True,
        )
        self.assertTrue(result.ready)
        self.assertEqual(result.status, READY_FOR_P34_EVENT_ENERGY_GATE)

    def test_inventory_pins_meter_and_cumulative_evidence(self):
        inv = {row["record_id"]: row for row in rows(INVENTORY)}
        self.assertEqual(inv["B05-P36-E03"]["feed_id"], "501345")
        self.assertEqual(inv["B05-P36-E04"]["feed_id"], "501342")
        self.assertEqual(inv["B05-P36-E05"]["common_timestamps"], "8297")
        self.assertEqual(inv["B05-P36-E05"]["negative_heat_common_points"], "596")
        self.assertEqual(inv["B05-P36-E08"]["feed_id"], "501346")
        self.assertEqual(inv["B05-P36-E09"]["feed_id"], "501343")
        self.assertEqual(inv["B05-P36-E10"]["common_timestamps"], "68")
        self.assertEqual(inv["B05-P36-E10"]["negative_heat_common_points"], "42")

    def test_registry_resolves_meter_and_cumulative_routes_only(self):
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            reg["SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED"]["status"],
            "RESOLVED_EXACT_PUBLIC_COTIMED_METER_EXPORT",
        )
        self.assertEqual(
            reg["SILKEBORG_S2125_INTERVAL_MEAN_OR_QUALIFIED_CUMULATIVE_DELTA_REQUIRED"]["status"],
            "RESOLVED_QUALIFIED_CUMULATIVE_DELTA_ROUTE",
        )
        narrowed = reg["NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED"]
        self.assertEqual(
            narrowed["status"],
            "OPEN_NARROWED_TO_OWNER_RAW_DIRECT_STATE_EXPORT",
        )
        self.assertEqual(
            narrowed["residual_gap"],
            "SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED",
        )

    def test_negative_heat_remains_forbidden_as_direct_identity(self):
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            reg["NEGATIVE_HEAT_COMMON_POINTS_AS_DIRECT_DEFROST_IDENTITY"]["status"],
            "FORBIDDEN",
        )

    def test_native_power_interval_mean_is_still_not_proven(self):
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            reg["PHPFINA_NATIVE_10S_POWER_AS_INTERVAL_MEAN"]["status"],
            "NOT_PROVEN",
        )
        self.assertEqual(
            reg["PUBLIC_KWH_FEEDS_AS_QUALIFIED_EVENT_DELTA"]["status"],
            "RESOLVED_BOUNDED_CUMULATIVE_DELTA_ROUTE",
        )

    def test_variables_promote_meter_and_energy_route_but_not_event_series(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(
            variables["VAR-B05-SILKEBORG-S2125-COTIMED-METER-EXPORT"]["status"],
            "OBS",
        )
        self.assertEqual(
            variables["VAR-B05-SILKEBORG-S2125-EVENT-ENERGY-SEMANTICS"]["status"],
            "DER",
        )
        self.assertEqual(
            variables["VAR-B05-SILKEBORG-S2125-DIRECT-STATE-EXPORT"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-NIBE-DEFROST-COTIMED-EVENT-SERIES"]["status"],
            "Q",
        )

    def test_question_and_readiness_remain_open_without_event_identity(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "OPEN_NARROWED_TO_DIRECT_STATE_WEATHER_TO_BT16_AND_CROSS_PRODUCT",
            q["notes"],
        )
        self.assertIn("No numeric event kWh is admitted", q["notes"])

        readiness = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(readiness["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

    def test_sources_pin_both_probes_and_app_contract(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-OEM-S2125-PUBLIC-EMONCMS-APP-2024",
            "SRC-B05-P36-SILKEBORG-EMONCMS-METER-PROBE-2026",
            "SRC-B05-EMONCMS-PHPFINA-NOAVG-669ACA-2025",
            "SRC-B05-EMONCMS-MYHEATPUMP-KWH-52FF3D-2026",
            "SRC-B05-P36-SILKEBORG-KWH-SEMANTICS-PROBE-2026",
        ):
            self.assertIn(source_id, sources)

    def test_no_read_credential_is_committed(self):
        for path in (PACK, INVENTORY, REG):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("readkey=", text)

    def test_docs_readme_and_boundaries_are_pinned(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("8297", text)
        self.assertIn("42 / 42", text)
        self.assertIn("Fixed Interval No Averaging", text)
        self.assertIn("OPEN_NARROWED_TO_OWNER_RAW_DIRECT_STATE_EXPORT", text)
        self.assertIn("B05-P36", README.read_text(encoding="utf-8"))

        boundary = p36_boundary()
        self.assertIn(
            "CUMULATIVE_DELTA_ROUTE_ADMITTED != DIRECT_EVENT_IDENTITY_ADMITTED",
            boundary,
        )
        self.assertIn(
            "NO_NUMERIC_EVENT_KWH_WITHOUT_DIRECT_STATE_EVENT_BOUNDARY",
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
