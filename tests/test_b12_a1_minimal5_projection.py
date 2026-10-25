"""Real annual-data projection and adversarial contract checks; no SCN selected."""
import copy,csv,hashlib,io,json,tempfile,unittest
from collections import Counter
from dataclasses import replace
from datetime import datetime,date
from decimal import Decimal,localcontext,ROUND_DOWN,ROUND_UP,ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
from modules.B12 import a1_reference_response as a1
from modules.B12 import a1_profile_projection as p

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed/b12/a1_minimal5'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def binding():return p.REPOSITORY_PROJECTION_BINDING
def csv_bytes(rows,columns=p.COLUMNS):
    f=io.StringIO(newline='');w=csv.writer(f,lineterminator='\n');w.writerow(columns);w.writerows(rows)
    return f.getvalue().encode()

class RealProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=a1.load_reference(ROOT)  # repository default, same accepted quantities
        cls.new=a1.load_reference(ROOT,projection_binding=binding())
        with (DATA/'REFERENCE_HOURLY_5.csv').open(encoding='utf-8',newline='') as f:
            cls.newrows=list(csv.DictReader(f))

    def test_independently_reviewed_43800_field_commitment_retained(self):
        receipt=read(DATA/'DERIVATION_RECEIPT.json')
        self.assertEqual(len(self.newrows),8760)
        retained=[[row[key] for key in p.COLUMNS] for row in self.newrows]
        # Same canonical serialization used by the preserved derivation.
        actual=hashlib.sha256(json.dumps(retained,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(actual,receipt['view_retained_fields_sha256'])
        self.assertEqual(actual,receipt['source_retained_fields_sha256'])
        self.assertTrue(receipt['all_retained_fields_text_identical'])
        self.assertEqual(receipt['source_sha256'],'cd1247bb9c904531e06951542958b257e2471cf8fbd7469fed2e9ce55ffe554b')

    def test_S1_S2_and_sufficient_statistics_exactly_equal(self):
        self.assertEqual(self.old.periods,self.new.periods)
        self.assertEqual([x.hours for x in self.new.periods],[5086,3674])
        self.assertEqual(self.old.source_ids,self.new.source_ids)
        # Same exact per-period quantities and same pure B04 producer imply the
        # same parameterized function for every admissible common q/m mapping.
        self.assertEqual(digest(Path(a1.b04.__file__)),'57f00eb92999a317cfc016f96ae87378f548b0d1be93f5e70a08cac2874fbdcb')

    def test_full_hourly_support_DST_and_partial_days_retained(self):
        counts=Counter(datetime.fromisoformat(r['interval_start_utc']).astimezone(a1.LOCAL).date() for r in self.newrows)
        for day,expected in [(date(2025,3,30),23),(date(2025,10,26),25),(date(2025,1,1),23),(date(2026,1,1),1)]:
            self.assertEqual(counts[day],expected)
        self.assertEqual(self.new.periods[0].start_utc,a1.START)
        self.assertEqual(self.new.periods[-1].end_utc_exclusive,a1.END)
        self.assertFalse(self.new.complete_local_civil_year)

    def test_retained_own_model_and_full_MVM_pattern_not_open_license(self):
        m=read(DATA/'SOURCE_CLASSIFICATION.json')
        self.assertEqual(m['annual_scale']['truth'],'ASS')
        self.assertTrue(m['hp_reference']['own_calculation'])
        self.assertEqual(m['hp_reference']['truth'],'DER')
        self.assertIn('Whole UTC2025 hourly',m['mvm_profile']['retained_pattern'])
        self.assertFalse(m['removed_national_load']['included'])
        self.assertFalse(m['privacy_boundary']['private_measured_household_data_in_output'])
        meta=read(DATA/'PROJECTION_SIDECAR.json')
        self.assertEqual(meta['scope'],p.SCOPE)
        self.assertEqual(meta['rights'],p.RIGHTS)
        self.assertFalse(meta['rights']['publication_authorized'])
        self.assertTrue(all(v['truth']=='Q' and v['value'] is None for v in meta['scope']['unknown_components'].values()))

    def test_old_and_current_hashes_remain_distinct_and_traceable(self):
        old=dict(self.old.provenance);new=dict(self.new.provenance)
        self.assertEqual(new['ancestral_physical_profile'],'cd1247bb9c904531e06951542958b257e2471cf8fbd7469fed2e9ce55ffe554b')
        self.assertNotEqual(new['ancestral_physical_profile'],new['physical_profile'])
        self.assertEqual(new['physical_profile'],digest(DATA/'REFERENCE_HOURLY_5.csv'))
        self.assertEqual(new['projection_sidecar'],binding().sha256)
        for key in ['repo/modules/B04/engine.py','repo/modules/B12/input_accounting_contract.py','B04_tariffs']:
            self.assertEqual(old[key],new[key])

    def test_projection_runtime_does_not_load_external_legacy_CSV(self):
        original=Path.read_bytes
        def forbid(path):
            if path.name=='UNIT_INCREMENT_HOURLY_8760.csv':raise AssertionError('legacy full dataset read')
            return original(path)
        with patch.object(Path,'read_bytes',forbid):
            actual=a1.load_reference(ROOT,projection_binding=binding())
        self.assertEqual(actual,self.new)

    def test_repository_default_and_explicit_legacy_contract(self):
        self.assertEqual(self.old.projection_binding,binding())
        # No silent legacy fallback. Explicit legacy mode still requires its
        # original hash-bound data; it is intentionally absent from clean CI.
        with self.assertRaises(FileNotFoundError):a1.load_reference(ROOT,projection_binding=None)
        self.assertIsNotNone(self.new.projection_binding)
        with self.assertRaises(a1.A1ReferenceError):a1.summarize_hourly_profile((DATA/'REFERENCE_HOURLY_5.csv').read_bytes())

    def test_repository_binding_is_selfcontained_and_ancestor_is_not_required(self):
        self.assertEqual(binding().path,'data/processed/b12/a1_minimal5/PROJECTION_SIDECAR.json')
        self.assertEqual(binding().sha256,digest(ROOT/binding().path))
        self.assertFalse((ROOT/'inputs/a1_reference/UNIT_INCREMENT_HOURLY_8760.csv').exists())
        self.assertFalse((ROOT.parent/'PROJECTION_BINDING.json').exists())
        self.assertEqual(a1.load_reference(ROOT),self.new)

    def test_missing_default_projection_fails_without_legacy_fallback(self):
        original=Path.read_bytes
        seen=[]
        def missing(path):
            seen.append(path.name)
            if path.name=='PROJECTION_SIDECAR.json':raise FileNotFoundError('missing reviewed minimal5 sidecar')
            return original(path)
        with patch.object(Path,'read_bytes',missing),self.assertRaisesRegex(a1.A1ReferenceError,'missing projection sidecar'):
            a1.load_reference(ROOT)
        self.assertNotIn('UNIT_INCREMENT_HOURLY_8760.csv',seen)

    def test_all_parametric_B04_regions_and_fixed_fees_replay_equally(self):
        # These are labeled TEST_ONLY invocation witnesses, not adopted quotas
        # or household choices. Universal equivalence rests on identical inputs.
        with localcontext() as ctx:
            ctx.prec=50;ctx.rounding=ROUND_HALF_EVEN
            eps=Decimal('0.00000000000000000001')
            vectors=[]
            for period in self.old.periods:
                b,h=period.base_kwh,period.hp_kwh
                vectors.append([Decimal(0),b-eps,b,b+eps,b+h-eps,b+h,b+h+eps,Decimal('1000000000')])
            for i in range(8):
                for months in [Decimal(0),Decimal(1)/31,Decimal(12)]:
                    q={'S1':vectors[0][i],'S2':vectors[1][(i+3)%8]}
                    m={'S1':months,'S2':months/7}
                    old=a1.evaluate_reference(self.old,allowances=q,billed_months=m,context=None)
                    new=a1.evaluate_reference(self.new,allowances=q,billed_months=m,context=None)
                    self.assertEqual((old.status,old.missing,old.periods,old.totals,old.bills),
                                     (new.status,new.missing,new.periods,new.totals,new.bills))
                    self.assertEqual(new.status,'EVALUATED_CONTEXT_INCOMPLETE')
                    self.assertFalse(new.bills)
                    for pold,pnew,row in zip(self.old.periods,self.new.periods,new.periods):
                        for energy1,energy2 in [(pold.base_kwh,pnew.base_kwh),(pold.base_kwh+pold.hp_kwh,pnew.base_kwh+pnew.hp_kwh)]:
                            self.assertEqual(a1.b04.price_a1(energy1,q[pold.id],m[pold.id],a1.AREA),
                                             a1.b04.price_a1(energy2,q[pnew.id],m[pnew.id],a1.AREA))
                        old_bill=a1.b04.price_a1(pold.base_kwh,q[pold.id],m[pold.id],a1.AREA)
                        new_bill=a1.b04.price_a1(pold.base_kwh+pold.hp_kwh,q[pold.id],m[pold.id],a1.AREA)
                        self.assertEqual(old_bill.fixed_charge_huf,new_bill.fixed_charge_huf)
                        self.assertEqual(row['common_fixed_gross_HUF'],old_bill.fixed_charge_huf)
                        # Cancellation is exact for the components as rationals.
                        # Rounded Decimal totals are compared old/new above,
                        # without imposing a new rounding rule or tolerance.
                        self.assertEqual(Fraction(new_bill.consumption_charge_huf)+Fraction(new_bill.fixed_charge_huf)
                                         -Fraction(old_bill.consumption_charge_huf)-Fraction(old_bill.fixed_charge_huf),
                                         Fraction(new_bill.consumption_charge_huf)-Fraction(old_bill.consumption_charge_huf))

    def test_missing_invalid_q_m_context_and_no_native_bill_unchanged(self):
        for q,m in [(None,None),({'S1':Decimal('NaN'),'S2':Decimal(1)},{'S1':Decimal(1),'S2':Decimal(1)}),
                    ({'S1':Decimal(0),'S2':Decimal(0)},{'S1':Decimal(-1),'S2':Decimal(0)})]:
            a=a1.evaluate_reference(self.old,allowances=q,billed_months=m)
            b=a1.evaluate_reference(self.new,allowances=q,billed_months=m)
            self.assertEqual((a.status,a.missing,a.totals,a.bills),(b.status,b.missing,b.totals,b.bills))
            self.assertFalse(b.bills)

    def test_ambient_Decimal_context_does_not_change_source_or_evaluation(self):
        for rounding in [ROUND_DOWN,ROUND_UP]:
            with localcontext() as ctx:
                ctx.prec=6;ctx.rounding=rounding
                self.assertEqual(a1.load_reference(ROOT,projection_binding=binding()).periods,self.old.periods)
                q={'S1':Decimal(0),'S2':Decimal(0)};m={'S1':Decimal(1),'S2':Decimal(1)}
                a=a1.evaluate_reference(self.old,allowances=q,billed_months=m)
                b=a1.evaluate_reference(self.new,allowances=q,billed_months=m)
                self.assertEqual(a.totals,b.totals)

    def test_supplied_period_tampering_rejected(self):
        bad=replace(self.new,periods=(replace(self.new.periods[0],hp_kwh=Decimal(1)),self.new.periods[1]))
        with self.assertRaises(a1.A1ReferenceError):a1.evaluate_reference(bad)

class ParserRejectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (DATA/'REFERENCE_HOURLY_5.csv').open(encoding='utf-8',newline='') as f:
            cls.rows=list(csv.reader(f))[1:]
    def changed(self,change,columns=p.COLUMNS):
        rows=[list(r) for r in self.rows];change(rows);return csv_bytes(rows,columns)

    def test_missing_extra_duplicate_reordered_or_wrong_unit_header(self):
        headers=[p.COLUMNS[:-1],p.COLUMNS+('national_load',),p.COLUMNS[:-1]+(p.COLUMNS[3],),tuple(reversed(p.COLUMNS)),
                 p.COLUMNS[:-1]+('unit_incremental_W55_device_reference_MW',)]
        for header in headers:
            with self.subTest(header=header),self.assertRaises(p.ProjectionError):p.parse_profile(csv_bytes(self.rows,header))
    def test_missing_extra_row_field_and_blank_row(self):
        for change in [lambda r:r[0].pop(),lambda r:r[0].append('1'),lambda r:r.insert(3,[])]:
            with self.assertRaises(p.ProjectionError):p.parse_profile(self.changed(change))
    def test_missing_duplicate_unordered_or_extra_hours(self):
        for change in [lambda r:r.pop(1),lambda r:r.__setitem__(1,list(r[0])),lambda r:r.reverse(),lambda r:r.append(list(r[-1]))]:
            with self.assertRaises(p.ProjectionError):p.parse_profile(self.changed(change))
    def test_nonUTC_naive_relabelled_and_invalid_endpoints(self):
        for value in ['2028-01-01T00:00:00+00:00','2025-01-01T00:00:00+01:00','2025-01-01T00:00:00','not-a-time','']:
            with self.subTest(value=value),self.assertRaises(p.ProjectionError):
                p.parse_profile(self.changed(lambda r:r[0].__setitem__(0,value)))
        with self.assertRaises(p.ProjectionError):p.parse_profile(self.changed(lambda r:r[0].__setitem__(1,r[0][0])))
    def test_nonfinite_negative_missing_and_malformed_numbers(self):
        for index in [2,3,4]:
            for value in ['NaN','Infinity','-Infinity','-1','',' 1','1 ','true','1_0']:
                with self.subTest(index=index,value=value),self.assertRaises(p.ProjectionError):
                    p.parse_profile(self.changed(lambda r:r[0].__setitem__(index,value)))
        for value in ['0','0.5','2']:
            with self.assertRaises(p.ProjectionError):p.parse_profile(self.changed(lambda r:r[0].__setitem__(2,value)))
    def test_noncanonical_encoding_and_line_endings_rejected(self):
        raw=(DATA/'REFERENCE_HOURLY_5.csv').read_bytes()
        for altered in [b'\xef\xbb\xbf'+raw,raw.replace(b'\n',b'\r\n'),b'\xff'+raw,raw+b'\n']:
            with self.assertRaises(p.ProjectionError):p.parse_profile(altered)

class SidecarRejectionTests(unittest.TestCase):
    def fixture(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);root=Path(t.name)
        for f in DATA.iterdir():
            dest=root/'data/processed/b12/a1_minimal5'/f.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
        return root,read(DATA/'PROJECTION_SIDECAR.json')
    def load(self,root,meta):
        side=root/binding().path;side.write_text(json.dumps(meta),encoding='utf-8')
        return p.load_payload(root,p.ProjectionBinding(binding().path,digest(side)),
            ancestor_sha256='cd1247bb9c904531e06951542958b257e2471cf8fbd7469fed2e9ce55ffe554b',scenario_id=a1.SCENARIO)
    def rewrite_pin(self,root,meta,key,change):
        file=root/meta[key]['path'];d=read(file);change(d);file.write_text(json.dumps(d),encoding='utf-8')
        meta[key]['sha256']=digest(file);meta[key]['bytes']=file.stat().st_size
    def test_stale_sidecar_and_missing_explicit_binding_rejected(self):
        root,meta=self.fixture();side=root/binding().path;side.write_bytes(side.read_bytes()+b' ')
        with self.assertRaises(p.ProjectionError):p.load_payload(root,binding(),ancestor_sha256=meta['ancestor']['sha256'],scenario_id=a1.SCENARIO)
        for bad in [None,{},(binding().path,binding().sha256)]:
            with self.assertRaises(p.ProjectionError):p.load_payload(root,bad,ancestor_sha256=meta['ancestor']['sha256'],scenario_id=a1.SCENARIO)
    def test_missing_extra_sidecar_fields_rejected_after_rehash(self):
        for change in [lambda m:m.pop('scope'),lambda m:m.update(unexpected='x')]:
            root,meta=self.fixture();change(meta)
            with self.assertRaises(p.ProjectionError):self.load(root,meta)
    def test_Q_zero_SCN_and_rights_promotions_rejected_after_rehash(self):
        for change in [lambda m:m['scope']['unknown_components']['HMV_electricity_kw'].update(value=0),
                       lambda m:m['scope'].update(truth_context='OBS'),lambda m:m['scope'].update(complete_local_civil_year=0),
                       lambda m:m['rights'].update(publication_authorized=True),lambda m:m['rights'].update(open_license_asserted=True)]:
            root,meta=self.fixture();change(meta)
            with self.assertRaises(p.ProjectionError):self.load(root,meta)
    def test_schema_units_precision_window_and_extra_fields_rejected_after_rehash(self):
        for change in [lambda d:d['units'].update(common_base_reference_kw='MW'),lambda d:d.update(precision=6),
                       lambda d:d.update(rows=8760.0),lambda d:d.update(start_utc='2028-01-01'),lambda d:d.update(extra=True)]:
            root,meta=self.fixture();self.rewrite_pin(root,meta,'schema',change)
            with self.assertRaises(p.ProjectionError):self.load(root,meta)
    def test_old_hash_mapping_and_derivation_revisions_rejected(self):
        for change in [lambda m:m['ancestor'].update(sha256='0'*64),lambda m:m['ancestor'].update(retained_columns=[]),
                       lambda m:m['derivation'].update(sha256='0'*64)]:
            root,meta=self.fixture();change(meta)
            with self.assertRaises(p.ProjectionError):self.load(root,meta)
    def test_changed_derivation_period_or_unproven_mapping_rejected_after_rehash(self):
        for change in [lambda d:d.update(all_retained_fields_text_identical=False),lambda d:d['periods'][0].update(base_kWh='1'),
                       lambda d:d.update(source_sha256='0'*64),lambda d:d.update(source_retained_fields_sha256='bad',view_retained_fields_sha256='bad')]:
            root,meta=self.fixture();self.rewrite_pin(root,meta,'derivation',change)
            with self.assertRaises(p.ProjectionError):self.load(root,meta)
    def test_source_classification_drift_or_missing_fields_rejected_after_rehash(self):
        for change in [lambda d:d['mvm_profile'].update(preserved_reuse_status='OPEN'),lambda d:d['hp_reference'].update(truth='OBS'),
                       lambda d:d['annual_scale'].update(value_kWh=2000),lambda d:d['mvm_profile'].pop('source_id'),
                       lambda d:d['removed_national_load'].update(included=True)]:
            root,meta=self.fixture();self.rewrite_pin(root,meta,'source_classification',change)
            with self.assertRaises(p.ProjectionError):self.load(root,meta)
    def test_path_escape_missing_pin_duplicate_JSON_and_nonfinite_JSON_rejected(self):
        for value in ['../outside.csv',str(ROOT/'outside.csv')]:
            root,meta=self.fixture();meta['view']['path']=value
            with self.assertRaises(p.ProjectionError):self.load(root,meta)
        root,meta=self.fixture();(root/meta['view']['path']).unlink()
        with self.assertRaises(p.ProjectionError):self.load(root,meta)
        for raw in [b'{"a":1,"a":2}',b'{"a":NaN}']:
            with self.assertRaises(p.ProjectionError):p.strict_json(raw)

if __name__=='__main__':unittest.main()
