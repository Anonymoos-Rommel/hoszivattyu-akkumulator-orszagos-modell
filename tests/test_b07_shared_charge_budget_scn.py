"""Approved two-household shared AC budget; native physical limits unchanged."""
import math,unittest
from datetime import datetime,timezone
from fractions import Fraction as F
from modules.B12 import battery_reservation_reference as a
from test_b07_coordinated_pair_scn import inputs

class SharedBudgetTests(unittest.TestCase):
    def setUp(self):
        self.ref=a.reference(household_policy=a.EVENING_PRIORITY)
        self.load=a.LoadHour(datetime(2025,1,2,0,tzinfo=timezone.utc),datetime(2025,1,2,1,tzinfo=timezone.utc),F(1),F(0))
        self.cap=self.ref.charge.point(self.ref.charge.upper)[0]
    def test_exact_binary_subtraction_rounding_conservatively_bounded(self):
        cap,used=1.,.1
        self.assertGreater(F.from_float(cap-used)+F.from_float(used),F.from_float(cap))
        available=a._remaining_charge_budget(cap,used)
        self.assertLessEqual(F.from_float(available)+F.from_float(used),F.from_float(cap))
        self.assertEqual(available,math.nextafter(cap-used,0.))
    def test_equal_shares_and_supported_curves(self):
        rows=a._shared_hour(self.ref,self.load,F(1),F(10),{'HH1':2.,'HH2':2.})
        for item in rows.values():
            n=item['native'];self.assertAlmostEqual(n['admitted_charge_ac_kwh'],self.cap/2,places=12)
            self.assertGreaterEqual(n['admitted_charge_dc_kwh'],self.ref.charge.lower)
        self.assertLessEqual(math.fsum(r['native']['admitted_charge_ac_kwh'] for r in rows.values()),self.cap)
    def test_single_supported_point_lower_inventory_then_HH1(self):
        # Allocation-only stub, not an alternative physical/source curve.
        # Actual native physics and guards are exercised by all other tests.
        from unittest.mock import patch
        def stub(ref,load,price,med,policy,x,floor,*,charge_budget_kw):
            return {'native':{'admitted_charge_ac_kwh':charge_budget_kw if charge_budget_kw>=2. else 0.}}
        with patch.object(a,'_hour_record',side_effect=stub):
            for states,winner in [({'HH1':2.,'HH2':3.},'HH1'),({'HH1':3.,'HH2':2.},'HH2'),({'HH1':2.,'HH2':2.},'HH1')]:
                rows=a._shared_hour(self.ref,self.load,F(1),F(10),states)
                self.assertGreater(rows[winner]['native']['admitted_charge_ac_kwh'],0.)
                self.assertEqual(rows['HH2' if winner=='HH1' else 'HH1']['native']['admitted_charge_ac_kwh'],0.)
    def test_full_skipped_and_unused_reallocated(self):
        rows=a._shared_hour(self.ref,self.load,F(1),F(10),{'HH1':10.,'HH2':2.})
        self.assertEqual(rows['HH1']['native']['admitted_charge_ac_kwh'],0.)
        self.assertAlmostEqual(rows['HH2']['native']['admitted_charge_ac_kwh'],self.cap,places=12)
    def test_near_full_no_extrapolation_or_capacity_overrun(self):
        rows=a._shared_hour(self.ref,self.load,F(1),F(10),{'HH1':9.99,'HH2':2.})
        self.assertEqual(rows['HH1']['native']['admitted_charge_ac_kwh'],0.)
        self.assertAlmostEqual(rows['HH2']['native']['admitted_charge_ac_kwh'],self.cap,places=12)
        for item in rows.values():self.assertLessEqual(item['native']['x_end_kwh'],10.)
    def test_low_supported_budget_declined_not_extrapolated(self):
        row=a._hour_record(self.ref,self.load,F(1),F(10),a.EVENING_PRIORITY,2.,2.,charge_budget_kw=0.001)
        self.assertEqual(row['native']['admitted_charge_ac_kwh'],0.)
        for bad in (-1.,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):a._hour_record(self.ref,self.load,F(1),F(10),a.EVENING_PRIORITY,2.,2.,charge_budget_kw=bad)
    def test_three_arms_identity_baseline_unchanged(self):
        x=inputs(hours=72);pair=a.shared_budget_pair(*x);old=a.coordinated_pair(*x)
        for mode in ('independent','coordinated'):
            for name in ('HH1','HH2'):
                self.assertEqual(pair[mode][name]['case'],old[mode][name]['case'])
                self.assertEqual(pair[mode][name]['controller_records'],old[mode][name]['controller_records'])
        self.assertNotEqual(pair['shared_budget']['HH1']['case'].content_sha256,pair['coordinated']['HH1']['case'].content_sha256)
    def test_causal_no_future_prices_and_warmup(self):
        loads,prices=inputs(hours=72);left=a.shared_budget_pair(loads,prices)
        right=a.shared_budget_pair(loads,prices[:50]+(F(999),)*22)
        self.assertEqual(left['shared_selection'][:50],right['shared_selection'][:50])
        for name in ('HH1','HH2'):
            rows=left['shared_budget'][name]['controller_records']['reserved']
            self.assertTrue(all(r['charge_kw']==r['discharge_kw']==0 for r in rows[:24]))
    def test_DST_bounds_physical_balance_and_no_export(self):
        for start in (datetime(2025,3,29,tzinfo=timezone.utc),datetime(2025,10,25,tzinfo=timezone.utc)):
            pair=a.shared_budget_pair(*inputs(start,hours=72))
            for name,result in pair['shared_budget'].items():
                self.assertEqual(result['audit']['legs']['reserved']['physical_status'],'PASS_SCN')
                for r in result['controller_records']['reserved']:
                    n=r['native'];h=r['load'].start.astimezone(a.LOCAL).hour
                    self.assertGreaterEqual(n['x_end_kwh'],2.);self.assertLessEqual(n['x_end_kwh'],10.)
                    self.assertFalse(r['charge_kw'] and r['discharge_kw'])
                    if r['charge_kw']:self.assertTrue(h<6 or 10<=h<16);self.assertLess(F(r['control_price_exact']),F(r['previous24_median_exact']))
                    if r['discharge_kw']:self.assertTrue(18<=h<22)
                    self.assertLessEqual(n['delivered_discharge_ac_kwh'],min(1.5,float(r['load'].base_kw+r['load'].hp_kw)))
    def test_no_price_history_no_charge_and_reserve(self):
        rows=a._shared_hour(self.ref,self.load,F(1),None,{'HH1':2.,'HH2':2.})
        for row in rows.values():
            self.assertEqual(row['native']['x_end_kwh'],2.)
            self.assertEqual(row['native']['admitted_charge_ac_kwh'],0.)

if __name__=='__main__':unittest.main()
