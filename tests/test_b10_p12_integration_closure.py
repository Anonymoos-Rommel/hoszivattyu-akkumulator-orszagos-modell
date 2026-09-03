import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import (
    ACCEPTANCE_MANAGED_PEAK_SURVIVABILITY,
    ACCEPTANCE_NETWORK_LAYER_SEPARATION,
    ACCEPTANCE_QUESTION_HANDLING,
    ACCEPTANCE_REGIONAL_PENETRATION_HOSTING,
    ACCEPTANCE_SATISFIED,
    ACCEPTANCE_TIMED_INVESTMENT_PATHWAY,
    B10_CLOSURE_BLOCKED,
    B10IntegrationClosureError,
    CONTRACT_BOUNDED,
    CURRENT_LEGACY_ACCEPTANCE_MAPPINGS,
    OUTPUT_CONNECTION_DEMAND,
    OUTPUT_LIMITING_NODES,
    OUTPUT_REGIONAL_CAPEX,
    OUTPUT_TIMING,
    Q_UNRESOLVED,
    current_b10_closure_assessment,
    require_b10_closure_ready,
)


ROOT = Path(__file__).resolve().parents[1]


class B10P12IntegrationClosureTests(unittest.TestCase):
    def test_current_assessment_is_explicitly_blocked(self):
        result = current_b10_closure_assessment()
        self.assertEqual(B10_CLOSURE_BLOCKED, result.status)
        self.assertEqual("IN_PROGRESS", result.module_status)
        self.assertFalse(result.issue_should_close)
        self.assertEqual(15, result.readiness_percent)
        self.assertTrue(result.blocking_refs)

    def test_issue_acceptance_matrix_is_complete_and_unique(self):
        result = current_b10_closure_assessment()
        ids = [item.gate_id for item in result.acceptance_gates]
        self.assertEqual(
            {
                ACCEPTANCE_NETWORK_LAYER_SEPARATION,
                ACCEPTANCE_REGIONAL_PENETRATION_HOSTING,
                ACCEPTANCE_MANAGED_PEAK_SURVIVABILITY,
                ACCEPTANCE_TIMED_INVESTMENT_PATHWAY,
                ACCEPTANCE_QUESTION_HANDLING,
            },
            set(ids),
        )
        self.assertEqual(len(ids), len(set(ids)))

    def test_primary_output_matrix_is_complete_and_unpopulated(self):
        result = current_b10_closure_assessment()
        ids = [item.gate_id for item in result.output_gates]
        self.assertEqual(
            {OUTPUT_REGIONAL_CAPEX, OUTPUT_TIMING, OUTPUT_CONNECTION_DEMAND, OUTPUT_LIMITING_NODES},
            set(ids),
        )
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(item.status == Q_UNRESOLVED for item in result.output_gates))

    def test_contract_bounded_is_not_acceptance_satisfied(self):
        result = current_b10_closure_assessment()
        by_id = {item.gate_id: item for item in result.acceptance_gates}
        self.assertEqual(CONTRACT_BOUNDED, by_id[ACCEPTANCE_NETWORK_LAYER_SEPARATION].status)
        self.assertEqual(CONTRACT_BOUNDED, by_id[ACCEPTANCE_MANAGED_PEAK_SURVIVABILITY].status)
        self.assertEqual(CONTRACT_BOUNDED, by_id[ACCEPTANCE_TIMED_INVESTMENT_PATHWAY].status)
        self.assertEqual(ACCEPTANCE_SATISFIED, by_id[ACCEPTANCE_QUESTION_HANDLING].status)
        self.assertNotEqual(ACCEPTANCE_SATISFIED, by_id[ACCEPTANCE_NETWORK_LAYER_SEPARATION].status)

    def test_regional_hosting_remains_q_with_p15_membership_blockers(self):
        result = current_b10_closure_assessment()
        gate = next(item for item in result.acceptance_gates if item.gate_id == ACCEPTANCE_REGIONAL_PENETRATION_HOSTING)
        self.assertEqual(Q_UNRESOLVED, gate.status)
        self.assertIn("B10-P14", gate.canonical_refs)
        self.assertIn("B10-P15", gate.canonical_refs)
        self.assertIn("Q-B01-002", gate.blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", gate.blocking_refs)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", gate.blocking_refs)
        self.assertIn("REGIONAL_READINESS_HEADER_ONLY", gate.blocking_refs)
        self.assertNotIn("NO_NATIONAL_DSO_COVERAGE", gate.blocking_refs)
        self.assertNotIn("NO_NATIONAL_SERVICE_AREA_MEMBERSHIP_CROSSWALK", gate.blocking_refs)

    def test_legacy_q05_q07_are_source_scoped_not_global(self):
        result = current_b10_closure_assessment()
        gate = next(item for item in result.acceptance_gates if item.gate_id == ACCEPTANCE_QUESTION_HANDLING)
        self.assertEqual(ACCEPTANCE_SATISFIED, gate.status)
        self.assertEqual(("Q-05", "Q-07"), result.legacy_acceptance_labels)
        self.assertFalse(gate.blocking_refs)
        self.assertEqual(CURRENT_LEGACY_ACCEPTANCE_MAPPINGS, result.legacy_acceptance_mappings)

        by_label = {item.legacy_label: item for item in result.legacy_acceptance_mappings}
        self.assertEqual(
            ("B10-P10", "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY"),
            by_label["Q-05"].canonical_refs,
        )
        self.assertEqual(
            ("Q-B01-002", "Q-B10-001", "Q-B10-002", "B10-P11"),
            by_label["Q-07"].canonical_refs,
        )
        self.assertIn("V1.1_SECTION_11_B14_LOCAL_Q07_FINANCING", by_label["Q-07"].excluded_conflicts)

        mapping_doc = (ROOT / "docs/methodology/question_identifiers.md").read_text(encoding="utf-8")
        self.assertNotIn("\n| Q-05 |", mapping_doc)
        self.assertNotIn("\n| Q-07 |", mapping_doc)
        self.assertIn("Issue #10 — B10 legacy acceptance mapping", mapping_doc)
        self.assertIn("B14 finanszírozási fejezete szintén `Q-07`", mapping_doc)

    def test_legacy_identifier_blockers_are_removed_but_substantive_blockers_remain(self):
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertNotIn("LEGACY:Q-05", blockers)
        self.assertNotIn("LEGACY:Q-07", blockers)
        self.assertIn("NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY", blockers)
        self.assertIn("Q-B10-001", blockers)
        self.assertIn("Q-B10-002", blockers)

    def test_canonical_b10_and_spatial_questions_are_still_open(self):
        with (ROOT / "registry/open_questions.csv").open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B01-002", "Q-B10-001", "Q-B10-002"):
            self.assertIn(question_id, rows)
            self.assertEqual("OPEN", rows[question_id]["status"])

        result = current_b10_closure_assessment()
        self.assertEqual(
            (("Q-B01-002", "OPEN"), ("Q-B10-001", "OPEN"), ("Q-B10-002", "OPEN")),
            result.canonical_question_statuses,
        )

    def test_regional_readiness_registry_is_still_header_only(self):
        lines = (ROOT / "registry/regional_readiness.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("period,region_id,region_type,"))

    def test_incremental_capex_registry_is_still_header_only(self):
        lines = (ROOT / "registry/incremental_capex_attribution.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("attribution_id,baseline_id,intervention_id,"))

    def test_p15_membership_crosswalk_registry_is_still_header_only(self):
        lines = (ROOT / "registry/dso_service_area_membership_crosswalk.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("ksh_settlement_code,settlement_name,operator_id,"))

    def test_p16_national_node_inventory_registry_is_still_header_only(self):
        lines = (ROOT / "registry/dso_node_inventory.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("operator_id,network_operator,service_area_id,node_id,"))

    def test_module_registry_keeps_b10_in_progress_at_15(self):
        with (ROOT / "registry/module_status.csv").open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual("IN_PROGRESS", rows["B10"]["status"])
        self.assertEqual("15", rows["B10"]["readiness_percent"])

    def test_require_closure_ready_fails_on_current_state(self):
        with self.assertRaisesRegex(B10IntegrationClosureError, "do not mark module DONE"):
            require_b10_closure_ready(current_b10_closure_assessment())

    def test_p23_refines_active_node_source_blockers_without_closing_topology(self):
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertNotIn("NO_NATIONAL_DSO_COVERAGE", blockers)
        self.assertNotIn("NO_NATIONAL_SERVICE_AREA_MEMBERSHIP_CROSSWALK", blockers)
        self.assertNotIn("NO_NATIONAL_DSO_NODE_INVENTORY", blockers)
        self.assertNotIn("FOUR_DSO_NODE_SOURCE_DISCOVERY_UNRESOLVED", blockers)
        self.assertNotIn("ELMU_CONSUMPTION_NODE_SOURCE_UNRESOLVED", blockers)
        self.assertNotIn("EON_DDASZ_NODE_SOURCE_UNRESOLVED", blockers)
        self.assertNotIn("EON_EDASZ_NODE_SOURCE_UNRESOLVED", blockers)
        self.assertNotIn("MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED", blockers)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        self.assertIn("NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY", blockers)
        self.assertIn("Q-B10-P23-ELMU-2026-CONSUMPTION-PUBLICATION-URL", blockers)
        self.assertIn("Q-B10-P23-EON-DDASZ-2026-CONSUMPTION-PUBLICATION-URL", blockers)
        self.assertIn("Q-B10-P23-EON-EDASZ-2026-CONSUMPTION-PUBLICATION-URL", blockers)
        self.assertIn("PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED", blockers)
        self.assertIn("HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS", blockers)
        self.assertIn("Q-B01-002", blockers)

    def test_limiting_node_gate_references_p23_and_remains_q(self):
        result = current_b10_closure_assessment()
        gate = next(item for item in result.output_gates if item.gate_id == OUTPUT_LIMITING_NODES)
        self.assertEqual(Q_UNRESOLVED, gate.status)
        for ref in ("B10-P16", "B10-P17", "B10-P18", "B10-P19", "B10-P23"):
            self.assertIn(ref, gate.canonical_refs)
        self.assertIn("registry/dso_node_inventory_sources.csv", gate.canonical_refs)
        self.assertIn("registry/dso_consumption_publication_authorities.csv", gate.canonical_refs)
        self.assertIn("registry/dso_published_node_facts_p23.csv", gate.canonical_refs)
        self.assertIn("registry/dso_node_inventory.csv", gate.canonical_refs)
        self.assertIn("NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY", gate.blocking_refs)
        self.assertIn("Q-B10-P23-ELMU-2026-CONSUMPTION-PUBLICATION-URL", gate.blocking_refs)
        self.assertIn("PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED", gate.blocking_refs)
        self.assertIn("NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY", gate.blocking_refs)

    def test_blockers_cover_all_current_non_results(self):
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertTrue(
            {
                "Q-B01-002",
                "Q-B10-001",
                "Q-B10-002",
                "NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK",
                "PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED",
                "NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY",
                "Q-B10-P23-ELMU-2026-CONSUMPTION-PUBLICATION-URL",
                "Q-B10-P23-EON-DDASZ-2026-CONSUMPTION-PUBLICATION-URL",
                "Q-B10-P23-EON-EDASZ-2026-CONSUMPTION-PUBLICATION-URL",
                "PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED",
                "HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS",
                "REGIONAL_READINESS_HEADER_ONLY",
                "INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY",
                "NO_REAL_PROGRAMME_NODE_PANEL",
                "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY",
                "NO_REAL_TIMED_PROGRAMME_CAPEX",
            }.issubset(blockers)
        )


if __name__ == "__main__":
    unittest.main()
