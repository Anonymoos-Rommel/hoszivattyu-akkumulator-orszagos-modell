import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest
from unittest.mock import patch
from modules.B04.engine import TariffInputError, price_a1, price_h_heating

ROOT = Path(__file__).resolve().parents[1]
SCOPE = 'ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES'


class CanonicalTariffConsumerTests(unittest.TestCase):
    def test_a1_reads_canonical_area_rates_and_adds_fixed_once(self):
        expected = {'MVM Démász': '36.386', 'E.ON Dél/E.ON Észak/OPUS': '35.293', 'ELMŰ': '36.208', 'MVM Émász': '35.992'}
        for area, rate in expected.items():
            bill = price_a1(2524, 2523, 12, area)
            self.assertEqual(bill.total_huf, Decimal(2523) * Decimal(rate) + Decimal('70.104') + Decimal('1836.42'))
            self.assertEqual(bill.excess_kwh, 1)
            self.assertTrue(bill.source_ids)

    def test_h_uses_final_price_not_energy_component_and_no_heating_cap(self):
        bill = price_h_heating(3000, 1, 'MVM Démász', date(2026, 3, 1), date(2026, 3, 31), load_scope=SCOPE)
        self.assertEqual(bill.total_huf, Decimal(3000) * Decimal('22.962') + Decimal('50.165'))
        self.assertEqual(bill.excess_kwh, 0)
        self.assertNotEqual(bill.consumption_charge_huf, Decimal(3000) * Decimal('2.41'))

    def test_h_outside_interval_and_noneligible_load_fail_closed(self):
        for start, end in [(date(2026, 4, 15), date(2026, 4, 16)), (date(2026, 10, 14), date(2026, 10, 15))]:
            with self.assertRaises(TariffInputError):
                price_h_heating(1, 1, 'MVM Démász', start, end, load_scope=SCOPE)
        for scope in ['BATTERY', 'EXPORT', 'HOUSEHOLD', 'Q']:
            with self.assertRaises(TariffInputError):
                price_h_heating(1, 1, 'MVM Démász', date(2026, 3, 1), date(2026, 3, 31), load_scope=scope)

    def test_invalid_numeric_inputs_are_not_free_energy(self):
        for value in [-1, 'NaN', 'Infinity', '-Infinity', None]:
            for argument in range(3):
                inputs = [100, 200, 1]; inputs[argument] = value
                with self.assertRaises(TariffInputError):
                    price_a1(*inputs, 'MVM Démász')
        with self.assertRaises(TariffInputError):
            price_a1(100, 200, 1, 'UNKNOWN')

    def test_missing_or_duplicate_high_rate_is_a_typed_failure(self):
        from modules.B04.engine import _rows
        rows = _rows('residential_electricity_tariff_schedule.csv')
        high = next(r for r in rows if r['tariff_id'] == 'A1-ALL-MARKET')
        for bad in [[r for r in rows if r['tariff_id'] != 'A1-ALL-MARKET'], rows + [dict(high)]]:
            with patch('modules.B04.engine._rows', return_value=bad):
                with self.assertRaises(TariffInputError):
                    price_a1(3000, 2523, 1, 'MVM Démász')

    def test_unadmitted_source_status_cannot_be_priced(self):
        from modules.B04.engine import _rows
        rows = _rows('residential_electricity_tariff_schedule.csv')
        bad = [dict(r, status='Q') if r['tariff_id']=='A1-ALL-MARKET' else r for r in rows]
        with patch('modules.B04.engine._rows', return_value=bad):
            with self.assertRaises(TariffInputError):
                price_a1(3000, 2523, 1, 'MVM Démász')

    def test_result_is_explicit_frozen_price_scenario_not_an_actual_invoice(self):
        for year in [2025, 2027]:
            bill = price_h_heating(1, 1, 'MVM Démász', date(year, 3, 1), date(year, 3, 31), load_scope=SCOPE)
            self.assertEqual(bill.status, 'SCN_CONSTANT_2026_TARIFF_SNAPSHOT')
            self.assertEqual(bill.tariff_snapshot_date, date(2026, 10, 1))
            self.assertIn('NOT_HISTORICAL_OR_FUTURE_INVOICE', bill.price_basis)

    def test_h_component_bridge_reconciles_source_rounding(self):
        with (ROOT/'data/processed/electricity_price_component_bridge.csv').open() as f:
            row = next(r for r in csv.DictReader(f) if r['bridge_id']=='B04-H-DÉMÁSZ-BRIDGE')
        gross = (Decimal(row['energy_net_huf_per_kwh']) + Decimal(row['network_charge_huf_per_kwh'])) * (1 + Decimal(row['vat_rate']))
        self.assertLess(abs(gross - Decimal(row['final_gross_huf_per_kwh'])), Decimal('0.00051'))

    def test_outside_discounted_energy_exists_but_full_bill_is_not_invented(self):
        with (ROOT/'data/processed/h_tariff_schedule.csv').open() as f:
            rows = list(csv.DictReader(f))
        outside = [r for r in rows if r['period_type']=='outside season discounted energy']
        self.assertEqual(len(outside), 4)
        self.assertTrue(all(r['net_huf_per_kwh'] and r['final_price_status']=='Q' and not r['final_gross_huf_per_kwh'] for r in outside))
        self.assertTrue(all(r['battery_charging_status']=='Q' and r['export_status']=='Q' for r in rows))


if __name__ == '__main__':
    unittest.main()
