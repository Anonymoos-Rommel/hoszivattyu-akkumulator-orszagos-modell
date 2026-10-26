"""Read-only bridge of accepted components, with temporal adoption fail-closed.

No new cash event, period mapping, tariff formula or source qualification.
The approved normalized-year policy binds only reference components;
it cannot turn them into receipts, complete cashflows or ROI.
"""
import dataclasses
import hashlib
import json
from datetime import date
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from pathlib import Path
from fractions import Fraction
from types import MappingProxyType

from . import input_accounting_contract as native
from . import a1_reference_response as a1_reference
from .a1_reference_response import NATIVE_C01_BASELINE_SHA, NATIVE_IMPLEMENTATION_SHA

ROOT = Path(__file__).resolve().parents[2]

def _bound_path(relative):
    p = (ROOT / relative).resolve()
    if Path(relative).is_absolute() or not p.is_relative_to(ROOT):
        raise ReferenceError("Binding path escapes candidate repository")
    return p


class ReferenceError(ValueError):
    pass


ACCEPTED_MANIFESTS={
    'C01':'27653e8dea750ef82813ccf3e93a0a4e8c7784bcf19f62da7de55a380b164e61',
    'A1':'3ff7c5838127b764440cb631be9639a303179f81372dc1a585e247d34c5f37a4',
    'GAS':'c2588ffaf9d7201e444afb20799039d9e2e5ca421c1aa6716e758adac1eba8e4',
}
ACCEPTED_POLICY={
    'id':'SCN-NORMALIZED-365-ENERGY-REFERENCE-20261025',
    'mode':'NORMALIZED_365_DAY_REFERENCE','days':365,
    'programme_start_anchor':'2028-01-01','calendar_year':None,
    'remap_original_timestamps':False,'money':'FROZEN_2026_NOMINAL_HUF',
    'recurrence_years':None,'payment_dates':None,
    'decision_ref':'Sentinel_3edee9c757008191a603f883d7495649',
}

# Explicit annual-input vocabulary, classified under existing native categories.
# Unknown identities are refused, rather than assumed to be non-energy O&M.
OM_COMPONENT_CLASSES=MappingProxyType({
    'MAINTENANCE':('O_AND_M','NON_ENERGY'),
    'MAINTENANCE_TRAVEL':('O_AND_M','NON_ENERGY'),
    'REPAIR_LABOUR':('O_AND_M','NON_ENERGY'),
    'REPAIR_PARTS':('O_AND_M','NON_ENERGY'),
    'INSURANCE':('INSURANCE','NON_ENERGY'),
})


def _identity(value,name):
    if not isinstance(value,str) or not value or value!=value.strip():
        raise ReferenceError('Canonical explicit identity required for '+name)


def _components(values):
    if type(values) is not tuple or not values:
        raise ReferenceError('Explicit component tuple required')
    classified=[]
    seen=set()
    for raw in values:
        if not isinstance(raw,str) or not raw.strip():
            raise ReferenceError('Explicit component identity required')
        key=raw.strip().upper()
        if key not in OM_COMPONENT_CLASSES:
            raise ReferenceError('Unknown or non-O&M component class: '+key)
        if key in seen:
            raise ReferenceError('Duplicate normalized component identity: '+key)
        seen.add(key)
        category,energy_class=OM_COMPONENT_CLASSES[key]
        classified.append({'id':key,'native_category':category,'energy_class':energy_class})
    return classified


def _encode_record(value):
    """Lossless source/input snapshot; not native admission or cash serialization."""
    if dataclasses.is_dataclass(value):
        return {'__record__':type(value).__name__,
                **{f.name:_encode_record(getattr(value,f.name)) for f in dataclasses.fields(value)}}
    if isinstance(value,Decimal):return {'__decimal__':str(value)}
    if type(value) is date:return {'__date__':value.isoformat()}
    if type(value) is tuple:return {'__tuple__':[_encode_record(v) for v in value]}
    if value is None or type(value) in (str,int,bool):return value
    raise ReferenceError('Unsupported input-record value; provenance cannot be discarded')


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _decode(value, native):
    if isinstance(value, list):
        return [_decode(v, native) for v in value]
    if not isinstance(value, dict):
        return value
    if set(value)=={'__decimal__'}:
        return Decimal(value['__decimal__'])
    if set(value)=={'__date__'}:
        return date.fromisoformat(value['__date__'])
    if set(value)=={'__tuple__'}:
        return tuple(_decode(v,native) for v in value['__tuple__'])
    if '__native_record__' in value:
        cls=getattr(native,value['__native_record__'],None)
        if not isinstance(cls,type) or not dataclasses.is_dataclass(cls):
            raise ReferenceError('Unknown native record')
        return cls(**{k:_decode(v,native) for k,v in value.items() if k!='__native_record__'})
    return {k:_decode(v,native) for k,v in value.items()}


def prepare(binding_path, temporal_binding=None, om_inputs=None, *, reference_consumer=None):
    binding=_read(Path(binding_path))
    manifests={}
    for key,expected in ACCEPTED_MANIFESTS.items():
        p=_bound_path(binding['accepted_manifests'][key])
        if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise ReferenceError('Accepted manifest drift: '+key)
        manifests[key]=(p.parent,{r['path']:r['sha256'] for r in _read(p)['files']})
    docs={}
    for key,item in binding['sources'].items():
        path=_bound_path(item['path'])
        if key!='temporal_policy':
            base,pins=manifests[item['package']]
            if key=='native':
                if (item['package']!='C01' or item['relative']!='repo/modules/B12/input_accounting_contract.py'
                        or pins.get(item['relative'])!=NATIVE_C01_BASELINE_SHA
                        or item.get('baseline_sha256')!=NATIVE_C01_BASELINE_SHA
                        or item['sha256']!=NATIVE_IMPLEMENTATION_SHA):
                    raise ReferenceError('Native implementation revision/baseline identity mismatch')
            elif pins.get(item['relative'])!=item['sha256']:
                raise ReferenceError('Source not bound to accepted manifest: '+key)
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise ReferenceError('Source hash mismatch: '+key)
        if path.suffix=='.json':
            docs[key]=json.loads(raw.decode('utf-8'))
    if docs.get('temporal_policy')!=ACCEPTED_POLICY:
        raise ReferenceError('Policy is not the exact accepted normalized-year decision')
    if Path(native.__file__).resolve()!=_bound_path(binding['sources']['native']['path']):
        raise ReferenceError('Actual native implementation does not match bound candidate')
    case=_decode(docs['case'],native)
    native.validate_case(case)
    if len(case.costs.rows)!=1:
        raise ReferenceError('One accepted C01 initial component required')
    cost=case.costs.rows[0]
    if cost.gross.value!=Decimal(docs['c01_source']['observed_unit_price']):
        raise ReferenceError('C01 source amount mismatch')
    a1=docs['a1'];gas=docs['gas']
    if a1['profile_remapped_to_2028'] is not False or a1['new_BillInputs']!=0:
        raise ReferenceError('Original A1 temporal/context limits changed')
    if gas['u_parameter']['selected_value'] is not None or gas['E2_adoption'] is not False:
        raise ReferenceError('Gas benchmark no longer has the accepted parametric scope')
    if temporal_binding is None:
        status='INCOMPLETE_TEMPORAL_BINDING'
        missing=['approved normalized annual temporal binding']
    else:
        if not isinstance(temporal_binding,dict):
            raise ReferenceError('Explicit binding record required')
        if temporal_binding.get('mode')!='NORMALIZED_365_DAY_REFERENCE':
            raise ReferenceError('Calendar-year or timestamp remapping not permitted')
        if type(temporal_binding.get('days')) is not int or temporal_binding['days']!=365:
            raise ReferenceError('Exactly365 normalized days required; not366 calendar2028')
        if temporal_binding.get('remap_original_timestamps') is not False:
            raise ReferenceError('Original timestamps must remain unchanged')
        if temporal_binding != docs.get('temporal_policy'):
            status='INCOMPLETE_TEMPORAL_ADOPTION'
            missing=['binding must match the separately hash-pinned accepted policy record']
        else:
            status='BOUND_NORMALIZED_REFERENCE_COMPONENTS'
            missing=[]
    bound=status=='BOUND_NORMALIZED_REFERENCE_COMPONENTS'
    result={
        'status':status,'missing':missing,'complete':False,
        'native_case_id':case.case_id,
        'one_off_initial_component':{'gross_HUF':str(cost.gross.value),
            'cost_id':cost.cost_id,'scope':'C01 standalone outdoor only; not fullCAPEX',
            'repeat_annually':False},
        'preserved_reference_components':{
            'A1_increment_HUF':a1['totals']['incremental_consumption_gross_HUF'],
            'gas_u':gas['u_parameter'],'gas_formula':gas['marginal_SH_gas_charge_definition'],
            'gas_use':'B13 conditional benchmark; not native MARKET_RESIDENTIAL_FINAL BillInput',
            'source_periods':binding['source_periods'],
        },
        'proposed_binding_applied':False,'original_timestamp_remap':False,
        'operating_year':None,'settlement_dates':None,'payment_dates':None,
        'annual_economic_cashflow':None,'full_CAPEX':None,'additional_CAPEX':None,
        'monetary_OM':None,'external_auxiliary_delta':None,'ROI':None,
        'household_first_day_non_worsening':None,'subsidy_exit':None,
        'new_Costs':0,'new_BillInputs':0,'recurrence_years':None,
        'source_use_adoption':False,
    }
    result['temporal_policy_applied']=bound
    result['normalized_reference']=dict(temporal_binding) if bound else None
    result['annual_component_model']=None
    if bound:
        result['annual_component_model']={
            'formula':'F(u+Q)-F(u)-Delta_A1; F(x)=L*min(x,T)+H*max(x-T,0)',
            'Q_MJ':gas['Q_SH_hypothetical_tariff_MJ']['exact'],
            'T_MJ':gas['annual_cap_T_MJ']['exact'],
            'L_HUF_per_MJ':gas['low_gross_HUF_per_MJ']['exact'],
            'H_HUF_per_MJ':gas['high_gross_HUF_per_MJ']['exact'],
            'Delta_A1_HUF':gas['accepted_A1_increment_HUF']['exact'],
            'u_selected':None,'unit':'gross frozen2026 HUF per normalized365-day reference',
            'scope':'Energy reference component only, not full operating saving or native receipt',
        }
    result = integrate_annual_om(result, native, om_inputs)
    if reference_consumer is not None:
        result['reference_consumer'] = _reference_consumer_view(
            reference_consumer, result, case, docs['a1'], Path(binding_path))
    return result


REFERENCE_CONSUMER_PATH = 'data/processed/b12/REFERENCE_CONSUMER_SCN.json'
REFERENCE_CONSUMER_SHA256 = '63fae5b7a96b129ee857f41dec0e928ebe03fe13b1ab932857a292201341be8e'
DEVICE_REFERENCE_PATH = 'registry/b05_annual_device_reference_manifest.json'
DEVICE_REFERENCE_SHA256 = 'd4f53d6b8c60633723875d3cc815b40d29edd0d4f737535de3d88324cd810b15'


def _reference_consumer_view(selection, result, case, accepted_a1, binding_path):
    """Reuse one admitted device reference within the selected household SCN.

    No installed-system calibration, national weight or financial completion is
    inferred. The existing reference admission and its validation debt survive.
    """
    raw_policy = _bound_path(REFERENCE_CONSUMER_PATH).read_bytes()
    if hashlib.sha256(raw_policy).hexdigest() != REFERENCE_CONSUMER_SHA256:
        raise ReferenceError('Reference-consumer decision record changed')
    policy = a1_reference._json(raw_policy)
    try:
        supplied = json.dumps(selection, sort_keys=True, separators=(',', ':'), allow_nan=False)
        expected = json.dumps(policy, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ReferenceError('Exact explicit reference-consumer SCN required') from exc
    if type(selection) is not dict or supplied != expected:
        raise ReferenceError('Reference-consumer selection is not the exact approved SCN')
    if case.scope.household_id != policy['household_id']:
        raise ReferenceError('Reference consumer and C01 household differ')
    view = {
        'status': 'INCOMPLETE_TEMPORAL_BINDING', 'truth_context': 'SCN',
        'selection': json.loads(expected), 'selection_sha256': REFERENCE_CONSUMER_SHA256,
        'native_case_id': case.case_id, 'annual_energy': None,
        'national_scaling': None, 'installed_system_total_kWh': None,
        'new_evidence_admission': False, 'new_Costs': 0, 'new_BillInputs': 0,
        'full_CAPEX': None, 'full_operating_balance': None, 'ROI': None,
    }
    if not result['temporal_policy_applied']:
        return view
    raw_device = _bound_path(DEVICE_REFERENCE_PATH).read_bytes()
    if hashlib.sha256(raw_device).hexdigest() != DEVICE_REFERENCE_SHA256:
        raise ReferenceError('Admitted device-reference manifest changed')
    device = a1_reference._json(raw_device)
    if (device['reference_id'] != policy['reference_id'] or
            device['evidence_status'] != 'DER' or device['evidence_tier'] != 'E2' or
            device['base_status'] != 'PROVISIONAL_BASE'):
        raise ReferenceError('Existing bounded E2 device admission required')
    for relative, pin in device['repository_pins'].items():
        if hashlib.sha256(_bound_path(relative).read_bytes()).hexdigest() != pin:
            raise ReferenceError('Device-reference producer drift: ' + relative)
    try:
        reference = a1_reference.load_reference(ROOT)
    except a1_reference.A1ReferenceError as exc:
        raise ReferenceError('Selected hourly reference: ' + str(exc)) from exc
    if reference.scenario_id != a1_reference.SCENARIO:
        raise ReferenceError('Wrong existing household reference')
    windows = [dict(id=p.id, start_utc=p.start_utc.isoformat(),
        end_utc_exclusive=p.end_utc_exclusive.isoformat(), hours=p.hours,
        base_kWh=str(p.base_kwh), HP_reference_kWh=str(p.hp_kwh))
        for p in reference.periods]
    if windows != accepted_a1['physical_windows']:
        raise ReferenceError('Hourly reference does not reproduce accepted A1 energy windows')
    base = sum((Fraction(p.base_kwh) for p in reference.periods), Fraction(0))
    hp = sum((Fraction(p.hp_kwh) for p in reference.periods), Fraction(0))
    def amount(value):
        with localcontext() as ctx:
            ctx.prec = 50; ctx.rounding = ROUND_HALF_EVEN
            decimal = Decimal(value.numerator) / Decimal(value.denominator)
            return {'exact_kWh': str(value), 'decimal_kWh': str(decimal),
                    'readable_kWh_6dp': format(decimal, '.6f')}
    view.update({
        'status': 'E2_REFERENCE_SCENARIO_READY',
        'device_reference': {'id': device['reference_id'], 'truth': 'DER',
            'evidence_tier': 'E2', 'base_status': 'PROVISIONAL_BASE',
            'scope': device['scope'], 'prior_review': device['source_and_method_review']},
        'annual_energy': {'unit': 'kWh per normalized 365-day reference household',
            'hours': sum(p.hours for p in reference.periods),
            'declared_common_base_kWh': policy['common_base_declared_kWh'],
            'declared_common_base_truth': policy['common_base_truth'],
            'baseline_common_base': amount(base), 'programme_common_base_plus_device': amount(base + hp),
            'incremental_W55_device_reference': amount(hp), 'windows': windows,
            'common_base_counted_once': True, 'original_timestamps_remapped': False},
        'energy_economic_component': result['annual_component_model'],
        'annual_om_status': result['annual_om']['status'],
        'validation_debt': device['validation_debt'],
        'unknown_components': {key: {'value': None, 'truth': 'Q'} for key in
            ('additional_CAPEX', 'monetary_OM', 'HMV', 'external_auxiliary_delta',
             'installed_pump_correction', 'fiscal_allocation')},
        'provenance': {'decision': REFERENCE_CONSUMER_SHA256,
            'device_manifest': DEVICE_REFERENCE_SHA256,
            'annual_input_binding': hashlib.sha256(binding_path.read_bytes()).hexdigest(),
            'annual_adapter': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'hourly_reference': dict(reference.provenance)},
        'limits': device['limits'],
    })
    return view


def component_balance(result,u):
    """Evaluate a caller-supplied parameter; never choose a household value."""
    if result['annual_component_model'] is None:
        raise ReferenceError('Temporal binding incomplete')
    if isinstance(u,bool) or not isinstance(u,(Decimal,Fraction,int)):
        raise ReferenceError('Exact nonnegative MJ parameter required')
    try:u=Fraction(u)
    except (ValueError,OverflowError) as exc:raise ReferenceError('Finite parameter required') from exc
    if u<0:raise ReferenceError('Negative retained gas')
    m=result['annual_component_model']
    q,t,l,h,d=[Fraction(m[k]) for k in ['Q_MJ','T_MJ','L_HUF_per_MJ','H_HUF_per_MJ','Delta_A1_HUF']]
    def f(x):return l*min(x,t)+h*max(x-t,0)
    return f(u+q)-f(u)-d


@dataclasses.dataclass(frozen=True)
class AnnualOMInputs:
    """Annual view of native money amounts, not a new cash-event schema.

    Scalar.reference_period retains the supplied source/reference period;
    normalized service coverage is explicit and is not a dated cash period.
    Projection to native Cost requires its existing event/party/period fields
    and native validation/admission. No Cost is manufactured here.
    """
    baseline: object  # native.Scalar, gross total for declared coverage
    programme: object  # native.Scalar, same explicit MoneyBasis
    money_basis: object  # native.MoneyBasis
    money_bridge: object  # native.Reference, energy/OM frozen-basis reconciliation
    baseline_coverage: object  # native.Reference; Q remains incomplete
    programme_coverage: object
    baseline_inclusions: tuple
    programme_inclusions: tuple
    household_id: str
    scope_ref: str
    year_policy_id: str


def integrate_annual_om(result, native, inputs):
    r=dict(result)
    missing=[]
    view={'status':'INCOMPLETE_ANNUAL_OM','baseline_gross_HUF':None,
          'programme_gross_HUF':None,'delta_programme_minus_baseline_HUF_exact':None,
          'money_basis':None,'normalized_policy_id':ACCEPTED_POLICY['id'],
          'settlement_dates_required_for_this_annual_view':False,
          'new_native_Cost_events':0,'evidence_adoption':False,
          'scope':'Non-energy O&M annual input view only; no native cash-event issuance',
          'input_records':None,'input_records_sha256':None,
          'classified_components':None}
    if inputs is None:
        missing=['baseline gross annual O&M','programme gross annual O&M',
                 'explicit shared money basis and bridge','both annual coverage references']
    else:
        if not isinstance(inputs,AnnualOMInputs):
            raise ReferenceError('Annual O&M view must use AnnualOMInputs with native records')
        _identity(inputs.household_id,'household_id')
        _identity(inputs.scope_ref,'scope_ref')
        if inputs.household_id!='SCN-MODEL-HH1':
            raise ReferenceError('Explicit matching household and O&M scope required')
        if inputs.year_policy_id!=ACCEPTED_POLICY['id']:
            raise ReferenceError('O&M normalized-year scope mismatch')
        basis=inputs.money_basis
        if not isinstance(basis,native.MoneyBasis):
            raise ReferenceError('Native MoneyBasis required; funding rule facts are not O&M amounts')
        if (basis.currency!='HUF' or basis.nominal_real!='NOMINAL' or
                type(basis.price_date) is not date or basis.price_date.year!=2026 or
                not isinstance(basis.basis_id,str) or not basis.basis_id.strip()):
            raise ReferenceError('Explicit frozen2026 nominal HUF basis required; no implicit conversion')
        _identity(basis.basis_id,'money basis')
        refs=[basis.convention,inputs.money_bridge,inputs.baseline_coverage,inputs.programme_coverage]
        for name,ref in zip(['money convention','money bridge','baseline coverage','programme coverage'],refs):
            if not isinstance(ref,native.Reference) or ref.kind=='SYNTHETIC_WITNESS':
                raise ReferenceError('Native non-synthetic Reference required for '+name)
            native.Reference(**{f.name:getattr(ref,f.name) for f in dataclasses.fields(ref)})
            if ref.ref is not None:_identity(ref.ref,name)
            if ref.kind=='Q':missing.append(name)
        classifications={}
        for leg,amount,inclusions in [('baseline',inputs.baseline,inputs.baseline_inclusions),
                                      ('programme',inputs.programme,inputs.programme_inclusions)]:
            if not isinstance(amount,native.Scalar):
                raise ReferenceError('Native Scalar required for '+leg)
            # Reuse its own validation; no second number/provenance convention.
            native.Scalar(**{f.name:getattr(amount,f.name) for f in dataclasses.fields(amount)})
            if amount.unit!='HUF' or amount.basis_id!=basis.basis_id:
                raise ReferenceError('Both O&M legs must use exactly the same explicit money basis')
            if amount.value is not None and amount.value<0:
                raise ReferenceError('Gross annual O&M is nonnegative; difference may be signed')
            classifications[leg]=_components(inclusions)
            for identifier in (*amount.source_ids,amount.scenario_ref,amount.admission_ref):
                if identifier is not None:_identity(identifier,leg+' provenance')
            view[leg+'_gross_HUF']=None if amount.value is None else str(amount.value)
            if amount.value is None:missing.append(leg+' gross annual O&M')
        view['money_basis']={'basis_id':basis.basis_id,'currency':basis.currency,
                             'nominal_real':basis.nominal_real,'price_date':basis.price_date.isoformat()}
        view['scope_ref']=inputs.scope_ref
        view['coverage']={'baseline':list(inputs.baseline_inclusions),'programme':list(inputs.programme_inclusions)}
        view['classified_components']=classifications
        view['input_records']=_encode_record(inputs)
        view['input_records_sha256']=hashlib.sha256(json.dumps(
            view['input_records'],sort_keys=True,separators=(',',':'),ensure_ascii=True,
            allow_nan=False).encode('utf-8')).hexdigest()
        if not missing:
            delta=Fraction(inputs.programme.value)-Fraction(inputs.baseline.value)
            view['delta_programme_minus_baseline_HUF_exact']=str(delta)
            view['status']='ANNUAL_OM_PARAMETER_INPUTS_AVAILABLE'
    if not r['temporal_policy_applied']:
        missing.append('approved normalized temporal binding')
        view['delta_programme_minus_baseline_HUF_exact']=None
        view['status']='INCOMPLETE_TEMPORAL_BINDING'
    view['missing']=missing
    r['annual_om']=view
    r['full_operating_balance']=None
    r['dated_cashflow_status']='UNFULFILLED_EXPLICIT_NATIVE_EVENT_AND_SETTLEMENT_BINDING_REQUIRED'
    return r


def energy_minus_om_component(result,u):
    """Scoped subtotal only; unknown auxiliary/cash-flow inputs are not zero."""
    om=result['annual_om']
    if om['status']!='ANNUAL_OM_PARAMETER_INPUTS_AVAILABLE':
        raise ReferenceError('Annual O&M input or coverage/basis remains incomplete')
    snapshot=om.get('input_records')
    digest=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':'),
                                   ensure_ascii=True,allow_nan=False).encode('utf-8')).hexdigest()
    if digest!=om.get('input_records_sha256'):
        raise ReferenceError('Returned O&M input provenance identity changed')
    expected=(Fraction(Decimal(snapshot['programme']['value']['__decimal__']))-
              Fraction(Decimal(snapshot['baseline']['value']['__decimal__'])))
    if expected!=Fraction(om['delta_programme_minus_baseline_HUF_exact']):
        raise ReferenceError('O&M difference no longer matches returned native input records')
    amount=component_balance(result,u)-Fraction(om['delta_programme_minus_baseline_HUF_exact'])
    return {'HUF_exact':str(amount),'scope':'Energy minus declared non-energy O&M component only',
            'full_operating_balance':None,'external_auxiliary_delta':None,
            'annual_economic_cashflow':None,'ROI':None,'native_cash_events':0}
