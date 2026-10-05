import copy
from decimal import Decimal
import unittest
from modules.B04.engine import _rows
from tools.verify_b04_b_alap_extract import AREAS, parse_source_tables, verify_rates


class TariffSourceVerifierTests(unittest.TestCase):
    def tables(self):
        facts = [('5.250', '1.900', '36.386', '22.962'),
                 ('4.390', '2.340', '35.293', '23.520'),
                 ('5.110', '2.050', '36.208', '23.152'),
                 ('4.940', '1.680', '35.992', '22.682')]
        lines = []
        for a, b, af, bf in facts:
            lines += [f'{a} 31.800 {b} 31.800', '120.500 120.500 39.500 39.500',
                      '23.400 23.400 16.180 16.180', '153.035 153.035 50.165 50.165',
                      f'{af} 70.104 {bf} 60.935']
        return parse_source_tables('\n'.join(line.replace('.', ',') for line in lines))

    def test_all_numeric_controls_match_curated_rates(self):
        result = verify_rates(self.tables(), _rows('residential_electricity_tariff_schedule.csv'),
                              _rows('h_tariff_schedule.csv'))
        self.assertEqual([r['distributor_area'] for r in result], list(AREAS))
        self.assertEqual(result[0]['b_excess_gross_huf_kwh'], '60.935')

    def test_incomplete_or_extra_table_is_rejected(self):
        for n in (0, 19, 21):
            with self.assertRaises(ValueError):
                parse_source_tables('\n'.join(['1,000 2,000 3,000 4,000']*n))

    def test_component_changes_cannot_hide_behind_unchanged_final_rate(self):
        for field in ('energy_price_net_huf_per_kwh', 'energy_price_gross_huf_per_kwh',
                      'network_charge_huf_per_kwh', 'fixed_charge_huf_per_year'):
            rows = _rows('residential_electricity_tariff_schedule.csv')
            row = next(r for r in rows if r['tariff_id'] == 'B-ALAP-DÉMÁSZ-DISCOUNTED')
            row[field] = str(Decimal(row[field])+Decimal('.001'))
            with self.assertRaises(ValueError):
                verify_rates(self.tables(), rows, _rows('h_tariff_schedule.csv'))

    def test_outside_h_mapping_numeric_drift_is_rejected(self):
        rows = _rows('h_tariff_schedule.csv')
        row = next(r for r in rows if r['tariff_id'] == 'H-DÉMÁSZ-OUTSIDE-DISCOUNTED')
        row['fixed_gross_huf_per_month'] = '50.165'
        with self.assertRaises(ValueError):
            verify_rates(self.tables(), _rows('residential_electricity_tariff_schedule.csv'), rows)

    def test_missing_duplicate_rate_or_tier_dependent_fixed_fee_is_rejected(self):
        original = _rows('residential_electricity_tariff_schedule.csv')
        high = next(r for r in original if r['tariff_id'] == 'B-ALAP-ALL-MARKET')
        for rows in ([r for r in original if r is not high], original+[dict(high)]):
            with self.assertRaises(ValueError):
                verify_rates(self.tables(), rows, _rows('h_tariff_schedule.csv'))
        tables = copy.deepcopy(self.tables())
        tables[0]['base_gross'][3] = Decimal('0')
        with self.assertRaises(ValueError):
            verify_rates(tables, original, _rows('h_tariff_schedule.csv'))


if __name__ == '__main__':
    unittest.main()
