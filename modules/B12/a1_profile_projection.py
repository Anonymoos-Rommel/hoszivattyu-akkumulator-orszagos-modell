"""Strict local projection contract; no source rights or economic formula added."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from decimal import Decimal,DecimalException,localcontext,ROUND_HALF_EVEN
from pathlib import Path
import csv,hashlib,io,json,re

COLUMNS=('interval_start_utc','interval_end_utc','hours','common_base_reference_kw',
         'unit_incremental_W55_device_reference_kw')
START=datetime(2025,1,1,tzinfo=timezone.utc)
CUT=datetime(2025,7,31,22,tzinfo=timezone.utc)
END=datetime(2026,1,1,tzinfo=timezone.utc)
SCHEMA={
    'schema_id':'B12-A1-MINIMAL5-UTC2025-V1','encoding':'UTF-8','line_endings':'LF',
    'columns':list(COLUMNS),'column_count':5,'rows':8760,'additional_columns':False,
    'units':{'interval_start_utc':'UTC ISO8601','interval_end_utc':'UTC ISO8601',
             'hours':'h','common_base_reference_kw':'kW','unit_incremental_W55_device_reference_kw':'kW'},
    'start_utc':START.isoformat(),'end_utc_exclusive':END.isoformat(),
    'billing_cut_utc':CUT.isoformat(),'period_hours':{'S1':5086,'S2':3674},
    'numeric_contract':'finite nonnegative decimal strings; duration exactly1h',
    'precision':50,'rounding':'ROUND_HALF_EVEN',
}
UNKNOWN={'truth':'Q','value':None,'reason':'NOT_SUPPLIED_IN_ACCEPTED_SH_ONLY_REFERENCE'}
SCOPE={
    'truth_context':'SCN','boundary':'COMMON_BASE_PLUS_W55_SPACE_HEATING_ONLY',
    'baseline':'COMMON_BASE_ONLY','programme':'COMMON_BASE_PLUS_W55_DEVICE_REFERENCE',
    'PV':'ABSENT_SCN','battery':'ABSENT_SCN','complete_local_civil_year':False,
    'original_timestamps_remapped':False,'observed_household_claim':False,
    'unknown_components':{k:UNKNOWN.copy() for k in
        ('HMV_electricity_kw','outside_unit_auxiliary_correction_kw','physical_net_increment_kw')},
}
RIGHTS={'publication_authorized':False,'open_license_asserted':False,
        'source_classification_review_required':True,'scope':'LOCAL_PROJECTION_AND_REVIEW_ONLY'}

class ProjectionError(ValueError):pass

def require(ok,message):
    if not ok:raise ProjectionError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def same(value,expected):
    return json.dumps(value,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':'))

def strict_json(raw):
    def pairs(items):
        result={}
        for k,v in items:
            require(k not in result,'duplicate JSON key');result[k]=v
        return result
    def invalid(_):raise ProjectionError('nonfinite JSON value')
    try:return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=invalid)
    except (UnicodeError,ValueError) as exc:raise ProjectionError('malformed strict JSON') from exc

def exact_keys(value,keys,name):
    require(type(value) is dict and set(value)==set(keys),'unexpected or missing '+name+' fields')

def path(root,relative):
    require(type(relative) is str and bool(relative),'relative path required')
    p=(root/relative).resolve()
    require(not Path(relative).is_absolute() and p.is_relative_to(root),'path escapes projection root')
    return p

def pin_bytes(root,item):
    exact_keys(item,('path','sha256','bytes'),'pin')
    require(type(item['sha256']) is str and re.fullmatch('[0-9a-f]{64}',item['sha256']) is not None,'SHA256 required')
    require(type(item['bytes']) is int and item['bytes']>0,'positive exact byte count required')
    p=path(root,item['path'])
    try:raw=p.read_bytes()
    except OSError as exc:raise ProjectionError('missing pinned projection evidence') from exc
    require(len(raw)==item['bytes'] and sha(raw)==item['sha256'],'projection pin byte/hash mismatch')
    return raw

def number(value):
    require(type(value) is str and value==value.strip() and bool(value),'explicit decimal string required')
    require(re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?',value) is not None,'canonical nonnegative decimal syntax required')
    try:d=Decimal(value)
    except (DecimalException,ValueError) as exc:raise ProjectionError('invalid decimal') from exc
    require(d.is_finite() and d>=0,'finite nonnegative decimal required')
    return d

def parse_profile(raw):
    """Return exactly the six existing ReferencePeriod constructor arguments."""
    require(type(raw) is bytes,'CSV bytes required')
    try:
        require(b'\r' not in raw,'canonical LF projection required')
        reader=csv.reader(io.StringIO(raw.decode('utf-8'),newline=''),strict=True)
        require(tuple(next(reader,()))==COLUMNS,'minimal5 exact column/unit contract')
        sums=[[0,Decimal(0),Decimal(0)],[0,Decimal(0),Decimal(0)]]
        with localcontext() as ctx:
            ctx.prec=50;ctx.rounding=ROUND_HALF_EVEN
            count=0
            for i,row in enumerate(reader):
                require(len(row)==5,'malformed row: missing or extra fields')
                left=datetime.fromisoformat(row[0]);right=datetime.fromisoformat(row[1])
                require(left.utcoffset()==right.utcoffset()==timedelta(0),'UTC-aware endpoints required')
                require(left==START+timedelta(hours=i) and right==left+timedelta(hours=1),'missing duplicate unordered or shifted hour')
                hours,base,hp=map(number,row[2:])
                require(hours==1,'exactly1h duration required')
                bucket=sums[0 if left<CUT else 1]
                bucket[0]+=1;bucket[1]+=base*hours;bucket[2]+=hp*hours;count+=1
        require(count==8760 and [s[0] for s in sums]==[5086,3674],'exact8760 UTC2025 coverage required')
        return tuple((key,left,right,*s) for key,left,right,s in
            (('S1',START,CUT,sums[0]),('S2',CUT,END,sums[1])))
    except ProjectionError:raise
    except (UnicodeError,csv.Error,ValueError,TypeError,DecimalException,OverflowError) as exc:
        raise ProjectionError('malformed projection values') from exc

@dataclass(frozen=True)
class ProjectionBinding:
    path:str
    sha256:str

def load_payload(root,binding,*,ancestor_sha256,scenario_id):
    """Bind current minimal bytes separately from the external historical source.

    The derivation receipt records local equivalence. It is not an independent
    publisher license or E2 admission. The old full CSV is not silently loaded.
    """
    root=Path(root).resolve()
    require(type(binding) is ProjectionBinding,'explicit ProjectionBinding required')
    require(type(binding.sha256) is str and re.fullmatch('[0-9a-f]{64}',binding.sha256) is not None,'sidecar SHA256 required')
    try:raw=path(root,binding.path).read_bytes()
    except OSError as exc:raise ProjectionError('missing projection sidecar') from exc
    require(sha(raw)==binding.sha256,'sidecar hash mismatch')
    meta=strict_json(raw)
    exact_keys(meta,('schema_version','representation','scenario_id','schema','view','ancestor',
                    'derivation','source_classification','scope','rights'),'sidecar')
    require(type(meta['schema_version']) is int and meta['schema_version']==1,'sidecar version')
    require(meta['representation']=='MINIMAL5_UTC2025' and meta['scenario_id']==scenario_id,'projection representation/SCN mismatch')
    require(same(meta['scope'],SCOPE),'Q/SCN/system boundary changed')
    require(same(meta['rights'],RIGHTS),'local artifact cannot confer publication/license rights')
    schema=strict_json(pin_bytes(root,meta['schema']))
    require(same(schema,SCHEMA),'schema/unit/time contract changed')
    ancestor=meta['ancestor']
    exact_keys(ancestor,('sha256','bytes','representation','retained_columns'),'ancestor')
    require(ancestor['sha256']==ancestor_sha256 and type(ancestor['bytes']) is int and ancestor['bytes']==1592688,
            'historical full source identity changed')
    require(ancestor['representation']=='LEGACY14_UTC2025' and ancestor['retained_columns']==list(COLUMNS),'ancestral mapping changed')
    view=pin_bytes(root,meta['view']);parse_profile(view)
    require(meta['view']['sha256']!=ancestor_sha256,'old and projected hashes must be distinct')
    derivation=strict_json(pin_bytes(root,meta['derivation']))
    exact_keys(derivation,('source_sha256','view_sha256','rows','columns','all_retained_fields_text_identical',
                           'source_retained_fields_sha256','view_retained_fields_sha256','periods','method'),'derivation')
    require(derivation['source_sha256']==ancestor_sha256 and derivation['view_sha256']==sha(view),'derivation source/view mismatch')
    require(type(derivation['rows']) is int and derivation['rows']==8760 and derivation['columns']==list(COLUMNS),
            'derivation coverage changed')
    require(derivation['all_retained_fields_text_identical'] is True and
            derivation['source_retained_fields_sha256']==derivation['view_retained_fields_sha256'],
            'derivation retained-field identity missing')
    require(type(derivation['source_retained_fields_sha256']) is str and
            re.fullmatch('[0-9a-f]{64}',derivation['source_retained_fields_sha256']) is not None,'retained-field SHA256 required')
    require(derivation['method']=='DIRECT_COLUMN_SELECTION_NO_NUMERIC_REWRITE','unsupported projection derivation')
    actual_periods=[dict(id=p[0],start_utc=p[1].isoformat(),end_utc_exclusive=p[2].isoformat(),hours=p[3],
                         base_kWh=str(p[4]),HP_kWh=str(p[5])) for p in parse_profile(view)]
    require(same(derivation['periods'],actual_periods),'derivation period totals changed')
    classification=strict_json(pin_bytes(root,meta['source_classification']))
    exact_keys(classification,('mvm_profile','annual_scale','hp_reference','removed_national_load','privacy_boundary'),'source classification')
    for key,fields in {
        'mvm_profile':('source_id','original_url','index_url','workbook_sha256','preserved_reuse_status','classification_basis','publisher_notice_url','retained_pattern'),
        'annual_scale':('value_kWh','truth','source_url','limitation'),
        'hp_reference':('reference_id','hourly_source_sha256','manifest_sha256','truth','evidence_tier','own_calculation','underlying_sources','limit'),
        'removed_national_load':('included','field','source_record','reason'),
        'privacy_boundary':('private_measured_household_data_in_output','basis','not_a_license_claim'),
    }.items():exact_keys(classification[key],fields,key)
    require(classification['removed_national_load']['included'] is False,'national load must be absent')
    require(classification['removed_national_load']['field']=='native_national_hourly_mean_mw_reference_only'
            and classification['removed_national_load']['source_record']=='B08B09-P5-R01','removed source identity changed')
    require(classification['mvm_profile']['preserved_reuse_status']=='LOCAL_ANALYSIS_ONLY_NOT_REPOSITORY_REDISTRIBUTION_CLEARED',
            'MVM source classification cannot be silently promoted')
    mvm=classification['mvm_profile'];hp=classification['hp_reference'];scale=classification['annual_scale']
    require(mvm['source_id']=='SRC-MVM-2025' and mvm['original_url']=='https://mvmhalozat.hu/attachments/39326'
            and mvm['index_url']=='https://mvmhalozat.hu/aram/oldalak/1871'
            and mvm['workbook_sha256']=='7e6135250f69f48deab35e2f8f56711b0a92b37e15eed9147090dd8be1365dc5',
            'MVM source identity changed')
    require(type(scale['value_kWh']) is int and scale['value_kWh']==2419 and scale['truth']=='ASS'
            and scale['source_url']=='https://www.ksh.gov.hu/stadat_files/kor/hu/kor0044.html','annual scale classification changed')
    require(classification['hp_reference']['reference_id']=='E2-ANNUAL-WM50-W55-TABULA-SFH01-UTC2025-001',
            'HP source reference changed')
    require(hp['hourly_source_sha256']=='1dd563c4984f91a6aa5b5cbe156bcc827ad65e5252a9f14772651f10c50cb493'
            and hp['manifest_sha256']=='d4f53d6b8c60633723875d3cc815b40d29edd0d4f737535de3d88324cd810b15'
            and hp['truth']=='DER' and hp['evidence_tier']=='E2' and hp['own_calculation'] is True,
            'HP derivation classification changed')
    require(classification['privacy_boundary']['private_measured_household_data_in_output'] is False,'private data boundary changed')
    require(classification['privacy_boundary']['not_a_license_claim'] is True,'privacy statement cannot confer license')
    proof={'projection_sidecar':binding.sha256,'projection_schema':meta['schema']['sha256'],
           'projection_derivation':meta['derivation']['sha256'],
           'projection_source_classification':meta['source_classification']['sha256'],
           'ancestral_physical_profile':ancestor_sha256}
    return view,meta,proof


REPOSITORY_PROJECTION_BINDING = ProjectionBinding(
    "data/processed/b12/a1_minimal5/PROJECTION_SIDECAR.json",
    "4b811a63c5c7b37c5c4687fb7af891cde4e0eea595af96e2ad63749c2f54a3eb",
)
