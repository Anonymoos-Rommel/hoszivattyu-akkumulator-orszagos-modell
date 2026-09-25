import csv
import unittest
from pathlib import Path

from modules.B05.public_s2125_direct_event_acquisition import (
    COMPLETE_EVENT_PACKAGE_ADMITTED,
    PUBLIC_FLEET_AUDIT_BOUNDED,
    Q_COMPLETE_EVENT_PACKAGE,
    CompleteEventPackageEvidence,
    PublicFleetAuditEvidence,
    p38_boundary,
    qualify_complete_event_package,
    qualify_public_fleet_audit,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p38_public_s2125_direct_event_acquisition.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p38_public_s2125_fleet_inventory.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P38_PUBLIC_S2125_DIRECT_EVENT_ACQUISITION.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def exact_p38_fleet():
    return PublicFleetAuditEvidence(
        public_system_count=809,
        s2125_system_ids=(252, 448, 660, 729),
        audited_system_ids=(252, 448, 660, 729),
        direct_candidate_counts=(0, 0, 0, 0),
        energy_keys_present_for_all=True,
        underlying_public_routes_audited=True,
    )


class B05P38PublicS2125DirectEventAcquisitionTests(unittest.TestCase):
    def test_fleet_audit_is_bounded_not_global_absence(self):
        result = qualify_public_fleet_audit(exact_p38_fleet())
        self.assertFalse(result.complete_public_event_acquired)
        self.assertEqual(result.status, PUBLIC_FLEET_AUDIT_BOUNDED)
        self.assertEqual(result.evidence_status, "DER")
        self.assertFalse(result.global_absence_proven)
        self.assertEqual(result.residual_gaps, (Q_COMPLETE_EVENT_PACKAGE,))

    def test_incomplete_fleet_does_not_qualify_bounded_result(self):
        result = qualify_public_fleet_audit(
            PublicFleetAuditEvidence(
                public_system_count=809,
                s2125_system_ids=(252, 448, 660, 729),
                audited_system_ids=(252, 448, 660),
                direct_candidate_counts=(0, 0, 0),
                energy_keys_present_for_all=True,
                underlying_public_routes_audited=True,
            )
        )
        self.assertEqual(result.evidence_status, "Q")

    def test_complete_event_package_requires_every_physical_component(self):
        blocked = qualify_complete_event_package(
            CompleteEventPackageEvidence(
                exact_s2125_system=True,
                raw_timestamped_direct_state=True,
                state_values_subset_0_1_2=True,
                complete_off_event_off_boundary=True,
                electric_energy_observed=True,
                thermal_energy_observed=False,
                common_timebase=True,
                machine_readable=True,
            )
        )
        self.assertFalse(blocked.admitted)

        admitted = qualify_complete_event_package(
            CompleteEventPackageEvidence(
                exact_s2125_system=True,
                raw_timestamped_direct_state=True,
                state_values_subset_0_1_2=True,
                complete_off_event_off_boundary=True,
                electric_energy_observed=True,
                thermal_energy_observed=True,
                common_timebase=True,
                machine_readable=True,
            )
        )
        self.assertTrue(admitted.admitted)
        self.assertEqual(admitted.status, COMPLETE_EVENT_PACKAGE_ADMITTED)
        self.assertEqual(admitted.evidence_status, "OBS")

    def test_public_inventory_contains_all_four_s2125_systems(self):
        inv = {row["system_id"]: row for row in rows(INVENTORY)}
        self.assertEqual(set(("252", "448", "660", "729")).issubset(inv), True)
        for sid in ("252", "448", "660", "729"):
            self.assertEqual(inv[sid]["direct_state_candidate_count"], "0")
            self.assertEqual(inv[sid]["public_complete_event_package"], "NO")

    def test_mid_metered_systems_still_have_no_direct_state_surface(self):
        inv = {row["system_id"]: row for row in rows(INVENTORY)}
        for sid in ("448", "660", "729"):
            self.assertIn("SDM120", inv[sid]["electric_meter"])
            self.assertIn("Axioma", inv[sid]["heat_meter"])
            self.assertEqual(inv[sid]["direct_state_candidate_count"], "0")

    def test_registry_creates_product_level_complete_event_residual(self):
        reg = {row["claim"]: row for row in rows(REG)}
        event = reg["S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED"]
        self.assertEqual(event["status"], "OPEN")
        self.assertEqual(event["evidence_status"], "Q")
        self.assertEqual(
            event["residual_gap"],
            "S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED",
        )
        self.assertEqual(
            reg["PUBLIC_FLEET_ZERO_CANDIDATES_AS_GLOBAL_SOURCE_ABSENCE"]["status"],
            "FORBIDDEN",
        )

    def test_silkeborg_route_remains_valid_but_is_not_only_route(self):
        reg = {row["claim"]: row for row in rows(REG)}
        row = reg["SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED"]
        self.assertEqual(row["status"], "OPEN_VALID_ROUTE")
        self.assertEqual(
            row["residual_gap"],
            "S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED",
        )

    def test_shared_event_series_stays_q_and_public_fleet_is_der(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(
            variables["VAR-B05-NIBE-DEFROST-COTIMED-EVENT-SERIES"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-S2125-PUBLIC-FLEET-DIRECT-EVENT-SURFACE"]["status"],
            "DER",
        )

    def test_question_hands_next_priority_to_weather_bt16(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_WEATHER_TO_BT16_AND_CROSS_PRODUCT",
            q["notes"],
        )
        self.assertIn("S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED", q["notes"])
        self.assertIn("WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED", q["notes"])
        self.assertIn("No numeric event kWh is admitted", q["notes"])

    def test_readiness_does_not_increase_for_search_effort(self):
        readiness = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(readiness["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

    def test_sources_pin_fleet_and_route_probes(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-P38-HPM-S2125-FLEET-SCAN-2026",
            "SRC-B05-P38-HPM-S2125-PUBLIC-ROUTE-SCAN-2026",
            "SRC-B05-S2125-HA-MULTISIGNAL-HISTORYGRAPH-2024",
        ):
            self.assertIn(source_id, sources)

    def test_no_raw_third_party_payload_or_readkey_is_committed(self):
        for path in (PACK, INVENTORY, REG):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("readkey=", text)
            self.assertNotIn("apikey=", text)

    def test_docs_readme_and_boundaries_are_pinned(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("public S2125 systems: 4", text)
        self.assertIn("S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED", text)
        self.assertIn("WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED", text)
        self.assertIn("DEFROST: 20% -> 20%", text)
        self.assertIn("B05-P38", README.read_text(encoding="utf-8"))

        boundary = p38_boundary()
        self.assertIn(
            "PUBLIC_FLEET_SCAN_WITH_ZERO_DIRECT_FEEDS != GLOBAL_SOURCE_ABSENCE",
            boundary,
        )
        self.assertIn(
            "STATE_FROM_SYSTEM_A + ENERGY_FROM_SYSTEM_B != ADMISSIBLE_EVENT_ENERGY",
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
