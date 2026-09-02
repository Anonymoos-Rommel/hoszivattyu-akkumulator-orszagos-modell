import unittest

from modules.B10.baseline_infrastructure_contract import (
    ANNOUNCED_UNFUNDED,
    BASELINE,
    BUDGETED_OR_ALLOCATED,
    CONTRACTED,
    CostAttribution,
    InfrastructureEvidence,
    InfrastructureRecord,
    PROGRAM_ACCELERATED,
    PROGRAM_INCREMENTAL,
    UNRESOLVED,
    UNDER_CONSTRUCTION,
    OPEN_TENDER,
    OPERATING,
    B10BaselineInfrastructureContractError,
    classify_infrastructure,
    validate_attribution_ledger,
)


def evidence(*, supports=(), level=3, source_id="SRC-B10-AUTH-2026", truth="OBS"):
    return InfrastructureEvidence(
        source_id=source_id,
        authority_level=level,
        truth_status=truth,
        effective_date="2026-08-01",
        revision="REV-2026-08-01",
        supports=tuple(supports),
    )


def record(status=CONTRACTED, **kwargs):
    default_support = {
        OPERATING: ("OPERATING",),
        UNDER_CONSTRUCTION: ("UNDER_CONSTRUCTION",),
        CONTRACTED: ("CONTRACTED",),
        BUDGETED_OR_ALLOCATED: ("FUNDED_OR_ALLOCATED",),
    }.get(status, ())
    ev = kwargs.pop("evidence", (evidence(supports=default_support),))
    default_without = kwargs.pop("without_program_required", status not in {ANNOUNCED_UNFUNDED, OPEN_TENDER})
    default_with = kwargs.pop("with_program_required", status not in {ANNOUNCED_UNFUNDED, OPEN_TENDER})
    default_commitment = {
        CONTRACTED: "CONTRACTED",
        BUDGETED_OR_ALLOCATED: "FUNDED_OR_ALLOCATED",
    }.get(status)
    return InfrastructureRecord(
        project_id=kwargs.pop("project_id", "PROJECT-001"),
        network_operator="DSO-A",
        owner="DSO-A",
        region_id="DSO-A:REGION-1",
        region_grain="DSO_REGION",
        infrastructure_type="SUBSTATION_REINFORCEMENT",
        status_taxonomy=status,
        status_effective_date="2026-08-01",
        source_refs=kwargs.pop("source_refs", tuple(item.source_id for item in ev)),
        evidence=ev,
        evidence_status=kwargs.pop("evidence_status", "OBS"),
        contractual_or_funding_status=kwargs.pop("contractual_or_funding_status", default_commitment),
        without_program_required=default_without,
        with_program_required=default_with,
        **kwargs,
    )


class B10BaselineInfrastructureTests(unittest.TestCase):
    def test_operating_contracted_and_allocated_are_baseline(self):
        for status in (OPERATING, UNDER_CONSTRUCTION, CONTRACTED, BUDGETED_OR_ALLOCATED):
            decision = classify_infrastructure(record(status))
            self.assertEqual(BASELINE, decision.attribution_status)

    def test_announced_unfunded_is_not_promoted_to_baseline(self):
        decision = classify_infrastructure(record(ANNOUNCED_UNFUNDED))
        self.assertEqual(UNRESOLVED, decision.attribution_status)
        self.assertIn("announced", decision.reason)

    def test_open_tender_is_not_funding_evidence(self):
        decision = classify_infrastructure(record(OPEN_TENDER))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_missing_effective_date_is_q(self):
        item = evidence()
        item = InfrastructureEvidence(item.source_id, item.authority_level, item.truth_status, None, item.revision)
        decision = classify_infrastructure(record(evidence=(item,)))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_temporal_coincidence_does_not_prove_causality(self):
        decision = classify_infrastructure(record(
            UNDER_CONSTRUCTION,
            temporal_coincidence_only=True,
            program_causality_status="Q",
        ))
        self.assertEqual(BASELINE, decision.attribution_status)
        self.assertIn("not proven", decision.reason)

    def test_program_incremental_requires_explicit_difference(self):
        decision = classify_infrastructure(record(
            ANNOUNCED_UNFUNDED,
            program_causality_status="DER",
        ))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_incremental_scope_without_cost_remains_unquantified(self):
        decision = classify_infrastructure(record(
            ANNOUNCED_UNFUNDED,
            program_causality_status="DER",
            incremental_scope_proven=True,
            without_program_required=False,
            with_program_required=True,
        ))
        self.assertEqual(PROGRAM_INCREMENTAL, decision.attribution_status)
        self.assertIsNone(decision.incremental_cost_huf)
        self.assertEqual("Q", decision.evidence_status)

    def test_acceleration_cost_requires_cost_authority_and_is_not_full_cost(self):
        ev = (evidence(supports=("CONTRACTED", "COST")),)
        decision = classify_infrastructure(record(
            CONTRACTED,
            evidence=ev,
            program_causality_status="DER",
            acceleration_proven=True,
            without_program_required=True,
            with_program_required=True,
            baseline_cost_huf=90,
            incremental_cost_huf=10,
            total_project_cost_huf=100,
            contractual_or_funding_status="CONTRACTED",
        ))
        self.assertEqual(PROGRAM_ACCELERATED, decision.attribution_status)
        self.assertEqual(10, decision.incremental_cost_huf)

    def test_total_cost_copy_is_rejected(self):
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "copied"):
            record(
                CONTRACTED,
                total_project_cost_huf=100,
                incremental_cost_huf=100,
            )

    def test_unsupported_numeric_capex_stays_q(self):
        decision = classify_infrastructure(record(CONTRACTED, total_project_cost_huf=100))
        self.assertEqual(UNRESOLVED, decision.attribution_status)
        self.assertIsNone(decision.baseline_cost_huf)

    def test_program_causality_cannot_be_obs(self):
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "cannot be OBS"):
            record(CONTRACTED, program_causality_status="OBS")

    def test_wrong_source_identity_fails_closed(self):
        with self.assertRaises(B10BaselineInfrastructureContractError):
            InfrastructureRecord(
                project_id="P",
                network_operator="D",
                owner="D",
                region_id="R",
                region_grain="DSO_REGION",
                infrastructure_type="LINE",
                status_taxonomy=CONTRACTED,
                status_effective_date="2026-08-01",
                source_refs=("SRC-WRONG",),
                evidence=(evidence(),),
                evidence_status="OBS",
            )

    def test_cost_component_cannot_be_baseline_and_incremental(self):
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "both baseline"):
            CostAttribution("P", "LINE-1", 100, 5, PROGRAM_ACCELERATED, ("SRC",))

    def test_ledger_rejects_duplicate_project_component(self):
        projects = [record(project_id="P")]
        rows = [
            CostAttribution("P", "LINE-1", 100, None, BASELINE, ("SRC",)),
            CostAttribution("P", "LINE-1", None, 5, PROGRAM_INCREMENTAL, ("SRC",)),
        ]
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "duplicate"):
            validate_attribution_ledger(projects, rows)

    def test_ledger_rejects_announced_baseline(self):
        projects = [record(ANNOUNCED_UNFUNDED, project_id="P")]
        rows = [CostAttribution("P", "LINE-1", 100, None, BASELINE, ("SRC",))]
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "ANNOUNCED"):
            validate_attribution_ledger(projects, rows)

    def test_missing_is_not_zero(self):
        decision = classify_infrastructure(record(ANNOUNCED_UNFUNDED, program_causality_status="DER", incremental_scope_proven=True, without_program_required=False, with_program_required=True))
        self.assertIsNone(decision.incremental_cost_huf)

    def test_contracted_without_contract_support_is_q(self):
        decision = classify_infrastructure(record(CONTRACTED, contractual_or_funding_status=None))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_budgeted_without_funding_support_is_q(self):
        decision = classify_infrastructure(record(BUDGETED_OR_ALLOCATED, contractual_or_funding_status=None))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_under_construction_generic_notice_is_q(self):
        decision = classify_infrastructure(record(UNDER_CONSTRUCTION, evidence=(evidence(),)))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_operating_generic_authority_is_q(self):
        decision = classify_infrastructure(record(OPERATING, evidence=(evidence(),)))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_open_tender_cannot_satisfy_contracted_semantics(self):
        ev = (evidence(supports=("CONTRACTED",)),)
        decision = classify_infrastructure(record(OPEN_TENDER, evidence=ev, contractual_or_funding_status="CONTRACTED"))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_announced_unfunded_cannot_satisfy_funding_semantics(self):
        ev = (evidence(supports=("FUNDED_OR_ALLOCATED",)),)
        decision = classify_infrastructure(record(ANNOUNCED_UNFUNDED, evidence=ev, contractual_or_funding_status="FUNDED_OR_ALLOCATED"))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_record_truth_obs_cannot_promote_referenced_q(self):
        ev = (evidence(supports=("CONTRACTED",), truth="Q"),)
        decision = classify_infrastructure(record(CONTRACTED, evidence=ev, evidence_status="OBS"))
        self.assertEqual(UNRESOLVED, decision.attribution_status)
        self.assertEqual("Q", decision.evidence_status)

    def test_referenced_ass_or_scn_cannot_become_obs_baseline(self):
        for truth in ("ASS", "SCN"):
            ev = (evidence(supports=("CONTRACTED",), truth=truth),)
            decision = classify_infrastructure(record(CONTRACTED, evidence=ev, evidence_status="OBS"))
            self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_unreferenced_authority_cannot_satisfy_status_gate(self):
        generic = evidence(source_id="SRC-REFERENCED")
        status = evidence(source_id="SRC-UNREFERENCED", supports=("CONTRACTED",), level=1)
        decision = classify_infrastructure(record(
            CONTRACTED,
            evidence=(generic, status),
            source_refs=(generic.source_id,),
            contractual_or_funding_status="CONTRACTED",
        ))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_unreferenced_cost_evidence_cannot_authorize_capex(self):
        relevant = evidence(source_id="SRC-STATUS", supports=("CONTRACTED",))
        cost = evidence(source_id="SRC-COST", supports=("COST",), level=1)
        decision = classify_infrastructure(record(
            CONTRACTED,
            evidence=(relevant, cost),
            source_refs=(relevant.source_id,),
            total_project_cost_huf=100,
            contractual_or_funding_status="CONTRACTED",
        ))
        self.assertEqual(UNRESOLVED, decision.attribution_status)

    def test_referenced_contract_support_still_passes_baseline(self):
        decision = classify_infrastructure(record(CONTRACTED, evidence=(evidence(supports=("CONTRACTED",)),)))
        self.assertEqual(BASELINE, decision.attribution_status)

    def test_referenced_funding_support_still_passes_baseline(self):
        decision = classify_infrastructure(record(BUDGETED_OR_ALLOCATED, evidence=(evidence(supports=("FUNDED_OR_ALLOCATED",)),)))
        self.assertEqual(BASELINE, decision.attribution_status)


if __name__ == "__main__":
    unittest.main()

