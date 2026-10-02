"""Analytic/independent-quadrature checks and pinned-source adverse cases."""
import copy
import inspect
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules.B06 import common_service_envelope_reference as model
from modules.B05 import hourly_power_component_reference as electricity


def simpson(function, n=4096):
    return (function(0)+function(1)+4*sum(function(i/n) for i in range(1,n,2))
            +2*sum(function(i/n) for i in range(2,n,2)))/(3*n)


class CurveTests(unittest.TestCase):
    def test_constant_demands_have_correct_energy_and_strict_excess_duration(self):
        for demand in (0.,1000.,2000.,3000.):
            result=model._curve(demand,0.,.5,capacity_kw=2.)
            self.assertEqual(result['required_heat_kwh'],demand/1000)
            self.assertEqual(result['additional_thermal_kwh'],max(0.,demand/1000-2))
            self.assertEqual(result['over_capacity_duration_h'],float(demand>2000))
            self.assertIsNone(result['capacity_crossing_hour_fraction'])

    def test_exact_and_near_capacity_do_not_invent_equal_demand_excess(self):
        for delta in (-1e-5,0.,1e-5):
            result=model._curve(2000+delta,0.,.5,capacity_kw=2.)
            self.assertEqual(result['over_capacity_duration_h'],float(delta>0))
            self.assertAlmostEqual(result['additional_thermal_kwh'],max(0.,delta)/1000)

    def test_decreasing_crossing_has_exact_half_interval_root(self):
        k=math.log(4)
        result=model._curve(1000.,2000.,k,capacity_kw=2.)
        self.assertAlmostEqual(result['capacity_crossing_hour_fraction'],.5)
        self.assertAlmostEqual(result['over_capacity_duration_h'],.5)
        self.assertAlmostEqual(result['additional_thermal_kwh'],-.5+1/k)
        self.assertEqual(result['peak_required_kw'],3.)

    def test_increasing_crossing_has_exact_half_interval_root(self):
        k=math.log(4)
        result=model._curve(3000.,-2000.,k,capacity_kw=2.)
        self.assertAlmostEqual(result['capacity_crossing_hour_fraction'],.5)
        self.assertAlmostEqual(result['over_capacity_duration_h'],.5)
        self.assertAlmostEqual(result['additional_thermal_kwh'],.5-.5/k)
        self.assertEqual(result['peak_required_kw'],2.5)

    def test_hourly_mean_can_hide_a_real_short_capacity_excess(self):
        result=model._curve(1000.,1100.,math.log(2),capacity_kw=2.)
        self.assertLess(result['required_heat_kwh'],2.)
        self.assertGreater(result['additional_thermal_kwh'],0.)
        self.assertGreater(result['over_capacity_duration_h'],0.)
        self.assertLess(result['over_capacity_duration_h'],1.)

    def test_endpoint_equality_is_not_an_interior_crossing(self):
        k=math.log(2)
        for a,b,duration in ((1000.,1000.,0.),(3000.,-1000.,1.),(1000.,2000.,1.),(3000.,-2000.,0.)):
            result=model._curve(a,b,k,capacity_kw=2.)
            self.assertEqual(result['over_capacity_duration_h'],duration)
            self.assertIsNone(result['capacity_crossing_hour_fraction'])

    def test_analytic_integrals_match_separate_composite_simpson_calculation(self):
        for a,b,k,cap in ((1000.,2000.,.7,1.8),(3000.,-1800.,.3,2.),
                          (2200.,0.,.2,2.),(0.,0.,.2,4.),(2000.,500.,1.2,2.2)):
            result=model._curve(a,b,k,capacity_kw=cap)
            f=lambda t:(a+b*math.exp(-k*t))/1000
            with self.subTest(a=a,b=b,k=k,cap=cap):
                self.assertAlmostEqual(result['required_heat_kwh'],simpson(f),places=10)
                self.assertAlmostEqual(result['additional_thermal_kwh'],simpson(lambda t:max(0.,f(t)-cap)),delta=5e-7)

    def test_partitioning_interval_preserves_heat_and_excess(self):
        a,b,k,split=1000.,2000.,.7,.25
        full=model._curve(a,b,k,capacity_kw=2.)
        left=model._curve(a,b,k,split,2.)
        right=model._curve(a,b*math.exp(-k*split),k,1-split,2.)
        for key in ('required_heat_kwh','additional_thermal_kwh','over_capacity_duration_h'):
            self.assertAlmostEqual(full[key],left[key]+right[key],places=12)

    def test_unknown_capacity_does_not_erase_supported_thermal_demand(self):
        result=model._curve(1000.,2000.,.7)
        self.assertIsNotNone(result['required_heat_kwh'])
        self.assertIsNone(result['additional_thermal_kwh'])
        self.assertIsNone(result['over_capacity_duration_h'])
        self.assertEqual(result['capacity_comparison_status'],'Q')

    def test_required_cooling_cannot_be_clipped_to_a_heating_saving(self):
        for a,b in ((-1.,0.),(1000.,-2000.),(-1000.,1500.)):
            with self.subTest(a=a,b=b),self.assertRaisesRegex(ValueError,'cooling'):
                model._curve(a,b,1.,capacity_kw=2.)

    def test_invalid_dimensions_types_and_derived_overflow_reject(self):
        for name,value in (('a',None),('a',True),('a',float('inf')),('b',float('nan')),
                           ('k',0.),('k',-1.),('hours',0.),('hours',-1.),
                           ('capacity_kw',0.),('capacity_kw',-1.),('capacity_kw','2')):
            args=dict(a=2000.,b=500.,k=.5,hours=1.,capacity_kw=2.)
            args[name]=value
            with self.subTest(name=name,value=value),self.assertRaises(ValueError):model._curve(**args)
        with self.assertRaises(ValueError):model._curve(1e308,1e308,.5)
        with self.assertRaises(ValueError):model._curve(1e308,0.,.5,1e308)
        with self.assertRaises(ValueError):model._curve(1000.,0.,.5,capacity_kw=1e308)


class SourceAndPropagationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=model.hourly.calculate_reference()
        cls.manifest=model.hourly._load_manifest(model.hourly.MANIFEST_PATH)
        cls.items,cls.package=model._source_items(cls.base,cls.manifest)

    def test_source_states_have_substantive_baseline_and_common_controls(self):
        self.assertEqual([x['source_row'] for x in self.items],[1239,1240,1241])
        for c in model.COMMON:self.assertEqual(len({x['values'][c] for x in self.items}),1)
        for c in model.hourly.PARTS:
            self.assertEqual(self.items[0]['values']['f_Measure_'+c],0)
            self.assertEqual(self.items[0]['values']['R_Measure_'+c],0)
        self.assertEqual([x['values']['R_Add_UnheatedSpace_Roof_1'] for x in self.items],[.3,.3,.3])

    def test_baseline_original_glazing_and_existing_attic_resistance_are_retained(self):
        p=[model._parameters(x,self.manifest) for x in self.items]
        self.assertEqual([x['glazing_transmittance'] for x in p],[.75,.6,.6])
        self.assertAlmostEqual(p[0]['effective_u_w_m2k']['Roof_1'],1/(1/2.01+.3))
        self.assertAlmostEqual(p[0]['ventilation_h_w_k'],.34*(.4+.4)*2.5*56)
        for q in p[1:]:self.assertAlmostEqual(q['ventilation_h_w_k'],.34*(.4+.1)*2.5*56)

    def test_source_byte_change_rejects_before_state_selection(self):
        real_read=Path.read_bytes
        target=model.hourly.ROOT/self.manifest['repository_pins']['building']['path']
        def changed(path):
            data=real_read(path)
            return data+b'\n' if path==target else data
        with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'extract hash'):
            model._source_items(self.base,self.manifest)

    def test_common_geometry_and_zero_retrofit_guards_are_not_label_based(self):
        # Test semantic guards after the independent byte guard; no public override.
        mutations=(lambda v:v.update(A_C_Ref=99),
                   lambda v:v.update(R_Measure_Roof_1=1),
                   lambda v:v.update(f_Measure_Window_1=.5))
        for mutate in mutations:
            package=copy.deepcopy(self.package)
            target=next(r for r in package['rows'] if r['values']['Code_BuildingVariant']==model.VARIANTS[0])
            mutate(target['values'])
            with self.subTest(mutation=mutate),patch.object(model.json,'loads',return_value=package):
                with self.assertRaises(ValueError):model._source_items(self.base,self.manifest)

    def test_duplicate_and_wrong_source_row_reject(self):
        for duplicate in (False,True):
            package=copy.deepcopy(self.package)
            target=next(r for r in package['rows'] if r['values']['Code_BuildingVariant']==model.VARIANTS[0])
            if duplicate:package['rows'].append(copy.deepcopy(target))
            else:target['source_row']=999
            with self.subTest(duplicate=duplicate),patch.object(model.json,'loads',return_value=package):
                with self.assertRaisesRegex(ValueError,'unique source'):model._source_items(self.base,self.manifest)

    def test_no_radiation_keeps_all_state_totals_and_reductions_unknown(self):
        result=model.calculate_reference()
        self.assertEqual(len(result['states']),3)
        for state in result['states']:
            self.assertEqual(state['unknown_thermal_hours'],72)
            for field in ('required_thermal_kwh','additional_thermal_kwh','conditional_heat_reduction_from_existing_kwh',
                          'actual_electricity_kwh','actual_spf','payback'):
                self.assertIsNone(state[field])
            self.assertTrue(all(r['evidence_status']=='Q' for r in state['rows']))
            self.assertTrue(all(r['source_capacity_kw'] is not None for r in state['rows']))
        self.assertFalse(result['empirical_validation'])
        self.assertFalse(result['national_adoption'])
        self.assertFalse(result['whole_slice_complete'])
        self.assertFalse(result['annual_output_used'])
        self.assertFalse(result['source_seasonal_service_factors_used'])
        self.assertIn('UNAVAILABLE',result['electrical_consumer_handoff'])

    def test_partial_aggregates_do_not_masquerade_as_complete(self):
        known=dict(model._curve(2000.,0.,.5,capacity_kw=1.5),duration_h=1.)
        unknown=dict(required_heat_kwh=None,peak_required_kw=None,additional_thermal_kwh=None,
                     peak_additional_kw=None,over_capacity_duration_h=None,capacity_crossing_hour_fraction=None)
        result=model._aggregate([known,unknown])
        self.assertIsNone(result['required_thermal_kwh'])
        self.assertIsNone(result['additional_thermal_kwh'])
        self.assertEqual(result['supported_only_heat_kwh'],2.)
        self.assertEqual(result['supported_only_additional_thermal_kwh'],.5)
        self.assertIsNone(result['actual_electricity_kwh'])
        without_cap=dict(known,additional_thermal_kwh=None,peak_additional_kw=None,over_capacity_duration_h=None)
        result=model._aggregate([known,without_cap])
        self.assertEqual(result['required_thermal_kwh'],4.)
        self.assertIsNone(result['additional_thermal_kwh'])

    def test_interval_or_reference_path_substitution_rejects(self):
        row=copy.deepcopy(self.base['rows'][0]);fixed=copy.deepcopy(self.base['fixed_path']['rows'][0])
        p=model._parameters(self.items[0],self.manifest)
        fixed['interval_end_utc']='2025-02-18T10:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'interval mismatch'):
            model._record(row,fixed,self.base['parameters'],p,.6)
        changed=copy.deepcopy(self.base);changed['parameters']['source_variant']=model.VARIANTS[0]
        with self.assertRaisesRegex(ValueError,'ambitious reference'):
            model._source_items(changed,self.manifest)

    def test_public_entry_point_has_no_scenario_override_or_electrical_handoff(self):
        self.assertEqual(set(inspect.signature(model.calculate_reference).parameters),{'radiation_path'})
        for field in ('states','trajectory','initial_temperature_c','weather','source_parameters'):
            with self.subTest(field=field),self.assertRaises(TypeError):model.calculate_reference(**{field:{}})
        with self.assertRaises(TypeError):electricity.calculate_reference(thermal_result={'states':[]})

    def test_fake_external_input_and_changed_thermal_code_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fake.csv';path.write_text('invented,0\n')
            with self.assertRaisesRegex(ValueError,'bytes/hash mismatch'):model.calculate_reference(radiation_path=path)
        actual=Path.read_bytes;target=Path(model.hourly.__file__)
        def changed(path):return actual(path)+b'\n' if path==target else actual(path)
        with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'thermal API changed'):
            model.calculate_reference()


if __name__=='__main__':
    unittest.main()
