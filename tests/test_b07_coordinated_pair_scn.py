"""Two explicit SCN households; native physics unchanged, no feeder claim."""
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
import unittest
from modules.B12 import battery_reservation_reference as a

def inputs(start=datetime(2025,1,1,tzinfo=timezone.utc),hours=96):
    loads=tuple(a.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),F(1),F(0)) for i in range(hours))
    prices=tuple(F(1 if i%24<4 or 10<=i%24<16 else 100) for i in range(hours))
    return loads,prices

class CoordinatedPairTests(unittest.TestCase):
    def test_first_grant_HH1_alternation_and_native_skip(self):
        pair=a.coordinated_pair(*inputs());grants=[r for r in pair['selection'] if r['selected']]
        self.assertEqual(grants[0]['selected'],'HH1')
        for row in pair['selection']:
            eligible=row['physically_chargeable'];selected=row['selected']
            if not eligible:self.assertIsNone(selected);self.assertEqual(row['turn_before'],row['turn_after'])
            else:
                self.assertIn(selected,eligible)
                expected=row['turn_before'] if row['turn_before'] in eligible else next(iter(eligible))
                self.assertEqual(selected,expected)
                self.assertNotEqual(row['turn_after'],selected)
        self.assertTrue(any(len(r['physically_chargeable'])==1 for r in pair['selection']))
    def test_one_charger_shared_cap_reserve_no_export_DST(self):
        for start in (datetime(2025,3,29,tzinfo=timezone.utc),datetime(2025,10,25,tzinfo=timezone.utc)):
            pair=a.coordinated_pair(*inputs(start))
            for i in range(96):
                rows=[pair['coordinated'][n]['controller_records']['reserved'][i] for n in ('HH1','HH2')]
                self.assertLessEqual(sum(r['native']['admitted_charge_ac_kwh']>0 for r in rows),1)
                self.assertLessEqual(sum(r['native']['admitted_charge_ac_kwh'] for r in rows),pair['battery_charge_cap_kw'])
                for r in rows:
                    h=r['load'].start.astimezone(a.LOCAL).hour;n=r['native']
                    self.assertGreaterEqual(n['x_end_kwh'],2.);self.assertLessEqual(n['x_end_kwh'],10.)
                    self.assertLessEqual(n['delivered_discharge_ac_kwh'],min(1.5,float(r['load'].base_kw+r['load'].hp_kw)))
                    if r['charge_kw']:self.assertTrue(h<6 or 10<=h<16);self.assertLess(F(r['control_price_exact']),F(r['previous24_median_exact']))
                    if r['discharge_kw']:self.assertTrue(18<=h<22)
                    self.assertFalse(r['charge_kw'] and r['discharge_kw'])
            self.assertIsNone(pair['feeder_capacity_kw']);self.assertIsNone(pair['national_result'])
    def test_entity_identity_and_initial_state_are_explicit_and_distinct(self):
        pair=a.coordinated_pair(*inputs())
        for mode in ('independent','coordinated'):
            first=pair[mode]['HH1']['case'];second=pair[mode]['HH2']['case']
            self.assertNotEqual(first.identity.household_actor_id,second.identity.household_actor_id)
            self.assertNotEqual(first.identity.connection_id,second.identity.connection_id)
            self.assertNotEqual(first.content_sha256,second.content_sha256)
            for case in (first,second):
                self.assertEqual(case.actual_leg.initial_inventory_kwh,2.)
                self.assertEqual(case.actual_leg.agreement.initial_protected_kwh.value,2.)
    def test_native_audits_no_invented_state_activation_or_success(self):
        pair=a.coordinated_pair(*inputs())
        for mode in ('independent','coordinated'):
            for name,result in pair[mode].items():
                leg=result['audit']['legs']['reserved'];network=result['case'].identity.state_actor_id
                self.assertEqual(leg['physical_status'],'PASS_SCN');self.assertEqual(leg['allocation_status'],'PASS_SCN')
                self.assertNotEqual(leg['rights']['status'],'FAIL')
                self.assertTrue(all(r['actors'][network]['available_before_kwh']==2. for r in leg['rights']['intervals']))
                self.assertFalse(result['actual_activation']);self.assertIsNone(result['ROI'])
    def test_no_charge_without_price_history_or_cheap_price(self):
        loads,_=inputs();pair=a.coordinated_pair(loads,(F(10),)*len(loads))
        self.assertTrue(all(r['selected'] is None for r in pair['selection']))
        for result in pair['coordinated'].values():
            rows=result['controller_records']['reserved']
            self.assertTrue(all(r['charge_kw']==r['discharge_kw']==0 for r in rows))
            self.assertTrue(all(r['warmup_hold'] for r in rows[:24]))
    def test_future_prices_do_not_change_past_selection(self):
        loads,prices=inputs();left=a.coordinated_pair(loads,prices)
        right=a.coordinated_pair(loads,prices[:60]+(F(999),)*36)
        self.assertEqual(left['selection'][:60],right['selection'][:60])
        for name in ('HH1','HH2'):
            self.assertEqual(left['coordinated'][name]['controller_records']['reserved'][:60],right['coordinated'][name]['controller_records']['reserved'][:60])
    def test_independent_records_reproduce_source_baseline_exactly(self):
        pair=a.coordinated_pair(*inputs())
        for result in pair['independent'].values():
            self.assertEqual(result['controller_records'],pair['source_baseline']['controller_records'])
    def test_unknown_entity_or_unpaired_mode_rejected(self):
        loads,prices=inputs();ref,records=a.schedules(loads,prices,household_policy=a.EVENING_PRIORITY)
        for entity,mode in [('HH3','COORDINATED'),('HH1',None),(None,'INDEPENDENT')]:
            with self.assertRaises(ValueError):a.build_case(ref,records,household_policy=a.EVENING_PRIORITY,entity_id=entity,coordination=mode)

if __name__=='__main__':unittest.main()
