"""Explicit existing-column selection, per-entity load and unchanged physics."""
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
import unittest
from modules.B12 import battery_reservation_reference as a

def inputs(month=1,hours=72,base=F(1,4),hp=F(1)):
    t=datetime(2025,month,1,tzinfo=timezone.utc)
    loads=tuple(a.LoadHour(t+timedelta(hours=i),t+timedelta(hours=i+1),base,hp) for i in range(hours))
    return loads,tuple(F(1 if i%24<6 or 10<=i%24<12 else 20) for i in range(hours))

class MixedHouseholdTests(unittest.TestCase):
    def pair(self,policy=a.EVENING_PRIORITY,**kwargs):
        return a.shared_budget_pair(*inputs(**kwargs),household_policy=policy,profile_case=a.MIXED_HP_BASE)
    def test_actual_and_counterfactual_loads_are_entity_specific(self):
        loads,_=inputs();pair=self.pair()
        for name,result in pair['shared_budget'].items():
            for leg in ('household_only','reserved'):
                rs=result['controller_records'][leg]
                self.assertEqual(len(rs),len(loads))
                for source,row in zip(loads,rs):
                    self.assertEqual(row['load'].base_kw,source.base_kw)
                    self.assertEqual(row['load'].hp_kw,source.hp_kw if name=='HH1' else F(0))
                    self.assertEqual((row['load'].start,row['load'].end),(source.start,source.end))
    def test_own_discharge_is_not_cloned_from_HH1(self):
        pair=self.pair()
        hh1=pair['shared_budget']['HH1']['controller_records']['reserved'];hh2=pair['shared_budget']['HH2']['controller_records']['reserved']
        self.assertTrue(any(x['native']['delivered_discharge_ac_kwh']>y['native']['delivered_discharge_ac_kwh'] for x,y in zip(hh1,hh2)))
        self.assertTrue(any(r['native']['delivered_discharge_ac_kwh']>0 for r in hh2))
        self.assertTrue(all(r['native']['delivered_discharge_ac_kwh']<=.25 for r in hh2))
    def test_zero_actual_HH2_load_does_not_export(self):
        pair=self.pair(base=F(0),hp=F(1))
        self.assertTrue(all(r['native']['delivered_discharge_ac_kwh']==0 for r in pair['shared_budget']['HH2']['controller_records']['reserved']))
    def test_source_assignment_bound_to_case_identity(self):
        mixed=self.pair(hp=F(0));plain=a.shared_budget_pair(*inputs(hp=F(0)))
        for name,result in mixed['shared_budget'].items():
            self.assertIn(a.MIXED_HP_BASE,result['case'].scenario_reference)
            self.assertNotEqual(result['case'].content_sha256,plain['shared_budget'][name]['case'].content_sha256)
            p=result['profile_provenance'];self.assertEqual(p['entity_id'],name)
            self.assertEqual(len(p['selected_columns']),2 if name=='HH1' else 1)
            self.assertNotIn('A1_reference',result)
    def test_default_identical_profiles_unchanged(self):
        first=a.shared_budget_pair(*inputs());second=a.shared_budget_pair(*inputs(),profile_case=a.IDENTICAL_HP)
        for name in ('HH1','HH2'):
            self.assertEqual(first['shared_budget'][name]['case'].content_sha256,second['shared_budget'][name]['case'].content_sha256)
            self.assertEqual(first['shared_budget'][name]['controller_records'],second['shared_budget'][name]['controller_records'])
    def test_reserve_domain_cap_and_no_simultaneous_power(self):
        for policy in (a.EVENING_PRIORITY,a.WINTER_PRIORITY):
            pair=self.pair(policy);ref=pair['source_baseline']['case'].executor;cap=F.from_float(pair['battery_charge_cap_kw'])
            for i in range(72):
                actual=[]
                for name,result in pair['shared_budget'].items():
                    r=result['controller_records']['reserved'][i];n=r['native'];actual.append(F.from_float(n['admitted_charge_ac_kwh']))
                    self.assertGreaterEqual(n['x_end_kwh'],2.);self.assertLessEqual(n['x_end_kwh'],10.)
                    self.assertLessEqual(n['delivered_discharge_ac_kwh'],min(1.5,float(r['load'].base_kw+r['load'].hp_kw)))
                    self.assertFalse(r['charge_kw'] and r['discharge_kw'])
                    if n['admitted_charge_dc_kwh']:self.assertGreaterEqual(n['admitted_charge_dc_kwh'],ref.charge.lower)
                    self.assertEqual(result['audit']['legs']['reserved']['physical_status'],'PASS_SCN')
                self.assertLessEqual(sum(actual,F(0)),cap)
    def test_unknown_profile_assignment_is_rejected(self):
        with self.assertRaises(ValueError):a.shared_budget_pair(*inputs(),profile_case='SCALED_HOUSE')
    def test_explicit_hour_load_map_rejects_missing_extra_and_misaligned(self):
        loads,prices=inputs();ref=a.reference(household_policy=a.EVENING_PRIORITY);load=loads[0]
        bad=[{'HH1':load},{'HH1':load,'HH2':load,'HH3':load},{'HH1':load,'HH2':loads[1]}, {'HH1':load,'HH2':a.LoadHour(load.start,load.end,F(-1),F(0))}]
        for mapping in bad:
            with self.assertRaises(ValueError):a._shared_hour(ref,load,prices[0],F(10),{'HH1':2.,'HH2':2.},household_loads=mapping)
    def test_warmup_and_causal_history_remain_common(self):
        loads,prices=inputs();changed=prices[:60]+tuple(F(999) for _ in prices[60:])
        first=a.shared_budget_pair(loads,prices,profile_case=a.MIXED_HP_BASE)
        second=a.shared_budget_pair(loads,changed,profile_case=a.MIXED_HP_BASE)
        for name in ('HH1','HH2'):
            before=first['shared_budget'][name]['controller_records']['reserved'];after=second['shared_budget'][name]['controller_records']['reserved']
            self.assertEqual(before[:60],after[:60])
            self.assertTrue(all(r['warmup_hold'] and not r['charge_kw'] and not r['discharge_kw'] for r in before[:24]))
            self.assertEqual([r['previous24_median_exact'] for r in before], [r['previous24_median_exact'] for r in first['shared_budget']['HH1']['controller_records']['reserved']])
    def test_winter_extension_reaches_both_households_with_actual_load(self):
        old=self.pair();winter=self.pair(a.WINTER_PRIORITY)
        for name in ('HH1','HH2'):
            before=old['shared_budget'][name]['controller_records']['reserved'];after=winter['shared_budget'][name]['controller_records']['reserved']
            selected=[i for i,r in enumerate(after) if not r['warmup_hold'] and r['load'].start.astimezone(a.LOCAL).hour==15]
            self.assertTrue(any(after[i]['native']['delivered_discharge_ac_kwh']>0 for i in selected))
            self.assertTrue(all(before[i]['native']['delivered_discharge_ac_kwh']==0 and after[i]['native']['admitted_charge_ac_kwh']==0 for i in selected))

if __name__=='__main__':unittest.main()
