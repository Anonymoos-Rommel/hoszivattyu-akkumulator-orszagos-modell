"""Explicit synthetic witnesses; never substitutes for the missing real prices."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
from pathlib import Path
import unittest
import json
from unittest.mock import patch
from decimal import Decimal,localcontext,ROUND_DOWN
from modules.B04 import wholesale_reference as wholesale
from modules.B12 import battery_reservation_reference as annual
from modules.B07 import discharge_equivalent_reference as native
from modules.B07 import shared_use_schedule_contract as shared

def fixture(start=datetime(2025,1,1,tzinfo=timezone.utc),hours=96):
    loads=tuple(annual.LoadHour(start+timedelta(hours=i),start+timedelta(hours=i+1),F(1,4),F(1,2)) for i in range(hours))
    prices=tuple(F(10 if (i%24<6 or 10<=i%24<16) else 80) for i in range(hours))
    return loads,prices

class AnnualReservationTests(unittest.TestCase):
    def real_prefix_case(self):
        data=json.loads((annual.ROOT/'data/fixtures/b07_real_price_prefix_384.json').read_text(encoding='utf-8'))
        loads,_,_=annual.load_profile()
        ref,records=annual.schedules(loads[:384],tuple(F(p) for p in data['prices_EUR_per_MWh_exact']))
        return annual.build_case(ref,records)
    def test_real_prefix_active_roundoff_then_idle_and_charge(self):
        case=self.real_prefix_case();out=shared.evaluate_shared_use(case)
        rights=out['legs']['reserved']['rights']
        self.assertNotEqual(rights['status'],'FAIL')
        fixes=rights['numerical_ledger_reconciliations']
        self.assertTrue(fixes)
        for fix in fixes:
            self.assertLess(fix['raw_after_kwh'],0.)
            self.assertLessEqual(-fix['raw_after_kwh'],fix['arithmetic_bound_kwh'])
            self.assertLessEqual(-fix['raw_after_kwh'],fix['active_flow_allowance_kwh'])
            self.assertEqual(fix['reconciled_after_kwh'],0.)
            row=out['legs']['reserved']['rows'][int(fix['interval_id'][1:])]
            self.assertGreater(row['inventory_credit_kwh']+row['inventory_debit_kwh'],0.)
        for i in (381,382,383):self.assertNotEqual(rights['intervals'][i]['status'],'FAIL')
        self.assertEqual(out['legs']['reserved']['rows'][380]['inventory_after_kwh'],annual.PROTECTED)
    def test_real_deficit_below_flow_allowance_above_ulp_bound_rejected(self):
        case=self.real_prefix_case();original=shared._rights
        def corrupted(c,leg,rows):
            if leg.leg_id=='reserved':
                a=rows[380]['allocation']['actors'][annual.H]['allocation']
                self.assertLess(1e-10,shared._allowance(c,a['inventory_debit_kwh']))
                a['inventory_debit_kwh']+=1e-10
            return original(c,leg,rows)
        with patch.object(shared,'_rights',side_effect=corrupted):out=shared.evaluate_shared_use(case)
        rights=out['legs']['reserved']['rights']
        self.assertEqual(rights['status'],'FAIL')
        self.assertIn(annual.H+':DRAW_BUDGET_EXCEEDED',rights['intervals'][381]['failures'])
        self.assertFalse(any(x['interval_id']=='h0380' for x in rights['numerical_ledger_reconciliations']))
    def test_transfers_do_not_acquire_roundoff_reconciliation(self):
        case=self.real_prefix_case();g=case.actual_leg.agreement
        # A zero-size transfer is still an explicit transfer contract; this
        # repair must not normalize transfer/replenishment accounting.
        g=replace(g,transfers=(shared.Transfer('unchanged',case.actual_leg.intervals[0].start,'FREE_TO_PROTECTED',0.),))
        g=replace(g,content_sha256=shared.content_digest(g))
        case=replace(case,actual_leg=replace(case.actual_leg,agreement=g))
        case=replace(case,content_sha256=shared.content_digest(case))
        out=shared.evaluate_shared_use(case)
        self.assertEqual(out['legs']['reserved']['rights']['numerical_ledger_reconciliations'],[])
        self.assertEqual(out['legs']['reserved']['rights']['status'],'FAIL')
    def test_default_idle_stays_Q(self):
        ref=annual.reference()
        r=native.run(ref,initial_dc_output_equiv_kwh=annual.INITIAL,commands=[dict(charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.)])
        self.assertIsNone(r['terminal_dc_output_equiv_kwh'])
        self.assertFalse(r['zero_cell_self_discharge_is_SCN_idealization'])
    def test_explicit_idle_only_preserves_inventory(self):
        r=native.run(annual.reference(),initial_dc_output_equiv_kwh=annual.INITIAL,
            commands=[dict(charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.)],idle_convention=native.SCN_IDLE_ZERO)
        self.assertEqual(r['terminal_dc_output_equiv_kwh'],annual.INITIAL)
        self.assertEqual(r['records'][0]['result']['idle_dc_drain_kwh'],0.)
        self.assertIsNone(r['actual_total_system_energy_kwh'])
    def test_unknown_idle_convention_rejected(self):
        with self.assertRaises(ValueError):native.run(annual.reference(),initial_dc_output_equiv_kwh=0.,commands=[],idle_convention='ZERO')
    def test_old_Q_cannot_be_repaired_by_flag(self):
        r=native.step(annual.reference(),native.Inventory(None,'Earlier unqualified state'),charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.,idle_convention=native.SCN_IDLE_ZERO)
        self.assertIsNone(r['x_end_kwh'])
    def test_warmup_and_negative_prices(self):
        loads,prices=fixture();prices=tuple(p-100 for p in prices)
        _,legs=annual.schedules(loads,prices)
        for rows in legs.values():
            self.assertTrue(all(x['warmup_hold'] and x['charge_kw']==x['discharge_kw']==0 for x in rows[:24]))
            self.assertTrue(any(x['charge_kw']>0 for x in rows[24:]))
    def test_previous24_excludes_current_and_future(self):
        loads,prices=fixture();_,left=annual.schedules(loads,prices)
        changed=prices[:60]+tuple(F(999) for _ in prices[60:]);_,right=annual.schedules(loads,changed)
        for key in left:
            self.assertEqual(left[key][:60],right[key][:60])
        rows=left['reserved']
        self.assertEqual(F(rows[24]['previous24_median_exact']),F(45))
    def test_equal_price_no_operation(self):
        loads,_=fixture();_,legs=annual.schedules(loads,(F(5),)*len(loads))
        self.assertTrue(all(x['charge_kw']==x['discharge_kw']==0 for x in legs['reserved']))
    def test_local_windows_and_DST(self):
        for date in [datetime(2025,3,29,tzinfo=timezone.utc),datetime(2025,10,25,tzinfo=timezone.utc)]:
            loads,prices=fixture(date);_,legs=annual.schedules(loads,prices)
            for rows in legs.values():
                for item in rows:
                    h=item['load'].start.astimezone(annual.LOCAL).hour
                    if item['charge_kw']:self.assertTrue(h<6 or 10<=h<16)
                    if item['discharge_kw']:self.assertTrue(16<=h<22)
                    self.assertFalse(item['charge_kw'] and item['discharge_kw'])
            self.assertEqual(len(legs['reserved']),96)
    def test_protected_pool_no_export_and_no_fake_terminal(self):
        loads,prices=fixture();ref,legs=annual.schedules(loads,prices)
        for item in legs['reserved']:
            self.assertGreaterEqual(item['native']['x_end_kwh'],annual.PROTECTED)
            self.assertLessEqual(item['native']['x_end_kwh'],ref.capacity_dc_output_equiv_kwh)
            self.assertLessEqual(item['native']['delivered_discharge_ac_kwh'],float(item['load'].base_kw+item['load'].hp_kw))
        self.assertNotEqual(legs['reserved'][-1]['native']['x_end_kwh'],annual.INITIAL)
    def test_shared_native_replay_and_standby_once(self):
        loads,prices=fixture();result=annual.evaluate(loads,prices)
        for key,leg in result['audit']['legs'].items():
            self.assertEqual(leg['physical_status'],'PASS_SCN')
            self.assertEqual(leg['allocation_status'],'PASS_SCN')
            self.assertNotEqual(leg['rights']['status'],'FAIL')
            idle=sum(x['charge_kw']==x['discharge_kw']==0 for x in result['controller_records'][key])
            self.assertAlmostEqual(leg['idle_ac']['ac_energy_debit_kwh'],idle*.00407)
            self.assertTrue(all(x['allocation']['actors'][annual.S]['allocation']['discharge_ac_kwh']==0 for x in leg['rows']))
        self.assertFalse(result['audit']['actual_execution_admitted'])
        self.assertIsNone(result['ROI'])
    def test_assumption_bound_to_case_and_comparison_hash(self):
        loads,prices=fixture();ref,records=annual.schedules(loads,prices);case=annual.build_case(ref,records)
        strict=replace(case,stored_standing_loss_condition='NOT_APPLICABLE_REFERENCE_IDLE_Q')
        self.assertNotEqual(shared.content_digest(case),shared.content_digest(strict))
        self.assertNotEqual(shared.comparison_digest(case),shared.comparison_digest(strict))
    def test_idle_cannot_introduce_new_stock_or_roundoff(self):
        loads,prices=fixture();ref,records=annual.schedules(loads,prices);case=annual.build_case(ref,records)
        original=shared._execute
        def corrupted(c,leg):
            rows,run=original(c,leg)
            if leg.leg_id=='reserved':
                # Introduce new inventory on the very first zero-flow interval;
                # opt-in must not waive or widen the zero-flow conservation gate.
                rows[0]['inventory_after_kwh']+=1e-12
            return rows,run
        with patch.object(shared,'_execute',side_effect=corrupted):out=shared.evaluate_shared_use(case)
        self.assertEqual(out['legs']['reserved']['rights']['status'],'FAIL')
        self.assertIn('POOL_CONSERVATION',out['legs']['reserved']['rights']['failures'])
    def test_missing_prices_and_bad_chronology(self):
        loads,prices=fixture()
        for bad in [prices[:-1],tuple(float(x) for x in prices)]:
            with self.assertRaises(ValueError):annual.schedules(loads,bad)
        with self.assertRaises(ValueError):annual.schedules(loads[:1]+loads,prices[:1]+prices)
    def test_real_annual_missing_source_fails_before_simulation(self):
        with patch.object(annual,'evaluate',side_effect=AssertionError('Must not simulate')):
            with self.assertRaises(ValueError):annual.annual({})
    def test_curve_decline_no_invented_duty_cycle(self):
        loads,prices=fixture();loads=tuple(replace(x,base_kw=F(1,1000),hp_kw=F(0)) for x in loads)
        _,legs=annual.schedules(loads,prices)
        self.assertTrue(all(x['discharge_kw']==0 for x in legs['reserved']))
    def test_A1_and_wholesale_are_separate_and_standby_once(self):
        # Explicit no-operation synthetic valuation witness over real timestamp
        # and load support. This does not claim source-price annual simulation.
        loads,_,_=annual.load_profile()
        price_rows=tuple(wholesale.WholesaleHour(x.start,x.end,'fixture','fixture','0.00',F(0),'SCN:TEST',False) for x in loads)
        priced=wholesale.WholesaleReference('utc2025',price_rows,{'reference_id':'SCN:TEST'}, {})
        rows=[{'load':x,'charge_kw':0.,'discharge_kw':0.,'control_price_exact':'0',
            'native':{'admitted_charge_ac_kwh':0.,'delivered_discharge_ac_kwh':0.}} for x in loads]
        leg={'initial_inventory_kwh':annual.INITIAL,'terminal_inventory_kwh':annual.INITIAL,
             'terminal_minus_initial_kwh':0.,'totals':{},'idle_ac':{'ac_energy_debit_kwh':8760*.00407},
             'rights':{'intervals':[{'actors':{annual.S:{'available_before_kwh':annual.PROTECTED}}} for _ in loads]}}
        case={'controller_records':{'household_only':rows,'reserved':rows},'wholesale_reference':priced,
            'audit':{'legs':{'household_only':leg,'reserved':leg},'response':{'foregone_household_discharge_kwh':0.,'actual_minus_baseline_terminal_kwh':0.}}}
        parameters=(annual.ROOT/'data/fixtures/b07_reservation_day_parameters.json').read_bytes()
        expected=annual.priced_summary(case,parameters)
        with localcontext() as ctx:
            ctx.prec=6;ctx.rounding=ROUND_DOWN
            changed=annual.priced_summary(case,parameters)
        self.assertEqual(expected,changed)
        self.assertEqual(F(expected['reserved']['standby_AC_kWh_exact']),F('35.6532'))
        self.assertEqual(expected['reserved']['wholesale_EUR_exact'],'0')
        self.assertGreater(Decimal(expected['reserved']['A1_total_gross_HUF']),0)
        self.assertEqual(expected['comparison']['A1_bill_difference_not_stock_adjusted_saving_HUF_exact'],'0')
        self.assertIsNone(expected['comparison']['ROI'])
        with self.assertRaises(ValueError):annual.priced_summary(case,parameters+b' ')

if __name__=='__main__':unittest.main()
