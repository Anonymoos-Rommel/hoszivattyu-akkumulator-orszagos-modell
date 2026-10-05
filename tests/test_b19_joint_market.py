"""Exact synthetic same-window comparisons and private-output adversaries."""
from copy import deepcopy
from dataclasses import replace
from decimal import localcontext, Inexact, Rounded
from fractions import Fraction as F
import inspect
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from modules.B04 import wholesale_reference as hu
from modules.B19 import historical_joint_market as market
from modules.B19 import historical_joint_stress as old
from modules.B19 import austrian_price_reference as at
from tests.test_b19_historical_joint_stress import START,HOUR,QUARTER,grid,weather,exact
from tests.test_b19_austrian_price_reference import label,cent_lexeme
from tools import materialize_b19_joint_market as materializer


def price_rows(values,zone,*,start=START):
    records=[]
    cls=hu.WholesaleHour if zone=='HU' else at.AustrianHour
    tz=hu.HU if zone=='HU' else at.AT
    for i,value in enumerate(values):
        a=start+i*HOUR;local=a.astimezone(tz).replace(tzinfo=None)
        value=F(str(value));cents=value*100
        assert cents.denominator==1
        records.append(cls(a,a+HOUR,label(local),label(local+HOUR),cent_lexeme(cents.numerator),
                           value,'SYNTHETIC_'+zone,local+HOUR!=(a+HOUR).astimezone(tz).replace(tzinfo=None)))
    return records


def summarize(q,t,hp,ap,k,*,start=START):
    return market._summarize(grid(q,start=start),weather(t,start=start),price_rows(hp,'HU',start=start),
            price_rows(ap,'AT',start=start),hu_source_id='SYNTHETIC_HU',at_source_id='SYNTHETIC_AT',
            window_hours=k,start=start,end=start+len(t)*HOUR)


class CoincidenceTests(unittest.TestCase):
    def test_each_selection_retains_actual_other_variables_and_signed_spread(self):
        q=[(4,3)]*4+[(8,7)]*4+[(6,-2)]*4+[(2,9)]*4+[(3,1)]*4
        r=summarize(q,[-10,1,5,3,2],[-2,5,-3,9,4],[1,2,1,-5,10],1)
        selected=[r['criteria'][key]['window_indices'] for key in market.CRITERIA]
        self.assertEqual(selected,[[0],[1],[2],[3],[4]])
        self.assertEqual(exact(r['windows'][0]['mean_power_mw']['load_mw']),4)
        self.assertEqual(exact(r['windows'][2]['energy_mwh']['signed_generation_mwh']),-2)
        self.assertEqual(exact(r['windows'][3]['energy_mwh']['source_reference_residual_mwh']),-7)
        self.assertEqual(exact(r['hourly_observations'][3]['signed_hu_minus_at_eur_per_mwh']),14)
        self.assertEqual(r['hourly_observations'][0]['HU']['source_price_lexeme'],'-2.00')
        self.assertEqual(r['hourly_observations'][0]['AT']['source_id'],'SYNTHETIC_AT')

    def test_existing_selectors_scores_ties_and_all_old_fields_unchanged(self):
        q=[(1,0)]*16;t=['0.1','0.2','0.1','0.2']
        result=summarize(q,t,[1,3,1,3],[2,2,2,2],2)
        original=old._summarize(grid(q),weather(t),window_hours=2,start=START,end=START+4*HOUR)
        self.assertEqual(result['annual_energy_mwh'],original['annual_energy_mwh'])
        self.assertEqual(result['annual_mean_temperature_c'],original['annual_mean_temperature_c'])
        for name in old.CRITERIA:
            a,b=result['criteria'][name],original['criteria'][name]
            self.assertEqual(a['mean_score'],b['mean_score']);self.assertEqual(a['ties'],b['ties'])
            for i,w in zip(a['window_indices'],b['windows']):
                self.assertEqual({key:result['windows'][i][key] for key in w},w)
        self.assertEqual(result['criteria']['HIGHEST_MEAN_HU_PRICE']['ties'],3)

    def test_ranks_negative_prices_counts_and_ranges(self):
        r=summarize([(2,1)]*16,[1,1,2,3],[-2,0,2,2],[0,0,1,3],2)
        w=r['windows'][0];rank=w['descriptive_same_domain_ranks']['temperature_sum_c']
        self.assertEqual(rank,{'lower_windows':0,'equal_windows_including_self':1,'higher_windows':2,
                               'ascending_rank_first':1,'ascending_rank_last':1})
        self.assertEqual(w['spread_hour_counts'],{'negative':1,'equal':1,'positive':0})
        self.assertEqual(exact(w['market_eur_per_mwh']['HU']['arithmetic_time_mean']),-1)
        self.assertEqual(exact(w['market_eur_per_mwh']['HU_MINUS_AT']['min_hourly']),-2)
        self.assertEqual(exact(w['market_eur_per_mwh']['HU_MINUS_AT']['max_hourly']),0)
        rank=r['windows'][-1]['descriptive_same_domain_ranks']['load_mwh']
        self.assertEqual(rank['equal_windows_including_self'],3)

    def test_overlap_is_exact_coverage_union_and_does_not_inflate_ties(self):
        r=summarize([(1,0)]*24,[1]*6,[1]*6,[1]*6,3)
        for c in r['criteria'].values():
            self.assertEqual(c['ties'],4);self.assertEqual(len(c['selected_hour_coverage_union']),1)
            self.assertEqual(c['selected_hour_coverage_union'][0]['hours'],6)
        self.assertEqual(len(r['selector_temporal_overlap']),10)
        for pair in r['selector_temporal_overlap']:
            self.assertEqual(pair['coverage_union_intersection_hours'],6)
            self.assertEqual(pair['shared_selected_window_count'],4)
        self.assertEqual(market._intersection([[0,3],[6,8]],[[1,2],[3,7]]),[[1,2],[6,7]])

    def test_price_load_overlap_retains_shifted_actual_window(self):
        r=summarize([(1,0)]*4+[(4,0)]*4+[(4,0)]*4+[(1,0)]*4,[0,1,2,3],[5,5,0,0],[0]*4,2)
        load=r['criteria']['HIGHEST_MEAN_SOURCE_LOAD']['window_indices'][0]
        price=r['criteria']['HIGHEST_MEAN_HU_PRICE']['window_indices'][0]
        self.assertEqual((load,price),(1,0))
        pair=next(x for x in r['selector_temporal_overlap'] if x['left_criterion']=='HIGHEST_MEAN_SOURCE_LOAD' and x['right_criterion']=='HIGHEST_MEAN_HU_PRICE')
        self.assertEqual(pair['coverage_union_intersection_hours'],1)
        self.assertNotEqual(r['windows'][price]['mean_temperature_c'],r['windows'][load]['mean_temperature_c'])

    def test_random_all_windows_ranks_ties_and_market_arithmetic_match_brute_force(self):
        rng=random.Random(58)
        for n in range(2,8):
            q=[(rng.randrange(6),rng.randrange(-3,8)) for _ in range(n*4)]
            t=[rng.randrange(-5,6) for _ in range(n)];hp=[rng.randrange(-4,5) for _ in range(n)];ap=[rng.randrange(-4,5) for _ in range(n)]
            for h in range(1,n+1):
                r=summarize(q,t,hp,ap,h);values=[]
                for i in range(n-h+1):
                    selected=q[4*i:4*(i+h)]
                    load=sum(F(a,4) for a,b in selected)
                    inject=sum(F(max(b,0),4) for a,b in selected);withdraw=sum(F(max(-b,0),4) for a,b in selected)
                    values.append(dict(zip(market.FIELDS,(sum(t[i:i+h]),load,inject,withdraw,inject-withdraw,load-inject+withdraw,
                                     sum(hp[i:i+h]),sum(ap[i:i+h]),sum(hp[i:i+h])-sum(ap[i:i+h])))))
                for i,w in enumerate(r['windows']):
                    self.assertEqual(w['hour_indices_half_open'],[i,i+h])
                    for key in market.FIELDS:
                        ranking=w['descriptive_same_domain_ranks'][key]
                        self.assertEqual(ranking['lower_windows'],sum(v[key]<values[i][key] for v in values))
                        self.assertEqual(ranking['equal_windows_including_self'],sum(v[key]==values[i][key] for v in values))
                        self.assertEqual(ranking['higher_windows'],sum(v[key]>values[i][key] for v in values))
                    spreads=[a-b for a,b in zip(hp[i:i+h],ap[i:i+h])]
                    self.assertEqual(exact(w['market_eur_per_mwh']['HU_MINUS_AT']['arithmetic_time_mean']),F(sum(spreads),h))
                    self.assertEqual(exact(w['market_eur_per_mwh']['HU_MINUS_AT']['min_hourly']),min(spreads))
                    self.assertEqual(exact(w['market_eur_per_mwh']['HU_MINUS_AT']['max_hourly']),max(spreads))
                for name,(key,direction) in market.CRITERIA.items():
                    best=(min if direction=='min' else max)(v[key] for v in values)
                    self.assertEqual(r['criteria'][name]['window_indices'],[i for i,v in enumerate(values) if v[key]==best])

    def test_decimal_context_cannot_change_any_result(self):
        q=grid([(2,1)]*12);w=weather(['0.1','0.2','0.1']);hp=price_rows(['0.10','0.20','-0.10'],'HU');ap=price_rows([0,1,2],'AT')
        def run():return market._summarize(q,w,hp,ap,hu_source_id='SYNTHETIC_HU',at_source_id='SYNTHETIC_AT',window_hours=3,start=START,end=START+3*HOUR)
        expected=run()
        with localcontext() as c:
            c.prec=1;c.traps[Inexact]=True;c.traps[Rounded]=True
            self.assertEqual(run(),expected)

    def test_full_domain_duration_and_no_partial_or_wraparound_windows(self):
        r=summarize([(1,2)]*20,[1]*5,[1]*5,[2]*5,5)
        self.assertEqual(r['windows_evaluated'],1)
        self.assertEqual(r['windows'][0]['hour_indices_half_open'],[0,5])
        self.assertEqual(r['windows'][0]['energy_mwh'],r['annual_energy_mwh'])
        self.assertEqual(summarize([(1,0)]*20,[1]*5,[1]*5,[2]*5,3)['windows_evaluated'],3)


class JointFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.g=grid([(2,1)]*8);self.w=weather([1,2]);self.h=price_rows([1,2],'HU');self.a=price_rows([3,4],'AT')

    def run_rows(self,**updates):
        args={'grid_rows':self.g,'weather':self.w,'hu_rows':self.h,'at_rows':self.a,'hu_source_id':'SYNTHETIC_HU',
              'at_source_id':'SYNTHETIC_AT','window_hours':1,'start':START,'end':START+2*HOUR}
        args.update(updates);return market._summarize(**args)

    def test_invalid_window_and_domain_fail_before_sources(self):
        for k in (None,True,0,-1,1.0,'1',3):
            with self.assertRaises(ValueError):self.run_rows(window_hours=k)
        signature=inspect.signature(market.calculate_reference)
        for key in ('window','window_hours'):
            self.assertIs(signature.parameters[key].default,inspect.Parameter.empty)
        for window in ('civil2025',None,'2025'):
            with self.assertRaises(ValueError):market.calculate_reference({}, {},weather_path='absent',hu_source_paths={},at_source_paths={},window=window,window_hours=1)

    def test_each_source_is_exhausted_including_post_final_yield(self):
        for name,rows in (('grid_rows',self.g),('hu_rows',self.h),('at_rows',self.a)):
            def late_failure():
                yield from rows
                raise ValueError('late source validation')
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'late source'):
                self.run_rows(**{name:late_failure()})

    def test_both_price_sources_missing_extra_duplicate_reordered_fail(self):
        for name,rows in (('hu_rows',self.h),('at_rows',self.a)):
            for bad in (rows[:-1],rows+[rows[-1]],[rows[0],rows[0]],list(reversed(rows))):
                with self.subTest(name=name),self.assertRaises(ValueError):self.run_rows(**{name:bad})

    def test_price_shifted_end_source_float_nonfinite_and_lexeme_fail(self):
        for name,rows in (('hu_rows',self.h),('at_rows',self.a)):
            for field,value in (('start_utc',START+HOUR),('end_utc',START+2*HOUR),
                                ('source_id','WRONG_ZONE'),('price_eur_per_mwh',1.0),
                                ('price_eur_per_mwh','NaN'),('price_eur_per_mwh',F(999)),
                                ('source_price_lexeme','1.0')):
                bad=[replace(rows[0],**{field:value}),rows[1]]
                with self.subTest(name=name,field=field),self.assertRaises(ValueError):self.run_rows(**{name:bad})

    def test_grid_and_weather_final_boundary_fail(self):
        for bad in (self.g[:-1],self.g+[self.g[-1]]):
            with self.assertRaises(ValueError):self.run_rows(grid_rows=bad)
        with self.assertRaises(ValueError):self.run_rows(weather=self.w[:-1])
        bad=deepcopy(self.g);bad[-1].end_utc+=QUARTER
        with self.assertRaises(ValueError):self.run_rows(grid_rows=bad)

    def test_source_contract_has_separate_uncertainty_and_no_valuation_code(self):
        m=at.source_manifest()
        self.assertEqual(set(m['uncertainty']),{'statistical','structural','POL'})
        for flag in ('policy_defaults_selected','national_admission','public_source_publication_authorized'):
            self.assertIs(m[flag],False)
        source=inspect.getsource(market)
        self.assertNotIn('value_wholesale_reference(',source)
        self.assertNotIn('ImportedEnergy(',source)
        self.assertNotIn('hu._value(',source)


class PrivateOutputTests(unittest.TestCase):
    def test_public_path_guard_precedes_any_source_read(self):
        with patch.object(market,'calculate_reference',side_effect=AssertionError('must not read')):
            with self.assertRaises(ValueError):materializer.materialize({},window='utc2025',window_hours=1,output_dir=materializer.ROOT/'public_numeric_output')

    def test_symlink_nested_git_existing_and_external_git_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);actual=root/'actual';actual.mkdir();link=root/'link';link.symlink_to(actual,target_is_directory=True)
            with self.assertRaises(ValueError):materializer.guard_private_output(link/'new')
            (actual/'.git').mkdir()
            with self.assertRaises(ValueError):materializer.guard_private_output(actual/'new')
            external=root/'external';external.mkdir();(external/'receipt.json').write_text('occupied')
            with self.assertRaises(ValueError):materializer.guard_private_output(external)
            external2=root/'external2';external2.mkdir();(external2/'receipt.json').symlink_to(root/'missing')
            with self.assertRaises(ValueError):materializer.guard_private_output(external2)

    def test_synthetic_receipt_permissions_no_overwrite_and_no_output_on_failure(self):
        synthetic={'reference_id':'SYNTHETIC_ONLY','result':{'hours':2,'windows_evaluated':2}}
        private_parent=materializer.ROOT/'data/interim'
        private_parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=private_parent) as tmp:
            target=Path(tmp)/'fresh'
            with patch.object(market,'calculate_reference',return_value=synthetic):
                result=materializer.materialize({},window='utc2025',window_hours=1,output_dir=target)
            self.assertEqual((target/'receipt.json').stat().st_mode & 0o777,0o600)
            self.assertEqual(result['hours'],2)
            with self.assertRaises(ValueError):materializer.materialize({},window='utc2025',window_hours=1,output_dir=target)
            fresh=Path(tmp)/'never_created'
            with patch.object(market,'calculate_reference',side_effect=ValueError('final source failure')):
                with self.assertRaisesRegex(ValueError,'final source'):
                    materializer.materialize({},window='utc2025',window_hours=1,output_dir=fresh)
            self.assertFalse(fresh.exists())

    def test_path_contract_duplicate_keys_and_cli_explicit_parameters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'paths.json';path.write_text('{"source_paths":{},"source_paths":{}}')
            with self.assertRaises(ValueError):materializer.paths_contract(path)
        run=subprocess.run([sys.executable,'tools/materialize_b19_joint_market.py'],cwd=materializer.ROOT,capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        for flag in ('--paths-json','--window','--window-hours','--output-dir'):self.assertIn(flag,run.stderr)


if __name__=='__main__':unittest.main()
