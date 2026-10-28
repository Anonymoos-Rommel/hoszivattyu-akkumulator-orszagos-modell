import unittest,math
from datetime import datetime,timezone
from modules.B07 import discharge_equivalent_reference as n
from modules.B08.engine import GridBoundaryRecord,B08ContractError

class ReferenceIntegrationTests(unittest.TestCase):
    def setUp(self):self.ref=n.capacity_sensitivity_reference()
    def project(self,x=5.,c=0.,d=0.,dt=1.,**kw):
        args=dict(charge_ac_kw=c,discharge_ac_kw=d,hours=dt,idle_convention=n.SCN_IDLE_ZERO,scenario_ref='SCN-INTEGRATION');args.update(kw)
        return n.project_b08_reference(self.ref,n.Inventory(x),**args)
    def row(self,**kw):
        args=dict(timestamp=datetime(2025,1,3,tzinfo=timezone.utc),source_entity_id='HH1',region_id='R1',region_scheme='EXPLICIT_TEST_SCN',b01_state_id='S3',source_refs=('PROFILE-HASH-TEST',),scenario_ref='SCN-INTEGRATION',reference=self.ref,inventory=n.Inventory(5.),charge_ac_kw=0.,discharge_ac_kw=0.,timestep_hours=.5,idle_convention=n.SCN_IDLE_ZERO,household_load_kw=.4,heat_pump_load_kw=.6);args.update(kw)
        return GridBoundaryRecord.from_discharge_equivalent_reference(**args)
    def test_post_step_bounds_match_native_alternative_steps(self):
        p=self.project(c=1.,dt=.5);x=p['actual']['x_end_kwh']
        up=n.step(self.ref,n.Inventory(x),charge_ac_kw=0.,discharge_ac_kw=self.ref.discharge_ac_source_limit_kw,hours=.5,idle_convention=n.SCN_IDLE_ZERO)
        down=n.step(self.ref,n.Inventory(x),charge_ac_kw=self.ref.charge.point(self.ref.charge.upper)[0],discharge_ac_kw=0.,hours=.5,idle_convention=n.SCN_IDLE_ZERO)
        self.assertEqual(p['physical_up_flex_kw'],up['delivered_discharge_ac_kwh']/.5)
        self.assertEqual(p['physical_down_flex_kw'],down['admitted_charge_ac_kwh']/.5)
        self.assertNotEqual(x,5.);self.assertEqual(p['battery_charge_kw'],p['actual']['admitted_charge_ac_kwh']/.5)
    def test_empty_full_and_below_minimum_are_known_zero(self):
        self.assertEqual(self.project(x=0.)['physical_up_flex_kw'],0.)
        self.assertEqual(self.project(x=10.)['physical_down_flex_kw'],0.)
        self.assertEqual(self.project(x=.01)['physical_up_flex_kw'],0.)
        self.assertEqual(self.project(x=math.nextafter(10.,0.))['physical_down_flex_kw'],0.)
    def test_no_SOC_group_standby_and_HP_once(self):
        row=self.row();self.assertAlmostEqual(row.net_grid_import_kw,1.00407)
        self.assertEqual(row.truth_context,'SCN');self.assertEqual(row.net_grid_export_kw,0.)
        for k in ('battery_charge_kw','battery_discharge_kw','soc_fraction','handoff_status','upstream_timestep_hours'):self.assertIsNone(getattr(row,k))
        row=self.row(discharge_ac_kw=.5);p=self.project(d=.5,dt=.5)
        self.assertEqual(p['standby_ac_kwh'],0.)
        self.assertAlmostEqual(row.net_grid_import_kw,1.-p['battery_discharge_kw'])
    def test_Q_bad_sources_idle_and_time_rejected(self):
        for args in ({'x':None},{'dt':0.},{'idle_convention':None},{'scenario_ref':''}):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):self.project(**args)
        with self.assertRaises(ValueError):self.row(reference=None)
        with self.assertRaises(ValueError):self.row(heat_pump_load_kw=float('nan'))
        with self.assertRaises(ValueError):self.row(source_refs=())
        for name in ('household_load_kw','heat_pump_load_kw'):
            with self.assertRaises(ValueError):self.row(**{name:True})
    def test_no_export_and_simultaneous_flow_rejected(self):
        with self.assertRaises(ValueError):self.row(discharge_ac_kw=1.5,household_load_kw=.01,heat_pump_load_kw=0.)
        with self.assertRaises(ValueError):self.project(c=1.,d=1.)
    def test_input_provenance_distinguishes_same_clipped_flow(self):
        a=self.project(x=10.,c=1.);b=self.project(x=10.,c=2.)
        self.assertEqual(a['battery_charge_kw'],b['battery_charge_kw'])
        self.assertNotEqual(a['input_sha256'],b['input_sha256'])
        self.assertIsNone(a['actual_bms_soc'])
        self.assertTrue(any(s.startswith('B07_INPUT_SHA256:') for s in self.row().source_refs))
        self.assertNotEqual(self.row().source_refs,self.row(household_load_kw=.5,heat_pump_load_kw=.5).source_refs)

if __name__=='__main__':unittest.main()
