"""Exact owner-adopted capacity sensitivity; no observed10kWh product claim."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
from unittest.mock import patch
import unittest
from modules.B12 import battery_reservation_reference as a
from modules.B07 import discharge_equivalent_reference as n
from modules.B07 import shared_use_schedule_contract as s

def inputs(start=datetime(2025,1,1,tzinfo=timezone.utc),hours=96):
    loads=tuple(a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),F(2),F(0)) for i in range(hours))
    prices=tuple(F(10 if i%24<6 or 10<=i%24<16 else 80) for i in range(hours))
    return loads,prices

class CapacitySensitivityTests(unittest.TestCase):
    def test_capacity_only_transfer_and_measured_identity_preserved(self):
        measured=a.reference();scenario=n.capacity_sensitivity_reference()
        self.assertEqual(measured.capacity_dc_output_equiv_kwh,7.572)
        self.assertEqual(scenario.capacity_dc_output_equiv_kwh,10.)
        self.assertNotEqual(measured.identity,scenario.identity)
        self.assertEqual(replace(scenario,capacity_dc_output_equiv_kwh=7.572,identity=measured.identity),measured)
        self.assertTrue(n.is_capacity_sensitivity_reference(scenario))
    def test_measured_identity_cannot_be_retagged_10kWh(self):
        bad=replace(a.reference(),capacity_dc_output_equiv_kwh=10.)
        with self.assertRaises(ValueError):n.run(bad,initial_dc_output_equiv_kwh=2.,commands=[dict(charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.)],idle_convention=n.SCN_IDLE_ZERO)
    def test_narrow_scn_rejects_capacity_eta_power_and_idle_tampering(self):
        ref=n.capacity_sensitivity_reference()
        for bad in (replace(ref,capacity_dc_output_equiv_kwh=12.),replace(ref,battery_dc_cycle_efficiency=.99),replace(ref,empty_ac_test_kw=0.),replace(ref,discharge_ac_source_limit_kw=9.),replace(ref,charge=replace(ref.charge,points=tuple((p,e*.99) for p,e in ref.charge.points)))):
            self.assertFalse(n.is_capacity_sensitivity_reference(bad))
            with self.assertRaises(ValueError):n.step(bad,n.Inventory(2.),charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.,idle_convention=n.SCN_IDLE_ZERO)
    def test_default_idle_remains_Q_for_capacity_scn(self):
        ref=n.capacity_sensitivity_reference()
        out=n.step(ref,n.Inventory(2.),charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.)
        self.assertIsNone(out['x_end_kwh'])
    def test_named_scn_native_run_labels_parameter_transfer(self):
        out=n.run(n.capacity_sensitivity_reference(),initial_dc_output_equiv_kwh=2.,commands=[dict(charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.)],idle_convention=n.SCN_IDLE_ZERO)
        self.assertIn('OWNER_APPROVED',str(out))
        self.assertIn('UNVALIDATED_PARAMETER_TRANSFER',str(out))
    def test_both_legs_start2_and_reservation_remains2(self):
        loads,prices=inputs();out=a.evaluate(loads,prices,household_policy=a.CAPACITY10_HOUSEHOLD)
        self.assertEqual(out['case'].identity.capacity_kwh,10.)
        self.assertEqual(out['case'].identity.device_id,n.CAPACITY_SCN_ID)
        self.assertFalse(out['parameter_transfer']['actual_product_10kWh_validated'])
        for key,leg in out['audit']['legs'].items():
            self.assertEqual(leg['initial_inventory_kwh'],2.)
            self.assertEqual(leg['physical_status'],'PASS_SCN');self.assertEqual(leg['allocation_status'],'PASS_SCN')
            self.assertNotEqual(leg['rights']['status'],'FAIL')
        leg=out['audit']['legs']['reserved']
        self.assertEqual(leg['idle_ac']['status'],'SCN_TRANSFERRED_AGGREGATE_ONLY')
        self.assertTrue(all(r['actors'][a.S]['available_before_kwh']==2. for r in leg['rights']['intervals']))
        self.assertFalse(out['actual_activation']);self.assertIsNone(out['ROI'])
    def test_18_22_cap15_no_export_and_unchanged_charge_windows_DST(self):
        for date in (datetime(2025,3,29,tzinfo=timezone.utc),datetime(2025,10,25,tzinfo=timezone.utc)):
            loads,prices=inputs(date);_,legs=a.schedules(loads,prices,household_policy=a.CAPACITY10_HOUSEHOLD)
            for key,rows in legs.items():
                active=set()
                for item in rows:
                    h=item['load'].start.astimezone(a.LOCAL).hour;r=item['native']
                    if item['discharge_kw']:active.add(h);self.assertTrue(18<=h<22)
                    if item['charge_kw']:self.assertTrue(h<6 or 10<=h<16)
                    self.assertLessEqual(r['delivered_discharge_ac_kwh'],1.5)
                    self.assertLessEqual(r['delivered_discharge_ac_kwh'],float(item['load'].base_kw+item['load'].hp_kw))
                    self.assertGreaterEqual(r['x_end_kwh'],2. if key=='reserved' else 0.)
                    self.assertLessEqual(r['x_end_kwh'],10.)
                    self.assertFalse(item['charge_kw'] and item['discharge_kw'])
                self.assertTrue({18,21}<=active)
    def test_policy_reference_mismatch_and_missing_lineage_rejected(self):
        loads,prices=inputs();ref,records=a.schedules(loads,prices,household_policy=a.CAPACITY10_HOUSEHOLD)
        with self.assertRaises(ValueError):a.build_case(ref,records)
        case=a.build_case(ref,records,household_policy=a.CAPACITY10_HOUSEHOLD)
        bad=replace(case,source_pins=());bad=replace(bad,content_sha256=s.content_digest(bad))
        with self.assertRaises(ValueError):s.evaluate_shared_use(bad)
    def test_real_deficit_remains_failure(self):
        loads,prices=inputs();ref,records=a.schedules(loads,prices,household_policy=a.CAPACITY10_HOUSEHOLD)
        case=a.build_case(ref,records,household_policy=a.CAPACITY10_HOUSEHOLD)
        g=case.actual_leg.agreement
        # No energy is created to satisfy a larger initial reservation.
        g=replace(g,initial_protected_kwh=s.Term('SCN',3.,'SCN:test-shortage'))
        g=replace(g,content_sha256=s.content_digest(g));case=replace(case,actual_leg=replace(case.actual_leg,agreement=g));case=replace(case,content_sha256=s.content_digest(case))
        out=s.evaluate_shared_use(case)
        self.assertEqual(out['legs']['reserved']['rights']['status'],'FAIL')
        self.assertIn('INITIAL_PROTECTED_TARGET_UNMET',out['legs']['reserved']['rights']['failures'])
    def test_cheap_price_filter_still_required(self):
        loads,prices=inputs();_,records=a.schedules(loads,(F(10),)*len(loads),household_policy=a.CAPACITY10_HOUSEHOLD)
        self.assertTrue(all(r['charge_kw']==r['discharge_kw']==0. for r in records['reserved']))

if __name__=='__main__':unittest.main()
