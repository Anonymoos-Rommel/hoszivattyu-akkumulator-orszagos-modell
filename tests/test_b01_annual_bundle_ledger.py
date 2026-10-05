from __future__ import annotations

import unittest
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction

from modules.B01.engine import create_annual_plan
from modules.B01.capability_contract import CapabilitySnapshot, DatedAssertion, EvidenceIdentity, load_contract
from modules.B01.annual_bundle_ledger import (
    AnnualLedgerError, AnnualPlanSession, CashPoolQualification, CashRelease, CashViewRestriction, HouseholdBundle, JointNetworkAssessment,
    PlannedAction, QualifiedBundle, Quantity, ResourceConstraint, ResourceUse, bundle_scope_digest,
    RequirementCatalogue, RequirementCoverage, requirement_catalogue_digest,
)


NATIONAL = ("COUNTRY", "HU")
REGION = ("REGION", "R1")
RULES = load_contract()


def q(value, unit="unit", status=None, basis="SCN-2028"):
    return Quantity(None if value is None else Decimal(value), unit, basis, status or ("Q" if value is None else "SCN"), ("SCN-RESOURCE-WITNESS",))


def limit(kind="ANNUAL_FLOW", value="10", *, scope=NATIONAL, name="LIMIT", dimension="RESOURCE", unit="unit", opening=None, releases=(), pool_total=True):
    return ResourceConstraint(name, dimension, kind, scope, q(value, unit), "SCN-RESOURCE-HOLDER", pool_total,
                              "2028-01-01" if kind == "PUBLIC_CASH" else None,
                              q(opening, unit) if kind == "PUBLIC_CASH" else None,
                              releases, "BEFORE_ALL_DECLARED_IN_YEAR_DEBITS" if kind == "PUBLIC_CASH" else None,
                              CashPoolQualification("FUNGIBLE_POOL_NONADDITIVE_ACCESS_CEILINGS", "SCN", ("SCN-POOL-ACCESS-BASIS",),
                                                    "Synthetic fungible pool; views are non-additive access ceilings, not exclusive source allocations.")
                              if kind == "PUBLIC_CASH" and pool_total else None)


def use(key, value="1", *, start="2028-02-01", stop="2028-02-02", dimension="RESOURCE", unit="unit", tags=(NATIONAL, REGION), source=None):
    return ResourceUse(key, source or "SOURCE-" + key, dimension, q(value, unit), tags, start, stop, "SCN-RESOURCE-HOLDER")


def ready(hh, site, basis, when, subject):
    identity = EvidenceIdentity(hh, site, basis, "SCN", "INDIVIDUAL_RECORD")
    assertions = []
    for claim in RULES["actions"][subject]["technical_prerequisites"] + RULES["programme_action_claims"]:
        assertions.append(DatedAssertion("ASSERT-" + subject + claim, identity, claim, "PASS", "SCN", ("SCN-QUALIFIED-INPUT",),
                                         when, "2029-01-01", "Synthetic record and exact action qualification.",
                                         (subject,) if claim in RULES["subject_scoped_claims"] else ()))
    return CapabilitySnapshot(identity, when, (), tuple(assertions))


def action(key, subject="COMMISSION_BATTERY", *, hh="H1", site="S1", basis="B1", start="2028-02-01", stop="2028-02-02", uses=None, predecessors=(), generation=None):
    return PlannedAction(key, subject, "WORK-" + key, generation or "GEN-" + key, start, stop, predecessors,
                         ready(hh, site, basis, start, subject), (use("USE-" + key, start=start, stop=stop),) if uses is None else uses)


def qualified(bundle, *, floor="PASS", eligibility="PASS"):
    return replace(bundle, qualification=QualifiedBundle(bundle_scope_digest(bundle), eligibility, floor, "SCN",
                                                        ("SCN-JOINT-BUNDLE-QUALIFICATION",), "Combined package and first-day/interim cashflow, dates and costs qualified together."))


def catalogue(pools=("RESOURCE",), *, completeness="COMPLETE", version="v1"):
    return RequirementCatalogue("SCN-REQUIREMENT-INVENTORY", version, tuple(sorted(pools)), completeness,
                                "Q" if completeness == "Q" else "SCN", ("SCN-QUALIFIED-INVENTORY",),
                                "Synthetic bounded case inventory; this is not a discovered complete physical programme resource list.")


def coverage(action_id, pool="RESOURCE", applicability="REQUIRED"):
    return RequirementCoverage(action_id, pool, applicability, "Q" if applicability == "Q" else "SCN",
                               ("SCN-REQUIREMENT-SCOPE",), "Explicit synthetic applicability; absence never means zero.")


def bundle(key="BUNDLE-1", *, hh="H1", site="S1", basis="B1", actions=None, floor="PASS", domains=None, covered=None):
    actions = (action("ACTION-" + key, hh=hh, site=site, basis=basis),) if actions is None else actions
    domains = domains or catalogue()
    covered = tuple(coverage(a.proposal_id, pool, "REQUIRED" if any(use.pool_id == pool for use in a.resource_uses) else "NOT_REQUIRED") for a in actions for pool in domains.pool_ids) if covered is None else covered
    return qualified(HouseholdBundle(key, "v1", hh, site, basis, "SCN-WITHOUT-PROGRAMME-BASELINE", actions,
                                    requirement_catalogue_digest(domains), covered), floor=floor)


def session(constraints=None, *, opening=(), opening_state=None, domains=None):
    constraints = (limit(),) if constraints is None else constraints
    domains = domains or catalogue(tuple({item.pool_id for item in constraints}))
    return create_annual_plan(ledger_id="SCN-LEDGER", plan_year=2028, plan_basis_id="SCN-ANNUAL-PLAN", calendar_timezone="Europe/Budapest",
                             constraints=constraints, requirement_catalogue=domains,
                             opening_uses_state=opening_state or ("USES" if opening else "NONE"), opening_uses_refs=("SCN-OPENING-DECLARATION",), opening_uses=opening)


def reserve(s, *bundles):
    return s.reserve(tuple(bundles), expected_revision=s.state.digest, order_ref="SCN-EXPLICIT-ORDER-NOT-OPTIMUM")


class AnnualBundleLedgerTests(unittest.TestCase):
    def test_two_independent_actions_one_household(self):
        s = session()
        b = bundle(actions=(action("BAT"), action("ENV", "ACCEPT_ENVELOPE_SCOPE")))
        r = reserve(s, b)
        self.assertEqual("RESERVED_PLANNED", r.decisions[0].status)
        self.assertEqual(1, r.distinct_planned_households)
        self.assertEqual(2, r.planned_actions)
        self.assertEqual(Fraction(2), r.resource_checks[0].used_or_peak)
        self.assertEqual("UNKNOWN", r.joint_network_status)
        self.assertFalse(r.actual_funding_or_completion)
        self.assertTrue(all(not a.snapshot.completion_events for a in s.state.bundles[0].actions))

    def test_declared_predecessor_within_same_year(self):
        b = bundle(actions=(action("ENV", "ACCEPT_ENVELOPE_SCOPE"), action("HP", "COMMISSION_HEAT_PUMP", start="2028-02-02", stop="2028-02-03", predecessors=("ENV",))))
        self.assertEqual("RESERVED_PLANNED", reserve(session(), b).decisions[0].status)

    def test_missing_later_self_and_cyclic_predecessors_fail(self):
        for predecessors in (("MISSING",), ("HP",), ("LATER",)):
            b = bundle(actions=(action("HP", "COMMISSION_HEAT_PUMP", predecessors=predecessors), action("LATER", start="2028-02-03", stop="2028-02-04", predecessors=("HP",))))
            with self.subTest(predecessors=predecessors), self.assertRaises(AnnualLedgerError):
                reserve(session(), b)

    def test_bundle_is_atomic_when_phases_separately_fit_but_total_does_not(self):
        s = session((limit(value="1"),))
        before = s.state
        r = reserve(s, bundle(actions=(action("BAT"), action("ENV", "ACCEPT_ENVELOPE_SCOPE"))))
        self.assertEqual("WAIT_RESOURCE", r.decisions[0].status)
        self.assertEqual(Fraction(-1), r.decisions[0].resource_checks[0].remaining)
        self.assertEqual("unit", r.decisions[0].resource_checks[0].unit)
        self.assertEqual(before, s.state)
        self.assertEqual(0, r.planned_actions)

    def test_dropping_phase_cannot_reuse_full_bundle_qualification(self):
        b = bundle(actions=(action("BAT"), action("ENV", "ACCEPT_ENVELOPE_SCOPE")))
        with self.assertRaises(AnnualLedgerError):
            reserve(session(), replace(b, actions=b.actions[:1]))

    def test_changed_dates_costs_or_counterfactual_require_matching_joint_proof(self):
        b = bundle()
        variants = [replace(b, counterfactual_ref="OTHER"), replace(b, actions=(replace(b.actions[0], ends_before="2028-02-03"),)),
                    replace(b, actions=(replace(b.actions[0], resource_uses=(replace(b.actions[0].resource_uses[0], quantity=q("2")),)),))]
        for changed in variants:
            with self.assertRaises(AnnualLedgerError):
                reserve(session(), changed)

    def test_individual_floor_cannot_be_offset_by_other_household(self):
        for floor in ("FAIL", "UNKNOWN"):
            s = session()
            r = reserve(s, bundle(), bundle("B2", hh="H2", site="S2", basis="B2", floor=floor))
            self.assertEqual(["RESERVED_PLANNED", "BLOCKED_PREREQUISITE"], [item.status for item in r.decisions])
            self.assertEqual(1, r.distinct_planned_households)

    def test_action_specific_unknown_floor_blocks_even_if_joint_claim_passes(self):
        a = action("BAT")
        snap = replace(a.snapshot, assertions=tuple(item for item in a.snapshot.assertions if item.claim_id != "HOUSEHOLD_CASHFLOW_PROTECTED"))
        b = bundle(actions=(replace(a, snapshot=snap),))
        self.assertEqual("BLOCKED_PREREQUISITE", reserve(session(), b).decisions[0].status)

    def test_second_call_cannot_reset_annual_usage(self):
        s = session((limit(value="1"),))
        reserve(s, bundle())
        r = reserve(s, bundle("B2", hh="H2", site="S2", basis="B2"))
        self.assertEqual("WAIT_RESOURCE", r.decisions[0].status)
        self.assertEqual(Fraction(1), r.resource_checks[0].used_or_peak)
        self.assertEqual(1, s.state.revision)

    def test_stale_revision_checked_against_session_current_state(self):
        s = session()
        old = s.state
        reserve(s, bundle())
        with self.assertRaises(AnnualLedgerError):
            s.reserve((bundle("B2", hh="H2", site="S2", basis="B2"),), expected_revision=old.digest, order_ref="SCN")
        self.assertEqual(1, len(s.state.bundles))

    def test_same_version_retry_is_idempotent(self):
        s = session()
        b = bundle()
        reserve(s, b)
        before = s.state
        r = reserve(s, b)
        self.assertEqual("ALREADY_RESERVED", r.decisions[0].status)
        self.assertEqual(before, s.state)
        self.assertEqual(2, len(s.history))

    def test_changed_reserved_bundle_and_household_alternative_requalify_without_refund(self):
        s = session()
        b = bundle()
        reserve(s, b)
        changed = qualified(replace(b, version="v2"))
        before = s.state
        r = reserve(s, changed, bundle("ALTERNATIVE"))
        self.assertTrue(all(item.status == "REQUALIFICATION_REQUIRED" for item in r.decisions))
        self.assertEqual(before, s.state)
        self.assertEqual("REQUALIFICATION_REQUIRED", s.request_amendment(b.bundle_id, expected_revision=s.state.digest).status)

    def test_duplicate_work_alias_does_not_create_another_installation(self):
        a = action("A")
        duplicate = replace(action("B"), asset_generation_id=a.asset_generation_id)
        with self.assertRaises(AnnualLedgerError):
            reserve(session(), bundle(actions=(a, duplicate)))

    def test_shared_site_work_cannot_be_counted_again_under_another_household(self):
        s = session()
        reserve(s, bundle(actions=(action("A", generation="SAME-GEN"),)))
        b = bundle("B2", hh="H2", site="S1", basis="B2", actions=(action("B", hh="H2", site="S1", basis="B2", generation="SAME-GEN"),))
        with self.assertRaises(AnnualLedgerError):
            reserve(s, b)

    def test_different_use_alias_cannot_duplicate_source_cost_event(self):
        s = session()
        reserve(s, bundle(actions=(action("A", uses=(use("A", source="SAME-COST"),)),)))
        b = bundle("B2", hh="H2", site="S2", basis="B2", actions=(action("B", hh="H2", site="S2", basis="B2", uses=(use("B", source="SAME-COST"),)),))
        with self.assertRaises(AnnualLedgerError):
            reserve(s, b)

    def test_failure_after_tentative_first_bundle_leaves_entire_session_unchanged(self):
        s = session()
        a = bundle(actions=(action("A", uses=(use("A", source="DUPLICATE"),)),))
        b = bundle("B2", hh="H2", site="S2", basis="B2", actions=(action("B", hh="H2", site="S2", basis="B2", uses=(use("B", source="DUPLICATE"),)),))
        before = s.state
        with self.assertRaises(AnnualLedgerError):
            reserve(s, a, b)
        self.assertEqual(before, s.state)

    def test_disjoint_work_reuses_concurrent_capacity_but_not_flow_quota(self):
        actions = (action("BAT"), action("ENV", "ACCEPT_ENVELOPE_SCOPE", start="2028-02-02", stop="2028-02-03"))
        b = bundle(actions=actions)
        self.assertEqual("RESERVED_PLANNED", reserve(session((limit("CONCURRENT", "1"),)), b).decisions[0].status)
        self.assertEqual("WAIT_RESOURCE", reserve(session((limit("ANNUAL_FLOW", "1"),)), b).decisions[0].status)

    def test_overlapping_concurrent_work_exceeds_shared_capacity(self):
        b = bundle(actions=(action("BAT"), action("ENV", "ACCEPT_ENVELOPE_SCOPE")))
        self.assertEqual("WAIT_RESOURCE", reserve(session((limit("CONCURRENT", "1"),)), b).decisions[0].status)

    def test_installed_occupancy_can_persist_after_installation_labour_ends(self):
        s = session((limit("CONCURRENT", "1"),))
        reserve(s, bundle(actions=(action("BAT", uses=(use("PERSISTENT", stop="2029-01-01"),)),)))
        b = bundle("B2", hh="H2", site="S2", basis="B2", actions=(action("B", hh="H2", site="S2", basis="B2", start="2028-03-01", stop="2028-03-02"),))
        self.assertEqual("WAIT_RESOURCE", reserve(s, b).decisions[0].status)

    def test_national_and_regional_views_share_one_unique_use(self):
        s = session((limit(value="10", name="NATIONAL"), limit(value="1", scope=REGION, name="REGIONAL", pool_total=False)))
        r = reserve(s, bundle())
        self.assertEqual([Fraction(1), Fraction(1)], [check.used_or_peak for check in r.resource_checks])
        self.assertEqual(1, len(s.state.bundles[0].actions[0].resource_uses))
        b = bundle("B2", hh="H2", site="S2", basis="B2")
        self.assertEqual("WAIT_RESOURCE", reserve(s, b).decisions[0].status)

    def test_unrelated_regional_capacity_cannot_cover_missing_scope(self):
        s = session((limit(scope=("REGION", "OTHER")),))
        self.assertEqual("WAIT_RESOURCE", reserve(s, bundle()).decisions[0].status)

    def test_missing_resource_requirement_or_quantity_is_not_zero(self):
        for uses in ((), (use("Q", None),)):
            s = session()
            r = reserve(s, bundle(actions=(action("BAT", uses=uses),), covered=(coverage("BAT"),)))
            self.assertNotEqual("RESERVED_PLANNED", r.decisions[0].status)
            self.assertEqual(0, len(s.state.bundles))

    def test_missing_capacity_and_opening_commitments_are_not_infinite_or_zero(self):
        self.assertEqual("WAIT_RESOURCE", reserve(session((limit(value=None),)), bundle()).decisions[0].status)
        self.assertEqual("WAIT_RESOURCE", reserve(session(opening_state="Q"), bundle()).decisions[0].status)

    def test_explicit_qualified_zero_is_distinct_from_missing(self):
        b = bundle(actions=(action("BAT", uses=(use("ZERO", "0"),)),))
        self.assertEqual("RESERVED_PLANNED", reserve(session((limit(value="0"),)), b).decisions[0].status)

    def test_units_basis_and_cross_year_intervals_fail(self):
        for changed in (replace(use("BAD"), quantity=q("1", "kg")), replace(use("BAD"), quantity=q("1", basis="OTHER")), replace(use("BAD"), starts_on="2027-12-31"), replace(use("BAD"), ends_before="2029-01-02")):
            with self.assertRaises(AnnualLedgerError):
                reserve(session(), bundle(actions=(action("BAT", uses=(changed,)),)))

    def test_bool_float_nan_and_infinite_quantities_reject(self):
        for value in (True, 1.0, Decimal("NaN"), Decimal("Infinity"), Decimal("-1")):
            bad = replace(q("1"), value=value)
            with self.subTest(value=value), self.assertRaises(AnnualLedgerError):
                reserve(session(), bundle(actions=(action("BAT", uses=(replace(use("BAD"), quantity=bad),)),)))

    def test_exact_addition_does_not_depend_on_decimal_context(self):
        cap = "1000000000000000000000000000000"
        b = bundle(actions=(action("BAT", uses=(use("BIG", cap),)), action("ENV", "ACCEPT_ENVELOPE_SCOPE", uses=(use("SMALL", "1"),))))
        with localcontext() as context:
            context.prec = 2
            self.assertEqual("WAIT_RESOURCE", reserve(session((limit(value=cap),)), b).decisions[0].status)

    def test_later_cash_cannot_cover_earlier_payment_even_below_annual_cap(self):
        release = CashRelease("SCN-JULY-RECEIPT", "2028-07-01", q("100", "HUF"))
        s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(release,)),))
        b = bundle(actions=(action("BAT", uses=(use("JAN-PAYMENT", "50", start="2028-01-15", stop="2028-01-16", unit="HUF"),)),))
        self.assertEqual("WAIT_RESOURCE", reserve(s, b).decisions[0].status)
        self.assertEqual(0, len(s.state.bundles))

    def test_future_payment_can_use_earlier_release_regardless_of_reservation_time(self):
        release = CashRelease("SCN-JUNE-RECEIPT", "2028-06-01", q("100", "HUF"))
        s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(release,)),))
        b = bundle(actions=(action("BAT", uses=(use("JULY-PAYMENT", "50", start="2028-07-01", stop="2028-07-02", unit="HUF"),)),))
        self.assertEqual("RESERVED_PLANNED", reserve(s, b).decisions[0].status)

    def test_cash_and_annual_ceiling_both_apply(self):
        s = session((limit("PUBLIC_CASH", "40", unit="HUF", opening="100"),))
        b = bundle(actions=(action("BAT", uses=(use("PAYMENT", "50", unit="HUF"),)),))
        self.assertEqual("WAIT_RESOURCE", reserve(s, b).decisions[0].status)

    def test_prior_in_year_commitment_is_deducted_once(self):
        old = use("PRIOR-COMMITMENT", "30", start="2028-01-10", stop="2028-01-11", unit="HUF")
        s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening="100"),), opening=(old,))
        b = bundle(actions=(action("BAT", uses=(use("NEW", "70", unit="HUF"),)),))
        r = reserve(s, b)
        self.assertEqual("RESERVED_PLANNED", r.decisions[0].status)
        self.assertEqual(Fraction(100), r.resource_checks[0].used_or_peak)
        self.assertEqual("ALREADY_RESERVED", reserve(s, b).decisions[0].status)

    def test_opening_balance_cannot_be_already_netted_or_at_another_date(self):
        base = limit("PUBLIC_CASH", "100", unit="HUF", opening="100")
        for changed in (replace(base, opening_basis="NET_AFTER_COMMITMENTS"), replace(base, opening_on="2028-02-01")):
            with self.assertRaises(AnnualLedgerError):
                session((changed,))

    def test_unknown_cash_and_negative_opening_gap_are_explicit(self):
        for opening in (None, "-1"):
            s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening=opening),))
            b = bundle(actions=(action("BAT", uses=(use("PAYMENT", "1", unit="HUF"),)),))
            self.assertEqual("WAIT_RESOURCE", reserve(s, b).decisions[0].status)

    def test_duplicate_cash_receipt_is_rejected(self):
        release = CashRelease("DUPLICATE", "2028-01-10", q("1", "HUF"))
        with self.assertRaises(AnnualLedgerError):
            session((limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(release, release)),))

    def test_network_result_binds_the_whole_current_set_and_never_becomes_permission(self):
        s = session()
        reserve(s, bundle())
        witness = JointNetworkAssessment(s.active_set_digest, 2028, "PASS", "SCN", ("SCN-JOINT-STUDY",), "Synthetic joint set with compatible baseline and demand window; no MGT claim.")
        self.assertEqual("PASS", s.assess_joint_network(witness))
        reserve(s, bundle("B2", hh="H2", site="S2", basis="B2"))
        self.assertEqual("UNKNOWN", s.assess_joint_network(witness))
        self.assertEqual("UNKNOWN", s.assess_joint_network(None))
        with self.assertRaises(AnnualLedgerError):
            s.assess_joint_network(replace(witness, evidence_status="OBS"))

    def test_population_grain_and_wrong_household_do_not_pass_action_gate(self):
        a = action("BAT")
        for identity in (replace(a.snapshot.identity, evidence_scope="POPULATION_ESTIMATE"), replace(a.snapshot.identity, household_id="OTHER")):
            changed = replace(a, snapshot=replace(a.snapshot, identity=identity))
            with self.assertRaises(ValueError):
                reserve(session(), bundle(actions=(changed,)))

    def test_actor_mismatch_cannot_turn_household_money_into_public_funds(self):
        changed = replace(use("MONEY", "1", unit="HUF"), payer_or_resource_holder="HOUSEHOLD")
        with self.assertRaises(AnnualLedgerError):
            reserve(session((limit("PUBLIC_CASH", "100", unit="HUF", opening="100"),)), bundle(actions=(action("BAT", uses=(changed,)),)))

    def test_cost_identity_cannot_be_relabelled_to_another_resource_pool(self):
        a = action("BAT", uses=(use("ONE", source="SAME-PAYMENT"), use("TWO", dimension="OTHER", source="SAME-PAYMENT")))
        with self.assertRaises(AnnualLedgerError):
            reserve(session((limit(), limit(dimension="OTHER", name="OTHER"))), bundle(actions=(a,), domains=catalogue(("RESOURCE", "OTHER"))))

    def test_known_annual_excess_remains_failure_when_cash_is_unknown(self):
        from modules.B01.annual_bundle_ledger import _resource_checks
        s = session((limit("PUBLIC_CASH", "1", unit="HUF", opening=None),), opening=(use("PRIOR", "2", unit="HUF"),))
        self.assertEqual("FAIL", _resource_checks(s.state)[0].status)

    def test_one_cash_movement_cannot_finance_itself(self):
        receipt = CashRelease("SAME-MOVEMENT", "2028-02-01", q("1", "HUF"))
        s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(receipt,)),))
        b = bundle(actions=(action("BAT", uses=(use("PAYMENT", "1", unit="HUF", source="SAME-MOVEMENT"),)),))
        with self.assertRaises(AnnualLedgerError):
            reserve(s, b)

    def test_explicit_order_and_input_digest_are_retained_in_revision_history(self):
        s = session()
        first = reserve(s, bundle())
        second = reserve(s, bundle("B2", hh="H2", site="S2", basis="B2"))
        self.assertEqual(first.order_ref, s.state.selection_history[0].order_ref)
        self.assertEqual(first.ordered_input_digest, s.state.selection_history[0].ordered_input_digest)
        self.assertEqual(second.before_digest, s.state.selection_history[1].prior_digest)
        self.assertEqual(2, len(s.state.selection_history))

    def test_omitting_total_or_regional_scope_cannot_bypass_a_ceiling(self):
        limits = (limit(value="1", name="TOTAL"), limit(value="1", scope=REGION, name="REGION", pool_total=False))
        for tags in ((REGION,), (NATIONAL,), (NATIONAL, ("REGION", "UNCOVERED"))):
            b = bundle(actions=(action("BAT", uses=(use("SCOPED", "2", tags=tags),)),))
            with self.subTest(tags=tags):
                r = reserve(session(limits), b)
                self.assertEqual("WAIT_RESOURCE", r.decisions[0].status)
                self.assertTrue(any(item.status == "UNKNOWN" and item.constraint_id.startswith("UNCOVERED:") for item in r.decisions[0].resource_checks))
                self.assertTrue(any(item.status == "FAIL" and item.constraint_id == "TOTAL" for item in r.decisions[0].resource_checks))

    def test_regional_independent_pool_needs_no_invented_national_capacity(self):
        s = session((limit(scope=REGION),))
        b = bundle(actions=(action("BAT", uses=(use("LOCAL", tags=(REGION,)),)),))
        self.assertEqual("RESERVED_PLANNED", reserve(s, b).decisions[0].status)

    def test_missing_or_multiple_pool_total_roles_are_rejected(self):
        for limits in ((limit(pool_total=False),), (limit(), limit(name="SECOND", scope=REGION))):
            with self.assertRaises(AnnualLedgerError):
                session(limits)

    def test_one_funding_event_cannot_supply_two_distinct_pools(self):
        receipt = CashRelease("ONE-TEN-HUF-RECEIPT", "2028-01-01", q("10", "HUF"))
        limits = (limit("PUBLIC_CASH", "10", dimension="POOL-A", unit="HUF", opening="0", releases=(receipt,), name="A"),
                  limit("PUBLIC_CASH", "10", dimension="POOL-B", unit="HUF", opening="0", releases=(receipt,), name="B"))
        with self.assertRaises(AnnualLedgerError):
            session(limits)

    def test_nested_receipt_views_share_the_same_pool_total(self):
        receipt = CashRelease("ONE-TEN-HUF-RECEIPT", "2028-01-01", q("10", "HUF"))
        limits = (limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(receipt,), name="TOTAL"),
                  limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(receipt,), scope=REGION, name="R1", pool_total=False),
                  limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(receipt,), scope=("REGION", "R2"), name="R2", pool_total=False))
        s = session(limits)
        first = bundle(actions=(action("A", uses=(use("PAY-A", "10", unit="HUF"),)),))
        second = bundle("B2", hh="H2", site="S2", basis="B2", actions=(action("B", hh="H2", site="S2", basis="B2", uses=(use("PAY-B", "10", unit="HUF", tags=(NATIONAL, ("REGION", "R2"))),)),))
        r = reserve(s, first, second)
        self.assertEqual(["RESERVED_PLANNED", "WAIT_RESOURCE"], [item.status for item in r.decisions])
        self.assertEqual(Fraction(10), next(item.used_or_peak for item in r.resource_checks if item.constraint_id == "TOTAL"))

    def test_nonempty_labour_list_cannot_omit_cash_or_equipment_domains(self):
        domains = catalogue(("LABOUR", "CASH", "EQUIPMENT"))
        limits = (limit(dimension="LABOUR", name="LABOUR"), limit(dimension="CASH", name="CASH", value="0"), limit(dimension="EQUIPMENT", name="EQUIPMENT", value="0"))
        a = action("BAT", uses=(use("HOURS", dimension="LABOUR"),))
        b = bundle(actions=(a,), domains=domains, covered=(coverage("BAT", "LABOUR"),))
        r = reserve(session(limits, domains=domains), b)
        self.assertEqual("BLOCKED_PREREQUISITE", r.decisions[0].status)
        self.assertTrue(any("CASH" in reason for reason in r.decisions[0].reasons))
        self.assertTrue(any("EQUIPMENT" in reason for reason in r.decisions[0].reasons))

    def test_qualified_not_required_domains_need_no_invented_positive_use(self):
        domains = catalogue(("LABOUR", "CASH", "EQUIPMENT"))
        limits = (limit(dimension="LABOUR", name="LABOUR"), limit(dimension="CASH", name="CASH", value="0"), limit(dimension="EQUIPMENT", name="EQUIPMENT", value="0"))
        a = action("BAT", uses=(use("HOURS", dimension="LABOUR"),))
        b = bundle(actions=(a,), domains=domains,
                   covered=(coverage("BAT", "LABOUR"), coverage("BAT", "CASH", "NOT_REQUIRED"), coverage("BAT", "EQUIPMENT", "NOT_REQUIRED")))
        self.assertEqual("RESERVED_PLANNED", reserve(session(limits, domains=domains), b).decisions[0].status)
        self.assertEqual(1, len(b.actions[0].resource_uses))

    def test_not_required_is_inconsistent_with_a_supplied_use(self):
        b = bundle(covered=(coverage("ACTION-BUNDLE-1", applicability="NOT_REQUIRED"),))
        with self.assertRaises(AnnualLedgerError):
            reserve(session(), b)

    def test_unknown_catalogue_or_domain_does_not_become_complete(self):
        domains = catalogue(completeness="Q")
        self.assertEqual("BLOCKED_PREREQUISITE", reserve(session(domains=domains), bundle(domains=domains)).decisions[0].status)
        b = bundle(covered=(coverage("ACTION-BUNDLE-1", applicability="Q"),))
        self.assertEqual("BLOCKED_PREREQUISITE", reserve(session(), b).decisions[0].status)

    def test_catalogue_version_and_domain_changes_require_matching_qualification(self):
        b = bundle()
        with self.assertRaises(AnnualLedgerError):
            reserve(session(domains=catalogue(version="v2")), b)
        with self.assertRaises(AnnualLedgerError):
            reserve(session(), replace(b, requirement_coverage=()))

    def test_known_flow_excess_remains_fail_with_unknown_other_use(self):
        s = session((limit(value="1"),))
        b = bundle(actions=(action("BAT", uses=(use("KNOWN", "2"), use("UNKNOWN", None))),))
        r = reserve(s, b)
        check = r.decisions[0].resource_checks[0]
        self.assertEqual("FAIL", check.status)
        self.assertEqual(Fraction(2), check.known_use_lower_bound)
        self.assertIsNone(check.used_or_peak)
        self.assertIsNone(check.remaining)

    def test_known_concurrent_excess_remains_fail_with_unknown_use(self):
        s = session((limit("CONCURRENT", "1"),))
        b = bundle(actions=(action("BAT", uses=(use("KNOWN", "2"), use("UNKNOWN", None))),))
        check = reserve(s, b).decisions[0].resource_checks[0]
        self.assertEqual("FAIL", check.status)
        self.assertEqual(Fraction(2), check.known_use_lower_bound)
        self.assertIsNone(check.used_or_peak)

    def test_known_unfunded_opening_is_not_erased_by_unknown_payment(self):
        s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening="-1"),))
        b = bundle(actions=(action("BAT", uses=(use("UNKNOWN", None, unit="HUF"),)),))
        check = reserve(s, b).decisions[0].resource_checks[0]
        self.assertEqual("FAIL", check.status)
        self.assertEqual("2028-01-01", check.first_cash_gap_on)
        self.assertIsNone(check.used_or_peak)

    def test_unknown_later_receipt_cannot_erase_known_earlier_cash_gap(self):
        receipt = CashRelease("UNKNOWN-JULY", "2028-07-01", q(None, "HUF"))
        s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(receipt,)),))
        b = bundle(actions=(action("BAT", uses=(use("JAN", "1", start="2028-01-10", stop="2028-01-11", unit="HUF"),)),))
        check = reserve(s, b).decisions[0].resource_checks[0]
        self.assertEqual("FAIL", check.status)
        self.assertEqual("2028-01-10", check.first_cash_gap_on)

    def test_unknown_opening_does_not_hide_definite_flow_or_concurrent_excess(self):
        for kind in ("ANNUAL_FLOW", "CONCURRENT"):
            with self.subTest(kind=kind):
                s = session((limit(kind, "1"),), opening_state="Q")
                b = bundle(actions=(action("BAT", uses=(use("KNOWN", "2"),)),))
                r = reserve(s, b)
                checks = {item.constraint_id: item for item in r.decisions[0].resource_checks}
                self.assertEqual("WAIT_RESOURCE", r.decisions[0].status)
                self.assertEqual("UNKNOWN", checks["OPENING_COMMITMENTS"].status)
                self.assertEqual("FAIL", checks["LIMIT"].status)
                self.assertEqual(Fraction(2), checks["LIMIT"].known_use_lower_bound)
                self.assertIsNone(checks["LIMIT"].used_or_peak)
                self.assertIsNone(checks["LIMIT"].remaining)

    def test_unknown_opening_preserves_known_payment_gap_but_not_cash_pass(self):
        for opening, expected in (("0", "FAIL"), ("10", "UNKNOWN")):
            with self.subTest(opening=opening):
                s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening=opening),), opening_state="Q")
                b = bundle(actions=(action("BAT", uses=(use("PAY", "2", unit="HUF"),)),))
                r = reserve(s, b)
                check = next(item for item in r.decisions[0].resource_checks if item.constraint_id == "LIMIT")
                self.assertEqual(expected, check.status)
                self.assertEqual("WAIT_RESOURCE", r.decisions[0].status)
                self.assertIsNone(check.used_or_peak)
                self.assertIsNone(check.remaining)
                self.assertEqual(Fraction(2), check.known_use_lower_bound)
                self.assertEqual("2028-02-01" if expected == "FAIL" else None, check.first_cash_gap_on)

    def test_unknown_opening_keeps_negative_opening_gap_without_new_uses(self):
        s = session((limit("PUBLIC_CASH", "100", unit="HUF", opening="-1"),), opening_state="Q")
        r = reserve(s)
        check = next(item for item in r.resource_checks if item.constraint_id == "LIMIT")
        self.assertEqual("FAIL", check.status)
        self.assertEqual("2028-01-01", check.first_cash_gap_on)
        self.assertEqual(Fraction(0), check.known_use_lower_bound)
        self.assertIsNone(check.used_or_peak)

    def test_network_proof_binds_opening_knowledge_state_and_provenance(self):
        known = session()
        unknown = session(opening_state="Q")
        other = create_annual_plan(ledger_id=known.state.ledger_id, plan_year=known.state.plan_year,
                                  plan_basis_id=known.state.plan_basis_id, calendar_timezone=known.state.calendar_timezone,
                                  constraints=known.state.constraints, requirement_catalogue=known.state.requirement_catalogue,
                                  opening_uses_state="NONE", opening_uses_refs=("OTHER-QUALIFIED-OPENING",), opening_uses=())
        witness = JointNetworkAssessment(known.active_set_digest, 2028, "PASS", "SCN", ("SCN-JOINT-NETWORK",), "Exact known opening.")
        self.assertEqual("PASS", known.assess_joint_network(witness))
        self.assertEqual("UNKNOWN", unknown.assess_joint_network(witness))
        self.assertEqual("UNKNOWN", other.assess_joint_network(witness))
        self.assertEqual(3, len({known.active_set_digest, unknown.active_set_digest, other.active_set_digest}))
        # This binding does not invent a resource/finance condition for a network study.
        self.assertEqual("PASS", unknown.assess_joint_network(replace(witness, active_set_digest=unknown.active_set_digest)))

    def test_cash_pool_requires_explicit_fungibility_and_access_scope(self):
        root = limit("PUBLIC_CASH", "100", unit="HUF", opening="100")
        for qualification in (None, replace(root.cash_pool_qualification, semantics="EARMARKED_SOURCE_ALLOCATIONS"),
                              replace(root.cash_pool_qualification, evidence_status="Q")):
            with self.subTest(qualification=qualification), self.assertRaises(AnnualLedgerError):
                session((replace(root, cash_pool_qualification=qualification),))

    def test_subview_cannot_inflate_receipt_or_advance_availability_even_with_extra_total_cash(self):
        source = CashRelease("RECEIPT", "2028-06-01", q("10", "HUF"))
        restriction = CashViewRestriction("SCN", ("SCN-ACCESS",), "Explicit restriction does not authorize an increase.")
        for view in (replace(source, quantity=q("20", "HUF"), view_restriction=restriction),
                     replace(source, available_on="2028-01-01", view_restriction=restriction)):
            with self.subTest(view=view), self.assertRaises(AnnualLedgerError):
                session((limit("PUBLIC_CASH", "100", unit="HUF", opening="100", releases=(source,), name="TOTAL"),
                         limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(view,), scope=REGION, name="REGION", pool_total=False)))

    def test_smaller_later_access_view_is_qualified_and_does_not_create_total_cash(self):
        source = CashRelease("RECEIPT", "2028-02-01", q("10", "HUF", status="OBS"))
        view = CashRelease("RECEIPT", "2028-03-01", q("5", "HUF", status="DER"),
                           CashViewRestriction("DER", ("DER-REGIONAL-ACCESS",), "Derived non-additive regional access ceiling on the same fungible pool."))
        limits = (limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(source,), name="TOTAL"),
                  limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(view,), scope=REGION, name="REGION", pool_total=False))
        for amount, start, expected in (("5", "2028-03-01", "RESERVED_PLANNED"), ("6", "2028-03-01", "WAIT_RESOURCE"), ("1", "2028-02-01", "WAIT_RESOURCE")):
            b = bundle(actions=(action("BAT", uses=(use("PAY", amount, unit="HUF", start=start, stop="2028-04-01"),)),))
            with self.subTest(amount=amount, start=start):
                self.assertEqual(expected, reserve(session(limits), b).decisions[0].status)
        self.assertEqual("OBS", source.quantity.status)
        self.assertEqual("DER", view.quantity.status)

    def test_modified_receipt_view_needs_qualified_restriction_and_original_root(self):
        source = CashRelease("RECEIPT", "2028-01-01", q("10", "HUF"))
        for view in (replace(source, source_event_id="UNBOUND"), replace(source, quantity=q("5", "HUF")),
                     replace(source, available_on="2028-02-01"),
                     replace(source, quantity=q("5", "HUF", status="OBS"), view_restriction=CashViewRestriction("DER", ("REF",), "Restricted amount."))):
            with self.subTest(view=view), self.assertRaises(AnnualLedgerError):
                session((limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(source,), name="TOTAL"),
                         limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(view,), scope=REGION, name="REGION", pool_total=False)))

    def test_unknown_total_receipt_cannot_become_known_in_a_view(self):
        source = CashRelease("RECEIPT", "2028-01-01", q(None, "HUF"))
        restriction = CashViewRestriction("SCN", ("SCN-ACCESS",), "Unknown source amount remains unknown.")
        limits = (limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(source,), name="TOTAL"),
                  limit("PUBLIC_CASH", "100", unit="HUF", opening="0", releases=(source,), scope=REGION, name="REGION", pool_total=False))
        self.assertEqual("WAIT_RESOURCE", reserve(session(limits), bundle(actions=(action("BAT", uses=(use("PAY", "1", unit="HUF"),)),))).decisions[0].status)
        with self.assertRaises(AnnualLedgerError):
            session((limits[0], replace(limits[1], releases=(replace(source, quantity=q("1", "HUF"), view_restriction=restriction),))))


if __name__ == "__main__":
    unittest.main()
