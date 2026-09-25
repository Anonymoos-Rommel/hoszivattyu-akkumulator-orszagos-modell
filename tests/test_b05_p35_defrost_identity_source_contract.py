import csv
import unittest
from pathlib import Path

from modules.B05.defrost_identity_source_contract import (
    CONTEXT_ONLY,
    DIRECT_CONTROLLER_RAW,
    DIRECT_STATE_ADMITTED,
    NEGATIVE_HEAT_PROXY,
    OWNER_VISUAL_LOG,
    PROXY_ONLY,
    PUBLIC_APP_FEED,
    Q_OWNER_STATE_EXPORT,
    REMOTE_ACCESS_RESULT,
    DefrostIdentityEvidence,
    qualify_cotimed_join,
    qualify_defrost_identity,
    p35_boundary,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p35_nibe_defrost_direct_state_export_boundary.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p35_silkeborg_defrost_source_inventory.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P35_NIBE_DEFROST_DIRECT_STATE_EXPORT_BOUNDARY.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P35DefrostIdentitySourceContractTests(unittest.TestCase):
    def test_negative_heat_proxy_never_becomes_direct_state(self):
        result = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=NEGATIVE_HEAT_PROXY,
                exact_system_bound=True,
                raw_timestamped_series=True,
                direct_controller_semantics=False,
                state_values_explicit=False,
                public_feed_binding_proven=True,
            )
        )
        self.assertFalse(result.direct_identity_admitted)
        self.assertEqual(result.status, PROXY_ONLY)
        self.assertIn(Q_OWNER_STATE_EXPORT, result.residual_gaps)

    def test_owner_visual_log_proves_context_not_raw_state_export(self):
        result = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=OWNER_VISUAL_LOG,
                exact_system_bound=True,
                raw_timestamped_series=False,
                direct_controller_semantics=True,
                state_values_explicit=True,
                public_feed_binding_proven=False,
            )
        )
        self.assertFalse(result.direct_identity_admitted)
        self.assertEqual(result.status, CONTEXT_ONLY)
        self.assertEqual(result.evidence_status, "OBS")

    def test_remote_http_result_cannot_establish_source_absence(self):
        result = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=REMOTE_ACCESS_RESULT,
                exact_system_bound=True,
                raw_timestamped_series=False,
                direct_controller_semantics=False,
                state_values_explicit=False,
                public_feed_binding_proven=False,
                note="HTTP 403",
            )
        )
        self.assertFalse(result.direct_identity_admitted)
        self.assertEqual(result.status, CONTEXT_ONLY)
        self.assertIn("retrieval path only", result.reason)

    def test_public_app_feed_requires_explicit_controller_binding(self):
        result = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=PUBLIC_APP_FEED,
                exact_system_bound=True,
                raw_timestamped_series=True,
                direct_controller_semantics=True,
                state_values_explicit=True,
                public_feed_binding_proven=False,
            )
        )
        self.assertFalse(result.direct_identity_admitted)
        self.assertIn(Q_OWNER_STATE_EXPORT, result.residual_gaps)

    def test_explicitly_bound_public_raw_controller_feed_can_be_admitted(self):
        result = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=PUBLIC_APP_FEED,
                exact_system_bound=True,
                raw_timestamped_series=True,
                direct_controller_semantics=True,
                state_values_explicit=True,
                public_feed_binding_proven=True,
            )
        )
        self.assertTrue(result.direct_identity_admitted)
        self.assertEqual(result.status, DIRECT_STATE_ADMITTED)
        self.assertEqual(result.evidence_status, "OBS")

    def test_complete_direct_raw_controller_series_is_admitted(self):
        result = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=DIRECT_CONTROLLER_RAW,
                exact_system_bound=True,
                raw_timestamped_series=True,
                direct_controller_semantics=True,
                state_values_explicit=True,
                public_feed_binding_proven=True,
            )
        )
        self.assertTrue(result.direct_identity_admitted)
        self.assertEqual(result.status, DIRECT_STATE_ADMITTED)
        self.assertEqual(result.evidence_status, "OBS")
        self.assertEqual(result.residual_gaps, ())

    def test_incomplete_direct_raw_series_fails_closed(self):
        result = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=DIRECT_CONTROLLER_RAW,
                exact_system_bound=True,
                raw_timestamped_series=False,
                direct_controller_semantics=True,
                state_values_explicit=True,
                public_feed_binding_proven=False,
            )
        )
        self.assertFalse(result.direct_identity_admitted)
        self.assertIn(Q_OWNER_STATE_EXPORT, result.residual_gaps)

    def test_cotimed_join_needs_direct_state_and_both_raw_meter_series(self):
        proxy = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=NEGATIVE_HEAT_PROXY,
                exact_system_bound=True,
                raw_timestamped_series=True,
                direct_controller_semantics=False,
                state_values_explicit=False,
                public_feed_binding_proven=True,
            )
        )
        blocked = qualify_cotimed_join(
            direct_state=proxy,
            electric_raw_obs=True,
            thermal_raw_obs=True,
            same_system=True,
            common_timebase=True,
            meter_boundaries_explicit=True,
        )
        self.assertFalse(blocked.ready_for_p34_event_energy_gate)

        direct = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=DIRECT_CONTROLLER_RAW,
                exact_system_bound=True,
                raw_timestamped_series=True,
                direct_controller_semantics=True,
                state_values_explicit=True,
                public_feed_binding_proven=True,
            )
        )
        missing_meter = qualify_cotimed_join(
            direct_state=direct,
            electric_raw_obs=True,
            thermal_raw_obs=False,
            same_system=True,
            common_timebase=True,
            meter_boundaries_explicit=True,
        )
        self.assertFalse(missing_meter.ready_for_p34_event_energy_gate)

    def test_complete_source_package_can_only_handoff_to_p34_gate(self):
        direct = qualify_defrost_identity(
            DefrostIdentityEvidence(
                source_kind=DIRECT_CONTROLLER_RAW,
                exact_system_bound=True,
                raw_timestamped_series=True,
                direct_controller_semantics=True,
                state_values_explicit=True,
                public_feed_binding_proven=True,
            )
        )
        result = qualify_cotimed_join(
            direct_state=direct,
            electric_raw_obs=True,
            thermal_raw_obs=True,
            same_system=True,
            common_timebase=True,
            meter_boundaries_explicit=True,
        )
        self.assertTrue(result.ready_for_p34_event_energy_gate)
        self.assertEqual(result.status, "READY_FOR_P34_EVENT_ENERGY_GATE")
        self.assertIn("P34", result.reason)

    def test_public_inventory_preserves_source_separation(self):
        inventory = {row["record_id"]: row for row in rows(INVENTORY)}
        self.assertEqual(inventory["B05-P35-E01"]["source_kind"], "NEGATIVE_HEAT_PROXY")
        self.assertEqual(inventory["B05-P35-E01"]["direct_state_raw_export"], "NO")
        self.assertEqual(inventory["B05-P35-E03"]["source_kind"], "OWNER_VISUAL_LOG")
        self.assertEqual(inventory["B05-P35-E04"]["source_kind"], "FIELD_ACQUISITION_PATH")
        self.assertEqual(inventory["B05-P35-E06"]["what_is_proven"].endswith("retrieval"), True)
        self.assertIn("REMOTE_403", inventory["B05-P35-E06"]["notes"])

    def test_registry_narrows_exact_p34_residual(self):
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            reg["HEATPUMPMONITOR_DEFROST_AND_LOSS_DISPLAY"]["status"],
            "RESOLVED_NEGATIVE_HEAT_PROXY",
        )
        self.assertEqual(
            reg["HEATPUMPMONITOR_NEGATIVE_HEAT_AS_DIRECT_DEFROST_IDENTITY"]["status"],
            "FORBIDDEN",
        )
        narrowed = reg["NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED"]
        self.assertEqual(
            narrowed["status"],
            "OPEN_NARROWED_TO_OWNER_DIRECT_STATE_EXPORT_AND_COTIMED_METER_JOIN",
        )
        self.assertIn(
            "SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED",
            narrowed["residual_gap"],
        )
        self.assertIn(
            "SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED",
            narrowed["residual_gap"],
        )

    def test_current_question_is_narrowed_without_numeric_closure(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "OPEN_NARROWED_TO_OWNER_EXPORT_WEATHER_TO_BT16_AND_CROSS_PRODUCT",
            q["notes"],
        )
        self.assertIn("REMOTE_403 != SOURCE_ABSENCE", q["notes"])
        self.assertIn("No numeric event kWh is admitted", q["notes"])

    def test_readiness_remains_20_and_event_series_remains_q(self):
        readiness = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(readiness["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(
            variables["VAR-B05-NIBE-DEFROST-COTIMED-EVENT-SERIES"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-SILKEBORG-S2125-DIRECT-STATE-EXPORT"]["status"],
            "Q",
        )
        self.assertIn(
            variables["VAR-B05-SILKEBORG-S2125-COTIMED-METER-EXPORT"]["status"],
            {"Q", "OBS"},
        )
        self.assertEqual(
            variables["VAR-B05-HEATPUMPMONITOR-DEFROST-LOSS-PROXY"]["status"],
            "DER",
        )

    def test_sources_pin_code_field_fork_and_probe_authorities(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-HEATPUMPMONITOR-CODE-A68FDC-2026",
            "SRC-B05-OEM-S2125-MODBUS-TCP-FIELD-2024",
            "SRC-B05-JKJAER-EMONHUB-FORK-5B231D-2024",
            "SRC-B05-P35-HPM252-REMOTE-PROBE-2026",
        ):
            self.assertIn(source_id, sources)
        self.assertIn(
            "a68fdc026bdfc74afe557d952f0d4d96ce76eba5",
            sources["SRC-B05-HEATPUMPMONITOR-CODE-A68FDC-2026"]["url"],
        )
        self.assertIn(
            "5b231d1d13b215cea891ff0abfb62a8376f2c0d3",
            sources["SRC-B05-JKJAER-EMONHUB-FORK-5B231D-2024"]["url"],
        )

    def test_docs_and_boundaries_are_pinned(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("NEGATIVE_HEAT_PROXY", text)
        self.assertIn("DIRECT_NIBE_DEFROST_STATE", text)
        self.assertIn("REMOTE_HTTP_403 != SOURCE_ABSENCE", text)
        self.assertIn("DEFROST: 20% -> 20%", text)
        self.assertIn("B05 overall: 64% -> 64%", text)

        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P35", readme)

        boundary = p35_boundary()
        self.assertIn(
            "NEGATIVE_HEAT_PROXY != DIRECT_NIBE_DEFROST_STATE",
            boundary,
        )
        self.assertIn(
            "DIRECT_RAW_STATE_EXPORT_PLUS_COTIMED_METER_EXPORT_REQUIRED",
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
