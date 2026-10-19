"""Load-matched energy arithmetic, preserved controls and explicit non-identification."""
import copy
import json
import math
import os
import unittest
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from tools import analyze_b05_eoh_annual_transfer as a
from tools import validate_registry as validator


def row(at='2022-01-01T00:00:00', **values):
    return {'t': datetime.fromisoformat(at), 'H': 0., 'E': 0., 'CP': 0., 'IH': 0.,
            'A': 7., 'F': 55., 'R': 48., 'HW': None, **values}


class EnergyMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = a.LoadReference()

    def test_ordered_load_interpolation_is_power_not_best_cop(self):
        points, reason = self.model.points(7, 55)
        self.assertIsNone(reason)
        lo, hi = points[0:2]
        q = (lo[0] + hi[0]) / 2
        result = self.model.evaluate(q, 7, 55)
        self.assertEqual('PAIRED_POWER_CONTINUOUS', result['branch'])
        self.assertAlmostEqual((lo[1] + hi[1]) / 2, result['reference_kWh'])
        self.assertEqual(1., result['stage_on_fraction'])

    def test_minimum_stage_components_sum_once_and_duration_scales(self):
        points, _ = self.model.points(7, 55)
        q, p = points[0]
        result = self.model.evaluate(q / 4, 7, 55, duration_h=.5)
        self.assertAlmostEqual(.25 * p * .5, result['active_kWh'])
        self.assertAlmostEqual(p * (140 / 1370) * .25 * .75 * .5, result['inertia_kWh'])
        self.assertAlmostEqual(.015 * .75 * .5, result['idle_kWh'])
        self.assertAlmostEqual(sum(result[k] for k in ('active_kWh', 'inertia_kWh', 'idle_kWh')), result['reference_kWh'])

    def test_zero_heat_keeps_declared_idle_and_negative_heat_not_clipped(self):
        zero = self.model.evaluate(0, 30, 55, duration_h=2)
        self.assertEqual((0., 0., .03, .03), tuple(zero[k] for k in ('active_kWh', 'inertia_kWh', 'idle_kWh', 'reference_kWh')))
        negative = self.model.evaluate(-1, 7, 55)
        self.assertIsNone(negative['reference_kWh'])
        self.assertIn('NEGATIVE_HEAT', negative['branch'])

    def test_unserved_or_blank_never_supplies_same_service_reference(self):
        self.assertIsNone(self.model.evaluate(1, -17, 42.5)['reference_kWh'])
        above = self.model.evaluate(20, 7, 55)
        self.assertEqual('ABOVE_MAX_NOT_SAME_SERVICE', above['branch'])
        self.assertIsNone(above['reference_kWh'])
        self.assertGreater(above['unserved_H_kWh'], 0)

    def test_reversed_modes_and_conflicting_equal_capacity_fail_closed(self):
        original = self.model.guard.evaluate
        def altered(mode, ambient, flow):
            status, p = original(mode, ambient, flow)
            if mode == 'MAX':
                from dataclasses import replace
                p = replace(p, thermal_capacity_kw=.1)
            return status, p
        model = a.LoadReference()
        with patch.object(model.guard, 'evaluate', altered):
            self.assertIn('REVERSED', model.points(7, 55)[1])

    def test_physical_nonfinite_or_nonpositive_duration_rejected(self):
        for q, ta, f, h in ((math.nan, 7, 55, 1), (1, math.inf, 55, 1), (1, 7, 55, 0)):
            with self.assertRaises(ValueError):
                self.model.evaluate(q, ta, f, duration_h=h)

    def test_gaps_and_missing_counters_split_without_energy_allocation(self):
        rows = [row(), row('2022-01-01T00:02:00', H=1., E=2.),
                row('2022-01-01T00:08:00', H=50., E=40.),
                row('2022-01-01T00:10:00', H=51., E=42.)]
        segments = list(a.segments(rows, 60, 0))
        self.assertEqual(2, len(segments))
        self.assertEqual((2., 4., 2), (sum(s['H'] for s in segments), sum(s['E'] for s in segments), sum(s['steps'] for s in segments)))

    def test_signed_heat_zero_heat_electricity_and_missing_cp_ih_retained(self):
        rows = [row(), row('2022-01-01T00:02:00', H=-1., E=2., CP=None, IH=None)]
        segment = next(a.segments(rows, 2, 0))
        output = a.segment_reference(segment, self.model)
        self.assertEqual((-1., 2., 2.), tuple(output[k] for k in ('H_kWh', 'E_kWh', 'zero_or_negative_heat_E_kWh')))
        self.assertIsNone(output['CP_kWh_complete_same_mask'])
        self.assertIsNone(output['IH_kWh_complete_same_mask'])
        self.assertFalse(output['same_SH_service_proven'])

    def test_immersion_electricity_never_becomes_heat(self):
        segment = next(a.segments([row(), row('2022-01-01T00:02:00', H=.02, E=.03, IH=2.)], 2, 0))
        output = a.segment_reference(segment, self.model)
        self.assertEqual((.02, 2.), (output['H_kWh'], output['IH_kWh_complete_same_mask']))

    def test_calendar_year_assignment_and_no_invented_timezone(self):
        output = a.segment_reference(next(a.segments([row('2021-12-31T23:58:00'), row(H=.1, E=.05)], 60, 0)), self.model)
        self.assertEqual((2022, '2022-01', 'Q'), (output['year_current_endpoint'], output['month'], output['timezone']))

    def test_hw_flow_is_not_substituted_and_proxies_split(self):
        rows = [row(), row('2022-01-01T00:02:00', H=.1, E=.1, F=None, HW=55.)]
        result = a.segment_reference(next(a.segments(rows, 30, 0)), self.model)
        self.assertIsNone(result['reference_kWh'])
        self.assertFalse(result['all_endpoint_heating_flow_near55'])

    def test_aggregation_keeps_measured_energy_but_exposes_reference_sensitivity(self):
        rows = [row(), row('2022-01-01T00:02:00', H=0., E=.01),
                row('2022-01-01T00:04:00', H=.04, E=.03)]
        fine = [a.segment_reference(s, self.model) for s in a.segments(rows, 2, 0)]
        coarse = [a.segment_reference(s, self.model) for s in a.segments(rows, 30, 0)]
        self.assertAlmostEqual(sum(s['H_kWh'] for s in fine), sum(s['H_kWh'] for s in coarse))
        self.assertAlmostEqual(sum(s['E_kWh'] for s in fine), sum(s['E_kWh'] for s in coarse))
        self.assertNotAlmostEqual(sum(s['reference_kWh'] for s in fine), sum(s['reference_kWh'] for s in coarse), places=8)

    def test_segment_mean_cannot_hide_original_source_blank(self):
        rows = [row(A=-20., F=25.), row('2022-01-01T00:02:00', H=.01, E=.02, A=20., F=25.)]
        result = a.segment_reference(next(a.segments(rows, 30, 0)), self.model)
        self.assertEqual('Q_ORIGINAL_ENDPOINT_SOURCE_SUPPORT', result['branch'])
        self.assertIsNone(result['reference_kWh'])

    def test_shifted_hour_segments_can_cross_recorded_clock_hour(self):
        rows = [row('2022-01-01T00:58:00'), row('2022-01-01T01:00:00', H=.01, E=.02),
                row('2022-01-01T01:02:00', H=.02, E=.04)]
        parts = list(a.segments(rows, 60, 30))
        self.assertEqual(1, len(parts))
        self.assertEqual(2, parts[0]['steps'])

    def test_conditional_mapping_replaces_complete_reference_not_adds_overhead(self):
        target = [dict(interval_start_utc='2025-01-01T00:00:00+00:00', ambient_C=7., load_over_min=.3,
                       generator_H_kWh=1., reference_kWh=.4, stage_on_fraction=.3)]
        cell = a.transfer_cell(7., .3, True)
        cells = {'2min_offset0': {(2021, *cell): dict(E=2., reference=1., H=3., hours=4., segments=2)}}
        rows, support = a.target_transfer(target, cells, {})
        year = next(r for r in rows if r['donor_year'] == 2021)
        self.assertEqual((.8, .4), (year['conditional_replacement_E_kWh'], year['conditional_signed_delta_kWh']))
        self.assertIsNone(year['installed_total_kWh'])
        unknown = next(r for r in support if r['donor_year'] == 2022 and r['support'] == 'UNIDENTIFIED')
        self.assertEqual((1., 1., .4), (unknown['hours'], unknown['H_kWh'], unknown['reference_E_kWh']))
        self.assertIsNone(unknown['conditional_replacement_E_kWh'])

    def test_hybrid_context_never_turns_into_transfer(self):
        target = [dict(interval_start_utc='2025-01-01T00:00:00+00:00', ambient_C=7., load_over_min=.3,
                       generator_H_kWh=1., reference_kWh=.4, stage_on_fraction=.3)]
        rows, _ = a.target_transfer(target, {'2min_offset0': {}}, {a.transfer_cell(7., .3, True): {'home1'}})
        self.assertTrue(all(r['support'] == 'UNIDENTIFIED' and r['hybrid_context_systems_not_transfer'] == 1 for r in rows))

    def test_lower_supply_is_retained_in_explicit_normalized_route(self):
        s = next(a.segments([row(F=35.), row('2022-01-01T00:02:00', H=.02, E=.01, F=35.)], 60, 0, self.model))
        r = a.segment_reference(s, self.model)
        pools = {}; a.collect_eoh_routes(pools, '60min_offset0', r, self.model)
        self.assertTrue(any(k[1] == 'EOH_ACTUAL_CONDITIONS_TO_W55' for k in pools))
        self.assertFalse(any(k[1] == 'EOH_NEAR55_OBSERVED' for k in pools))

    def test_bad_endpoint_splits_before_aggregation_and_preserves_ledger(self):
        data = [row(F=35.), row('2022-01-01T00:02:00', H=.02, E=.01, F=35.),
                row('2022-01-01T00:04:00', H=.04, E=.02, F=None),
                row('2022-01-01T00:06:00', H=.06, E=.03, F=35.),
                row('2022-01-01T00:08:00', H=.08, E=.04, F=35.)]
        parts = list(a.segments(data, 60, 0, self.model))
        self.assertEqual(['SUPPORTED', 'MISSING_ENDPOINT_CONDITIONS', 'SUPPORTED'], [s['source_status'] for s in parts])
        self.assertAlmostEqual(.08, sum(s['H'] for s in parts))
        self.assertAlmostEqual(.04, sum(s['E'] for s in parts))
        good = [a.segment_reference(s, self.model) for s in parts if s['source_status'] == 'SUPPORTED']
        self.assertEqual(2, sum(s['steps'] for s in good))
        self.assertTrue(all(s['reference_kWh'] is not None for s in good))

    def test_IH_over_whole_E_is_not_clamped_or_automatically_subtracted(self):
        r = {'temperature_proxy': 'heating_temperature_indicated_not_service_proven',
             'H_kWh': .1, 'E_kWh': .02, 'IH_kWh_complete_same_mask': .03}
        self.assertEqual((.1, .02), a.allocated_observation(r, 'HEATING_PROXY_WHOLE_E')[0])
        self.assertEqual('IH_OUTSIDE_AGGREGATED_WHOLE_E_BOUNDARY', a.allocated_observation(r, 'HEATING_PROXY_LESS_IH_VALID')[1])

    def test_conditional_and_E2_qualification_follow_evidence_and_coverage(self):
        conditional = {'mapping': {'status': 'CONDITIONAL', 'source_ids': ['source']}}
        justified = {'mapping': {'status': 'JUSTIFIED_FOR_TARGET', 'source_ids': ['source']}}
        self.assertEqual('SCN_COMPLETE_CONDITIONAL', a.route_qualification(complete=True, physical=True, documented_assumptions=conditional)[0])
        self.assertEqual('SCN_COMPLETE_CONDITIONAL', a.route_qualification(complete=True, physical=True, documented_assumptions=justified)[0])
        self.assertNotEqual('E2_CANDIDATE', a.route_qualification(complete=False, physical=True, documented_assumptions=justified)[0])

    def test_eight_point_qualification_cannot_leak_between_routes_or_boundaries(self):
        binding=json.loads(a.MANIFEST.read_text(encoding='utf-8'))['aggregate_assessment']['binding']
        record=dict(binding=binding,e2_criteria=[dict(criterion=i,verdict='SUPPORTED_PROVISIONAL',
                    reason='claim-specific applicability assessment',quantitative_or_source_locators=['assessment.csv']) for i in range(1,9)])
        def qualify(context=binding, records=None, complete=True, physical=True):
            return a.route_qualification(complete=complete,physical=physical,route_context=context,
                documented_assumptions={'qualification_records':[record] if records is None else records})[0]
        self.assertEqual('E2_CANDIDATE',qualify())
        for key in a.QUALIFICATION_BINDING_KEYS:
            self.assertNotEqual('E2_CANDIDATE',qualify({**binding,key:'OTHER'}),key)
        self.assertNotEqual('E2_CANDIDATE',qualify(complete=False))
        self.assertNotEqual('E2_CANDIDATE',qualify(physical=False))
        for broken in ([],[record,record], [{**record,'e2_criteria':record['e2_criteria'][:7]}]):
            self.assertNotEqual('E2_CANDIDATE',qualify(records=broken))
        for criterion in range(8):
            bad=copy.deepcopy(record);bad['e2_criteria'][criterion]['reason']=''
            self.assertNotEqual('E2_CANDIDATE',qualify(records=[bad]))
            bad=copy.deepcopy(record);bad['e2_criteria'][criterion]['verdict']='CONDITIONAL_NOT_IDENTIFIED'
            self.assertNotEqual('E2_CANDIDATE',qualify(records=[bad]))

    def test_paired_energy_prediction_keeps_idle_once_and_missing_cells_unknown(self):
        target=[dict(interval_start_utc='2025-01-01',ambient_C=7.,load_over_min=.3,
                     generator_H_kWh=1.,reference_kWh=.5,active_kWh=.3,inertia_kWh=.1,idle_kWh=.1)]
        cell=a.transfer_cell(7.,.3,True)
        p={cell:dict(variable_ref=.4,variable_E=.8)}
        pred,_=a.assessment_predict(target,p,{})
        self.assertAlmostEqual(.9,pred['conditional_annual_E_kWh'])
        pred,_=a.assessment_predict(target,{},{})
        self.assertIsNone(pred['conditional_annual_E_kWh'])
        self.assertEqual(0,pred['supported_hours'])

    def test_documented_mode_does_not_impute_transitions_missing_or_return_channel(self):
        self.assertEqual('SH_MODE_ENDPOINTS',a.interval_mode(row(),row()))
        self.assertEqual('DHW_MODE_ENDPOINTS',a.interval_mode(row(F=None,HW=50.),row(F=None,HW=51.)))
        self.assertEqual('SH_DHW_TRANSITION',a.interval_mode(row(),row(F=None,HW=50.)))
        self.assertEqual('MISSING_MODE',a.interval_mode(row(F=None,R=48.),row(F=None,R=48.)))
        self.assertEqual('BOTH_CHANNELS_UNALLOCATED',a.interval_mode(row(HW=50.),row(HW=50.)))
        self.assertEqual('MODE_BOUNDARY_OR_INCOMPLETE',a.interval_mode(row(),row(F=None)))

    def test_assessment_derives_coverage_and_physical_validity_from_predictions(self):
        binding=json.loads(a.MANIFEST.read_text(encoding='utf-8'))['aggregate_assessment']['binding']
        record=dict(binding=binding,e2_criteria=[dict(criterion=i,verdict='SUPPORTED_PROVISIONAL',reason='scoped evidence',
                    quantitative_or_source_locators=['evidence.csv']) for i in range(1,9)])
        target=[dict(interval_start_utc='2025-02-01T00:00:00+00:00',generator_H_kWh=1.)]
        valid=[dict(interval_start_utc=target[0]['interval_start_utc'],supported=True,conditional_E_kWh=.5)]
        self.assertEqual('E2_CANDIDATE',a.qualify_assessment(target,valid,record)['qualification'])
        for predictions in ([],valid+valid,[{**valid[0],'supported':False}],
                            [{**valid[0],'interval_start_utc':'WRONG'}],[{**valid[0],'conditional_E_kWh':None}]):
            result=a.qualify_assessment(target,predictions,record)
            self.assertFalse(result['complete'])
            self.assertNotEqual('E2_CANDIDATE',result['qualification'])
        for energy in (-1.,0.,float('inf'),float('nan')):
            result=a.qualify_assessment(target,[{**valid[0],'conditional_E_kWh':energy}],record)
            self.assertFalse(result['physical'])
            self.assertNotEqual('E2_CANDIDATE',result['qualification'])

    def test_variable_replacement_adds_target_idle_exactly_once(self):
        target = [dict(interval_start_utc='2025-01-01T00:00:00+00:00', ambient_C=7., load_over_min=.3,
                       generator_H_kWh=1., reference_kWh=.5, active_kWh=.3, inertia_kWh=.1, idle_kWh=.1)]
        pools = {}; obs = dict(recorded_start='2022-01-01', recorded_end='2022-01-02', hours=1.)
        ref = dict(reference_kWh=.5, active_kWh=.3, inertia_kWh=.1, idle_kWh=.1)
        a.add_pool(pools, ('60min_offset0','EOH_ACTUAL_CONDITIONS_TO_W55','HEATING_PROXY_WHOLE_E','EOH2074',2022,a.transfer_cell(7.,.3,True)),obs,1.,.9,ref)
        _, results = a.evaluate_transfer_routes(target,pools,{}, {'mapping':{'status':'CONDITIONAL','source_ids':['source']}})
        r = next(r for r in results if r['accounting']=='VARIABLE_REPLACEMENT_IDLE_ONCE' and r['donor_year']=='ALL_YEARS_POOLED')
        self.assertAlmostEqual(.9,r['conditional_full_annual_E_kWh'])
        self.assertIsNone(r['admissible_E2_annual_E_kWh'])

    def test_hybrid_fixed_CP_and_boiler_share_are_not_added_twice(self):
        source = dict(category=a.comparison.CATEGORY, HP_heat_kWh='1', whole_E_kWh='1', hours='1',
            PDI_size_kW='4', ambient_mean_C='7', flow_mean_C='55', CP_valid_steps='30', steps='30',
            CP_kWh_valid_steps_only='.2', boiler_valid_steps='30', boiler_signed_kWh_valid_steps_only='1',
            start='2022-01-01T00:00:00', end='2022-01-01T01:00:00', property_id='hybrid', year_start='2022',
            boiler_positive_steps='30')
        with patch.object(a, 'csv_rows', return_value=iter([source])):
            pools, _ = a.hybrid_transfer_pools(Path('synthetic'), self.model)
        energy = {k[2]: v['E_kWh'] for k, v in pools.items()}
        self.assertAlmostEqual(1.25, energy['LINEAR_ALL_E'])
        self.assertAlmostEqual(1.2, energy['CP_NONSCALING_RETAINED'])
        self.assertAlmostEqual(1.1, energy['BOILER_SHARED_CP_HEAT_SHARE'])
        self.assertTrue(all(v['boiler_positive_windows'] == 1 for v in pools.values()))


class ManifestAndControlTests(unittest.TestCase):
    def errors(self, change=None):
        spec = json.loads(a.MANIFEST.read_text(encoding='utf-8'))
        if change:
            change(spec)
        original = Path.read_text
        def read(path, *args, **kwargs):
            return json.dumps(spec) if path == a.MANIFEST else original(path, *args, **kwargs)
        ids = {r['source_id'] for r in validator.read_csv(a.ROOT / 'registry/sources.csv')[1]}
        errors = []
        with patch.object(Path, 'read_text', read):
            validator.validate_b05_eoh_annual_transfer(errors, ids)
        return errors

    def test_new_research_contract_and_protected_canonical_bytes(self):
        self.assertEqual([], self.errors())
        spec = json.loads(a.MANIFEST.read_text(encoding='utf-8'))
        self.assertNotEqual(spec['recovered_weather']['sha256'], spec['recovered_weather']['old_canonical_weather_sha256_unchanged'])
        for path, expected in spec['protected_sha256'].items():
            self.assertEqual(expected, a.digest(a.ROOT / path))

    def test_weather_identity_guard_admission_and_double_count_mutations_reject(self):
        for change in (
            lambda m: m['recovered_weather'].__setitem__('canonical_guard_bypassed', True),
            lambda m: m['recovered_weather'].__setitem__('sha256', m['recovered_weather']['old_canonical_weather_sha256_unchanged']),
            lambda m: m['target'].__setitem__('expected_device_reference_kWh', 2472.633793065277 + 82.1090879123),
            lambda m: m['target'].__setitem__('components_included', ['active_rating']),
            lambda m: m['target'].__setitem__('installed_annual_kWh', 3000),
            lambda m: m['non_admission'].__setitem__('central_E2_installed_selected', True),
            lambda m: m['aggregate_assessment'].__setitem__('prediction_admission_gates', 'HARDCODED_TRUE'),
            lambda m: m['aggregate_assessment']['season_state_matching'].__setitem__('partial_support_annualized', True),
            lambda m: m['target_weighted_assessment'].__setitem__('canonical_or_national_admission', True),
            lambda m: m['target_weighted_assessment']['boundary'].__setitem__('modeled_duty_is_measured_controller_state', True),
            lambda m: m['circulation_identification'].__setitem__('target_pump_kWh',100.),
            lambda m: m['circulation_identification']['topology']['candidate_only'].__setitem__('assigned_to_donor',True),
        ):
            self.assertTrue(self.errors(change))

    def test_period_controls_detect_missing_or_changed_month(self):
        annual = [dict(property_id='home', year='2021', present_rows='2', HP_E_common_steps='2')]
        monthly = [dict(property_id='home', month='2021-01', present_rows='1', HP_E_common_steps='1'),
                   dict(property_id='home', month='2021-02', present_rows='1', HP_E_common_steps='1')]
        self.assertEqual(2, len(a.check_period_controls(annual, monthly)))
        with self.assertRaises(ValueError):
            a.check_period_controls(annual, monthly[:1])


@unittest.skipUnless(os.environ.get('B05_ANNUAL_ADDITIVE') and os.environ.get('B05_ANNUAL_OUTPUT'), 'optional hash-bound local input/output')
class LocalIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.additive = Path(os.environ['B05_ANNUAL_ADDITIVE'])
        cls.output = Path(os.environ['B05_ANNUAL_OUTPUT'])
        cls.spec = json.loads(a.MANIFEST.read_text(encoding='utf-8'))
        a.verify_additive(cls.additive, cls.spec)

    def test_all_weather_rows_and_reference_components_independently_reproduce(self):
        weather = a.recovered_weather(self.additive, self.spec)
        _, summary = a.target_reference(weather, a.LoadReference(), self.spec)
        self.assertEqual(2472.633793065277, summary['device_reference_kWh'])
        self.assertEqual({'MINIMUM_STAGE_ONOFF_E2_TRANSFER': 6028, 'PAIRED_POWER_CONTINUOUS': 72, 'ZERO_HEAT': 2660}, summary['branch_hours'])
        self.assertAlmostEqual(2321.7472067406616, summary['active_kWh'])
        self.assertAlmostEqual(68.77749841231555, summary['inertia_kWh'])
        self.assertAlmostEqual(82.10908791230001, summary['idle_kWh'])
        self.assertAlmostEqual(6050.554431653909, summary['generator_H_kWh'])

    def test_target_support_partitions_close_and_unknown_not_zero_energy(self):
        rows = list(a.csv_rows(self.output / 'target_support_by_year_and_aggregation.csv'))
        for minutes, offset in a.AGGREGATIONS:
            for year in ('2021', '2022', '2023', 'ALL_YEARS_POOLED'):
                selected = [r for r in rows if r['aggregation'] == f'{minutes}min_offset{offset}' and r['donor_year'] == year]
                self.assertEqual(2, len(selected))
                for column, expected in (('hours', 8760.), ('H_kWh', 6050.554431653909), ('reference_E_kWh', 2472.633793065277)):
                    self.assertAlmostEqual(expected, math.fsum(float(r[column]) for r in selected), places=7)
                self.assertTrue(all(r['qualified_direct_hours'] == '0.0' and r['installed_annual_point_estimate_kWh'] == '' for r in selected))
                self.assertEqual('', next(r for r in selected if r['support'] == 'UNIDENTIFIED')['conditional_replacement_E_kWh'])

    def test_all_years_original_controls_and_hybrid_population_remain(self):
        years = list(a.csv_rows(self.output / 'all_34_system_year_observed_period_balances.csv'))
        months = list(a.csv_rows(self.output / 'all_34_system_month_observed_period_balances.csv'))
        self.assertEqual((98, 901, 34), (len(years), len(months), len({r['property_id'] for r in years})))
        self.assertEqual(45, len(list(a.csv_rows(self.output / 'eoh2074_original_45_year_control_checks.csv'))))
        windows = list(a.csv_rows(self.output / 'hybrid_all_windows_counterfactual_context.csv'))
        self.assertEqual((4546, 96019, 3334), (len(windows), sum(int(r['steps']) for r in windows), sum(int(r['boiler_positive_steps']) > 0 for r in windows)))
        self.assertTrue(all(r['cross_product_transfer_qualified'] == 'False' for r in windows))
        self.assertEqual(1, sum(r['year_start'] != r['year_end'] for r in windows))

    def test_output_hash_chain_and_no_central_point(self):
        manifest = json.loads((self.output / 'INPUT_CODE_OUTPUT_MANIFEST.json').read_text())
        if os.environ.get('B05_E2_ASSESSMENT_OUTPUT'):
            self.assertEqual(self.spec['aggregate_assessment']['prior_merged_code_sha256'],manifest['research_code_sha256'])
            self.assertEqual(self.spec['aggregate_assessment']['prior_output_manifest_sha256'],a.digest(self.output/'INPUT_CODE_OUTPUT_MANIFEST.json'))
        else:
            self.assertEqual(a.digest(a.MANIFEST), manifest['research_manifest_sha256'])
            self.assertEqual(a.digest(Path(a.__file__)), manifest['research_code_sha256'])
        for item in manifest['outputs']:
            self.assertEqual(item['sha256'], a.digest(self.output / item['path']))
        decision = json.loads((self.output / 'ANNUAL_TRANSFER_DECISION.json').read_text())
        self.assertIsNone(decision['selected_central_E2_installed_kWh'])
        self.assertIsNone(decision['annual_signed_installed_residual_kWh'])
        self.assertGreater(decision['evaluated_route_variants'], 0)
        self.assertGreater(decision['complete_conditional_variants'], 0)

    def test_reviewer_recovered_intervals_and_complementary_energy(self):
        recovery = json.loads((self.output / 'preaggregation_split_recovery_summary.json').read_text())
        self.assertEqual(493, recovery['old_segments_with_supported_positive_steps'])
        self.assertEqual(6758, recovery['supported_positive_2min_steps_recovered'])
        self.assertAlmostEqual(594.518, recovery['H_kWh_recovered'], places=7)
        self.assertAlmostEqual(165.109, recovery['E_kWh_recovered'], places=7)

    def test_evaluated_engineering_routes_and_broad_zero_state_are_numeric(self):
        variants = list(a.csv_rows(self.output / 'evaluated_annual_transfer_routes.csv'))
        self.assertEqual({'EOH_NEAR55_OBSERVED','EOH_ACTUAL_CONDITIONS_TO_W55','HYBRID_AGGREGATE_TO_W55'}, {r['route'] for r in variants})
        complete = [r for r in variants if r['conditional_full_annual_E_kWh'] != '']
        self.assertTrue(complete)
        self.assertTrue(all(r['admissible_E2_annual_E_kWh'] == '' for r in variants))
        base = next(r for r in variants if r['aggregation']=='60min_offset0' and r['route']=='EOH_ACTUAL_CONDITIONS_TO_W55'
                    and r['assumption']=='HEATING_PROXY_WHOLE_E' and r['donor_year']=='ALL_YEARS_POOLED'
                    and r['accounting']=='VARIABLE_REPLACEMENT_IDLE_ONCE')
        self.assertEqual(8760.,float(base['supported_hours']))
        cells=list(a.csv_rows(self.output/'all_evaluated_donor_route_cells.csv'))
        zero=[r for r in cells if r['aggregation']=='60min_offset0' and r['route']=='EOH_ZERO_MONTH_POWER'
              and r['assumption']=='HEATING_PROXY_WHOLE_E']
        self.assertGreater(math.fsum(float(r['hours']) for r in zero),1000.)
        audit=list(a.csv_rows(self.output/'service_IH_CP_zero_heat_boundary_audit.csv'))
        self.assertGreater(sum(int(r['IH_exceeds_E_segments']) for r in audit if r['aggregation']=='2min_offset0'),0)


class TargetWeightingMethodTests(unittest.TestCase):
    def sample(self,month='01',duty=.3):
        t=dict(interval_start_utc=f'2025-{month}-01T00:00:00+00:00',ambient_C=7.,load_over_min=.3,
               stage_on_fraction=duty,generator_H_kWh=1.,reference_kWh=.5,active_kWh=.3,inertia_kWh=.1,idle_kWh=.1)
        donor=dict(year='2022',month='01',day='2022-01-01',cell=a.weighted_cell(7.,.3,.3),ref_var=.4,
                   H_kWh=1.,E_kWh=.9,idle_kWh=.1,hours=1.,IH=.1,CP=.2,joint_valid=True,
                   endpoint_proxy_mean_flow_C=30.,return_C=25.)
        return t,donor

    def test_target_month_heat_reference_duty_and_month_pooling_are_explicit(self):
        self.assertEqual(a.month_kernel('12','01',1),a.month_kernel('01','02',1))
        self.assertEqual(0,a.month_kernel('01','02',0))
        t,d=self.sample('02');g=a.weighted_target_groups([t])
        c,_,_=a.target_weighted_coefficients(g,[d],bandwidth=0)
        self.assertFalse(c['complete_positive_target'])
        c,_,_=a.target_weighted_coefficients(g,[d],bandwidth=1)
        self.assertTrue(c['complete_positive_target'])
        self.assertEqual(1,c['supported_H_kWh'])
        self.assertAlmostEqual(.9,a.conditional_response(c,.5,0,0)['conditional_annual_kWh'])
        january={**t,'interval_start_utc':'2025-01-01T00:00:00+00:00'}
        june={**t,'interval_start_utc':'2025-06-01T00:00:00+00:00'}
        july_donor={**d,'month':'07','day':'2022-07-01','E_kWh':1.7}
        jan,_,_=a.target_weighted_coefficients(a.weighted_target_groups([january]),[d,july_donor],bandwidth=1)
        jun,_,_=a.target_weighted_coefficients(a.weighted_target_groups([june]),[d,july_donor],bandwidth=1)
        pooled,_,_=a.target_weighted_coefficients(a.weighted_target_groups([january]),[d,july_donor],bandwidth=None)
        self.assertLess(a.conditional_response(jan,.5,0,0)['conditional_annual_kWh'],1.)
        self.assertGreater(a.conditional_response(jun,.5,0,0)['conditional_annual_kWh'],1.6)
        self.assertAlmostEqual(1.3,a.conditional_response(pooled,.5,0,0)['conditional_annual_kWh'])
        t['stage_on_fraction']=.8
        c,_,_=a.target_weighted_coefficients(a.weighted_target_groups([t]),[d],bandwidth=1)
        self.assertFalse(c['complete_positive_target'])

    def test_paired_component_allocation_and_fixed_CP_replacement_do_not_double_idle(self):
        t,d=self.sample();c,_,_=a.target_weighted_coefficients(a.weighted_target_groups([t]),[d],cohort='JOINT_VALID')
        self.assertAlmostEqual(.9,a.conditional_response(c,.5,0,0)['conditional_annual_kWh'])
        self.assertAlmostEqual(.5,a.conditional_response(c,.5,0,0,theta=0)['conditional_annual_kWh'])
        self.assertAlmostEqual(.8,a.conditional_response(c,.5,0,0,IH_excluded=1)['conditional_annual_kWh'])
        self.assertAlmostEqual(.7,a.conditional_response(c,.5,0,0,CP_excluded=1)['conditional_annual_kWh'])
        self.assertAlmostEqual(.06,c['CP_fixed_reference_on_coefficient_kWh'])
        self.assertAlmostEqual(.2,c['CP_fixed_positive_hours_coefficient_kWh'])
        c,_,_=a.target_weighted_coefficients(a.weighted_target_groups([t]),[d])
        with self.assertRaises(ValueError):a.conditional_response(c,.5,0,0,IH_excluded=1)

    def test_conditional_response_has_no_fabricated_transfer_upper_bound_or_partial_annual(self):
        t,d=self.sample();c,_,_=a.target_weighted_coefficients(a.weighted_target_groups([t]),[d])
        self.assertGreater(a.conditional_response(c,.5,0,0,theta=100)['conditional_annual_kWh'],30.)
        self.assertIn('NOT_HOURLY_ADMISSION',a.conditional_response(c,.5,0,0,theta=100)['physical_response_scope'])
        bad=a.conditional_response(c,.5,0,0,theta=-100)
        self.assertFalse(bad['physical_response']);self.assertIsNone(bad['conditional_annual_kWh'])
        partial={**c,'complete_positive_target':False}
        self.assertIsNone(a.conditional_response(partial,.5,0,0)['conditional_annual_kWh'])
        with self.assertRaises(ValueError):a.conditional_response(c,.5,0,0,theta=float('nan'))

    def test_service_allocation_cannot_silently_repeat_component_exclusion(self):
        t,d=self.sample();c,_,_=a.target_weighted_coefficients(a.weighted_target_groups([t]),[d],cohort='JOINT_VALID')
        for exclusions in ({'IH_excluded':1.},{'CP_excluded':1.},{'IH_excluded':.5,'CP_excluded':.5}):
            with self.assertRaisesRegex(ValueError,'mixed allocation is undefined'):
                a.conditional_response(c,.5,0,0,service_share=.5,**exclusions)
        self.assertAlmostEqual(.45,a.conditional_response(c,.5,0,0,service_share=.5)['conditional_annual_kWh'])
        self.assertAlmostEqual(.7,a.conditional_response(c,.5,0,0,CP_excluded=1.)['conditional_annual_kWh'])

    def test_finite_parameters_cannot_overflow_derived_energy_balances(self):
        t,d=self.sample();c,_,_=a.target_weighted_coefficients(a.weighted_target_groups([t]),[d])
        scenarios=[({**c,'whole_coefficient_kWh':10.},.5,0.,0.,{'theta':1e308}),
                   ({**c,'whole_coefficient_kWh':1e308,'donor_idle_coefficient_kWh':-1e308},.5,0.,0.,{}),
                   (c,.5,1e308,-1e308,{}),
                   (c,.5,2.,0.,{'zero_transfer':1e308}),
                   ({**c,'whole_coefficient_kWh':1e308,'donor_idle_coefficient_kWh':0.,'target_variable_kWh':0.},1e308,0.,0.,{}),
                   ({**c,'whole_coefficient_kWh':1e308,'donor_idle_coefficient_kWh':0.,'target_variable_kWh':0.},1e308,1e308,1e308,{})]
        for coefficients,reference,zero_observed,zero_reference,parameters in scenarios:
            with self.assertRaisesRegex(ValueError,'nonfinite derived energy'):
                a.conditional_response(coefficients,reference,zero_observed,zero_reference,**parameters)


@unittest.skipUnless(os.environ.get('B05_TARGET_WEIGHTED_OUTPUT'), 'optional target monthly/duty output')
class TargetWeightedIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output=Path(os.environ['B05_TARGET_WEIGHTED_OUTPUT'])
        cls.result=json.loads((cls.output/'TARGET_WEIGHTED_RESPONSE_FAMILY.json').read_text())

    def test_preserved_reference_complete_support_and_new_output_identity(self):
        manifest=json.loads((self.output/'INPUT_CODE_OUTPUT_MANIFEST.json').read_text())
        if os.environ.get('B05_CP_OUTPUT'):
            spec=json.loads(a.MANIFEST.read_text(encoding='utf-8'))
            self.assertEqual(spec['circulation_identification']['prior_corrected_weighted_manifest_sha256'],a.digest(self.output/'INPUT_CODE_OUTPUT_MANIFEST.json'))
        else:
            self.assertEqual(a.digest(Path(a.__file__)),manifest['source_code_sha256'])
            self.assertEqual(a.digest(a.MANIFEST),manifest['source_manifest_sha256'])
        for item in manifest['outputs']:self.assertEqual(item['sha256'],a.digest(self.output/item['path']))
        self.assertEqual(2472.633793065277,self.result['reference_kWh'])
        self.assertAlmostEqual(4003.3949236948883,self.result['preserved_conditional_route_kWh'],places=7)
        c=self.result['anchor_coefficients']
        self.assertEqual(6100,c['supported_hours']);self.assertEqual(2660,self.result['zero_target_hours'])
        self.assertAlmostEqual(6050.554431653909,c['supported_H_kWh'],places=7)
        self.assertIsNone(self.result['selected_central_kWh'])
        self.assertTrue(self.result['no_finite_total_uncertainty_interval'])
        with self.assertRaisesRegex(ValueError,'nonfinite derived energy'):
            a.conditional_response(c,self.result['reference_kWh'],self.result['zero_observed_kWh'],
                                   self.result['zero_reference_kWh'],theta=1e308)

    def test_target_state_shares_are_normalized_conditional_not_observed(self):
        rows=list(a.csv_rows(self.output/'target_cell_conditional_donor_state_shares.csv'))
        sums={}
        for r in rows:
            key=tuple(r[k] for k in ('target_month','ambient_bin','reference_load_bin','reference_duty_bin'))
            sums[key]=sums.get(key,0.)+float(r['conditional_donor_reference_share'])
            self.assertIn('NOT_OBSERVED_TARGET_SHARES',r['share_status'])
        for total in sums.values():self.assertAlmostEqual(1,total)
        self.assertAlmostEqual(2390.524705152976,math.fsum(float(r['target_variable_exposure_kWh']) for r in rows),places=7)
        months=list(a.csv_rows(self.output/'target_monthly_positive_energy_and_support.csv'))
        self.assertAlmostEqual(6050.554431653909,math.fsum(float(r['target_H_kWh']) for r in months),places=7)

    def test_pooling_support_and_sampling_uncertainty_are_not_population_bounds(self):
        rows=list(a.csv_rows(self.output/'declared_month_pooling_flow_accounting_responses.csv'))
        primary=[r for r in rows if r['cohort']=='ALL_HE' and r['flow_range']=='None']
        strict=next(r for r in primary if r['bandwidth_months']=='0.0')
        self.assertEqual('',strict['conditional_annual_kWh']);self.assertEqual(5043,int(strict['supported_hours']))
        pooled=next(r for r in primary if r['bandwidth_months']=='')
        self.assertAlmostEqual(4003.3949236948883,float(pooled['conditional_annual_kWh']),places=7)
        sampling=list(a.csv_rows(self.output/'within_installation_block_multiplier_responses.csv'))
        self.assertEqual(300,len(sampling))
        self.assertTrue(all(r['is_population_confidence_interval']=='False' and r['central_E2_selected']=='False' for r in sampling))
        for summary in self.result['within_donor_sampling']:
            self.assertEqual(100,summary['complete_replicates'])
            values=sorted(float(r['conditional_annual_kWh']) for r in sampling if int(r['block_days'])==summary['block_days'])
            self.assertEqual(values[49],summary['q50'])


class CPEnergyBlockMethodTests(unittest.TestCase):
    def event(self,at,**changes):
        start=datetime.fromisoformat(at)
        return dict(start=start,end=start+timedelta(minutes=2),mode='SH_MODE_ENDPOINTS',heat_state='POSITIVE',
            ref_available=True,H=.1,E=.02,CP=.005,IH=.001,ref_active=.01,ref_inertia=.001,ref_idle=.0001,**changes)

    def test_contiguous_parent_preserves_service_sign_reference_and_gap_complements(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/'blocks.csv';writer=a.CPEnergyBlocks(path,60)
            writer.add(self.event('2022-01-01T00:00:00'))
            e=self.event('2022-01-01T00:02:00');e.update(mode='DHW_MODE_ENDPOINTS',heat_state='ZERO_WITH_TOLERANCE_1E-8',H=0.,ref_available=False,ref_active=0.,ref_inertia=0.,ref_idle=0.)
            writer.add(e)
            e=self.event('2022-01-01T00:08:00');e.update(heat_state='NEGATIVE',H=-.1,E=-.02,CP=-.005,IH=0.,ref_available=False,ref_active=0.,ref_inertia=0.,ref_idle=0.)
            writer.add(e);writer.close();rows=list(a.csv_rows(path))
            self.assertEqual(2,len({r['block_id'] for r in rows}))
            self.assertEqual({'POSITIVE','NEGATIVE','ZERO_WITH_TOLERANCE_1E-8'},{r['heat_state'] for r in rows})
            self.assertAlmostEqual(.005,math.fsum(float(r['CP_kWh']) for r in rows))
            negative=next(r for r in rows if r['heat_state']=='NEGATIVE')
            self.assertEqual('-0.015',negative['E_minus_CP_kWh'])
            self.assertEqual('',negative['reference_kWh'])
            self.assertEqual('',negative['ref_idle_kWh'])
            for r in rows:self.assertEqual('False',r['residual_is_compressor_electricity'])
            previous=row();current=row(at='2022-01-01T00:02:00')
            self.assertIsNone(a.cp_event(previous,current,{'H':.1,'E':.02,'CP':.005},None))

    def test_reference_comparison_keeps_the_same_measured_subset(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/'blocks.csv';w=a.CPEnergyBlocks(path,60)
            w.add(self.event('2022-01-01T00:00:00'))
            e=self.event('2022-01-01T00:02:00');e.update(ref_available=False,ref_active=0.,ref_inertia=0.,ref_idle=0.)
            w.add(e);w.close()
            self.assertAlmostEqual(2/30,a.cp_block_rows(path)[0]['hours'])
            self.assertAlmostEqual(1/30,a.cp_block_rows(path,reference_only=True)[0]['hours'])

    def test_missing_counter_spans_keep_signed_energy_without_assigning_runtime(self):
        first={};last={};spans=[]
        for minute,cp in ((0,1.),(2,1.1),(4,None),(6,1.3),(8,1.2),(10,None),(12,1.1)):
            r=row(at=f'2022-01-01T00:{minute:02d}:00',CP=cp)
            a.cp_counter_span_ledger(r,first,last,spans)
        self.assertEqual(2,len(spans))
        self.assertAlmostEqual(.2,spans[0]['signed_counter_change_kWh'])
        self.assertAlmostEqual(-.1,spans[1]['signed_counter_change_kWh'])
        self.assertTrue(all(not r['used_in_model_fit'] and not r['missing_intervals_imputed'] for r in spans))

    def test_energy_fit_distinguishes_time_and_reference_and_reports_zero_collinearity(self):
        rows=[dict(hours=t,reference_kWh=r,CP_kWh=.16*t) for t,r in ((1.,.2),(2.,.1),(1.,.7),(2.,1.))]
        time=a.fit_cp_energy_model(rows,'ELAPSED_STATE_TIME');ref=a.fit_cp_energy_model(rows,'PROPORTIONAL_REFERENCE')
        self.assertAlmostEqual(.16,time['time_kW'])
        self.assertLess(a.cp_prediction_error(rows,time)['squared_error_kWh2'],1e-20)
        self.assertGreater(a.cp_prediction_error(rows,ref)['squared_error_kWh2'],.01)
        zero=[dict(hours=t,reference_kWh=.015*t,CP_kWh=.05*t) for t in (1.,2.,3.)]
        joint=a.fit_cp_energy_model(zero,'NONNEGATIVE_TIME_PLUS_REFERENCE')
        self.assertLess(abs(joint['relative_determinant']),1e-10)
        self.assertAlmostEqual(0.,a.cp_prediction_error(zero,joint)['squared_error_kWh2'])

    def test_blocked_prediction_does_not_train_on_held_year_or_impute_unknown_states(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/'blocks.csv';rows=[]
            for i,(year,power) in enumerate((('2021',.1),('2022',.2),('2023',.3))):
                rows.append(dict(block_id=i,year=year,month=year+'-01',service='SH_MODE_ENDPOINTS',heat_state='POSITIVE',
                    reference_available=True,hours=1.,CP_kWh=power,E_kWh=.5,H_kWh=1.,IH_kWh=0.,reference_kWh=1.,
                    ref_active_kWh=1.,ref_inertia_kWh=0.,ref_idle_kWh=0.))
            rows.append({**rows[-1],'block_id':4,'service':'DHW_MODE_ENDPOINTS'})
            a.write_csv(path,rows);folds,_,_=a.cp_blocked_predictive_comparisons(path,'synthetic')
            r=next(r for r in folds if r['fold_type']=='LEAVE_YEAR_OUT' and r['held_block']=='2023'
                   and r['service']=='SH_MODE_ENDPOINTS' and r['model']=='ELAPSED_STATE_TIME')
            self.assertAlmostEqual(.15,r['fitted_time_kW']);self.assertAlmostEqual(-.15,r['bias_kWh'])
            r=next(r for r in folds if r['fold_type']=='LEAVE_YEAR_OUT' and r['held_block']=='2023'
                   and r['service']=='DHW_MODE_ENDPOINTS' and r['model']=='ELAPSED_STATE_TIME')
            self.assertEqual(1,r['unpredicted_blocks']);self.assertEqual(0,r['predicted_blocks'])


@unittest.skipUnless(os.environ.get('B05_CP_OUTPUT'),'optional full-telemetry CP energy output')
class CPIdentificationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.output=Path(os.environ['B05_CP_OUTPUT'])

    def test_reviewed_hash_chain_and_no_target_or_internal_pump_assignment(self):
        manifest=json.loads((self.output/'INPUT_CODE_OUTPUT_MANIFEST.json').read_text())
        self.assertEqual(a.digest(Path(a.__file__)),manifest['source_code_sha256'])
        self.assertEqual(a.digest(a.MANIFEST),manifest['source_manifest_sha256'])
        self.assertEqual('b4d56a129b2cc39822579bf4a0a0693a1988d75b',manifest['reviewed_tree'])
        for r in manifest['outputs']:self.assertEqual(r['sha256'],a.digest(self.output/r['path']))
        result=json.loads((self.output/'CP_EMPIRICAL_IDENTIFICATION.json').read_text())
        self.assertIsNone(result['target_annual_pump_kWh']);self.assertFalse(result['internal_primary_pump_identified'])
        self.assertIn('standard pump correction',result['rating_overlap'])

    def test_every_aggregation_preserves_full_mask_signed_energy_and_contiguity(self):
        closure=json.loads((self.output/'CP_masks_gaps_signed_closure.json').read_text())
        self.assertEqual(544833,closure['channel_masks']['CP']['common_steps'])
        for channel in ('H','E','CP','IH'):
            p=closure['channel_masks'][channel]
            self.assertAlmostEqual(p['independent_kWh'],p['common_kWh']+p['complement_kWh'])
            self.assertAlmostEqual(p['first_to_last_valid_counter_change_kWh'],p['independent_kWh']+p['unallocated_valid_endpoint_span_kWh'])
        for path in self.output.glob('CP_common_blocks_*.csv'):
            rows=list(a.csv_rows(path));self.assertEqual(544833,sum(int(r['steps']) for r in rows))
            for channel in ('H','E','CP','IH'):
                self.assertAlmostEqual(closure['channel_masks'][channel]['common_kWh'],math.fsum(float(r[f'{channel}_kWh']) for r in rows),places=7)
            parents={}
            for r in rows:
                p=parents.setdefault(r['block_id'],dict(steps=0,start=r['parent_start'],end=r['parent_end']))
                p['steps']+=int(r['steps'])
            for p in parents.values():self.assertAlmostEqual(p['steps']*120,(datetime.fromisoformat(p['end'])-datetime.fromisoformat(p['start'])).total_seconds())
        ledgers=closure['lag_ledgers']
        for channel in ('H','E','IH'):
            self.assertAlmostEqual(0.,max(p[f'{channel}_kWh'] for p in ledgers.values())-min(p[f'{channel}_kWh'] for p in ledgers.values()))

    def test_blocked_error_same_support_and_signed_auxiliary_residual_identity(self):
        rows=list(a.csv_rows(self.output/'CP_blocked_prediction_summary.csv'))
        rows=[r for r in rows if r['aggregation']=='common_blocks_180min_offset0' and r['cohort']=='REFERENCE_MATCHED_STATES'
              and r['minimum_component_hours']=='0.5' and r['fold_type']=='LEAVE_YEAR_OUT'
              and r['service']=='SH_MODE_ENDPOINTS' and r['heat_state']=='POSITIVE']
        time=next(r for r in rows if r['model']=='ELAPSED_STATE_TIME');ref=next(r for r in rows if r['model']=='PROPORTIONAL_REFERENCE')
        self.assertEqual(time['predicted_blocks'],ref['predicted_blocks']);self.assertEqual(time['observed_CP_kWh'],ref['observed_CP_kWh'])
        self.assertLess(float(time['WAPE_percent']),float(ref['WAPE_percent'])/10)
        residual=list(a.csv_rows(self.output/'CP_removed_same_mask_reference_residuals.csv'))
        self.assertTrue(any(float(r['E_minus_CP_IH_kWh'])<0 for r in residual))
        for r in residual:
            self.assertAlmostEqual(float(r['E_kWh']),float(r['E_minus_CP_kWh'])+float(r['CP_kWh']))
            self.assertAlmostEqual(float(r['E_minus_CP_minus_reference_kWh']),float(r['E_minus_CP_kWh'])-float(r['reference_kWh']))
            self.assertEqual('False',r['residual_is_compressor_energy'])


@unittest.skipUnless(os.environ.get('B05_E2_ASSESSMENT_OUTPUT'), 'optional aggregate assessment outputs')
class AggregateAssessmentIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output=Path(os.environ['B05_E2_ASSESSMENT_OUTPUT'])

    def test_assessment_hash_chain_and_exact_qualification(self):
        manifest=json.loads((self.output/'INPUT_CODE_OUTPUT_MANIFEST.json').read_text())
        if os.environ.get('B05_TARGET_WEIGHTED_OUTPUT'):
            spec=json.loads(a.MANIFEST.read_text(encoding='utf-8'))
            self.assertEqual(spec['target_weighted_assessment']['prior_R2_manifest_sha256'],a.digest(self.output/'INPUT_CODE_OUTPUT_MANIFEST.json'))
        else:
            self.assertEqual(a.digest(Path(a.__file__)),manifest['source_code_sha256'])
            self.assertEqual(a.digest(a.MANIFEST),manifest['source_manifest_sha256'])
        for entry in manifest['outputs']:
            self.assertEqual(entry['sha256'],a.digest(self.output/entry['path']))
        record=json.loads((self.output/'EXACT_ROUTE_QUALIFICATION_RECORD.json').read_text())
        self.assertEqual('SCN_COMPLETE_CONDITIONAL',a.route_qualification(complete=True,physical=True,
            route_context=record['binding'],documented_assumptions={'qualification_records':[record]})[0])
        claims=list(a.csv_rows(self.output/'claim_specific_eight_point_E2_evidence.csv'))
        self.assertEqual(40,len(claims))
        for claim in {r['claim_id'] for r in claims}:
            self.assertEqual(set(range(1,9)),{int(r['criterion']) for r in claims if r['claim_id']==claim})
        summary=json.loads((self.output/'AGGREGATE_E2_ASSESSMENT.json').read_text())
        self.assertTrue(summary['complete'])
        self.assertTrue(summary['physical'])

    def test_complete_target_replay_and_cohort_conservation(self):
        weights=list(a.csv_rows(self.output/'designated_route_target_weights.csv'))
        self.assertEqual(8760,len(weights))
        self.assertTrue(all(r['supported']=='True' for r in weights))
        self.assertAlmostEqual(4003.3949236948883,math.fsum(float(r['conditional_E_kWh']) for r in weights),places=7)
        closure=json.loads((self.output/'IH_timing_cohort_closure.json').read_text())
        for c in ('H','E','IH'):
            self.assertAlmostEqual(closure[f'HEI_{c}_kWh'],closure[f'complete_hour_{c}_kWh']+closure[f'complement_{c}_kWh'])
        ledger=[r for r in a.csv_rows(self.output/'same_mask_service_month_ledgers.csv') if r['mask']=='HP_E_IH']
        self.assertEqual(closure['HEI_steps'],sum(int(r['steps']) for r in ledger))
        for c in ('H','E','IH'):
            self.assertAlmostEqual(closure[f'HEI_{c}_kWh'],math.fsum(float(r[f'{c}_kWh']) for r in ledger),places=7)
        lag=list(a.csv_rows(self.output/'IH_E_same_mask_lag_diagnostics.csv'))
        for key in {(r['year'],r['temperature_proxy']) for r in lag}:
            self.assertEqual(1,len({r['n'] for r in lag if (r['year'],r['temperature_proxy'])==key}))
        aggregate=list(a.csv_rows(self.output/'IH_E_common_hour_aggregation_diagnostics.csv'))
        for minutes in ('2','10','30','60'):
            chosen=[r for r in aggregate if r['aggregation_minutes']==minutes]
            self.assertAlmostEqual(closure['complete_hour_steps'],sum(int(r['n'])*int(minutes)/2 for r in chosen))
            for c in ('H','E','IH'):
                self.assertAlmostEqual(closure[f'complete_hour_{c}_kWh'],math.fsum(float(r[f'{c}_kWh']) for r in chosen),places=7)
        joint=list(a.csv_rows(self.output/'normalized_joint_year_flow_same_target_cells.csv'))
        self.assertTrue(any(r['dimension']=='YEAR_WITHIN_FLOW' and int(r['common_target_hours'])>3000
                            and abs(float(r['right_minus_left_kWh']))>300 for r in joint))

    def test_season_state_matching_has_no_annualization_and_decomposition_closes(self):
        rows=list(a.csv_rows(self.output/'matched_month_duration_return_duty_target_exposure.csv'))
        self.assertTrue(rows)
        for r in rows:
            original=float(r['original_year_mix_difference_same_target_kWh'])
            remaining=float(r['remaining_standardized_difference_kWh'])
            self.assertAlmostEqual(original,remaining+float(r['total_composition_change_kWh']),places=7)
            self.assertAlmostEqual(float(r['total_composition_change_kWh']),float(r['month_selection_change_kWh'])
                                   +float(r['within_month_composition_change_kWh']),places=7)
            self.assertEqual('False',r['annual_extrapolated'])
            self.assertEqual('False',r['causal_year_or_controller_effect'])
            if r['exposure']=='TARGET_SAME_MONTH':self.assertLessEqual(int(r['common_target_hours']),31*24)
        example=next(r for r in rows if r['level']=='MONTH_FLOW_GE45MIN' and r['month']=='02'
                     and r['flow_bin_C']=='[25,30)' and (r['left_year'],r['right_year'])==('2022','2023')
                     and r['exposure']=='ALL_TARGET_CELL_EXPOSURE_DIAGNOSTIC')
        self.assertEqual(2962,int(example['common_target_hours']))
        self.assertAlmostEqual(-415.6655011716441,float(example['remaining_standardized_difference_kWh']),places=7)


if __name__ == '__main__':
    unittest.main()
