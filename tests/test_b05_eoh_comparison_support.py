"""Exact-mask numerical regressions; optional local hash-bound input integration."""
import copy
import hashlib
import subprocess
import json
import math
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from tools import analyze_b05_eoh_comparison_support as tool
from tools import validate_registry as validator

ROOT = Path(__file__).resolve().parents[1]


def row(at='2022-01-01 00:00:00', **kw):
    return {'t': datetime.fromisoformat(at), 'H': 0.0, 'E': 0.0, 'CP': 0.0, 'IH': 0.0,
            'A': 7.0, 'F': 35.0, 'R': 30.0, 'HW': None, **kw}


class ComparisonNumericalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.refs = tool.References()

    def analyze(self, rows):
        return tool.analyze_target(iter(rows), self.refs)

    def test_distinct_masks_missing_cp_is_not_zero_and_ih_is_new(self):
        rows = [row(CP=None), row('2022-01-01 00:02:00', H=1, E=2, CP=3, IH=4),
                row('2022-01-01 00:04:00', H=4, E=7, CP=6, IH=None)]
        ledger, _, _ = self.analyze(rows)
        masks = {r['mask']: r for r in ledger}
        self.assertEqual((2, 1, 1, 0), tuple(masks[m]['steps'] for m in tool.MASKS))
        self.assertEqual((4, 7), (masks['HP_E']['H_kWh'], masks['HP_E']['E_kWh']))
        self.assertEqual((3, 5, 3, 2), tuple(masks['HP_E_CP'][k] for k in
                         ('H_kWh', 'E_kWh', 'CP_kWh', 'E_minus_CP_kWh_same_mask')))
        self.assertEqual((1, 2, 4), tuple(masks['HP_E_IH'][k] for k in ('H_kWh', 'E_kWh', 'IH_kWh')))
        self.assertIsNone(masks['HP_E']['CP_kWh'])
        self.assertIsNone(masks['HP_E_IH']['CP_kWh'])
        self.assertEqual(1, masks['HP_E_IH']['H_kWh'])  # IH electricity is not useful heat.

    def test_sign_and_zero_heat_electricity_are_retained(self):
        rows = [row(H=10, E=5, CP=2, IH=2),
                row('2022-01-01 00:02:00', H=9, E=7, CP=1, IH=1),
                row('2022-01-01 00:04:00', H=9, E=8, CP=1, IH=1),
                row('2022-01-01 00:06:00', H=11, E=7, CP=1, IH=1)]
        ledger, _, _ = self.analyze(rows)
        r = next(r for r in ledger if r['mask'] == 'HP_E_CP_IH')
        self.assertEqual((1, 2, -1, -1), tuple(r[k] for k in ('H_kWh', 'E_kWh', 'CP_kWh', 'IH_kWh')))
        self.assertEqual((1, 1, 1, 1), tuple(r[f'{c}_negative_steps'] for c in tool.CHANNELS))
        self.assertEqual((2, 3), (r['H_zero_or_negative_steps'], r['E_kWh_when_H_zero_or_negative']))

    def test_gaps_never_allocate_energy(self):
        ledger, comparisons, coverage = self.analyze([
            row(), row('2022-01-01 00:06:00', H=90, E=30),
            row('2022-01-01 00:08:00', H=91, E=31)])
        self.assertEqual(1, ledger[0]['steps'])
        self.assertEqual(1, ledger[0]['H_kWh'])
        self.assertEqual(1, coverage[0]['excluded_non120_pairs'])
        self.assertAlmostEqual(0.1, coverage[0]['excluded_positive_elapsed_hours_no_energy_allocated'])
        self.assertTrue(all(r['steps'] == 1 for r in comparisons))

    def test_year_assignment_is_current_endpoint(self):
        ledger, _, coverage = self.analyze([row('2021-12-31 23:58:00'), row(H=1, E=2)])
        result = {(r['year_current_endpoint'], r['mask']): r for r in ledger}
        self.assertEqual((0, 1), (result[2021, 'HP_E']['steps'], result[2022, 'HP_E']['steps']))
        self.assertEqual(1, coverage[1]['cross_year_grid120_steps'])

    def test_native_25_and_under30_are_supported_when_cells_exist(self):
        self.assertEqual([25, 35, 40, 45, 50, 55, 60], self.refs.supplies)
        for mode in tool.MODES:
            for flow in (25, 29, 35, 40, 45, 50, 55, 60):
                self.assertIsNotNone(self.refs.evaluate(mode, 7, flow)[1], (mode, flow))

    def test_source_blank_and_domain_fail_closed(self):
        for mode in tool.MODES:
            for a, f, expected in ((-20, 25, 'SOURCE_BLANK'), (-17, 42.5, 'SOURCE_BLANK'),
                                   (7, 24.99, 'OUTSIDE_NATIVE_DOMAIN'), (21, 35, 'OUTSIDE_NATIVE_DOMAIN')):
                status, point = self.refs.evaluate(mode, a, f)
                self.assertEqual(expected, status)
                self.assertIsNone(point)
        custom = tool.References()
        custom.present.remove(('MAX', 7.0, 35.0))
        self.assertEqual('SOURCE_BLANK', custom.evaluate('MAX', 5, 35)[0])

    def test_every_native_cell_preserves_source_availability_and_power(self):
        count = 0
        for source in tool.source_grid():
            status, point = self.refs.evaluate(source['mode'], float(source['outdoor_temperature_c']),
                                               float(source['supply_temperature_c']))
            if source['availability'] == 'SOURCE_BLANK':
                self.assertEqual('SOURCE_BLANK', status)
                self.assertIsNone(point)
            else:
                count += 1
                self.assertEqual('SUPPORTED', status)
                self.assertAlmostEqual(float(source['thermal_capacity_kw']), point.thermal_capacity_kw)
                self.assertAlmostEqual(float(source['cop']), point.cop)
                self.assertAlmostEqual(point.thermal_capacity_kw, point.electrical_input_kw * point.cop)
        self.assertEqual(208, count)

    def test_nonfinite_cells_are_missing_and_timestamp_order_not_repaired(self):
        for value in ('', 'NaN', 'inf', '-inf', None):
            self.assertIsNone(tool.number(value))
        ledger, _, coverage = self.analyze([row('2022-01-01 00:02:00'), row(H=20, E=5)])
        self.assertEqual(0, ledger[0]['steps'])
        self.assertEqual(1, coverage[0]['nonincreasing_timestamp_pairs'])

    def test_hw_flow_never_substitutes_heating_flow(self):
        _, comparisons, _ = self.analyze([row(), row('2022-01-01 00:02:00', H=1, E=2, F=None, HW=35)])
        self.assertTrue(all(r['support'] != 'SUPPORTED' for r in comparisons))
        self.assertTrue(all(r['current_endpoint_reference_mean_COP'] is None for r in comparisons))

    def test_previous_endpoint_must_also_be_supported(self):
        _, comparisons, _ = self.analyze([row(F=24), row('2022-01-01 00:02:00', H=1, E=2)])
        self.assertTrue(all('previous=OUTSIDE_NATIVE_DOMAIN' in r['support'] for r in comparisons))

    def test_actual_reference_values_all_modes_and_identical_measured_mask(self):
        _, comparisons, _ = self.analyze([row(), row('2022-01-01 00:02:00', H=0.1, E=0.05, A=10)])
        yearly = [r for r in comparisons if r['grain'] == 'year' and r['mask'] == 'HP_E']
        self.assertEqual(set(tool.MODES), {r['mode'] for r in yearly})
        for r in yearly:
            native = tool.load_wm50_reference(r['mode']).evaluate(10, 35).point
            self.assertAlmostEqual(native.thermal_capacity_kw, r['current_endpoint_reference_mean_Qh_kW'])
            self.assertAlmostEqual(native.electrical_input_kw, r['current_endpoint_reference_mean_Pel_kW'])
            self.assertAlmostEqual(native.cop, r['current_endpoint_reference_mean_COP'])
            self.assertEqual((0.1, 0.05, 1), (r['H_kWh'], r['E_kWh'], r['steps']))
            self.assertAlmostEqual(3, r['observed_H_mean_kW'])
        with self.assertRaises(ValueError):
            self.refs.evaluate('BEST_COP', 7, 35)

    def test_conditions_and_proxy_do_not_claim_measured_mode(self):
        self.assertEqual('heating_temperature_indicated_not_service_proven', tool.proxy(row(), row()))
        self.assertEqual('DHW_temperature_indicated_not_service_proven', tool.proxy(row(F=None, HW=55), row(F=None, HW=55)))
        self.assertEqual('both_temperature_channels_present_unallocated', tool.proxy(row(HW=55), row(HW=55)))
        self.assertEqual('[25,35)', tool.condition(row(), row(F=29))[2])
        self.assertEqual('missing', tool.condition(row(), row(R=None))[3])

    def test_missing_independent_channels_are_coverage_not_zero(self):
        ledger, _, coverage = self.analyze([row(H=None), row('2022-01-01 00:02:00', H=1, E=2)])
        self.assertEqual(0, ledger[0]['steps'])
        self.assertEqual((1, 1, 2), tuple(coverage[0][k] for k in ('H_missing_steps', 'E_valid_steps', 'E_signed_kWh')))


class ManifestTests(unittest.TestCase):
    def errors(self, mutation=None):
        m = json.loads(tool.MANIFEST.read_text(encoding='utf-8'))
        if mutation:
            mutation(m)
        original = Path.read_text
        def read(path, *args, **kwargs):
            return json.dumps(m) if path == tool.MANIFEST else original(path, *args, **kwargs)
        ids = {r['source_id'] for r in validator.read_csv(ROOT / 'registry/sources.csv')[1]}
        errors = []
        with patch.object(Path, 'read_text', read):
            validator.validate_b05_eoh_comparison_support(errors, ids)
        return errors

    def test_contract_and_original_admission_unchanged(self):
        self.assertEqual([], self.errors())
        m = json.loads(tool.MANIFEST.read_text(encoding='utf-8'))
        for relative, expected in m['protected_sha256'].items():
            if relative == "modules/B11/physical_displacement_contract.py":
                # Historical research identity, not permission for today's replay.
                # Independently read the pinned blob; do not call validator helper.
                blob = subprocess.run(
                    ["git", "--no-replace-objects", "-C", str(ROOT), "show",
                     m["base_commit"] + ":" + relative],
                    capture_output=True, check=False, timeout=10,
                    env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
                )
                self.assertEqual(blob.returncode, 0, blob.stderr.decode(errors="replace"))
                self.assertEqual(expected, hashlib.sha256(blob.stdout).hexdigest())
            else:
                self.assertEqual(expected, tool.digest(ROOT / relative))
        old = json.loads((ROOT / 'registry/b05_eoh_observed_boundary_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual('NOT_COMPUTED', old['selected_rows']['IH']['HP_E_IH_common_intersection'])
        self.assertFalse(old['non_admission']['annual_residual_admitted'])

    def test_admission_mode_flow_mask_and_population_mutations_rejected(self):
        for mutate in (
            lambda m: m['non_admission'].__setitem__('annual_residual_admitted', True),
            lambda m: m['definitions'].__setitem__('mode_policy', 'BEST_COP'),
            lambda m: m['definitions'].__setitem__('flow_substitution', tool.HW),
            lambda m: m['definitions']['masks'].__setitem__('HP_E', ['H', 'E', 'CP']),
            lambda m: m['definitions'].__setitem__('native_supply_C', [30, 35, 40, 45, 50, 55, 60]),
            lambda m: m['definitions'].__setitem__('hybrid_boiler_positive', 'EXCLUDE'),
            lambda m: m['definitions'].__setitem__('gap_fill', True),
            lambda m: m['input_binding'].__setitem__('zip_sha256', '0' * 64),
        ):
            self.assertTrue(self.errors(mutate))

    def test_handoff_hash_and_path_checks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'input.txt'
            source.write_text('test', encoding='utf-8')
            manifest = {'files': [{'path': 'input.txt', 'bytes': 4, 'sha256': tool.digest(source)}], 'input_file_count': 1}
            path = root / 'HANDOFF_MANIFEST.json'
            path.write_text(json.dumps(manifest), encoding='utf-8')
            binding = {'handoff_manifest_sha256': tool.digest(path), 'input_file_count': 1}
            tool.verify_handoff(root, binding)
            source.write_text('fail', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'input identity'):
                tool.verify_handoff(root, binding)
            manifest['files'][0]['path'] = '../outside.txt'
            path.write_text(json.dumps(manifest), encoding='utf-8')
            binding['handoff_manifest_sha256'] = tool.digest(path)
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                tool.verify_handoff(root, binding)


@unittest.skipUnless(os.environ.get('B05_EOH_HANDOFF') and os.environ.get('B05_EOH_OUTPUT'), 'optional hash-bound local inputs/output')
class LocalInputIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff = Path(os.environ['B05_EOH_HANDOFF'])
        cls.output = Path(os.environ['B05_EOH_OUTPUT'])
        cls.spec = json.loads(tool.MANIFEST.read_text(encoding='utf-8'))
        tool.verify_handoff(cls.handoff, cls.spec['input_binding'])
        cls.comparisons = list(tool.read_csv(cls.output / 'eoh2074_matched_comparisons.csv'))
        cls.ledger = list(tool.read_csv(cls.output / 'eoh2074_year_ledger.csv'))

    def test_original_annual_controls_and_negative_control(self):
        numerical = [{k: (v if k in ('status', 'mask') else None if v == '' else float(v)) for k, v in r.items()} for r in self.ledger]
        controls = list(tool.read_csv(self.handoff / 'eoh2074/EOH2074_all_period_common_interval_year.csv'))
        checks = tool.check_ledger(numerical, controls)
        self.assertEqual(45, len(checks))
        altered = copy.deepcopy(numerical)
        next(r for r in altered if r['mask'] == 'HP_E')['H_kWh'] += 1
        with self.assertRaisesRegex(ValueError, 'ledger mismatch'):
            tool.check_ledger(altered, controls)

    def test_support_partition_and_conditions_conserve_each_mask_energy(self):
        for ledger in self.ledger:
            for mode in tool.MODES:
                subset = [r for r in self.comparisons if r['year_current_endpoint'] == ledger['year_current_endpoint'] and r['mask'] == ledger['mask'] and r['mode'] == mode]
                for grain in ('year', 'condition'):
                    selected = [r for r in subset if r['grain'] == grain]
                    for column in ('steps', 'H_kWh', 'E_kWh', 'E_kWh_when_H_zero_or_negative'):
                        self.assertAlmostEqual(float(ledger[column]), math.fsum(float(r[column]) for r in selected), places=7)
                    for column in ('CP_kWh', 'IH_kWh'):
                        if ledger[column] == '':
                            self.assertTrue(all(r[column] == '' for r in selected))
                        else:
                            self.assertAlmostEqual(float(ledger[column]), math.fsum(float(r[column]) for r in selected), places=7)

    def test_all_comparative_tables_preserved_and_boiler_positive_retained(self):
        summary = tool.summarize_hybrids(tool.read_csv(self.handoff / 'comparison/documented_SH_primary_comparative_population.csv'))
        self.assertGreater(summary['boiler_positive_windows_retained'], 0)
        self.assertEqual(1, summary['cross_year_windows_retained'])
        self.assertFalse(summary['WM50_calibration'])
        for source in (self.handoff / 'comparison').iterdir():
            self.assertEqual(tool.digest(source), tool.digest(self.output / 'comparison_source_tables' / source.name))
        clock = list(tool.read_csv(self.output / 'hybrid_exact_selected_interval_calendar_clock_support.csv'))
        self.assertEqual(96019, sum(int(r['steps']) for r in clock))
        windows = list(tool.read_csv(self.handoff / 'comparison/documented_SH_primary_comparative_population.csv'))
        cross = next(r for r in windows if r['year_start'] != r['year_end'])
        self.assertEqual(('2021', '2022', '98'), (cross['year_start'], cross['year_end'], cross['steps']))

    def test_output_hashes_and_actual_references(self):
        manifest = json.loads((self.output / 'OUTPUT_MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(tool.digest(tool.MANIFEST), manifest['comparison_manifest_sha256'])
        for item in manifest['outputs']:
            self.assertEqual(item['sha256'], tool.digest(self.output / item['path']))
        supported = [r for r in self.comparisons if r['grain'] == 'year' and r['support'] == 'SUPPORTED']
        self.assertEqual(48, len(supported))
        self.assertTrue(all(float(r['current_endpoint_reference_mean_Qh_kW']) > 0 for r in supported))
        self.assertTrue(all(float(r['current_endpoint_reference_mean_Pel_kW']) > 0 for r in supported))

    def test_existing_output_is_never_overwritten(self):
        before = tool.digest(self.output / 'OUTPUT_MANIFEST.json')
        with self.assertRaises(FileExistsError):
            tool.run(self.handoff, self.output)
        self.assertEqual(before, tool.digest(self.output / 'OUTPUT_MANIFEST.json'))


if __name__ == '__main__':
    unittest.main()
