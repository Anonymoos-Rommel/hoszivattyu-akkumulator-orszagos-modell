import copy
from dataclasses import replace
import hashlib
import math
import csv
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from modules.B07 import discharge_equivalent_reference as m


def toy(*,capacity=9.,eta=.9,reserve=0.,variable=False):
    c=((.01,1.),(20.,1.)) if not variable else ((.1,.8),(4.,.96))
    d=((.01,1.),(20.,1.)) if not variable else ((.1,.7),(4.,.97))
    return m.Reference(capacity,eta,reserve,m.Curve('SYNTHETIC_CHARGE',c,'AC_TO_DC'),
                       m.Curve('SYNTHETIC_DISCHARGE',d,'DC_TO_AC'),20.,None,
                       'SYNTHETIC_COORDINATE_TEST')


def command(charge=0.,discharge=0.,hours=1.):
    return dict(charge_ac_kw=charge,discharge_ac_kw=discharge,hours=hours)


class CurveTests(unittest.TestCase):
    def test_source_vertices_and_midpoints_preserve_output_axis_and_inverse(self):
        for ident in m.source.CURVES:
            direction='AC_TO_DC' if ident=='AC2BAT_STANDARD' else 'DC_TO_AC'
            curve=m.Curve(ident,m.source.curve_points(ident),direction)
            for i,(q,eta) in enumerate(curve.points):
                with self.subTest(curve=ident,index=i):
                    self.assertEqual(curve.point(q),(q/eta,eta))
                    inverse=curve.largest_output(q/eta,curve.upper)
                    self.assertAlmostEqual(inverse,q,places=11)
                    self.assertLessEqual(curve.point(inverse)[0],q/eta)
            for (a,ea),(b,eb) in zip(curve.points[::37],curve.points[1::37]):
                if a>=b:continue
                q=(a+b)/2;inp,eta=curve.point(q)
                native=m.source.converter_point(ident,q)
                self.assertAlmostEqual(inp,native['path_input_kw'],places=12)
                self.assertAlmostEqual(eta,native['efficiency_ratio'],places=12)

    def test_unsupported_inputs_are_declined_not_extrapolated(self):
        curve=toy(variable=True).charge
        self.assertIsNone(curve.largest_output(curve.point(curve.lower)[0]/2,curve.upper))
        self.assertIsNone(curve.largest_output(20.,curve.lower/2))
        self.assertEqual(curve.largest_output(20.,20.),curve.upper)
        for q in (0.,curve.lower/2,curve.upper+1,float('nan'),True):
            with self.subTest(q=q),self.assertRaises(ValueError):curve.point(q)

    def test_input_mapping_must_be_monotone_inside_every_segment(self):
        for points in (((1.,.1),(2.,.9)),((1.,.8),(1.,.9)),((1.,1.1),(2.,.9)),((0.,.8),(2.,.9))):
            with self.subTest(points=points),self.assertRaises(ValueError):m.Curve('bad',points,'AC_TO_DC')

    def test_curve_pairs_are_immutable_and_path_boundaries_are_explicit(self):
        with self.assertRaises(ValueError):m.Curve('bad',[(1.,.9),(2.,.9)],'AC_TO_DC')
        with self.assertRaises(ValueError):m.Curve('bad',((1.,.9),(2.,.9)),'UNSPECIFIED')
        ref=toy()
        with self.assertRaises(ValueError):replace(ref,charge=ref.discharge,discharge=ref.charge)


class ConditionalFlowTests(unittest.TestCase):
    def test_full_synthetic_cycle_requires_ten_input_for_nine_output(self):
        r=m.run(toy(),initial_dc_output_equiv_kwh=0.,commands=[command(charge=2.,hours=5.),command(discharge=3.,hours=3.)])
        self.assertEqual(r['active_reference_totals']['admitted_charge_dc_kwh'],10.)
        self.assertEqual(r['active_reference_totals']['admitted_discharge_dc_kwh'],9.)
        self.assertEqual(r['terminal_dc_output_equiv_kwh'],0.)
        self.assertAlmostEqual(r['conditional_active_roundtrip_ratio'],.9)
        self.assertAlmostEqual(r['finite_horizon_residual_kwh'],0.)

    def test_finite_initial_and_terminal_inventory_are_not_free_cycle_benefits(self):
        r=m.run(toy(),initial_dc_output_equiv_kwh=4.,commands=[command(discharge=1.,hours=2.)])
        self.assertEqual(r['terminal_dc_output_equiv_kwh'],2.)
        self.assertIsNone(r['conditional_active_roundtrip_ratio'])
        self.assertFalse(r['cyclic_inventory_within_numerical_tolerance'])
        self.assertEqual(r['conditional_accounting_components']['terminal_minus_initial_inventory_kwh'],-2.)
        self.assertAlmostEqual(r['finite_horizon_residual_kwh'],0.)

    def test_partial_cycle_retains_terminal_stock(self):
        r=m.run(toy(),initial_dc_output_equiv_kwh=0.,commands=[command(charge=2.,hours=2.),command(discharge=1.,hours=2.)])
        self.assertAlmostEqual(r['terminal_dc_output_equiv_kwh'],1.6)
        self.assertIsNone(r['conditional_active_roundtrip_ratio'])
        self.assertAlmostEqual(r['finite_horizon_residual_kwh'],0.)

    def test_charge_clips_before_admission_and_recomputes_efficiency(self):
        ref=toy(variable=True)
        r=m.step(ref,m.Inventory(8.),**command(charge=4.))
        self.assertEqual(r['status'],'SCN_ACTIVE_REFERENCE_ONLY')
        self.assertLessEqual(r['x_end_kwh'],9.)
        self.assertAlmostEqual(r['x_end_kwh'],9.)
        self.assertAlmostEqual(r['admitted_charge_dc_kwh'],1/.9)
        p,eta=ref.charge.point(r['actual_curve_output_kw'])
        self.assertEqual(r['post_clipping_conversion_efficiency'],eta)
        self.assertAlmostEqual(r['admitted_charge_ac_kwh'],p)
        self.assertNotAlmostEqual(eta,ref.charge.point(ref.charge.upper)[1])
        self.assertAlmostEqual(r['unused_active_charge_request_kwh'],4.-p)

    def test_discharge_clips_at_explicit_reserve_before_admission(self):
        ref=toy(variable=True,reserve=1.)
        r=m.step(ref,m.Inventory(1.5),**command(discharge=3.))
        self.assertGreaterEqual(r['x_end_kwh'],1.)
        self.assertAlmostEqual(r['x_end_kwh'],1.)
        self.assertLessEqual(r['admitted_discharge_dc_kwh'],.5)
        p,eta=ref.discharge.point(r['actual_curve_output_kw'])
        self.assertEqual(r['post_clipping_conversion_efficiency'],eta)
        self.assertAlmostEqual(r['admitted_discharge_dc_kwh'],p)
        self.assertGreater(r['unserved_battery_ac_request_kwh'],0.)

    def test_reserve_limits_discharge_but_does_not_forbid_recharging_below_it(self):
        ref=toy(reserve=1.)
        charge=m.step(ref,m.Inventory(0.),**command(charge=1.,hours=.5))
        self.assertEqual(charge['status'],'SCN_ACTIVE_REFERENCE_ONLY')
        self.assertAlmostEqual(charge['x_end_kwh'],.45)
        decline=m.step(ref,m.Inventory(.45),**command(discharge=1.))
        self.assertIsNone(decline['x_end_kwh'])
        self.assertEqual(decline['delivered_discharge_ac_kwh'],0.)

    def test_tiny_capacity_or_inventory_does_not_invent_a_duty_cycle(self):
        ref=toy(variable=True)
        for state,cmd in ((m.Inventory(8.999),command(charge=2.)),(m.Inventory(.001),command(discharge=2.))):
            r=m.step(ref,state,**cmd)
            self.assertEqual(r['status'],'Q_IDLE_INVENTORY')
            self.assertIsNone(r['x_end_kwh'])
            self.assertEqual(r['admitted_charge_dc_kwh'],0.)
            self.assertEqual(r['admitted_discharge_dc_kwh'],0.)
            self.assertIsNone(r['idle_dc_drain_kwh'])

    def test_full_and_empty_declines_are_not_unchanged_known_future_states(self):
        ref=toy()
        for state,cmd in ((m.Inventory(9.),command(charge=2.)),(m.Inventory(0.),command(discharge=2.))):
            r=m.step(ref,state,**cmd)
            self.assertIsNone(r['x_end_kwh'])
            self.assertEqual(r['admitted_charge_ac_kwh'],0.)
            self.assertEqual(r['delivered_discharge_ac_kwh'],0.)

    def test_nonempty_idle_invalidates_following_inventory_without_restart(self):
        r=m.run(toy(),initial_dc_output_equiv_kwh=3.,commands=[command(),command(charge=1.),command(discharge=1.)])
        self.assertEqual(r['records'][0]['result']['status'],'Q_IDLE_INVENTORY')
        self.assertTrue(all(x['result']['x_end_kwh'] is None for x in r['records']))
        self.assertTrue(all(v is None for v in r['active_reference_totals'].values()))
        self.assertIsNone(r['finite_horizon_residual_kwh'])
        self.assertIsNone(r['conditional_active_roundtrip_ratio'])

    def test_empty_ac_component_is_separate_from_unmeasured_standby_dc_drain(self):
        ref=m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)
        r=m.step(ref,m.Inventory(0.),**command(hours=2.))
        self.assertAlmostEqual(r['conditional_empty_ac_component_kwh'],.00814)
        self.assertIsNone(r['idle_dc_drain_kwh'])
        self.assertIsNone(r['x_end_kwh'])
        self.assertIsNone(r['actual_system_electricity_kwh'])
        nonempty=m.step(ref,m.Inventory(1.),**command(hours=2.))
        self.assertIsNone(nonempty['conditional_empty_ac_component_kwh'])

    def test_interior_constant_power_is_timestep_consistent(self):
        ref=toy(variable=True)
        for initial,cmd in ((0.,command(charge=1.)),(5.,command(discharge=1.))):
            full=m.run(ref,initial_dc_output_equiv_kwh=initial,commands=[cmd])
            split=m.run(ref,initial_dc_output_equiv_kwh=initial,commands=[dict(cmd,hours=.25),dict(cmd,hours=.75)])
            self.assertAlmostEqual(full['terminal_dc_output_equiv_kwh'],split['terminal_dc_output_equiv_kwh'],places=12)
            for k,v in full['active_reference_totals'].items():self.assertAlmostEqual(v,split['active_reference_totals'][k],places=12)

    def test_latent_one_way_splits_are_coordinate_equivalent(self):
        eta=.9;c=1.4;d=.6;x=3.;capacity=9.;reserve=.5
        for i in range(21):
            a=eta+(1-eta)*i/20;b=eta/a
            z=x/b;cz=capacity/b;rz=reserve/b
            next_z=z+a*c-d/b
            self.assertAlmostEqual(b*next_z,x+eta*c-d,places=12)
            self.assertAlmostEqual((cz-z)/a,(capacity-x)/eta,places=12)
            self.assertAlmostEqual(b*(z-rz),x-reserve,places=12)

    def test_commands_and_initial_inventory_fail_closed_on_invalid_values(self):
        ref=toy()
        with self.assertRaises(ValueError):m.step(ref,m.Inventory(1.),**command(charge=1.,discharge=1.))
        for field,value in (('charge_ac_kw',None),('charge_ac_kw',True),('discharge_ac_kw',-1.),
                            ('hours',0.),('hours',float('inf')),('charge_ac_kw',float('nan'))):
            cmd=command();cmd[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):m.step(ref,m.Inventory(1.),**cmd)
        for x in (-1.,10.,float('nan'),True):
            with self.subTest(x=x),self.assertRaises(ValueError):m.run(ref,initial_dc_output_equiv_kwh=x,commands=[command()])
        with self.assertRaises(ValueError):m.step(ref,m.Inventory(1.),**command(charge=1e308,hours=1e308))
        for commands in ([],[{}],[dict(command(),override=True)]):
            with self.subTest(commands=commands),self.assertRaises(ValueError):m.run(ref,initial_dc_output_equiv_kwh=1.,commands=commands)

    def test_declared_commands_are_copied_into_the_ledger(self):
        cmd=command(charge=1.);r=m.run(toy(),initial_dc_output_equiv_kwh=0.,commands=[cmd]);cmd['hours']=99.
        self.assertEqual(r['records'][0]['command']['hours'],1.)

    def test_unknown_state_cannot_be_smuggled_back_as_a_numeric_inventory(self):
        with self.assertRaises(ValueError):m.Inventory(1.,'Q_IDLE_DRAIN')
        for ref,state in ((None,m.Inventory(1.)),(toy(),None)):
            with self.assertRaises(ValueError):m.step(ref,state,**command(charge=1.))
        with self.assertRaises(ValueError):m.run(toy(),initial_dc_output_equiv_kwh=0.,commands=None)
        result=m.step(toy(),m.Inventory(None,'UNKNOWN_INITIAL'),**command(charge=1.))
        self.assertIsNone(result['x_end_kwh'])
        self.assertIsNone(result['admitted_charge_ac_kwh'])


class SourceBoundaryTests(unittest.TestCase):
    def test_source_control_units_and_explicit_selection_preserve_identity(self):
        ref=m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)
        self.assertEqual(ref.capacity_dc_output_equiv_kwh,7.572)
        self.assertAlmostEqual(ref.battery_dc_cycle_efficiency,.958183)
        self.assertEqual(ref.discharge_ac_source_limit_kw,4.5459)
        self.assertGreater(ref.discharge_ac_source_limit_kw,ref.discharge.upper)
        with self.assertRaises(TypeError):m.source_reference(discharge_curve_id='BAT2AC_STANDARD')
        with self.assertRaises(ValueError):m.source_reference(discharge_curve_id='AUTO',reserve_dc_output_equiv_kwh=0.)

    def test_fits_are_not_averaged_or_silently_switched_at_low_load(self):
        standard=m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)
        low=m.source_reference(discharge_curve_id='BAT2AC_LOW_LOAD',reserve_dc_output_equiv_kwh=0.)
        s=m.step(standard,m.Inventory(1.),**command(discharge=.1))
        l=m.step(low,m.Inventory(1.),**command(discharge=.1))
        self.assertEqual(s['status'],'Q_IDLE_INVENTORY')
        self.assertEqual(l['status'],'SCN_ACTIVE_REFERENCE_ONLY')
        self.assertAlmostEqual(l['delivered_discharge_ac_kwh'],.1)
        self.assertNotEqual(standard.discharge.point(.2)[1],low.discharge.point(.2)[1])

    def test_genuine_closed_active_cycle_has_full_ac_dc_accounting_but_no_actual_claim(self):
        ref=m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)
        q=2.;charge=ref.charge.point(q)[0];hours=ref.capacity_dc_output_equiv_kwh/(ref.battery_dc_cycle_efficiency*q)
        first=m.step(ref,m.Inventory(0.),**command(charge=charge,hours=hours))
        discharge=2.;duration=first['x_end_kwh']/ref.discharge.point(discharge)[0]
        result=m.run(ref,initial_dc_output_equiv_kwh=0.,commands=[command(charge=charge,hours=hours),command(discharge=discharge,hours=duration)])
        self.assertTrue(result['active_reference_ledger_complete'])
        self.assertTrue(result['cyclic_inventory_within_numerical_tolerance'])
        total=result['active_reference_totals'];components=result['conditional_accounting_components']
        self.assertAlmostEqual(total['admitted_charge_ac_kwh']-total['delivered_discharge_ac_kwh'],sum(components.values()),places=12)
        self.assertAlmostEqual(total['admitted_discharge_dc_kwh'],7.572,places=12)
        self.assertIsNone(result['actual_total_system_energy_kwh'])
        self.assertIsNone(result['actual_roundtrip_efficiency'])
        self.assertIsNone(result['actual_bms_soc'])
        self.assertIsNone(result['annual_result'])
        self.assertTrue(result['conditional_method_adopted'])
        self.assertFalse(result['legacy_contract_replaced'])
        self.assertFalse(result['national_admission'])
        self.assertFalse(result['complete_hardware_admission'])

    def test_every_pinned_source_file_is_checked(self):
        actual=Path.read_bytes
        for name in m.PINS:
            target=m.ROOT/name
            def changed(path):return actual(path)+b'\n' if path==target else actual(path)
            with self.subTest(name=name),patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'pinned source'):
                m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)

    def test_reference_rejects_invalid_efficiency_reserve_and_swapped_paths(self):
        ref=toy()
        for values in (dict(capacity_dc_output_equiv_kwh=0),dict(battery_dc_cycle_efficiency=1.1),
                       dict(battery_dc_cycle_efficiency=0),dict(reserve_dc_output_equiv_kwh=10.),
                       dict(reserve_dc_output_equiv_kwh=-1.),dict(empty_ac_test_kw=-1.)):
            with self.subTest(values=values),self.assertRaises(ValueError):replace(ref,**values)


class CycleClosureRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref=m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)

    def test_review_tiny_initial_stock_witness_and_ordinary_neighbor_have_no_ratio(self):
        for hours in (1e-10,.1):
            with self.subTest(hours=hours):
                r=m.run(self.ref,initial_dc_output_equiv_kwh=1.,commands=[
                    command(charge=1.,hours=hours),command(discharge=2.,hours=hours)])
                self.assertFalse(r['cyclic_inventory_within_numerical_tolerance'])
                self.assertIsNone(r['conditional_active_roundtrip_ratio'])
                self.assertLess(r['terminal_dc_output_equiv_kwh'],1.)
                self.assertAlmostEqual(r['active_reference_totals']['delivered_discharge_ac_kwh'] /
                                       r['active_reference_totals']['admitted_charge_ac_kwh'],2.)
                closure=r['cycle_closure']
                self.assertGreater(abs(closure['net_dc_flow_kwh']),closure['arithmetic_allowance_kwh'])

    def test_review_valid_tiny_closed_neighbor_keeps_conditional_ratio(self):
        r=m.run(self.ref,initial_dc_output_equiv_kwh=0.,commands=[
            command(charge=1.,hours=1e-10),command(discharge=2.,hours=4.6199212770167005e-11)])
        self.assertEqual(r['terminal_dc_output_equiv_kwh'],0.)
        self.assertTrue(r['cyclic_inventory_within_numerical_tolerance'])
        self.assertEqual(r['conditional_active_roundtrip_ratio'],.9239842554033401)
        self.assertEqual(r['active_reference_totals']['admitted_charge_dc_kwh'],9.793283989735316e-11)
        self.assertEqual(r['active_reference_totals']['admitted_discharge_dc_kwh'],9.383758233136553e-11)

    def test_closure_scales_with_flow_without_a_physical_minimum_duration(self):
        for duration in (.1,1e-10,1e-20,1e-100,1e-250):
            with self.subTest(duration=duration):
                first=m.step(self.ref,m.Inventory(0.),**command(charge=1.,hours=duration))
                discharge_duration=first['x_end_kwh']/self.ref.discharge.point(2.)[0]
                r=m.run(self.ref,initial_dc_output_equiv_kwh=0.,commands=[
                    command(charge=1.,hours=duration),command(discharge=2.,hours=discharge_duration)])
                self.assertTrue(r['cyclic_inventory_within_numerical_tolerance'])
                self.assertAlmostEqual(r['conditional_active_roundtrip_ratio'],.9239842554033401,places=14)
                self.assertLess(r['cycle_closure']['arithmetic_allowance_kwh'],
                                r['active_reference_totals']['admitted_discharge_dc_kwh']*1e-12)

    def test_rounded_equal_endpoints_do_not_hide_nonclosed_tiny_flow(self):
        for duration in (1e-20,1e-100,1e-250):
            with self.subTest(duration=duration):
                r=m.run(self.ref,initial_dc_output_equiv_kwh=1.,commands=[
                    command(charge=1.,hours=duration),command(discharge=2.,hours=duration)])
                self.assertEqual(r['terminal_dc_output_equiv_kwh'],1.)
                self.assertFalse(r['cyclic_inventory_within_numerical_tolerance'])
                self.assertIsNone(r['conditional_active_roundtrip_ratio'])
                self.assertLess(r['cycle_closure']['net_dc_flow_kwh'],0.)

    def test_subnormal_unresolved_flow_does_not_become_resolved_by_equal_endpoints(self):
        ref=toy(eta=1.);smallest=math.ulp(0.)
        ledger=[{'result':dict(admitted_charge_dc_kwh=smallest,admitted_discharge_dc_kwh=0.)},
                {'result':dict(admitted_charge_dc_kwh=0.,admitted_discharge_dc_kwh=smallest)}]
        closure=m._cycle_closure(ref,0.,0.,ledger)
        self.assertGreaterEqual(closure['arithmetic_allowance_kwh'],smallest)
        self.assertFalse(closure['resolved_closed'])
        # The full command path also rejects an unrepresentable power bound;
        # no source-domain or numerical failure is repaired with a fake ratio.
        with self.assertRaisesRegex(ValueError,'finite nonnegative path output limit'):
            m.run(ref,initial_dc_output_equiv_kwh=0.,commands=[
                command(charge=1.,hours=smallest),command(discharge=1.,hours=smallest)])

    def test_review_subnormal_full_command_witness_and_closed_neighbor_are_unresolved(self):
        ref=toy(capacity=1e-300,eta=1.);u=math.ulp(0.)
        for charge_units,discharge_units in ((5,9),(5,5),(100,150),(100,100)):
            with self.subTest(charge_units=charge_units,discharge_units=discharge_units):
                r=m.run(ref,initial_dc_output_equiv_kwh=5e-301,commands=[
                    command(charge=1.,hours=charge_units*u),
                    command(discharge=1.,hours=discharge_units*u)])
                self.assertTrue(r['active_reference_ledger_complete'])
                self.assertEqual(r['terminal_dc_output_equiv_kwh'],5e-301)
                self.assertFalse(r['cycle_closure']['relative_roundoff_resolved'])
                self.assertFalse(r['cyclic_inventory_within_numerical_tolerance'])
                self.assertIsNone(r['conditional_active_roundtrip_ratio'])
                self.assertEqual(r['active_reference_totals']['admitted_charge_ac_kwh'],charge_units*u)
                self.assertEqual(r['active_reference_totals']['delivered_discharge_ac_kwh'],discharge_units*u)

    def test_normal_scale_closed_neighbor_remains_resolved_near_small_reference_capacity(self):
        ref=toy(capacity=1e-295,eta=1.)
        r=m.run(ref,initial_dc_output_equiv_kwh=0.,commands=[
            command(charge=1.,hours=1e-300),command(discharge=1.,hours=1e-300)])
        self.assertEqual(r['terminal_dc_output_equiv_kwh'],0.)
        self.assertTrue(r['cycle_closure']['relative_roundoff_resolved'])
        self.assertTrue(r['cyclic_inventory_within_numerical_tolerance'])
        self.assertEqual(r['conditional_active_roundtrip_ratio'],1.)

    def test_split_closed_cycle_retains_flows_and_no_unknown_chain_gets_a_ratio(self):
        duration=1e-10
        first=m.step(self.ref,m.Inventory(0.),**command(charge=1.,hours=duration))
        discharge_duration=first['x_end_kwh']/self.ref.discharge.point(2.)[0]
        cycle=[command(charge=1.,hours=duration),command(discharge=2.,hours=discharge_duration)]
        r=m.run(self.ref,initial_dc_output_equiv_kwh=0.,commands=cycle*100)
        self.assertTrue(r['cyclic_inventory_within_numerical_tolerance'])
        self.assertAlmostEqual(r['conditional_active_roundtrip_ratio'],.9239842554033401,places=14)
        q=m.run(self.ref,initial_dc_output_equiv_kwh=0.,commands=[*cycle,command()])
        self.assertEqual(q['cycle_closure']['status'],'Q_INCOMPLETE_INVENTORY')
        self.assertIsNone(q['conditional_active_roundtrip_ratio'])


class ProvisionalIdleAccountingTests(unittest.TestCase):
    def test_debt_record_keeps_e2_continuation_and_exact_upgrade_scope(self):
        debt=json.loads((m.ROOT/'registry/b07_reference_validation_debt.json').read_text())
        self.assertEqual(debt['question_id'],'Q-B07-003')
        self.assertEqual(debt['single_bases']['aggregate_idle_power']['value'],
                         m.provisional_standby_ac_energy(idle_hours=1.)['base_power_w'])
        self.assertFalse(debt['model_blocker'])
        self.assertFalse(debt['e1_component_campaign_required_for_e2'])
        self.assertEqual(len(debt['validation_debt']),3)
        with (m.ROOT/'registry/project_blocker_evidence_audit.csv').open() as f:
            audit=next(r for r in csv.DictReader(f) if r['blocker_id']=='Q-B07-003')
        self.assertEqual((audit['evidence_tier'],audit['blocker_class'],audit['model_blocker'],audit['canonical_use']),
                         ('E2','VALIDATION_BLOCKER','no','MODEL_CONTINUE'))

    def test_synthetic_reference_is_not_promoted_by_method_adoption(self):
        r=m.run(toy(),initial_dc_output_equiv_kwh=1.,commands=[command(discharge=1.,hours=.1)])
        self.assertEqual(r['applicability_evidence_tier'],'E3')
        self.assertEqual(r['evidence_status'],'DER')
        ref=m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)
        source_run=m.run(ref,initial_dc_output_equiv_kwh=1.,commands=[command(discharge=1.,hours=.1)])
        self.assertEqual(source_run['applicability_evidence_tier'],'E2')
        with self.assertRaisesRegex(ValueError,'differs from pinned source'):
            m.run(replace(ref,battery_dc_cycle_efficiency=1.),initial_dc_output_equiv_kwh=1.,
                  commands=[command(discharge=1.,hours=.1)])

    def test_single_source_supported_base_and_explicit_energy_boundary(self):
        r=m.provisional_standby_ac_energy(idle_hours=1250.)
        self.assertEqual(r['base_power_w'],4.07)
        self.assertAlmostEqual(r['ac_energy_debit_kwh'],5.0875)
        self.assertEqual((r['evidence_tier'],r['base_status'],r['validation_debt_id']),
                         ('E2','PROVISIONAL_BASE','Q-B07-003'))
        self.assertIsNone(r['dc_inventory_drain_kwh'])
        for key in ('physical_inventory_path_admitted','cell_bms_inclusion_verified',
                    'all_state_measurement_verified','is_upper_bound',
                    'complete_annual_system_result_admitted','national_admission'):
            self.assertFalse(r[key],key)

    def test_exposure_scaling_does_not_choose_an_annual_profile(self):
        self.assertEqual(m.provisional_standby_ac_energy(idle_hours=0.)['ac_energy_debit_kwh'],0.)
        self.assertAlmostEqual(m.provisional_standby_ac_energy(idle_hours=3500.)['ac_energy_debit_kwh'],14.245)
        self.assertAlmostEqual(m.provisional_standby_ac_energy(idle_hours=8760.)['ac_energy_debit_kwh'],35.6532)
        with self.assertRaises(TypeError):m.provisional_standby_ac_energy()
        for h in (None,True,-1.,float('inf'),float('nan'),'8760'):
            with self.subTest(h=h),self.assertRaises(ValueError):m.provisional_standby_ac_energy(idle_hours=h)

    def test_aggregate_proxy_never_satisfies_missing_physical_inventory(self):
        ref=m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)
        before=m.run(ref,initial_dc_output_equiv_kwh=1.,commands=[command(),command(discharge=1.)])
        debit=m.provisional_standby_ac_energy(idle_hours=1.)
        after=m.run(ref,initial_dc_output_equiv_kwh=1.,commands=[command(),command(discharge=1.)])
        self.assertEqual(before,after)
        self.assertIsNone(after['terminal_dc_output_equiv_kwh'])
        self.assertGreater(debit['ac_energy_debit_kwh'],0.)

    def test_idle_source_identity_and_units_cannot_be_retagged(self):
        original=m.source.source_controls()
        for key,value in (('edition',2023),('firmware','OTHER')):
            changed=copy.deepcopy(original);changed[key]=value
            with patch.object(m.source,'source_controls',return_value=changed),self.assertRaises(ValueError):
                m.provisional_standby_ac_energy(idle_hours=1.)
        changed=copy.deepcopy(original);changed['native_numeric_units']['P_SYS_SOC0']='kW'
        with patch.object(m.source,'source_controls',return_value=changed),self.assertRaises(ValueError):
            m.provisional_standby_ac_energy(idle_hours=1.)


if __name__=='__main__':unittest.main()
