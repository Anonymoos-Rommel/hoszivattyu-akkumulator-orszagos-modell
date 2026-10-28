"""The approved reserve-estimate horizon change, with legacy cases preserved."""
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
from modules.B12 import battery_reservation_reference as a

def inputs():
    start=a.START;loads=[];prices=[]
    for i in range(144):
        t=start+timedelta(hours=i);loc=t.astimezone(a.LOCAL)
        base=F(1,5) if 15<=loc.hour<18 else F(1,4)
        loads.append(a.LoadHour(t,t+timedelta(hours=1),base,F(1,2)))
        prices.append(F(1 if loc.hour<6 or 10<=loc.hour<12 else 20))
    return tuple(loads),tuple(prices)

class FullWinterBudgetTests(unittest.TestCase):
    def setUp(self):
        self.ref=a.reference(household_policy=a.WINTER_PRIORITY)
        self.decision=a.approved_signal().valid_from
        start=datetime(2025,1,2,14,tzinfo=timezone.utc)
        self.history=tuple(a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),F(1,4),F(1,2)) for i in range(7))

    def test_seven_own_hours_use_same_inverse_curve_and_rounding(self):
        old=a._evening_budget(self.ref,self.history,self.decision)
        new=a._evening_budget(self.ref,self.history,self.decision,start_hour=15)
        self.assertEqual(len(old['parts']),4);self.assertEqual(len(new['parts']),7)
        self.assertEqual(new['source_local_date'],'2025-01-02')
        expected=7*F.from_float(self.ref.discharge.point(.75)[0])
        self.assertEqual(F(new['estimated_dc_kwh_exact_binary']),expected)
        self.assertGreaterEqual(F.from_float(new['floor_kwh']),2+expected)
        self.assertAlmostEqual(new['estimated_dc_kwh'],7*self.ref.discharge.point(.75)[0],places=12)

    def test_missing_or_unsupported_afternoon_cannot_pass_with_complete_evening(self):
        for history in (self.history[1:],(replace(self.history[0],base_kw=F(1,100000),hp_kw=F(0)),)+self.history[1:]):
            self.assertIsNotNone(a._evening_budget(self.ref,history,self.decision)['floor_kwh'])
            result=a._evening_budget(self.ref,history,self.decision,start_hour=15)
            self.assertEqual(result['status'],'Q');self.assertIsNone(result['floor_kwh'])

    def test_same_schedule_separate_scenario_identity_no_reset(self):
        args=dict(household_policy=a.WINTER_PRIORITY,profile_case=a.MIXED_HP_BASE)
        old=a.shared_budget_pair(*inputs(),signal_case=a.THREE_SIGNALS,**args)
        new=a.shared_budget_pair(*inputs(),signal_case=a.THREE_SIGNALS_FULL_BLOCK,**args)
        self.assertEqual(a.approved_signals(a.THREE_SIGNALS),a.approved_signals(a.THREE_SIGNALS_FULL_BLOCK))
        self.assertEqual(old['signal_provenance']['events'],new['signal_provenance']['events'])
        self.assertIn('local15-22',new['signal_provenance']['reserve_estimation']['history_block'])
        for name in ('HH1','HH2'):
            x=new['shared_budget'][name];b=old['shared_budget'][name]
            self.assertNotEqual(x['case'].content_sha256,b['case'].content_sha256)
            self.assertIn(a.THREE_SIGNALS_FULL_BLOCK,x['case'].scenario_reference)
            records=x['controller_records']['reserved']
            for prev,cur in zip(records,records[1:]):self.assertEqual(prev['native']['x_end_kwh'],cur['native']['x_start_kwh'])
            for event in new['signal_selection']:
                budget=event['households'][name]['budget'];self.assertEqual(len(budget['parts']),7)
                self.assertEqual([datetime.fromisoformat(p['start_utc']).astimezone(a.LOCAL).hour for p in budget['parts']],list(range(15,22)))

    def test_unapproved_history_start_rejected(self):
        with self.assertRaises(ValueError):a._evening_budget(self.ref,self.history,self.decision,start_hour=14)

if __name__=='__main__':unittest.main()
