import csv
import unittest
from pathlib import Path

from modules.B05.direct_defrost_state_acquisition import (
    CROSS_SYSTEM_LOGGING_FEASIBLE,
    EXACT_DIRECT_STATE_ADMITTED,
    PUBLIC_SURFACE_NO_DIRECT_STATE_ACQUIRED,
    Q_PRIVATE_EXPORT,
    CrossSystemLoggingEvidence,
    PublicDirectStateSurfaceEvidence,
    RawDirectStateExportEvidence,
    p37_boundary,
    qualify_cross_system_logging,
    qualify_public_surface,
    qualify_raw_direct_state,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p37_s2125_direct_state_public_acquisition.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p37_s2125_public_state_surface_inventory.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P37_S2125_DIRECT_STATE_PUBLIC_ACQUISITION.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def exact_public_surface():
    return PublicDirectStateSurfaceEvidence(
        public_feed_count=13,
        targeted_candidate_count=1,
        candidate_operation_mode_values=(10, 20, 30),
        public_input_names=(
            "OutdoorTemp",
            "FlowRate",
            "TargetSupplyTemp",
            "OperationMode",
            "ReturnTemp",
            "SupplyTemp",
            "CurPwr",
        ),
        direct_state_feed_bound=False,
        direct_state_input_bound=False,
        owner_private_direct_state_context=True,
    )


class B05P37DirectDefrostStateAcquisitionTests(unittest.TestCase):
    def test_public_surface_does_not_mint_direct_state(self):
        result = qualify_public_surface(exact_public_surface())
        self.assertFalse(result.direct_state_admitted)
        self.assertEqual(result.status, PUBLIC_SURFACE_NO_DIRECT_STATE_ACQUIRED)
        self.assertEqual(result.evidence_status, "DER")
        self.assertEqual(result.residual_gaps, (Q_PRIVATE_EXPORT,))

    def test_operation_mode_semantics_are_not_defrost_semantics(self):
        result = qualify_public_surface(exact_public_surface())
        self.assertIn("prioritisation", result.reason)

    def test_public_surface_result_does_not_claim_private_history_absence(self):
        result = qualify_public_surface(exact_public_surface())
        self.assertIn("private Home Assistant", result.reason)

    def test_cross_system_real_logger_proves_feasibility_only(self):
        result = qualify_cross_system_logging(
            CrossSystemLoggingEvidence(
                official_direct_register_bound=True,
                direct_state_values_explicit=True,
                real_history_pipeline_documented=True,
                exact_silkeborg_system=False,
            )
        )
        self.assertFalse(result.exact_event_admitted)
        self.assertTrue(result.logging_feasibility_proven)
        self.assertEqual(result.status, CROSS_SYSTEM_LOGGING_FEASIBLE)
        self.assertEqual(result.residual_gaps, (Q_PRIVATE_EXPORT,))

    def test_only_complete_exact_raw_state_is_admitted(self):
        blocked = qualify_raw_direct_state(
            RawDirectStateExportEvidence(
                exact_silkeborg_system=True,
                raw_timestamped=False,
                official_or_explicit_direct_state_binding=True,
                values_subset_0_1_2=True,
                complete_off_event_off_boundary=True,
            )
        )
        self.assertFalse(blocked.admitted)

        admitted = qualify_raw_direct_state(
            RawDirectStateExportEvidence(
                exact_silkeborg_system=True,
                raw_timestamped=True,
                official_or_explicit_direct_state_binding=True,
                values_subset_0_1_2=True,
                complete_off_event_off_boundary=True,
            )
        )
        self.assertTrue(admitted.admitted)
        self.assertEqual(admitted.status, EXACT_DIRECT_STATE_ADMITTED)
        self.assertEqual(admitted.evidence_status, "OBS")

    def test_inventory_preserves_bounded_public_findings(self):
        inv = {row["record_id"]: row for row in rows(INVENTORY)}
        self.assertIn("13 feeds", inv["B05-P37-E01"]["observed_identity"])
        self.assertEqual(inv["B05-P37-E02"]["observed_values"], "10;20;30")
        self.assertIn("OutdoorTemp", inv["B05-P37-E04"]["observed_identity"])
        self.assertEqual(inv["B05-P37-E06"]["direct_defrost_identity"], "YES")
        self.assertEqual(inv["B05-P37-E06"]["system_scope"], "CROSS_SYSTEM_S2125")

    def test_registry_narrows_exact_residual_without_closing_it(self):
        reg = {row["claim"]: row for row in rows(REG)}
        old = reg["SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED"]
        self.assertEqual(
            old["status"],
            "OPEN_NARROWED_TO_PRIVATE_HA_HISTORY_OR_NEW_1805_LOGGER_EXPORT",
        )
        self.assertEqual(
            old["residual_gap"],
            "SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED",
        )
        new = reg["SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED"]
        self.assertEqual(new["status"], "OPEN")
        self.assertEqual(new["evidence_status"], "Q")

    def test_operation_mode_is_forbidden_as_direct_defrost(self):
        reg = {row["claim"]: row for row in rows(REG)}
        row = reg["SILKEBORG_OPERATION_MODE_501344_AS_DIRECT_DEFROST"]
        self.assertEqual(row["status"], "FORBIDDEN")
        self.assertIn("10_20_30", row["resolved_scope"])

    def test_shared_variables_keep_event_series_q(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(
            variables["VAR-B05-SILKEBORG-S2125-DIRECT-STATE-EXPORT"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-NIBE-DEFROST-COTIMED-EVENT-SERIES"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-SILKEBORG-S2125-PUBLIC-DIRECT-STATE-SURFACE"]["status"],
            "DER",
        )

    def test_question_and_readiness_remain_open(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "OPEN_NARROWED_TO_PRIVATE_DIRECT_STATE_EXPORT_WEATHER_TO_BT16_AND_CROSS_PRODUCT",
            q["notes"],
        )
        self.assertIn(
            "SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED",
            q["notes"],
        )
        self.assertIn("No numeric event kWh is admitted", q["notes"])

        readiness = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(readiness["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

    def test_sources_pin_probe_and_cross_system_routes(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-P37-SILKEBORG-PUBLIC-FEED-CANDIDATE-PROBE-2026",
            "SRC-B05-P37-SILKEBORG-OPMODE-SEMANTICS-PROBE-2026",
            "SRC-B05-P37-SILKEBORG-PUBLIC-INPUT-PROBE-2026",
            "SRC-B05-P37-SILKEBORG-PUBLIC-INPUT-INVENTORY-2026",
            "SRC-B05-NIBE2MQTT-S2125-DIRECT-STATE-E3922C-2023",
            "SRC-B05-S2125-HA-INFLUX-DIRECT-STATE-FIELD-2023",
        ):
            self.assertIn(source_id, sources)

    def test_no_read_credential_is_committed(self):
        for path in (PACK, INVENTORY, REG):
            self.assertNotIn("readkey=", path.read_text(encoding="utf-8"))

    def test_docs_and_boundaries_are_pinned(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("Operation Mode", text)
        self.assertIn("OutdoorTemp", text)
        self.assertIn("PRIVATE_HA_HISTORY_OR_NEW_1805_LOGGER_EXPORT", text)
        self.assertIn("DEFROST: 20% -> 20%", text)
        self.assertIn("B05-P37", README.read_text(encoding="utf-8"))

        boundary = p37_boundary()
        self.assertIn(
            "OPERATION_PRIORITISATION_10_20_30 != DIRECT_DEFROST_STATE_0_1_2",
            boundary,
        )
        self.assertIn(
            "CROSS_SYSTEM_S2125_DIRECT_STATE_LOGGING != EXACT_SILKEBORG_RAW_EVENT",
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
