"""Real preserved physical/tariff inputs; explicit invocation probes only.

Test q/m, cash dates and context are never adopted reference-case parameters.
No historical builder, existing test fixture, network or private raw data used.
"""
import csv
import io
import json
import unittest
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import (Decimal, getcontext, localcontext, ROUND_DOWN, ROUND_UP,
                     ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_DOWN, ROUND_HALF_UP)
from pathlib import Path
from unittest.mock import patch

from modules.B04 import engine as b04
from modules.B12 import input_accounting_contract as native
from modules.B12.a1_reference_response import (
    A1ReferenceError, BillContext, CUT, END, LOCAL, SCENARIO, START,
    evaluate_reference, load_reference, summarize_hourly_profile,
)


ROOT = Path(__file__).resolve().parents[1]


def unpack(value):
    if isinstance(value, list):
        return [unpack(v) for v in value]
    if not isinstance(value, dict):
        return value
    if "__decimal__" in value:
        return Decimal(value["__decimal__"])
    if "__date__" in value:
        return date.fromisoformat(value["__date__"])
    if "__tuple__" in value:
        return tuple(unpack(v) for v in value["__tuple__"])
    if "__native_record__" in value:
        return getattr(native, value["__native_record__"])(**{
            k: unpack(v) for k, v in value.items() if k != "__native_record__"})
    return {k: unpack(v) for k, v in value.items()}


def reference(name):
    return native.Reference("EXTERNAL_ADMISSION", "TEST_ONLY:" + name, None, None)


def unknown_section():
    return native.Section("Q", (), native.Reference("Q", None, "Not supplied by this test", "B12-D03"), ())


def invocation_context():
    # C01 supplies the current native record shapes, not its t0 or outdoor-only
    # scope as implicit billing defaults. Test context choices are explicit.
    c01 = unpack(json.loads((ROOT / "C01_NATIVE_CASE.json").read_text(encoding="utf-8")))
    window = native.Period(date(2026, 1, 1), date(2028, 12, 31))
    scope = replace(c01.scope, scope_id="TEST_ONLY:HH_SELECTED_A1_BASE_PLUS_SH",
                    mapping=reference("declared-selected-meter-household-scope"))
    case = replace(c01, case_id="TEST_ONLY:A1-ADAPTER-INVOCATION", scope=scope,
                   evaluation_period=window, reporting_periods=(window,),
                   costs=unknown_section(), assets=unknown_section(), bills=unknown_section())
    return BillContext(case=case, money_basis=case.monetary_basis,
        settlement_dates={"S1": date(2026, 10, 1), "S2": date(2026, 11, 1)},
        meter_id="TEST_ONLY:COMMON-A1-METER", scope_ref=scope.scope_id,
        service_basis_ref=case.service_basis_ref,
        application=reference("conditional-A1-application-not-legal-entitlement"),
        allocation=reference("explicit-test-q-m-not-selected-in-owner-SCN"),
        coverage=reference("UTC2025-partial-local-boundary-days-selected-SH-meter-reference"),
        scenario_ref="TEST_ONLY:EXPLICIT_INVOCATION_NOT_ADOPTED_SCN", event_prefix="TEST_ONLY:A1")


class A1ReferenceResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = load_reference(ROOT)
        cls.raw = (ROOT / "inputs/a1_reference/UNIT_INCREMENT_HOURLY_8760.csv").read_bytes()
        cls.rows = list(csv.DictReader(io.StringIO(cls.raw.decode("utf-8-sig"), newline="")))
        cls.saved = json.loads((ROOT / "inputs/a1_reference/PRESERVED_PARAMETRIC_RESPONSE.json").read_text(encoding="utf-8"))

    def params(self):
        with localcontext() as ctx:
            ctx.prec = 50
            return ({p.id: p.base_kwh + p.hp_kwh / 2 for p in self.ref.periods},
                    {"S1": Decimal("1.25"), "S2": Decimal("2.5")})

    def evaluate(self, **changes):
        q, m = self.params()
        kw = dict(allowances=q, billed_months=m)
        kw.update(changes)
        return evaluate_reference(self.ref, **kw)

    def changed_csv(self, change):
        rows = [dict(r) for r in self.rows]
        columns = list(rows[0])
        change(rows, columns)
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().encode("utf-8")

    def test_01_actual_hash_bound_profile_and_source_ids(self):
        self.assertEqual(dict(self.ref.provenance)["physical_profile"],
                         "cd1247bb9c904531e06951542958b257e2471cf8fbd7469fed2e9ce55ffe554b")
        self.assertEqual(self.ref.scenario_id, SCENARIO)
        self.assertEqual(self.ref.source_ids, tuple(self.saved["source_ids"]))
        self.assertEqual(sum(p.hours for p in self.ref.periods), 8760)

    def test_02_legacy_and_current_B12_identities_are_separate(self):
        pins = dict(self.ref.provenance)
        self.assertNotEqual(pins["historical_B12_adapter"], pins["repo/modules/B12/input_accounting_contract.py"])
        self.assertEqual(pins["repo/modules/B12/input_accounting_contract.py"],
                         "ced2880d4dda1f91e8f1ae72014f945806e1768e0befa954c5f684e1f2bdbd6a")

    def test_03_physical_hash_change_rejected(self):
        original = Path.read_bytes
        def altered(path):
            raw = original(path)
            return raw + b"\n" if path.name == "UNIT_INCREMENT_HOURLY_8760.csv" else raw
        with patch.object(Path, "read_bytes", altered), self.assertRaisesRegex(A1ReferenceError, "source hash"):
            load_reference(ROOT)

    def test_04_current_adapter_drift_rejected(self):
        original = Path.read_bytes
        def altered(path):
            raw = original(path)
            return raw + b"\n" if path.name == "input_accounting_contract.py" else raw
        with patch.object(Path, "read_bytes", altered), self.assertRaisesRegex(A1ReferenceError, "C01 implementation"):
            load_reference(ROOT)

    def test_05_supplied_reference_cannot_replace_loaded_quantities(self):
        bad = replace(self.ref, periods=(replace(self.ref.periods[0], hp_kwh=Decimal("1")), self.ref.periods[1]))
        with self.assertRaisesRegex(A1ReferenceError, "changed after loading"):
            evaluate_reference(bad)

    def test_06_exact_UTC_split_and_energy_conservation(self):
        self.assertEqual([(p.start_utc, p.end_utc_exclusive, p.hours) for p in self.ref.periods],
                         [(START, CUT, 5086), (CUT, END, 3674)])
        with localcontext() as ctx:
            ctx.prec = 50
            for actual, saved in zip(self.ref.periods, self.saved["periods"]):
                self.assertEqual(actual.base_kwh, Decimal(saved["base_kWh"]))
                self.assertEqual(actual.hp_kwh, Decimal(saved["HP_reference_kWh"]))
                self.assertEqual(actual.base_kwh + actual.hp_kwh, Decimal(saved["programme_kWh"]))
            self.assertEqual(sum(p.hp_kwh for p in self.ref.periods), Decimal(self.saved["physical_HP_reference_annual_kWh"]))

    def test_07_DST_spring_and_autumn_hour_counts(self):
        counts = Counter(datetime.fromisoformat(r["interval_start_utc"]).astimezone(LOCAL).date() for r in self.rows)
        self.assertEqual(counts[date(2025, 3, 30)], 23)
        self.assertEqual(counts[date(2025, 10, 26)], 25)
        self.assertEqual(CUT.astimezone(LOCAL).isoformat(), "2025-08-01T00:00:00+02:00")

    def test_08_partial_boundary_days_are_preserved(self):
        counts = Counter(datetime.fromisoformat(r["interval_start_utc"]).astimezone(LOCAL).date() for r in self.rows)
        self.assertEqual(counts[date(2025, 1, 1)], 23)
        self.assertEqual(counts[date(2026, 1, 1)], 1)
        self.assertFalse(self.ref.complete_local_civil_year)
        self.assertEqual(self.ref.periods[1].service_period.end, date(2026, 1, 1))

    def test_09_wrong_column_or_unit_label_rejected(self):
        def change(rows, columns):
            old = "unit_incremental_W55_device_reference_kWh"
            columns[columns.index(old)] = "unit_incremental_W55_device_reference_MWh"
            for row in rows: row[columns[7]] = row.pop(old)
        with self.assertRaisesRegex(A1ReferenceError, "column/unit"):
            summarize_hourly_profile(self.changed_csv(change))

    def test_10_hours_power_energy_and_MW_inconsistency_rejected(self):
        for field in ("hours", "programme_selected_reference_kw", "unit_incremental_W55_device_reference_kWh",
                      "unit_incremental_W55_device_reference_mw"):
            with self.subTest(field=field), self.assertRaises(A1ReferenceError):
                summarize_hourly_profile(self.changed_csv(lambda rows, _: rows[0].update({field: "999"})))

    def test_11_missing_hour_rejected(self):
        with self.assertRaises(A1ReferenceError):
            summarize_hourly_profile(self.changed_csv(lambda rows, _: rows.pop(10)))

    def test_12_duplicate_hour_rejected(self):
        with self.assertRaises(A1ReferenceError):
            summarize_hourly_profile(self.changed_csv(lambda rows, _: rows.__setitem__(1, dict(rows[0]))))

    def test_13_unordered_hours_rejected(self):
        def change(rows, _): rows[10], rows[11] = rows[11], rows[10]
        with self.assertRaises(A1ReferenceError): summarize_hourly_profile(self.changed_csv(change))

    def test_14_relabelled_year_and_nonUTC_timestamps_rejected(self):
        for stamp in ("2028-01-01T00:00:00+00:00", "2025-01-01T00:00:00+01:00"):
            with self.subTest(stamp=stamp), self.assertRaises(A1ReferenceError):
                summarize_hourly_profile(self.changed_csv(lambda rows, _: rows[0].update(interval_start_utc=stamp)))

    def test_15_negative_and_nonfinite_physical_values_rejected(self):
        for value in ("-1", "NaN", "Infinity", ""):
            with self.subTest(value=value), self.assertRaises(A1ReferenceError):
                summarize_hourly_profile(self.changed_csv(lambda rows, _: rows[0].update(common_base_reference_kw=value)))

    def test_16_unknown_HMV_and_auxiliary_not_silently_zero(self):
        for field in ("HMV_electricity_kw", "outside_unit_auxiliary_correction_kw", "physical_net_increment_kw"):
            with self.subTest(field=field), self.assertRaises(A1ReferenceError):
                summarize_hourly_profile(self.changed_csv(lambda rows, _: rows[0].update({field: "0"})))

    def test_17_missing_parameters_return_incomplete_not_bill(self):
        result = evaluate_reference(self.ref)
        self.assertEqual(result.status, "INCOMPLETE_PARAMETERS")
        self.assertIsNone(result.totals)
        self.assertEqual(result.bills, ())

    def test_18_invalid_allowances_return_incomplete(self):
        for value in (None, True, 0.0, Decimal("NaN"), Decimal("Infinity"), Decimal("-1")):
            with self.subTest(value=str(value)):
                result = self.evaluate(allowances={"S1": value, "S2": Decimal(0)}, context=invocation_context())
                self.assertEqual(result.status, "INCOMPLETE_PARAMETERS")
                self.assertEqual(result.bills, ())

    def test_19_invalid_month_fractions_return_incomplete(self):
        for value in (None, False, 1.5, Decimal("NaN"), Decimal("-1")):
            with self.subTest(value=str(value)):
                result = self.evaluate(billed_months={"S1": value, "S2": Decimal(0)})
                self.assertEqual(result.status, "INCOMPLETE_PARAMETERS")
                self.assertEqual(result.bills, ())

    def test_20_missing_extra_or_leg_specific_parameter_keys_rejected(self):
        q, _ = self.params()
        for mapping in ({"S1": q["S1"]}, {**q, "S3": Decimal(1)}, {"baseline": q, "programme": q}):
            with self.subTest(keys=list(mapping)):
                self.assertEqual(self.evaluate(allowances=mapping).status, "INCOMPLETE_PARAMETERS")

    def test_21_context_missing_keeps_charge_response_not_BillInput(self):
        result = self.evaluate()
        self.assertEqual(result.status, "EVALUATED_CONTEXT_INCOMPLETE")
        self.assertEqual(result.bills, ())
        self.assertGreater(result.totals["incremental_consumption_gross_HUF"], 0)
        self.assertTrue(any("t0" in s for s in result.missing))

    def test_22_complete_explicit_context_reuses_native_adapter(self):
        with patch.object(native.BillInput, "from_b04", wraps=native.BillInput.from_b04) as adapter:
            result = self.evaluate(context=invocation_context())
        self.assertEqual(result.missing, ())
        self.assertEqual(len(result.bills), 4)
        self.assertEqual(adapter.call_count, 4)
        self.assertTrue(all(type(b) is native.BillInput for b in result.bills))
        self.assertTrue(all(b.upstream_status == "SCN_CONSTANT_2026_TARIFF_SNAPSHOT" for b in result.bills))
        self.assertTrue(all(b.period.start.year == 2026 and b.service_period.start.year == 2025 for b in result.bills))

    def test_23_exact_B04_producer_equivalence(self):
        q, m = self.params()
        result = self.evaluate()
        with localcontext() as ctx:
            ctx.prec = 50
            for p, r in zip(self.ref.periods, result.periods):
                old = b04.price_a1(p.base_kwh, q[p.id], m[p.id], self.saved["distributor"])
                new = b04.price_a1(p.base_kwh + p.hp_kwh, q[p.id], m[p.id], self.saved["distributor"])
                self.assertEqual(r["baseline_total_gross_HUF"], old.total_huf)
                self.assertEqual(r["programme_total_gross_HUF"], new.total_huf)
                self.assertEqual(r["incremental_consumption_gross_HUF"], new.consumption_charge_huf - old.consumption_charge_huf)

    def test_24_Decimal_thresholds_no_implicit_entitlement(self):
        low = Decimal(self.saved["rates"]["low_final_gross_HUF_per_kWh"])
        high = Decimal(self.saved["rates"]["high_final_gross_HUF_per_kWh"])
        with localcontext() as ctx:
            ctx.prec = 50
            for p in self.ref.periods:
                for value in (Decimal(0), p.base_kwh, p.base_kwh + Decimal("1e-25"),
                              p.base_kwh + p.hp_kwh - Decimal("1e-25"), p.base_kwh + p.hp_kwh):
                    q = {other.id: value if other.id == p.id else Decimal(0) for other in self.ref.periods}
                    r = next(r for r in self.evaluate(allowances=q).periods if r["id"] == p.id)
                    expected = high*p.hp_kwh - (high-low)*(min(p.base_kwh+p.hp_kwh, value)-min(p.base_kwh, value))
                    self.assertEqual(r["incremental_consumption_gross_HUF"], expected)

    def test_25_fixed_fee_once_per_alternative_not_per_end_use(self):
        result = self.evaluate(context=invocation_context())
        q, m = self.params()
        with localcontext() as ctx:
            ctx.prec = 50
            fixed = Decimal(self.saved["rates"]["fixed_gross_HUF_per_year"]) * sum(m.values()) / 12
            for leg in ("baseline", "programme"):
                self.assertEqual(sum(b.fixed_gross.value for b in result.bills if b.leg == leg), fixed)
            self.assertEqual(result.totals["common_fixed_gross_HUF"], fixed)
            self.assertEqual(result.totals["programme_total_gross_HUF"] - result.totals["baseline_total_gross_HUF"],
                             result.totals["incremental_consumption_gross_HUF"])

    def test_26_same_q_m_and_meter_for_both_alternatives(self):
        result = self.evaluate(context=invocation_context())
        for p in self.ref.periods:
            bills = [b for b in result.bills if b.bill_id.split(":")[-2] == p.id]
            self.assertEqual(len(bills), 2)
            self.assertEqual(bills[0].discounted_allocation, bills[1].discounted_allocation)
            self.assertEqual(bills[0].billed_months, bills[1].billed_months)
            self.assertEqual(bills[0].meter_id, bills[1].meter_id)
            with localcontext() as ctx:
                ctx.prec = 50
                self.assertEqual(bills[1].quantity.value - bills[0].quantity.value, p.hp_kwh)

    def test_27_missing_or_invalid_settlement_dates_not_t0(self):
        context = invocation_context()
        for dates in (None, {}, {"S1": date(2026, 1, 1)}, {"S1": None, "S2": date(2026, 1, 1)},
                      {"S1": datetime(2026, 1, 1), "S2": date(2026, 1, 1)}):
            with self.subTest(dates=str(dates)):
                r = self.evaluate(context=replace(context, settlement_dates=dates))
                self.assertEqual(r.status, "EVALUATED_CONTEXT_INCOMPLETE")
                self.assertEqual(r.bills, ())

    def test_28_cash_outside_explicit_case_window_rejected(self):
        c = replace(invocation_context(), settlement_dates={"S1": date(2025, 1, 1), "S2": date(2026, 1, 1)})
        result = self.evaluate(context=c)
        self.assertEqual(result.bills, ())
        self.assertTrue(any("outside evaluation" in s for s in result.missing))

    def test_29_missing_or_rebased_money_basis_rejected(self):
        c = invocation_context()
        for basis in (None, replace(c.money_basis, currency="EUR"),
                      replace(c.money_basis, price_date=date(2028, 1, 1)),
                      replace(c.money_basis, convention=None)):
            with self.subTest(basis=str(basis)):
                r = self.evaluate(context=replace(c, money_basis=basis))
                self.assertEqual(r.status, "EVALUATED_CONTEXT_INCOMPLETE")
                self.assertEqual(r.bills, ())

    def test_30_explicit_application_allocation_coverage_and_scope_required(self):
        c = invocation_context()
        for key, value in (("application", None), ("allocation", native.Reference("Q", None, "Missing", "B12-D03")),
                           ("coverage", None), ("meter_id", ""), ("scope_ref", "wrong"),
                           ("service_basis_ref", "different-service"), ("scenario_ref", None)):
            with self.subTest(key=key):
                r = self.evaluate(context=replace(c, **{key: value}))
                self.assertEqual(r.status, "EVALUATED_CONTEXT_INCOMPLETE")
                self.assertEqual(r.bills, ())

    def test_31_duplicate_meter_coverage_rejected_even_with_new_labels(self):
        c = invocation_context()
        old = self.evaluate(context=c)
        existing = tuple(replace(b, bill_id="old-"+b.bill_id, event_id="old-"+b.event_id,
                                 end_use="RENAMED_END_USE", fixed_charge_key="other-key") for b in old.bills)
        c = replace(c, case=replace(c.case, bills=native.Section("ROWS", existing, reference("existing-test-bills"), ())))
        result = self.evaluate(context=c)
        self.assertEqual(result.bills, ())
        self.assertTrue(any("overlaps existing" in s for s in result.missing))

    def test_32_duplicate_coverage_rejected_also_for_explicit_zero_fixed_fee(self):
        zero = {"S1": Decimal(0), "S2": Decimal(0)}
        c = invocation_context()
        old = self.evaluate(context=c, billed_months=zero)
        existing = tuple(replace(b, bill_id="old-"+b.bill_id, event_id="old-"+b.event_id,
                                 end_use="RENAMED", fixed_charge_key="different") for b in old.bills)
        c = replace(c, case=replace(c.case, bills=native.Section("ROWS", existing, reference("test-existing-zero-fee"), ())))
        self.assertEqual(self.evaluate(context=c, billed_months=zero).bills, ())

    def test_33_invalid_nested_native_case_is_incomplete(self):
        c = invocation_context()
        r = self.evaluate(context=replace(c, case=replace(c.case, scope=None)))
        self.assertEqual(r.status, "EVALUATED_CONTEXT_INCOMPLETE")
        self.assertEqual(r.bills, ())

    def test_34_no_full_financial_or_qualified_audit_claim(self):
        result = self.evaluate(context=invocation_context())
        self.assertIn("REVIEW_NOT_QUALIFIED", result.status)
        self.assertIsNone(result.full_cashflow)
        self.assertIsNone(result.full_capex)
        self.assertIsNone(result.roi)

    def test_35_loading_independent_of_ambient_precision_and_rounding(self):
        for mode in (ROUND_DOWN, ROUND_UP, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_DOWN, ROUND_HALF_UP):
            with self.subTest(rounding=mode), localcontext() as ambient:
                ambient.prec = 7
                ambient.rounding = mode
                actual = load_reference(ROOT)
                self.assertEqual(actual, self.ref)
                self.assertEqual(getcontext().prec, 7)
                self.assertEqual(getcontext().rounding, mode)

    def test_36_evaluating_independent_of_ambient_precision_and_rounding(self):
        # Test invocation values are supplied before entering the altered caller
        # context. No new allowance, cash-date or economic scenario is adopted.
        q, m = self.params()
        context = invocation_context()
        expected_incomplete = evaluate_reference(self.ref, allowances=q, billed_months=m)
        expected_native = evaluate_reference(self.ref, allowances=q, billed_months=m, context=context)
        for mode in (ROUND_DOWN, ROUND_UP, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_DOWN, ROUND_HALF_UP):
            with self.subTest(rounding=mode), localcontext() as ambient:
                ambient.prec = 7
                ambient.rounding = mode
                self.assertEqual(evaluate_reference(self.ref, allowances=q, billed_months=m), expected_incomplete)
                self.assertEqual(evaluate_reference(self.ref, allowances=q, billed_months=m, context=context), expected_native)
                self.assertEqual(getcontext().prec, 7)
                self.assertEqual(getcontext().rounding, mode)


if __name__ == "__main__":
    unittest.main()
