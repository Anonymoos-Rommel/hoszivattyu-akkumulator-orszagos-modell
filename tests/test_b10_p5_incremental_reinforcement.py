from dataclasses import replace
import unittest

from modules.B10.baseline_infrastructure_contract import (
    ANNOUNCED_UNFUNDED,
    B10BaselineInfrastructureContractError,
    InfrastructureEvidence,
    InfrastructureRecord,
    PROGRAM_INCREMENTAL,
)
from modules.B10.dso_headroom_contract import (
    CURRENT,
    FIVE_YEAR,
    DsoHeadroomRecord,
    HeadroomAssessment,
)
from modules.B10.incremental_reinforcement_contract import (
    ACCELERATION,
    ACCELERATION_COST,
    B10IncrementalReinforcementContractError,
    COST_COMPONENT_BINDING_PREFIX,
    CUSTOMER_CONNECTION_CHARGE,
    DSO_SUBSTATION,
    EXCEEDS_PUBLISHED_HEADROOM_SCREENING,
    HORIZON_BINDING_PREFIX,
    INCREMENTAL_SCOPE,
    NETWORK_OPERATOR_BINDING_PREFIX,
    PROGRAM_INCREMENTAL_COST,
    PROJECT_BINDING_PREFIX,
    REGION_BINDING_PREFIX,
    REGION_GRAIN_BINDING,
    REINFORCEMENT_REQUIRED,
    SCREENING_Q,
    TOTAL_REINFORCEMENT_PROJECT_COST,
    UPSIZE,
    UPSIZE_COST,
    WITHIN_PUBLISHED_HEADROOM_SCREENING,
    HeadroomScreeningContext,
    evaluate_programme_incremental_reinforcement,
    screening_context_from_headroom_assessment,
)
from modules.B10.rrf_baseline_ledger import RRF_BASELINE_RECORDS


PROJECT_ID = "P5-SCN-PROJECT"
REGION_ID = "MVM_DEMASZ:ABCD:132KV"
OPERATOR = "DEMASZ"
COMPONENT = "TX-UPSIZING-1"
STATUS_SOURCE = "SRC-P5-STATUS"
REINFORCEMENT_SOURCE = "SRC-P5-REINFORCEMENT"
COST_SOURCE = "SRC-P5-COST"


def bindings(project_id=PROJECT_ID, region_id=REGION_ID, operator=OPERATOR, horizon=CURRENT):
    return (
        f"{PROJECT_BINDING_PREFIX}{project_id}",
        f"{NETWORK_OPERATOR_BINDING_PREFIX}{operator}",
        f"{REGION_BINDING_PREFIX}{region_id}",
        REGION_GRAIN_BINDING,
        f"{HORIZON_BINDING_PREFIX}{horizon}",
    )


def evidence(source_id, *, level=2, truth="DER", supports=()):
    return InfrastructureEvidence(
        source_id=source_id,
        authority_level=level,
        truth_status=truth,
        effective_date="2026-09-02",
        revision="P5-SCN-2026-09-02",
        supports=tuple(supports),
    )


def incremental_record(
    *,
    reinforcement_claims=(REINFORCEMENT_REQUIRED, INCREMENTAL_SCOPE),
    cost_claims=(),
    incremental_cost_huf=None,
    cost_component_id=None,
    project_id=PROJECT_ID,
    region_id=REGION_ID,
    operator=OPERATOR,
    horizon=CURRENT,
    program_causality_status="DER",
    incremental_scope_proven=True,
    incremental_capacity_proven=False,
    acceleration_proven=False,
    upsizing_proven=False,
    extra_evidence=(),
):
    bind = bindings(project_id, region_id, operator, horizon)
    status = evidence(
        STATUS_SOURCE,
        level=2,
        truth="DER",
        supports=("PROJECT_ID", *bind),
    )
    reinforcement = evidence(
        REINFORCEMENT_SOURCE,
        level=2,
        truth="DER",
        supports=(*reinforcement_claims, *bind),
    )
    ev = [status, reinforcement]
    if cost_claims:
        ev.append(
            evidence(
                COST_SOURCE,
                level=3,
                truth="DER",
                supports=(
                    "COST",
                    *cost_claims,
                    *bind,
                    f"{COST_COMPONENT_BINDING_PREFIX}{cost_component_id or COMPONENT}",
                ),
            )
        )
    ev.extend(extra_evidence)
    return InfrastructureRecord(
        project_id=project_id,
        network_operator=operator,
        owner="DSO",
        region_id=region_id,
        region_grain=DSO_SUBSTATION,
        infrastructure_type="SUBSTATION_REINFORCEMENT",
        status_taxonomy=ANNOUNCED_UNFUNDED,
        status_effective_date="2026-09-02",
        source_refs=tuple(item.source_id for item in ev),
        evidence=tuple(ev),
        evidence_status="DER",
        without_program_required=False,
        with_program_required=True,
        program_causality_status=program_causality_status,
        incremental_cost_huf=incremental_cost_huf,
        cost_component_id=cost_component_id,
        incremental_scope_proven=incremental_scope_proven,
        incremental_capacity_proven=incremental_capacity_proven,
        acceleration_proven=acceleration_proven,
        upsizing_proven=upsizing_proven,
    )


def screening(status=EXCEEDS_PUBLISHED_HEADROOM_SCREENING, *, horizon=CURRENT):
    overload = 2.0 if status == EXCEEDS_PUBLISHED_HEADROOM_SCREENING else 0.0
    return HeadroomScreeningContext(
        network_operator=OPERATOR,
        region_id=REGION_ID,
        region_grain=DSO_SUBSTATION,
        horizon=horizon,
        screening_status=status,
        evidence_status="SCN",
        source_refs=("SRC-HEADROOM", "SRC-DEMAND"),
        incremental_demand_mw=12.0,
        published_headroom_mw=10.0 if overload else 12.0,
        remaining_headroom_mw=0.0,
        overload_mw=overload,
    )


class B10P5IncrementalReinforcementTests(unittest.TestCase):
    def test_exact_grain_headroom_assessment_becomes_screening_only(self):
        row = DsoHeadroomRecord(
            station_name="Example",
            station_code="ABCD",
            voltage_kv=132,
            horizon=CURRENT,
            n_minus_1_capacity_mw=None,
            winter_evening_peak_load_mw=None,
            theoretical_free_capacity_mw=None,
            evidence_status="Q",
            source_refs=("SRC-HEADROOM",),
        )
        assessment = HeadroomAssessment(
            region_id=row.region_id,
            region_scheme=DSO_SUBSTATION,
            horizon=CURRENT,
            incremental_demand_mw=12,
            published_headroom_mw=10,
            remaining_headroom_mw=0,
            overload_mw=2,
            evidence_status="SCN",
            source_refs=("SRC-HEADROOM", "SRC-DEMAND"),
        )
        context = screening_context_from_headroom_assessment(row, assessment, programme_horizon=CURRENT)
        self.assertEqual(EXCEEDS_PUBLISHED_HEADROOM_SCREENING, context.screening_status)
        self.assertNotEqual("OBS", context.evidence_status)

    def test_q_screening_remains_q_and_missing_is_not_zero(self):
        row = DsoHeadroomRecord(
            station_name="Example",
            station_code="ABCD",
            voltage_kv=132,
            horizon=CURRENT,
            n_minus_1_capacity_mw=None,
            winter_evening_peak_load_mw=None,
            theoretical_free_capacity_mw=None,
            evidence_status="Q",
            source_refs=("SRC-HEADROOM",),
        )
        assessment = HeadroomAssessment(
            region_id=row.region_id,
            region_scheme=DSO_SUBSTATION,
            horizon=CURRENT,
            incremental_demand_mw=12,
            published_headroom_mw=None,
            remaining_headroom_mw=None,
            overload_mw=None,
            evidence_status="Q",
            source_refs=("SRC-HEADROOM", "SRC-DEMAND"),
        )
        context = screening_context_from_headroom_assessment(row, assessment, programme_horizon=CURRENT)
        self.assertEqual(SCREENING_Q, context.screening_status)
        self.assertIsNone(context.published_headroom_mw)
        self.assertIsNone(context.overload_mw)

    def test_current_five_year_mismatch_fails_closed(self):
        row = DsoHeadroomRecord(
            station_name="Example",
            station_code="ABCD",
            voltage_kv=132,
            horizon=CURRENT,
            n_minus_1_capacity_mw=None,
            winter_evening_peak_load_mw=None,
            theoretical_free_capacity_mw=None,
            evidence_status="Q",
            source_refs=("SRC",),
        )
        assessment = HeadroomAssessment(
            row.region_id,
            DSO_SUBSTATION,
            CURRENT,
            1,
            None,
            None,
            None,
            "Q",
            ("SRC",),
        )
        with self.assertRaisesRegex(B10IncrementalReinforcementContractError, "CURRENT and FIVE_YEAR"):
            screening_context_from_headroom_assessment(row, assessment, programme_horizon=FIVE_YEAR)

    def test_headroom_exceedance_alone_cannot_prove_reinforcement_or_incremental_scope(self):
        no_claim = incremental_record(reinforcement_claims=())
        with self.assertRaisesRegex(B10IncrementalReinforcementContractError, "REINFORCEMENT_REQUIRED"):
            evaluate_programme_incremental_reinforcement(
                no_claim, reinforcement_horizon=CURRENT, screening=screening()
            )

    def test_within_headroom_is_not_no_reinforcement_authority(self):
        result = evaluate_programme_incremental_reinforcement(
            incremental_record(),
            reinforcement_horizon=CURRENT,
            screening=screening(WITHIN_PUBLISHED_HEADROOM_SCREENING),
        )
        self.assertTrue(result.reinforcement_required_proven)
        self.assertEqual(WITHIN_PUBLISHED_HEADROOM_SCREENING, result.screening_status)

    def test_wrong_operator_region_and_service_area_fail_closed(self):
        rec = incremental_record()
        for bad in (
            replace(screening(), network_operator="OTHER"),
            replace(screening(), region_id="MVM_DEMASZ:WXYZ:132KV"),
        ):
            with self.assertRaisesRegex(B10IncrementalReinforcementContractError, "exact operator"):
                evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT, screening=bad)
        with self.assertRaisesRegex(B10IncrementalReinforcementContractError, "DSO_SUBSTATION"):
            replace(rec, region_grain="DSO_SERVICE_AREA") and evaluate_programme_incremental_reinforcement(
                replace(rec, region_grain="DSO_SERVICE_AREA"), reinforcement_horizon=CURRENT
            )

    def test_p4_service_area_baseline_cannot_become_p5_node_record(self):
        with self.assertRaisesRegex(B10IncrementalReinforcementContractError, "DSO_SUBSTATION"):
            evaluate_programme_incremental_reinforcement(
                RRF_BASELINE_RECORDS[0], reinforcement_horizon=CURRENT
            )

    def test_unquantified_incremental_difference_survives_with_blank_capex(self):
        result = evaluate_programme_incremental_reinforcement(
            incremental_record(), reinforcement_horizon=CURRENT, screening=screening()
        )
        self.assertEqual(PROGRAM_INCREMENTAL, result.attribution.attribution_status)
        self.assertIsNone(result.program_incremental_capex_huf)

    def test_numeric_incremental_cost_requires_component_specific_claim(self):
        rec = incremental_record(
            cost_claims=(PROGRAM_INCREMENTAL_COST,),
            incremental_cost_huf=10,
            cost_component_id=COMPONENT,
        )
        result = evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT)
        self.assertEqual(10, result.program_incremental_capex_huf)
        self.assertEqual(PROGRAM_INCREMENTAL, result.attribution.attribution_status)

    def test_generic_cost_customer_charge_or_total_cost_cannot_mint_incremental_capex(self):
        for claims in ((), (CUSTOMER_CONNECTION_CHARGE,), (TOTAL_REINFORCEMENT_PROJECT_COST,)):
            rec = incremental_record(
                cost_claims=claims or ("GENERIC_ONLY",),
                incremental_cost_huf=10,
                cost_component_id=COMPONENT,
            )
            with self.assertRaisesRegex(B10IncrementalReinforcementContractError, "cannot mint"):
                evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT)

    def test_smaller_arbitrary_number_without_incremental_cost_authority_fails(self):
        rec = incremental_record(
            cost_claims=(TOTAL_REINFORCEMENT_PROJECT_COST,),
            incremental_cost_huf=1,
            cost_component_id=COMPONENT,
        )
        with self.assertRaises(B10IncrementalReinforcementContractError):
            evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT)

    def test_unreferenced_incremental_cost_evidence_fails(self):
        bind = bindings()
        cost = evidence(
            "SRC-UNREFERENCED-COST",
            level=3,
            supports=(
                "COST",
                PROGRAM_INCREMENTAL_COST,
                *bind,
                f"{COST_COMPONENT_BINDING_PREFIX}{COMPONENT}",
            ),
        )
        rec = incremental_record(
            incremental_cost_huf=10,
            cost_component_id=COMPONENT,
            extra_evidence=(cost,),
        )
        rec = replace(rec, source_refs=tuple(ref for ref in rec.source_refs if ref != cost.source_id))
        with self.assertRaises(B10IncrementalReinforcementContractError):
            evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT)

    def test_wrong_project_or_component_cost_evidence_fails(self):
        wrong_project = evidence(
            COST_SOURCE,
            level=3,
            supports=(
                "COST",
                PROGRAM_INCREMENTAL_COST,
                *bindings(project_id="OTHER"),
                f"{COST_COMPONENT_BINDING_PREFIX}{COMPONENT}",
            ),
        )
        rec = incremental_record(
            incremental_cost_huf=10,
            cost_component_id=COMPONENT,
            extra_evidence=(wrong_project,),
        )
        rec = replace(rec, source_refs=(STATUS_SOURCE, REINFORCEMENT_SOURCE, COST_SOURCE))
        with self.assertRaises(B10IncrementalReinforcementContractError):
            evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT)

        rec = incremental_record(
            cost_claims=(PROGRAM_INCREMENTAL_COST,),
            incremental_cost_huf=10,
            cost_component_id="OTHER-COMPONENT",
        )
        # helper binds the same chosen component, therefore create a mismatched record afterwards
        rec = replace(rec, cost_component_id=COMPONENT)
        with self.assertRaises(B10IncrementalReinforcementContractError):
            evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT)

    def test_acceleration_and_upsize_require_their_own_claims(self):
        for flag, claim, cost_claim in (
            ("acceleration", ACCELERATION, ACCELERATION_COST),
            ("upsize", UPSIZE, UPSIZE_COST),
        ):
            kwargs = {
                "reinforcement_claims": (claim,),
                "incremental_scope_proven": False,
                "acceleration_proven": flag == "acceleration",
                "upsizing_proven": flag == "upsize",
                "cost_claims": (cost_claim,),
                "incremental_cost_huf": 5,
                "cost_component_id": COMPONENT,
            }
            rec = incremental_record(**kwargs)
            # ANNOUNCED_UNFUNDED uses pure PROGRAM_INCREMENTAL in P3; the point
            # of this test is claim-specific P5 cost authority, not status taxonomy.
            result = evaluate_programme_incremental_reinforcement(rec, reinforcement_horizon=CURRENT)
            self.assertEqual(5, result.program_incremental_capex_huf)

    def test_programme_causality_obs_is_still_rejected_by_p3(self):
        with self.assertRaisesRegex(B10BaselineInfrastructureContractError, "cannot be OBS"):
            incremental_record(program_causality_status="OBS")

    def test_negative_or_nonfinite_screening_values_fail_closed(self):
        with self.assertRaises(B10IncrementalReinforcementContractError):
            replace(screening(), incremental_demand_mw=-1)
        with self.assertRaises(B10IncrementalReinforcementContractError):
            replace(screening(), published_headroom_mw=float("inf"))

    def test_screening_status_does_not_create_scope_or_timing_fields(self):
        context = screening()
        self.assertFalse(hasattr(context, "reinforcement_scope"))
        self.assertFalse(hasattr(context, "reinforcement_timing"))
        self.assertFalse(hasattr(context, "reinforcement_cost_huf"))


if __name__ == "__main__":
    unittest.main()
