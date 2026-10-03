"""Synthetic-only contracts and adverse cases; no original market-price panel."""
from copy import deepcopy
import csv
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext, Inexact, Rounded
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from modules.B04 import wholesale_reference as ref
from tools import materialize_b04_wholesale_reference as tool

UTC = timezone.utc
START = datetime(2024, 12, 31, tzinfo=UTC)
END = datetime(2026, 1, 2, tzinfo=UTC)
TRANSITION = datetime(2025, 9, 30, 22, tzinfo=UTC)


def label(local):
    return f'{ref.MONTHS[local.month-1]} {local.day}, {local.year} {local.hour%12 or 12}:{local.minute:02d} {"AM" if local.hour < 12 else "PM"}'


def cents(value):
    return ('-' if value < 0 else '') + str(abs(value)//100) + '.' + str(abs(value)%100).zfill(2)


def synthetic_price(instant, hourly=False):
    n = (instant-START)//ref.HOUR
    base = (n % 13 - 6) * 100
    return base + (1 if hourly else instant.minute//15) if instant >= TRANSITION else base


def csv_bytes(start, count, *, minutes=60, values=None):
    field = 'Hungary [€/MWh] ' + ('Calculated resolutions' if minutes == 60 else 'Original resolutions')
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';', lineterminator='\r\n')
    writer.writerow(['Start date', 'End date', field])
    for i in range(count):
        a = start + i*timedelta(minutes=minutes)
        local = a.astimezone(ref.HU).replace(tzinfo=None)
        price = values[i] if values is not None else cents(synthetic_price(a, minutes == 60))
        writer.writerow([label(local), label(local+timedelta(minutes=minutes)), price])
    return buffer.getvalue().encode('utf-8-sig'), {'source_id':'SYNTHETIC_ONLY', 'field':field, 'duration_minutes':minutes, 'rows':count}


def fixture(folder):
    m = deepcopy(ref.source_manifest())
    paths = {}
    for pin in m['source_artifacts']:
        role = pin['intended_use']
        if role in ('PUBLISHER_HOURLY_PRICE', 'NATIVE_RESOLUTION_RECONCILIATION'):
            raw, _ = csv_bytes(START, pin['rows'], minutes=pin['duration_minutes'])
        elif role == 'HU_IDENTITY':
            doc = {'meta_data': {'version':1}, 'main':[{'id':8000262, 'data_id':262,
                   'name':'MM-Bausteine.Ungarn','unit':'VD-Einheit.Euro/MWh',
                   'source_resolution':'quarterhour','region':['DE-LU']}]}
            raw = json.dumps(doc).encode()
        elif role == 'PHYSICAL_UTC_EPOCH_WITNESS':
            points = []
            for i in range(pin['points']):
                epoch = pin['first_epoch_ms']+i*900000
                at = ref.EPOCH + timedelta(milliseconds=epoch)
                points.append([epoch, synthetic_price(at)/100])
            raw = json.dumps({'meta_data':pin['file_generation_metadata'], 'series':points}).encode()
        else:
            raw = b'SYNTHETIC RIGHTS OR TIME EVIDENCE; NOT ORIGINAL CONTENT'
        path = folder / (pin['source_id']+'.fixture')
        path.write_bytes(raw)
        paths[pin['source_id']] = path
        pin['bytes'] = len(raw)
        pin['sha256'] = hashlib.sha256(raw).hexdigest()
    return m, paths


class SourceParserTests(unittest.TestCase):
    def parse(self, raw, pin, start, count, minutes=60):
        return ref._parse_csv(raw, pin, start=start, end=start+count*timedelta(minutes=minutes))

    def test_synthetic_negative_zero_precision_and_native_lexemes(self):
        raw,pin=csv_bytes(START,3,values=['-12.34','0.00','12345678901234567890.12'])
        with localcontext() as ctx:
            ctx.prec=2;ctx.traps[Inexact]=True;ctx.traps[Rounded]=True
            rows=self.parse(raw,pin,START,3)
        self.assertEqual([r.source_price_lexeme for r in rows],['-12.34','0.00','12345678901234567890.12'])
        self.assertEqual(rows[0].price_eur_per_mwh,Fraction(-617,50))
        self.assertEqual(rows[2].price_eur_per_mwh,Fraction(1234567890123456789012,100))

    def test_spring_dst_end_is_derived_and_original_clock_retained(self):
        start=datetime(2025,3,30,tzinfo=UTC)
        raw,pin=csv_bytes(start,3)
        rows=self.parse(raw,pin,start,3)
        self.assertTrue(rows[0].source_end_label_anomaly)
        self.assertEqual(rows[0].source_end_label,'Mar 30, 2025 2:00 AM')
        self.assertEqual(rows[0].end_utc.astimezone(ref.HU).hour,3)
        self.assertEqual(rows[1].start_utc,rows[0].end_utc)

    def test_autumn_fold_keeps_both_starts_and_anomaly(self):
        start=datetime(2025,10,26,tzinfo=UTC)
        raw,pin=csv_bytes(start,3)
        rows=self.parse(raw,pin,start,3)
        self.assertEqual(rows[0].source_start_label,rows[1].source_start_label)
        self.assertNotEqual(rows[0].start_utc,rows[1].start_utc)
        self.assertTrue(rows[0].source_end_label_anomaly)
        self.assertFalse(rows[1].source_end_label_anomaly)

    def test_quarter_dst_same_physical_rule(self):
        start=datetime(2025,3,30,tzinfo=UTC)
        raw,pin=csv_bytes(start,8,minutes=15)
        rows=self.parse(raw,pin,start,8,15)
        self.assertEqual(sum(r.source_end_label_anomaly for r in rows),1)
        self.assertEqual(rows[3].end_utc,rows[4].start_utc)

    def test_missing_invalid_nonfinite_and_noncent_prices_fail(self):
        for price in ('','NaN','Infinity','-Infinity','1,20','1.2','1.234',' 1.20','1e2','--1.00'):
            with self.subTest(price=price):
                raw,pin=csv_bytes(START,1,values=[price])
                with self.assertRaises(ref.WholesaleReferenceError):self.parse(raw,pin,START,1)

    def test_wrong_country_currency_headers_fail(self):
        raw,pin=csv_bytes(START,2)
        for old,new in (('Hungary','Germany'),('€/MWh','HUF/kWh'),('Calculated','Original')):
            with self.subTest(new=new),self.assertRaises(ref.WholesaleReferenceError):
                self.parse(raw.replace(old.encode(),new.encode()),pin,START,2)

    def test_gap_duplicate_reorder_extra_and_malformed_rows_fail(self):
        raw,pin=csv_bytes(START,3)
        lines=raw.decode('utf-8-sig').splitlines()
        changes=(lines[:-1],lines+[lines[-1]],lines[:2]+[lines[1]]+lines[3:],
                 [lines[0],lines[2],lines[1],lines[3]],lines+[''],lines[:2]+['bad;row']+lines[3:])
        for changed in changes:
            with self.subTest(changed=changed),self.assertRaises(ref.WholesaleReferenceError):
                self.parse(('\n'.join(changed)+'\n').encode(),pin,START,3)

    def test_wrong_source_end_and_boundary_fail(self):
        raw,pin=csv_bytes(START,1)
        with self.assertRaises(ref.WholesaleReferenceError):
            self.parse(raw.replace(b'2:00 AM',b'3:00 AM'),pin,START,1)
        with self.assertRaises(ref.WholesaleReferenceError):
            self.parse(raw,pin,START+ref.HOUR,1)
        with self.assertRaises(ref.WholesaleReferenceError):
            self.parse(raw,pin,START,2)


class SourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.m,cls.paths=fixture(Path(cls.temp.name))

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def read(self,window='utc2025',paths=None,m=None):
        with patch.object(ref,'source_manifest',return_value=m or self.m):
            return ref.read_wholesale_reference(paths or self.paths,window=window)

    def test_public_manifest_has_no_local_paths_or_policy_default(self):
        m=ref.source_manifest()
        self.assertEqual(m['reference_id'],ref.REFERENCE_ID)
        self.assertIsNone(m['window_default']);self.assertIsNone(m['imported_energy_default'])
        self.assertFalse(m['public_source_publication_authorized'])
        self.assertEqual(len(m['source_artifacts']),11)
        self.assertTrue(all('private_path' not in s for s in m['source_artifacts']))
        transition=next(s for s in m['source_artifacts'] if s['intended_use']=='NATIVE_AUCTION_TRANSITION')
        self.assertEqual(transition['displayed_publication_date'],'2025-10-10')

    def test_manifest_hash_unknown_versions_and_bad_identity_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'manifest.json'
            path.write_text('{}')
            with patch.object(ref,'MANIFEST',path),self.assertRaises(ref.WholesaleReferenceError):ref.source_manifest()
            for field,value in (('schema_version',2),('reference_id','UNKNOWN'),('bidding_zone','DE-LU'),('currency','HUF')):
                m=deepcopy(self.m);m[field]=value;path.write_text(json.dumps(m))
                with patch.object(ref,'MANIFEST',path),patch.object(ref,'MANIFEST_SHA256',hashlib.sha256(path.read_bytes()).hexdigest()):
                    with self.subTest(field=field),self.assertRaises(ref.WholesaleReferenceError):ref.source_manifest()

    def test_synthetic_full_padded_native_epoch_validation_both_windows(self):
        utc=self.read();civil=self.read('civil2025')
        self.assertEqual(len(utc.records),8760);self.assertEqual(len(civil.records),8760)
        self.assertEqual(utc.records[0].start_utc,datetime(2025,1,1,tzinfo=UTC))
        self.assertEqual(civil.records[0].start_utc,datetime(2024,12,31,23,tzinfo=UTC))
        self.assertEqual(civil.records[-1].end_utc,datetime(2025,12,31,23,tzinfo=UTC))
        self.assertEqual(utc.reconciliation['epoch_overlapping_quarters'],2976)
        self.assertEqual(utc.reconciliation['max_abs_mean_difference_eur_per_mwh'],ref.exact(Fraction(1,200)))
        self.assertEqual(utc.evidence['currency'],'EUR')
        self.assertIsNone(utc.evidence['original_auction_vintage'])

    def test_unsupported_window_and_path_set_fail(self):
        for window in ('2025',None,'utc2026'):
            with self.subTest(window=window),self.assertRaises(ref.WholesaleReferenceError):self.read(window)
        for paths in ({'WRONG':Path('absent')},{**self.paths,'EXTRA':Path('absent')},dict(list(self.paths.items())[1:])):
            with self.assertRaises(ref.WholesaleReferenceError):self.read(paths=paths)

    def test_each_original_hash_drift_fails(self):
        for sid,path in self.paths.items():
            original=path.read_bytes()
            try:
                path.write_bytes(original+b' ')
                with self.subTest(sid=sid),self.assertRaises(ref.WholesaleReferenceError):self.read()
            finally:path.write_bytes(original)

    def test_bad_configuration_identity_fails(self):
        raw={'meta_data':{'version':1},'main':[{'id':8000262,'data_id':262,'name':'MM-Bausteine.Ungarn','unit':'VD-Einheit.Euro/MWh','source_resolution':'quarterhour','region':['DE-LU']}]}
        for field,value in (('id',8000416),('data_id',416),('name','Germany'),('unit','HUF/kWh')):
            doc=deepcopy(raw);doc['main'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ref.WholesaleReferenceError):ref._configuration(json.dumps(doc))

    def test_epoch_numeric_mismatch_fails_even_if_test_pin_requalified(self):
        m=deepcopy(self.m);pin=next(s for s in m['source_artifacts'] if s['intended_use']=='PHYSICAL_UTC_EPOCH_WITNESS')
        p=self.paths[pin['source_id']];old=p.read_bytes()
        try:
            doc=json.loads(old);doc['series'][200][1]+=1;p.write_text(json.dumps(doc))
            pin['bytes']=p.stat().st_size;pin['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ref.WholesaleReferenceError,'epoch witness/source price mismatch'):self.read(m=m)
        finally:p.write_bytes(old)

    def test_native_reconciliation_tolerance_and_pretransition_repetition_fail(self):
        start=TRANSITION-ref.HOUR
        raw,pin=csv_bytes(start,2)
        hours=ref._parse_csv(raw,pin,start=start,end=start+2*ref.HOUR)
        raw,pin=csv_bytes(start,8,minutes=15)
        quarters=ref._parse_csv(raw,pin,start=start,end=start+2*ref.HOUR)
        broken=list(hours);broken[-1]=replace(broken[-1],price_eur_per_mwh=broken[-1].price_eur_per_mwh+1)
        with self.assertRaises(ref.WholesaleReferenceError):ref._reconcile(broken,quarters,TRANSITION)
        broken=list(quarters);broken[0]=replace(broken[0],price_eur_per_mwh=broken[0].price_eur_per_mwh+Fraction(1,100))
        with self.assertRaisesRegex(ref.WholesaleReferenceError,'pretransition'):ref._reconcile(hours,broken,TRANSITION)

    def test_source_map_duplicate_and_nonpaths_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'paths.json'
            for content in ('{"x":"a","x":"b"}','[]','{"x":null}','{"x":""}'):
                p.write_text(content)
                with self.subTest(content=content),self.assertRaises(ref.WholesaleReferenceError):ref.source_map(p)


class ValuationTests(unittest.TestCase):
    def setUp(self):
        raw,pin=csv_bytes(START,3,values=['-2.00','3.00','0.25'])
        rows=ref._parse_csv(raw,pin,start=START,end=START+3*ref.HOUR)
        self.reference=ref.WholesaleReference('synthetic',rows,{'currency':'EUR','source_id':'SYNTHETIC_ONLY'}, {})
        self.loads=tuple(ref.ImportedEnergy(r.start_utc,r.end_utc,q) for r,q in zip(rows,('2','1.5',Fraction(1,3))))
        self.kw={'convention':ref.CONVENTION,'within_hour_profile':'FLAT','energy_unit':'MWh','profile_id':'SYNTHETIC_VARYING'}

    def test_exact_varying_arithmetic_credit_and_weighted_price(self):
        out=ref._value(self.reference,self.loads,**self.kw)
        self.assertEqual(out['total_imported_mwh'],ref.exact(Fraction(23,6)))
        self.assertEqual(out['wholesale_reference_eur'],ref.exact(Fraction(7,12)))
        self.assertEqual(out['negative_price_credit_eur'],ref.exact(-4))
        self.assertEqual(out['consumption_weighted_price_eur_per_mwh'],ref.exact(Fraction(7,46)))

    def test_ambient_decimal_precision_and_traps_have_no_effect(self):
        baseline=ref._value(self.reference,self.loads,**self.kw)
        with localcontext() as ctx:
            ctx.prec=1;ctx.traps[Inexact]=True;ctx.traps[Rounded]=True
            actual=ref._value(self.reference,self.loads,**self.kw)
        self.assertEqual(actual,baseline)

    def test_huge_exact_decimal_energy_no_precision_loss(self):
        q=Decimal('123456789012345678901234567890.12345678901234567890')
        loads=[replace(e,imported_mwh=q) for e in self.loads]
        with localcontext() as ctx:
            ctx.prec=1;ctx.traps[Inexact]=True;ctx.traps[Rounded]=True
            out=ref._value(self.reference,loads,**self.kw)
        self.assertEqual(out['wholesale_reference_eur'],ref.exact(Fraction(q)*Fraction(5,4)))

    def test_zero_imports_no_weighted_price(self):
        out=ref._value(self.reference,[replace(e,imported_mwh=0) for e in self.loads],**self.kw)
        self.assertEqual(out['wholesale_reference_eur'],ref.exact(0));self.assertIsNone(out['consumption_weighted_price_eur_per_mwh'])

    def test_bad_profile_convention_units_and_identity_fail(self):
        for key,value in (('convention','RETAIL'),('within_hour_profile','VARYING_QUARTERS'),('energy_unit','kWh'),('profile_id','')):
            with self.subTest(key=key),self.assertRaises(ref.WholesaleReferenceError):ref._value(self.reference,self.loads,**{**self.kw,key:value})

    def test_missing_extra_duplicate_reordered_naive_and_short_energy_fail(self):
        bad=(self.loads[:-1],self.loads+(self.loads[-1],),self.loads+(None,),self.loads[::-1],
             (self.loads[0],self.loads[0],self.loads[2]),
             (replace(self.loads[0],start_utc=START.replace(tzinfo=None)),)+self.loads[1:],
             (replace(self.loads[0],end_utc=START+ref.QUARTER),)+self.loads[1:])
        for loads in bad:
            with self.subTest(loads=loads),self.assertRaises(ref.WholesaleReferenceError):ref._value(self.reference,loads,**self.kw)

    def test_negative_nonfinite_float_bool_missing_quantity_fail(self):
        for value in (-1,'NaN','Infinity',Decimal('NaN'),1.2,True,None,[],{},'1/3'):
            with self.subTest(value=value),self.assertRaises(ref.WholesaleReferenceError):
                ref._value(self.reference,(replace(self.loads[0],imported_mwh=value),)+self.loads[1:],**self.kw)

    def test_public_valuation_always_calls_pinned_reader(self):
        with patch.object(ref,'read_wholesale_reference',return_value=self.reference) as reader:
            result=ref.value_wholesale_reference({'source':'explicit'},window='utc2025',imports=self.loads,**self.kw)
        reader.assert_called_once_with({'source':'explicit'},window='utc2025')
        self.assertEqual(result['negative_price_credit_eur'],ref.exact(-4))


class MaterializerTests(unittest.TestCase):
    def git(self,root,*args):
        return subprocess.run(['git',*args],cwd=root,capture_output=True,check=False)

    def test_existing_private_guard_is_reused_without_mutation(self):
        from tools.materialize_b13_fiscal_reference import guard_private_output
        self.assertIs(tool.guard_private_output,guard_private_output)

    def test_bad_outputs_fail_before_first_source_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'repo';root.mkdir();self.git(root,'init')
            (root/'.gitignore').write_text('/data/interim/\n')
            output=root/'data/interim/case';output.mkdir(parents=True)
            guarded=tool.guard_private_output
            for case in ('public','existing','symlink','nested','tracked_deleted','unignored'):
                target=output/'receipt.json';chosen=output
                if case=='public':chosen=root/'public'
                elif case=='existing':target.write_text('keep')
                elif case=='symlink':target.symlink_to(root/'absent')
                elif case=='nested':(output/'.git').mkdir()
                elif case=='tracked_deleted':
                    target.write_text('keep');self.git(root,'add','-f','--',str(target.relative_to(root)));target.unlink()
                elif case=='unignored':(root/'.gitignore').write_text('')
                try:
                    with patch.object(tool,'guard_private_output',side_effect=lambda p: guarded(p,root=root)),patch.object(tool.wholesale,'read_wholesale_reference') as reader:
                        with self.subTest(case=case),self.assertRaises(ValueError):tool.materialize({},window='utc2025',output_dir=chosen)
                        reader.assert_not_called()
                finally:
                    if target.exists() or target.is_symlink():target.unlink()
                    if (output/'.git').exists():(output/'.git').rmdir()
                    if case=='tracked_deleted':self.git(root,'rm','--cached','--',str(target.relative_to(root)))
                    (root/'.gitignore').write_text('/data/interim/\n')

    def test_synthetic_materialization_writes_only_guarded_receipt(self):
        raw,pin=csv_bytes(START,1,values=['-1.25'])
        rows=ref._parse_csv(raw,pin,start=START,end=START+ref.HOUR)
        reference=ref.WholesaleReference('synthetic',rows,{'reference_id':'SYNTHETIC_ONLY'}, {})
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'repo';root.mkdir();self.git(root,'init');(root/'.gitignore').write_text('/data/interim/\n')
            output=root/'data/interim/test';guarded=tool.guard_private_output
            with patch.object(tool,'guard_private_output',side_effect=lambda p:guarded(p,root=root)),patch.object(ref,'read_wholesale_reference',return_value=reference):
                summary=tool.materialize({},window='utc2025',output_dir=output)
                self.assertFalse(summary['has_caller_declared_valuation'])
                self.assertEqual({p.name for p in output.iterdir()},{'receipt.json'})
                body=json.loads((output/'receipt.json').read_text())
                self.assertEqual(body['normalized_rows'][0]['source_price_lexeme'],'-1.25')
                self.assertEqual((output/'receipt.json').stat().st_mode & 0o777,0o600)
                with self.assertRaises(ValueError):tool.materialize({},window='utc2025',output_dir=output)

    def test_invalid_import_contract_creates_no_receipt(self):
        raw,pin=csv_bytes(START,1)
        rows=ref._parse_csv(raw,pin,start=START,end=START+ref.HOUR)
        reference=ref.WholesaleReference('synthetic',rows,{}, {})
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'repo';root.mkdir();self.git(root,'init');(root/'.gitignore').write_text('/data/interim/\n')
            bad=root/'bad.json';bad.write_text('{}');output=root/'data/interim/absent';guarded=tool.guard_private_output
            with patch.object(tool,'guard_private_output',side_effect=lambda p:guarded(p,root=root)),patch.object(ref,'read_wholesale_reference',return_value=reference):
                with self.assertRaises(ref.WholesaleReferenceError):tool.materialize({},window='utc2025',output_dir=output,imports_json=bad)
            self.assertFalse(output.exists())

    def test_invalid_unicode_profile_leaves_no_partial_numeric_output(self):
        raw,pin=csv_bytes(START,1)
        rows=ref._parse_csv(raw,pin,start=START,end=START+ref.HOUR)
        reference=ref.WholesaleReference('synthetic',rows,{}, {})
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'repo';root.mkdir();self.git(root,'init');(root/'.gitignore').write_text('/data/interim/\n')
            bad=root/'bad.json';output=root/'data/interim/absent';guarded=tool.guard_private_output
            bad.write_text(json.dumps({'profile_id':chr(0xD800),'convention':ref.CONVENTION,'within_hour_profile':'FLAT','energy_unit':'MWh','intervals':[{'start_utc':START.isoformat(),'end_utc':(START+ref.HOUR).isoformat(),'imported_mwh':'1'}]}))
            with patch.object(tool,'guard_private_output',side_effect=lambda p:guarded(p,root=root)),patch.object(ref,'read_wholesale_reference',return_value=reference):
                with self.assertRaises(UnicodeEncodeError):tool.materialize({},window='utc2025',output_dir=output,imports_json=bad)
            self.assertFalse(output.exists())

    def test_import_json_requires_complete_contract_and_exact_intervals(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'imports.json'
            for content in ({}, {'profile_id':'x','convention':ref.CONVENTION,'within_hour_profile':'FLAT','energy_unit':'MWh','intervals':[{}]}):
                p.write_text(json.dumps(content))
                with self.assertRaises(ref.WholesaleReferenceError):tool.imports_contract(p)
            p.write_text(json.dumps({'profile_id':'x','convention':ref.CONVENTION,'within_hour_profile':'FLAT','energy_unit':'MWh','intervals':[{'start_utc':START.isoformat(),'end_utc':(START+ref.HOUR).isoformat(),'imported_mwh':'0.125'}]}))
            contract,loads=tool.imports_contract(p)
            self.assertEqual(loads[0].imported_mwh,Fraction(1,8));self.assertEqual(contract['energy_unit'],'MWh')


if __name__ == '__main__':unittest.main()
