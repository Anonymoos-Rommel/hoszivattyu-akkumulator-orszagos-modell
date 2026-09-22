import csv
import unittest
from pathlib import Path

from modules.B10.national_network_inference_layer import (
    NATIONAL_NETWORK_INFERENCE,
    Q_NATIONAL_NETWORK_INFERENCE,
    QUALIFIED_NATIONAL_BOUNDED_NETWORK_INFERENCE,
    assess_national_network_inference,
    blocker_repairs,
    current_evidence_surface,
    exact_claim_boundary,
    repaired_requirement,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b10_p67_national_network_inference_repair.csv"
DOC = ROOT / "docs" / "source_packs" / "P67_B10_NATIONAL_NETWORK_INFERENCE_LAYER.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B10P67NationalNetworkInferenceLayerTests(unittest.TestCase):
    def test_p64_spatial_surface_and_six_dso_sources_are_admitted(self):
        surface = current_evidence_surface()
        self.assertAlmostEqual(surface.resolved_spatial_share_pct, 96.767036)
        self.assertAlmostEqual(surface.unresolved_spatial_share_pct, 3.232964)
        self.assertEqual(surface.canonical_dso_count, 6)
        self.assertEqual(surface.bounded_node_source_dso_count, 6)
        self.assertEqual(surface.baseline_project_count, 2)
        self.assertEqual(surface.baseline_project_operator_count, 2)

    def test_complete_node_inventory_is_not_national_expected_impact_blocker(self):
        repair = repaired_requirement("NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY")
        self.assertEqual(repair.plane, NATIONAL_NETWORK_INFERENCE)
        self.assertEqual(
            repair.status,
            "RETIRED_AS_NATIONAL_EXPECTED_IMPACT_BLOCKER",
        )
        self.assertEqual(
            repair.replacement,
            "DEFENSIBLE_REPRESENTATIVE_NODE_COHORT_REQUIRED",
        )

    def test_repository_materialization_is_separate_from_model_use(self):
        repair = repaired_requirement(
            "PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED"
        )
        self.assertEqual(
            repair.status,
            "RETIRED_AS_PUBLIC_REPOSITORY_PREREQUISITE",
        )
        self.assertIn("RAW_REPUBLICATION", repair.exact_claim_boundary)

    def test_current_national_inference_stays_q_without_real_population_inputs(self):
        result = assess_national_network_inference(
            independent_dso_strata=2,
            programme_demand_distribution=False,
            representative_headroom_cohort=False,
            reinforcement_project_cohort=False,
            programme_incremental_capex_attribution=False,
            delivery_timing_distribution=False,
            managed_peak_survivability_model=False,
            population_calibration=False,
            uncertainty_explicit=False,
        )
        self.assertEqual(result.status, Q_NATIONAL_NETWORK_INFERENCE)
        self.assertIn(
            "DEFENSIBLE_PROGRAMME_DEMAND_DISTRIBUTION_BY_DSO_STRATUM_REQUIRED",
            result.blockers,
        )
        self.assertIn(
            "REPRESENTATIVE_REINFORCEMENT_COHORT_AND_INCREMENTAL_CAPEX_DISTRIBUTION_REQUIRED",
            result.blockers,
        )
        self.assertIn(
            "FEWER_THAN_PREFERRED_THREE_INDEPENDENT_DSO_STRATA",
            result.warnings,
        )

    def test_qualified_national_inference_does_not_require_complete_node_inventory(self):
        result = assess_national_network_inference(
            independent_dso_strata=3,
            programme_demand_distribution=True,
            representative_headroom_cohort=True,
            reinforcement_project_cohort=True,
            programme_incremental_capex_attribution=True,
            delivery_timing_distribution=True,
            managed_peak_survivability_model=True,
            population_calibration=True,
            uncertainty_explicit=True,
        )
        self.assertEqual(
            result.status,
            QUALIFIED_NATIONAL_BOUNDED_NETWORK_INFERENCE,
        )
        self.assertEqual(result.blockers, ())
        self.assertEqual(result.warnings, ())

    def test_exact_claim_boundary_remains_fail_closed(self):
        boundary = exact_claim_boundary()
        self.assertIn(
            "SPECIFIC_NODE_DEMAND_REQUIRES_EXACT_ENTITY_TO_NODE_MAPPING",
            boundary,
        )
        self.assertIn(
            "SPECIFIC_REINFORCEMENT_REQUIRES_AUTHORITATIVE_DSO_MGT_OR_NETWORK_STUDY",
            boundary,
        )
        self.assertIn(
            "SPECIFIC_PROGRAMME_INCREMENTAL_CAPEX_REQUIRES_EXACT_ATTRIBUTION_LINEAGE",
            boundary,
        )

    def test_all_nine_legacy_blockers_have_explicit_repairs(self):
        repairs = blocker_repairs()
        self.assertEqual(len(repairs), 9)
        self.assertEqual(len({x.legacy_blocker for x in repairs}), 9)

    def test_registry_and_document_freeze_nonpromotion_rules(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B10-P67-R03"]["status"],
            "RETIRED_AS_NATIONAL_EXPECTED_IMPACT_BLOCKER",
        )
        self.assertEqual(
            reg["B10-P67-R10"]["current_state"],
            "Q_NATIONAL_NETWORK_INFERENCE",
        )
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "NO COMPLETE NATIONAL NODE INVENTORY != NATIONAL MODEL BLOCKED",
            "NATIONAL NETWORK ESTIMATE != SPECIFIC NODE PASS/FAIL",
            "PUBLIC REPOSITORY MATERIALIZATION != MODEL USABILITY",
            "B10 remains **15%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
