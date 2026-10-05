"""Complete SCN and adverse witnesses; no empirical/policy parameter adoption."""
import csv
from dataclasses import asdict, fields, is_dataclass, replace
from datetime import date
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import unittest

from modules.B01 import engine
from modules.B01.benefit_metric_contract import (
    BenefitContractError, Candidate, CandidateIdentity, CashCoverage, CashPeriod, ComparisonFrame,
    Constraint, EffectContribution, Evidence, HouseholdProtection, Measurement,
    MetricDefinition, MetricRole, OverlapAssessment, Period, PeriodAdapter,
    PeriodProtection, PopulationQualification, RatioPolicy, Transformation,
    UtilityMapping, bind_b12_output, cash_scope_digest, exact, fingerprint, load_benefit_contract,
)
from modules.B12.input_accounting_contract import MoneyBasis, Reference, Scalar, audit_accounting

ROOT = Path(__file__).resolve().parents[1]
SCN = Evidence("SCN", "SCN:explicit-supplied-witness")
Q = Evidence("Q", "Q:obtain-claim-specific-output")
YEAR = Period("2028-01-01", "2029-01-01", "HALF_OPEN", "Europe/Budapest")
MONEY = MoneyBasis("SCN:HUF-2028-real", "HUF", "REAL", date(2028, 1, 1),
                   Reference("SYNTHETIC_WITNESS", "SYNTHETIC_WITNESS:price", None, None))


def frame(**changes):
    values = dict(frame_id="SCN:comparison", version="1", methodology_ref="SCN:matched-method",
                  claim_scope="HOUSEHOLD", geography="SCN:region", service_basis="SCN:matched-service",
                  evaluation_horizon=YEAR, world_id="SCN:joint-world-1",
                  counterfactual_method="SCN:same-service-baseline-method", valuation_method="SCN:upstream-evaluation",
                  evidence=SCN)
    values.update(changes)
    return ComparisonFrame(**values)


def metric(name, **changes):
    values = dict(metric_id=name, version="1", concept="SCN:explicit-" + name, unit="HUF",
                  actor="SOCIETY" if name == "benefit" else "PUBLIC", consolidation_boundary="SCN:HU-economic-boundary",
                  meaning="INCREMENTAL", native_counting_unit="HOUSEHOLD", per_unit_denominator="NOT_APPLICABLE",
                  accounting_basis="SCN:qualified-economic-total", time_basis="SCN:evaluation-total",
                  counterfactual_method="SCN:same-service-baseline-method", valuation_method="SCN:upstream-evaluation",
                  quantity_dimension="MONETARY", money_basis=MONEY, denominator_kind="NONE" if name == "benefit" else "GROSS_PUBLIC_OUTLAY",
                  historical_component=None, evidence=SCN)
    values.update(changes)
    return MetricDefinition(**values)


def mapping(definition, f, *, direction="MAXIMIZE", anchors=((-10, 0), (0, 1), (20, 3)), **changes):
    values = dict(mapping_id="SCN:utility:" + definition.metric_id, version="1", metric_digest=fingerprint(definition),
                  frame_digest=fingerprint(f), raw_direction=direction, domain=(anchors[0][0], anchors[-1][0]),
                  anchors=anchors, evidence=SCN)
    values.update(changes)
    return UtilityMapping(**values)


def policy(f, definitions, **changes):
    values = dict(policy_id="SCN:ratio-policy", version="1", mode="SCN", method="RATIO_ORDERING",
                  frame_digest=fingerprint(f), numerator_metric_digest=fingerprint(definitions[0]),
                  denominator_metric_digest=fingerprint(definitions[1]), ratio_unit=f"{definitions[0].unit or 'Q'}/HUF",
                  roles=tuple(MetricRole(fingerprint(d), "OBJECTIVE" if i < 2 else "DIAGNOSTIC", "SCN:role-qualification")
                              for i, d in enumerate(definitions)), constraints=(), utility_mappings=(), evidence=SCN)
    values.update(changes)
    return RatioPolicy(**values)


def candidate(name, f, definitions, values, **changes):
    identity = CandidateIdentity(name, f.claim_scope, "scope:" + name, "record-or-project:" + name,
                                 fingerprint(("SCN:bundle", name)), "baseline:" + name, "programme:" + name, f.world_id)
    measures = tuple(Measurement("SCN:measurement:" + name + ":" + d.metric_id, fingerprint(d), fingerprint(identity),
                                fingerprint(f), value, d.unit or "Q", (YEAR,), f.evaluation_horizon, f.valuation_method,
                                "Q" if value is None else "READY", "SCN:upstream", name + ":" + d.metric_id, "1", SCN)
                     for d, value in zip(definitions, values))
    periods = tuple(CashPeriod("SCN:" + kind, kind, YEAR) for kind in ("INITIAL", "INTERIM", "PAYMENT", "SETTLEMENT"))
    population = None
    if f.claim_scope == "POPULATION":
        population = PopulationQualification(identity.scope_id, "SCN:joint-model", "1", fingerprint(("SCN:output", name)),
                                             "SCN:weighting", "SCN:diagnostics", "SCN:aligned-uncertainty",
                                             "SCN:structural-sensitivity", "SCN:coverage", "JOINT_QUALIFYING_POPULATION_NOT_MEAN", SCN)
    protection = HouseholdProtection(fingerprint(identity), fingerprint(f), fingerprint(periods),
                                    "HOUSEHOLD_PERIODS" if f.claim_scope == "HOUSEHOLD" else "POPULATION_JOINT_ESTIMATE",
                                    tuple(PeriodProtection(p, "PASS", SCN) for p in periods), population)
    overlap = OverlapAssessment(fingerprint(identity), fingerprint(f), fingerprint(measures[0]), fingerprint(measures[1]),
                                definitions[0].consolidation_boundary, "COMPLETE",
                                (EffectContribution("SCN:aggregate-total", "SCN:producer-total-event", "SCN:qualified-economic-contribution"),), (), (), SCN)
    data = dict(identity=identity, measurements=measures, required_cash_periods=periods,
                period_inventory_evidence=SCN, protection=protection, overlap=overlap,
                first_cashflow_on="2028-01-01",
                cash_coverage=tuple(CashCoverage(p.kind, "REQUIRED", (p.period_id,), SCN) for p in periods))
    data.update(changes)
    result = Candidate(**data)
    return replace(result, protection=replace(protection, period_inventory_digest=cash_scope_digest(result))) if result.protection is protection else result


def remeasure(c, index, **changes):
    values = list(c.measurements)
    values[index] = replace(values[index], **changes)
    overlap = c.overlap
    if overlap is not None:
        overlap = replace(overlap, numerator_output_digest=fingerprint(values[0]), denominator_output_digest=fingerprint(values[1]))
    return replace(c, measurements=tuple(values), overlap=overlap)


def bound(d, f, operator, lower=None, upper=None, **changes):
    values = dict(constraint_id="SCN:" + d.metric_id + ":" + operator, metric_digest=fingerprint(d), frame_digest=fingerprint(f),
                  space="RAW", operator=operator, lower=lower, upper=upper, unit=d.unit, utility_digest=None, required=True, evidence=SCN)
    values.update(changes)
    return Constraint(**values)


class BenefitMetricTests(unittest.TestCase):
    def setUp(self):
        self.f = frame()
        self.defs = (metric("benefit"), metric("public-cost"))
        self.p = policy(self.f, self.defs)

    def compare(self, *candidates, **changes):
        args = dict(frame=self.f, definitions=self.defs, policy=self.p, candidates=candidates)
        args.update(changes)
        return engine.compare_benefit_ratios(**args)

    def c(self, name="A", n=12, d=6, **changes):
        return candidate(name, self.f, self.defs, (n, d), **changes)

    def test_s01_signed_zero_unknown_exact_and_invalid_numbers(self):
        for value in (-5, 0, "-1.25", Decimal("-3.5"), Fraction(-2, 7), None):
            result = self.compare(self.c(n=value)).candidates[0]
            self.assertEqual(result.metrics[0].raw_quantity, exact(value))
            self.assertEqual(result.ratio.value, None if value is None else exact(value) / 6)
        for value in (True, False, 1.2, float("nan"), Decimal("NaN"), "Infinity", "x"):
            with self.subTest(value=value), self.assertRaises(BenefitContractError):
                self.compare(self.c(n=value))

    def test_s01_number_does_not_repair_unresolved_definition(self):
        defs = (replace(self.defs[0], concept=None), self.defs[1])
        result = self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        self.assertEqual(result.candidates[0].metrics[0].raw_quantity, 12)
        self.assertEqual(result.candidates[0].ratio.status, "NUMERATOR_Q")
        self.assertEqual(result.unresolved_candidates, ("A",))

    def test_s01_each_unresolved_semantic_field_remains_q(self):
        for field in ("concept", "unit", "actor", "consolidation_boundary", "meaning", "native_counting_unit",
                      "per_unit_denominator", "accounting_basis", "time_basis", "counterfactual_method",
                      "valuation_method", "denominator_kind", "quantity_dimension"):
            defs = (replace(self.defs[0], **{field: None}), self.defs[1])
            c = candidate("A", self.f, defs, (12, 6), overlap=None)
            with self.subTest(field=field):
                result = self.compare(c, definitions=defs, policy=policy(self.f, defs))
                self.assertEqual(result.candidates[0].metrics[0].status, "Q")
                self.assertEqual(result.unresolved_candidates, ("A",))

    def test_s02_upper_cost_lower_benefit_independent_of_direction(self):
        utility = mapping(self.defs[1], self.f, direction="MINIMIZE", anchors=((0, 1), (10, 0)))
        p = replace(self.p, utility_mappings=(utility,), constraints=(bound(self.defs[1], self.f, "UPPER_BOUND", upper=5),
                                                                    bound(self.defs[0], self.f, "LOWER_BOUND", lower=10)))
        result = self.compare(self.c(), policy=p).candidates[0]
        self.assertEqual([r.status for r in result.constraints], ["FAIL", "PASS"])
        self.assertEqual(result.utilities[0].value, Fraction(2, 5))
        self.assertEqual(result.status, "BLOCKED")

    def test_s02_known_failure_dominates_unknown_required_bound(self):
        p = replace(self.p, constraints=(bound(self.defs[1], self.f, "RANGE", lower=None, upper=5),
                                        bound(self.defs[0], self.f, "LOWER_BOUND", lower=None)))
        result = self.compare(self.c(), policy=p).candidates[0]
        self.assertEqual([r.status for r in result.constraints], ["FAIL", "Q"])
        self.assertEqual(result.status, "BLOCKED")

    def test_s02_bounds_are_inclusive_and_q_is_not_unlimited(self):
        for operator, low, high, expected in (("RANGE", 12, 12, "PASS"), ("LOWER_BOUND", None, None, "Q"),
                                               ("UPPER_BOUND", None, None, "Q")):
            p = replace(self.p, constraints=(bound(self.defs[0], self.f, operator, low, high),))
            self.assertEqual(self.compare(self.c(), policy=p).candidates[0].constraints[0].status, expected)

    def test_s03_increasing_decreasing_knots_plateaus_and_segments(self):
        for direction, anchors, value, expected, length in (
            ("MAXIMIZE", ((0, 0), (5, 1), (10, 1)), 0, 0, 1),
            ("MAXIMIZE", ((0, 0), (5, 1), (10, 1)), 5, 1, 1),
            ("MAXIMIZE", ((0, 0), (5, 1), (10, 1)), 7, 1, 2),
            ("MINIMIZE", ((0, 1), (5, "0.5"), (10, 0)), 10, 0, 1),
            ("MINIMIZE", ((0, 1), (5, "0.5"), (10, 0)), 2, Fraction(4, 5), 2),
        ):
            u = mapping(self.defs[0], self.f, direction=direction, anchors=anchors)
            trace = self.compare(self.c(n=value), policy=replace(self.p, utility_mappings=(u,))).candidates[0].utilities[0]
            self.assertEqual((trace.value, len(trace.segment)), (expected, length))
            self.assertEqual(trace.raw.definition.unit, "HUF")

    def test_s03_duplicate_and_nonmonotone_anchors_reject(self):
        for anchors in (((0, 0), (0, 1), (10, 1)), ((0, 0), (5, 1), (10, "0.5"))):
            with self.assertRaises(BenefitContractError):
                self.compare(self.c(), policy=replace(self.p, utility_mappings=(mapping(self.defs[0], self.f, anchors=anchors),)))

    def test_s03_mapping_version_changes_constraint_binding(self):
        u = mapping(self.defs[0], self.f)
        c = bound(self.defs[0], self.f, "LOWER_BOUND", 1, space="UTILITY", unit="UTILITY", utility_digest=fingerprint(u))
        with self.assertRaises(BenefitContractError):
            self.compare(self.c(), policy=replace(self.p, utility_mappings=(replace(u, version="2"),), constraints=(c,)))

    def test_s04_domain_unknown_not_clipped_and_raw_failure_survives(self):
        u = mapping(self.defs[0], self.f, anchors=((0, 0), (10, 1)))
        p = replace(self.p, utility_mappings=(u,), constraints=(bound(self.defs[0], self.f, "UPPER_BOUND", upper=10),))
        result = self.compare(self.c(n=12), policy=p).candidates[0]
        self.assertIsNone(result.utilities[0].value)
        self.assertEqual(result.utilities[0].reason, "OUTSIDE_QUALIFIED_DOMAIN")
        self.assertEqual(result.status, "BLOCKED")

    def test_s05_unitless_outputs_do_not_pool_metric_utilities(self):
        u1 = mapping(self.defs[0], self.f, anchors=((0, 0), (12, 1)))
        u2 = mapping(self.defs[1], self.f, anchors=((0, 0), (6, 1)))
        result = self.compare(self.c(), policy=replace(self.p, utility_mappings=(u1, u2))).candidates[0]
        self.assertEqual(tuple(u.value for u in result.utilities), (1, 1))
        self.assertNotEqual(result.utilities[0].mapping.metric_digest, result.utilities[1].mapping.metric_digest)
        self.assertEqual(result.ratio.value, 2)
        self.assertFalse(hasattr(result, "weighted_score"))

    def test_s06_distinct_households_and_baselines_compare_under_shared_frame(self):
        result = self.compare(self.c("A"), self.c("B", 9, 5))
        self.assertEqual(result.tie_groups, (("A",), ("B",)))
        self.assertNotEqual(result.candidates[0].candidate.identity.baseline_id, result.candidates[1].candidate.identity.baseline_id)
        self.assertTrue(result.arithmetic_scope_complete)

    def test_s06_same_labels_do_not_bypass_definition_or_frame(self):
        for field, value in (("unit", "EUR"), ("actor", "HOUSEHOLD"), ("denominator_kind", "NET_PUBLIC_COST")):
            d = replace(self.defs[1], **{field: value})
            bad = remeasure(self.c(), 1, metric_digest=fingerprint(d))
            with self.subTest(field=field), self.assertRaises(BenefitContractError):
                self.compare(bad)
        for f in (replace(self.f, world_id="SCN:other-world"), replace(self.f, geography="SCN:other-region"),
                  replace(self.f, evaluation_horizon=Period("2028-01-01", "2030-01-01", "HALF_OPEN", "Europe/Budapest"))):
            with self.assertRaises(BenefitContractError):
                self.compare(remeasure(self.c(), 0, frame_digest=fingerprint(f)))

    def test_s06_nominal_real_money_basis_mismatch_rejects(self):
        defs = (replace(self.defs[0], money_basis=replace(MONEY, nominal_real="NOMINAL")), self.defs[1])
        with self.assertRaises(BenefitContractError):
            self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))

    def test_s07_upfront_and_later_native_events_share_qualified_evaluation(self):
        c = remeasure(self.c(), 0, native_periods=(Period("2028-10-01", "2029-01-01", "HALF_OPEN", "Europe/Budapest"),))
        c = remeasure(c, 1, native_periods=(Period("2028-01-01", "2028-01-02", "HALF_OPEN", "Europe/Budapest"),))
        result = self.compare(c).candidates[0]
        self.assertEqual(result.status, "COMPARABLE")
        self.assertNotEqual(result.metrics[0].measurement.native_periods, result.metrics[1].measurement.native_periods)

    def test_s07_inclusive_adapter_explicit_and_exact(self):
        inclusive = Period("2028-01-01", "2028-12-31", "INCLUSIVE", "Europe/Budapest")
        c = remeasure(self.c(), 0, evaluation_period=inclusive)
        with self.assertRaises(BenefitContractError):
            self.compare(c)
        good = PeriodAdapter(inclusive, YEAR, SCN)
        self.assertEqual(self.compare(remeasure(c, 0, period_adapter=good)).candidates[0].status, "COMPARABLE")
        with self.assertRaises(BenefitContractError):
            self.compare(remeasure(c, 0, period_adapter=replace(good, original=replace(inclusive, end="2028-12-30"))))
        unknown = self.compare(remeasure(c, 0, period_adapter=replace(good, evidence=Q)))
        self.assertEqual(unknown.unresolved_candidates, ("A",))

    def test_s08_upstream_q_pointer_and_unimplemented_are_not_ready(self):
        for status in ("Q", "EXTERNAL_ADMISSION", "UNIMPLEMENTED"):
            result = self.compare(remeasure(self.c(), 0, native_status=status)).candidates[0]
            self.assertEqual(result.metrics[0].raw_quantity, 12)
            self.assertEqual(result.ratio.status, "NUMERATOR_Q")
            self.assertEqual(result.metrics[0].measurement.native_status, status)

    def test_s08_valid_b12_case_preserved_without_financial_promotion(self):
        from test_b12_input_accounting_contract import case
        bcase = case()
        audit = audit_accounting(bcase)
        f = replace(self.f, evaluation_horizon=Period("2026-01-01", "2027-01-01", "HALF_OPEN", "Europe/Budapest"))
        d = replace(self.defs[0], money_basis=bcase.monetary_basis)
        identity = CandidateIdentity("SCN:B12-candidate", "HOUSEHOLD", bcase.scope.household_id, bcase.intervention_id,
                                     fingerprint(("SCN:exact-case-scope", bcase.case_id)), bcase.baseline_id, bcase.programme_id, f.world_id)
        adapter = PeriodAdapter(Period("2026-01-01", "2026-12-31", "INCLUSIVE", "Europe/Budapest"), f.evaluation_horizon, SCN)
        m = bind_b12_output(case=bcase, audit=audit, output_key="valuation.programme", definition=d, identity=identity,
                            frame=f, evidence=SCN, correspondence=SCN, period_adapter=adapter)
        self.assertEqual(m.native_status, "Q")
        self.assertIsNone(m.quantity)
        self.assertIs(m.b12_binding.case, bcase)
        self.assertIs(m.b12_binding.audit, audit)
        self.assertIs(m.b12_binding.case.valuation, bcase.valuation)
        self.assertIn("valuation", audit.unavailable)
        self.assertEqual(m.evaluation_period.convention, "INCLUSIVE")
        self.assertEqual(m.b12_binding.case.transition_ref, "S2_TO_S3")
        from modules.B01.benefit_metric_contract import _measurement_trace
        with self.assertRaises(BenefitContractError):
            _measurement_trace(d, replace(m, quantity=100, native_status="READY"), identity, f)
        with self.assertRaises(BenefitContractError):
            bind_b12_output(case=replace(bcase, transition_ref="COMPOSITE_HP_BATTERY"), audit=audit,
                            output_key="valuation.programme", definition=d, identity=identity, frame=f,
                            evidence=SCN, correspondence=SCN, period_adapter=adapter)

    def test_s08_b12_ready_synthetic_bucket_remains_exact_scenario(self):
        from test_b12_input_accounting_contract import case
        bcase = case()
        audit = audit_accounting(bcase)
        f = replace(self.f, evaluation_horizon=Period("2026-01-01", "2026-12-31", "INCLUSIVE", "Europe/Budapest"))
        d = replace(self.defs[1], money_basis=bcase.monetary_basis, concept="B12:total_initial_cost.programme",
                    actor="CASE_COST_SCOPE", meaning="TOTAL", denominator_kind="NONE")
        identity = CandidateIdentity("A", "HOUSEHOLD", bcase.scope.household_id, bcase.intervention_id,
                                     fingerprint(("SCN:case-scope", bcase.case_id)), bcase.baseline_id, bcase.programme_id, f.world_id)
        m = bind_b12_output(case=bcase, audit=audit, output_key="total_initial_cost.programme", definition=d,
                            identity=identity, frame=f, evidence=SCN, correspondence=SCN)
        self.assertEqual(m.quantity, audit.amounts["total_initial_cost.programme"])
        self.assertEqual(m.native_status, "READY")
        self.assertEqual(m.b12_binding.audit_sha256, fingerprint(audit))

    def test_s09_denominator_states_and_signed_numerator(self):
        for d, expected in ((0, "ZERO_DENOMINATOR"), (-2, "NEGATIVE_DENOMINATOR"), (None, "DENOMINATOR_Q"), (3, "READY")):
            result = self.compare(self.c(n=-2, d=d)).candidates[0]
            self.assertEqual(result.ratio.status, expected)
            self.assertEqual(result.ratio.value, Fraction(-2, 3) if d == 3 else None)
        self.assertEqual(self.compare(self.c(n=0)).candidates[0].ratio.value, 0)

    def test_s10_named_denominator_kinds_have_distinct_contracts(self):
        hashes = set()
        for kind in ("GROSS_PUBLIC_OUTLAY", "NET_PUBLIC_COST", "SEED_BRIDGE"):
            defs = (self.defs[0], replace(self.defs[1], denominator_kind=kind))
            result = self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
            self.assertEqual(result.candidates[0].ratio.value, 2)
            hashes.add(fingerprint(defs[1]))
        self.assertEqual(len(hashes), 3)

    def test_s10_nonmonetary_numerator_does_not_require_full_b12(self):
        defs = (replace(self.defs[0], unit="kWh", quantity_dimension="NONMONETARY", money_basis=None, concept="SCN:incremental-energy-saving"), self.defs[1])
        result = self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        self.assertEqual((result.candidates[0].ratio.value, result.candidates[0].ratio.unit), (2, "kWh/HUF"))

    def test_s11_duplicate_events_and_inclusion_conflicts_fail(self):
        c = self.c()
        for contributions, excluded, pairs in (
            ((EffectContribution("GDP", "event", "same-money-contribution"), EffectContribution("jobs", "event", "same-money-contribution")), (), ()),
            ((EffectContribution("GDP", "gdp-event", "gdp-contribution", ("jobs",)), EffectContribution("jobs", "jobs-event", "jobs-contribution")), (), ()),
            ((EffectContribution("GDP", "gdp-event", "gdp-contribution"),), ("GDP",), ()),
            ((EffectContribution("GDP", "gdp-event", "gdp-contribution"), EffectContribution("jobs", "jobs-event", "jobs-contribution")), (), (("GDP", "jobs"),)),
        ):
            result = self.compare(replace(c, overlap=replace(c.overlap, contributions=contributions,
                                                            excluded_effect_ids=excluded, known_overlapping_pairs=pairs))).candidates[0]
            self.assertEqual(result.overlap_status, "FAIL_DECLARED_OVERLAP")
            self.assertEqual(result.status, "BLOCKED")

    def test_s11_different_ids_do_not_close_unknown_coverage(self):
        c = self.c()
        c = replace(c, overlap=replace(c.overlap, coverage="Q", contributions=(EffectContribution("GDP", "gdp", "gdp-contribution"), EffectContribution("jobs", "jobs", "jobs-contribution"))),
                    utility_redundancy_notes=("SCN:employment diagnostic may be redundant with GDP utility; not an added cash event",))
        result = self.compare(c).candidates[0]
        self.assertEqual(result.overlap_status, "Q")
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertEqual(result.candidate.utility_redundancy_notes, c.utility_redundancy_notes)
        known = self.compare(self.c()).candidates[0]
        self.assertEqual(known.overlap_status, "CONDITIONAL_SCN")

    def test_s11_overlap_binds_exact_upstream_outputs(self):
        c = self.c()
        with self.assertRaises(BenefitContractError):
            self.compare(replace(c, measurements=(replace(c.measurements[0], quantity=15), c.measurements[1])))

    def test_s12_initial_and_interim_failures_cannot_be_offset(self):
        for index in (0, 1):
            c = self.c(n=1000000, d=1)
            results = list(c.protection.results)
            results[index] = replace(results[index], status="FAIL")
            results[3] = replace(results[3], status="Q")
            r = self.compare(replace(c, protection=replace(c.protection, results=tuple(results)))).candidates[0]
            self.assertEqual(r.protection_status, "FAIL")
            self.assertEqual(r.status, "BLOCKED")
            self.assertEqual(r.ratio.value, 1000000)

    def test_s12_q_missing_or_incomplete_floor_never_passes(self):
        c = self.c()
        for changed in (replace(c, protection=None), replace(c, protection=replace(c.protection, results=tuple(replace(r, evidence=Q) for r in c.protection.results))),
                        replace(c, protection=replace(c.protection, results=c.protection.results[:1]))):
            self.assertEqual(self.compare(changed).candidates[0].protection_status, "Q")

    def test_s12_candidate_bundle_baseline_and_cash_period_mismatch_reject(self):
        c = self.c()
        for field, value in (("bundle_fingerprint", fingerprint("other-bundle")), ("baseline_id", "other-baseline")):
            with self.assertRaises(BenefitContractError):
                self.compare(replace(c, identity=replace(c.identity, **{field: value})))
        row = c.protection.results[0]
        bad = replace(row, cash_period=replace(row.cash_period, period=Period("2028-02-01", "2029-01-01", "HALF_OPEN", "Europe/Budapest")))
        with self.assertRaises(BenefitContractError):
            self.compare(replace(c, protection=replace(c.protection, results=(bad,) + c.protection.results[1:])))

    def test_s13_population_scenario_no_census_or_individual_permission(self):
        f = replace(self.f, claim_scope="POPULATION")
        defs = tuple(replace(d, native_counting_unit="DWELLING") for d in self.defs)
        c = candidate("population-project", f, defs, (12, 6))
        result = self.compare(c, frame=f, definitions=defs, policy=policy(f, defs))
        self.assertEqual(result.tie_groups, (("population-project",),))
        self.assertFalse(result.individual_permission)
        self.assertFalse(result.selected_or_funded)
        with self.assertRaises(BenefitContractError):
            self.compare(replace(self.c(), protection=c.protection))

    def test_s13_population_mean_cannot_qualify_household_floor(self):
        f = replace(self.f, claim_scope="POPULATION")
        c = candidate("P", f, self.defs, (12, 6))
        p = replace(c.protection, population_qualification=replace(c.protection.population_qualification, claim="POPULATION_MEAN"))
        with self.assertRaises(BenefitContractError):
            self.compare(replace(c, protection=p), frame=f, policy=policy(f, self.defs))

    def test_s13_admitted_e2_population_preserves_debt_without_census(self):
        f = replace(self.f, claim_scope="POPULATION")
        c = candidate("P", f, self.defs, (12, 6))
        admitted = Evidence("ADMITTED", "SCN:external-model-qualification-witness", (("SCN:source-pin", "a" * 64),), "E2", ("SCN:exact-primary-validation-debt",))
        p = replace(c.protection, population_qualification=replace(c.protection.population_qualification, evidence=admitted))
        result = self.compare(replace(c, protection=p), frame=f, policy=policy(f, self.defs))
        self.assertEqual(result.candidates[0].protection_status, "PASS")
        self.assertEqual(result.candidates[0].candidate.protection.population_qualification.evidence.validation_debt, admitted.validation_debt)

    def test_s14_q_diagnostic_and_unused_weights_do_not_gate_ratio(self):
        defs = self.defs + (metric("jobs-diagnostic", unit="job-year", quantity_dimension="NONMONETARY", money_basis=None, denominator_kind="NONE", actor="WORKERS", evidence=Q),)
        c = candidate("A", self.f, defs, (12, 6, None))
        u = mapping(defs[2], self.f, evidence=Q)
        p = policy(self.f, defs, utility_mappings=(u,), unused_weights=(("jobs-diagnostic", None),))
        result = self.compare(c, definitions=defs, policy=p)
        self.assertEqual(result.tie_groups, (("A",),))
        self.assertEqual(result.candidates[0].utilities[0].status, "Q")
        self.assertTrue(result.arithmetic_scope_complete)

    def test_s14_required_utility_q_gates_but_optional_does_not(self):
        u = mapping(self.defs[0], self.f, evidence=Q)
        c = bound(self.defs[0], self.f, "LOWER_BOUND", 1, space="UTILITY", unit="UTILITY", utility_digest=fingerprint(u))
        p = replace(self.p, utility_mappings=(u,), constraints=(c,))
        self.assertEqual(self.compare(self.c(), policy=p).candidates[0].status, "UNRESOLVED")
        p = replace(p, constraints=(replace(c, required=False),))
        self.assertEqual(self.compare(self.c(), policy=p).candidates[0].status, "COMPARABLE")

    def test_s14_unsupported_modes_do_not_default(self):
        for method in ("MCDA", "LEXICOGRAPHIC", "", "AUTO"):
            with self.assertRaises(BenefitContractError):
                self.compare(self.c(), policy=replace(self.p, method=method))

    def test_s15_partial_ties_and_nonpositive_candidates_remain_visible(self):
        result = self.compare(self.c("Z", 9, 5), self.c("A", 12, 6), self.c("B", 9, 5),
                              self.c("unknown", None, 1), self.c("zero", 1, 0), self.c("negative", 1, -1))
        self.assertEqual(result.tie_groups, (("A",), ("B", "Z")))
        self.assertEqual(result.unresolved_candidates, ("unknown",))
        self.assertEqual(result.nonpositive_denominator_candidates, ("negative", "zero"))
        self.assertFalse(result.arithmetic_scope_complete)
        self.assertFalse(hasattr(result, "winner"))

    def test_s16_aligned_worlds_can_reverse_order_without_probabilities(self):
        first = self.compare(self.c("A", 12, 6), self.c("B", 9, 5))
        second_frame = replace(self.f, world_id="SCN:joint-world-2")
        second = self.compare(candidate("A", second_frame, self.defs, (3, 6)), candidate("B", second_frame, self.defs, (9, 5)),
                              frame=second_frame, policy=policy(second_frame, self.defs))
        self.assertEqual(first.tie_groups, (("A",), ("B",)))
        self.assertEqual(second.tie_groups, (("B",), ("A",)))
        self.assertFalse(hasattr(first, "probability"))
        with self.assertRaises(BenefitContractError):
            self.compare(candidate("A", second_frame, self.defs, (3, 6)))

    def test_s17_ratio_order_is_not_budget_optimal_selection(self):
        result = self.compare(self.c("A", 12, 6), self.c("B", 9, 5), self.c("C", 9, 5))
        self.assertEqual(result.tie_groups, (("A",), ("B", "C")))
        # SCN witness only: A leaves 4 of a budget of 10; B+C costs 10 and
        # produces 18 versus A's 12. There is no production selection routine.
        self.assertEqual(10 - 6, 4)
        self.assertLess(4, 5)
        self.assertEqual(5 + 5, 10)
        self.assertGreater(9 + 9, 12)
        self.assertFalse(result.selected_or_funded)

    def test_s18_official_example_is_method_context_not_model_input(self):
        self.assertEqual((1000 - 700, 500 - 300, 500 - 400), (300, 200, 100))
        self.assertEqual(round(Fraction(7, 3), 1), Fraction(23, 10))
        contract = load_benefit_contract()
        self.assertIn("inconsistent", contract["official_illustration_boundary"]["meaning"])
        self.assertEqual(contract["numeric_defaults"], {})
        self.assertTrue(all(s["repo_snapshot_path"] is None for s in contract["method_sources"]))

    def test_s19_legacy_output_and_owner_unset_are_exact(self):
        raw = (json.dumps(asdict(engine.run_fixture(ROOT / "data/fixtures/b01_state_stock_scn.json")), ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual(sha256(raw).hexdigest(), "fd8fbc5bbb97820b4ed26cde510b636cb90af1a0ca0440aec014503eb58dca7a")
        owner = json.loads((ROOT / "registry/owner_policy_decisions.json").read_text())
        priority = owner["decisions"]["selection_priority"]
        self.assertTrue(all(priority[k] is None for k in ("benefit_metric_definition", "public_cost_denominator", "normalization_and_weights")))
        questions = list(csv.DictReader((ROOT / "registry/open_questions.csv").read_text().splitlines()))
        self.assertEqual(next(q["status"] for q in questions if q["question_id"] == "Q-B01-006"), "OPEN")

    def test_s19_canonical_call_cannot_adopt_scenario_definitions(self):
        result = self.compare(self.c(), policy=replace(self.p, mode="CANONICAL"))
        self.assertEqual(result.authority, "CANONICAL_NOT_READY")
        self.assertEqual(result.tie_groups, ())
        self.assertEqual(result.unresolved_candidates, ("A",))
        self.assertEqual(result.canonical_readiness, "Q-B01-006_OPEN")

    def test_s20_composed_entrypoint_trace_and_authority(self):
        u = mapping(self.defs[0], self.f)
        p = replace(self.p, utility_mappings=(u,), constraints=(bound(self.defs[0], self.f, "LOWER_BOUND", 0),))
        result = self.compare(self.c(), policy=p)
        r = result.candidates[0]
        self.assertEqual((r.metrics[0].raw_quantity, r.utilities[0].value, r.constraints[0].status, r.ratio.value),
                         (12, Fraction(11, 5), "PASS", 2))
        self.assertEqual((r.protection_status, r.status), ("PASS", "COMPARABLE"))
        self.assertEqual(result.authority, "CONDITIONAL_SCENARIO_COMPARISON")
        self.assertFalse(result.individual_permission)
        self.assertFalse(result.selected_or_funded)

    def test_exact_arithmetic_is_independent_of_decimal_context(self):
        with localcontext() as ctx:
            ctx.prec = 2
            result = self.compare(self.c(n="1.23456789", d="0.003"))
        self.assertEqual(result.candidates[0].ratio.value, Fraction(123456789, 300000))

    def test_empty_and_duplicate_candidate_universes_reject(self):
        with self.assertRaises(BenefitContractError):
            self.compare()
        with self.assertRaises(BenefitContractError):
            self.compare(self.c(), self.c())

    def test_metric_roles_cannot_exclude_household_protection(self):
        self.assertEqual(self.compare(self.c(protection=None)).candidates[0].status, "UNRESOLVED")
        with self.assertRaises(BenefitContractError):
            self.compare(self.c(), policy=replace(self.p, roles=()))

    def test_one_payment_floor_uses_qualified_applicability_without_invented_periods(self):
        c = self.c()
        day = CashPeriod("SCN:one-payment", "PAYMENT", Period("2028-01-01", "2028-01-02", "HALF_OPEN", "Europe/Budapest"))
        coverage = (CashCoverage("INITIAL", "REQUIRED", (day.period_id,), SCN),
                    CashCoverage("PAYMENT", "REQUIRED", (day.period_id,), SCN),
                    CashCoverage("INTERIM", "NOT_APPLICABLE", (), SCN),
                    CashCoverage("SETTLEMENT", "NOT_APPLICABLE", (), SCN))
        c = replace(c, required_cash_periods=(day,), cash_coverage=coverage)
        c = replace(c, protection=replace(c.protection, period_inventory_digest=cash_scope_digest(c), results=(PeriodProtection(day, "PASS", SCN),)))
        self.assertEqual(self.compare(c).candidates[0].protection_status, "PASS")
        for changed in (replace(c, first_cashflow_on="2027-12-31"),
                        replace(c, cash_coverage=tuple(replace(v, applicability="Q") if v.kind == "INTERIM" else v for v in coverage)),
                        replace(c, first_cashflow_on=None)):
            changed = replace(changed, protection=replace(changed.protection, period_inventory_digest=cash_scope_digest(changed)))
            self.assertEqual(self.compare(changed).candidates[0].protection_status, "Q")

    def test_shared_source_event_is_not_necessarily_duplicate_economic_value(self):
        c = self.c()
        contributions = (EffectContribution("SCN:energy-effect", "same-observation", "qualified-energy-component"),
                         EffectContribution("SCN:independent-endpoint", "same-observation", "qualified-distinct-component"))
        c = replace(c, overlap=replace(c.overlap, contributions=contributions))
        self.assertEqual(self.compare(c).candidates[0].overlap_status, "CONDITIONAL_SCN")
        c = replace(c, overlap=replace(c.overlap, coverage="Q"))
        self.assertEqual(self.compare(c).candidates[0].overlap_status, "Q")

    def test_b12_same_id_different_case_cannot_reuse_audit(self):
        from test_b12_input_accounting_contract import case, cost, rows
        original = case()
        # Ordinary metadata identities stay equal while the actual Case changes.
        from test_b12_input_accounting_contract import scalar
        changed = replace(original, costs=rows(cost(gross=scalar(200), net=scalar(160), vat=scalar(40), eligible_gross=scalar(200))))
        audit = audit_accounting(original)
        f = replace(self.f, evaluation_horizon=Period("2026-01-01", "2026-12-31", "INCLUSIVE", "Europe/Budapest"))
        d = replace(self.defs[0], money_basis=original.monetary_basis)
        identity = CandidateIdentity("A", "HOUSEHOLD", original.scope.household_id, original.intervention_id,
                                     fingerprint("SCN:case"), original.baseline_id, original.programme_id, f.world_id)
        with self.assertRaisesRegex(BenefitContractError, "actual existing producer output"):
            bind_b12_output(case=changed, audit=audit, output_key="valuation.programme", definition=d,
                            identity=identity, frame=f, evidence=SCN, correspondence=SCN)

    def test_b12_project_cost_cannot_become_public_incremental_outlay(self):
        from test_b12_input_accounting_contract import case
        bcase = case()
        f = replace(self.f, evaluation_horizon=Period("2026-01-01", "2026-12-31", "INCLUSIVE", "Europe/Budapest"))
        identity = CandidateIdentity("A", "HOUSEHOLD", bcase.scope.household_id, bcase.intervention_id,
                                     fingerprint("SCN:case"), bcase.baseline_id, bcase.programme_id, f.world_id)
        with self.assertRaisesRegex(BenefitContractError, "cannot be relabelled"):
            bind_b12_output(case=bcase, audit=audit_accounting(bcase), output_key="total_initial_cost.programme",
                            definition=replace(self.defs[1], money_basis=bcase.monetary_basis), identity=identity,
                            frame=f, evidence=SCN, correspondence=SCN)

    def test_explicit_conversion_retains_native_values_and_rejects_retagging(self):
        from test_b12_input_accounting_contract import scalar, ref
        from modules.B12.input_accounting_contract import Conversion
        conversion = Conversion(scalar(6, "EUR", "SCN:EUR-basis"), scalar(12, "HUF", MONEY.basis_id),
                                scalar(2, "ratio", "SCN:conversion-factor"), date(2028, 1, 1), ref("explicit-conversion"))
        transform = Transformation("CONVERSION", fingerprint("SCN:original-output"), "SCN:EUR-basis", MONEY.basis_id,
                                   "SCN:explicit-conversion", conversion, SCN,
                                   MoneyBasis("SCN:EUR-basis", "EUR", "REAL", date(2028, 1, 1), ref("EUR-basis")))
        c = remeasure(self.c(), 0, transformations=(transform,))
        result = self.compare(c).candidates[0]
        self.assertEqual(result.ratio.value, 2)
        self.assertIs(result.metrics[0].measurement.transformations[0].native_binding, conversion)
        for changed in (replace(transform, target_basis="other-HUF-price-date"),
                        replace(transform, native_binding=replace(conversion, converted=scalar(10, "HUF", MONEY.basis_id))),
                        replace(transform, native_binding=replace(conversion, multiplier=scalar(3, "ratio", "SCN:conversion-factor")))):
            with self.assertRaises(BenefitContractError):
                self.compare(remeasure(c, 0, transformations=(changed,)))

    def test_unresolved_b12_valuation_metadata_is_not_a_ready_transformation(self):
        from test_b12_input_accounting_contract import case
        native = case().valuation
        valuation = replace(native, basis_id=MONEY.basis_id,
                            discount_rate=replace(native.discount_rate, basis_id=MONEY.basis_id))
        transform = Transformation("VALUATION", fingerprint("SCN:upstream-cash"), "SCN:native-cash", MONEY.basis_id,
                                   self.f.valuation_method, valuation, SCN)
        result = self.compare(remeasure(self.c(), 0, transformations=(transform,))).candidates[0]
        self.assertEqual(result.ratio.status, "NUMERATOR_Q")
        self.assertIn("UPSTREAM_B12_TRANSFORMATION_Q", result.metrics[0].reasons)

    def test_actual_b12_external_references_keep_native_q(self):
        from test_b12_input_accounting_contract import case
        def external(obj):
            if isinstance(obj, Reference):
                return obj if obj.kind == "Q" else Reference("EXTERNAL_ADMISSION", "SCN:external-review-pointer-test", None, None)
            if isinstance(obj, Scalar):
                return obj if obj.truth == "Q" else replace(obj, truth="DER", scenario_ref=None, source_ids=("SCN:external-source-witness",),
                                                            evidence_tier="E2", admission_ref="SCN:external-review-qualification")
            if is_dataclass(obj):
                return replace(obj, **{f.name: external(getattr(obj, f.name)) for f in fields(obj)})
            if isinstance(obj, tuple):
                return tuple(external(x) for x in obj)
            return obj
        bcase = replace(external(case()), mode="CONDITIONAL_CASE")
        audit = audit_accounting(bcase)
        f = replace(self.f, evaluation_horizon=Period("2026-01-01", "2026-12-31", "INCLUSIVE", "Europe/Budapest"))
        d = replace(self.defs[0], money_basis=bcase.monetary_basis)
        identity = CandidateIdentity("A", "HOUSEHOLD", bcase.scope.household_id, bcase.intervention_id,
                                     fingerprint("SCN:case"), bcase.baseline_id, bcase.programme_id, f.world_id)
        m = bind_b12_output(case=bcase, audit=audit, output_key="financed_cash.incremental", definition=d,
                            identity=identity, frame=f, evidence=Evidence("EXTERNAL_ADMISSION", "SCN:pointer"), correspondence=SCN)
        self.assertEqual((m.native_status, m.quantity, m.b12_binding.audit.truth), ("Q", None, "Q"))

    def test_legacy_minimize_hard_minimum_remains_literal_lower_bound(self):
        data = json.loads((ROOT / "data/fixtures/b01_state_stock_scn.json").read_text())
        base = engine._candidate_from_payload(data["candidates"][1])
        policy = {k: replace(v, weight=0.0, hard_minimum=0.0) for k, v in engine._policy_from_payload(data["policy"]).items()}
        policy["FISCAL_EFFECT"] = replace(policy["FISCAL_EFFECT"], weight=1.0, direction="MINIMIZE", hard_minimum=0.5)
        candidates = tuple(replace(base, household_id=label, intervention_id=label,
                                   scores={**base.scores, "FISCAL_EFFECT": value})
                           for label, value in (("SCN:LOW", 0.2), ("SCN:HIGH", 0.8)))
        self.assertEqual([c.intervention_id for c in engine.mcda_order(candidates, policy)], ["SCN:HIGH"])

    def test_r2_missing_monetary_numerator_basis_preserves_signed_raw_but_stays_q(self):
        defs = (replace(self.defs[0], money_basis=None), self.defs[1])
        for value in (-12, 0, 12):
            with self.subTest(value=value):
                result = self.compare(candidate("A", self.f, defs, (value, 6)), definitions=defs, policy=policy(self.f, defs))
                trace = result.candidates[0]
                self.assertEqual(trace.metrics[0].raw_quantity, value)
                self.assertIn("MONETARY_BASIS_Q", trace.metrics[0].reasons)
                self.assertEqual((trace.status, trace.ratio.status, trace.ratio.value), ("UNRESOLVED", "NUMERATOR_Q", None))
                self.assertEqual(result.tie_groups, ())

    def test_r2_missing_public_denominator_basis_remains_q(self):
        defs = (self.defs[0], replace(self.defs[1], money_basis=None))
        result = self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        self.assertEqual(result.candidates[0].metrics[1].raw_quantity, 6)
        self.assertEqual(result.candidates[0].ratio.status, "DENOMINATOR_Q")
        self.assertEqual(result.unresolved_candidates, ("A",))

    def test_r2_currency_cannot_be_declared_nonmonetary(self):
        defs = (replace(self.defs[0], quantity_dimension="NONMONETARY", money_basis=None), self.defs[1])
        with self.assertRaisesRegex(BenefitContractError, "dimension mismatch"):
            self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))

    def test_r2_monetary_aliases_scalings_and_compounds_are_never_physical_units(self):
        # These are intentionally unsupported spellings, not a conversion test.
        aliases = ("Ft", "forint", "Hungarian forint", "huf", "HUF ", "HUF/year", "HUF/household", "HUF/kWh",
                   "HUF_HOUSEHOLD", "million HUF", "kWh*HUF", "HUF-equivalent", "EUR", "USD", "€", "$", "EUR/year")
        for unit in aliases:
            for dimension in ("NONMONETARY", "MONETARY", None):
                defs = (replace(self.defs[0], unit=unit, quantity_dimension=dimension, money_basis=None), self.defs[1])
                with self.subTest(unit=unit, dimension=dimension), self.assertRaisesRegex(BenefitContractError, "unsupported metric output unit"):
                    self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))

    def test_r2_signed_physical_numerator_remains_comparable_without_money_basis(self):
        defs = (replace(self.defs[0], unit="kWh", quantity_dimension="NONMONETARY", money_basis=None), self.defs[1])
        for value in (-12, 0, 12):
            result = self.compare(candidate("A", self.f, defs, (value, 6)), definitions=defs, policy=policy(self.f, defs))
            self.assertEqual(result.candidates[0].status, "COMPARABLE")
            self.assertEqual((result.candidates[0].ratio.value, result.candidates[0].ratio.unit), (Fraction(value, 6), "kWh/HUF"))
            self.assertIsNone(result.candidates[0].metrics[0].definition.money_basis)

    def test_r2_known_money_requires_every_compatible_basis_dimension(self):
        self.assertEqual(self.compare(self.c()).candidates[0].ratio.value, 2)
        for basis in (replace(MONEY, currency="EUR"), replace(MONEY, nominal_real="NOMINAL"),
                      replace(MONEY, price_date=date(2027, 1, 1)),
                      replace(MONEY, convention=Reference("SYNTHETIC_WITNESS", "SYNTHETIC_WITNESS:other-price-method", None, None))):
            defs = (replace(self.defs[0], money_basis=basis), self.defs[1])
            with self.subTest(basis=basis), self.assertRaises(BenefitContractError):
                self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        defs = (replace(self.defs[0], valuation_method="SCN:incompatible-valuation"), self.defs[1])
        with self.assertRaisesRegex(BenefitContractError, "methodology mismatch"):
            self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))

    def test_r2_removing_quantity_dimension_does_not_infer_applicability(self):
        for unit, basis in (("HUF", MONEY), ("HUF", None), ("kWh", None)):
            defs = (replace(self.defs[0], unit=unit, quantity_dimension=None, money_basis=basis), self.defs[1])
            result = self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
            self.assertEqual(result.candidates[0].metrics[0].raw_quantity, 12)
            self.assertEqual(result.unresolved_candidates, ("A",))
            self.assertIsNone(result.candidates[0].ratio.value)

    def test_r2_unknown_money_convention_and_incomplete_basis_never_default(self):
        qconvention = Reference("Q", None, "price convention unresolved", "SCN:qualification-needed")
        defs = (self.defs[0], replace(self.defs[1], money_basis=replace(MONEY, convention=qconvention)))
        # A known conflict between the two bases is rejected; using the same
        # explicitly unresolved basis cannot create a ready monetary result.
        with self.assertRaises(BenefitContractError):
            self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        defs = tuple(replace(d, money_basis=replace(MONEY, convention=qconvention)) for d in self.defs)
        result = self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        self.assertEqual(result.unresolved_candidates, ("A",))
        for field in ("currency", "nominal_real", "price_date", "convention"):
            defs = (replace(self.defs[0], money_basis=replace(MONEY, **{field: None})), self.defs[1])
            with self.subTest(field=field), self.assertRaises(BenefitContractError):
                self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))

    def test_r2_unsupported_physical_tokens_are_explicit_not_guessed(self):
        defs = (replace(self.defs[0], unit="custom-energy-units", quantity_dimension="NONMONETARY", money_basis=None), self.defs[1])
        with self.assertRaisesRegex(BenefitContractError, "unsupported metric output unit"):
            self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        defs = (replace(defs[0], unit=None), defs[1])
        result = self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))
        self.assertEqual(result.unresolved_candidates, ("A",))

    def test_r2_dimension_and_unit_labels_cannot_conflict_with_basis(self):
        for dimension, unit, basis in (("MONETARY", "kWh", None), ("NONMONETARY", "kWh", MONEY),
                                       ("UNSET_AS_PHYSICAL", "kWh", None)):
            defs = (replace(self.defs[0], quantity_dimension=dimension, unit=unit, money_basis=basis), self.defs[1])
            with self.subTest(dimension=dimension, unit=unit), self.assertRaises(BenefitContractError):
                self.compare(candidate("A", self.f, defs, (12, 6)), definitions=defs, policy=policy(self.f, defs))

    def native_transformation_witnesses(self):
        from test_b12_input_accounting_contract import case, scalar, ref
        from modules.B12.input_accounting_contract import Conversion
        valuation = replace(case().valuation, basis_id=MONEY.basis_id, valuation_date=date(2028, 1, 1),
                            discount_rate=scalar("0.05", "ratio", MONEY.basis_id),
                            nominal_rate=scalar("0.071", "ratio", MONEY.basis_id),
                            real_rate=scalar("0.05", "ratio", MONEY.basis_id),
                            inflation=scalar("0.02", "ratio", MONEY.basis_id),
                            time_convention=ref("time"), terminal_debt_treatment=ref("terminal"), escalation=ref("escalation"))
        conversion = Conversion(scalar(6, "EUR", "SCN:EUR"), scalar(12, "HUF", MONEY.basis_id),
                                scalar(2, "ratio", "SCN:factor"), date(2028, 1, 1), ref("conversion"))
        return valuation, conversion

    def compare_native_transformation(self, kind, binding, *, quantity=12, **context):
        transform = Transformation(kind, fingerprint("SCN:upstream-native-output"),
                                   "SCN:EUR" if kind == "CONVERSION" else "SCN:upstream-cash",
                                   MONEY.basis_id, self.f.valuation_method, binding, SCN)
        if kind == "CONVERSION":
            from test_b12_input_accounting_contract import ref
            transform = replace(transform, original_money_basis=MoneyBasis("SCN:EUR", "EUR", "REAL",
                                                                           date(2028, 1, 1), ref("EUR-basis")))
        transform = replace(transform, **context)
        return self.compare(remeasure(self.c(n=quantity), 0, transformations=(transform,))).candidates[0]

    def test_r3_complete_native_transformations_remain_comparable(self):
        valuation, conversion = self.native_transformation_witnesses()
        for kind, binding in (("VALUATION", valuation), ("CONVERSION", conversion)):
            result = self.compare_native_transformation(kind, binding)
            self.assertEqual((result.metrics[0].status, result.status, result.ratio.value), ("READY", "COMPARABLE", 2))
            self.assertIs(result.metrics[0].measurement.transformations[0].native_binding, binding)

    def test_r3_each_missing_native_valuation_field_rejects(self):
        valuation, _ = self.native_transformation_witnesses()
        for field in fields(valuation):
            with self.subTest(field=field.name), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("VALUATION", replace(valuation, **{field.name: None}))
        with self.assertRaises(BenefitContractError):
            self.compare_native_transformation("VALUATION", replace(valuation, discount_rate=None, nominal_rate=None,
                                               real_rate=None, inflation=None, time_convention=None,
                                               terminal_debt_treatment=None, escalation=None))

    def test_r3_native_valuation_requires_exact_date_and_reference_shapes(self):
        from datetime import datetime
        valuation, _ = self.native_transformation_witnesses()
        for field, value in (("valuation_date", "2028-01-01"), ("valuation_date", datetime(2028, 1, 1)),
                             ("time_convention", "ACT/365"), ("terminal_debt_treatment", {}),
                             ("escalation", False), ("discount_rate", Decimal("0.05"))):
            with self.subTest(field=field, value=value), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("VALUATION", replace(valuation, **{field: value}))

    def test_r3_each_native_rate_obeys_ratio_unit_and_greater_than_minus_one_domain(self):
        from test_b12_input_accounting_contract import scalar, unknown
        valuation, _ = self.native_transformation_witnesses()
        for field in ("discount_rate", "nominal_rate", "real_rate", "inflation"):
            for rate in (scalar("0.05", "kWh", MONEY.basis_id), scalar(-1, "ratio", MONEY.basis_id),
                         scalar(-2, "ratio", MONEY.basis_id), unknown("kWh", MONEY.basis_id)):
                with self.subTest(field=field, rate=rate), self.assertRaisesRegex(BenefitContractError, "rate unit/domain"):
                    self.compare_native_transformation("VALUATION", replace(valuation, **{field: rate}))
        for value in ("-0.999", "0", "0.05"):
            result = self.compare_native_transformation("VALUATION", replace(valuation, discount_rate=scalar(value, "ratio", MONEY.basis_id)))
            self.assertEqual(result.status, "COMPARABLE")

    def test_r3_discount_basis_and_known_fisher_identity_match_native_b12_rules(self):
        from test_b12_input_accounting_contract import case, scalar
        from modules.B12.input_accounting_contract import validate_case, B12ContractError
        valuation, _ = self.native_transformation_witnesses()
        original = case()
        for changed in (replace(valuation, discount_rate=scalar("0.05", "ratio", "SCN:other-basis")),
                        replace(valuation, nominal_rate=scalar("0.07", "ratio", MONEY.basis_id))):
            with self.assertRaises(B12ContractError):
                validate_case(replace(original, valuation=changed, other_bases=(MONEY,)))
            with self.assertRaises(BenefitContractError):
                self.compare_native_transformation("VALUATION", changed)
        native = validate_case(replace(original, valuation=valuation, other_bases=(MONEY,)))
        self.assertEqual(native.structural_status, "VALID")
        self.assertEqual(self.compare_native_transformation("VALUATION", valuation).status, "COMPARABLE")

    def test_r3_native_identity_checks_keep_b12_decimal_context(self):
        from test_b12_input_accounting_contract import scalar
        valuation, conversion = self.native_transformation_witnesses()
        with localcontext() as ctx:
            ctx.prec = 2
            self.assertEqual(self.compare_native_transformation("VALUATION", valuation).status, "COMPARABLE")
            self.assertEqual(self.compare_native_transformation("CONVERSION", conversion).status, "COMPARABLE")
            with self.assertRaisesRegex(BenefitContractError, "Fisher"):
                self.compare_native_transformation("VALUATION", replace(valuation, nominal_rate=scalar("0.07", "ratio", MONEY.basis_id)))

    def test_r3_every_properly_typed_valuation_unknown_remains_q(self):
        from test_b12_input_accounting_contract import unknown, qref
        valuation, _ = self.native_transformation_witnesses()
        replacements = {name: unknown("ratio", MONEY.basis_id) for name in ("discount_rate", "nominal_rate", "real_rate", "inflation")}
        replacements.update({name: qref(name) for name in ("time_convention", "terminal_debt_treatment", "escalation")})
        for field, value in replacements.items():
            with self.subTest(field=field):
                result = self.compare_native_transformation("VALUATION", replace(valuation, **{field: value}))
                self.assertEqual((result.metrics[0].raw_quantity, result.metrics[0].status, result.status), (12, "Q", "UNRESOLVED"))
                self.assertIn("UPSTREAM_B12_TRANSFORMATION_Q", result.metrics[0].reasons)
                self.assertIsNone(result.ratio.value)

    def test_r3_each_missing_conversion_field_rejects(self):
        _, conversion = self.native_transformation_witnesses()
        for field in fields(conversion):
            with self.subTest(field=field.name), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("CONVERSION", replace(conversion, **{field.name: None}))

    def test_r3_native_conversion_requires_date_factor_unit_domain_and_identity(self):
        from datetime import datetime
        from test_b12_input_accounting_contract import scalar
        _, conversion = self.native_transformation_witnesses()
        for changed in (replace(conversion, conversion_date="2028-01-01"),
                        replace(conversion, conversion_date=datetime(2028, 1, 1)),
                        replace(conversion, method="SCN:untyped-method"),
                        replace(conversion, multiplier=scalar(2, "kWh", "SCN:factor")),
                        replace(conversion, multiplier=scalar(0, "ratio", "SCN:factor")),
                        replace(conversion, multiplier=scalar(-2, "ratio", "SCN:factor")),
                        replace(conversion, multiplier=scalar(3, "ratio", "SCN:factor"))):
            with self.subTest(changed=changed), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("CONVERSION", changed)

    def test_r3_properly_typed_conversion_unknowns_remain_q(self):
        from test_b12_input_accounting_contract import unknown, qref
        _, conversion = self.native_transformation_witnesses()
        cases = (("method", qref("conversion"), 12), ("original", unknown("EUR", "SCN:EUR"), 12),
                 ("multiplier", unknown("ratio", "SCN:factor"), 12), ("converted", unknown("HUF", MONEY.basis_id), None))
        for field, value, quantity in cases:
            with self.subTest(field=field):
                result = self.compare_native_transformation("CONVERSION", replace(conversion, **{field: value}), quantity=quantity)
                self.assertEqual((result.metrics[0].status, result.status), ("Q", "UNRESOLVED"))
                self.assertIn("UPSTREAM_B12_TRANSFORMATION_Q", result.metrics[0].reasons)
                self.assertIsNone(result.ratio.value)

    def test_r3_native_nested_scalar_period_shape_is_validated(self):
        from copy import copy
        valuation, _ = self.native_transformation_witnesses()
        # Simulate decoded native objects whose constructor checks were bypassed.
        # Correct dataclass field types alone cannot validate their Q/period rules.
        bad_rate = copy(valuation.discount_rate)
        object.__setattr__(bad_rate, "truth", "Q")  # Q may not retain a number.
        bad_reference = copy(valuation.time_convention)
        object.__setattr__(bad_reference, "ref", None)  # Resolved reference needs a ref.
        bad_period = copy(valuation.discount_rate.reference_period)
        object.__setattr__(bad_period, "start", date(2027, 1, 1))
        period_rate = copy(valuation.discount_rate)
        object.__setattr__(period_rate, "reference_period", bad_period)
        for changed in (replace(valuation, discount_rate=bad_rate), replace(valuation, time_convention=bad_reference),
                        replace(valuation, discount_rate=period_rate),
                        replace(valuation, discount_rate={"value": "0.05", "unit": "ratio"})):
            with self.subTest(changed=changed), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("VALUATION", changed)

    def test_r4_physical_originals_cannot_become_money_through_ratio_multiplier(self):
        _, conversion = self.native_transformation_witnesses()
        for unit in ("kWh", "GJ", "ratio", "person"):
            changed = replace(conversion, original=replace(conversion.original, unit=unit))
            with self.subTest(unit=unit), self.assertRaisesRegex(BenefitContractError, "original currency"):
                self.compare_native_transformation("CONVERSION", changed)

    def test_r4_original_basis_identity_and_currency_must_match_explicit_context(self):
        from test_b12_input_accounting_contract import ref
        _, conversion = self.native_transformation_witnesses()
        source = MoneyBasis("SCN:EUR", "EUR", "REAL", date(2028, 1, 1), ref("EUR-basis"))
        for changed in (replace(source, basis_id="SCN:other-source-basis"), replace(source, currency="USD")):
            with self.subTest(changed=changed), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("CONVERSION", conversion, original_money_basis=changed)
        with self.assertRaises(BenefitContractError):
            self.compare_native_transformation("CONVERSION", replace(conversion, original=replace(conversion.original, basis_id="SCN:other")))

    def test_r4_absent_original_context_preserves_raw_value_but_is_q(self):
        _, conversion = self.native_transformation_witnesses()
        result = self.compare_native_transformation("CONVERSION", conversion, original_money_basis=None)
        self.assertEqual((result.metrics[0].raw_quantity, result.metrics[0].status, result.status), (12, "Q", "UNRESOLVED"))
        self.assertIn("CONVERSION_ORIGINAL_MONEY_BASIS_Q", result.metrics[0].reasons)
        self.assertIsNone(result.ratio.value)
        self.assertEqual(result.metrics[0].measurement.native_status, "READY")

    def test_r4_typed_unknown_original_convention_and_native_fields_remain_q(self):
        from test_b12_input_accounting_contract import qref, ref, unknown
        _, conversion = self.native_transformation_witnesses()
        source = MoneyBasis("SCN:EUR", "EUR", "REAL", date(2028, 1, 1), qref("original-money-convention"))
        result = self.compare_native_transformation("CONVERSION", conversion, original_money_basis=source)
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertIn("CONVERSION_ORIGINAL_MONEY_BASIS_Q", result.metrics[0].reasons)
        qualified = replace(source, convention=ref("original-money-convention"))
        for changed in (replace(conversion, original=unknown("EUR", "SCN:EUR")),
                        replace(conversion, multiplier=unknown("ratio", "SCN:factor")),
                        replace(conversion, method=qref("conversion-method"))):
            with self.subTest(changed=changed):
                self.assertEqual(self.compare_native_transformation("CONVERSION", changed, original_money_basis=qualified).status, "UNRESOLVED")
        with self.assertRaises(BenefitContractError):
            self.compare_native_transformation("CONVERSION", conversion, original_money_basis=replace(source, currency="USD"))

    def test_r4_original_money_context_uses_native_required_shape_and_basis_rules(self):
        from test_b12_input_accounting_contract import ref
        _, conversion = self.native_transformation_witnesses()
        source = MoneyBasis("SCN:EUR", "EUR", "REAL", date(2028, 1, 1), ref("EUR-basis"))
        for field in fields(source):
            with self.subTest(field=field.name), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("CONVERSION", conversion, original_money_basis=replace(source, **{field.name: None}))
        for changed in (replace(source, nominal_real="UNSPECIFIED"), replace(source, price_date="2028-01-01"),
                        {"basis_id": "SCN:EUR", "currency": "EUR"}):
            with self.subTest(changed=changed), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("CONVERSION", conversion, original_money_basis=changed)

    def test_r4_qualified_source_currency_never_comes_from_basis_id_spelling(self):
        from test_b12_input_accounting_contract import ref
        _, conversion = self.native_transformation_witnesses()
        for identity, currency in (("opaque-source-7", "EUR"), ("SCN:EUR", "USD"), ("mentions-kWh", "EUR")):
            source = MoneyBasis(identity, currency, "REAL", date(2028, 1, 1), ref("explicit-source-currency"))
            changed = replace(conversion, original=replace(conversion.original, unit=currency, basis_id=identity))
            result = self.compare_native_transformation("CONVERSION", changed, original_basis=identity, original_money_basis=source)
            self.assertEqual((result.status, result.ratio.value), ("COMPARABLE", 2))
            self.assertIs(result.metrics[0].measurement.transformations[0].original_money_basis, source)

    def test_r4_qualified_deflator_and_signed_monetary_outputs_remain_valid(self):
        from test_b12_input_accounting_contract import ref, scalar
        _, conversion = self.native_transformation_witnesses()
        source = MoneyBasis("SCN:earlier-HUF", "HUF", "NOMINAL", date(2026, 1, 1), ref("earlier-HUF-basis"))
        for original, converted in ((-6, -12), (0, 0), (6, 12)):
            changed = replace(conversion, original=scalar(original, "HUF", source.basis_id), converted=scalar(converted, "HUF", MONEY.basis_id))
            result = self.compare_native_transformation("CONVERSION", changed, quantity=converted,
                                                        original_basis=source.basis_id, original_money_basis=source)
            self.assertEqual((result.status, result.ratio.value), ("COMPARABLE", Fraction(converted, 6)))

    def test_r4_qualified_source_cannot_hide_known_target_conflicts(self):
        _, conversion = self.native_transformation_witnesses()
        for changed in (replace(conversion, converted=replace(conversion.converted, unit="EUR")),
                        replace(conversion, converted=replace(conversion.converted, basis_id="SCN:other-target"))):
            with self.subTest(changed=changed), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("CONVERSION", changed)

    def test_r4_missing_target_context_is_q_and_physical_numerators_need_no_case(self):
        from test_b12_input_accounting_contract import ref
        _, conversion = self.native_transformation_witnesses()
        source = MoneyBasis("SCN:EUR", "EUR", "REAL", date(2028, 1, 1), ref("EUR-basis"))
        transform = Transformation("CONVERSION", fingerprint("SCN:original"), source.basis_id, MONEY.basis_id,
                                   self.f.valuation_method, conversion, SCN, source)
        defs = (replace(self.defs[0], money_basis=None), self.defs[1])
        c = remeasure(candidate("A", self.f, defs, (12, 6)), 0, transformations=(transform,))
        result = self.compare(c, definitions=defs, policy=policy(self.f, defs)).candidates[0]
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertIn("UPSTREAM_TARGET_MONEY_BASIS_Q", result.metrics[0].reasons)
        defs = (replace(self.defs[0], quantity_dimension="NONMONETARY", unit="kWh", money_basis=None), self.defs[1])
        result = self.compare(candidate("A", self.f, defs, (-12, 6)), definitions=defs, policy=policy(self.f, defs)).candidates[0]
        self.assertEqual((result.status, result.ratio.value), ("COMPARABLE", -2))
        self.assertEqual(result.metrics[0].measurement.transformations, ())

    def test_r4_native_b12_original_currency_rule_agrees_with_bounded_consumer(self):
        from test_b12_input_accounting_contract import case, ref, scalar
        from modules.B12.input_accounting_contract import Conversion, validate_case, B12ContractError
        native = case()
        source = MoneyBasis("SCN:EUR", "EUR", "NOMINAL", date(2026, 1, 1), ref("EUR-basis"))
        conversion = Conversion(scalar(6, "EUR", source.basis_id), scalar(12, "HUF", native.monetary_basis.basis_id),
                                scalar(2, "ratio", "SCN:factor"), date(2026, 1, 1), ref("conversion"))
        self.assertEqual(validate_case(replace(native, other_bases=(source,), conversions=(conversion,))).structural_status, "VALID")
        _, bounded = self.native_transformation_witnesses()
        for unit in ("kWh", "GJ", "ratio", "person"):
            with self.subTest(unit=unit), self.assertRaises(B12ContractError):
                validate_case(replace(native, other_bases=(source,), conversions=(replace(conversion, original=replace(conversion.original, unit=unit)),)))
            with self.subTest(unit=unit), self.assertRaises(BenefitContractError):
                self.compare_native_transformation("CONVERSION", replace(bounded, original=replace(bounded.original, unit=unit)))

    def test_r4_one_basis_identity_cannot_refer_to_conflicting_money_contexts(self):
        from test_b12_input_accounting_contract import ref, qref
        _, conversion = self.native_transformation_witnesses()
        # Both ends may use one declared basis, but that ID cannot name two
        # incompatible currencies, vintages or nominal/real conventions.
        changed = replace(conversion, original=replace(conversion.original, unit="HUF", basis_id=MONEY.basis_id))
        self.assertEqual(self.compare_native_transformation("CONVERSION", changed,
                         original_basis=MONEY.basis_id, original_money_basis=MONEY).status, "COMPARABLE")
        for source in (replace(MONEY, currency="EUR"), replace(MONEY, nominal_real="NOMINAL"),
                       replace(MONEY, price_date=date(2027, 1, 1)), replace(MONEY, convention=ref("other-money-convention"))):
            native = replace(changed, original=replace(changed.original, unit=source.currency))
            with self.subTest(source=source), self.assertRaisesRegex(BenefitContractError, "reuse one basis identity"):
                self.compare_native_transformation("CONVERSION", native, original_basis=MONEY.basis_id, original_money_basis=source)
        result = self.compare_native_transformation("CONVERSION", changed, original_basis=MONEY.basis_id,
                                                    original_money_basis=replace(MONEY, convention=qref("source-convention")))
        self.assertEqual(result.status, "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
