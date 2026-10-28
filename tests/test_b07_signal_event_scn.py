"""One fixed SCN event; causal evening history and unchanged native limits."""
import unittest,math
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
from unittest.mock import patch
from modules.B12 import battery_reservation_reference as a

def inputs(start=None,hours=96,base=F(1,4),hp=F(1,2)):
    start=start or a.START
    loads=tuple(a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),base,hp) for i in range(hours))
    prices=tuple(F(1 if i%24<6 or 10<=i%24<12 else 20) for i in range(hours))
    return loads,prices

class SignalTests(unittest.TestCase):
    def setUp(self):self.ref=a.reference(household_policy=a.WINTER_PRIORITY)
    def pair(self,signal=a.ONE_SIGNAL,**kwargs):
        return a.shared_budget_pair(*inputs(**kwargs),household_policy=a.WINTER_PRIORITY,profile_case=a.MIXED_HP_BASE,signal_case=signal)
    def history(self,base=F(1,4),hp=F(1,2)):
        return inputs(start=datetime(2025,1,2,17,tzinfo=timezone.utc),hours=4,base=base,hp=hp)[0]
    def test_exact_issue_validity_and_halfopen_hour_alignment(self):
        signal=a.approved_signal();self.assertEqual(signal.issued_at,datetime(2025,1,3,8,tzinfo=timezone.utc))
        self.assertEqual(signal.valid_from.astimezone(a.LOCAL).hour,10)
        self.assertEqual(signal.valid_until.astimezone(a.LOCAL).hour,11)
        load=inputs(start=signal.valid_from,hours=1)[0][0]
        self.assertTrue(a._signal_active(signal,load))
        for shift in (-1,1):self.assertFalse(a._signal_active(signal,replace(load,start=load.start+timedelta(hours=shift),end=load.end+timedelta(hours=shift))))
        self.assertFalse(a._signal_active(replace(signal,issued_at=load.start+timedelta(seconds=1)),load))
        self.assertFalse(a._signal_active(replace(signal,truth='OBS'),load))
        self.assertFalse(a._signal_active(None,load))
    def test_previous_closed_block_uses_own_not_served_and_exact_curve(self):
        history=self.history();b=a._evening_budget(self.ref,history,a.approved_signal().valid_from)
        self.assertEqual(b['source_local_date'],'2025-01-02');self.assertEqual(len(b['parts']),4)
        exact=sum((F.from_float(self.ref.discharge.point(.75)[0]) for _ in history),F(0))
        self.assertEqual(F(b['estimated_dc_kwh_exact_binary']),exact)
        self.assertGreaterEqual(F.from_float(b['estimated_dc_kwh']),exact)
        self.assertGreaterEqual(F.from_float(b['floor_kwh']),2+exact)
    def test_no_second_cycle_or_charging_loss(self):
        b=a._evening_budget(self.ref,self.history(),a.approved_signal().valid_from)
        self.assertAlmostEqual(b['estimated_dc_kwh'],4*self.ref.discharge.point(.75)[0],places=12)
    def test_missing_duplicate_invalid_and_unsupported_stay_Q(self):
        hist=self.history();t=a.approved_signal().valid_from
        for h in ((),hist[:-1],hist+(hist[-1],),(replace(hist[0],base_kw=F(-1)),)+hist[1:]):
            b=a._evening_budget(self.ref,h,t);self.assertEqual(b['status'],'Q');self.assertIsNone(b['floor_kwh']);self.assertIsNone(b['estimated_dc_kwh'])
        b=a._evening_budget(self.ref,self.history(base=F(1,100000),hp=F(0)),t)
        self.assertEqual(b['status'],'Q');self.assertIn('CURVE',b['reason'])
    def test_known_zero_demand_is_not_missing(self):
        b=a._evening_budget(self.ref,self.history(base=F(0),hp=F(0)),a.approved_signal().valid_from)
        self.assertEqual(b['estimated_dc_kwh'],0.);self.assertEqual(b['floor_kwh'],2.)
    def test_future_block_does_not_replace_last_closed_history(self):
        h=self.history();t=a.approved_signal().valid_from
        future=tuple(replace(x,start=x.start+timedelta(days=1),end=x.end+timedelta(days=1),hp_kw=F(100)) for x in h)
        self.assertEqual(a._evening_budget(self.ref,h,t),a._evening_budget(self.ref,h+future,t))
    def test_next_evening_selected_only_once_closed(self):
        h=self.history();t=datetime(2025,1,3,20,tzinfo=timezone.utc)
        self.assertEqual(a._evening_budget(self.ref,h,t)['source_local_date'],'2025-01-02')
        self.assertEqual(a._evening_budget(self.ref,h,t+timedelta(hours=1))['status'],'Q')
    def test_event_charging_disabled_and_extra_floor_preserved(self):
        pair=self.pair();self.assertEqual(len(pair['signal_selection']),1)
        note=pair['signal_selection'][0]
        for name,result in pair['shared_budget'].items():
            selected=[r for r in result['controller_records']['reserved'] if r['load'].start==a.approved_signal().valid_from];self.assertEqual(len(selected),1)
            r=selected[0];n=note['households'][name]
            self.assertEqual(r['native']['admitted_charge_ac_kwh'],0.)
            self.assertGreater(r['native']['delivered_discharge_ac_kwh'],0.)
            self.assertGreaterEqual(r['native']['x_end_kwh'],n['budget']['floor_kwh'])
            self.assertLessEqual(r['native']['delivered_discharge_ac_kwh'],min(1.5,float(r['load'].base_kw+r['load'].hp_kw)))
            self.assertIn(a.ONE_SIGNAL,result['case'].scenario_reference)
    def test_unknown_history_no_extra_discharge_no_charge(self):
        with patch.object(a,'_evening_budget',return_value={'status':'Q','reason':'MISSING','estimated_dc_kwh':None,'floor_kwh':None}):pair=self.pair()
        for result in pair['shared_budget'].values():
            r=next(r for r in result['controller_records']['reserved'] if r['load'].start==a.approved_signal().valid_from)
            self.assertEqual(r['native']['admitted_charge_ac_kwh'],0.);self.assertEqual(r['native']['delivered_discharge_ac_kwh'],0.)
    def test_insufficient_stock_above_evening_floor_does_not_force_it(self):
        with patch.object(a,'_evening_budget',return_value={'status':'SCN','reason':None,'estimated_dc_kwh':20.,'floor_kwh':22.}):pair=self.pair()
        for n in pair['signal_selection'][0]['households'].values():
            self.assertFalse(n['extra_eligible']);self.assertEqual(n['actual_discharge_ac_kwh'],0.)
    def test_event_in_first24_hours_retains_hold(self):
        pair=self.pair(start=datetime(2025,1,3,tzinfo=timezone.utc),hours=24)
        for r in pair['shared_budget'].values():
            self.assertTrue(all(x['warmup_hold'] and not x['charge_kw'] and not x['discharge_kw'] for x in r['controller_records']['reserved']))
    def test_no_event_preserves_old_cases_and_no_early_difference(self):
        base=self.pair(signal=None);new=self.pair()
        for name in ('HH1','HH2'):
            b=base['shared_budget'][name];n=new['shared_budget'][name]
            self.assertNotEqual(b['case'].content_sha256,n['case'].content_sha256)
            before=[r for r in b['controller_records']['reserved'] if r['load'].end<=a.approved_signal().valid_from]
            after=[r for r in n['controller_records']['reserved'] if r['load'].end<=a.approved_signal().valid_from]
            self.assertEqual(before,after)
    def test_unknown_or_wrong_base_signal_case_rejected(self):
        for signal in ('OTHER',):
            with self.assertRaises(ValueError):self.pair(signal=signal)
        with self.assertRaises(ValueError):a.shared_budget_pair(*inputs(),household_policy=a.EVENING_PRIORITY,profile_case=a.MIXED_HP_BASE,signal_case=a.ONE_SIGNAL)
        with self.assertRaises(ValueError):a.shared_budget_pair(*inputs(),household_policy=a.WINTER_PRIORITY,signal_case=a.ONE_SIGNAL)

if __name__=='__main__':unittest.main()
