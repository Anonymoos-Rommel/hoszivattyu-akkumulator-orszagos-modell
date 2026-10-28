"""Approved DJF earlier self-use; baseline and physical engine remain intact."""
import unittest,math
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
from modules.B12 import battery_reservation_reference as a

class WinterPriorityTests(unittest.TestCase):
    def setUp(self):self.ref=a.reference(household_policy=a.WINTER_PRIORITY)
    def load(self,month,hour,kw=1):
        start=datetime(2025,month,2,hour,tzinfo=a.LOCAL).astimezone(timezone.utc)
        return a.LoadHour(start,start+timedelta(hours=1),F(kw),F(0))
    def record(self,month,hour,*,x=10.,price=F(1),med=F(10),kw=1,policy=a.WINTER_PRIORITY):
        return a._hour_record(self.ref,self.load(month,hour,kw),price,med,policy,x,2.)
    def test_djf_15_discharge_priority_and_no_charge(self):
        for month in (12,1,2):
            r=self.record(month,15)
            self.assertGreater(r['native']['delivered_discharge_ac_kwh'],0.)
            self.assertEqual(r['native']['admitted_charge_ac_kwh'],0.)
    def test_15_at_reserve_remains_idle_not_cheap_charge(self):
        r=self.record(1,15,x=2.)
        self.assertEqual(r['native']['admitted_charge_ac_kwh'],0.)
        self.assertEqual(r['native']['delivered_discharge_ac_kwh'],0.)
        self.assertEqual(r['native']['x_end_kwh'],2.)
    def test_boundaries_and_other_cheap_windows(self):
        for h in (0,5,10,14):self.assertGreater(self.record(1,h,x=2.)['native']['admitted_charge_ac_kwh'],0.)
        for h in (6,9,22,23):
            r=self.record(1,h);self.assertEqual(r['native']['delivered_discharge_ac_kwh'],0.)
            self.assertEqual(r['native']['admitted_charge_ac_kwh'],0.)
        for h in (15,16,17,18,21):self.assertGreater(self.record(1,h)['native']['delivered_discharge_ac_kwh'],0.)
    def test_other_months_identical_hour_step_at_same_state(self):
        for month in (3,6,10,11):
            for h in range(24):
                for x in (2.,6.,10.):
                    self.assertEqual(self.record(month,h,x=x),self.record(month,h,x=x,policy=a.EVENING_PRIORITY))
    def test_baseline_still_charges_at_15_and_does_not_discharge_17(self):
        r=self.record(1,15,x=2.,policy=a.EVENING_PRIORITY)
        self.assertGreater(r['native']['admitted_charge_ac_kwh'],0.)
        self.assertEqual(self.record(1,17,policy=a.EVENING_PRIORITY)['native']['delivered_discharge_ac_kwh'],0.)
    def test_price_gate_removed_only_for_discharge_history_required(self):
        self.assertEqual(self.record(1,15,price=F(1))['native'],self.record(1,15,price=F(20))['native'])
        r=self.record(1,15,med=None)
        self.assertEqual(r['native']['admitted_charge_ac_kwh'],0.)
        self.assertEqual(r['native']['delivered_discharge_ac_kwh'],0.)
        self.assertEqual(self.record(1,14,x=2.,price=F(20))['native']['admitted_charge_ac_kwh'],0.)
    def test_own_load_power_and_physical_reserve(self):
        for x in (2.,2.000000000000001,2.1,5.,10.):
            for kw in (F(0),F(1,10),F(1),F(3)):
                r=self.record(1,17,x=x,kw=kw);n=r['native']
                self.assertGreaterEqual(n['x_end_kwh'],2.)
                self.assertLessEqual(n['delivered_discharge_ac_kwh'],min(1.5,float(kw)))
                self.assertFalse(r['charge_kw'] and r['discharge_kw'])
        with self.assertRaises(ValueError):self.record(1,17,x=1.)
    def test_shared_power_budget_and_distinct_case_identity(self):
        cap=self.ref.charge.point(self.ref.charge.upper)[0]
        rows=a._shared_hour(self.ref,self.load(1,14),F(1),F(10),{'HH1':2.,'HH2':2.},household_policy=a.WINTER_PRIORITY)
        self.assertLessEqual(sum((F.from_float(r['native']['admitted_charge_ac_kwh']) for r in rows.values()),F(0)),F.from_float(cap))
        start=datetime(2025,1,1,tzinfo=timezone.utc)
        loads=[a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),F(1),F(0)) for i in range(72)]
        pair=a.shared_budget_pair(loads,[F(1 if i%24<16 else 20) for i in range(72)],household_policy=a.WINTER_PRIORITY)
        for name,result in pair['shared_budget'].items():
            self.assertIn(a.WINTER_PRIORITY,result['case'].scenario_reference)
            self.assertEqual(result['audit']['legs']['reserved']['physical_status'],'PASS_SCN')
            self.assertNotEqual(result['case'].identity.household_actor_id,pair['shared_budget']['HH2' if name=='HH1' else 'HH1']['case'].identity.household_actor_id)
    def test_local_month_boundary_is_not_utc_month_boundary(self):
        start=datetime(2025,2,28,23,tzinfo=timezone.utc)
        load=a.LoadHour(start,start+timedelta(hours=1),F(1),F(0))
        # Local March1 00:00 must behave exactly like the unchanged policy.
        self.assertEqual(a._hour_record(self.ref,load,F(1),F(10),a.WINTER_PRIORITY,2.,2.),a._hour_record(self.ref,load,F(1),F(10),a.EVENING_PRIORITY,2.,2.))

if __name__=='__main__':unittest.main()
