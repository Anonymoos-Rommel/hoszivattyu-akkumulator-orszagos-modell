"""Only the new multi-event gaps; single-event edge cases remain in their tests."""
import unittest
from dataclasses import replace
from datetime import timedelta
from fractions import Fraction as F
from unittest.mock import patch
from modules.B12 import battery_reservation_reference as a

def inputs():
    loads=[];prices=[]
    for i in range(144):
        t=a.START+timedelta(hours=i);local=t.astimezone(a.LOCAL)
        # Changing, fully known own-demand blocks, not a forecast of future evenings.
        base=F(local.day,10) if 18<=local.hour<22 else F(1,4)
        loads.append(a.LoadHour(t,t+timedelta(hours=1),base,F(1,2)))
        prices.append(F(1 if local.hour<6 or 10<=local.hour<12 else 20))
    return tuple(loads),tuple(prices)

class RepeatedSignalTests(unittest.TestCase):
    def pair(self,case=a.THREE_SIGNALS):
        return a.shared_budget_pair(*inputs(),household_policy=a.WINTER_PRIORITY,
                                   profile_case=a.MIXED_HP_BASE,signal_case=case)

    def test_exact_three_dates_unique_issue_validity_and_once_each(self):
        sigs=a.approved_signals(a.THREE_SIGNALS)
        self.assertEqual(len(sigs),3);self.assertEqual(len({s.signal_id for s in sigs}),3)
        for day,s in zip((3,4,5),sigs):
            self.assertEqual((s.issued_at.astimezone(a.LOCAL).day,s.issued_at.astimezone(a.LOCAL).hour),(day,9))
            self.assertEqual((s.valid_from.astimezone(a.LOCAL).day,s.valid_from.astimezone(a.LOCAL).hour),(day,10))
            self.assertEqual(s.valid_until-s.valid_from,timedelta(hours=1))
        pair=self.pair();notes=pair['signal_selection']
        self.assertEqual([n['signal_id'] for n in notes],[s.signal_id for s in sigs])
        self.assertEqual(pair['signal_provenance']['processed_signal_ids'],[s.signal_id for s in sigs])
        self.assertTrue(all(n['households'][h]['charging_disabled'] for n in notes for h in ('HH1','HH2')))

    def test_duplicate_overlap_and_unordered_schedules_rejected_before_execution(self):
        one,two,three=a.approved_signals(a.THREE_SIGNALS)
        invalid=((one,one),(one,replace(two,valid_from=one.valid_from,valid_until=one.valid_until)),
                 (two,one),(one,replace(two,signal_id=one.signal_id)),
                 (replace(one,valid_until=one.valid_until+timedelta(hours=1)),),
                 (replace(one,issued_at=one.valid_from+timedelta(seconds=1)),))
        for schedule in invalid:
            with self.subTest(schedule=schedule):
                with self.assertRaises(ValueError):a._validated_signal_schedule(schedule)

    def test_state_continues_every_hour_and_first_event_matches_single(self):
        repeated=self.pair();single=self.pair(a.ONE_SIGNAL)
        second=a.approved_signals(a.THREE_SIGNALS)[1].valid_from
        for h in ('HH1','HH2'):
            rows=repeated['shared_budget'][h]['controller_records']['reserved']
            old=single['shared_budget'][h]['controller_records']['reserved']
            self.assertEqual(rows[0]['native']['x_start_kwh'],2.)
            for prev,cur in zip(rows,rows[1:]):
                self.assertEqual(prev['native']['x_end_kwh'],cur['native']['x_start_kwh'])
            self.assertEqual([r for r in rows if r['load'].start<second],
                             [r for r in old if r['load'].start<second])
            self.assertIn(a.THREE_SIGNALS,repeated['shared_budget'][h]['case'].scenario_reference)

    def test_each_event_refreshes_from_its_last_closed_own_block(self):
        pair=self.pair();ref=a.reference(household_policy=a.WINTER_PRIORITY)
        for day,n in zip((3,4,5),pair['signal_selection']):
            for h,own in (('HH1',F(day-1,10)+F(1,2)),('HH2',F(day-1,10))):
                b=n['households'][h]['budget']
                self.assertEqual(b['source_local_date'],f'2025-01-{day-1:02d}')
                self.assertAlmostEqual(b['estimated_dc_kwh'],4*ref.discharge.point(float(own))[0],places=12)

    def test_missing_middle_estimate_does_not_reuse_old_or_poison_next(self):
        original=a._evening_budget
        def selective(ref,history,decision):
            if decision.astimezone(a.LOCAL).day==4:
                return {'status':'Q','reason':'INCOMPLETE_LAST_CLOSED_EVENING',
                        'floor_kwh':None,'estimated_dc_kwh':None}
            return original(ref,history,decision)
        with patch.object(a,'_evening_budget',side_effect=selective):pair=self.pair()
        first,middle,last=pair['signal_selection']
        for h in ('HH1','HH2'):
            self.assertIsNone(middle['households'][h]['budget']['floor_kwh'])
            self.assertFalse(middle['households'][h]['extra_eligible'])
            self.assertEqual(middle['households'][h]['actual_discharge_ac_kwh'],0.)
            self.assertEqual(last['households'][h]['budget']['source_local_date'],'2025-01-04')
            self.assertEqual(first['households'][h]['budget']['source_local_date'],'2025-01-02')

    def test_partial_input_does_not_claim_unobserved_events_processed(self):
        loads,prices=inputs();loads=loads[:72];prices=prices[:72]
        pair=a.shared_budget_pair(loads,prices,household_policy=a.WINTER_PRIORITY,
                                 profile_case=a.MIXED_HP_BASE,signal_case=a.THREE_SIGNALS)
        self.assertEqual(len(pair['signal_selection']),1)
        self.assertEqual(len(pair['signal_provenance']['events']),3)
        self.assertEqual(len(pair['signal_provenance']['processed_signal_ids']),1)

if __name__=='__main__':unittest.main()
