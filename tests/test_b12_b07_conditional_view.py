"""TEST_ONLY conditional witnesses: no real B07 lifecycle or price adoption.

Every numerical fixture below is inherited from the existing synthetic contract
tests. Patching the production-empty review allowlist is test-only; this suite
does not qualify a dossier, source, lifecycle assumption or household result.
"""
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from modules.B12 import input_accounting_contract as native
from modules.B12 import source_cost_inputs as source
from test_b12_input_accounting_contract import case, none, unknown, bill, grant
from test_b12_source_cost_inputs import Fixture as CostFixture, BASIS as COST_BASIS, TEST_CONTEXT

ROOT = Path(__file__).resolve().parents[1]
PRODUCERS = ("modules/B12/input_accounting_contract.py",
             "modules/B12/source_cost_inputs.py", "modules/B04/engine.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReviewedFixture:
    """Fictional evidence sealed only by a TEST_ONLY mocked code allowlist."""
    def __init__(self, case_input):
        self.temp = tempfile.TemporaryDirectory(prefix="b07-reviewed-test-only-")
        self.root = Path(self.temp.name)
        self.case = case_input
        self.review = dict(schema="B07_CONDITIONAL_USE_V1", review_id="TEST_ONLY:B07-review",
                           status="QUALIFIED", mode="CONDITIONAL_CASE", scope="B07_BATTERY_ONLY",
                           outputs=["gross_asset_cost"],
                           producer_pins={}, leaf_evidence=[],
                           scope_coverage=dict(complete_nonenergy_costs=True, receipt_free=True,
                                               battery_components=["BATTERY"]),
                           intervals=[dict(leg=a.leg, component_id=a.component_id,
                                           asset_generation_id=a.asset_generation_id,
                                           start=a.commissioning_date.isoformat(),
                                           end_exclusive=(a.operating_coverage_end + timedelta(days=1)).isoformat(),
                                           order=i) for i, a in enumerate(case_input.assets.rows)],
                           operations=[])
        for name in PRODUCERS:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
            self.review["producer_pins"][name] = sha(path)
        self.review["case_pin"] = self.pin("case.json", native.b07_case_payload(case_input))
        self.prove_all()

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        return path

    def pin(self, name, data):
        path = self.write(name, data)
        return dict(path=name, sha256=sha(path))

    def prove_all(self):
        self.review["leaf_evidence"] = []
        for i, (path, value) in enumerate(native._walk(self.case)):
            if isinstance(value, native.Scalar) and value.truth == "Q":
                continue
            if isinstance(value, native.Reference) and value.kind == "Q":
                continue
            proof = dict(case_id=self.case.case_id, input_path=path,
                         value=native.b07_case_payload(value),
                         authority="OWNER_SCENARIO" if isinstance(value, native.Scalar) else "REVIEWED_USE")
            self.review["leaf_evidence"].append(dict(input_path=path, pin=self.pin(f"proof/{i}.json", proof)))

    def seal(self):
        path = self.write("review.json", self.review)
        return {self.review["review_id"]: sha(path)}

    def audit(self, case_input=None):
        with patch.object(native, "B07_REVIEW_PINS", self.seal()):
            return native.audit_accounting(self.case if case_input is None else case_input,
                b07_use=native.B07Use(self.root, "review.json"))

    def close(self):
        self.temp.cleanup()


def external_value(value):
    """Convert fixture provenance without treating fixture numbers as sources."""
    if isinstance(value, native.Reference):
        if value.kind == "Q":
            return value
        return native.Reference("EXTERNAL_ADMISSION", "TEST_ONLY:use-review", None, None)
    if isinstance(value, native.Scalar):
        if value.truth == "Q":
            return value
        return replace(value, truth="SCN", source_ids=(), evidence_tier="E3",
                       scenario_ref="TEST_ONLY:explicit-parameter",
                       admission_ref=None)
    if is_dataclass(value):
        return replace(value, **{f.name: external_value(getattr(value, f.name)) for f in fields(value)})
    if isinstance(value, tuple):
        return tuple(external_value(item) for item in value)
    return value


def external_case(**changes):
    """Keep all numbers TEST_ONLY; changes may supply reviewed-shape fixtures."""
    result = external_value(case(instruments=none(), receipts=none(), resources=none(), liquid_assets=none()))
    result = replace(result, case_id="TEST_ONLY:B07-conditional", mode="CONDITIONAL_CASE",
                     intervention_id="TEST_ONLY:B07-intervention",
                     archetype_id="TEST_ONLY:archetype", region_id="TEST_ONLY:region",
                     population=replace(result.population, evidence_class="Q"),
                     assets=replace(result.assets, rows=tuple(replace(a, component_id="BATTERY") for a in result.assets.rows)),
                     costs=replace(result.costs, rows=tuple(replace(c, component_id="BATTERY", procurement_basis="PROCUREMENT") for c in result.costs.rows)))
    return replace(result, **changes)


def replacement_case(cut=date(2026, 7, 1)):
    """TEST_ONLY two-generation witness, never a selected replacement year."""
    original = external_case()
    first = original.assets.rows[0]
    first = replace(first, operating_coverage_end=cut - timedelta(days=1),
                    replacement_cost_ids=native.Section("ROWS", ("TEST_ONLY:replacement-cost",),
                                                       first.replacement_cost_ids.authority, ()))
    second = replace(first, asset_generation_id="TEST_ONLY:battery-generation-2",
                     commissioning_date=cut, operating_coverage_end=original.evaluation_period.end,
                     retired_generation_id=first.asset_generation_id,
                     replacement_cost_ids=original.assets.rows[0].replacement_cost_ids)
    replacement = replace(original.costs.rows[0], cost_id="TEST_ONLY:replacement-cost",
                          event_id="TEST_ONLY:replacement-event", category="REPLACEMENT",
                          asset_generation_id=second.asset_generation_id,
                          period=native.Period(cut, cut))
    return replace(original, assets=replace(original.assets, rows=(first, second)),
                   costs=replace(original.costs, rows=original.costs.rows + (replacement,)))


class B07ConditionalBoundaryTests(unittest.TestCase):
    def fixture(self, case_input=None):
        result = ReviewedFixture(external_case() if case_input is None else case_input)
        self.addCleanup(result.close)
        return result

    def cash_fixture(self, split=False):
        c = external_case()
        baseline = replace(c.assets.rows[0], leg="baseline")
        c = replace(c, assets=replace(c.assets, rows=(baseline,) + c.assets.rows, absent_legs=()))
        end = c.evaluation_period.end + timedelta(days=1)
        boundaries = [c.evaluation_period.start, date(2026, 7, 1), end] if split else [c.evaluation_period.start, end]
        bills = []
        for leg in native.LEGS:
            for n, (start, stop) in enumerate(zip(boundaries, boundaries[1:])):
                row = external_value(bill(leg, bill_id=f"TEST_ONLY:{leg}-bill-{n}",
                                          event_id=f"TEST_ONLY:{leg}-bill-event-{n}",
                                          service_period=native.Period(start, stop - timedelta(days=1)),
                                          period=native.Period(start, start),
                                          fixed_charge_key=f"TEST_ONLY:{leg}-meter-{n}"))
                bills.append(row)
        c = replace(c, bills=native.Section("ROWS", tuple(bills), c.bills.authority, ()))
        f = self.fixture(c)
        f.review["outputs"].append("unfinanced_cash")
        for leg in native.LEGS:
            for n, (start, stop) in enumerate(zip(boundaries, boundaries[1:])):
                identity = f"TEST_ONLY:{leg}-operation-{n}"
                bill_id = f"TEST_ONLY:{leg}-bill-{n}"
                source_bill = next(row for row in bills if row.bill_id == bill_id)
                ref = f.pin(f"energy/{leg}-{n}.json", {"opening": "2", "closing": "3",
                             "meter_quantities": {bill_id: str(source_bill.quantity.value)}})
                data = dict(case_id=c.case_id, id=identity, leg=leg, component_id="BATTERY",
                            asset_generation_id="hp1", coordinate="kWh_DC_discharge_equivalent",
                            opening="2", closing="3", reference_pin=ref,
                            reference_fields={"opening": ["opening"], "closing": ["closing"]},
                            application="EXPLICIT_REVIEWED_TARGET_PERIOD", start=start.isoformat(),
                            end_exclusive=stop.isoformat(), bill_ids=[bill_id], bill_bindings={bill_id: {
                                "physical_ref": source_bill.physical_ref,
                                "quantity": native.b07_case_payload(source_bill.quantity),
                                "source_quantity_pointer": ["meter_quantities", bill_id]}})
                f.review["operations"].append(f.pin(f"operation/{leg}-{n}.json", data))
        return f

    def rewrite_operation(self, f, index, change):
        pin = f.review["operations"][index]
        data = json.loads((f.root / pin["path"]).read_text(encoding="utf-8"))
        change(data)
        f.review["operations"][index] = f.pin(pin["path"], data)
        return data

    def test_no_opt_in_retains_generic_external_q(self):
        result = native.audit_accounting(external_case())
        self.assertEqual(result.truth, "Q")
        self.assertEqual(result.rows, ())
        self.assertEqual(dict(result.amounts), {})
        self.assertIsNone(result.b07_view)
        self.assertTrue(any(native.EXTERNAL_Q in deps for deps in result.unavailable.values()))

    def test_missing_review_is_incomplete_without_numerical_output(self):
        with tempfile.TemporaryDirectory(prefix="b07-test-only-") as folder:
            result = native.audit_accounting(external_case(), b07_use=native.B07Use(Path(folder), None))
        self.assertEqual(result.truth, "Q")
        self.assertEqual(result.rows, ())
        self.assertEqual(dict(result.amounts), {})
        self.assertEqual(result.b07_view.status, "INCOMPLETE")
        self.assertTrue(result.b07_view.missing)
        self.assertFalse(any(value is not None for value in result.b07_view.amounts.values()))
        self.assertEqual(result.b07_view.rows, ())
        self.assertEqual(result.b07_view.inventory, ())

    def test_only_conditional_mode_may_request_the_new_view(self):
        with tempfile.TemporaryDirectory(prefix="b07-test-only-") as folder:
            use = native.B07Use(Path(folder), None)
            for mode in ("INDIVIDUAL_RECORD", "POPULATION_ESTIMATE"):
                with self.subTest(mode=mode), self.assertRaises(native.B12ContractError):
                    native.audit_accounting(external_case(mode=mode), b07_use=use)
            with self.assertRaises(native.B12ContractError):
                native.audit_accounting(case(), b07_use=use)

    def test_test_only_qualified_cost_view_does_not_open_full_audit(self):
        result = self.fixture().audit()
        self.assertEqual(result.truth, "Q")
        self.assertEqual(result.rows, ())
        self.assertEqual(dict(result.amounts), {})
        view = result.b07_view
        self.assertEqual(view.status, "READY_SCN")
        self.assertEqual(view.truth, "SCN")
        self.assertEqual(dict(view.amounts), {
            "gross_asset_cost.baseline": Decimal(0),
            "gross_asset_cost.programme": Decimal(127000),
            "gross_asset_cost.incremental": Decimal(127000),
        })
        self.assertTrue(view.provenance)
        self.assertFalse(view.missing)
        for row in view.rows:
            self.assertIsNone(row.financed)
            self.assertIsNone(row.bank)
            self.assertIsNone(row.recurring)
        self.assertTrue(any(native.EXTERNAL_Q in deps for deps in result.unavailable.values()))

    def test_unpinned_self_declared_review_is_rejected(self):
        f = self.fixture()
        f.seal()
        with self.assertRaises(native.B12ContractError):
            native.audit_accounting(f.case, b07_use=native.B07Use(f.root, "review.json"))

    def test_closed_output_allowlist(self):
        for output in ("financed_cash", "bank_liquidity", "valuation", "tax_split", "noncash_terminal"):
            with self.subTest(output=output):
                f = self.fixture()
                f.review["outputs"].append(output)
                with self.assertRaises(native.B12ContractError):
                    f.audit()

    def test_review_mode_and_scope_cannot_broaden_conditional_use(self):
        for field, value in (("mode", "INDIVIDUAL_RECORD"), ("scope", "WHOLE_HOUSEHOLD")):
            with self.subTest(field=field):
                f = self.fixture()
                f.review[field] = value
                with self.assertRaises(native.B12ContractError):
                    f.audit()

    def test_changed_actual_case_cannot_reuse_reviewed_snapshot(self):
        f = self.fixture()
        changed = replace(f.case, case_id="TEST_ONLY:different-case")
        with self.assertRaises(native.B12ContractError):
            f.audit(changed)

    def test_changed_case_evidence_bytes_are_rejected(self):
        f = self.fixture()
        (f.root / "case.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(native.B12ContractError):
            f.audit()

    def test_changed_producer_bytes_are_rejected(self):
        f = self.fixture()
        path = f.root / PRODUCERS[0]
        path.write_bytes(path.read_bytes() + b"\n# TEST_ONLY altered producer\n")
        with self.assertRaises(native.B12ContractError):
            f.audit()

    def test_changed_running_producer_is_rejected_with_unchanged_reviewed_copy(self):
        f = self.fixture()
        running = Path(native.__file__).resolve()
        original = Path.read_bytes
        def altered(path):
            content = original(path)
            return content + b"\n# TEST_ONLY runtime drift\n" if path.resolve() == running else content
        with patch.object(Path, "read_bytes", altered), self.assertRaises(native.B12ContractError):
            f.audit()

    def test_changed_leaf_proof_bytes_are_rejected(self):
        f = self.fixture()
        (f.root / f.review["leaf_evidence"][0]["pin"]["path"]).write_text("{}", encoding="utf-8")
        with self.assertRaises(native.B12ContractError):
            f.audit()

    def test_missing_required_leaf_is_incomplete_not_zero(self):
        f = self.fixture()
        f.review["leaf_evidence"] = [p for p in f.review["leaf_evidence"]
                                     if p["input_path"] != "case.costs.rows[0].gross"]
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("gross" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_unknown_service_life_is_incomplete_without_default(self):
        c = external_case()
        a = replace(c.assets.rows[0], service_life=unknown("year", name="TEST_ONLY life"))
        c = replace(c, assets=replace(c.assets, rows=(a,)))
        view = self.fixture(c).audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("service_life" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_unknown_gross_is_incomplete_without_default(self):
        c = external_case()
        original = c.costs.rows[0]
        price = unknown(name="TEST_ONLY price")
        changed = replace(original, gross=price, net=price, vat=price)
        c = replace(c, costs=replace(c.costs, rows=(changed,)))
        view = self.fixture(c).audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("gross" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_missing_cost_scope_cannot_claim_full_asset_total(self):
        f = self.fixture()
        f.review["scope_coverage"]["complete_nonenergy_costs"] = False
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_added_cost_with_no_new_leaf_review_cannot_enter_result(self):
        f = self.fixture()
        added = replace(f.case.costs.rows[0], cost_id="TEST_ONLY:extra-om", event_id="TEST_ONLY:extra-om",
                        category="O_AND_M", inclusion_scope=("TEST_ONLY:extra-service",))
        changed = replace(f.case, costs=replace(f.case.costs, rows=f.case.costs.rows + (added,)))
        f.case = changed
        f.review["case_pin"] = f.pin("case.json", native.b07_case_payload(changed))
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_cost_only_does_not_require_inventory_or_non_cash_terminal_value(self):
        c = external_case()
        a = replace(c.assets.rows[0], terminal_kind="Q", terminal_value=unknown(name="TEST_ONLY terminal"))
        c = replace(c, assets=replace(c.assets, rows=(a,)))
        f = self.fixture(c)
        self.assertEqual(f.review["operations"], [])
        view = f.audit().b07_view
        self.assertEqual(view.status, "READY_SCN")
        self.assertEqual(view.amounts["gross_asset_cost.programme"], Decimal(127000))
        self.assertFalse(any("terminal" in key or "inventory" in key for key in view.amounts))
        self.assertEqual(view.inventory, ())

    def test_interval_gap_is_incomplete_not_filled_from_life(self):
        c = external_case()
        a = replace(c.assets.rows[0], commissioning_date=date(2026, 1, 2))
        f = self.fixture(replace(c, assets=replace(c.assets, rows=(a,))))
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_two_generation_chain_covers_horizon_without_predecessor_survival(self):
        c = replacement_case()
        self.assertLess(c.assets.rows[0].operating_coverage_end, c.evaluation_period.end)
        view = self.fixture(c).audit().b07_view
        self.assertEqual(view.status, "READY_SCN")
        self.assertEqual(view.amounts["gross_asset_cost.programme"], Decimal(254000))

    def test_component_mismatch_in_replacement_chain_is_rejected(self):
        c = replacement_case()
        second = replace(c.assets.rows[1], component_id="TEST_ONLY:unrelated-component")
        replacement = replace(c.costs.rows[1], component_id=second.component_id)
        c = replace(c, assets=replace(c.assets, rows=(c.assets.rows[0], second)),
                    costs=replace(c.costs, rows=(c.costs.rows[0], replacement)))
        with self.assertRaises(native.B12ContractError):
            self.fixture(c).audit()

    def test_two_generation_overlap_is_rejected_or_explicitly_incomplete(self):
        f = self.fixture(replacement_case())
        f.review["intervals"][0]["end_exclusive"] = "2026-07-02"
        try:
            view = f.audit().b07_view
        except native.B12ContractError:
            return
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_two_generation_gap_is_incomplete(self):
        c = replacement_case()
        a = replace(c.assets.rows[0], operating_coverage_end=date(2026, 6, 29))
        f = self.fixture(replace(c, assets=replace(c.assets, rows=(a, c.assets.rows[1]))))
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_explicit_same_day_ordered_replacement_remains_supported(self):
        f = self.fixture(replacement_case(date(2026, 1, 1)))
        self.assertEqual(f.review["intervals"][0]["start"], f.review["intervals"][0]["end_exclusive"])
        view = f.audit().b07_view
        self.assertEqual(view.status, "READY_SCN")
        self.assertEqual(view.amounts["gross_asset_cost.programme"], Decimal(254000))

    def test_single_finite_window_cash_reports_no_free_terminal_credit(self):
        f = self.cash_fixture()
        result = f.audit()
        view = result.b07_view
        self.assertEqual(view.status, "READY_SCN")
        self.assertEqual(view.amounts["unfinanced_cash.incremental"], Decimal(-127000))
        self.assertEqual(set(view.amounts), {
            f"{name}.{suffix}" for name in ("gross_asset_cost", "unfinanced_cash")
            for suffix in (*native.LEGS, "incremental")
        })
        self.assertTrue(view.rows)
        self.assertTrue(all(row.financed is None and row.bank is None and row.recurring is None for row in view.rows))
        self.assertEqual(result.rows, ())
        self.assertEqual(dict(result.amounts), {})

    def test_cash_inventory_exposes_source_dc_values_without_cash_adjustment(self):
        f = self.cash_fixture()
        view = f.audit().b07_view
        self.assertEqual(view.status, "READY_SCN")
        self.assertEqual(len(view.inventory), len(f.review["operations"]))
        source_operations = [json.loads((f.root / pin["path"]).read_text(encoding="utf-8"))
                             for pin in f.review["operations"]]
        indexed = {row.operation_id: row for row in view.inventory}
        for operation in source_operations:
            row = indexed[operation["id"]]
            self.assertIs(type(row), native.B07InventoryRow)
            self.assertEqual(row.leg, operation["leg"])
            self.assertEqual(row.component_id, operation["component_id"])
            self.assertEqual(row.asset_generation_id, operation["asset_generation_id"])
            self.assertEqual(row.start, date.fromisoformat(operation["start"]))
            self.assertEqual(row.end_exclusive, date.fromisoformat(operation["end_exclusive"]))
            self.assertIs(type(row.opening_kwh_dc_reference), Decimal)
            self.assertIs(type(row.closing_kwh_dc_reference), Decimal)
            self.assertEqual(row.opening_kwh_dc_reference, Decimal(operation["opening"]))
            self.assertEqual(row.closing_kwh_dc_reference, Decimal(operation["closing"]))
        # The inherited TEST_ONLY capital cost remains the only leg difference;
        # the unequal DC endpoint inventory supplies no credit/debit or cash row.
        self.assertEqual(view.amounts["unfinanced_cash.incremental"], Decimal(-127000))
        self.assertFalse(any("inventory" in key for key in view.amounts))
        self.assertFalse(any("INVENTORY" in row.category for row in view.rows))

    def test_unfilled_repository_dossier_reports_exact_null_input_paths(self):
        path = ROOT / "inputs/b07_conditional/DOSSIER_TEMPLATE.json"
        before = path.read_bytes()
        template = json.loads(before.decode("utf-8-sig"))
        def null_paths(value, prefix="dossier"):
            if value is None:
                return {prefix}
            if isinstance(value, dict):
                return {item for key, child in value.items()
                        for item in null_paths(child, prefix + "." + key)}
            return set()
        missing = native.b07_dossier_missing(template)
        self.assertEqual({item.path for item in missing}, null_paths(template))
        for required in ("dossier.assets.service_life", "dossier.assets.external_replacement_schedule",
                         "dossier.case.evaluation_period.start", "dossier.case.evaluation_period.end_inclusive",
                         "dossier.costs.prices_and_units", "dossier.energy.opening_and_closing_inventory"):
            self.assertIn(required, {item.path for item in missing})
        self.assertTrue(all(type(item) is native.MissingInput and item.reason and item.acquisition_ref
                            for item in missing))
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(template["status"], "INCOMPLETE_NO_MODEL_VALUES_SELECTED")

    def test_dossier_missing_section_is_reported_without_building_native_case(self):
        template = json.loads((ROOT / "inputs/b07_conditional/DOSSIER_TEMPLATE.json").read_text(encoding="utf-8-sig"))
        del template["assets"]
        missing = native.b07_dossier_missing(template)
        paths = {item.path for item in missing}
        self.assertIn("dossier.assets.service_life", paths)
        self.assertIn("dossier.assets.external_replacement_schedule", paths)
        self.assertIn("dossier.assets.intervals", paths)
        self.assertIsInstance(template, dict)
        self.assertNotIsInstance(template, native.Case)

    def test_cash_without_operations_is_incomplete_but_cost_scope_is_not_opened(self):
        f = self.cash_fixture()
        f.review["operations"] = []
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("operations" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_repeated_branch_does_not_get_implicit_inventory_reset(self):
        f = self.cash_fixture(split=True)
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("transition" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_declared_unequal_inventory_continuity_is_not_a_correction_method(self):
        f = self.cash_fixture(split=True)
        for index in (1, 3):
            def add_transition(op, leg=native.LEGS[index // 2]):
                op["transition_pin"] = f.pin(f"transition/{leg}.json", dict(
                    case_id=f.case.case_id, **{"from": f"TEST_ONLY:{leg}-operation-0"},
                    to=op["id"], closing="3", opening="2", boundary=op["start"], kind="EXPLICIT_CONTINUITY"))
            self.rewrite_operation(f, index, add_transition)
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("unsupported correction" in m.reason for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_equal_inventory_continuity_requires_explicit_source_and_transition(self):
        f = self.cash_fixture(split=True)
        for index in (1, 3):
            def make_continuous(op, leg=native.LEGS[index // 2]):
                op["opening"] = "3"
                source = json.loads((f.root / op["reference_pin"]["path"]).read_text(encoding="utf-8"))
                source["opening"] = "3"
                op["reference_pin"] = f.pin(f"continuous-source/{leg}.json", source)
                op["transition_pin"] = f.pin(f"transition/{leg}.json", dict(
                    case_id=f.case.case_id, **{"from": f"TEST_ONLY:{leg}-operation-0"},
                    to=op["id"], closing="3", opening="3", boundary=op["start"], kind="EXPLICIT_CONTINUITY"))
            self.rewrite_operation(f, index, make_continuous)
        view = f.audit().b07_view
        self.assertEqual(view.status, "READY_SCN")
        self.assertEqual(view.amounts["unfinanced_cash.incremental"], Decimal(-127000))

    def test_unknown_terminal_blocks_cash_not_gross_cost_only(self):
        f = self.cash_fixture()
        c = f.case
        changed = replace(c.assets.rows[0], terminal_kind="Q", terminal_value=unknown(name="TEST_ONLY terminal"))
        f.case = replace(c, assets=replace(c.assets, rows=(changed,) + c.assets.rows[1:]))
        f.review["case_pin"] = f.pin("case.json", native.b07_case_payload(f.case))
        f.prove_all()
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("terminal" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_cash_requires_explicit_receipt_free_declaration(self):
        f = self.cash_fixture()
        f.review["scope_coverage"]["receipt_free"] = False
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("receipts" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_duplicate_bill_allocation_cannot_enter_cash_view(self):
        f = self.cash_fixture()
        self.rewrite_operation(f, 1, lambda op: op["bill_ids"].append("TEST_ONLY:programme-bill-0"))
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("bill_ids" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_operation_cannot_allocate_other_legs_bill(self):
        f = self.cash_fixture()
        def other_leg(op):
            old = op["bill_ids"][0]
            op["bill_ids"] = ["TEST_ONLY:baseline-bill-0"]
            op["bill_bindings"] = {op["bill_ids"][0]: op["bill_bindings"][old]}
        self.rewrite_operation(f, 1, other_leg)
        with self.assertRaises(native.B12ContractError):
            f.audit()

    def test_operation_physical_reference_cannot_be_changed(self):
        f = self.cash_fixture()
        def changed(op):
            op["bill_bindings"][op["bill_ids"][0]]["physical_ref"] = "TEST_ONLY:foreign-physical-profile"
        self.rewrite_operation(f, 0, changed)
        with self.assertRaises(native.B12ContractError):
            f.audit()

    def test_operation_full_meter_quantity_must_replay_its_source(self):
        f = self.cash_fixture()
        def changed(op):
            source = json.loads((f.root / op["reference_pin"]["path"]).read_text(encoding="utf-8"))
            source["meter_quantities"][op["bill_ids"][0]] = "99"
            op["reference_pin"] = f.pin("TEST_ONLY:changed-meter-quantity.json", source)
        self.rewrite_operation(f, 0, changed)
        with self.assertRaises(native.B12ContractError):
            f.audit()

    def test_matching_partial_bills_do_not_cover_a_full_year_operation(self):
        f = self.cash_fixture()
        partial = tuple(replace(row, service_period=native.Period(date(2026, 1, 1), date(2026, 6, 30)))
                        for row in f.case.bills.rows)
        f.case = replace(f.case, bills=replace(f.case.bills, rows=partial))
        f.review["case_pin"] = f.pin("case.json", native.b07_case_payload(f.case))
        f.prove_all()
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("service coverage" in m.reason for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))

    def test_a_receipt_cannot_silently_enter_the_receipt_free_cash_route(self):
        f = self.cash_fixture()
        receipt = external_value(grant())
        f.case = replace(f.case, receipts=native.Section("ROWS", (receipt,),
                                                       f.case.receipts.authority, ("baseline",)))
        f.review["case_pin"] = f.pin("case.json", native.b07_case_payload(f.case))
        f.prove_all()
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("receipts" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))


    def test_warranty_label_is_not_a_service_life_definition(self):
        c = external_case()
        c = replace(c, assets=replace(c.assets, rows=(replace(c.assets.rows[0], life_definition="WARRANTY"),)))
        with self.assertRaises(native.B12ContractError):
            self.fixture(c).audit()

    def test_a_source_scalar_requires_source_authority_not_scenario_self_declaration(self):
        c = external_case()
        cost = c.costs.rows[0]
        gross = replace(cost.gross, truth="DER", source_ids=("TEST_ONLY:source",),
                        scenario_ref=None, evidence_tier="E2", admission_ref="TEST_ONLY:source-review")
        c = replace(c, costs=replace(c.costs, rows=(replace(cost, gross=gross),)))
        with self.assertRaises(native.B12ContractError):
            self.fixture(c).audit()

    def test_generation_change_does_not_inherit_predecessor_inventory(self):
        f = self.cash_fixture(split=True)
        generations = replacement_case()
        baseline = next(a for a in f.case.assets.rows if a.leg == "baseline")
        f.case = replace(f.case, assets=replace(f.case.assets, rows=(baseline,) + generations.assets.rows),
                         costs=generations.costs)
        f.review["case_pin"] = f.pin("case.json", native.b07_case_payload(f.case))
        f.review["intervals"] = [dict(leg=a.leg, component_id=a.component_id,
                                           asset_generation_id=a.asset_generation_id,
                                           start=a.commissioning_date.isoformat(),
                                           end_exclusive=(a.operating_coverage_end + timedelta(days=1)).isoformat(),
                                           order=i) for i, a in enumerate(f.case.assets.rows)]
        f.prove_all()
        def baseline_continuity(op):
            op["opening"] = "3"
            source = json.loads((f.root / op["reference_pin"]["path"]).read_text(encoding="utf-8"))
            source["opening"] = "3"
            op["reference_pin"] = f.pin("TEST_ONLY:baseline-continuous-source.json", source)
            op["transition_pin"] = f.pin("TEST_ONLY:baseline-transition.json", dict(
                case_id=f.case.case_id, **{"from": "TEST_ONLY:baseline-operation-0"},
                to=op["id"], closing="3", opening="3", boundary=op["start"], kind="EXPLICIT_CONTINUITY"))
        self.rewrite_operation(f, 1, baseline_continuity)
        self.rewrite_operation(f, 3, lambda op: op.update(asset_generation_id="TEST_ONLY:battery-generation-2"))
        view = f.audit().b07_view
        self.assertEqual(view.status, "INCOMPLETE")
        self.assertTrue(any("operations[3].transition_pin" in m.path for m in view.missing))
        self.assertFalse(any(v is not None for v in view.amounts.values()))


class B07SourceCostScopeTests(unittest.TestCase):
    """Only TEST_ONLY source witnesses; no battery price is selected."""
    def setUp(self):
        self.f = CostFixture()
        self.addCleanup(self.f.temp.cleanup)
        self.f.binding.update(component_id="BATTERY", asset_generation_id="TEST_ONLY:battery-generation")

    def resolve(self, catalogue):
        return source.resolve_cost_inputs(catalogue, (self.f.binding,), COST_BASIS, case_context=TEST_CONTEXT)

    @staticmethod
    def b07_scope(review):
        review.update(service_scope="B07_BATTERY_REFERENCE", owner_module="B07")

    def test_qualified_b07_scope_keeps_exact_source_cost_binding(self):
        catalogue = self.f.build(review_change=self.b07_scope)
        result = self.resolve(catalogue)
        self.assertEqual(len(result.costs), 1)
        self.assertFalse(result.missing)
        self.assertEqual(result.costs[0].component_id, "BATTERY")
        self.assertEqual(result.costs[0].category, "INITIAL_CAPEX")

    def test_b07_scope_requires_b07_owner_module(self):
        catalogue = self.f.build(review_change=lambda review: review.update(service_scope="B07_BATTERY_REFERENCE"))
        with self.assertRaises(native.B12ContractError):
            self.resolve(catalogue)

    def test_replacement_requires_explicit_source_and_economic_category_mapping(self):
        self.f.binding.update(category="REPLACEMENT", source_category="INITIAL_CAPEX")
        def qualified(review):
            self.b07_scope(review)
            review["category_mapping"] = dict(source="INITIAL_CAPEX", economic="REPLACEMENT",
                                              asset_generation_id=self.f.binding["asset_generation_id"])
        result = self.resolve(self.f.build(review_change=qualified))
        self.assertEqual(len(result.costs), 1)
        self.assertFalse(result.missing)
        self.assertEqual(result.costs[0].category, "REPLACEMENT")

    def test_replacement_without_category_mapping_is_rejected(self):
        self.f.binding.update(category="REPLACEMENT", source_category="INITIAL_CAPEX")
        with self.assertRaises(native.B12ContractError):
            self.resolve(self.f.build(review_change=self.b07_scope))

    def test_replacement_mapping_cannot_target_another_generation(self):
        self.f.binding.update(category="REPLACEMENT", source_category="INITIAL_CAPEX")
        def wrong_generation(review):
            self.b07_scope(review)
            review["category_mapping"] = dict(source="INITIAL_CAPEX", economic="REPLACEMENT",
                                              asset_generation_id="TEST_ONLY:other-generation")
        with self.assertRaises(native.B12ContractError):
            self.resolve(self.f.build(review_change=wrong_generation))



if __name__ == "__main__":
    unittest.main()
