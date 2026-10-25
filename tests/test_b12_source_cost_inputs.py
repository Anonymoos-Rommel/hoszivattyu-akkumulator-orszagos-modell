"""Fictional local contract witnesses, plus pinned real-source missingness checks.

TEST_ONLY records are not source admissions for the WM50 study. No target
quantity, equipment configuration or invoice is selected by these fixtures.
"""
import copy
from dataclasses import fields, is_dataclass, replace
from datetime import date
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from modules.B12.input_accounting_contract import (
    B12ContractError, Cost, MoneyBasis, Reference, Scalar, Section, SYNTHETIC,
    audit_accounting, validate_case,
)
from modules.B12.source_cost_inputs import (
    E2_CRITERIA, load_source_catalogue, resolve_cost_inputs,
    normalization_input_revision, offer_evidence_revision,
)
from test_b12_input_accounting_contract import case, missing

PACKAGE = Path(__file__).resolve().parents[1]
BASIS = MoneyBasis("HUF_NOMINAL_2026", "HUF", "NOMINAL", date(2026, 10, 21),
                   Reference("EXTERNAL_ADMISSION", "TEST_ONLY:nominal-snapshot", None, None))
TEST_CONTEXT = dict(case_id="TEST_ONLY:case", intervention_id="TEST_ONLY:intervention",
                    archetype_id="TEST_ONLY:archetype", region_id="TEST_ONLY:region",
                    transition_ref="S2_TO_S3", scope_id="household-scope",
                    household_id="synthetic-household", service_basis_ref="matched-weather-and-service")


class Fixture:
    """Every source, binding and review in this class is a test-only invention."""
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="b12-cost-witness-")
        self.root = Path(self.temp.name).resolve()
        self.fact = dict(source_id="TEST_ONLY:merchant", product="TEST_ONLY:outdoor", value="100.25",
                         unit="HUF/item", scope="EXACT_PRODUCT_PART_PRICE", tax="GROSS", price_kind="EXACT_PRICE")
        self.offer = dict(offer_id="TEST_ONLY:offer", source_id=self.fact["source_id"], family_id="TEST_ONLY:family",
                          product=self.fact["product"], category="INITIAL_CAPEX", function_ids=["TEST_ONLY:outdoor-function"],
                          inclusions=["outdoor"], value=self.fact["value"], amount_field="value", unit="HUF/item",
                          quantity_unit="item", basis_id="HUF_TEST_ONLY_OFFER", tax_basis="GROSS", price_kind="EXACT_PRICE",
                          original_price_kind="EXACT_PRICE",
                          use_scope=self.fact["scope"], scope_field="scope", reference_period=["2026-10-21", "2026-10-21"],
                          qualifier_pin=None)
        self.binding = dict(cost_id="TEST_ONLY:invoice", offer_id=self.offer["offer_id"], product=self.offer["product"],
                            event_id="TEST_ONLY:cash-event", scope_event_id="TEST_ONLY:purchase-1", leg="programme",
                            component_id="HP", asset_generation_id="hp1", phase_ref="S2_TO_S3", category="INITIAL_CAPEX",
                            quantity=dict(value="2", unit="item", truth="SCN", reference_period=["2026-10-21", "2026-10-21"],
                                          basis_id="TEST_ONLY:quantity", source_ids=[], scenario_ref="TEST_ONLY:quantity-two",
                                          evidence_tier="E3", admission_ref=None, reason=None, acquisition_ref=None),
                            scope_ref="household-scope", payer="synthetic-household", payee="TEST_ONLY:merchant",
                            settlement_ref="TEST_ONLY:whole-attributed-event", cash_period=["2026-10-22", "2026-10-22"],
                            service_period=None, inclusion_scope=["outdoor"], attribution_ref="TEST_ONLY:full-attribution",
                            price_basis_ref="TEST_ONLY:frozen-snapshot", applicability_ref="TEST_ONLY:scope-match",
                            review_id="TEST_ONLY:review")

    def write(self, name, value):
        p = self.root / name
        p.write_text(json.dumps(value), encoding="utf-8")
        return p

    def as_visit(self):
        self.fact.update(product="TEST_ONLY:maintenance", unit="HUF/visit", scope="GENERIC_MAINTENANCE_VISIT")
        self.offer.update(product=self.fact["product"], unit="HUF/visit", quantity_unit="visit",
                          use_scope=self.fact["scope"], category="O_AND_M", inclusions=["maintenance_visit"])
        self.binding.update(product=self.fact["product"], category="O_AND_M", inclusion_scope=["maintenance_visit"])
        self.binding["quantity"]["unit"] = "visit"

    def pin(self, name, value):
        p = self.write(name, value)
        return dict(path=name, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), pointer=[], expected=value)

    def build(self, bindings=None, *, qualified=True, review_change=None, offers=None):
        bindings = bindings or [self.binding]
        offer = copy.deepcopy(self.offer)
        offer["fact_pin"] = self.pin("fact.json", self.fact)
        offer["scope_pin"] = self.pin("scope.json", {"function_ids": offer["function_ids"]})
        offers = offers or [offer]
        for n, active in enumerate(offers):
            active["period_pin"] = self.pin(f"period-{n}.json", active["reference_period"][0])
            active["package_pin"] = self.pin(f"package-{n}.json", {"inclusions": active["inclusions"]})
            active["normalization_pin"] = self.pin(f"normalization-{n}.json", dict(
                input_revision=normalization_input_revision(active),
                normalized={k: active[k] for k in ("tax_basis", "price_kind", "reference_period", "inclusions")},
                qualification_pin=None))
        uses = []
        for n, b in enumerate(bindings):
            o = next(x for x in offers if x["offer_id"] == b["offer_id"])
            review = dict(review_id=b["review_id"], status="QUALIFIED" if qualified else "Q", binding=b,
                          offer_evidence_revision=offer_evidence_revision(o),
                          case_context=TEST_CONTEXT,
                          offer_id=b["offer_id"], source_id=o["source_id"], evidence_tier="E2",
                          monetary_basis=dict(basis_id=BASIS.basis_id, currency="HUF", nominal_real="NOMINAL", price_date="2026-10-21"),
                          service_scope="SPACE_HEATING_ONLY", function_ids=o["function_ids"],
                          price_use="EXPLICIT_FROZEN_SOURCE_SNAPSHOT_NOT_REAL_INVOICE", known_stronger_contradiction=False,
                          criteria={k: f"TEST_ONLY:fixture evidence for {k}" for k in E2_CRITERIA},
                          validation_debt=["TEST_ONLY:unverified installation, not a real source"],
                          evidence_pins=[o["fact_pin"]], binding_evidence_pin=self.pin(f"binding-{n}.json", b))
            if review_change: review_change(review)
            uses.append(review)
        payload = dict(schema_version=2, offers=offers, use_reviews_pin=self.pin("reviews.json", uses))
        manifest = self.write("catalogue.json", payload)
        return load_source_catalogue(self.root, manifest.name, expected_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest())


def external_shape(value):
    """Keep fictional SCN lineage explicit while exercising the external path."""
    if isinstance(value, Reference) and value.kind == SYNTHETIC:
        return Reference("EXTERNAL_ADMISSION", "TEST_ONLY:" + value.ref, None, None)
    if isinstance(value, Scalar) and value.scenario_ref:
        return replace(value, scenario_ref="TEST_ONLY:" + value.scenario_ref)
    if is_dataclass(value):
        return replace(value, **{f.name: external_shape(getattr(value, f.name)) for f in fields(value)})
    if isinstance(value, tuple): return tuple(external_shape(x) for x in value)
    return value


class SourceCostInputTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.temp.cleanup)

    def result(self, *, bindings=None, **kwargs):
        b = tuple(bindings or [self.f.binding])
        return resolve_cost_inputs(self.f.build(list(b), **kwargs), b, BASIS, case_context=TEST_CONTEXT)

    def test_qualified_source_quantity_becomes_native_cost_without_vat_invention(self):
        r = self.result()
        c = r.costs[0]
        self.assertIs(type(c), Cost)
        self.assertEqual(c.gross.value, Decimal("200.50"))
        self.assertEqual(c.gross.truth, "SCN")
        self.assertEqual(c.quantity.value, 2)
        self.assertEqual((c.net.truth, c.vat.truth, c.eligible_gross.truth), ("Q", "Q", "Q"))
        self.assertIsNone(r.full_capex)

    def test_reproducible_decimal_product_ignores_ambient_precision(self):
        with localcontext() as ctx:
            ctx.prec = 2
            self.assertEqual(self.result().costs[0].gross.value, Decimal("200.50"))

    def test_unknown_quantity_keeps_price_observation_but_no_cost(self):
        q = self.f.binding["quantity"]
        q.update(value=None, truth="Q", source_ids=[], scenario_ref=None, evidence_tier=None,
                 admission_ref=None, reason="not selected", acquisition_ref="B12-D01")
        r = self.result(qualified=False)
        self.assertEqual(r.observations[0].price.value, Decimal("100.25"))
        self.assertFalse(r.costs)
        self.assertTrue(any(x.path.endswith("quantity") for x in r.missing))

    def test_unknown_target_cash_date_is_not_retrieval_day(self):
        self.f.binding["cash_period"] = None
        r = self.result(qualified=False)
        self.assertFalse(r.costs)
        self.assertTrue(any(x.path.endswith("cash_period") for x in r.missing))

    def test_offer_or_admission_identifier_alone_never_authorizes_cost(self):
        self.assertFalse(self.result(qualified=False).costs)
        c = self.f.build()
        b = copy.deepcopy(self.f.binding);b["review_id"] = "unresolved-ref"
        self.assertFalse(resolve_cost_inputs(c, (b,), BASIS, case_context=TEST_CONTEXT).costs)

    def test_binding_cannot_reuse_review_for_other_quantity(self):
        c = self.f.build()
        b = copy.deepcopy(self.f.binding);b["quantity"]["value"] = "3"
        with self.assertRaisesRegex(B12ContractError, "binding changed"):
            resolve_cost_inputs(c, (b,), BASIS, case_context=TEST_CONTEXT)

    def test_071_price_cannot_become_072_price(self):
        self.f.binding["product"] = "PAC-IF072B-E"
        with self.assertRaisesRegex(B12ContractError, "product mismatch"):
            self.result()

    def test_unit_denominator_mismatch_rejected(self):
        self.f.binding["quantity"]["unit"] = "visit"
        with self.assertRaisesRegex(B12ContractError, "denominator"):
            self.result()

    def test_unknown_tax_and_localization_caveat_remain_q(self):
        for tax in ["Q_NOT_EXPLICITLY_SEPARATED", "VAT_INCLUDED_GENERAL_TERMS_WITH_CURRENCY_LOCALIZATION_CAVEAT"]:
            with self.subTest(tax=tax):
                self.f.offer["tax_basis"] = tax
                self.f.fact["tax"] = tax
                r = self.result()
                self.assertFalse(r.costs)
                self.assertTrue(any(m.path.endswith("tax_basis") for m in r.missing))

    def test_starting_minimum_indicative_or_policy_price_not_exact(self):
        for kind in ["STARTING_FROM", "MINIMUM_FEE", "INDICATIVE", "POLICY_CAP"]:
            with self.subTest(kind=kind):
                self.f.offer["price_kind"] = kind
                self.f.offer["original_price_kind"] = self.f.fact["price_kind"] = kind
                self.assertFalse(self.result().costs)

    def test_comparison_scope_cannot_be_silently_promoted(self):
        self.f.fact["scope"] = self.f.offer["use_scope"] = "COMPARISON_ONLY"
        self.assertFalse(self.result().costs)

    def test_maintenance_not_installation(self):
        self.f.offer["category"] = "O_AND_M"
        self.f.binding["category"] = "INITIAL_CAPEX"
        with self.assertRaisesRegex(B12ContractError, "category mismatch"):
            self.result()

    def test_maintenance_fee_without_service_period_not_annualized(self):
        self.f.as_visit()
        self.assertFalse(self.result().costs)

    def test_named_visit_is_separate_om_event_not_capex(self):
        self.f.as_visit()
        self.f.binding["service_period"] = ["2026-10-22", "2026-10-22"]
        c = self.result().costs[0]
        self.assertEqual(c.category, "O_AND_M")
        self.assertEqual(c.period.start, date(2026, 10, 22))

    def test_all_eight_e2_criteria_and_debt_required(self):
        for criterion in E2_CRITERIA:
            def change(r, key=criterion): r["criteria"][key] = ""
            with self.subTest(criterion=criterion), self.assertRaises(B12ContractError):
                self.result(review_change=change)
        with self.assertRaises(B12ContractError):
            self.result(review_change=lambda r:r.update(validation_debt=[]))

    def test_e3_and_contradictory_or_other_service_review_rejected(self):
        for change in [lambda r:r.update(evidence_tier="E3"), lambda r:r.update(known_stronger_contradiction=True),
                       lambda r:r.update(service_scope="HEATING_AND_DHW"),
                       lambda r:r.update(price_use="OBSERVED_PAID_INVOICE")]:
            with self.subTest(change=change), self.assertRaises(B12ContractError):
                self.result(review_change=change)

    def test_changed_pinned_source_or_manifest_detected_before_reuse(self):
        for filename in ["fact.json", "catalogue.json", "reviews.json", "binding-0.json"]:
            c = self.f.build()
            (self.f.root/filename).write_text("{}", encoding="utf-8")
            with self.subTest(file=filename), self.assertRaises(B12ContractError):
                resolve_cost_inputs(c, (self.f.binding,), BASIS, case_context=TEST_CONTEXT)

    def test_money_currency_price_date_and_nominal_basis_cannot_be_retagged(self):
        c = self.f.build()
        for basis in [replace(BASIS, currency="EUR"), replace(BASIS, price_date=date(2024, 1, 1)),
                      replace(BASIS, basis_id="other"), replace(BASIS, nominal_real="REAL")]:
            with self.subTest(basis=basis), self.assertRaises(B12ContractError):
                resolve_cost_inputs(c, (self.f.binding,), basis, case_context=TEST_CONTEXT)

    def test_unselected_basis_stays_q(self):
        self.assertFalse(resolve_cost_inputs(self.f.build(), (self.f.binding,), None).costs)

    def test_zero_negative_bool_float_and_nonfinite_quantities_rejected(self):
        for value in ["0", "-1", True, 1.1, "NaN", "Infinity"]:
            self.f.binding["quantity"]["value"] = value
            with self.subTest(value=value), self.assertRaises(B12ContractError): self.result()

    def test_bundle_inclusions_cannot_be_dropped(self):
        self.f.offer["inclusions"] = ["outdoor", "pump", "controller"]
        with self.assertRaisesRegex(B12ContractError, "inclusions"):
            self.result()

    def test_duplicate_binding_and_economic_event_rejected(self):
        with self.assertRaisesRegex(B12ContractError, "duplicate"):
            self.result(bindings=[self.f.binding, self.f.binding])
        b = copy.deepcopy(self.f.binding);b.update(cost_id="TEST_ONLY:second", review_id="TEST_ONLY:review2")
        with self.assertRaisesRegex(B12ContractError, "duplicate economic event"):
            self.result(bindings=[self.f.binding, b])

    def test_duplicate_purchase_not_hidden_by_changed_cash_date(self):
        b = copy.deepcopy(self.f.binding)
        b.update(cost_id="TEST_ONLY:second", event_id="TEST_ONLY:cash2", review_id="TEST_ONLY:review2",
                 cash_period=["2026-10-23", "2026-10-23"])
        with self.assertRaisesRegex(B12ContractError, "counted twice"):
            self.result(bindings=[self.f.binding, b])

    def test_bundle_and_separate_pump_from_other_source_overlap(self):
        self.f.offer["inclusions"] = self.f.binding["inclusion_scope"] = ["outdoor", "pump"]
        first = copy.deepcopy(self.f.offer)
        first["fact_pin"] = self.f.pin("fact.json", self.f.fact)
        first["scope_pin"] = self.f.pin("scope.json", {"function_ids": first["function_ids"]})
        pump_fact = dict(source_id="TEST_ONLY:pump-source", product="TEST_ONLY:pump", value="25", unit="HUF/item", scope="EXACT_PRODUCT_PART_PRICE", tax="GROSS", price_kind="EXACT_PRICE")
        pump = copy.deepcopy(first)
        pump.update(offer_id="TEST_ONLY:pump-offer", source_id=pump_fact["source_id"], family_id="TEST_ONLY:pump-family",
                    product=pump_fact["product"], value="25", inclusions=["pump"], fact_pin=self.f.pin("pump.json", pump_fact))
        b = copy.deepcopy(self.f.binding)
        b.update(cost_id="TEST_ONLY:pump-invoice", event_id="TEST_ONLY:pump-cash", review_id="TEST_ONLY:pump-review",
                 offer_id=pump["offer_id"], product=pump_fact["product"], inclusion_scope=["pump"],
                 cash_period=["2026-10-23", "2026-10-23"])
        with self.assertRaisesRegex(B12ContractError, "bundle/component overlap"):
            self.result(bindings=[self.f.binding, b], offers=[first, pump])

    def test_distinct_evidenced_visits_are_not_duplicate_or_annual_default(self):
        self.f.as_visit()
        self.f.binding["service_period"] = ["2026-10-22", "2026-10-22"]
        b = copy.deepcopy(self.f.binding)
        b.update(cost_id="TEST_ONLY:visit2", event_id="TEST_ONLY:cash2", review_id="TEST_ONLY:review2",
                 scope_event_id="TEST_ONLY:service-2", cash_period=["2026-11-22", "2026-11-22"],
                 service_period=["2026-11-22", "2026-11-22"])
        self.assertEqual(len(self.result(bindings=[self.f.binding, b]).costs), 2)

    def test_unknown_price_survives_as_q_not_zero(self):
        self.f.fact["value"] = self.f.offer["value"] = None
        r = self.result(qualified=False)
        self.assertIsNone(r.observations[0].price.value)
        self.assertEqual(r.observations[0].price.truth, "Q")
        self.assertFalse(r.costs)

    def test_native_consumer_exposes_only_qualified_subset_with_income_om_q(self):
        catalogue = self.f.build()
        cost = resolve_cost_inputs(catalogue, (self.f.binding,), BASIS, case_context=TEST_CONTEXT).costs[0]
        c = external_shape(case())
        c = replace(c, mode="CONDITIONAL_CASE", monetary_basis=BASIS, resources=missing(),
                    case_id=TEST_CONTEXT["case_id"], intervention_id=TEST_CONTEXT["intervention_id"],
                    archetype_id=TEST_CONTEXT["archetype_id"], region_id=TEST_CONTEXT["region_id"],
                    receipts=missing(), instruments=missing(), liquid_assets=missing(),
                    assets=replace(c.assets, rows=(replace(c.assets.rows[0],
                        operating_coverage=Reference("Q", None, "O&M coverage Q", "B12-D01")),)),
                    costs=Section("ROWS", (cost,), Reference("EXTERNAL_ADMISSION", "TEST_ONLY:costs", None, None), ("baseline",)))
        validate_case(c)
        audit = audit_accounting(c, source_catalogue=catalogue, cost_bindings=(self.f.binding,))
        self.assertEqual(audit.source_costs, (cost,))
        self.assertEqual(audit.amounts["qualified_initial_cost_subset.programme"], Decimal("200.50"))
        self.assertNotIn("total_initial_cost.programme", audit.amounts)
        self.assertNotIn("financed_cash.programme", audit.amounts)
        self.assertEqual(audit.truth, "Q")
        self.assertEqual(audit.rows, ())
        self.assertTrue(audit.unavailable["total_initial_cost"])
        self.assertTrue(audit.unavailable["recurring_budget"])
        # No matching Cost may be claimed merely by providing a resolution request.
        with self.assertRaisesRegex(B12ContractError, "actual native case input"):
            audit_accounting(replace(c, costs=Section("Q", (), Reference("Q", None, "cost Q", "B12-D01"), ())),
                             source_catalogue=catalogue, cost_bindings=(self.f.binding,))
        self.assertFalse(audit_accounting(c).amounts)
        with self.assertRaisesRegex(B12ContractError, "case context changed"):
            audit_accounting(replace(c, archetype_id="TEST_ONLY:other-archetype"),
                             source_catalogue=catalogue, cost_bindings=(self.f.binding,))

    def test_synthetic_case_cannot_use_external_source_resolver(self):
        with self.assertRaisesRegex(B12ContractError, "synthetic witnesses"):
            audit_accounting(case(), source_catalogue=self.f.build(), cost_bindings=(self.f.binding,))

    def test_real_source_packages_preserve_prices_and_all_target_gaps(self):
        path = PACKAGE/"data/processed/b12/source_catalogue.json"
        catalogue = load_source_catalogue(PACKAGE, str(path.relative_to(PACKAGE)), expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        bindings = json.loads((path.parent/"unresolved_target_bindings.json").read_text(encoding="utf-8"))["bindings"]
        r = resolve_cost_inputs(catalogue, tuple(bindings), None)
        facts = {x.offer_id:x for x in r.observations}
        self.assertEqual(facts["OUTDOOR_GROSS"].price.value, Decimal("1220781"))
        self.assertEqual(facts["CONTROLLER_GROSS"].price.value, Decimal("462772"))
        self.assertIsNone(facts["Q-072-HU"].price.value)
        self.assertEqual(facts["OBS-FS01-GROUPSUMI-HU"].price.value, Decimal("51991.15"))
        self.assertEqual(facts["PUMP_SHIPPING_COMPARISON"].tax_basis, "Q_NOT_EXPLICITLY_SEPARATED")
        self.assertFalse(r.costs)
        self.assertIsNone(r.full_capex)
        self.assertTrue(r.missing)


if __name__ == "__main__":
    unittest.main()
