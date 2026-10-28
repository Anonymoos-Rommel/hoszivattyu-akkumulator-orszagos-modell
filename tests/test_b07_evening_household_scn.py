"""Controller variant witnesses: synthetic prices, preserved native physics."""
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
import unittest
from modules.B12 import battery_reservation_reference as a
from modules.B07 import shared_use_schedule_contract as s

def inputs(start=datetime(2025,1,1,tzinfo=timezone.utc),hours=96,load=F(3,2)):
    loads=tuple(a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),load,F(0)) for i in range(hours))
    prices=tuple(F(10 if i%24<6 or 10<=i%24<16 else 80) for i in range(hours))
    return loads,prices

class EveningHouseholdTests(unittest.TestCase):
    def test_default_and_explicit_original_policy_identical(self):
        loads,prices=inputs()
        self.assertEqual(a.schedules(loads,prices),a.schedules(loads,prices,household_policy=a.DEFAULT_HOUSEHOLD))
    def test_unknown_policy_rejected(self):
        loads,prices=inputs()
        with self.assertRaises(ValueError):a.schedules(loads,prices,household_policy='18_24')
    def test_boundaries_cap_reserve_no_export_and_same_charge_windows(self):
        for start in (datetime(2025,3,29,tzinfo=timezone.utc),datetime(2025,10,25,tzinfo=timezone.utc)):
            loads,prices=inputs(start);_,legs=a.schedules(loads,prices,household_policy=a.EVENING_HOUSEHOLD)
            for key,rows in legs.items():
                for row in rows:
                    h=row['load'].start.astimezone(a.LOCAL).hour;r=row['native']
                    if row['charge_kw']:self.assertTrue(h<6 or 10<=h<16)
                    if row['discharge_kw']:self.assertTrue(18<=h<22)
                    self.assertLessEqual(r['delivered_discharge_ac_kwh'],1.)
                    self.assertLessEqual(r['delivered_discharge_ac_kwh'],float(row['load'].base_kw+row['load'].hp_kw))
                    self.assertGreaterEqual(r['x_end_kwh'],a.PROTECTED if key=='reserved' else 0.)
                    self.assertLessEqual(r['x_end_kwh'],7.572)
                    self.assertFalse(row['charge_kw'] and row['discharge_kw'])
    def test_high_load_exercises_18_and21_but_never17_or22(self):
        loads,prices=inputs();_,legs=a.schedules(loads,prices,household_policy=a.EVENING_HOUSEHOLD)
        active={r['load'].start.astimezone(a.LOCAL).hour for r in legs['reserved'] if r['discharge_kw']}
        self.assertTrue({18,21}<=active)
        self.assertTrue(active<={18,19,20,21})
    def test_price_threshold_retained(self):
        loads,_=inputs();_,legs=a.schedules(loads,(F(10),)*len(loads),household_policy=a.EVENING_HOUSEHOLD)
        self.assertTrue(all(r['charge_kw']==r['discharge_kw']==0 for r in legs['reserved']))
    def test_low_load_not_synthetic_1kw_and_min_curve_not_bypassed(self):
        loads,prices=inputs(load=F(1,1000));_,legs=a.schedules(loads,prices,household_policy=a.EVENING_HOUSEHOLD)
        self.assertTrue(all(r['discharge_kw']==0 for r in legs['reserved']))
    def test_native_audit_and_separate_scenario_identity(self):
        loads,prices=inputs();old=a.evaluate(loads,prices);new=a.evaluate(loads,prices,household_policy=a.EVENING_HOUSEHOLD)
        self.assertNotEqual(old['case'].content_sha256,new['case'].content_sha256)
        self.assertEqual(old['case'].actual_leg.initial_inventory_kwh,new['case'].actual_leg.initial_inventory_kwh)
        self.assertEqual(old['case'].actual_leg.agreement,new['case'].actual_leg.agreement)
        for leg in new['audit']['legs'].values():
            self.assertEqual(leg['physical_status'],'PASS_SCN')
            self.assertEqual(leg['allocation_status'],'PASS_SCN')
            self.assertNotEqual(leg['rights']['status'],'FAIL')
        self.assertFalse(new['actual_activation']);self.assertIsNone(new['ROI'])

if __name__=='__main__':unittest.main()
