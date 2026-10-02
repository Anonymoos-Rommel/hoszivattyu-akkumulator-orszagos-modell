import copy
import csv
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B04 import annual_reference as annual
from modules.B04 import engine as native


def ledger(scheme='H'):
    """Explicit synthetic example, not a production fee-prorating default."""
    months = []
    for month in range(1, 13):
        if scheme == 'A1':
            fractions = (('A1', 1),)
        elif month in (4, 10):
            h = Fraction(1, 2) if month == 4 else Fraction(17, 31)
            fractions = (('H_HEATING', h), ('H_OUTSIDE', 1 - h))
        elif month in (1, 2, 3, 11, 12):
            fractions = (('H_HEATING', 1),)
        else:
            fractions = (('H_OUTSIDE', 1),)
        months.append(annual.MonthFee(month, fractions))
    return annual.ConnectionLedger('synthetic-single-connection', 2025, 'CONTINUOUS_CIVIL_YEAR', tuple(months))


class AnnualReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.weather = Path(cls.tmp.name) / 'synthetic_civil_weather.csv'
        with cls.weather.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['station_id', 'interval_start_utc', 'source_endpoint_utc', 'ta_C', 'source_id'])
            for i in range(8760):
                a = annual.START + i * annual.HOUR
                w.writerow(['44527', a.isoformat(), (a + annual.HOUR).isoformat(), '10', 'TEST_SYNTHETIC_WEATHER'])
        cls.manifest = copy.deepcopy(annual._manifest())
        cls.manifest['weather'].update(sha256=hashlib.sha256(cls.weather.read_bytes()).hexdigest(),
                                     bytes=cls.weather.stat().st_size, history_source_id='TEST_SYNTHETIC_WEATHER')
        # Test seam replaces weather provenance only. Genuine original replay is
        # separately recorded outside Git; these fixtures claim no observation.
        with patch.object(annual, '_manifest', return_value=cls.manifest):
            cls.reference = annual.calculate_reference(weather_path=cls.weather, package='ambitious')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def args(self, scheme='H'):
        return dict(weather_path=self.weather, package='ambitious', scheme=scheme,
                    distributor_area='MVM Démász', condition=annual.CONDITION,
                    discounted_allocations=({'H_OUTSIDE': 50} if scheme == 'H' else
                        {'A1_2024_2025_PORTION': 1000, 'A1_2025_2026_PORTION': 0}),
                    connection_ledger=ledger(scheme), load_scope=annual.H_LOAD,
                    connection_scope='PROFILED_LOW_VOLTAGE')

    def evaluate(self, **changes):
        args = self.args(changes.pop('scheme', 'H')); args.update(changes)
        with patch.object(annual, '_manifest', return_value=self.manifest):
            return annual.evaluate_reference(**args)

    def test_complete_local_year_and_source_heat_conservation(self):
        r = self.reference
        self.assertEqual(r['rows'][0]['interval_start_local'], '2025-01-01T00:00:00+01:00')
        self.assertEqual(r['rows'][-1]['interval_end_local'], '2026-01-01T00:00:00+01:00')
        self.assertEqual([s['hours'] for s in r['segments']], [2519, 2568, 1800, 1873])
        total = sum(s['reference_electricity_kwh'] for s in r['segments'])
        self.assertAlmostEqual(float(total), r['summary']['annual_device_reference_electricity_kwh'], places=9)
        self.assertAlmostEqual(sum(x['useful_heat_kwh'] for x in r['rows']), r['thermal_reference']['useful_heat_kwh'], places=7)

    def test_dst_and_season_edges(self):
        rows = self.reference['rows']
        spring = [r for r in rows if r['interval_start_local'].startswith('2025-03-30')]
        autumn = [r for r in rows if r['interval_start_local'].startswith('2025-10-26')]
        self.assertEqual(len(spring), 23); self.assertEqual(len(autumn), 25)
        repeated = {r['interval_start_local'] for r in autumn if 'T02:00' in r['interval_start_local']}
        self.assertEqual(repeated, {'2025-10-26T02:00:00+02:00', '2025-10-26T02:00:00+01:00'})
        for day, segment in [('2025-04-15', 'H_JAN_APR'), ('2025-04-16', 'OUTSIDE_APR_JUL'),
                             ('2025-10-14', 'OUTSIDE_AUG_OCT'), ('2025-10-15', 'H_OCT_DEC')]:
            self.assertTrue(all(r['segment_id'] == segment for r in rows if r['interval_start_local'].startswith(day)))

    def test_utc_shift_gap_duplicate_and_naive_intervals_reject(self):
        for mode in ('shift', 'gap', 'duplicate', 'naive'):
            rows = copy.deepcopy(self.reference['rows'])
            if mode == 'shift':
                rows[0]['interval_start_utc'] = (annual.START + annual.HOUR).isoformat()
            elif mode == 'gap':
                rows.pop(100)
            elif mode == 'duplicate':
                rows[100] = copy.deepcopy(rows[99])
            else:
                rows[0]['interval_start_utc'] = '2024-12-31T23:00:00'
            with self.subTest(mode=mode), self.assertRaises(ValueError): annual._segment_profile(rows)

    def test_unknown_or_unserved_energy_is_not_zero_filled(self):
        for key, value in [('status', 'Q'), ('unserved_heat_kwh', 1), ('device_reference_electricity_kwh', None)]:
            rows = copy.deepcopy(self.reference['rows']); rows[25][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): annual._segment_profile(rows)

    def test_wrong_original_weather_identity_rejects(self):
        with self.assertRaisesRegex(ValueError, 'weather bytes'):
            annual.calculate_reference(weather_path=self.weather, package='ambitious')

    def test_original_incomplete_package_cannot_be_priced(self):
        with self.assertRaises(ValueError): self.evaluate(package='original')

    def test_a1_allowance_used_once_per_settlement_portion(self):
        r = self.evaluate(scheme='A1')
        self.assertEqual(len(r['pricing_calls']), 2)
        self.assertEqual(sum(x['discounted_kwh'] for x in r['pricing_calls']), Decimal(1000))
        self.assertEqual([x['connection_months_exact'] for x in r['pricing_calls']], ['7', '5'])
        with localcontext() as ctx:
            ctx.prec = 50
            expected = sum(native.price_a1(x['reference_kwh'], x['supplied_allocation_kwh'], x['connection_months'], 'MVM Démász').consumption_charge_huf for x in r['pricing_calls'])
        self.assertEqual(r['reference_consumption_charge_huf'], expected)

    def test_h_outside_is_continuous_and_has_one_allowance(self):
        r = self.evaluate(); calls = r['pricing_calls']
        self.assertEqual([x['period_id'] for x in calls], ['H_JAN_APR', 'H_OUTSIDE', 'H_OCT_DEC'])
        outside = calls[1]
        self.assertEqual(outside['start_local_date'], '2025-04-16')
        self.assertEqual(outside['end_local_date_inclusive'], '2025-10-14')
        self.assertEqual(outside['discounted_kwh'], Decimal(50))
        with self.assertRaises(ValueError):
            self.evaluate(discounted_allocations={'OUTSIDE_APR_JUL': 50, 'OUTSIDE_AUG_OCT': 50})

    def test_native_replay_all_regions_and_both_tariffs(self):
        for scheme in ('A1', 'H'):
            for region in ('MVM Démász', 'MVM Émász', 'ELMŰ', 'E.ON Dél/E.ON Észak/OPUS'):
                with self.subTest(scheme=scheme, region=region):
                    r = self.evaluate(scheme=scheme, distributor_area=region)
                    with localcontext() as ctx:
                        ctx.prec = 50
                        energy = fixed = Decimal(0)
                        for x in r['pricing_calls']:
                            p = {'period_id': x['period_id'], 'start': annual.date.fromisoformat(x['start_local_date']),
                                 'end': annual.date.fromisoformat(x['end_local_date_inclusive'])}
                            b = annual._native_bill(p, scheme, region, x['reference_kwh'],
                                x['supplied_allocation_kwh'] or 0, x['connection_months'], annual.H_LOAD, 'PROFILED_LOW_VOLTAGE')
                            energy += b.consumption_charge_huf; fixed += b.fixed_charge_huf
                        self.assertEqual(r['reference_consumption_charge_huf'], energy)
                        self.assertEqual(r['declared_connection_charge_huf'], fixed)

    def test_single_connection_fee_is_separate_and_not_end_use_attribution(self):
        r = self.evaluate()
        self.assertEqual(r['connection_months'], 12)
        self.assertAlmostEqual(float(r['declared_connection_charge_huf']), 1214.2224193548387)
        self.assertIsNone(r['connection_charge_attributed_to_device_huf'])
        self.assertFalse(r['alternatives_are_additive'])

    def test_missing_inputs_do_not_evaluate_as_zero(self):
        for change in [{'discounted_allocations': None}, {'discounted_allocations': {}}, {'connection_ledger': None},
                       {'discounted_allocations': {'H_OUTSIDE': None}}, {'discounted_allocations': {'H_OUTSIDE': -1}},
                       {'discounted_allocations': {'H_OUTSIDE': 'NaN'}}]:
            with self.subTest(change=change), self.assertRaises(ValueError): self.evaluate(**change)

    def test_forged_connection_and_missing_or_duplicate_month_reject(self):
        l = ledger()
        bad = [replace(l, connection_id=None), replace(l, calendar_year=True), replace(l, calendar_year=2024),
               replace(l, coverage='PARTIAL'), replace(l, months=l.months[:-1]),
               replace(l, months=l.months[:-1] + (l.months[0],)), replace(l, months=(None,) + l.months[1:])]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError): self.evaluate(connection_ledger=value)

    def test_monthly_fraction_budget_and_regime_reject(self):
        l = ledger()
        for month, fractions in [(4, (('H_HEATING', 1),)), (4, (('H_HEATING', 1), ('H_OUTSIDE', 1))),
                                  (5, (('H_HEATING', 1),)), (1, (('H_HEATING', None),)),
                                  (1, (('H_HEATING', 1), ('H_HEATING', 0))), (1, (('A1', 1),))]:
            rows = tuple(annual.MonthFee(month, fractions) if x.month == month else x for x in l.months)
            with self.subTest(month=month, fractions=fractions), self.assertRaises(ValueError):
                self.evaluate(connection_ledger=replace(l, months=rows))

    def test_fee_fraction_invalid_numbers_reject(self):
        for value in (None, True, float('nan'), float('inf'), -1, 2):
            with self.subTest(value=value), self.assertRaises(ValueError): annual._fraction(value)

    def test_scope_and_unknown_region_reject(self):
        for change in [{'condition': None}, {'scheme': 'B'}, {'scheme': []}, {'load_scope': 'BATTERY'},
                       {'connection_scope': 'SMART_METER'}, {'distributor_area': 'unknown'}]:
            with self.subTest(change=change), self.assertRaises(ValueError): self.evaluate(**change)

    def test_symbolic_response_selects_no_allocation_or_fee(self):
        args = self.args(); args.pop('discounted_allocations'); args.pop('connection_ledger')
        with patch.object(annual, '_manifest', return_value=self.manifest): r = annual.price_response(**args)
        self.assertIsNone(r['evaluated_total_huf'])
        self.assertEqual([x['allocation_key'] for x in r['terms']], [None, 'H_OUTSIDE', None])

    def test_native_nominal_basis_and_unknown_installed_cost_preserved(self):
        r = self.evaluate()
        self.assertEqual(r['price_status'], 'SCN_CONSTANT_2026_TARIFF_SNAPSHOT')
        self.assertEqual(r['monetary_basis'], 'NOMINAL_FROZEN_2026')
        self.assertEqual(r['currency'], 'HUF'); self.assertEqual(r['tariff_snapshot_date'], '2026-10-01')
        for key in ('whole_household_bill_huf', 'installed_cost_huf', 'site_eligibility'):
            self.assertIsNone(r[key])
        for key in ('is_installed_cost_lower_bound', 'b12_cashflow_admission', 'installed_signed_residual_priced'):
            self.assertFalse(r[key])

    def test_decimal_callers_precision_does_not_change_charge(self):
        expected = self.evaluate()
        with localcontext() as ctx:
            ctx.prec = 2
            actual = self.evaluate()
        self.assertEqual(expected, actual)

    def test_zero_energy_still_retains_connection_charge(self):
        p = {'period_id': 'H_JAN_APR', 'start': annual.date(2025, 1, 1), 'end': annual.date(2025, 4, 15)}
        b = annual._native_bill(p, 'H', 'MVM Démász', 0, 0, 1, annual.H_LOAD, 'PROFILED_LOW_VOLTAGE')
        self.assertEqual(b.consumption_charge_huf, 0); self.assertEqual(b.fixed_charge_huf, Decimal('50.165'))


if __name__ == '__main__':
    unittest.main()
