import itertools
import json
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest

from modules.B02 import current_area_reference as area


class AreaBudgetTests(unittest.TestCase):
    def test_open_tail_stays_open_without_national_budget(self):
        self.assertEqual(area._band_budget({'SQM_GE120': 2}), (2, F(240), None))

    def test_zero_open_tail_does_not_remove_finite_maximum(self):
        self.assertEqual(area._band_budget({'SQM_GE120': 0, 'SQM_LT30': 2}), (2, F(0), F(60)))

    def test_projection_matches_independent_finite_enumeration(self):
        # Every integer population consistent with these tiny bands; no midpoint.
        for lo, hi in [(65, 65), (67, 72), (75, 80)]:
            feasible = [(a, b) for a, b in itertools.product(range(30, 41), range(30, 41))
                        if lo <= a + b <= hi]
            self.assertEqual(area._partition_bounds({'SQM30-39': 1}, {'SQM30-39': 1}, lo, hi),
                             (min(a for a, b in feasible), max(a for a, b in feasible)))

    def test_selected_and_complement_open_tails(self):
        self.assertEqual(area._partition_bounds({'SQM_GE120': 1}, {'SQM_GE120': 1}, 300, 320),
                         (F(120), F(200)))

    def test_finite_complement_gives_positive_lower_constraint(self):
        self.assertEqual(area._partition_bounds({'SQM_GE120': 1}, {'SQM_LT30': 1}, 160, 180),
                         (F(130), F(180)))

    def test_infeasible_total_rejects(self):
        for counts, total in [({'SQM_GE120': 1}, (200, 239)), ({'SQM_LT30': 1}, (61, 70))]:
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                area._partition_bounds(counts, counts, *total)

    def test_invalid_counts_reject(self):
        for bad in [{}, {'unknown': 1}, {'SQM_LT30': -1}, {'SQM_LT30': True}, {'SQM_LT30': 1.5}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                area._band_budget(bad)

    def test_invalid_total_and_empty_partitions_reject(self):
        for lo, hi in [(-1, 10), (20, 10), (True, 10), (0, float('inf')), (0, None)]:
            with self.subTest(lo=lo, hi=hi), self.assertRaises(ValueError):
                area._partition_bounds({'SQM_LT30': 1}, {'SQM_LT30': 1}, lo, hi)
        with self.assertRaises(ValueError):
            area._partition_bounds({'SQM_LT30': 0}, {'SQM_LT30': 1}, 0, 30)

    def test_source_substitution_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'source.csv'; p.write_text('changed source')
            with self.assertRaisesRegex(ValueError, 'identity'):
                area._pin(p, '0' * 64)


class CurrentAreaReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = area.calculate_reference()

    def test_exact_population_and_no_synthetic_join(self):
        r = self.result
        self.assertEqual(r['observed_joint_rows'], 116452)
        self.assertEqual(r['reported_control']['occupied_dwellings'], 4008541)
        g = r['interpretations']['NEAREST_WHOLE_ASS']['groups']
        self.assertEqual(g['NON_DISTRICT']['dwellings'], 3389817)
        self.assertEqual(g['NON_DISTRICT_GAS_ONLY']['dwellings'], 1788022)
        self.assertEqual(g['NON_DISTRICT_OTHER']['dwellings'], 1601795)
        self.assertEqual(g['DISTRICT']['band_counts']['SQM_GE120'], 945)

    def test_exact_observed_band_and_budget_bounds(self):
        r = self.result['interpretations']['NEAREST_WHOLE_ASS']
        self.assertEqual(r['national_area_m2']['lower_exact'], '653392183/2')
        self.assertEqual(r['national_area_m2']['upper_exact'], '661409265/2')
        b = r['groups']['NON_DISTRICT']['total_area_m2']
        self.assertEqual(b['lower_exact'], '259044860')
        self.assertEqual(b['upper_exact'], '601867905/2')

    def test_coherent_wider_sensitivity_contains_primary_set(self):
        a, b = (self.result['interpretations'][k] for k in area.CONVENTIONS)
        self.assertEqual(b['national_area_m2']['lower_exact'], '324691821')
        self.assertEqual(b['national_area_m2']['upper_exact'], '332708903')
        for group in a['groups']:
            x, y = a['groups'][group]['total_area_m2'], b['groups'][group]['total_area_m2']
            self.assertLessEqual(F(y['lower_exact']), F(x['lower_exact']))
            self.assertGreaterEqual(F(y['upper_exact']), F(x['upper_exact']))

    def test_all_historical_transfers_rejected_without_changing_source(self):
        for interpretation in self.result['interpretations'].values():
            rows = interpretation['historical_experiments']
            self.assertEqual(len(rows), 4)
            self.assertTrue(all(not row['compatible_with_current_area_set'] for row in rows))
            self.assertTrue(all(row['shortfall_to_lower_m2'] > 0 for row in rows))
        rows = self.result['interpretations']['WIDER_ROUNDING_SENSITIVITY']['historical_experiments']
        reference = next(row for row in rows if row['case'] == 'REFERENCE_EXPERIMENT')
        self.assertAlmostEqual(reference['shortfall_to_lower_m2'], 6094711.3987201)

    def test_unknown_heat_and_weights_not_promoted(self):
        r = self.result
        self.assertEqual(r['evidence_status'], 'DER')
        self.assertEqual(r['evidence_tier'], 'E2_PROVISIONAL_BASE')
        for field in ('cell_area_means', 'heated_area_m2', 'annual_useful_heat_kwh'):
            self.assertIsNone(r[field])
        for field in ('national_heat_admission', 'type_weights_changed', 'automatic_national_rescaling'):
            self.assertIs(r[field], False)
        self.assertTrue(all(x['rounding_status'] == 'ASS' for x in r['interpretations'].values()))
        self.assertIn('not statistical confidence', r['interval_meaning'])
        json.dumps(r, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
