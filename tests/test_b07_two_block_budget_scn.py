"""Only the new two-block maximum and no-gap-fallback requirements."""
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
from modules.B12 import battery_reservation_reference as a

def block(day,own):
    start=datetime(2025,1,day,14,tzinfo=timezone.utc)
    return tuple(a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),own,F(0)) for i in range(7))

class TwoBlockBudgetTests(unittest.TestCase):
    def setUp(self):
        self.ref=a.reference(household_policy=a.WINTER_PRIORITY);self.t=a.approved_signal().valid_from

    def test_larger_exact_DC_block_and_deterministic_latest_tie(self):
        for early,late,selected in ((F(3,4),F(1,2),'2025-01-01'),(F(1,2),F(3,4),'2025-01-02'),(F(1,2),F(1,2),'2025-01-02')):
            result=a._two_block_budget(self.ref,block(1,early)+block(2,late),self.t)
            exact=max(7*F.from_float(self.ref.discharge.point(float(v))[0]) for v in (early,late))
            self.assertEqual(result['selected_source_local_date'],selected)
            self.assertEqual(result['decision_utc'],self.t.isoformat())
            self.assertEqual(F(result['estimated_dc_kwh_exact_binary']),exact)
            self.assertGreaterEqual(F.from_float(result['floor_kwh']),2+exact)
            self.assertEqual(len(result['blocks']),2)

    def test_any_missing_invalid_or_unsupported_block_is_Q_not_single_block(self):
        early=block(1,F(1,2));late=block(2,F(3,4))
        variants=(late,early,early[:-1]+late,
                  (replace(early[0],base_kw=F(-1)),)+early[1:]+late,
                  block(1,F(1,100000))+late)
        for history in variants:
            result=a._two_block_budget(self.ref,history,self.t)
            self.assertEqual(result['status'],'Q');self.assertIsNone(result['floor_kwh'])
            self.assertIsNone(result['estimated_dc_kwh'])

    def test_only_last_two_closed_blocks_no_future_or_older_max(self):
        current=block(1,F(1,2))+block(2,F(3,4))
        result=a._two_block_budget(self.ref,current,self.t)
        older=tuple(replace(x,start=x.start-timedelta(days=1),end=x.end-timedelta(days=1),base_kw=F(3,2)) for x in block(1,F(1,2)))
        future=block(3,F(3,2))
        self.assertEqual(a._two_block_budget(self.ref,older+current+future,self.t),result)

    def test_same_signals_identity_distinction_and_continuous_native_stock(self):
        loads=[];prices=[]
        for i in range(144):
            t=a.START+timedelta(hours=i);loc=t.astimezone(a.LOCAL)
            base=F(3,5) if loc.day%2 else F(1,4)
            loads.append(a.LoadHour(t,t+timedelta(hours=1),base,F(1,10)))
            prices.append(F(1 if loc.hour<6 or 10<=loc.hour<12 else 20))
        args=dict(household_policy=a.WINTER_PRIORITY,profile_case=a.MIXED_HP_BASE)
        old=a.shared_budget_pair(tuple(loads),tuple(prices),signal_case=a.THREE_SIGNALS_FULL_BLOCK,**args)
        new=a.shared_budget_pair(tuple(loads),tuple(prices),signal_case=a.THREE_SIGNALS_TWO_BLOCKS,**args)
        self.assertEqual(old['signal_provenance']['events'],new['signal_provenance']['events'])
        for h in ('HH1','HH2'):
            n=new['shared_budget'][h];self.assertNotEqual(n['case'].content_sha256,old['shared_budget'][h]['case'].content_sha256)
            self.assertIn(a.THREE_SIGNALS_TWO_BLOCKS,n['case'].scenario_reference)
            rs=n['controller_records']['reserved']
            for previous,current in zip(rs,rs[1:]):self.assertEqual(previous['native']['x_end_kwh'],current['native']['x_start_kwh'])
            for event in new['signal_selection']:
                b=event['households'][h]['budget'];self.assertEqual(len(b['blocks']),2)
                self.assertEqual(len(b['blocks'][0]['parts']),7);self.assertEqual(len(b['blocks'][1]['parts']),7)
                self.assertEqual(F(b['estimated_dc_kwh_exact_binary']),max(F(x['estimated_dc_kwh_exact_binary']) for x in b['blocks']))

if __name__=='__main__':unittest.main()
