"""Twenty reviewed acceptance groups. Every convenience value is SCN fixture data."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from modules.B07 import shared_use_schedule_contract as shared
from modules.B07.engine import BatterySpec, BatteryEngine
from modules.B07 import discharge_equivalent_reference as native

# Reuse exact existing downstream fixture builders; no new bridge/evidence producer.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_b10_p10_managed_flex_survivability as b10_fixture
import test_b01_benefit_metric_contract as b01_fixture
from modules.B10.managed_flex_survivability_contract import build_managed_node_load, PHYSICAL_FLEX_CAPABILITY, FLEX_ACTIVATION

T0 = datetime(2028, 1, 1, tzinfo=timezone.utc)
H, S = "SCN:household", "SCN:state"
SERVICE = "SCN:declared-service"
Q = shared.Unknown("Q:claim-specific qualification required")


def known(value): return shared.Term("SCN", value, "SCN:explicit-test-value")
def unknown(): return shared.Term("Q", None, "Q:obtain-term")
def na(): return shared.Term("NOT_APPLICABLE", None, "SCN:explicit-inapplicability")
def qualified(): return shared.Term("SCN", None, "SCN:independently-declared-comparison")
def stamp(hours): return (T0+timedelta(hours=hours)).isoformat()


def seal(value):
    return replace(value, content_sha256=shared.content_digest(value))


def allocation(actor, charge, discharge, hours, eta, *, debit=None, credit=None, cycle=0., charge_loss=None):
    acin, acout = charge*hours, discharge*hours
    credit = acin*eta if credit is None else credit
    debit = acout/eta if debit is None else debit
    return shared.Allocation(actor, "HOUSEHOLD_SELF_USE" if actor == H else SERVICE,
                             acin, acout, credit, debit,
                             acin-credit-cycle if charge_loss is None else charge_loss,
                             cycle, debit-acout)


def agreement(identity, end, *, mode=shared.ACCESS, protected=0., budget=100., duration=100., power=100., energy=100., replenishment="NONE"):
    budgets = tuple(shared.Budget("budget:"+actor, actor, stamp(0), stamp(end), known(budget), replenishment) for actor in (H, S))
    rights = tuple(shared.RightsWindow("right:"+actor, actor, stamp(0), stamp(end), stamp(0), stamp(end),
                  known(power), known(power), known(energy), known(duration), "budget:"+actor) for actor in (H, S))
    return seal(shared.Agreement("SCN:agreement", "1", "", shared.digest(identity), mode,
        known(protected) if mode == shared.PROTECTED else na(), na(), budgets, rights, (), qualified()))


def make_case(actual=((0., 1., 0., 2.),), baseline=None, *, hours=None, admissions=None,
              baseline_admissions=None, x=8., eta=.9, power=5., scope=shared.ACTIVATION,
              mode=shared.ACCESS, protected=0., executor=None, loads=(2., 0., 0.)):
    actual = tuple(actual)
    baseline = tuple((0., 0., 0., 0.) for _ in actual) if baseline is None else tuple(baseline)
    hours = tuple(1. for _ in actual) if hours is None else tuple(hours)
    admissions = actual if admissions is None else admissions
    baseline_admissions = baseline if baseline_admissions is None else baseline_admissions
    if executor is None:
        executor = BatterySpec(10., 10., 0., 1., power, power, eta, eta, hours[0], status="SCN")
    ref = type(executor) is native.Reference
    identity = shared.Identity("SCN:device", "SCN:connection", H, S, shared.REFERENCE if ref else shared.STORED,
            "DC_DISCHARGE_EQUIVALENT_CAPACITY_KWH" if ref else "STORED_USABLE_CAPACITY_KWH",
            executor.capacity_dc_output_equiv_kwh if ref else executor.usable_capacity_kwh, shared.digest(executor))
    g = agreement(identity, sum(hours), mode=mode, protected=protected)
    def leg(name, commands, admitted, contract):
        intervals = []
        elapsed = 0.
        for n, (command, actual_flow, dt) in enumerate(zip(commands, admitted, hours)):
            hc, hd, sc, sd = command
            ahc, ahd, asc, asd = actual_flow
            requests = (shared.Request(H, "HOUSEHOLD_SELF_USE", hc, hd), shared.Request(S, SERVICE, sc, sd))
            allocations = (allocation(H, ahc, ahd, dt, eta), allocation(S, asc, asd, dt, eta))
            intervals.append(shared.Interval(str(n), name+":event:"+str(n), shared.digest(identity),
                    stamp(elapsed), stamp(elapsed+dt), dt, loads, requests, allocations))
            elapsed += dt
        return shared.Leg(name, shared.digest(identity), x, contract, tuple(intervals), Q)
    b = leg("baseline", baseline, baseline_admissions, g if scope == shared.ACTIVATION else "HOUSEHOLD_ONLY")
    a = leg("actual", actual, admissions, g)
    descriptor = shared.Baseline("SCN:baseline", "SCN:matched-exogenous-schedules", "SCN:declared-"+scope,
                                 "1", scope, shared.digest(b), qualified())
    case = shared.SharedUseCase("SCN:shared-case", shared.VERSION, "", "SCN", identity, executor,
        tuple(native.PINS.items()) if ref else (), "SCN:complete-test-fixture",
        "NOT_APPLICABLE_REFERENCE_IDLE_Q" if ref else "CONDITIONAL_OMITTED_STANDING_LOSS", scope, SERVICE,
        descriptor, b, a, known(100.), known(100.), tuple(shared.Permission(op, "Q", "Q:actual-site-term") for op in shared.OPERATIONS),
        shared.FinancialInputs(tuple((k, unknown()) for k in shared.MONEY_FIELDS), Q), (), "SERVICE_ONLY", 1e-9, 1e-12)
    return seal(case)


def update_leg(case, name="actual", **changes):
    key = name+"_leg"
    leg = replace(getattr(case, key), **changes)
    case = replace(case, **{key: leg})
    if name == "baseline": case = replace(case, baseline=replace(case.baseline, leg_sha256=shared.digest(leg)))
    return seal(case)


def update_interval(case, n=0, name="actual", **changes):
    rows = list(getattr(case, name+"_leg").intervals)
    rows[n] = replace(rows[n], **changes)
    return update_leg(case, name, intervals=tuple(rows))


def update_agreement(case, **changes):
    g = seal(replace(case.actual_leg.agreement, **changes))
    case = update_leg(case, agreement=g)
    if case.scope == shared.ACTIVATION: case = update_leg(case, "baseline", agreement=g)
    return case


def ref_allocations(case, leg_name="actual"):
    """Explicit fixture-only accounting allocation at the single native point."""
    leg = getattr(case, leg_name+"_leg")
    state = native.Inventory(leg.initial_inventory_kwh)
    intervals = []
    for i in leg.intervals:
        charge = sum(r.charge_ac_kw for r in i.requests)
        discharge = sum(r.discharge_ac_kw for r in i.requests)
        r = native.step(case.executor, state, charge_ac_kw=charge, discharge_ac_kw=discharge, hours=i.hours)
        state = native.Inventory(r['x_end_kwh'], r['reason'])
        allocations = []
        if r['admitted_charge_ac_kwh'] is None:
            intervals.append(replace(i, allocations=Q)); continue
        for request in i.requests:
            fraction = ((request.charge_ac_kw+request.discharge_ac_kw)/(charge+discharge)) if charge+discharge else 0.
            acin = r['admitted_charge_ac_kwh']*fraction
            acout = r['delivered_discharge_ac_kwh']*fraction
            dc = r['admitted_charge_dc_kwh']*fraction
            debit = r['admitted_discharge_dc_kwh']*fraction
            allocations.append(allocation(request.actor_id, acin/i.hours, acout/i.hours, i.hours, 1.,
                debit=debit, credit=dc*case.executor.battery_dc_cycle_efficiency,
                cycle=(1-case.executor.battery_dc_cycle_efficiency)*dc, charge_loss=acin-dc))
        intervals.append(replace(i, allocations=tuple(allocations)))
    return update_leg(case, leg_name, intervals=tuple(intervals))


class SharedUseTests(unittest.TestCase):
    def actual(self, case): return shared.evaluate_shared_use(case)["legs"]["actual"]

    def test_g01_unconflicted_one_device_and_actor_conservation(self):
        case = make_case()
        original = BatteryEngine.step
        calls = []
        def observed(engine, *args, **kwargs):
            calls.append(args)
            return original(engine, *args, **kwargs)
        with patch.object(BatteryEngine, "step", observed): result = self.actual(case)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["allocation_status"], "PASS_SCN")
        self.assertAlmostEqual(result["totals"]["inventory_debit_kwh"], 3/.9)
        self.assertAlmostEqual(result["totals"]["discharge_converter_loss_kwh"], 3/.9-3)
        self.assertEqual(result["totals"]["discharge_ac_kwh"], 3.)

    def test_g01_duplicate_actor_service_and_double_claim_fail(self):
        c = make_case()
        allocations = c.actual_leg.intervals[0].allocations
        with self.assertRaisesRegex(ValueError, "duplicate actor allocation"):
            self.actual(update_interval(c, allocations=allocations+(replace(allocations[0], service_id="second-service"),)))
        bad = (allocation(H, 0, 1, 1, .9), allocation(S, 0, 3, 1, .9))
        self.assertEqual(self.actual(update_interval(c, allocations=bad))["allocation_status"], "FAIL")

    def test_g02_overbooked_power_explicit_shortage(self):
        c = make_case(actual=((0, 4, 0, 4),), admissions=((0, 1, 0, 4),))
        a = self.actual(c)
        self.assertEqual(a["totals"]["discharge_ac_kwh"], 5)
        self.assertEqual(a["rows"][0]["unserved_discharge_kwh"], 3)
        self.assertEqual(a["rows"][0]["allocation"]["actors"][H]["allocation"]["unserved_discharge_kwh"], 3)
        self.assertEqual(self.actual(update_interval(c, allocations=Q))["allocation_status"], "Q")
        self.assertEqual(self.actual(make_case(actual=((0, 4, 0, 4),)))["allocation_status"], "FAIL")

    def test_g03_energy_exhaustion_is_not_power_availability(self):
        c = make_case(actual=((0, 0, 0, 4),), admissions=((0, 0, 0, 1.8),), x=2.)
        a = self.actual(c)
        self.assertAlmostEqual(a["totals"]["discharge_ac_kwh"], 1.8)
        self.assertEqual(a["terminal_inventory_kwh"], 0)
        self.assertAlmostEqual(a["rows"][0]["unserved_discharge_kwh"], 2.2)
        self.assertEqual(a["allocation_status"], "PASS_SCN")

    def test_g04_independent_power_energy_duration_service_window(self):
        base = make_case(actual=((0, 0, 0, 2),), eta=1.)
        g = base.actual_leg.agreement
        for field, value in (("discharge_ac_kw", known(1)), ("draw_kwh", known(1)), ("callable_hours", known(.5))):
            rights = (g.rights[0], replace(g.rights[1], **{field: value}))
            with self.subTest(field=field): self.assertEqual(self.actual(update_agreement(base, rights=rights))["rights"]["status"], "FAIL")
        c = make_case(actual=((0, 0, 0, 1), (0, 0, 0, 1)), eta=1.)
        rights = tuple(replace(r, callable_hours=known(1)) for r in c.actual_leg.agreement.rights)
        self.assertEqual(self.actual(update_agreement(c, rights=rights))["rights"]["status"], "FAIL")
        rights = tuple(replace(r, service_end=stamp(1)) for r in c.actual_leg.agreement.rights)
        self.assertIn(S+":OUTSIDE_SERVICE_WINDOW", self.actual(update_agreement(c, rights=rights))["rights"]["failures"])

    def test_g05_opposing_before_netting_and_explicit_subintervals(self):
        with self.assertRaisesRegex(ValueError, "opposing"):
            self.actual(make_case(actual=((2, 0, 0, 1),)))
        c = make_case(actual=((2, 0, 0, 0), (0, 0, 0, 1)), hours=(.5, .5), x=2.)
        a = self.actual(c)
        self.assertAlmostEqual(a["terminal_inventory_kwh"], 2+.9-.5/.9)
        self.assertEqual(a["allocation_status"], "PASS_SCN")
        self.assertAlmostEqual(a["native"]["state"]["charged_energy_kwh"], 1)
        self.assertAlmostEqual(a["native"]["state"]["discharged_energy_kwh"], .5)

    def test_g06_nonlinear_reference_once_and_clipped_efficiency(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        for x in (7., .6):
            c = make_case(actual=((0, 1, 0, 2),), baseline=((0, 1, 0, 0),), hours=(.25,), x=x, executor=ref)
            c = ref_allocations(ref_allocations(c), "baseline")
            with patch.object(native, "step", wraps=native.step) as step:
                a = self.actual(c)
                self.assertEqual(step.call_count, 2)
            self.assertEqual(a["allocation_status"], "PASS_SCN")
            row = a["rows"][0]
            if x == 7.:
                self.assertAlmostEqual(row["inventory_debit_kwh"], .7619779345720935)
                self.assertNotAlmostEqual(row["inventory_debit_kwh"], .762991458932329, places=8)
            else:
                self.assertLess(row["discharge_ac_kwh"], .75)
                self.assertAlmostEqual(row["discharge_ac_kwh"]/row["inventory_debit_kwh"], row["native"]["post_clipping_conversion_efficiency"])
            self.assertEqual(a["native"]["applicability_evidence_tier"], "E2")

    def test_g06_reference_charge_keeps_three_loss_components(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        c = make_case(actual=((1, 0, 2, 0),), baseline=((1, 0, 0, 0),), hours=(.25,), x=2., executor=ref)
        a = self.actual(ref_allocations(ref_allocations(c), "baseline"))
        self.assertEqual(a["allocation_status"], "PASS_SCN")
        totals = a["totals"]
        self.assertGreater(totals["charge_converter_loss_kwh"], 0)
        self.assertGreater(totals["cycle_bookkeeping_loss_kwh"], 0)
        self.assertEqual(totals["discharge_converter_loss_kwh"], 0)
        self.assertAlmostEqual(totals["charge_ac_kwh"], totals["inventory_credit_kwh"]+totals["charge_converter_loss_kwh"]+totals["cycle_bookkeeping_loss_kwh"])

    def test_g07_access_vs_pool_and_unmet_target(self):
        c = make_case(actual=((0, 3, 0, 0), (0, 0, 0, 0)), eta=1., x=5.)
        rights = (c.actual_leg.agreement.rights[0], replace(c.actual_leg.agreement.rights[1], draw_kwh=known(4)))
        a = self.actual(update_agreement(c, rights=rights))
        self.assertEqual(a["rights"]["intervals"][1]["actors"][S]["available_before_kwh"], 2.)
        p = make_case(actual=((0, 3, 0, 0),), eta=1., x=5., mode=shared.PROTECTED, protected=4.)
        self.assertIn("PROTECTED_POOL_BORROWING_OR_SHORTAGE", self.actual(p)["rights"]["failures"])
        p = make_case(actual=((0, 0, 0, 0),), eta=1., x=2., mode=shared.PROTECTED, protected=4.)
        self.assertIn("INITIAL_PROTECTED_TARGET_UNMET", self.actual(p)["rights"]["failures"])

    def test_g08_pool_transfers_recharge_and_budget_are_separate(self):
        c = make_case(actual=((0, 0, 0, 1), (0, 0, 1, 0), (0, 0, 0, 1)),
                      eta=1., x=5., mode=shared.PROTECTED, protected=2., scope=shared.AGREEMENT)
        g = c.actual_leg.agreement
        budgets = (g.budgets[0], replace(g.budgets[1], draw_kwh=known(1)))
        transfers = (shared.Transfer("reserve", stamp(1), "FREE_TO_PROTECTED", 1.),
                     shared.Transfer("release", stamp(2), "PROTECTED_TO_FREE", 1.))
        c = update_agreement(c, budgets=budgets, transfers=transfers)
        a = self.actual(c)
        self.assertEqual(a["rights"]["remaining_budgets_kwh"]["budget:"+S], -1)
        self.assertIn(S+":DRAW_BUDGET_EXCEEDED", a["rights"]["failures"])
        self.assertEqual(a["rights"]["terminal_protected_free_kwh"], (1., 3.))
        for row, physical in zip(a["rights"]["intervals"], a["rows"]):
            self.assertAlmostEqual(sum(row["protected_free_after_kwh"]), physical["inventory_after_kwh"])
        replenished = (budgets[0], replace(budgets[1], replenishment="ATTRIBUTED_CHARGE_CREDIT"))
        self.assertEqual(self.actual(update_agreement(c, budgets=replenished))["rights"]["status"], "PASS_SCN")

    def test_g08_split_alias_overlap_and_future_transfer_fail(self):
        c = make_case(actual=((0, 0, 1, 0), (0, 0, 0, 0)), eta=1., x=1., mode=shared.PROTECTED, protected=1., scope=shared.AGREEMENT)
        g = c.actual_leg.agreement
        for budgets in (g.budgets+(replace(g.budgets[1], budget_id="alias"),),
                        g.budgets+(replace(g.budgets[1], budget_id="split", start=stamp(1)),)):
            with self.subTest(budgets=budgets), self.assertRaises(ValueError): self.actual(update_agreement(c, budgets=budgets))
        with self.assertRaisesRegex(ValueError, "overlapping"):
            self.actual(update_agreement(c, rights=g.rights+(replace(g.rights[1], right_id="double"),)))
        transfer = shared.Transfer("future", stamp(0), "FREE_TO_PROTECTED", 1.)
        self.assertIn("TRANSFER_SOURCE_SHORTAGE", self.actual(update_agreement(c, transfers=(transfer,)))["rights"]["failures"])
        with self.assertRaisesRegex(ValueError, "same-instant"):
            self.actual(update_agreement(c, transfers=(transfer, replace(transfer, event_id="return", direction="PROTECTED_TO_FREE"))))

    def test_g09_dynamic_depletion_and_window_expiry(self):
        c = make_case(actual=((0, 0, 0, 2), (0, 0, 0, 2)), admissions=((0, 0, 0, 2), (0, 0, 0, 0)), eta=1., x=2.)
        a = self.actual(c)
        self.assertEqual(a["rows"][1]["unserved_discharge_kwh"], 2)
        self.assertEqual(a["rights"]["intervals"][1]["actors"][S]["available_before_kwh"], 0)
        self.assertEqual(a["rows"][1]["allocation"]["actors"][S]["allocation"]["unserved_full_power_equivalent_hours"], 1)
        self.assertEqual(a["rows"][1]["allocation"]["actors"][S]["allocation"]["admitted_active_hours"], 0)
        self.assertEqual(a["rights"]["intervals"][1]["actors"][S]["callable_hours_after"], 99.)
        g = c.actual_leg.agreement
        rights = tuple(replace(r, end=stamp(1), service_end=stamp(1)) for r in g.rights)
        self.assertIn(S+":OUTSIDE_RIGHTS_WINDOW", self.actual(update_agreement(c, rights=rights))["rights"]["failures"])

    def test_g10_reduced_charge_is_response_without_discharge(self):
        c = make_case(actual=((1, 0, 0, 0),), baseline=((3, 0, 0, 0),), x=1.)
        result = shared.evaluate_shared_use(c)
        self.assertEqual(result["response"]["energy_kwh"], 2)
        self.assertEqual(result["legs"]["actual"]["totals"]["inventory_debit_kwh"], 0)
        self.assertAlmostEqual(result["response"]["actual_minus_baseline_terminal_kwh"], -1.8)

    def test_g11_activation_retains_reservation(self):
        c = make_case(actual=((0, 1, 0, 1),), baseline=((0, 1, 0, 0),), eta=1., x=5., mode=shared.PROTECTED, protected=4.)
        result = shared.evaluate_shared_use(c)
        self.assertEqual(result["response"]["energy_kwh"], 1)
        self.assertEqual(result["legs"]["actual"]["rights"]["terminal_protected_free_kwh"], (3., 0.))
        r = c.baseline_leg.intervals[0].requests
        with self.assertRaisesRegex(ValueError, "baseline cannot"):
            shared.evaluate_shared_use(update_interval(c, name="baseline", requests=(r[0], replace(r[1], discharge_ac_kw=1))))
        with self.assertRaisesRegex(ValueError, "exact reservation"):
            shared.evaluate_shared_use(update_leg(c, "baseline", agreement=seal(replace(c.baseline_leg.agreement, initial_protected_kwh=known(3)))))

    def test_g12_agreement_foregone_use_without_activation(self):
        c = make_case(actual=((0, 1, 0, 0),), baseline=((0, 2, 0, 0),), eta=1., x=5., mode=shared.PROTECTED, protected=4., scope=shared.AGREEMENT)
        r = shared.evaluate_shared_use(c)
        self.assertEqual(r["response"]["energy_kwh"], -1)
        self.assertEqual(r["response"]["foregone_household_discharge_kwh"], 1)
        self.assertEqual(r["financial"]["complete_household_protection_status"], "Q")
        self.assertIsNone(r["financial"]["monetary_result"])

    def test_g13_scope_hash_and_meaning_cannot_be_reused(self):
        c = make_case()
        claim = shared.ResponseClaim(c.scope, shared.comparison_digest(c), shared.digest(c.baseline), "CONDITIONAL_TOTAL_CONNECTION_RESPONSE", "SCN", False)
        self.assertEqual(shared.evaluate_shared_use(seal(replace(c, response_claims=(claim,))))["input_status"], "PASS_SCN")
        for bad in (replace(claim, scope=shared.AGREEMENT), replace(claim, comparison_sha256="0"*64), replace(claim, baseline_sha256="0"*64)):
            with self.subTest(bad=bad), self.assertRaises(ValueError): shared.evaluate_shared_use(seal(replace(c, response_claims=(bad,))))
        with self.assertRaises(ValueError): shared.evaluate_shared_use(seal(replace(c, baseline=replace(c.baseline, scope=shared.AGREEMENT))))

    def test_g14_rebound_terminal_stock_and_truncation(self):
        full = make_case(actual=((0, 0, 0, .9), (0, 0, 1/.9, 0)), x=4.)
        full = seal(replace(full, horizon_completeness="SUPPLIED_REBOUND_HORIZON"))
        result = shared.evaluate_shared_use(full)
        self.assertAlmostEqual(result["legs"]["actual"]["terminal_inventory_kwh"], 4.)
        self.assertAlmostEqual(result["response"]["records"][0]["response_up_kwh"], .9)
        self.assertAlmostEqual(result["response"]["records"][1]["response_up_kwh"], -1/.9)
        self.assertLess(result["response"]["energy_kwh"], 0)
        truncated = shared.evaluate_shared_use(make_case(actual=((0, 0, 0, .9),), x=4.))
        self.assertAlmostEqual(truncated["response"]["actual_minus_baseline_terminal_kwh"], -1)
        self.assertFalse(truncated["inventory_rebound"]["automatic_recharge"])
        self.assertEqual(truncated["inventory_rebound"]["cycle_adjusted_benefit_status"], "Q")

    def test_g15_reference_idle_unknown_continuity_and_E2_proxy(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, 1)), hours=(2., .25), x=3., executor=ref, mode=shared.PROTECTED, protected=2.)
        c = ref_allocations(ref_allocations(c), "baseline")
        idle = shared.IdleAccounting(("0",), 2., ((H, .00407), (S, .00407)), False)
        c = update_leg(c, idle_accounting=idle)
        a = self.actual(c)
        self.assertIsNone(a["terminal_inventory_kwh"])
        self.assertEqual([r["native"]["status"] for r in a["rows"]], ["Q_IDLE_INVENTORY", "Q_PREVIOUS_INVENTORY"])
        self.assertEqual(a["rights"]["terminal_protected_free_kwh"], (None, None))
        self.assertAlmostEqual(a["idle_ac"]["ac_energy_debit_kwh"], .00814)
        self.assertEqual(a["idle_ac"]["evidence_tier"], "E2")
        self.assertIsNone(a["idle_ac"]["dc_inventory_drain_kwh"])
        self.assertEqual(a["idle_ac"]["actor_allocation_status"], "PASS_SCN")
        with self.assertRaises(TypeError): replace(c.actual_leg.intervals[1], initial_inventory_kwh=3.)

    def test_g15_idle_double_count_and_wrong_exposure_rejected(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        c = make_case(actual=((0, 0, 0, 0),), hours=(2.,), x=0., executor=ref)
        c = ref_allocations(ref_allocations(c), "baseline")
        idle = shared.IdleAccounting(("0",), 2., Q, True)
        with self.assertRaisesRegex(ValueError, "double count"): self.actual(update_leg(c, idle_accounting=idle))
        self.assertAlmostEqual(self.actual(update_leg(c, idle_accounting=replace(idle, include_native_empty_component=False)))["idle_ac"]["ac_energy_debit_kwh"], .00814)
        with self.assertRaisesRegex(ValueError, "duration"): self.actual(update_leg(c, idle_accounting=replace(idle, idle_hours=3.)))

    def test_g16_physics_survives_unknown_permission_and_known_exclusion(self):
        c = make_case()
        r = shared.evaluate_shared_use(c)
        self.assertEqual(r["legs"]["actual"]["physical_status"], "PASS_SCN")
        self.assertEqual(r["legs"]["actual"]["rights"]["status"], "PASS_SCN")
        self.assertTrue(all(v["status"] == "Q" for v in r["actual_permissions"].values()))
        c = seal(replace(c, permissions=tuple(replace(p, status="FAIL", reference="SCN:known-exclusion") if p.operation == "EXPORT" else p for p in c.permissions)))
        self.assertEqual(shared.evaluate_shared_use(c)["actual_permissions"]["EXPORT"]["status"], "FAIL")
        self.assertFalse(shared.evaluate_shared_use(c)["actual_execution_admitted"])
        self.assertEqual(self.actual(c)["physical_status"], "PASS_SCN")

    def test_g17_raw_connection_conservation_and_unknown_envelope(self):
        c = make_case(actual=((0, 1, 0, 2),), loads=(1., 0., 0.))
        c = seal(replace(c, connection_export_limit_kw=known(0)))
        a = self.actual(c)
        row = a["rows"][0]
        self.assertEqual(row["connection"]["signed_kw"], -2)
        self.assertEqual(row["connection"]["export_kw"], 2)
        self.assertEqual(row["discharge_ac_kwh"], 3)
        self.assertEqual(a["connection_status"], "FAIL")
        self.assertEqual(self.actual(seal(replace(c, connection_export_limit_kw=unknown())))["connection_status"], "Q")
        self.assertEqual(self.actual(seal(replace(c, connection_import_limit_kw=unknown())))["connection_status"], "FAIL")

    def test_g17_connection_views_preserve_native_floating_operation_order(self):
        spec = BatterySpec(1e16, 1e16, 0., 1., 1e16, 1e16, 1., 1., 1.)
        c = make_case(actual=((0, 0, 0, 1e16),), x=1e16, eta=1., executor=spec, loads=(1e16, 1., 0.))
        connection = self.actual(c)["rows"][0]["connection"]
        self.assertEqual(connection["signed_kw"], connection["import_kw"]-connection["export_kw"])
        self.assertEqual(connection["signed_kw"], 0.)

    def test_g18_existing_B10_positive_import_boundary_and_no_new_bridge(self):
        panel = tuple(replace(row, heat_pump_import_kw=1.) for row in b10_fixture.demand_panel() if row.source_entity_id == "H1")
        flex = tuple(b10_fixture.flex_row("H1", row.timestamp, physical=3., committed=3., dispatched=3.,
                     claims=(PHYSICAL_FLEX_CAPABILITY, FLEX_ACTIVATION)) for row in panel)
        r = build_managed_node_load(panel, flex)
        for row in r.rows:
            self.assertAlmostEqual(row.proven_managed_reduction_mw, .001)
            self.assertAlmostEqual(row.managed_programme_import_mw, 0.)
        self.assertEqual(3.-r.rows[0].proven_managed_reduction_mw*1000, 2.)
        result = shared.evaluate_shared_use(make_case(actual=((0, 0, 0, 3),), eta=1., loads=(1., 0., 0.)))
        self.assertEqual(result["response"]["records"][0]["response_up_kw"], 3)
        self.assertIsNone(result["automatic_b10_projection"])
        self.assertFalse(result["real_delivery_admitted"])
        self.assertEqual(result["legs"]["actual"]["rows"][0]["connection"]["export_kw"], 2)

    def test_g18_automatic_projection_programme_scope_real_claim_rejected(self):
        c = make_case()
        claim = shared.ResponseClaim(c.scope, shared.comparison_digest(c), shared.digest(c.baseline), "CONDITIONAL_TOTAL_CONNECTION_RESPONSE", "SCN", False)
        for bad in (replace(claim, automatic_b10_projection=True), replace(claim, meaning="PROGRAMME_IMPORT_REDUCTION"), replace(claim, truth_context="REAL")):
            with self.subTest(bad=bad), self.assertRaises(ValueError): shared.evaluate_shared_use(seal(replace(c, response_claims=(bad,))))

    def protection_case(self, c, status="PASS", full=True):
        f = b01_fixture.frame()
        definitions = (b01_fixture.metric("benefit"), b01_fixture.metric("public-cost"))
        candidate = b01_fixture.candidate("A", f, definitions, (1000, 1))
        if status != "PASS":
            rows = candidate.protection.results
            candidate = replace(candidate, protection=replace(candidate.protection, results=(replace(rows[0], status=status),)+rows[1:]))
        p = shared.QualifiedProtection(H, shared.comparison_digest(c), candidate, f, shared.digest(candidate), shared.digest(f),
             b01_fixture.cash_scope_digest(candidate), status, qualified() if full else unknown(), b01_fixture.SCN)
        return seal(replace(c, financial=replace(c.financial, protection=p)))

    def test_g19_tariff_component_never_complete_benefit(self):
        c = make_case()
        terms = tuple((key, known(1000) if key == "tariff_energy_component" else value) for key, value in c.financial.components)
        r = shared.evaluate_shared_use(seal(replace(c, financial=replace(c.financial, components=terms))))
        self.assertEqual(r["financial"]["complete_household_protection_status"], "Q")
        self.assertIsNone(r["financial"]["monetary_result"])
        self.assertFalse(r["financial"]["calculation_performed"])
        self.assertIsNone(r["financial_dispatch_priority"])

    def test_g19_qualified_native_protection_preserved_and_deficit_dominates(self):
        for status in ("PASS", "FAIL", "Q"):
            c = self.protection_case(make_case(), status)
            r = shared.evaluate_shared_use(c)
            self.assertEqual(r["financial"]["complete_household_protection_status"], status)
            self.assertEqual(r["financial"]["qualified_protection"], c.financial.protection)
        c = self.protection_case(make_case(), "FAIL", full=False)
        self.assertEqual(shared.evaluate_shared_use(c)["financial"]["complete_household_protection_status"], "FAIL")
        c = self.protection_case(make_case(), "PASS", full=False)
        self.assertEqual(shared.evaluate_shared_use(c)["financial"]["complete_household_protection_status"], "Q")

    def test_g19_qualified_actor_counterfactual_period_binding_rejected(self):
        c = self.protection_case(make_case())
        p = c.financial.protection
        for bad in (replace(p, actor_id=S), replace(p, comparison_sha256="0"*64), replace(p, cash_scope_sha256="0"*64), replace(p, supplied_status="FAIL")):
            with self.subTest(bad=bad), self.assertRaises(ValueError): shared.evaluate_shared_use(seal(replace(c, financial=replace(c.financial, protection=bad))))

    def test_g20_identity_hash_denominator_coordinate_and_events(self):
        c = make_case(actual=((0, 1, 0, 0), (0, 1, 0, 0)))
        for name, value in (("device_id", "different"), ("connection_id", "different"), ("household_actor_id", "different"),
                            ("coordinate", shared.REFERENCE), ("capacity_denominator", "NOMINAL"), ("capacity_kwh", 9.), ("executor_sha256", "0"*64)):
            with self.subTest(name=name), self.assertRaises(ValueError): self.actual(seal(replace(c, identity=replace(c.identity, **{name: value}))))
        with self.assertRaisesRegex(ValueError, "duplicate physical"):
            self.actual(update_interval(c, 1, physical_event_id=c.actual_leg.intervals[0].physical_event_id))
        with self.assertRaisesRegex(ValueError, "contiguous"):
            self.actual(update_interval(c, 1, start=stamp(2), end=stamp(3)))
        with self.assertRaisesRegex(ValueError, "duration"):
            self.actual(update_interval(c, hours=.5))
        with self.assertRaisesRegex(ValueError, "digest"):
            self.actual(replace(c, case_id="changed-without-rebinding"))

    def test_g20_malformed_numbers_q_na_and_unknowns_are_distinct(self):
        c = make_case()
        for bad in (-1., True, float("nan"), float("inf"), None):
            request = replace(c.actual_leg.intervals[0].requests[0], discharge_ac_kw=bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.actual(update_interval(c, requests=(request, c.actual_leg.intervals[0].requests[1])))
        with self.assertRaises(ValueError): self.actual(seal(replace(c, connection_export_limit_kw=None)))
        with self.assertRaises(ValueError): self.actual(seal(replace(c, absolute_tolerance_kwh=1e6)))
        with self.assertRaises(ValueError): self.actual(update_interval(c, allocations=None))
        with self.assertRaises(ValueError): self.actual(seal(replace(c, stored_standing_loss_condition="ZERO_MEASURED")))
        self.assertEqual(self.actual(update_leg(c, agreement=Q) if c.scope == shared.AGREEMENT else update_leg(update_leg(c, agreement=Q), "baseline", agreement=Q))["rights"]["status"], "Q")

    def test_g20_reference_source_hash_and_unsupported_point_native_q(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        c = make_case(actual=((0, 0, 0, .000001),), hours=(.25,), x=3., executor=ref)
        c = ref_allocations(ref_allocations(c), "baseline")
        a = self.actual(c)
        self.assertEqual(a["physical_status"], "Q")
        self.assertEqual(a["rows"][0]["native"]["status"], "Q_IDLE_INVENTORY")
        with self.assertRaisesRegex(ValueError, "source pins"):
            self.actual(seal(replace(c, source_pins=tuple((k, "0"*64) for k, _ in c.source_pins))))

    def test_known_allocation_failure_dominates_unrelated_unknown_row(self):
        c = make_case()
        a = replace(c.actual_leg.intervals[0].allocations[0], inventory_debit_kwh=20.)
        result = self.actual(update_interval(c, allocations=(a,)))
        self.assertEqual(result["allocation_status"], "FAIL")
        self.assertIn("Q_ACTOR_ALLOCATION", result["rows"][0]["allocation"]["unknowns"])

    def test_g04_budget_window_independent_of_service_window(self):
        c = make_case(actual=((0, 0, 0, 1), (0, 0, 0, 1)), eta=1.)
        g = c.actual_leg.agreement
        budgets = (g.budgets[0], replace(g.budgets[1], end=stamp(1)))
        a = self.actual(update_agreement(c, budgets=budgets))
        self.assertIn(S+":OUTSIDE_BUDGET_WINDOW", a["rights"]["failures"])
        self.assertEqual(a["rights"]["intervals"][1]["actors"][S]["available_before_kwh"], 0.)

    def test_g07_remaining_access_uses_both_actors_and_separate_minimum(self):
        c = make_case(actual=((0, 3, 0, 0), (0, 0, 0, 0)), eta=1., x=5.)
        a = self.actual(c)
        self.assertEqual(a["rights"]["intervals"][0]["actors"][S]["remaining_available_inventory_kwh"], 2.)
        self.assertIn("MINIMUM_TOTAL_RETAINED_FAILED", self.actual(update_agreement(c, minimum_total_retained_kwh=known(4)))["rights"]["failures"])

    def test_g03_fulfillment_failure_survives_later_reference_unknown(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        c = make_case(actual=((0, 0, 0, 3), (0, 0, 0, 0)), hours=(.25, .25), x=.6, executor=ref)
        c = ref_allocations(ref_allocations(c), "baseline")
        a = self.actual(c)
        self.assertEqual(a["physical_status"], "Q")
        self.assertEqual(a["requested_schedule_fulfillment_status"], "FAIL")

    def test_g08_adjacent_right_revisions_share_depleted_budget(self):
        c = make_case(actual=((0, 0, 0, 1), (0, 0, 0, 1)), eta=1.)
        g = c.actual_leg.agreement
        budget = (g.budgets[0], replace(g.budgets[1], draw_kwh=known(1)))
        rights = (g.rights[0], replace(g.rights[1], end=stamp(1), service_end=stamp(1)),
                  replace(g.rights[1], right_id="revised", start=stamp(1), service_start=stamp(1)))
        a = self.actual(update_agreement(c, budgets=budget, rights=rights))
        self.assertEqual(a["rights"]["intervals"][1]["actors"][S]["budget_before_kwh"], 0.)
        self.assertIn(S+":DRAW_BUDGET_EXCEEDED", a["rights"]["failures"])

    def test_g20_nonfinite_aggregate_and_boolean_executor_fail(self):
        c = make_case(actual=((1e308, 0, 1e308, 0),), hours=(.25,))
        with self.assertRaises(ValueError): self.actual(c)
        c = make_case(loads=(1e308, 1e308, 0.))
        with self.assertRaises(ValueError): self.actual(c)
        c = make_case(executor=BatterySpec(10, 10, 0, 1, True, 5, .9, .9, 1))
        with self.assertRaises(ValueError): self.actual(c)

    def test_g16_known_contract_failure_dominates_unrelated_contract_q(self):
        c = make_case(actual=((0, 0, 0, 2),), eta=1.)
        g = c.actual_leg.agreement
        rights = (g.rights[0], replace(g.rights[1], discharge_ac_kw=known(1), draw_kwh=unknown()))
        a = self.actual(update_agreement(c, rights=rights))
        self.assertEqual(a["rights"]["status"], "FAIL")
        self.assertIn(S+":ENERGY_RIGHT_Q", a["rights"]["unknowns"])

    def test_g08_known_budget_deficit_dominates_unknown_replenishment(self):
        c = make_case(actual=((0, 0, 0, 2),), eta=1.)
        g = c.actual_leg.agreement
        budgets = (g.budgets[0], replace(g.budgets[1], draw_kwh=known(1), replenishment="Q"))
        a = self.actual(update_agreement(c, budgets=budgets))
        self.assertEqual(a["rights"]["status"], "FAIL")
        self.assertIn(S+":DRAW_BUDGET_EXCEEDED", a["rights"]["failures"])
        self.assertIn(S+":BUDGET_Q", a["rights"]["unknowns"])
        c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, 2)), eta=1.)
        g = c.actual_leg.agreement
        budgets = (g.budgets[0], replace(g.budgets[1], draw_kwh=known(1), replenishment="Q"))
        a = self.actual(update_agreement(c, budgets=budgets))
        self.assertEqual(a["rights"]["intervals"][1]["actors"][S]["budget_before_kwh"], 1.)
        self.assertEqual(a["rights"]["status"], "FAIL")

    def test_g09_missing_allocation_propagates_unknown_callable_duration(self):
        c = make_case(actual=((0, 0, 0, 1), (0, 0, 0, 1)), eta=1.)
        a = self.actual(update_interval(c, allocations=Q))
        self.assertIsNone(a["rights"]["intervals"][1]["actors"][S]["callable_hours_before"])
        self.assertIsNone(a["rights"]["intervals"][1]["actors"][S]["callable_hours_after"])

    def test_small_flow_cannot_borrow_tolerance_from_initial_stock(self):
        c = make_case(actual=((0, 0, 0, 1e-10),), admissions=((0, 0, 0, 1e-10),), x=0.)
        self.assertEqual(self.actual(c)["allocation_status"], "FAIL")

    def test_canonical_registry_hook_detects_contract_failure(self):
        from tools.validate_registry import validate_b07_shared_use_artifacts
        errors = []
        with patch.object(shared, "load_shared_use_contract", side_effect=ValueError("SCN:bad-contract")):
            validate_b07_shared_use_artifacts(errors)
        self.assertEqual(errors, ["invalid B07 shared-use schedule contract: SCN:bad-contract"])

    def test_g07_r1_retained_floor_bounds_access_and_protected_availability(self):
        for mode in (shared.ACCESS, shared.PROTECTED):
            for minimum in (0., 4.):
                with self.subTest(mode=mode, minimum=minimum):
                    c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, 0)), eta=1., x=5., mode=mode, protected=4.)
                    a = self.actual(update_agreement(c, minimum_total_retained_kwh=known(minimum)))
                    self.assertEqual(a["rights"]["status"], "PASS_SCN")
                    for actor, pool in ((H, 1.), (S, 4.)):
                        expected = min(5.-minimum, pool) if mode == shared.PROTECTED else 5.-minimum
                        row = a["rights"]["intervals"][0]["actors"][actor]
                        self.assertEqual(row["available_before_kwh"], expected)
                        self.assertEqual(row["remaining_available_inventory_kwh"], expected)
                        self.assertEqual(row["physical_drawable_inventory_before_kwh"], 5.)
                        self.assertEqual(row["shared_retained_floor_headroom_before_kwh"], 5.-minimum)
                        self.assertTrue(row["availability_is_conditional_actor_ceiling_not_additive"])

    def test_g09_r1_unknown_floor_preserves_physical_values_only(self):
        for mode in (shared.ACCESS, shared.PROTECTED):
            c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, 0)), eta=1., x=5., mode=mode, protected=4.)
            a = self.actual(update_agreement(c, minimum_total_retained_kwh=unknown()))
            self.assertEqual(a["physical_status"], "PASS_SCN")
            self.assertEqual(a["rights"]["status"], "Q")
            for actor in (H, S):
                row = a["rights"]["intervals"][0]["actors"][actor]
                self.assertIsNone(row["available_before_kwh"])
                self.assertIsNone(row["remaining_available_inventory_kwh"])
                self.assertIsNone(row["shared_retained_floor_headroom_before_kwh"])
                self.assertEqual(row["physical_drawable_inventory_before_kwh"], 5.)
                self.assertEqual(row["physical_drawable_inventory_after_kwh"], 5.)

    def test_g07_r1_retained_floor_and_native_reserve_are_not_added(self):
        spec = BatterySpec(10., 10., .2, 1., 5., 5., 1., 1., 1.)
        for floor, expected in ((0., 3.), (1., 3.), (4., 1.)):
            c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, 0)), x=5., eta=1., executor=spec)
            row = self.actual(update_agreement(c, minimum_total_retained_kwh=known(floor)))["rights"]["intervals"][0]["actors"][S]
            self.assertEqual(row["physical_drawable_inventory_before_kwh"], 3.)
            self.assertEqual(row["available_before_kwh"], expected)
            self.assertEqual(row["remaining_available_inventory_kwh"], expected)

    def test_g08_r2_partial_allocation_retains_known_actor_energy_budget_failure(self):
        for known_actor in (H, S):
            command = (0, 1, 0, 0) if known_actor == H else (0, 0, 0, 1)
            c = make_case(actual=(command,), x=5., eta=1.)
            g = c.actual_leg.agreement
            rights = tuple(replace(r, draw_kwh=known(.5)) if r.actor_id == known_actor else r for r in g.rights)
            budgets = tuple(replace(b, draw_kwh=known(.5)) if b.actor_id == known_actor else b for b in g.budgets)
            c = update_agreement(c, rights=rights, budgets=budgets)
            c = update_interval(c, allocations=tuple(a for a in c.actual_leg.intervals[0].allocations if a.actor_id == known_actor))
            a = self.actual(c)
            self.assertEqual(a["allocation_status"], "Q")
            self.assertEqual(a["rights"]["status"], "FAIL")
            self.assertIn(known_actor+":ENERGY_RIGHT_EXCEEDED", a["rights"]["failures"])
            self.assertIn(known_actor+":DRAW_BUDGET_EXCEEDED", a["rights"]["failures"])
            self.assertTrue(a["rights"]["intervals"][0]["actors"][known_actor]["submitted_actor_use_known"])
            self.assertTrue(all(v is None for v in a["rights"]["remaining_budgets_kwh"].values()))

    def test_g09_r2_partial_allocation_retains_known_pool_failure_without_advancing_pool(self):
        for known_actor, protected in ((H, 4.5), (S, .5)):
            command = (0, 1, 0, 0) if known_actor == H else (0, 0, 0, 1)
            c = make_case(actual=(command,), x=5., eta=1., mode=shared.PROTECTED, protected=protected)
            c = update_interval(c, allocations=tuple(a for a in c.actual_leg.intervals[0].allocations if a.actor_id == known_actor))
            a = self.actual(c)
            self.assertEqual(a["allocation_status"], "Q")
            self.assertEqual(a["rights"]["status"], "FAIL")
            self.assertIn(known_actor+":PROTECTED_POOL_BORROWING_OR_SHORTAGE", a["rights"]["failures"])
            self.assertEqual(a["rights"]["terminal_protected_free_kwh"], (None, None))
            self.assertEqual(a["terminal_inventory_kwh"], 4.)

    def test_g16_r2_genuinely_missing_actor_use_stays_unknown(self):
        c = make_case(actual=((0, 0, 0, 1),), eta=1., x=5., mode=shared.PROTECTED, protected=.5)
        g = c.actual_leg.agreement
        c = update_agreement(c, rights=(g.rights[0], replace(g.rights[1], draw_kwh=known(.5))),
                             budgets=(g.budgets[0], replace(g.budgets[1], draw_kwh=known(.5))))
        a = self.actual(update_interval(c, allocations=Q))
        self.assertEqual(a["rights"]["status"], "Q")
        self.assertEqual(a["rights"]["failures"], [])
        self.assertEqual(a["rights"]["terminal_protected_free_kwh"], (None, None))

    def test_g15_r3_idle_boundary_keeps_only_active_component_response(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        for baseline, actual, expected in (((0, 0, 0, 0), (0, 0, 0, 1), 1.),
                                           ((0, 1, 0, 0), (0, 0, 0, 0), -1.),
                                           ((0, 1, 0, 0), (0, 0, 0, .000001), -1.)):
            c = make_case(actual=(actual,), baseline=(baseline,), hours=(.25,), x=3., executor=ref)
            c = ref_allocations(ref_allocations(c), "baseline")
            result = shared.evaluate_shared_use(c)
            self.assertEqual(result["response"]["status"], "Q")
            self.assertIsNone(result["response"]["energy_kwh"])
            self.assertIsNone(result["response"]["records"][0]["response_up_kw"])
            component = result["response"]["active_component"]
            self.assertEqual(component["meaning"], "CONDITIONAL_ACTIVE_CONVERTER_COMPONENT_RESPONSE")
            self.assertEqual(component["status"], "CONDITIONAL_ACTIVE_CONVERTER_COMPONENT_DIFFERENCE")
            self.assertAlmostEqual(component["records"][0]["response_up_kw"], expected)
            self.assertAlmostEqual(component["energy_kwh"], expected*.25)
            idle_leg = "baseline" if not any(baseline) else "actual"
            connection = result["legs"][idle_leg]["rows"][0]["connection"]
            self.assertEqual(connection["status"], "Q")
            self.assertIsNone(connection["signed_kw"])
            self.assertIsNone(connection["import_kw"])
            self.assertIsNone(connection["export_kw"])
            self.assertEqual(connection["active_component"]["signed_kw"], 2.)

    def test_g17_r3_all_active_reference_and_stored_conditional_response_remain_known(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        c = make_case(actual=((0, 0, 0, 2),), baseline=((0, 1, 0, 0),), hours=(.25,), x=3., executor=ref)
        c = ref_allocations(ref_allocations(c), "baseline")
        result = shared.evaluate_shared_use(c)
        self.assertEqual(result["response"]["status"], "CONDITIONAL_SUPPLIED_SCHEDULE_DIFFERENCE")
        self.assertAlmostEqual(result["response"]["energy_kwh"], .25)
        stored = shared.evaluate_shared_use(make_case(actual=((0, 0, 0, 1),), hours=(.25,)))
        self.assertEqual(stored["response"]["status"], "CONDITIONAL_SUPPLIED_SCHEDULE_DIFFERENCE")
        self.assertEqual(stored["response"]["energy_kwh"], .25)

    def test_g15_r3_E2_idle_aggregate_is_retained_without_interval_or_DC_imputation(self):
        ref = native.source_reference(discharge_curve_id="BAT2AC_STANDARD", reserve_dc_output_equiv_kwh=0.)
        c = make_case(actual=((0, 0, 0, 0),), hours=(2.,), x=3., executor=ref, mode=shared.PROTECTED, protected=2.)
        c = ref_allocations(ref_allocations(c), "baseline")
        for leg in ("actual", "baseline"):
            c = update_leg(c, leg, idle_accounting=shared.IdleAccounting(("0",), 2., Q, False))
        result = shared.evaluate_shared_use(c)
        self.assertEqual(result["response"]["status"], "Q")
        self.assertIsNone(result["response"]["energy_kwh"])
        self.assertEqual(result["response"]["active_component"]["energy_kwh"], 0.)
        for leg in result["legs"].values():
            self.assertEqual(leg["idle_ac"]["status"], "E2_AGGREGATE_ONLY")
            self.assertAlmostEqual(leg["idle_ac"]["ac_energy_debit_kwh"], .00814)
            self.assertIsNone(leg["idle_ac"]["dc_inventory_drain_kwh"])
            self.assertIsNone(leg["rows"][0]["connection"]["signed_kw"])
            self.assertIsNone(leg["terminal_inventory_kwh"])
            self.assertEqual(leg["rights"]["terminal_protected_free_kwh"], (None, None))

    def test_g19_r4_unknown_or_pointer_correspondence_retains_native_failure_only(self):
        for mode in ("Q", "EXTERNAL_ADMISSION"):
            c = self.protection_case(make_case(), "FAIL")
            p = c.financial.protection
            p = replace(p, correspondence=replace(p.correspondence, mode=mode, reference="Q:upstream subject correspondence"))
            result = shared.evaluate_shared_use(seal(replace(c, financial=replace(c.financial, protection=p))))["financial"]
            self.assertEqual(result["complete_household_protection_status"], "Q")
            diagnostic = result["upstream_protection_diagnostic"]
            self.assertEqual(diagnostic["status"], "FAIL")
            self.assertEqual(diagnostic["native_subject_scope_id"], p.candidate.identity.scope_id)
            self.assertEqual(diagnostic["candidate_sha256"], p.candidate_sha256)
            self.assertEqual(diagnostic["cash_scope_sha256"], p.cash_scope_sha256)
            self.assertFalse(diagnostic["subject_correspondence_qualified"])
            self.assertEqual(result["qualified_protection"], p)

    def test_g19_r4_qualified_local_failure_dominates_unrelated_completeness_Q(self):
        for mode in ("SCN", "ADMITTED"):
            c = self.protection_case(make_case(), "FAIL", full=False)
            p = c.financial.protection
            # Declared fixture qualification only; no real source/subject admission.
            correspondence = (p.correspondence if mode == "SCN" else
                replace(p.correspondence, mode=mode, source_pins=(("SCN:correspondence-witness", "1"*64),), evidence_tier="E1"))
            p = replace(p, correspondence=correspondence)
            result = shared.evaluate_shared_use(seal(replace(c, financial=replace(c.financial, protection=p))))["financial"]
            self.assertEqual(result["complete_household_protection_status"], "FAIL")
            self.assertEqual(result["upstream_protection_diagnostic"]["status"], "FAIL")
            self.assertTrue(result["upstream_protection_diagnostic"]["subject_correspondence_qualified"])
            self.assertTrue(all(t.status == "Q" for t in result["components"].values()))
            self.assertFalse(result["calculation_performed"])

    def test_g08_r3_later_known_use_exceeds_absolute_caps_after_unknown(self):
        for actor, index in ((H, 0), (S, 1)):
            for mode in (shared.ACCESS, shared.PROTECTED):
                with self.subTest(actor=actor, mode=mode):
                    command = (0, 2, 0, 0) if actor == H else (0, 0, 0, 2)
                    c = make_case(actual=((0, 0, 0, 0), command), eta=1., x=5., mode=mode, protected=2.5)
                    g = c.actual_leg.agreement
                    c = update_agreement(c,
                        rights=tuple(replace(r, draw_kwh=known(1)) if r.actor_id == actor else r for r in g.rights),
                        budgets=tuple(replace(b, draw_kwh=known(1)) if b.actor_id == actor else b for b in g.budgets))
                    z = self.actual(update_interval(c, allocations=Q))["rights"]
                    row = z["intervals"][1]["actors"][actor]
                    self.assertEqual(z["status"], "FAIL")
                    self.assertIn(actor+":ENERGY_RIGHT_EXCEEDED", z["failures"])
                    self.assertIn(actor+":DRAW_BUDGET_EXCEEDED", z["failures"])
                    self.assertTrue(row["submitted_actor_use_known"])
                    self.assertIsNone(row["energy_right_before_kwh"])
                    self.assertIsNone(row["budget_before_kwh"])
                    self.assertIsNone(row["callable_hours_before"])
                    self.assertEqual(row["known_draw_lower_bound_after_kwh"], 2.)
                    self.assertEqual(row["non_replenishing_budget_remaining_upper_bound_after_kwh"], -1.)
                    self.assertTrue(z["unknowns"])
                    self.assertTrue(all(v is None for v in z["remaining_budgets_kwh"].values()))

    def test_g08_r3_known_draw_accumulates_across_unknown_positions(self):
        for unknown_position in (0, 1):
            for actor in (H, S):
                with self.subTest(unknown_position=unknown_position, actor=actor):
                    command = (0, .6, 0, 0) if actor == H else (0, 0, 0, .6)
                    commands = [command, command, command]
                    commands[unknown_position] = (0, 0, 0, 0)
                    c = make_case(actual=commands, eta=1., x=5.)
                    g = c.actual_leg.agreement
                    c = update_agreement(c,
                        rights=tuple(replace(r, draw_kwh=known(1)) if r.actor_id == actor else r for r in g.rights),
                        budgets=tuple(replace(b, draw_kwh=known(1)) if b.actor_id == actor else b for b in g.budgets))
                    z = self.actual(update_interval(c, unknown_position, allocations=Q))["rights"]
                    row = z["intervals"][2]["actors"][actor]
                    self.assertIn(actor+":ENERGY_RIGHT_EXCEEDED", z["intervals"][2]["failures"])
                    self.assertIn(actor+":DRAW_BUDGET_EXCEEDED", z["intervals"][2]["failures"])
                    self.assertAlmostEqual(row["known_draw_lower_bound_before_kwh"], .6)
                    self.assertAlmostEqual(row["known_draw_lower_bound_after_kwh"], 1.2)
                    self.assertAlmostEqual(row["known_budget_draw_lower_bound_after_kwh"], 1.2)
                    self.assertIsNone(row["energy_right_after_kwh"])
                    self.assertIsNone(row["budget_after_kwh"])

    def test_g08_r3_partial_known_rows_accumulate_without_filling_missing_actor(self):
        for actor, index in ((H, 0), (S, 1)):
            command = (0, .6, 0, 0) if actor == H else (0, 0, 0, .6)
            c = make_case(actual=(command, command), eta=1.)
            g = c.actual_leg.agreement
            c = update_agreement(c,
                rights=tuple(replace(r, draw_kwh=known(1)) if r.actor_id == actor else r for r in g.rights),
                budgets=tuple(replace(b, draw_kwh=known(1)) if b.actor_id == actor else b for b in g.budgets))
            for n in (0, 1):
                c = update_interval(c, n, allocations=(c.actual_leg.intervals[n].allocations[index],))
            z = self.actual(c)["rights"]
            row = z["intervals"][1]["actors"][actor]
            other = z["intervals"][1]["actors"][S if actor == H else H]
            self.assertIn(actor+":ENERGY_RIGHT_EXCEEDED", z["failures"])
            self.assertIn(actor+":DRAW_BUDGET_EXCEEDED", z["failures"])
            self.assertAlmostEqual(row["known_draw_lower_bound_after_kwh"], 1.2)
            self.assertEqual(other["known_draw_lower_bound_after_kwh"], 0.)
            self.assertFalse(other["submitted_actor_use_known"])
            self.assertIsNone(row["budget_after_kwh"])

    def test_g09_r3_known_duration_exceeds_whole_window_after_unknown(self):
        for actor in (H, S):
            command = (0, .2, 0, 0) if actor == H else (0, 0, 0, .2)
            c = make_case(actual=((0, 0, 0, 0), command), eta=1.)
            g = c.actual_leg.agreement
            c = update_agreement(c, rights=tuple(replace(r, callable_hours=known(.25)) if r.actor_id == actor else r for r in g.rights))
            z = self.actual(update_interval(c, allocations=Q))["rights"]
            row = z["intervals"][1]["actors"][actor]
            self.assertIn(actor+":REQUEST_DURATION_EXCEEDED", z["failures"])
            self.assertIn(actor+":ADMITTED_DURATION_EXCEEDED", z["failures"])
            self.assertEqual(row["callable_hours_upper_bound_before"], .25)
            self.assertEqual(row["known_admitted_hours_lower_bound_after"], 1.)
            self.assertIsNone(row["callable_hours_before"])
            self.assertIsNone(row["callable_hours_after"])

    def test_g09_r3_known_duration_accumulates_around_unknown(self):
        for unknown_position in (0, 1):
            commands = [(0, 0, 0, .2)]*3
            commands[unknown_position] = (0, 0, 0, 0)
            c = make_case(actual=commands, hours=(.5, .5, .5), eta=1.)
            g = c.actual_leg.agreement
            c = update_agreement(c, rights=(g.rights[0], replace(g.rights[1], callable_hours=known(.75))))
            z = self.actual(update_interval(c, unknown_position, allocations=Q))["rights"]
            row = z["intervals"][2]["actors"][S]
            self.assertIn(S+":REQUEST_DURATION_EXCEEDED", z["failures"])
            self.assertIn(S+":ADMITTED_DURATION_EXCEEDED", z["failures"])
            self.assertEqual(row["known_admitted_hours_lower_bound_before"], .5)
            self.assertEqual(row["known_admitted_hours_lower_bound_after"], 1.)
            self.assertIsNone(row["callable_hours_after"])

    def test_g09_r3_known_request_duration_survives_unknown_admission(self):
        c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, .2)), eta=1.)
        g = c.actual_leg.agreement
        c = update_agreement(c, rights=(g.rights[0], replace(g.rights[1], callable_hours=known(.25))))
        for n in (0, 1): c = update_interval(c, n, allocations=Q)
        z = self.actual(c)["rights"]
        self.assertIn(S+":REQUEST_DURATION_EXCEEDED", z["failures"])
        self.assertNotIn(S+":ADMITTED_DURATION_EXCEEDED", z["failures"])
        self.assertEqual(z["intervals"][1]["actors"][S]["known_admitted_hours_lower_bound_after"], 0.)

    def test_g16_r3_unknown_past_within_or_at_caps_stays_unknown(self):
        for debit in (.8, 1.):
            c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, debit), (0, 0, 0, 0)), eta=1.)
            g = c.actual_leg.agreement
            c = update_agreement(c, rights=(g.rights[0], replace(g.rights[1], draw_kwh=known(1), callable_hours=known(1))),
                                 budgets=(g.budgets[0], replace(g.budgets[1], draw_kwh=known(1))))
            z = self.actual(update_interval(c, allocations=Q))["rights"]
            row = z["intervals"][1]["actors"][S]
            self.assertEqual(z["status"], "Q")
            self.assertEqual(z["failures"], [])
            self.assertAlmostEqual(row["energy_right_remaining_upper_bound_after_kwh"], 1.-debit)
            self.assertIsNone(row["energy_right_after_kwh"])
            self.assertIsNone(row["budget_after_kwh"])
            self.assertIsNone(row["remaining_available_inventory_kwh"])

    def test_g08_r3_unknown_recharge_never_creates_fixed_replenishing_cap(self):
        for replenishment in ("ATTRIBUTED_CHARGE_CREDIT", "Q"):
            c = make_case(actual=((1, 0, 1, 0), (0, 0, 0, .8), (0, 0, 0, .8)), eta=1., x=5.)
            g = c.actual_leg.agreement
            c = update_agreement(c, budgets=(g.budgets[0], replace(g.budgets[1], draw_kwh=known(1), replenishment=replenishment)))
            z = self.actual(update_interval(c, allocations=Q))["rights"]
            row = z["intervals"][2]["actors"][S]
            self.assertEqual(z["status"], "Q")
            self.assertEqual(z["failures"], [])
            self.assertAlmostEqual(row["known_budget_draw_lower_bound_after_kwh"], 1.6)
            self.assertIsNone(row["non_replenishing_budget_remaining_upper_bound_before_kwh"])
            self.assertIsNone(row["non_replenishing_budget_remaining_upper_bound_after_kwh"])
            self.assertIsNone(row["budget_after_kwh"])

    def test_g08_r3_nonreplenishing_draw_bound_survives_unknown_charge(self):
        c = make_case(actual=((0, 0, 0, .6), (0, 0, 2, 0), (0, 0, 0, .6)), eta=1., x=5.)
        g = c.actual_leg.agreement
        c = update_agreement(c, budgets=(g.budgets[0], replace(g.budgets[1], draw_kwh=known(1))))
        z = self.actual(update_interval(c, 1, allocations=Q))["rights"]
        row = z["intervals"][2]["actors"][S]
        self.assertIn(S+":DRAW_BUDGET_EXCEEDED", z["failures"])
        self.assertNotIn(S+":ENERGY_RIGHT_EXCEEDED", z["failures"])
        self.assertAlmostEqual(row["known_budget_draw_lower_bound_after_kwh"], 1.2)
        self.assertIsNone(row["budget_after_kwh"])

    def test_g08_r3_shared_budget_bound_survives_adjacent_right_revision(self):
        c = make_case(actual=((0, 0, 0, .6), (0, 0, 0, 0), (0, 0, 0, .6)), eta=1.)
        g = c.actual_leg.agreement
        rights = (g.rights[0], replace(g.rights[1], end=stamp(2), service_end=stamp(2), draw_kwh=known(.75)),
                  replace(g.rights[1], right_id="SCN:revised-right", start=stamp(2), service_start=stamp(2), draw_kwh=known(.75)))
        c = update_agreement(c, rights=rights, budgets=(g.budgets[0], replace(g.budgets[1], draw_kwh=known(1))))
        z = self.actual(update_interval(c, 1, allocations=Q))["rights"]
        row = z["intervals"][2]["actors"][S]
        self.assertIn(S+":DRAW_BUDGET_EXCEEDED", z["failures"])
        self.assertNotIn(S+":ENERGY_RIGHT_EXCEEDED", z["failures"])
        self.assertEqual(row["known_draw_lower_bound_before_kwh"], 0.)
        self.assertAlmostEqual(row["known_budget_draw_lower_bound_after_kwh"], 1.2)
        self.assertIsNone(row["budget_before_kwh"])

    def test_g16_r3_unknown_caps_do_not_gain_numeric_upper_bounds(self):
        c = make_case(actual=((0, 0, 0, 0), (0, 0, 0, 2)), eta=1.)
        g = c.actual_leg.agreement
        c = update_agreement(c, rights=(g.rights[0], replace(g.rights[1], draw_kwh=unknown(), callable_hours=unknown())),
                             budgets=(g.budgets[0], replace(g.budgets[1], draw_kwh=unknown())))
        z = self.actual(update_interval(c, allocations=Q))["rights"]
        row = z["intervals"][1]["actors"][S]
        self.assertEqual(z["status"], "Q")
        self.assertEqual(z["failures"], [])
        self.assertEqual(row["known_draw_lower_bound_after_kwh"], 2.)
        for field in ("energy_right_remaining_upper_bound_after_kwh", "non_replenishing_budget_remaining_upper_bound_after_kwh", "callable_hours_upper_bound_after"):
            self.assertIsNone(row[field])

    def test_g16_r3_malformed_use_does_not_advance_known_lower_bounds(self):
        c = make_case(actual=((0, 0, 0, .6), (0, 0, 0, .8)), eta=1.)
        g = c.actual_leg.agreement
        c = update_agreement(c, rights=(g.rights[0], replace(g.rights[1], draw_kwh=known(1))),
                             budgets=(g.budgets[0], replace(g.budgets[1], draw_kwh=known(1))))
        alloc = c.actual_leg.intervals[0].allocations
        c = update_interval(c, allocations=(alloc[0], replace(alloc[1], inventory_debit_kwh=.4)))
        z = self.actual(c)["rights"]
        row = z["intervals"][1]["actors"][S]
        self.assertEqual(z["status"], "FAIL")  # malformed input remains its own failure
        self.assertNotIn(S+":ENERGY_RIGHT_EXCEEDED", z["failures"])
        self.assertNotIn(S+":DRAW_BUDGET_EXCEEDED", z["failures"])
        self.assertEqual(row["known_draw_lower_bound_before_kwh"], 0.)
        self.assertEqual(row["known_draw_lower_bound_after_kwh"], .8)
        self.assertIsNone(row["energy_right_after_kwh"])

    def test_g09_r3_unserved_request_does_not_consume_admitted_duration_bound(self):
        c = make_case(actual=((0, 0, 0, 1), (0, 0, 1, 0), (0, 0, 0, .5)),
                      admissions=((0, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, .5)), eta=1., x=0.)
        g = c.actual_leg.agreement
        c = update_agreement(c, rights=(g.rights[0], replace(g.rights[1], callable_hours=known(1))))
        z = self.actual(update_interval(c, 1, allocations=Q))["rights"]
        row = z["intervals"][2]["actors"][S]
        self.assertEqual(z["status"], "Q")
        self.assertEqual(z["failures"], [])
        self.assertEqual(row["known_admitted_hours_lower_bound_before"], 0.)
        self.assertEqual(row["known_admitted_hours_lower_bound_after"], 1.)
        self.assertIsNone(row["callable_hours_after"])

    def test_registry_has_all_twenty_groups_and_no_defaults(self):
        contract = shared.load_shared_use_contract()
        self.assertEqual(len(contract["acceptance_map"]), 20)
        self.assertEqual(contract["numeric_defaults"], {})


if __name__ == "__main__": unittest.main()
