"""Synthetic witnesses only: no household data or admitted national estimate."""
import csv
import json
import unittest
from dataclasses import fields, is_dataclass, replace
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

from modules.B12.input_accounting_contract import (
    SYNTHETIC, Asset, B12ContractError, BillInput, Case, Conversion, Cost, DebtRow,
    Instrument, LiquidAsset, MoneyBasis, Period, Policy, PopulationBinding,
    Receipt, Reference, Resource, Scalar, Scope, Section, PayerShare, Valuation,
    assess_readiness, audit_accounting, validate_case,
)
from modules.B04.engine import price_a1, price_h_heating, price_h_outside, price_b_alap

ROOT = Path(__file__).resolve().parents[1]
START = date(2026, 1, 1)
END = date(2026, 12, 31)
YEAR = Period(START, END)
BASIS = "HUF_NOMINAL_2026"


def ref(name="witness"):
    return Reference(SYNTHETIC, f"{SYNTHETIC}:{name}", None, None)


def qref(name="input"):
    return Reference("Q", None, f"{name} not acquired/selected", "B12-D02")


def scalar(value, unit="HUF", basis=BASIS, period=YEAR):
    return Scalar(Decimal(str(value)), unit, "SCN", period, basis, (), f"{SYNTHETIC}:explicit-input",
                  "E3", None, None, None)


def unknown(unit="HUF", basis=BASIS, name="input"):
    return Scalar(None, unit, "Q", YEAR, basis, (), None, "E3", None,
                  f"{name} unavailable", "B12-D01")


def none():
    return Section("NONE", (), ref("explicit-none"), ("baseline", "programme"))


def rows(*values):
    return Section("ROWS", values, ref("explicit-rows"), tuple(leg for leg in ("baseline", "programme") if not any(getattr(v, "leg", None) == leg for v in values)))


def missing():
    return Section("Q", (), qref(), ())


def day(month, number=1):
    d = date(2026, month, number)
    return Period(d, d)


def asset(generation="hp1", leg="programme", **changes):
    values = dict(asset_generation_id=generation, leg=leg, component_id="HP",
                  commissioning_date=START, service_life=scalar(12, "year"),
                  life_definition="EXPLICIT_SCENARIO_LIFE", retired_generation_id=None,
                  replacement_cost_ids=none(), operating_coverage=ref("explicit-zero-om-insurance"),
                  operating_coverage_end=END, terminal_kind="NONE", terminal_value=scalar(0),
                  terminal_receipt_id=None)
    values.update(changes)
    return Asset(**values)


def cost(cost_id="invoice", **changes):
    values = dict(cost_id=cost_id, event_id=cost_id, leg="programme", component_id="HP",
                  asset_generation_id="hp1", phase_ref="S2_TO_S3", category="INITIAL_CAPEX",
                  quantity=scalar(1, "set"), gross=scalar(127000), net=scalar(100000), vat=scalar(27000),
                  vat_representation="NET_VAT_GROSS", tax_treatment=ref("nonrecoverable-gross"),
                  eligible_gross=scalar(101600), eligibility_rule=ref("eligible-80000-net-plus-21600-vat"),
                  eligibility_caps=(scalar(110000),), period=day(1), scope_ref="household-scope",
                  payer="synthetic-household", payee="synthetic-supplier", settlement_ref="full-payable",
                  inclusion_scope=("equipment-and-installation",), procurement_basis=SYNTHETIC,
                  attribution=ref("household-attributed-cost"))
    values.update(changes)
    return Cost(**values)


def debt(event, period, opening, draw, principal, closing, **changes):
    values = dict(event_id=event, period=period, opening=scalar(opening), draw=scalar(draw),
                  capitalized_interest=scalar(0), capitalized_fees=scalar(0), cash_interest=scalar(0),
                  principal=scalar(principal), cash_fees=scalar(0), extinguishment=scalar(0), closing=scalar(closing),
                  draw_route="BANK", direct_cost_id=None, fee_route="BANK", support_event_id=None,
                  extinguishment_authority=ref("no-extinguishment"), accrual_rate=scalar(0, "ratio"))
    values.update(changes)
    return DebtRow(**values)


def instrument(**changes):
    values = dict(instrument_id="loan", leg="programme", kind="PROGRAMME", lender="synthetic-lender",
                  borrower="synthetic-household", as_of=START, terms_revision="synthetic-terms-1",
                  status="CONDITIONAL", amount_kind="DRAW_SCHEDULE", access=ref("conditional-loan"),
                  start=START, maturity=END, payment_frequency="EXPLICIT_SCHEDULE",
                  availability_grace=ref("explicit-no-grace"), interest_definition="ZERO", rate_path=ref("explicit-zero"),
                  day_count_compounding=ref("zero-interest-no-compounding"), balloon_or_refinance=ref("none-zero-at-maturity"),
                  rows=rows(debt("draw", day(1), 0, 57000, 0, 57000, cash_fees=scalar(1000), fee_route="WITHHELD"),
                            debt("repayment1", day(9), 57000, 0, 28500, 28500),
                            debt("repayment2", day(12), 28500, 0, 28500, 0)))
    values.update(changes)
    return Instrument(**values)


def grant(**changes):
    values = dict(receipt_id="grant", event_id="support-1", leg="programme", category="GRANT",
                  payer="synthetic-funder", beneficiary="synthetic-household", amount=scalar(20000), period=day(6),
                  status="CONDITIONAL", award_or_contract=ref("conditional-scenario-award"), route="BANK", cost_id="invoice",
                  asset_generation_id=None, allocation=ref("eligible-cost-allocation"))
    values.update(changes)
    return Receipt(**values)


def resource(resource_id="income", leg="programme", **changes):
    values = dict(resource_id=f"{resource_id}-{leg}", event_id=f"{resource_id}-{leg}", leg=leg, category="NET_INCOME",
                  amount=scalar(100000), period=day(7), scope_ref="household-scope", source_semantics="NET_COMPONENT",
                  gross_to_net_or_scope_bridge=ref("synthetic-net-income"), covered_categories=("WAGES",),
                  household_size=scalar(2, "person/household"), equivalence_definition=ref("no-equivalisation"))
    values.update(changes)
    return Resource(**values)


def liquid(leg):
    return LiquidAsset(f"deposit-{leg}", leg, "CASH_DEPOSIT", "synthetic-household", "household-scope", START, scalar(60000), scalar(0), scalar(0), scalar(60000), ref())


def case(**changes):
    pop = PopulationBinding(ref("hypothetical-cohort"), "synthetic-household-cohort", "household", "household",
                            ref("explicit-household-dwelling-mapping"), SYNTHETIC,
                            ref("selection"), ref("missingness"), ref("weights"), ref("estimator"), ref("diagnostics"),
                            ref("uncertainty"), ref("structural-sensitivity"), YEAR)
    policy = Policy("VAR-B01-CASH-FLOW-FLOOR", "VAR-B01-HORIZON-YEARS", qref("floor metric"), qref("floor actor"),
                    qref("floor group/period"), unknown(name="floor"), unknown(name="reserve"), qref("debt constraint"))
    valuation = Valuation(unknown("ratio", name="discount rate"), BASIS, START, qref("time convention"),
                          qref("terminal debt"), qref("escalation"), unknown("ratio"), unknown("ratio"), unknown("ratio"))
    values = dict(case_id=f"{SYNTHETIC}:delayed-grant", mode=SYNTHETIC, intervention_id=f"{SYNTHETIC}:intervention",
                  archetype_id=f"{SYNTHETIC}:archetype", region_id=f"{SYNTHETIC}:region", transition_ref="S2_TO_S3",
                  identity_binding=ref(), scope=Scope("household-scope", "synthetic-household",
                      (PayerShare("synthetic-household", "synthetic-dwelling", "OWNER", scalar(1, "ratio"), scalar(1, "ratio")),), ref()),
                  population=pop, baseline_id="baseline", programme_id="programme", as_of=START,
                  physical_reference_period=YEAR, evaluation_period=YEAR, reporting_periods=(YEAR,), time_grain="DATED",
                  service_basis_ref="matched-weather-and-service", monetary_basis=MoneyBasis(BASIS, "HUF", "NOMINAL", START, ref()),
                  other_bases=(), conversions=(), costs=rows(cost()), assets=rows(asset()), bills=none(),
                  instruments=rows(instrument()), receipts=rows(grant()), resources=rows(resource(), resource(leg="baseline")),
                  required_expenditure_coverage=ref("explicit-none-required-spending-for-arithmetic-witness"),
                  liquid_assets=rows(liquid("baseline"), liquid("programme")), policy=policy, valuation=valuation)
    values.update(changes)
    return Case(**values)


def bill(leg="programme", **changes):
    values = dict(bill_id=f"bill-{leg}", event_id=f"bill-{leg}", leg=leg, carrier="ELECTRICITY", end_use="HEATING", tariff_load_scope="RESIDENTIAL_GENERAL_LOAD", tariff_connection_scope="PROFILED_LOW_VOLTAGE",
                  physical_ref="B05:synthetic-profile", service_basis_ref="matched-weather-and-service", meter_id="meter-A1",
                  distributor="MVM Démász", tariff_layer="FINAL_RETAIL_GROSS", product="A1", revision="2026-10-01",
                  eligibility=ref("conditional-scope"), service_period=Period(date(2026, 1, 1), date(2026, 1, 31)), period=day(2), quantity=scalar(100, "kWh"), billed_months=scalar(1, "month"),
                  discounted_allocation=scalar(100, "kWh"), scope_ref="household-scope", fixed_charge_key="meter-A1:2026-02",
                  coverage=ref("complete-explicit-interval"), gas_reference_state_ref=None, allocation_ref=ref("caller-allocation"))
    values.update(changes)
    if values["product"] == "H":
        upstream = price_h_heating(values["quantity"].value, values["billed_months"].value, values["distributor"],
                                   values["service_period"].start, values["service_period"].end,
                                   load_scope=values["tariff_load_scope"])
    else:
        upstream = price_a1(values["quantity"].value, values["discounted_allocation"].value,
                            values["billed_months"].value, values["distributor"])
    return BillInput.from_b04(upstream, consumption_gross=scalar(upstream.consumption_charge_huf),
                             fixed_gross=scalar(upstream.fixed_charge_huf), total_gross=scalar(upstream.total_huf), **values)


class B12InputAccountingTests(unittest.TestCase):
    def test_delayed_grant_fee_principal_and_negative_intrayear_liquidity(self):
        c = case()
        result = audit_accounting(c)
        self.assertEqual(result.amounts["unfinanced_cash.programme"], Decimal(-127000))
        self.assertEqual(result.amounts["financed_cash.programme"], Decimal(-108000))
        self.assertEqual(result.amounts["total_initial_cost.programme"], Decimal(127000))
        self.assertEqual(result.amounts["eligible_initial_cost.programme"], Decimal(101600))
        self.assertEqual(result.amounts["outstanding_debt.programme.loan"], 0)
        balances = {d: v for leg, d, v in result.liquidity if leg == "programme"}
        self.assertEqual(balances[START], -11000)
        self.assertEqual(balances[date(2026, 6, 1)], 9000)
        self.assertEqual(balances[date(2026, 12, 1)], 52000)
        self.assertEqual(result.truth, "SCN")
        self.assertEqual(result.mode, SYNTHETIC)
        self.assertIn("affordability", result.unavailable)
        self.assertTrue(result.provenance)

    def test_grant_timing_changes_liquidity_not_lifetime_cost(self):
        late = audit_accounting(case())
        early = audit_accounting(case(receipts=rows(grant(period=day(1)))))
        self.assertEqual(late.amounts["financed_cash.programme"], early.amounts["financed_cash.programme"])
        self.assertEqual(min(v for l, _, v in early.liquidity if l == "programme"), 9000)
        self.assertEqual(min(v for l, _, v in late.liquidity if l == "programme"), -11000)

    def test_income_and_eligibility_q_do_not_erase_known_gross_cost(self):
        c = case(costs=rows(cost(eligible_gross=unknown(), eligibility_rule=qref())), resources=missing())
        result = audit_accounting(c)
        self.assertEqual(result.amounts["total_initial_cost.programme"], 127000)
        self.assertEqual(result.amounts["unfinanced_cash.programme"], -127000)
        self.assertNotIn("eligible_initial_cost.programme", result.amounts)
        self.assertNotIn("recurring_budget.programme", result.amounts)
        self.assertEqual(result.liquidity, ())
        self.assertTrue(any(m.path.endswith("eligible_gross") for m in validate_case(c).missing))

    def test_invalid_scalars_cannot_be_zero(self):
        for bad in (True, False, float("inf"), 0, Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(bad=bad), self.assertRaises(B12ContractError):
                replace(scalar(0), value=bad)
        with self.assertRaises(B12ContractError):
            replace(unknown(), value=Decimal(0))
        with self.assertRaises(B12ContractError):
            replace(scalar(0), scenario_ref=None)
        with self.assertRaises(B12ContractError):
            Section("ROWS", (), ref(), ())
        with self.assertRaises(B12ContractError):
            Section("NONE", (), qref(), ())
        with self.assertRaises(B12ContractError):
            validate_case(replace(case(), instruments=None))

    def test_eligible_subset_vat_double_count_and_cap_as_quote_rejected(self):
        for c in (cost(gross=scalar(154000)), cost(eligible_gross=scalar(128000)),
                  cost(procurement_basis="B14_POLICY_CAP"), cost(gross=scalar(107000)),
                  cost(category="DEBT_PRINCIPAL"), cost(eligibility_caps=(scalar(90000),))):
            with self.subTest(c=c), self.assertRaises(B12ContractError):
                validate_case(case(costs=rows(c)))

    def test_gross_only_keeps_tax_split_unknown(self):
        c = case(costs=rows(cost(net=unknown(), vat=unknown(), vat_representation="GROSS_ONLY")))
        a = audit_accounting(c)
        self.assertEqual(a.amounts["total_initial_cost.programme"], 127000)
        self.assertIn("tax_split", a.unavailable)
        self.assertEqual(a.amounts["financed_cash.programme"], -108000)

    def test_duplicate_events_and_bundled_components_rejected(self):
        for duplicate in (cost(cost_id="different"), cost(cost_id="different", event_id="different")):
            with self.subTest(duplicate=duplicate), self.assertRaises(B12ContractError):
                validate_case(case(costs=rows(cost(), duplicate)))
        # A matched counterfactual event may occur once in each leg.
        validate_case(case(costs=rows(cost(), cost(cost_id="baseline-invoice", leg="baseline")),
                           assets=rows(asset(), asset(leg="baseline"))))

    def test_direct_supplier_money_not_bank_inflow(self):
        i = instrument()
        draw = replace(i.rows.rows[0], draw_route="SUPPLIER", direct_cost_id="invoice", fee_route="BANK")
        c = case(instruments=rows(replace(i, rows=rows(draw, *i.rows.rows[1:]))),
                 receipts=rows(grant(route="SUPPLIER", period=day(1))))
        a = audit_accounting(c)
        self.assertEqual(a.amounts["financed_cash.programme"], -108000)
        grant_row = next(r for r in a.rows if r.category == "GRANT")
        loan_row = next(r for r in a.rows if r.event_id == "draw")
        self.assertEqual(grant_row.bank, 0)
        self.assertEqual(loan_row.bank, -1000)
        self.assertEqual(next(r.bank for r in a.rows if r.event_id == "invoice"), -50000)
        self.assertEqual(next(v for l, d, v in a.liquidity if l == "programme" and d == START and v != 60000), 9000)

    def test_direct_settlement_exact_leg_date_and_unique_support(self):
        for g in (grant(route="SUPPLIER"), grant(route="SUPPLIER", period=day(1), cost_id="absent")):
            with self.assertRaises(B12ContractError):
                validate_case(case(receipts=rows(g)))
        g = grant(route="SUPPLIER", period=day(1))
        with self.assertRaises(B12ContractError):
            validate_case(case(receipts=rows(g, replace(g, receipt_id="cash-copy", route="BANK"))))
        with self.assertRaises(B12ContractError):
            validate_case(case(receipts=rows(replace(g, amount=scalar(128000)))))

    def test_debt_balance_continuity_limit_apr_term_and_maturity(self):
        i = instrument()
        mutations = [replace(i, amount_kind="BORROWING_LIMIT"), replace(i, interest_definition="APR_DIV_12"),
                     replace(i, maturity=date(2026, 11, 1)),
                     replace(i, rows=rows(replace(i.rows.rows[0], closing=scalar(56000)), *i.rows.rows[1:])),
                     replace(i, rows=rows(i.rows.rows[0], replace(i.rows.rows[1], opening=scalar(56000)), i.rows.rows[2])),
                     replace(i, rows=rows(*i.rows.rows[:2]), balloon_or_refinance=qref())]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(B12ContractError):
                validate_case(case(instruments=rows(mutation)))

    def test_capitalized_fee_is_liability_not_bank_outflow(self):
        i = instrument(rows=rows(debt("draw", day(1), 0, 57000, 0, 58000, capitalized_fees=scalar(1000)),
                                 debt("repay", day(12), 58000, 0, 58000, 0)))
        a = audit_accounting(case(instruments=rows(i)))
        self.assertEqual(next(r.bank for r in a.rows if r.event_id == "draw"), 57000)
        self.assertEqual(a.amounts["financed_cash.programme"], -108000)

    def test_supplied_periodic_interest_and_unverified_external_accrual(self):
        i = instrument(interest_definition="SUPPLIED_PERIODIC_OPENING",
                       rows=rows(debt("draw", day(1), 0, 57000, 0, 57000),
                                 debt("repay", day(12), 57000, 0, 57000, 0, cash_interest=scalar(5700), accrual_rate=scalar("0.1", "ratio"))))
        self.assertEqual(audit_accounting(case(instruments=rows(i))).amounts["financed_cash.programme"], -112700)
        wrong = replace(i, rows=rows(i.rows.rows[0], replace(i.rows.rows[1], cash_interest=scalar(570))))
        with self.assertRaises(B12ContractError):
            validate_case(case(instruments=rows(wrong)))
        a = audit_accounting(case(instruments=rows(replace(i, interest_definition="EXTERNAL_ACCRUAL_Q"))))
        self.assertIn("financed_cash", a.unavailable)
        self.assertTrue(a.unverified_checks)

    def test_cash_grant_and_principal_forgiveness_cannot_share_event(self):
        i = instrument(rows=rows(debt("draw", day(1), 0, 57000, 0, 57000),
                                 debt("repay", day(12), 57000, 0, 37000, 0, extinguishment=scalar(20000), support_event_id="support-1")))
        with self.assertRaises(B12ContractError):
            validate_case(case(instruments=rows(i)))

    def test_lifecycle_replacement_baseline_and_non_cash_terminal(self):
        old = asset(replacement_cost_ids=rows("replacement"))
        new = asset("hp2", retired_generation_id="hp1", commissioning_date=date(2026, 10, 1),
                    terminal_kind="NONCASH", terminal_value=scalar(30000))
        replacement = cost("replacement", asset_generation_id="hp2", category="REPLACEMENT", period=day(10),
                           gross=scalar(25400), net=scalar(20000), vat=scalar(5400), eligible_gross=scalar(0))
        maintenance = cost("maintenance", category="O_AND_M", period=day(8), inclusion_scope=("service",),
                           gross=scalar(1270), net=scalar(1000), vat=scalar(270), eligible_gross=scalar(0))
        baseline = cost("avoided-replacement", leg="baseline", category="INITIAL_CAPEX", gross=scalar(12700),
                        net=scalar(10000), vat=scalar(2700), eligible_gross=scalar(0))
        c = case(costs=rows(cost(), replacement, maintenance, baseline), assets=rows(old, new, asset(leg="baseline")))
        a = audit_accounting(c)
        self.assertEqual(a.amounts["unfinanced_cash.incremental"], -140970)
        self.assertEqual(a.amounts["noncash_terminal.programme.hp2"], 30000)
        self.assertFalse(any(r.category == "SALE" for r in a.rows))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, assets=rows(replace(old, service_life=scalar(0, "year")), new, asset(leg="baseline"))))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, assets=rows(old, replace(new, terminal_receipt_id="invented-cash"), asset(leg="baseline"))))
        a = audit_accounting(case(assets=rows(asset(operating_coverage_end=date(2026, 3, 1)))))
        self.assertIn("lifecycle_cost", a.unavailable)
        self.assertEqual(a.amounts["total_initial_cost.programme"], 127000)

    def test_actual_b04_adapter_gross_snapshot_and_fixed_once(self):
        a = audit_accounting(case(bills=rows(bill(), bill("baseline"))))
        self.assertEqual(a.amounts["retail_bills.programme"], a.amounts["retail_bills.baseline"])
        self.assertEqual(next(r for r in a.rows if r.category == "RETAIL_BILL").unfinanced, -a.amounts["retail_bills.baseline"])
        b = bill()
        self.assertEqual(b.upstream_status, "SCN_CONSTANT_2026_TARIFF_SNAPSHOT")
        self.assertTrue(b.upstream_source_ids)
        for bad in (replace(b, upstream_price_basis="OBSERVED_2040"),
                    replace(b, total_gross=scalar(b.total_gross.value * Decimal("1.27"))),
                    replace(b, product="H", end_use="BATTERY"),
                    replace(b, service_basis_ref="different-comfort"),
                    replace(b, tariff_layer="NET_ENERGY_ONLY")):
            with self.assertRaises(B12ContractError):
                validate_case(case(bills=rows(bad, bill("baseline"))))
        with self.assertRaises(B12ContractError):
            validate_case(case(bills=rows(b, replace(b, bill_id="duplicate-fixed", event_id="duplicate-fixed", end_use="DHW"))))
        with self.assertRaises(B12ContractError):
            BillInput.from_b04(object(), consumption_gross=scalar(0), fixed_gross=scalar(0), total_gross=scalar(0))

    def test_gas_market_boundary_reference_state_and_no_heat_volume_relabel(self):
        b = replace(bill(), carrier="GAS", tariff_layer="MARKET_RESIDENTIAL_FINAL", quantity=scalar(10, "m3"),
                    discounted_allocation=scalar(10, "m3"), gas_reference_state_ref="B11:explicit-reference-state", product="MARKET_GAS", tariff_load_scope="RESIDENTIAL_GAS_LOAD", upstream_status="SCN_GAS_MARKET_WITNESS", upstream_source_ids=())
        validate_case(case(bills=rows(b)))
        for bad in (replace(b, tariff_layer="WHOLESALE_IMPORT"), replace(b, tariff_layer="REGULATED_RESIDENTIAL_TARIFF"),
                    replace(b, quantity=scalar(10, "kWh_useful_heat"), discounted_allocation=scalar(10, "kWh_useful_heat")),
                    replace(b, gas_reference_state_ref=None)):
            with self.assertRaises(B12ContractError):
                validate_case(case(bills=rows(bad)))

    def test_budget_disjoint_spending_existing_debt_and_signed_income(self):
        existing = instrument(instrument_id="existing", kind="EXISTING", leg="baseline",
                              rows=rows(debt("existing-service", day(12), 3000, 0, 3000, 0)))
        rent = resource("rent", category="REQUIRED_NON_ENERGY", amount=scalar(10000),
                        source_semantics="DISJOINT_REQUIRED_SPENDING", covered_categories=("RENT",))
        a = audit_accounting(case(instruments=rows(instrument(), existing), resources=rows(resource(), resource(leg="baseline"), rent)))
        self.assertEqual(a.amounts["recurring_budget.programme"], 32000)
        self.assertEqual(a.amounts["recurring_budget.baseline"], 97000)
        self.assertEqual(audit_accounting(case(resources=rows(resource(amount=scalar(-1000))))).amounts["recurring_budget.programme"], -59000)
        for bad in (replace(rent, covered_categories=("ENERGY",)), replace(rent, source_semantics="HFCS_HI0220_COMPLETE"),
                    resource(source_semantics="HFCS_GROSS_INCOME"), resource(source_semantics="DEBT_BALANCE"),
                    resource(amount=scalar(100, "HUF/person/year"))):
            with self.assertRaises(B12ContractError):
                validate_case(case(resources=rows(bad)))
        a = audit_accounting(case(required_expenditure_coverage=qref("missing rent/insurance/debt fees")))
        self.assertIn("recurring_budget", a.unavailable)

    def test_liquidity_access_encumbrance_and_stock_time(self):
        for bad in (replace(liquid("programme"), kind="TOTAL_WEALTH"),
                    replace(liquid("programme"), stock_date=date(2025, 1, 1)),
                    replace(liquid("programme"), encumbered=scalar(10000))):
            with self.assertRaises(B12ContractError):
                validate_case(case(liquid_assets=rows(bad)))
        a = audit_accounting(case(liquid_assets=rows(replace(liquid("programme"), access=qref("disposal/access")))))
        self.assertEqual(a.liquidity, ())

    def test_units_shares_population_and_no_individual_pass(self):
        c = case()
        self.assertEqual(validate_case(c).individual_permission, "NOT_ASSESSED")
        self.assertIn("population estimator consumer not implemented", assess_readiness(c)["population_aggregation"])
        for p in (replace(c.population, evidence_class="MULTIPLIED_MARGINALS"),
                  replace(c.population, target_unit="dwelling", household_dwelling_bridge=qref())):
            with self.assertRaises(B12ContractError):
                validate_case(replace(c, population=p))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, scope=replace(c.scope, shares=(replace(c.scope.shares[0], payment_share=scalar("0.5", "ratio")),))))

    def test_explicit_fx_real_conversion_and_fisher_identity(self):
        c = case()
        real = MoneyBasis("HUF_REAL_2026", "HUF", "REAL", START, ref("deflator-convention"))
        eur = MoneyBasis("EUR_NOMINAL_2023", "EUR", "NOMINAL", date(2023, 1, 1), ref("original-price-date"))
        conv = Conversion(scalar(100, "EUR", eur.basis_id), scalar(40000), scalar(400, "ratio"), START, ref("explicit-FX-date"))
        valuation = replace(c.valuation, nominal_rate=scalar("0.071", "ratio"), real_rate=scalar("0.05", "ratio", real.basis_id),
                            inflation=scalar("0.02", "ratio"))
        validate_case(replace(c, other_bases=(real, eur), conversions=(conv,), valuation=valuation))
        for bad in (replace(conv, converted=scalar(39000)),):
            with self.assertRaises(B12ContractError):
                validate_case(replace(c, other_bases=(eur,), conversions=(bad,)))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, valuation=replace(valuation, nominal_rate=scalar("0.07", "ratio"))))
        with self.assertRaises(B12ContractError):
            validate_case(case(costs=rows(cost(gross=scalar(127000, basis="HUF_NOMINAL_2024")))))
        with self.assertRaises(B12ContractError):
            validate_case(case(monetary_basis=replace(c.monetary_basis, nominal_real="REAL")))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, other_bases=(real,), valuation=replace(c.valuation, discount_rate=scalar("0.05", "ratio", real.basis_id))))

    def test_discount_floor_reserve_not_defaulted(self):
        c = case()
        ready = assess_readiness(c)
        self.assertEqual(ready["financed_cash"], ())
        self.assertIn("case.valuation.discount_rate", ready["valuation"])
        self.assertIn("case.policy.floor_metric", ready["affordability"])
        self.assertIn("case.policy.reserve", ready["affordability"])
        self.assertFalse(any(any(term in key.lower() for term in ("npv", "irr", "dscr", "affordable", "support_gap"))
                             for key in audit_accounting(c).amounts))

    def test_external_review_references_do_not_admit_actual_numeric_output(self):
        def external(obj):
            if isinstance(obj, Reference):
                return obj if obj.kind == "Q" else Reference("EXTERNAL_ADMISSION", "upstream-review:scoped-quantity-and-debt", None, None)
            if isinstance(obj, Scalar):
                return obj if obj.truth == "Q" else replace(obj, truth="DER", scenario_ref=None, source_ids=("EXTERNAL-SOURCE",),
                                                           evidence_tier="E2", admission_ref="upstream-review:all-eight-conditions-and-debt")
            if is_dataclass(obj):
                return replace(obj, **{f.name: external(getattr(obj, f.name)) for f in fields(obj)})
            if isinstance(obj, tuple):
                return tuple(external(x) for x in obj)
            return obj
        c = replace(external(case()), mode="CONDITIONAL_CASE")
        assessment = validate_case(c)
        self.assertEqual(assessment.structural_status, "VALID")
        self.assertEqual(assessment.evidence_status, "Q_EXTERNAL_REVIEW_UNRESOLVED")
        a = audit_accounting(c)
        self.assertEqual(dict(a.amounts), {})
        self.assertEqual(a.rows, ())
        self.assertEqual(a.truth, "Q")
        with self.assertRaises(B12ContractError):
            validate_case(replace(case(), mode="INDIVIDUAL_RECORD"))
        with self.assertRaises(B12ContractError):
            replace(scalar(1), truth="OBS", scenario_ref=None, evidence_tier="E2", source_ids=(f"{SYNTHETIC}:fake-source",), admission_ref="claimed")

    def test_decimal_context_cannot_change_results(self):
        with localcontext() as ctx:
            ctx.prec = 3
            self.assertEqual(audit_accounting(case()).amounts["financed_cash.programme"], Decimal(-108000))

    def test_later_cost_and_grant_unknowns_are_isolated(self):
        om = cost("later-om", category="O_AND_M", period=day(11), inclusion_scope=("later-service",),
                  gross=unknown(), net=unknown(), vat=unknown(), eligible_gross=unknown())
        a = audit_accounting(case(costs=rows(cost(), om)))
        self.assertEqual(a.amounts["total_initial_cost.programme"], 127000)
        self.assertIn("lifecycle_cost", a.unavailable)
        a = audit_accounting(case(receipts=rows(grant(amount=unknown(), award_or_contract=qref()))))
        self.assertEqual(a.amounts["unfinanced_cash.programme"], -127000)
        self.assertIn("financed_cash", a.unavailable)
        self.assertTrue(all(r.financed is None and r.bank is None for r in a.rows))

    def test_h_fuel_switch_preserves_service_scope_and_separate_load_gate(self):
        gas = replace(bill("baseline"), carrier="GAS", tariff_layer="MARKET_RESIDENTIAL_FINAL",
                      quantity=scalar(10, "m3"), discounted_allocation=scalar(10, "m3"),
                      gas_reference_state_ref="B11:synthetic-state", product="MARKET_GAS",
                      tariff_load_scope="RESIDENTIAL_GAS_LOAD", upstream_status="SCN_GAS_MARKET_WITNESS", upstream_source_ids=())
        hp = bill(product="H", tariff_load_scope="ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES")
        self.assertEqual(assess_readiness(case(bills=rows(gas, hp)))["retail_bills"], ())
        with self.assertRaises(B12ContractError):
            validate_case(case(bills=rows(replace(gas, tariff_load_scope=hp.tariff_load_scope), hp)))
        shifted = replace(hp, service_period=Period(date(2026, 2, 1), date(2026, 2, 28)))
        self.assertIn("matched_baseline_programme", str(assess_readiness(case(bills=rows(gas, shifted)))["retail_bills"]))

    def test_vat_refund_aggregate_and_liquid_household_identity(self):
        refund = grant(receipt_id="refund", event_id="refund-1", category="VAT_REFUND", amount=scalar(20000))
        with self.assertRaises(B12ContractError):
            validate_case(case(receipts=rows(refund, replace(refund, receipt_id="refund-copy", event_id="refund-2"))))
        with self.assertRaises(B12ContractError):
            validate_case(case(liquid_assets=rows(replace(liquid("programme"), household_id="another-household"))))
        with self.assertRaises(B12ContractError):
            validate_case(case(instruments=rows(instrument(), instrument())))

    def test_annual_ledger_cannot_certify_intrayear_liquidity(self):
        c = case(time_grain="ANNUAL", costs=rows(cost(period=YEAR)), receipts=rows(grant(period=YEAR)),
                 resources=rows(resource(period=YEAR), resource(leg="baseline", period=YEAR)),
                 instruments=rows(instrument(rows=rows(debt("annual-schedule", YEAR, 0, 57000, 57000, 0,
                                                            cash_fees=scalar(1000), fee_route="WITHHELD")))))
        a = audit_accounting(c)
        self.assertEqual(a.amounts["financed_cash.programme"], -108000)
        self.assertEqual(a.liquidity, ())
        self.assertTrue(all(r.bank is None for r in a.rows))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, time_grain="DATED"))

    def test_missing_nested_fields_raise_contract_error_and_no_mutable_state(self):
        with self.assertRaises(B12ContractError):
            validate_case(replace(case(), other_bases=[]))
        with self.assertRaises(B12ContractError):
            validate_case(replace(case(), scope=replace(case().scope, mapping=None)))
        with self.assertRaises(TypeError):
            audit_accounting(case()).amounts["invented"] = Decimal(0)

    def test_missing_counterfactual_leg_never_silently_becomes_none(self):
        c = case()
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, costs=replace(c.costs, absent_legs=())))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, costs=replace(c.costs, absent_legs=("baseline", "programme"))))
        self.assertEqual(audit_accounting(c).amounts["total_initial_cost.baseline"], 0)

    def test_same_existing_loan_in_both_legs_is_not_overwritten(self):
        loan = instrument(instrument_id="existing-loan", kind="EXISTING",
                          maturity=date(2027, 12, 31), rows=rows(debt("service", day(12), 3000, 0, 1000, 2000)))
        a = audit_accounting(case(instruments=rows(loan, replace(loan, leg="baseline"))))
        self.assertEqual(a.amounts["outstanding_debt.programme.existing-loan"], 2000)
        self.assertEqual(a.amounts["outstanding_debt.baseline.existing-loan"], 2000)
        self.assertEqual(len([r for r in a.rows if r.event_id == "service"]), 2)

    def test_review_r1_fixed_charges_bind_meter_intervals_not_freeform_key(self):
        b = bill()
        duplicate = replace(b, bill_id="other-enduse", event_id="other-enduse", end_use="DHW", fixed_charge_key="fresh-key")
        with self.assertRaisesRegex(B12ContractError, "one meter"):
            validate_case(case(bills=rows(b, duplicate, bill("baseline"), replace(duplicate, leg="baseline"))))
        # Different months on the same meter are legitimate distinct fixed charges.
        second = bill(bill_id="february", event_id="february", period=day(3), fixed_charge_key="meter-A1:2026-03",
                      service_period=Period(date(2026, 2, 1), date(2026, 2, 28)))
        a = audit_accounting(case(bills=rows(b, second, bill("baseline"), replace(second, leg="baseline"))))
        self.assertEqual(a.amounts["retail_bills.programme"], 2 * b.total_gross.value)
        # Separate meters may have their own fixed charges over the same dates.
        separate = replace(duplicate, meter_id="meter-two")
        self.assertEqual(assess_readiness(case(bills=rows(b, separate, bill("baseline"), replace(separate, leg="baseline"))))["retail_bills"], ())

    def test_review_r2_unknown_vat_cannot_create_known_refund_cash(self):
        gross = cost(vat_representation="GROSS_ONLY", net=unknown(), vat=unknown())
        refund = grant(category="VAT_REFUND", amount=scalar(200000), receipt_id="refund", event_id="refund")
        c = case(costs=rows(gross), receipts=rows(refund), instruments=none())
        self.assertEqual(validate_case(c).structural_status, "VALID")
        a = audit_accounting(c)
        self.assertEqual(a.amounts["total_initial_cost.programme"], 127000)
        self.assertNotIn("unfinanced_cash.programme", a.amounts)
        self.assertIn("case.costs.rows[0].vat", a.unavailable["unfinanced_cash"])
        self.assertEqual(a.liquidity, ())
        self.assertTrue(all(r.bank is None and r.unfinanced is None for r in a.rows))
        # Explicit known recoverable VAT gives a bounded cash recovery exactly once.
        good = audit_accounting(case(receipts=rows(replace(refund, amount=scalar(27000))), instruments=none()))
        self.assertEqual(good.amounts["unfinanced_cash.programme"], -100000)

    def test_review_r3_terminal_sales_require_reciprocal_binding(self):
        with self.assertRaisesRegex(B12ContractError, "SALE"):
            validate_case(case(assets=rows(asset(terminal_kind="CASH_SALE", terminal_value=scalar(99999), terminal_receipt_id="grant"))))
        sale = grant(receipt_id="sale", event_id="sale", category="SALE", amount=scalar(30000),
                     asset_generation_id="hp1", cost_id=None, period=day(12, 31))
        a = asset(terminal_kind="CASH_SALE", terminal_value=scalar(30000), terminal_receipt_id="sale")
        self.assertEqual(audit_accounting(case(assets=rows(a), receipts=rows(sale))).amounts["unfinanced_cash.programme"], -97000)
        for bad in (replace(sale, asset_generation_id="other-asset"), replace(sale, amount=scalar(20000)), replace(sale, leg="baseline")):
            with self.assertRaises(B12ContractError):
                validate_case(case(assets=rows(a), receipts=rows(bad)))

    def test_review_r4_all_nested_material_fields_are_runtime_typed(self):
        fixtures = [("costs", cost()), ("assets", asset()), ("bills", bill()),
                    ("instruments", instrument()), ("receipts", grant()),
                    ("resources", resource()), ("liquid_assets", liquid("programme"))]
        for section, record in fixtures:
            for field in fields(record):
                if not isinstance(getattr(record, field.name), (Scalar, Reference)):
                    continue
                for bad in (None, "missing-field", 0):
                    with self.subTest(section=section, field=field.name, bad=bad), self.assertRaises(B12ContractError):
                        validate_case(case(**{section: rows(replace(record, **{field.name: bad}))}))
        loan = instrument()
        for field in fields(loan.rows.rows[0]):
            if not isinstance(getattr(loan.rows.rows[0], field.name), (Scalar, Reference)):
                continue
            for bad in (None, "missing-field", 0):
                with self.subTest(debt_field=field.name, bad=bad), self.assertRaises(B12ContractError):
                    row = replace(loan.rows.rows[0], **{field.name: bad})
                    validate_case(case(instruments=rows(replace(loan, rows=rows(row, *loan.rows.rows[1:])))))
        # Explicit Q is valid and remains a dependency, unlike malformed None.
        q = audit_accounting(case(instruments=rows(instrument(access=qref("access")))))
        self.assertEqual(q.amounts["unfinanced_cash.programme"], -127000)
        self.assertIn("financed_cash", q.unavailable)
        fees_q = replace(loan.rows.rows[0], cash_fees=unknown())
        validate_case(case(instruments=rows(replace(loan, rows=rows(fees_q, *loan.rows.rows[1:])))))
        # Legitimately optional identifiers remain None in the ordinary control.
        validate_case(case())

    def test_review_r5_view_dependencies_are_independent(self):
        cases = [case(receipts=rows(grant(amount=unknown(), award_or_contract=qref()))),
                 case(costs=rows(cost(gross=unknown(), net=unknown(), vat=unknown(), eligible_gross=unknown(), eligibility_rule=qref())))]
        for c in cases:
            a = audit_accounting(c)
            self.assertEqual(a.amounts["recurring_budget.programme"], 42000)
            self.assertNotIn("financed_cash.programme", a.amounts)
            self.assertEqual(a.liquidity, ())
        income_q = audit_accounting(case(resources=missing()))
        self.assertEqual(income_q.amounts["financed_cash.programme"], -108000)
        self.assertIn("recurring_budget", income_q.unavailable)
        finance_q = audit_accounting(case(instruments=missing()))
        self.assertEqual(finance_q.amounts["unfinanced_cash.programme"], -127000)
        self.assertIn("recurring_budget", finance_q.unavailable)
        om_q = cost("om-q", category="O_AND_M", gross=unknown(), net=unknown(), vat=unknown(), eligible_gross=unknown(),
                    period=day(11), inclusion_scope=("service",))
        a = audit_accounting(case(costs=rows(cost(), om_q)))
        self.assertEqual(a.amounts["total_initial_cost.programme"], 127000)
        self.assertIn("recurring_budget", a.unavailable)

    def test_review_r6_replacement_chain_chronology_and_reciprocal_cost(self):
        first = asset(replacement_cost_ids=rows("replace-2"))
        second = asset("hp2", retired_generation_id="hp1", commissioning_date=date(2026, 6, 1), replacement_cost_ids=rows("replace-3"))
        third = asset("hp3", retired_generation_id="hp2", commissioning_date=date(2026, 10, 1))
        c2 = cost("replace-2", category="REPLACEMENT", asset_generation_id="hp2", period=day(6))
        c3 = cost("replace-3", category="REPLACEMENT", asset_generation_id="hp3", period=day(10))
        c = case(costs=rows(cost(), c2, c3), assets=rows(first, second, third))
        self.assertEqual(audit_accounting(c).amounts["lifecycle_cost.programme"], 381000)
        # Generation direction establishes order even when dates coincide.
        same_day = replace(c, assets=rows(first, second, replace(third, commissioning_date=second.commissioning_date)))
        validate_case(same_day)
        bad_assets = [rows(replace(first, retired_generation_id="hp3"), second, third),
                      rows(first, replace(second, commissioning_date=date(2025, 1, 1)), third),
                      rows(replace(first, replacement_cost_ids=none()), second, third)]
        for assets_bad in bad_assets:
            with self.assertRaises(B12ContractError):
                validate_case(replace(c, assets=assets_bad))
        # Invoice cash date and commissioning are separate: genuine prepayment is valid.
        validate_case(replace(c, costs=rows(cost(), replace(c2, period=day(5)), c3)))
        # Equal dates and reciprocal costs do not excuse a genuine directed cycle.
        cycle_a = asset("hp1", retired_generation_id="hp2", replacement_cost_ids=rows("cycle-b"))
        cycle_b = asset("hp2", retired_generation_id="hp1", replacement_cost_ids=rows("cycle-a"))
        cycle_cost_a = cost("cycle-a", category="REPLACEMENT", asset_generation_id="hp1")
        cycle_cost_b = cost("cycle-b", category="REPLACEMENT", asset_generation_id="hp2")
        with self.assertRaisesRegex(B12ContractError, "cyclic"):
            validate_case(case(costs=rows(cycle_cost_a, cycle_cost_b), assets=rows(cycle_a, cycle_b)))

    def test_review_r7_h_producer_invocation_rechecked_at_adapter_and_validation(self):
        h = bill(product="H", tariff_load_scope="ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES")
        good = price_h_heating(100, 1, "MVM Démász", date(2026, 1, 1), date(2026, 1, 31),
                              load_scope=h.tariff_load_scope)
        context = {f.name: getattr(h, f.name) for f in fields(h)
                   if f.name not in {"consumption_gross", "fixed_gross", "total_gross", "upstream_status", "upstream_price_basis", "upstream_source_ids"}}
        context["service_period"] = Period(date(2026, 7, 1), date(2026, 7, 31))
        with self.assertRaisesRegex(B12ContractError, "B04 producer context"):
            BillInput.from_b04(good, consumption_gross=h.consumption_gross, fixed_gross=h.fixed_gross, total_gross=h.total_gross, **context)
        with self.assertRaises(B12ContractError):
            validate_case(case(bills=rows(replace(h, service_period=context["service_period"])) ))
        validate_case(case(bills=rows(h, replace(h, leg="baseline"))))
        with self.assertRaises(B12ContractError):
            validate_case(case(bills=rows(replace(h, distributor="ELMŰ"))))

    def test_review_r8_recurring_receipts_and_income_components_are_disjoint(self):
        duplicate = resource("copy", category="RECURRING_RECEIPT", source_semantics="RECURRING_NET_RECEIPT")
        with self.assertRaisesRegex(B12ContractError, "duplicate budget component"):
            validate_case(case(resources=rows(resource(), duplicate, resource(leg="baseline"))))
        separate = replace(duplicate, covered_categories=("CHILD_BENEFIT",), amount=scalar(20000))
        self.assertEqual(audit_accounting(case(resources=rows(resource(), separate, resource(leg="baseline")))).amounts["recurring_budget.programme"], 62000)

    def test_review_r9_noncash_support_cannot_reappear_in_resources(self):
        loan = instrument(rows=rows(debt("draw", day(1), 0, 57000, 0, 57000),
                                    debt("repay", day(12), 57000, 0, 37000, 0, extinguishment=scalar(20000), support_event_id="support-1")))
        receipt = resource("support-income", event_id="support-1", category="RECURRING_RECEIPT", source_semantics="RECURRING_NET_RECEIPT",
                           covered_categories=("TRANSFER",), period=day(12), amount=scalar(20000))
        with self.assertRaisesRegex(B12ContractError, "noncash support"):
            validate_case(case(instruments=rows(loan), receipts=none(), resources=rows(resource(), receipt, resource(leg="baseline"))))
        self.assertEqual(audit_accounting(case(instruments=rows(loan), receipts=none())).amounts["recurring_budget.programme"], 63000)
        # A distinct cash grant and explicit principal repayment is legitimate.
        self.assertEqual(audit_accounting(case()).amounts["financed_cash.programme"], -108000)

    def test_review_r10_zero_interest_rate_still_requires_ratio(self):
        loan = instrument()
        with self.assertRaisesRegex(B12ContractError, "ratio"):
            validate_case(case(instruments=rows(replace(loan, rows=rows(*(replace(r, accrual_rate=scalar(0, "HUF")) for r in loan.rows.rows))))))

    def test_review_r11_maturity_label_is_not_dated_cash_settlement(self):
        loan = instrument()
        unpaid = replace(loan, rows=rows(*loan.rows.rows[:2], debt("maturity", day(12, 31), 28500, 0, 0, 28500)),
                         balloon_or_refinance=ref("balloon-needed-at-maturity"))
        a = audit_accounting(case(instruments=rows(unpaid)))
        self.assertEqual(validate_case(case(instruments=rows(unpaid))).structural_status, "VALID")
        self.assertIn("dated_maturity_settlement_required", str(a.unavailable["financed_cash"]))
        self.assertNotIn("recurring_budget.programme", a.amounts)
        self.assertEqual(a.liquidity, ())
        paid = replace(unpaid, rows=rows(*loan.rows.rows[:2], debt("maturity", day(12, 31), 28500, 0, 28500, 0)))
        a = audit_accounting(case(instruments=rows(paid)))
        self.assertEqual(a.amounts["financed_cash.programme"], -108000)
        self.assertEqual(next(v for l, _, v in reversed(a.liquidity) if l == "programme"), 52000)
        # Horizon end can carry debt when contractual maturity is later.
        later = replace(unpaid, maturity=date(2027, 12, 31))
        self.assertEqual(audit_accounting(case(instruments=rows(later))).amounts["outstanding_debt.programme.loan"], 28500)

    def test_invariant_crossings_event_support_and_cash_dates(self):
        b = bill()
        overlap = replace(b, bill_id="overlap", event_id="overlap", end_use="DHW", fixed_charge_key="fresh-key", period=day(3))
        with self.assertRaises(B12ContractError):
            validate_case(case(bills=rows(b, overlap)))
        loan = instrument(rows=rows(debt("draw", day(1), 0, 57000, 0, 57000),
                                    debt("repay", day(12), 57000, 0, 37000, 0, extinguishment=scalar(20000), support_event_id="support-1")))
        with self.assertRaises(B12ContractError):
            validate_case(case(instruments=rows(loan), receipts=rows(grant())))
        colliding = instrument(instrument_id="other", kind="EXISTING", rows=rows(debt("support-1", day(12), 1000, 0, 1000, 0)))
        with self.assertRaises(B12ContractError):
            validate_case(case(instruments=rows(loan, colliding), receipts=none()))
        # Logical support identity may appear once in each counterfactual leg.
        validate_case(case(instruments=rows(loan, replace(loan, leg="baseline")), receipts=none()))

    def test_invariant_crossings_refund_grant_budget_and_null_columns(self):
        gross = cost(vat_representation="GROSS_ONLY", net=unknown(), vat=unknown())
        refund = grant(category="VAT_REFUND", amount=scalar(10000), receipt_id="vat1", event_id="vat1")
        a = audit_accounting(case(costs=rows(gross), receipts=rows(refund, replace(refund, receipt_id="vat2", event_id="vat2"))))
        self.assertIn("unfinanced_cash", a.unavailable)
        self.assertEqual(a.amounts["recurring_budget.programme"], 42000)
        partial = audit_accounting(case(receipts=rows(refund, replace(refund, receipt_id="vat2", event_id="vat2"))))
        self.assertEqual(partial.amounts["unfinanced_cash.programme"], -107000)
        operating = grant(category="OPERATING", receipt_id="operating", event_id="operating", amount=scalar(3000), cost_id=None)
        rent = resource("rent", category="REQUIRED_NON_ENERGY", amount=scalar(10000),
                        source_semantics="DISJOINT_REQUIRED_SPENDING", covered_categories=("RENT",))
        c = case(receipts=rows(grant(amount=unknown(), award_or_contract=qref()), operating),
                 resources=rows(resource(), resource(leg="baseline"), rent),
                 assets=rows(asset(terminal_kind="Q", terminal_value=unknown())))
        a = audit_accounting(c)
        self.assertEqual(a.amounts["recurring_budget.programme"], 35000)
        self.assertEqual(a.amounts["unfinanced_cash.programme"], -124000)
        self.assertTrue(all(r.bank is None and r.financed is None for r in a.rows))
        self.assertEqual(sum(r.recurring for r in a.rows if r.leg == "programme"), 35000)

    def test_invariant_crossings_nested_types_and_rate_q_domains(self):
        for invalid in (object(), [], {"gross": 1}, 3):
            with self.assertRaises(B12ContractError):
                validate_case(case(costs=rows(invalid)))
        loan = instrument()
        for definition in ("ZERO", "SUPPLIED_PERIODIC_OPENING", "EXTERNAL_ACCRUAL_Q"):
            for rate in (scalar(0, "HUF"), unknown("HUF")):
                with self.assertRaises(B12ContractError):
                    bad = replace(loan.rows.rows[0], accrual_rate=rate)
                    validate_case(case(instruments=rows(replace(loan, interest_definition=definition,
                                                               rows=rows(bad, *loan.rows.rows[1:])))))
        q = replace(loan.rows.rows[0], accrual_rate=unknown("ratio"))
        a = audit_accounting(case(instruments=rows(replace(loan, rows=rows(q, *loan.rows.rows[1:])))))
        self.assertIn("financed_cash", a.unavailable)
        with self.assertRaises(B12ContractError):
            Section("Q", (), ref(), ())
        with self.assertRaises(B12ContractError):
            Section("ROWS", (loan,), qref(), ())

    def test_invariant_crossings_refinancing_and_terminal_replacement(self):
        loan = instrument()
        maturity = day(12, 31)
        old = replace(loan, rows=rows(*loan.rows.rows[:2], debt("old-balloon", maturity, 28500, 0, 28500, 0)))
        new = instrument(instrument_id="refinance", start=END, maturity=date(2027, 12, 31),
                         rows=rows(debt("refinance-draw", maturity, 0, 28500, 0, 28500)))
        a = audit_accounting(case(instruments=rows(old, new)))
        self.assertEqual(a.amounts["outstanding_debt.programme.loan"], 0)
        self.assertEqual(a.amounts["outstanding_debt.programme.refinance"], 28500)
        self.assertEqual(a.amounts["financed_cash.programme"], -79500)
        self.assertEqual(next(v for l, _, v in reversed(a.liquidity) if l == "programme"), 80500)
        first = asset(replacement_cost_ids=rows("replacement"))
        second = asset("hp2", retired_generation_id="hp1", commissioning_date=date(2026, 10, 1),
                       terminal_kind="CASH_SALE", terminal_value=scalar(30000), terminal_receipt_id="sale")
        replacement_cost = cost("replacement", category="REPLACEMENT", asset_generation_id="hp2", period=day(9))
        sale = grant(category="SALE", receipt_id="sale", event_id="sale", amount=scalar(30000),
                     asset_generation_id="hp2", cost_id=None, period=day(12, 31))
        c = case(costs=rows(cost(), replacement_cost), assets=rows(first, second), receipts=rows(sale))
        self.assertEqual(audit_accounting(c).amounts["unfinanced_cash.programme"], -224000)
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, receipts=rows(replace(sale, category="OPERATING"))))

    def test_invariant_crossings_b04_boundaries_and_context(self):
        period = Period(date(2026, 7, 1), date(2026, 7, 31))
        outside = price_h_outside(100, 100, 1, "MVM Démász", period.start, period.end,
                                  load_scope="ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES", connection_scope="PROFILED_LOW_VOLTAGE")
        template = bill()
        context = {f.name: getattr(template, f.name) for f in fields(template)
                   if f.name not in {"consumption_gross", "fixed_gross", "total_gross", "upstream_status", "upstream_price_basis", "upstream_source_ids"}}
        context.update(product="H_OUTSIDE", service_period=period, period=day(8), tariff_load_scope="ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES")
        h = BillInput.from_b04(outside, consumption_gross=scalar(outside.consumption_charge_huf),
                              fixed_gross=scalar(outside.fixed_charge_huf), total_gross=scalar(outside.total_huf), **context)
        validate_case(case(bills=rows(h, replace(h, leg="baseline"))))
        # Moving cash settlement does not alter the service-season authority.
        validate_case(case(bills=rows(replace(h, period=day(9)), replace(h, leg="baseline", period=day(10)))))
        # Equal zero amounts do not authorize a different producer context.
        zero = bill(quantity=scalar(0, "kWh"), discounted_allocation=scalar(0, "kWh"), billed_months=scalar(0, "month"))
        with self.assertRaises(B12ContractError):
            validate_case(case(bills=rows(replace(zero, product="H", service_period=period,
                                                  tariff_load_scope="ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES"))))
        # The exact heating/outside boundary remains available through upstream rules.
        heating_edge = bill(product="H", tariff_load_scope="ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES",
                            service_period=Period(date(2026, 4, 1), date(2026, 4, 15)), billed_months=scalar("0.5", "month"))
        validate_case(case(bills=rows(heating_edge, replace(heating_edge, leg="baseline"))))
        edge_period = Period(date(2026, 4, 16), date(2026, 4, 30))
        edge_raw = price_h_outside(100, 100, Decimal("0.5"), "MVM Démász", edge_period.start, edge_period.end,
                                   load_scope=h.tariff_load_scope, connection_scope=h.tariff_connection_scope)
        context.update(service_period=edge_period, billed_months=scalar("0.5", "month"))
        edge = BillInput.from_b04(edge_raw, consumption_gross=scalar(edge_raw.consumption_charge_huf),
                                 fixed_gross=scalar(edge_raw.fixed_charge_huf), total_gross=scalar(edge_raw.total_huf), **context)
        validate_case(case(bills=rows(edge, replace(edge, leg="baseline"))))
        for bad in (replace(h, product="H"), replace(h, tariff_connection_scope="SMART_METER_UNSUPPORTED"),
                    replace(h, billed_months=scalar(2, "month")), replace(h, upstream_source_ids=())):
            with self.assertRaises(B12ContractError):
                validate_case(case(bills=rows(bad)))

    def test_review_r12_policy_money_dimensions_without_floor_defaults(self):
        c = case()
        for field in ("floor_value", "reserve"):
            for bad in (scalar(5, "kWh"), scalar(5, basis="EUR_REAL_2023"),
                        unknown("kWh"), unknown(basis="EUR_REAL_2023")):
                with self.subTest(field=field, bad=bad), self.assertRaises(B12ContractError):
                    validate_case(replace(c, policy=replace(c.policy, **{field: bad})))
        for value in (scalar(-5), scalar(0), scalar(5), unknown()):
            validate_case(replace(c, policy=replace(c.policy, floor_value=value)))
        for value in (scalar(0), scalar(5), unknown()):
            validate_case(replace(c, policy=replace(c.policy, reserve=value)))
        with self.assertRaises(B12ContractError):
            validate_case(replace(c, policy=replace(c.policy, reserve=scalar(-5))))
        assessment = assess_readiness(replace(c, policy=replace(c.policy, floor_value=scalar(-5), reserve=scalar(0))))
        self.assertIn("case.policy.floor_metric", assessment["affordability"])
        self.assertIn("affordability consumer not implemented", assessment["affordability"])

    def test_review_r13_unknown_overlapping_fee_is_q_not_proven_duplicate(self):
        b = bill()
        partial = replace(b, bill_id="DHW-partial", event_id="DHW-partial", end_use="DHW", fixed_charge_key="DHW-fee",
                          fixed_gross=unknown(), total_gross=unknown(), upstream_status="Q_TARIFF_HANDOFF")
        for key in ("DHW-fee", b.fixed_charge_key):
            for fee in (unknown(), scalar(0)):
                extra = replace(partial, fixed_charge_key=key, fixed_gross=fee, period=day(3))
                c = case(bills=rows(b, extra, replace(b, leg="baseline"), replace(extra, leg="baseline")))
                self.assertEqual(validate_case(c).structural_status, "VALID")
                a = audit_accounting(c)
                self.assertIn("retail_bills", a.unavailable)
                self.assertIn("case.bills.rows[1].total_gross", a.unavailable["retail_bills"])
                self.assertEqual(a.amounts["total_initial_cost.programme"], 127000)
                self.assertTrue(all(r.bank is None and r.recurring is None for r in a.rows))
                if fee.truth == "Q":
                    self.assertIn("case.bills.rows[1].fixed_gross", a.unavailable["retail_bills"])
        positive = replace(partial, fixed_gross=scalar(1), total_gross=scalar(partial.consumption_gross.value + 1))
        with self.assertRaises(B12ContractError):
            validate_case(case(bills=rows(b, positive, replace(b, leg="baseline"), replace(positive, leg="baseline"))))
        zero = replace(partial, fixed_gross=scalar(0), total_gross=partial.consumption_gross)
        self.assertEqual(assess_readiness(case(bills=rows(b, zero, replace(b, leg="baseline"), replace(zero, leg="baseline"))))["retail_bills"], ())

    def test_review_r14_b04_native_huf_cannot_be_retagged_as_eur(self):
        b = bill()
        upstream = price_a1(100, 100, 1, "MVM Démász")
        context = {f.name: getattr(b, f.name) for f in fields(b)
                   if f.name not in {"consumption_gross", "fixed_gross", "total_gross", "upstream_status", "upstream_price_basis", "upstream_source_ids"}}
        with self.assertRaisesRegex(B12ContractError, "native HUF"):
            BillInput.from_b04(upstream, consumption_gross=replace(b.consumption_gross, unit="EUR"),
                              fixed_gross=replace(b.fixed_gross, unit="EUR"), total_gross=replace(b.total_gross, unit="EUR"), **context)
        def retag(obj):
            if isinstance(obj, Scalar):
                return replace(obj, unit="EUR" if obj.unit == "HUF" else obj.unit, basis_id="EUR_NOMINAL_2026")
            if isinstance(obj, MoneyBasis):
                return replace(obj, currency="EUR", basis_id="EUR_NOMINAL_2026")
            if is_dataclass(obj):
                changes = {f.name: retag(getattr(obj, f.name)) for f in fields(obj)}
                if isinstance(obj, Valuation):
                    changes["basis_id"] = "EUR_NOMINAL_2026"
                return replace(obj, **changes)
            if isinstance(obj, tuple):
                return tuple(retag(x) for x in obj)
            return obj
        with self.assertRaisesRegex(B12ContractError, "native HUF"):
            audit_accounting(retag(case(bills=rows(b, replace(b, leg="baseline")))))
        # Independently specified EUR scenarios remain legal without a B04 handoff.
        plain_eur = audit_accounting(retag(case()))
        self.assertEqual(plain_eur.basis.currency, "EUR")
        self.assertEqual(plain_eur.amounts["financed_cash.programme"], -108000)
        self.assertEqual(audit_accounting(case(bills=rows(b, replace(b, leg="baseline")))).amounts["retail_bills.programme"], b.total_gross.value)

    def test_review_b04_native_price_anchor_cannot_be_relabelled(self):
        c = case(bills=rows(bill(), bill("baseline")))
        rebased = replace(c.monetary_basis, price_date=date(2024, 1, 1), convention=ref("rebased-to-2024"))
        with self.assertRaisesRegex(B12ContractError, "native monetary anchor"):
            audit_accounting(replace(c, monetary_basis=rebased))
        # An unrelated valid conversion identity does not bind/rebase these bills.
        basis2024 = MoneyBasis("HUF_NOMINAL_2024", "HUF", "NOMINAL", date(2024, 1, 1), ref("2024"))
        conversion = Conversion(scalar(100), scalar(80, basis=basis2024.basis_id), scalar("0.8", "ratio"), START, ref("deflator"))
        with self.assertRaisesRegex(B12ContractError, "native monetary anchor"):
            audit_accounting(replace(c, monetary_basis=rebased, other_bases=(basis2024,), conversions=(conversion,)))
        # Price basis and service/cash/evaluation dates are distinct.
        def future(obj):
            if isinstance(obj, (Scalar, MoneyBasis)):
                return obj
            if type(obj) is date:
                return obj.replace(year=obj.year + 1)
            if is_dataclass(obj):
                return replace(obj, **{f.name: future(getattr(obj, f.name)) for f in fields(obj)})
            if isinstance(obj, tuple):
                return tuple(future(x) for x in obj)
            return obj
        later = future(c)
        self.assertEqual(later.monetary_basis.price_date.year, 2026)
        self.assertEqual(later.bills.rows[0].service_period.start.year, 2027)
        self.assertEqual(audit_accounting(later).amounts["retail_bills.programme"], audit_accounting(c).amounts["retail_bills.programme"])
        # A declared 2024 scenario without B04 is outside this producer-specific rule.
        validate_case(replace(case(), monetary_basis=rebased))

    def test_b14_snapshot_remains_rules_and_b12_globals_remain_q(self):
        from modules.B14.funding_reference import load_funding_reference, AS_OF, PROGRAMME_417, SCOPES, DATED_RULE_REFERENCE
        catalog = load_funding_reference()
        rule = catalog.read_programme(PROGRAMME_417, scope=SCOPES[PROGRAMME_417], as_of=AS_OF, claim=DATED_RULE_REFERENCE)
        self.assertTrue(rule["unknowns"])
        with self.assertRaises(B12ContractError):
            validate_case(case(receipts=rows(grant(status="CONFIRMED"))))
        inventory = json.loads((ROOT / "registry/b12_input_inventory.json").read_text())
        self.assertEqual(inventory["numerical_output_status"], "Q")
        self.assertEqual(inventory["b15_gate"], "BLOCKED")
        self.assertEqual([r["admission_id"] for r in inventory["current_source_admissions"]], ["B06-WM50-MODELED-LIFE-E2-001"])
        self.assertFalse(inventory["current_source_admissions"][0]["numerical_b12_output_admitted"])
        self.assertTrue(all(row["value"] is None and row["status"] == "Q" for row in inventory["inputs"]))
        with (ROOT / "registry/variables.csv").open(newline="") as stream:
            variables = {row["variable_id"]: row for row in csv.DictReader(stream)}
        for variable in inventory["derived_global_handoffs"]:
            self.assertEqual(variables[variable]["status"], "Q")
            self.assertEqual(variables[variable]["default_value"], "")
        self.assertEqual(variables["VAR-B01-HORIZON-YEARS"]["default_value"], "15")
        self.assertEqual(variables["VAR-B01-CASH-FLOW-FLOOR"]["default_value"], "")
        for row in inventory["inputs"]:
            self.assertTrue(all((ROOT / path).exists() for path in row["upstream_authorities"]))



if __name__ == "__main__":
    unittest.main()
