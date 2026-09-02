from dataclasses import replace
import csv
from pathlib import Path
import unittest

from modules.B10.baseline_infrastructure_contract import (
    B10BaselineInfrastructureContractError,
    BASELINE,
    CostAttribution,
    InfrastructureEvidence,
    classify_infrastructure,
)
from modules.B10.dso_headroom_contract import DsoHeadroomRecord, assess_incremental_demand
from modules.B10.rrf_baseline_ledger import (
    DSO_SERVICE_AREA,
    MVM_DEMASZ_RRF_COMPLETION_SOURCE_ID,
    MVM_DEMASZ_RRF_PROJECT_SOURCE_ID,
    OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID,
    OPUS_TITASZ_RRF_PROJECT_SOURCE_ID,
    RRF_BASELINE_RECORDS,
    classify_observed_baseline_projects,
    validate_observed_baseline_record,
)


ROOT = Path(__file__).resolve().parents[1]


class B10P4ObservedBaselineRrfTests(unittest.TestCase):
    def test_exactly_two_observed_baseline_projects_classify_through_p3(self):
        decisions = classify_observed_baseline_projects()
        self.assertEqual(2, len(decisions))
        self.assertTrue(all(item.attribution_status == BASELINE for item in decisions))
        self.assertTrue(all(item.evidence_status == "OBS" for item in decisions))

    def test_mvm_planning_page_without_completion_cannot_mint_operating(self):
        record = replace(
            RRF_BASELINE_RECORDS[0],
            source_refs=(MVM_DEMASZ_RRF_PROJECT_SOURCE_ID,),
        )
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "completion source"):
            validate_observed_baseline_record(record)
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)

    def test_opus_planning_page_without_completion_cannot_mint_operating(self):
        record = replace(
            RRF_BASELINE_RECORDS[1],
            source_refs=(OPUS_TITASZ_RRF_PROJECT_SOURCE_ID,),
        )
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "completion source"):
            validate_observed_baseline_record(record)
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)

    def test_wrong_project_id_binding_fails_closed(self):
        record = replace(RRF_BASELINE_RECORDS[0], project_id=RRF_BASELINE_RECORDS[1].project_id)
        with self.assertRaises(B10BaselineInfrastructureContractError):
            validate_observed_baseline_record(record)

    def test_completion_evidence_for_one_project_cannot_promote_another(self):
        record = replace(
            RRF_BASELINE_RECORDS[0],
            project_id=RRF_BASELINE_RECORDS[1].project_id,
        )
        with self.assertRaises(B10BaselineInfrastructureContractError):
            validate_observed_baseline_record(record)

    def test_generic_company_or_news_page_cannot_replace_status_evidence(self):
        evidence = InfrastructureEvidence(
            source_id="SRC-B10-GENERIC-COMPANY-2026",
            authority_level=2,
            truth_status="OBS",
            effective_date="2026-06-15",
            revision="CURRENT_2026",
            supports=("PROJECT_ID", "OPERATOR"),
        )
        record = replace(
            RRF_BASELINE_RECORDS[0],
            source_refs=(evidence.source_id,),
            evidence=(evidence,),
        )
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)

    def test_mvm_grant_rate_cannot_mint_exact_observed_total_cost(self):
        record = replace(RRF_BASELINE_RECORDS[0], total_project_cost_huf=85_818_375_654)
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "not source-authorised"):
            validate_observed_baseline_record(record)

    def test_mvm_total_cost_and_program_incremental_cost_remain_blank(self):
        record = RRF_BASELINE_RECORDS[0]
        self.assertIsNone(record.total_project_cost_huf)
        self.assertIsNone(record.incremental_cost_huf)
        with (ROOT / "registry" / "baseline_infrastructure.csv").open(newline="", encoding="utf-8") as handle:
            row = next(item for item in csv.DictReader(handle) if item["project_id"] == record.project_id)
        self.assertEqual("", row["counterfactual_cost_huf"])
        self.assertEqual("", row["program_incremental_cost_huf"])

    def test_opus_exact_source_supported_total_cost_is_accepted(self):
        record = RRF_BASELINE_RECORDS[1]
        self.assertEqual(41_489_280_000, record.total_project_cost_huf)
        self.assertIn(OPUS_TITASZ_RRF_PROJECT_SOURCE_ID, record.source_refs)
        self.assertIn(OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID, record.source_refs)
        decision = classify_observed_baseline_projects((record,))[0]
        self.assertEqual(BASELINE, decision.attribution_status)
        self.assertEqual(41_489_280_000, decision.baseline_cost_huf)

    def test_opus_exact_cost_completion_only_provenance_is_rejected(self):
        record = replace(
            RRF_BASELINE_RECORDS[1],
            source_refs=(OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID,),
        )
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "project/funding source"):
            validate_observed_baseline_record(record)

    def test_opus_exact_cost_requires_referenced_cost_support(self):
        project = next(
            item for item in RRF_BASELINE_RECORDS[1].evidence
            if item.source_id == OPUS_TITASZ_RRF_PROJECT_SOURCE_ID
        )
        completion = next(
            item for item in RRF_BASELINE_RECORDS[1].evidence
            if item.source_id == OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID
        )
        weakened_project = InfrastructureEvidence(
            source_id=project.source_id,
            authority_level=project.authority_level,
            truth_status=project.truth_status,
            effective_date=project.effective_date,
            revision=project.revision,
            supports=tuple(item for item in project.supports if item != "COST"),
        )
        record = replace(RRF_BASELINE_RECORDS[1], evidence=(weakened_project, completion))
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "support exact OBS COST"):
            validate_observed_baseline_record(record)

    def test_opus_completion_source_does_not_claim_exact_cost_support(self):
        completion = next(
            item for item in RRF_BASELINE_RECORDS[1].evidence
            if item.source_id == OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID
        )
        self.assertNotIn("COST", completion.supports)

    def test_opus_completion_remains_required_for_operating(self):
        record = replace(
            RRF_BASELINE_RECORDS[1],
            source_refs=(OPUS_TITASZ_RRF_PROJECT_SOURCE_ID,),
        )
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "completion source"):
            validate_observed_baseline_record(record)

    def test_dso_service_area_cannot_enter_dso_substation_assessment(self):
        row = DsoHeadroomRecord(
            station_name="Example",
            station_code="ABCD",
            voltage_kv=132,
            horizon="CURRENT",
            n_minus_1_capacity_mw=None,
            winter_evening_peak_load_mw=None,
            theoretical_free_capacity_mw=None,
            evidence_status="Q",
            source_refs=("SRC-B10-HEADROOM",),
        )
        with self.assertRaisesRegex(ValueError, "exactly match"):
            assess_incremental_demand(
                row,
                incremental_demand_mw=1,
                demand_region_id="MVM_DEMASZ:SERVICE_AREA",
                demand_region_scheme=DSO_SERVICE_AREA,
                demand_evidence_status="OBS",
                demand_source_refs=(MVM_DEMASZ_RRF_COMPLETION_SOURCE_ID,),
            )

    def test_rrf_capacity_figures_preserve_source_semantics(self):
        source_pack = (ROOT / "docs" / "source_packs" / "P4_B10_OBSERVED_BASELINE_RRF_PROJECTS.md").read_text(encoding="utf-8")
        self.assertIn("782 MW realised", source_pack)
        self.assertIn("378 MW as its", source_pack)
        self.assertIn("261 MW realised", source_pack)
        self.assertIn("378\nMW figure is not called realised completion capacity", source_pack)
        self.assertIn("household heat-pump consumption headroom", source_pack)
        self.assertTrue(all(item.region_grain == DSO_SERVICE_AREA for item in RRF_BASELINE_RECORDS))

    def test_no_national_headroom_or_sum_is_published(self):
        with (ROOT / "registry" / "regional_readiness.csv").open(newline="", encoding="utf-8") as handle:
            self.assertFalse(any(row.get("region_type") == "NATIONAL" for row in csv.DictReader(handle)))
        with (ROOT / "registry" / "baseline_infrastructure.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(2, len(rows))

    def test_mgt_required_semantics_remain_unchanged(self):
        self.assertEqual("MGT_REQUIRED", DsoHeadroomRecord.__dataclass_fields__["connection_authority"].default)

    def test_baseline_incremental_double_count_guard_remains_intact(self):
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "both baseline"):
            CostAttribution("P", "COMPONENT", 100, 1, "PROGRAM_ACCELERATED_OR_UPSIZED", ("SRC",))

    def test_headroom_evidence_alone_cannot_prove_project_completion(self):
        evidence = InfrastructureEvidence(
            source_id="SRC-B10-MVM-DEMASZ-CONSUMPTION-HEADROOM-2026",
            authority_level=1,
            truth_status="OBS",
            effective_date="2026-06-15",
            revision="CURRENT_2026",
            supports=("COST",),
        )
        record = replace(RRF_BASELINE_RECORDS[0], source_refs=(evidence.source_id,), evidence=(evidence,))
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)

    def test_unreferenced_completion_evidence_cannot_satisfy_gate(self):
        record = replace(
            RRF_BASELINE_RECORDS[0],
            source_refs=(MVM_DEMASZ_RRF_PROJECT_SOURCE_ID,),
        )
        self.assertEqual("Q", classify_infrastructure(record).attribution_status)


if __name__ == "__main__":
    unittest.main()
