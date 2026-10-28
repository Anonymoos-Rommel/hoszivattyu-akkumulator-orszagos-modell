"""Household priority removes only evening discharge price gate."""
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
import unittest
from modules.B12 import battery_reservation_reference as a

def inputs(start=datetime(2025,1,1,tzinfo=timezone.utc),hours=96):
    loads=tuple(a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),F(1),F(0)) for i in range(hours))
    # Cheap eligible charging, then low-priced evenings that the old rule skips.
    prices=tuple(F(1 if i%24<4 or 10<=i%24<16 else 2 if 17<=i%24<21 else 100) for i in range(hours))
    return loads,prices

class EveningPriorityTests(unittest.TestCase):
    def test_reference_initial_reserve_and_transfer_unchanged(self):
        self.assertEqual(a.reference(household_policy=a.CAPACITY10_HOUSEHOLD),a.reference(household_policy=a.EVENING_PRIORITY))
        self.assertEqual(a.initial_and_protected(a.EVENING_PRIORITY),(2.,2.))
    def test_equal_prices_do_not_charge_but_warmup_never_disappears(self):
        loads,_=inputs();_,rows=a.schedules(loads,(F(10),)*len(loads),household_policy=a.EVENING_PRIORITY)
        for items in rows.values():
            self.assertTrue(all(r['charge_kw']==0. for r in items))
            self.assertTrue(all(r['charge_kw']==r['discharge_kw']==0 for r in items[:24]))
        # No free household inventory is manufactured from protected stock.
        self.assertTrue(all(r['discharge_kw']==0 for r in rows['reserved']))
        self.assertTrue(any(r['discharge_kw'] for r in rows['household_only'][24:]))
    def test_low_evening_price_changes_discharge_not_charge_eligibility(self):
        loads,prices=inputs();_,old=a.schedules(loads,prices,household_policy=a.CAPACITY10_HOUSEHOLD)
        _,new=a.schedules(loads,prices,household_policy=a.EVENING_PRIORITY)
        added=[r for o,r in zip(old['reserved'],new['reserved']) if o['discharge_kw']==0 and r['discharge_kw']>0]
        self.assertTrue(added)
        self.assertTrue(any(F(r['control_price_exact'])<=F(r['previous24_median_exact']) for r in added))
        for r in new['reserved']:
            h=r['load'].start.astimezone(a.LOCAL).hour
            if r['charge_kw']:
                self.assertTrue(h<6 or 10<=h<16)
                self.assertLess(F(r['control_price_exact']),F(r['previous24_median_exact']))
    def test_windows_dst_power_load_and_protected_stock(self):
        for start in (datetime(2025,3,29,tzinfo=timezone.utc),datetime(2025,10,25,tzinfo=timezone.utc)):
            loads,prices=inputs(start);_,legs=a.schedules(loads,prices,household_policy=a.EVENING_PRIORITY)
            for name,rows in legs.items():
                for r in rows:
                    h=r['load'].start.astimezone(a.LOCAL).hour;n=r['native']
                    if r['discharge_kw']:self.assertTrue(18<=h<22)
                    if r['charge_kw']:self.assertTrue(h<6 or 10<=h<16)
                    self.assertLessEqual(n['delivered_discharge_ac_kwh'],min(1.5,float(r['load'].base_kw+r['load'].hp_kw)))
                    self.assertGreaterEqual(n['x_end_kwh'],2. if name=='reserved' else 0.)
                    self.assertLessEqual(n['x_end_kwh'],10.)
                    self.assertFalse(r['charge_kw'] and r['discharge_kw'])
    def test_no_future_price_reads(self):
        loads,prices=inputs();_,left=a.schedules(loads,prices,household_policy=a.EVENING_PRIORITY)
        _,right=a.schedules(loads,prices[:60]+(F(999),)*36,household_policy=a.EVENING_PRIORITY)
        self.assertEqual(left['reserved'][:60],right['reserved'][:60])
    def test_native_audit_identity_and_no_activation(self):
        loads,prices=inputs();old=a.evaluate(loads,prices,household_policy=a.CAPACITY10_HOUSEHOLD);new=a.evaluate(loads,prices,household_policy=a.EVENING_PRIORITY)
        self.assertNotEqual(old['case'].content_sha256,new['case'].content_sha256)
        for name,leg in new['audit']['legs'].items():
            self.assertEqual(leg['physical_status'],'PASS_SCN');self.assertEqual(leg['allocation_status'],'PASS_SCN')
            self.assertNotEqual(leg['rights']['status'],'FAIL')
            self.assertEqual(leg['initial_inventory_kwh'],2.)
        self.assertFalse(new['actual_activation']);self.assertIsNone(new['ROI'])

if __name__=='__main__':unittest.main()
