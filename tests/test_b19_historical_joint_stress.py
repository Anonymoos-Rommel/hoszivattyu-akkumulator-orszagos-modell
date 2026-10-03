"""Synthetic arithmetic/adversarial tests; genuine source replay is separate."""
import copy
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D, Inexact, localcontext
from fractions import Fraction as F
import hashlib
import inspect
import io
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from modules.B19 import historical_joint_stress as joint

START = datetime(2025, 1, 1, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)
QUARTER = timedelta(minutes=15)
ROOT = Path(__file__).resolve().parents[1]


def exact(record):
    return F(int(record['numerator']), int(record['denominator']))


def grid(quarters, *, start=START):
    result = []
    for i, (load, generation) in enumerate(quarters):
        load, generation = D(str(load)), D(str(generation))
        result.append(SimpleNamespace(
            start_utc=start + i * QUARTER, end_utc=start + (i + 1) * QUARTER,
            actual_load_mw=load, injection_mw=max(generation, D(0)),
            source_withdrawal_mw=max(-generation, D(0)), signed_generation_mw=generation,
            source_reference_residual_mw=load-generation, evidence_status='DER',
            evidence_tier='E2_PROVISIONAL_BASE', model_use_status='HISTORICAL_SOURCE_REFERENCE_ONLY'))
    return result


def weather(temperatures, *, start=START):
    return [(start + i * HOUR, start + (i + 1) * HOUR, F(str(t)), 'HIST')
            for i, t in enumerate(temperatures)]


def summarize(quarters, temperatures, hours, *, start=START):
    return joint._summarize(grid(quarters, start=start), weather(temperatures, start=start),
                            window_hours=hours, start=start, end=start + len(temperatures) * HOUR)


def weather_fixture(temperatures):
    n = len(temperatures)
    c = {'rows': n, 'start_utc': START.isoformat(), 'end_utc': (START+n*HOUR).isoformat(),
         'station_id': '44527', 'history_source_id': 'HIST', 'recent_source_id': 'RECENT',
         'recent_endpoint_utc': (START+n*HOUR).isoformat()}
    rows = [{'station_id':'44527', 'interval_start_utc':(START+i*HOUR).isoformat(),
             'source_endpoint_utc':(START+(i+1)*HOUR).isoformat(), 'ta_C':str(t),
             'source_id':'RECENT' if i==n-1 else 'HIST'} for i,t in enumerate(temperatures)]
    return rows,c


class JointArithmeticTests(unittest.TestCase):
    def test_four_quarters_integrate_before_join(self):
        r = summarize([(4,2),(8,3),(12,4),(16,5)], [-2], 1)
        w = r['criteria']['HIGHEST_MEAN_SOURCE_LOAD']['windows'][0]
        self.assertEqual(exact(w['energy_mwh']['load_mwh']),10)
        self.assertEqual(exact(w['mean_power_mw']['load_mw']),10)
        self.assertEqual(exact(w['mean_power_mw']['signed_generation_mw']),F(7,2))
        self.assertEqual(exact(w['mean_temperature_c']),-2)
        self.assertIn('not quarter-hour',w['temporal_meaning'])

    def test_negative_generation_withdrawal_preserved_once(self):
        r = summarize([(10,-2)]*4, [1], 1)
        e = r['annual_energy_mwh']
        self.assertEqual(exact(e['injection_mwh']),0)
        self.assertEqual(exact(e['source_withdrawal_mwh']),2)
        self.assertEqual(exact(e['signed_generation_mwh']),-2)
        self.assertEqual(exact(e['source_reference_residual_mwh']),12)

    def test_negative_residual_not_clipped(self):
        r = summarize([(1,3)]*8, [1,2], 1)
        selected = r['criteria']['HIGHEST_MEAN_SOURCE_REFERENCE_RESIDUAL']
        self.assertEqual(exact(selected['mean_score']),-2)
        self.assertEqual(selected['ties'],2)
        self.assertEqual(exact(r['annual_energy_mwh']['source_reference_residual_mwh']),-4)

    def test_all_ties_retained_in_chronological_order(self):
        r = summarize([(2,1)]*20, [-1]*5, 2)
        for choice in r['criteria'].values():
            self.assertEqual(choice['ties'],4)
            self.assertEqual([w['start_utc'] for w in choice['windows']],
                             [(START+i*HOUR).isoformat() for i in range(4)])

    def test_each_selector_keeps_its_own_coincident_values(self):
        q = [(4,3)]*4 + [(8,7)]*4 + [(6,0)]*4
        r = summarize(q,[-10,1,5],1)
        cold = r['criteria']['COLDEST_MEAN_BUDAPEST_TEMPERATURE']['windows'][0]
        highload = r['criteria']['HIGHEST_MEAN_SOURCE_LOAD']['windows'][0]
        highres = r['criteria']['HIGHEST_MEAN_SOURCE_REFERENCE_RESIDUAL']['windows'][0]
        self.assertEqual(exact(cold['mean_power_mw']['load_mw']),4)
        self.assertEqual(exact(highload['mean_temperature_c']),1)
        self.assertEqual(exact(highres['mean_temperature_c']),5)
        self.assertEqual(len({w['start_utc'] for w in (cold,highload,highres)}),3)

    def test_windows_do_not_wrap_pad_or_pick_partial_final_window(self):
        r = summarize([(1,0)]*16,[4,3,2,1],3)
        self.assertEqual(r['windows_evaluated'],2)
        c = r['criteria']['COLDEST_MEAN_BUDAPEST_TEMPERATURE']['windows'][0]
        self.assertEqual(c['start_utc'],(START+HOUR).isoformat())
        self.assertEqual(c['end_utc_exclusive'],(START+4*HOUR).isoformat())
        self.assertEqual(exact(c['mean_temperature_c']),2)

    def test_full_window_reconciles_to_annual_totals(self):
        r = summarize([(2,3)]*4+[(4,-1)]*4,[1,3],2)
        for choice in r['criteria'].values():
            self.assertEqual(choice['ties'],1)
            self.assertEqual(choice['windows'][0]['energy_mwh'],r['annual_energy_mwh'])
        self.assertEqual(exact(r['annual_energy_mwh']['load_mwh'])-
                         exact(r['annual_energy_mwh']['signed_generation_mwh']),
                         exact(r['annual_energy_mwh']['source_reference_residual_mwh']))

    def test_random_small_panels_match_independent_brute_force(self):
        rng=random.Random(48)
        for n in range(2,8):
            q=[(rng.randint(0,100),rng.randint(-5,120)) for _ in range(4*n)]
            t=[F(rng.randint(-100,100),10) for _ in range(n)]
            hourly=[(F(sum(a for a,b in q[4*i:4*i+4]),4),
                     F(sum(b for a,b in q[4*i:4*i+4]),4)) for i in range(n)]
            for k in range(1,n+1):
                r=summarize(q,t,k)
                for name,(field,direction) in joint.CRITERIA.items():
                    values=[]
                    for i in range(n-k+1):
                        value=(sum(t[i:i+k]) if field=='temperature_sum_c' else
                               sum(a for a,b in hourly[i:i+k]) if field=='load_mwh' else
                               sum(a-b for a,b in hourly[i:i+k]))/k
                        values.append(value)
                    target=(min if direction=='min' else max)(values)
                    expected=[(START+i*HOUR).isoformat() for i,v in enumerate(values) if v==target]
                    with self.subTest(n=n,k=k,name=name):
                        self.assertEqual(exact(r['criteria'][name]['mean_score']),target)
                        self.assertEqual([w['start_utc'] for w in r['criteria'][name]['windows']],expected)

    def test_fractional_ties_not_lost_to_sliding_float_drift(self):
        r=summarize([(1,0)]*16,['0.1','0.2','0.1','0.2'],2)
        self.assertEqual(r['criteria']['COLDEST_MEAN_BUDAPEST_TEMPERATURE']['ties'],3)
        self.assertEqual(exact(r['criteria']['COLDEST_MEAN_BUDAPEST_TEMPERATURE']['mean_score']),F(3,20))

    def test_decimal_context_and_inexact_trap_cannot_change_summary(self):
        q=[(2,1)]*12;t=['0.1','0.2','0.1']
        expected=summarize(q,t,3)
        with localcontext() as c:
            c.prec=1;c.traps[Inexact]=True
            actual=summarize(q,t,3)
        self.assertEqual(actual,expected)

    def test_source_weather_hours_on_boundary_remain_visible(self):
        w=weather([1,2,3]);w[-1]=(*w[-1][:3],'RECENT')
        r=joint._summarize(grid([(1,0)]*12),w,window_hours=2,start=START,end=START+3*HOUR)
        tied=r['criteria']['HIGHEST_MEAN_SOURCE_LOAD']['windows']
        self.assertEqual(tied[0]['weather_source_hours'],{'HIST':2})
        self.assertEqual(tied[1]['weather_source_hours'],{'HIST':1,'RECENT':1})

    def test_dst_day_is_physical_utc_hours(self):
        for day in ((2025,3,30),(2025,10,26)):
            start=datetime(*day,tzinfo=timezone.utc)
            r=summarize([(1,0)]*96,list(range(24)),24,start=start)
            self.assertEqual(r['hours'],24)
            self.assertEqual(r['quarter_hour_intervals'],96)
            self.assertEqual(r['windows_evaluated'],1)


class FailClosedTests(unittest.TestCase):
    def setUp(self):
        self.g=grid([(10,5)]*8);self.w=weather([1,2])

    def run_rows(self,g=None,w=None,k=1):
        return joint._summarize(self.g if g is None else g,self.w if w is None else w,
                                window_hours=k,start=START,end=START+2*HOUR)

    def test_invalid_or_missing_window_definition(self):
        for k in (None,True,0,-1,1.0,'1',3):
            with self.subTest(k=k),self.assertRaises(ValueError):self.run_rows(k=k)
        self.assertIs(inspect.signature(joint.calculate_reference).parameters['window_hours'].default,inspect.Parameter.empty)

    def test_missing_duplicate_extra_shifted_quarter_rejected(self):
        for bad in (self.g[:-1],self.g[:3]+self.g[2:],self.g+[self.g[-1]]):
            with self.assertRaises(ValueError):self.run_rows(g=bad)
        for field in ('start_utc','end_utc'):
            bad=copy.deepcopy(self.g);setattr(bad[-1],field,getattr(bad[-1],field)+QUARTER)
            with self.assertRaises(ValueError):self.run_rows(g=bad)

    def test_wrong_interval_duration_rejected(self):
        bad=copy.deepcopy(self.g);bad[0].end_utc+=QUARTER
        with self.assertRaises(ValueError):self.run_rows(g=bad)

    def test_source_raises_after_last_yield_propagates(self):
        def fail():
            yield from self.g
            raise ValueError('final original recovery validation failed')
        with self.assertRaisesRegex(ValueError,'final original'):self.run_rows(g=fail())

    def test_last_row_bad_balance_prevents_any_result(self):
        self.g[-1].source_reference_residual_mw=D('99')
        with self.assertRaisesRegex(ValueError,'balance'):self.run_rows()

    def test_source_sign_violations_rejected(self):
        for field in ('actual_load_mw','injection_mw','source_withdrawal_mw'):
            bad=copy.deepcopy(self.g);setattr(bad[0],field,D('-1'))
            with self.subTest(field=field),self.assertRaises(ValueError):self.run_rows(g=bad)

    def test_nonfinite_or_binary_float_source_power_rejected(self):
        for value in (D('NaN'),D('Infinity'),D('-Infinity'),D('sNaN'),True,1.0,None):
            bad=copy.deepcopy(self.g);bad[0].actual_load_mw=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.run_rows(g=bad)

    def test_source_evidence_promotion_rejected(self):
        for field,value in (('evidence_status','OBS'),('evidence_tier','E1'),('model_use_status','PROGRAMME_RESULT')):
            bad=copy.deepcopy(self.g);setattr(bad[0],field,value)
            with self.subTest(field=field),self.assertRaises(ValueError):self.run_rows(g=bad)

    def test_weather_incomplete_duplicate_extra_or_shifted_rejected(self):
        for bad in (self.w[:-1],self.w+[self.w[-1]],[self.w[0],self.w[0]]):
            with self.assertRaises(ValueError):self.run_rows(w=bad)
        bad=list(self.w);bad[0]=(START+HOUR,START+2*HOUR,*bad[0][2:])
        with self.assertRaises(ValueError):self.run_rows(w=bad)

    def test_utc_and_hour_boundaries_required(self):
        for start,end in ((START.replace(tzinfo=None),START+HOUR),
                          (START+QUARTER,START+HOUR+QUARTER),
                          (START,START),(START,START+QUARTER)):
            with self.assertRaises(ValueError):joint._duration(1,start=start,end=end)
        bad=copy.deepcopy(self.g);bad[0].start_utc=bad[0].start_utc.replace(tzinfo=timezone(timedelta(hours=1)))
        with self.assertRaises(ValueError):self.run_rows(g=bad)


class WeatherContractTests(unittest.TestCase):
    def setUp(self):self.rows,self.contract=weather_fixture(['-1.2','3.4'])

    def test_precise_preceding_hour_endpoint_and_recent_source(self):
        r=joint._weather_rows(self.rows,self.contract)
        self.assertEqual(r[0],(START,START+HOUR,F(-6,5),'HIST'))
        self.assertEqual(r[-1][-1],'RECENT')

    def test_missing_sentinel_and_bad_temperatures_rejected(self):
        for x in ('','-999','NaN','Infinity','abc',True,1.1):
            rows=copy.deepcopy(self.rows);rows[0]['ta_C']=x
            with self.subTest(x=x),self.assertRaises(ValueError):joint._weather_rows(rows,self.contract)

    def test_station_source_and_boundary_substitution_rejected(self):
        for key,value in (('station_id','other'),('source_id','RECENT'),
                          ('interval_start_utc',(START+HOUR).isoformat()),
                          ('source_endpoint_utc',START.isoformat())):
            rows=copy.deepcopy(self.rows);rows[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):joint._weather_rows(rows,self.contract)

    def test_extra_missing_and_wrong_count_rejected(self):
        for rows in (self.rows[:-1],self.rows+[self.rows[-1]]):
            with self.assertRaises(ValueError):joint._weather_rows(rows,self.contract)
        c=dict(self.contract,rows=3)
        with self.assertRaises(ValueError):joint._weather_rows(self.rows,c)

    def test_weather_hash_identity_and_exact_parse(self):
        output=io.StringIO();writer=csv.DictWriter(output,fieldnames=list(self.rows[0]));writer.writeheader();writer.writerows(self.rows);raw=output.getvalue().encode()
        c=dict(self.contract,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'weather.csv';p.write_bytes(raw)
            self.assertEqual(joint._weather(p,c),joint._weather_rows(self.rows,c))
            p.write_bytes(raw+b'\n')
            with self.assertRaisesRegex(ValueError,'bytes/hash'):joint._weather(p,c)


class PublicContractTests(unittest.TestCase):
    def test_source_contract_retains_native_boundaries(self):
        m=joint._contract()
        self.assertEqual(m['weather']['rows'],8760)
        self.assertEqual(m['weather']['history_rows'],8759)
        self.assertEqual(m['weather']['recent_rows'],1)
        self.assertIsNone(m['window_hours_default'])
        self.assertIsNone(m['national_weather_weights'])
        self.assertIsNone(m['probabilities'])
        self.assertIn('Q-B08-001',m['validation_debt']);self.assertIn('Q-B09-001',m['validation_debt'])
        self.assertIn('no national meteorological',m['spatial_boundary'])

    def test_authority_hash_change_rejected(self):
        manifest=json.loads(joint.MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'manifest.json';p.write_bytes(joint.MANIFEST.read_bytes())
            for relative in manifest['authority_sha256']:
                target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('changed authority')
            with patch.object(joint,'ROOT',root),patch.object(joint,'MANIFEST',p),self.assertRaisesRegex(ValueError,'authority changed'):joint._contract()

    def test_silent_policy_or_national_weather_default_rejected(self):
        for key,value in (('window_hours_default',72),('national_weather_weights',{}),('probabilities',{}),('station_id','OTHER')):
            m=json.loads(joint.MANIFEST.read_text());m[key]=value
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'manifest.json';p.write_text(json.dumps(m))
                with self.subTest(key=key),patch.object(joint,'MANIFEST',p),self.assertRaises(ValueError):joint._contract()

    def test_source_semantics_debt_and_reuse_metadata_cannot_silently_change(self):
        for key,value in (('source_evidence',{'load':'OBS'}),('validation_debt',[]),
                          ('excluded_claims',[]),('spatial_boundary','National weather'),
                          ('selection_interpretation','Joint probability model')):
            m=json.loads(joint.MANIFEST.read_text());m[key]=value
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'manifest.json';p.write_text(json.dumps(m,indent=2)+'\n')
                with self.subTest(key=key),patch.object(joint,'MANIFEST',p),self.assertRaisesRegex(ValueError,'manifest identity'):
                    joint._contract()

    def test_public_api_checks_window_before_reading_inputs(self):
        with patch.object(joint,'_contract',side_effect=AssertionError('should not read')):
            with self.assertRaises(ValueError):joint.calculate_reference({}, {}, weather_path='absent',window_hours=0)

    def test_result_is_json_safe_and_has_no_feasibility_promotion(self):
        m=joint._contract();w=weather([1,2]);g=grid([(10,5)]*8)
        with patch.object(joint,'_contract',return_value=m),patch.object(joint,'_weather',return_value=w),patch.object(joint.historical,'START',START),patch.object(joint.historical,'END',START+2*HOUR),patch.object(joint.historical,'iter_historical_source_balance',return_value=iter(g)):
            r=joint.calculate_reference({}, {}, weather_path='synthetic',window_hours=1)
        self.assertEqual(r['evidence_status'],'DER');self.assertEqual(r['evidence_tier'],'E2_PROVISIONAL_BASE')
        for key in ('probabilities','national_feasibility_verdict'):self.assertIsNone(r[key])
        self.assertIs(r['policy_defaults_selected'],False);self.assertIs(r['originals_republished'],False)
        self.assertEqual(json.loads(json.dumps(r,allow_nan=False)),r)
        self.assertIn('not a demonstration',r['selection_interpretation'])
        self.assertTrue(any('imports' in x for x in r['excluded_claims']))

    def test_cli_requires_explicit_paths_and_duration(self):
        run=subprocess.run([sys.executable,'-m','modules.B19.historical_joint_stress'],cwd=ROOT,capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('--window-hours',run.stderr);self.assertIn('--paths-json',run.stderr)


if __name__=='__main__':unittest.main()
