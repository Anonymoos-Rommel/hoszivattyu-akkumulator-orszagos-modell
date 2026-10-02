"""Actual native-ledger consumer and fail-closed conditional screen tests."""
import copy
import csv
import json
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from modules.B02 import national_accounting_bounds as bounds

ROOT = Path(__file__).resolve().parents[1]


class NationalAccountingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref, cls.manifest = bounds.load_reference()
        cls.report = cls.ref.report(cls.manifest)

    def test_native_count_reconciliation(self):
        self.assertEqual(self.report['population_counts'], {
            'NON_DISTRICT': 3389817, 'CENSUS_GAS_ONLY': 1788022,
            'EXPLICIT_GAS_CODED_UNION': 2496034})
        self.assertEqual(sum(self.report['census_fuel_partition'].values()) + 618724, 4008541)

    def test_ambiguous_combination_not_silently_classified(self):
        self.assertEqual(self.report['census_fuel_partition']['FUEL23'], 123910)
        self.assertIn('UNRESOLVED', self.report['ambiguous_FUEL23_gas_membership'])
        self.assertEqual(set(self.report['census_fuel_partition']), set(bounds.FUEL_CODES))

    def test_exact_native_energy_caps(self):
        self.assertEqual(self.ref.gas_service_gwh, D('18608.558275484032488'))
        self.assertEqual(self.ref.gas_final_gwh, D('27782.192703750693228'))
        self.assertEqual(self.ref.all_service_gwh, D('29266.7554342249645332516'))

    def test_direct_gas_leaf_not_parent_or_dhw(self):
        with (ROOT / 'data/processed/b02/jrc_sh_dhw_cohorts_2022_2023.csv').open() as f:
            cells = {x['native_code']: D(x['value']) for x in csv.DictReader(f) if x['reference_year'] == '2022'}
        self.assertEqual(self.ref.gas_service_gwh, cells[bounds.GAS_TES] * D('11.63'))
        self.assertNotEqual(self.ref.gas_service_gwh, cells['TES.ktoe.HU.Res.HH.Thermal.SH.Gas.SH'] * D('11.63'))
        self.assertEqual(self.ref.gas_final_gwh, cells[bounds.GAS_FEC] * D('11.63'))

    def test_carrier_label_in_standalone_bounds_and_screen(self):
        self.assertEqual(self.ref.gas_saving_screen(1)['source_carrier'], 'Natural gas and biogas')
        for q in bounds.QUANTITIES[:2]:
            self.assertEqual(self.report['source_bounds'][q]['source_carrier'], 'Natural gas and biogas')

    def test_whole_group_mean_is_gas_only_and_conservative(self):
        mean = self.report['whole_census_gas_only_mean_gas_service']
        actual = F(self.ref.gas_service_gwh) * 1000000 / 1788022
        self.assertGreaterEqual(F(mean['upper']), actual)
        self.assertLess(F(mean['upper']) - actual, F(1, 10**40))
        self.assertEqual(mean['denominator_dwellings'], 1788022)
        self.assertIn('annual gas exclusivity', mean['condition'])
        exact = mean['upper_exact_ratio']
        self.assertEqual(F(exact['numerator_gwh_times_1000000']) / exact['denominator_dwellings'], actual)
        self.assertTrue(mean['not_for_selected_group_scaling'])

    def test_nonempty_selection_does_not_prorate_energy(self):
        for n in (1, 1000, 1788022):
            for q, expected in zip(bounds.QUANTITIES, (self.ref.gas_service_gwh, self.ref.gas_final_gwh, self.ref.all_service_gwh)):
                with self.subTest(n=n, q=q):
                    r = self.ref.conditional_subset_bound(q, selected_dwellings=n, population='CENSUS_GAS_ONLY')
                    self.assertEqual(D(r['upper']), expected)
                    self.assertEqual(r['lower'], '0')
                    self.assertIsNone(r['central_value'])

    def test_empty_selection_is_zero_without_division(self):
        for q in bounds.QUANTITIES:
            r = self.ref.conditional_subset_bound(q, selected_dwellings=0, population='CENSUS_GAS_ONLY')
            self.assertEqual((r['lower'], r['upper']), ('0', '0'))
            self.assertNotIn('mean', r)

    def test_nonempty_other_population_same_source_enclosure(self):
        for population in bounds.POPULATIONS:
            r = self.ref.conditional_subset_bound('GAS_SH_FINAL_ENERGY', selected_dwellings=1, population=population)
            self.assertEqual(D(r['upper']), self.ref.gas_final_gwh)
            self.assertIn('does not prove applicability', r['condition'])

    def test_impossible_selected_count_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            self.ref.conditional_subset_bound('GAS_SH_SERVICE', selected_dwellings=1788023, population='CENSUS_GAS_ONLY')

    def test_illustrative_two_million_gas_only_excluded(self):
        r = self.ref.count_screen(2000000, population='CENSUS_GAS_ONLY')
        self.assertEqual(r['status'], 'EXCLUDED_BY_CENSUS_COUNT')
        self.assertEqual(r['minimum_count_shortfall'], 211978)
        self.assertIn('NOT_ACTIVE_POLICY', r['threshold_status'])

    def test_broader_two_million_not_declared_infeasible_or_feasible(self):
        for group in ('NON_DISTRICT', 'EXPLICIT_GAS_CODED_UNION'):
            self.assertEqual(self.ref.count_screen(2000000, population=group)['status'], 'INCONCLUSIVE')

    def test_exact_count_boundary_not_feasibility_pass(self):
        for group in bounds.POPULATIONS:
            n = self.ref.population_count(group)
            for requested in (0, n - 1, n):
                self.assertEqual(self.ref.count_screen(requested, population=group)['status'], 'INCONCLUSIVE')
            self.assertEqual(self.ref.count_screen(n + 1, population=group)['status'], 'EXCLUDED_BY_CENSUS_COUNT')

    def test_exact_energy_equality_inconclusive(self):
        self.assertEqual(self.ref.gas_saving_screen(self.ref.gas_final_gwh)['status'], 'INCONCLUSIVE')

    def test_energy_one_native_decimal_step_above_excluded(self):
        self.assertEqual(self.ref.gas_saving_screen('27782.192703750693229')['status'], 'EXCLUDED_IF_SOURCE_CONDITIONS_HOLD')

    def test_rounded_cap_must_not_decide_threshold(self):
        self.assertEqual(self.ref.gas_saving_screen('27782.1')['status'], 'INCONCLUSIVE')
        self.assertEqual(self.ref.gas_saving_screen('27782.192703750693227')['status'], 'INCONCLUSIVE')
        self.assertEqual(self.ref.gas_saving_screen('27782.2')['status'], 'EXCLUDED_IF_SOURCE_CONDITIONS_HOLD')

    def test_no_positive_saving_floor_or_zero_feasibility_pass(self):
        for threshold in (0, '0.001', '10000'):
            r = self.ref.gas_saving_screen(threshold)
            self.assertEqual(r['status'], 'INCONCLUSIVE')
            self.assertIsNone(r['positive_saving_floor_gwh_per_year'])
            self.assertEqual(len(r['conditions']), 2)
            self.assertIn('no added gas use', r['conditions'][1])

    def test_no_central_heat_probability_or_policy(self):
        for key in ('central_heat_allocation', 'probability_distribution'):
            self.assertIsNone(self.report[key])
        self.assertIs(self.report['policy_defaults_selected'], False)
        self.assertEqual(self.report['national_feasibility_verdict'], 'INCONCLUSIVE')
        self.assertEqual(len(self.report['validation_debt_ids']), 5)
        self.assertIn('VD-B02-V1-HEAT-ALLOCATION', self.report['validation_debt_ids'])

    def test_outer_bounds_not_statistical_or_attainability_claim(self):
        for r in self.report['source_bounds'].values():
            self.assertIn('NOT_CONFIDENCE_INTERVAL', r['meaning'])
            self.assertIs(r['endpoint_attainability_established'], False)
            self.assertIs(r['positive_floor_identified'], False)
        self.assertIn('independent endpoints', self.report['joint_constraint'])
        self.assertIn('Outside-target', self.report['source_accounting_conditions'][1])

    def test_serializable_no_float_rounding_of_caps(self):
        encoded = json.dumps(self.report, allow_nan=False)
        self.assertEqual(json.loads(encoded), self.report)
        self.assertIn('27782.192703750693228', encoded)

    def test_caller_decimal_context_cannot_round_reference(self):
        with localcontext() as context:
            context.prec = 6
            r, m = bounds.load_reference()
            report = r.report(m)
        self.assertEqual(report, self.report)

    def test_fresh_import_after_low_decimal_precision_preserves_source_caps(self):
        for precision in (1, 2, 6):
            script = (
                "from decimal import getcontext; getcontext().prec=" + str(precision) + "; "
                "from modules.B02 import national_accounting_bounds as b; "
                "import json; r,m=b.load_reference(); "
                "print(json.dumps({'report':r.report(m),'screen':r.gas_saving_screen('28000')}))"
            )
            run = subprocess.run([sys.executable, '-c', script], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            with self.subTest(precision=precision):
                self.assertEqual(result['report'], self.report)
                self.assertEqual(result['screen']['status'], 'EXCLUDED_IF_SOURCE_CONDITIONS_HOLD')

    def test_bad_counts_rejected(self):
        for n in (-1, True, 1.0, '1', D('1'), None):
            with self.subTest(n=n), self.assertRaises(ValueError):
                self.ref.count_screen(n, population='NON_DISTRICT')
            with self.subTest(n=n), self.assertRaises(ValueError):
                self.ref.conditional_subset_bound('GAS_SH_SERVICE', selected_dwellings=n, population='NON_DISTRICT')

    def test_bad_energy_thresholds_rejected(self):
        for x in (-1, True, 1.0, 'NaN', 'sNaN', 'Infinity', '-Infinity', '-0.01', '', 'abc', None):
            with self.subTest(x=x), self.assertRaises(ValueError):
                self.ref.gas_saving_screen(x)

    def test_unknown_population_and_quantity_rejected(self):
        with self.assertRaises(ValueError):
            self.ref.count_screen(1, population='ELIGIBLE_STOCK')
        with self.assertRaises(ValueError):
            self.ref.conditional_subset_bound('TOTAL_GAS_GCV', selected_dwellings=1, population='NON_DISTRICT')

    def test_source_substitution_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'registry').mkdir()
            (root / bounds.MANIFEST).write_text(json.dumps(self.manifest))
            for path in self.manifest['input_artifacts']:
                p = root / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('changed source')
            with patch.object(bounds, 'ROOT', root), self.assertRaisesRegex(ValueError, 'identity mismatch'):
                bounds.load_reference()

    def test_unsupported_contract_changes_fail_closed(self):
        for key, value in (('reference_year', 2023), ('geography', 'DE'), ('national_central_heat_admitted', True),
                           ('policy_defaults_selected', True), ('native_gas_service_code', 'total')):
            m = copy.deepcopy(self.manifest)
            m[key] = value
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / 'registry').mkdir()
                (root / bounds.MANIFEST).write_text(json.dumps(m))
                with self.subTest(key=key), patch.object(bounds, 'ROOT', root), self.assertRaises(ValueError):
                    bounds.load_reference()


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'modules.B02.national_accounting_bounds', *args], cwd=ROOT, capture_output=True, text=True)

    def test_default_report_has_no_selected_threshold(self):
        run = self.run_cli()
        self.assertEqual(run.returncode, 0, run.stderr)
        r = json.loads(run.stdout)
        self.assertNotIn('count_screen', r)
        self.assertNotIn('gas_saving_screen', r)
        self.assertFalse(r['policy_defaults_selected'])

    def test_explicit_scenario_screens(self):
        run = self.run_cli('--rollout-count', '2000000', '--population', 'CENSUS_GAS_ONLY', '--gas-saving-gwh', '30000')
        self.assertEqual(run.returncode, 0, run.stderr)
        r = json.loads(run.stdout)
        self.assertEqual(r['count_screen']['minimum_count_shortfall'], 211978)
        self.assertEqual(r['gas_saving_screen']['status'], 'EXCLUDED_IF_SOURCE_CONDITIONS_HOLD')

    def test_incomplete_scope_rejected(self):
        for args in (('--rollout-count', '1'), ('--population', 'NON_DISTRICT')):
            run = self.run_cli(*args)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('must be supplied together', run.stderr)

    def test_nonfinite_cli_threshold_rejected(self):
        run = self.run_cli('--gas-saving-gwh', 'NaN')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('finite nonnegative', run.stderr)


if __name__ == '__main__':
    unittest.main()
