"""Synthetic-only AT validation; public tests contain no genuine price panel."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import localcontext, Inexact, Rounded
from fractions import Fraction
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B19 import austrian_price_reference as at

START = datetime(2024,12,31,tzinfo=at.hu.UTC)
END = datetime(2026,1,2,tzinfo=at.hu.UTC)
TRANSITION = datetime(2025,9,30,22,tzinfo=at.hu.UTC)


def label(d):
    return f'{at.hu.MONTHS[d.month-1]} {d.day}, {d.year} {d.hour%12 or 12}:{d.minute:02d} {"AM" if d.hour<12 else "PM"}'


def cent_lexeme(n):
    return ('-' if n<0 else '')+str(abs(n)//100)+'.'+str(abs(n)%100).zfill(2)


def synthetic_price(a,hour=False):
    base = (((a-START)//at.HOUR)%11-5)*100
    return base + (1 if hour else a.minute//15) if a>=TRANSITION else base


def csv_fixture(start,count,minutes=60,values=None):
    field = 'Austria [€/MWh] '+('Calculated resolutions' if minutes==60 else 'Original resolutions')
    out=io.StringIO();w=csv.writer(out,delimiter=';',lineterminator='\n')
    w.writerow(['Start date','End date',field])
    for i in range(count):
        a=start+i*timedelta(minutes=minutes); local=a.astimezone(at.AT).replace(tzinfo=None)
        w.writerow([label(local),label(local+timedelta(minutes=minutes)),
                    values[i] if values is not None else cent_lexeme(synthetic_price(a,minutes==60))])
    return out.getvalue().encode('utf-8-sig'), {'field':field,'duration_minutes':minutes,'rows':count,'source_id':'SYNTHETIC_AT'}


def parse(start,count,minutes=60,values=None):
    raw,pin=csv_fixture(start,count,minutes,values)
    return at._parse_csv(raw,pin,start=start,end=start+count*timedelta(minutes=minutes))


class AustrianParsingTests(unittest.TestCase):
    def test_signed_lexemes_and_precision_context_independence(self):
        values=['-12.34','0.00','12345678901234567890.12']
        with localcontext() as c:
            c.prec=1;c.traps[Inexact]=True;c.traps[Rounded]=True
            rows=parse(START,3,values=values)
        self.assertEqual([r.source_price_lexeme for r in rows],values)
        self.assertEqual(rows[0].price_eur_per_mwh,Fraction(-617,50))
        self.assertEqual(rows[2].price_eur_per_mwh,Fraction(1234567890123456789012,100))

    def test_both_dst_changes_at_both_resolutions(self):
        for minutes in (15,60):
            for day in ((2025,3,30),(2025,10,26)):
                start=datetime(*day,tzinfo=at.hu.UTC);rows=parse(start,180//minutes,minutes)
                self.assertEqual(sum(r.source_end_label_anomaly for r in rows),1)
                self.assertTrue(all(a.end_utc==b.start_utc for a,b in zip(rows,rows[1:])))
                if day[1]==10:
                    self.assertEqual(rows[0].source_start_label,rows[60//minutes].source_start_label)
                    self.assertNotEqual(rows[0].start_utc,rows[60//minutes].start_utc)

    def test_invalid_prices_fail(self):
        for value in ('','NaN','Infinity','-Infinity','1.2','1.234','1e2','1,20',' 1.20','+1.20'):
            with self.subTest(value=value),self.assertRaises(ValueError):parse(START,1,values=[value])

    def test_country_currency_resolution_and_end_label_fail(self):
        raw,pin=csv_fixture(START,2)
        for before,after in ((b'Austria',b'Hungary'),('€/MWh'.encode(),b'HUF/kWh'),
                             (b'Calculated',b'Original'),(b'2:00 AM',b'2:30 AM')):
            with self.subTest(after=after),self.assertRaises(ValueError):
                at._parse_csv(raw.replace(before,after),pin,start=START,end=START+2*at.HOUR)
        changed=dict(pin,field='Hungary [€/MWh] Calculated resolutions')
        with self.assertRaises(ValueError):at._parse_csv(raw,changed,start=START,end=START+2*at.HOUR)

    def test_gap_duplicate_extra_reorder_and_truncation_fail(self):
        raw,pin=csv_fixture(START,3);lines=raw.decode('utf-8-sig').splitlines()
        for changed in (lines[:-1],lines+[lines[-1]],lines[:2]+[lines[1]]+lines[3:],
                        [lines[0],lines[2],lines[1],lines[3]],lines+[''],lines[:-1]+['bad;row']):
            with self.subTest(changed=changed),self.assertRaises(ValueError):
                at._parse_csv(('\n'.join(changed)+'\n').encode(),pin,start=START,end=START+3*at.HOUR)

    def test_shifted_utc_civil_endpoints_and_nonexistent_spring_label_fail(self):
        raw,pin=csv_fixture(START,3)
        for start,end in ((START-at.HOUR,START+2*at.HOUR),(START,START+4*at.HOUR),
                          (START.replace(tzinfo=None),START+3*at.HOUR)):
            with self.assertRaises(ValueError):at._parse_csv(raw,pin,start=start,end=end)
        start=datetime(2025,3,30,1,tzinfo=at.hu.UTC);raw,pin=csv_fixture(start,1)
        with self.assertRaises(ValueError):
            at._parse_csv(raw.replace(b'3:00 AM',b'2:00 AM'),pin,start=start,end=start+at.HOUR)

    def test_at_configuration_identity_is_independent(self):
        field={'id':8004170,'data_id':4170,'name':'MM-Bausteine.Österreich',
               'unit':'VD-Einheit.Euro/MWh','source_resolution':'quarterhour','region':['DE-LU']}
        doc={'meta_data':{'version':1},'fields':[field]}
        at._configuration(json.dumps(doc).encode())
        for key,value in (('id',8000262),('data_id',262),('name','MM-Bausteine.Ungarn'),
                          ('unit','HUF/MWh'),('source_resolution','hour'),('region',['HU'])):
            bad=deepcopy(doc);bad['fields'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):at._configuration(json.dumps(bad).encode())
        doc['fields'].append(field)
        with self.assertRaises(ValueError):at._configuration(json.dumps(doc).encode())

    def test_json_duplicate_keys_and_nonfinite_forbidden(self):
        for raw in (b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":Infinity}'):
            with self.assertRaises(ValueError):at._json(raw)


class AustrianSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hours=parse(START,8808)
        cls.quarters=parse(START,35232,15)
        cls.pins=deepcopy(at.source_manifest()['at']['source_artifacts'])
        cls.index_id='SYNTHETIC_INDEX'
        weeks=[p for p in cls.pins if p['intended_use']=='PHYSICAL_UTC_EPOCH_WITNESS']
        cls.pins=[*weeks,{'source_id':cls.index_id,'intended_use':'AT_SERIES_INDEX','timestamp_count':len(weeks)}]
        cls.raw={cls.index_id:json.dumps({'timestamps':[p['first_epoch_ms'] for p in weeks]}).encode()}
        for p in weeks:
            points=[]
            for i in range(p['points']):
                epoch=p['first_epoch_ms']+i*900000
                instant=at.EPOCH+timedelta(milliseconds=epoch)
                # Synthetic exact decimal strings are accepted by the shared exact helper.
                points.append([epoch,cent_lexeme(synthetic_price(instant))])
            cls.raw[p['source_id']]=json.dumps({'meta_data':p['file_generation_metadata'],'series':points}).encode()

    def test_full_padded_at_native_and_five_witness_contract(self):
        r=at._reconcile(self.hours,self.quarters,TRANSITION)
        self.assertEqual(r['hours_compared'],8808)
        self.assertEqual(r['max_abs_mean_difference_eur_per_mwh'],at.exact(Fraction(1,200)))
        self.assertEqual(r['first_varying_hour_utc'],TRANSITION.isoformat())
        result=at._witnesses(self.raw,self.pins,self.quarters,self.index_id)
        self.assertEqual(sum(p['exact_overlapping_quarters'] for p in result),2976)

    def test_witness_price_epoch_schema_generation_count_tail_and_index_fail(self):
        sid=self.pins[0]['source_id']
        for mutation in ('price','epoch','schema','metadata','count','tail'):
            raw=dict(self.raw);doc=json.loads(raw[sid]);rows=doc['series']
            if mutation=='price':rows[150][1]='999.00'
            elif mutation=='epoch':rows[150][0]+=1
            elif mutation=='schema':doc['extra']=1
            elif mutation=='metadata':doc['meta_data']['version']=999
            elif mutation=='count':rows.pop()
            elif mutation=='tail':rows[-1][1]='NaN'
            raw[sid]=json.dumps(doc).encode()
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):at._witnesses(raw,self.pins,self.quarters,self.index_id)
        raw=dict(self.raw);raw[self.index_id]=b'{"timestamps":[]}'
        with self.assertRaises(ValueError):at._witnesses(raw,self.pins,self.quarters,self.index_id)
        with self.assertRaises(ValueError):at._witnesses(self.raw,self.pins[:-2]+self.pins[-1:],self.quarters,self.index_id)

    def test_native_hour_end_quarter_start_precision_and_transition_fail(self):
        for variant in ('hour_end','quarter_start','precision','pretransition','transition'):
            hs=list(self.hours);qs=list(self.quarters);transition=TRANSITION
            if variant=='hour_end':hs[-1]=replace(hs[-1],end_utc=hs[-1].end_utc+at.HOUR)
            elif variant=='quarter_start':qs[-1]=replace(qs[-1],start_utc=qs[-1].start_utc-at.QUARTER)
            elif variant=='precision':hs[-1]=replace(hs[-1],price_eur_per_mwh=hs[-1].price_eur_per_mwh+1)
            elif variant=='pretransition':qs[0]=replace(qs[0],price_eur_per_mwh=qs[0].price_eur_per_mwh+Fraction(1,100))
            else:transition-=at.HOUR
            with self.subTest(variant=variant),self.assertRaises(ValueError):at._reconcile(hs,qs,transition)
        with self.assertRaises(ValueError):at._reconcile(self.hours,self.quarters[:-1],TRANSITION)

    def test_contract_pin_identity_domain_and_path_drift_fail(self):
        m=at.source_manifest()
        self.assertIsNone(m['window_hours_default']);self.assertFalse(m['national_admission'])
        self.assertEqual(m['at']['bidding_zone'],'AT')
        self.assertNotIn('private_path',json.dumps(m))
        for window in (None,'civil2025','2025',True):
            with self.assertRaises(ValueError):at.read_austrian_reference({},window=window)
        for paths in ({},{'WRONG':'absent'}):
            with self.assertRaises(ValueError):at.read_austrian_reference(paths,window='utc2025')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'manifest';p.write_text('{}')
            with patch.object(at,'MANIFEST',p),self.assertRaisesRegex(ValueError,'pinned'):
                at.source_manifest()
            for pin in m['at']['source_artifacts']:
                p.write_bytes(b'SYNTHETIC SOURCE DRIFT')
                with self.subTest(source_id=pin['source_id']),self.assertRaisesRegex(ValueError,'drift'):
                    at.hu._source_bytes({pin['source_id']:p},{'source_artifacts':[pin]})


if __name__=='__main__':unittest.main()
