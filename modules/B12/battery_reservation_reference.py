"""B12 reference-household consumer; native B07 executes all battery physics.

Wholesale prices are a retrospective control signal, not a retail tariff.
There is no state activation or export. The original no-battery input is read-only.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone, time
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo
import csv, hashlib, io, math, json

from modules.B07 import discharge_equivalent_reference as native
from modules.B07 import shared_use_schedule_contract as shared
from modules.B07.engine import compute_household_balance
from modules.B04 import wholesale_reference as wholesale, engine as tariff
from modules.B12 import a1_reference_response as a1

ROOT=Path(__file__).resolve().parents[2]
UTC=timezone.utc
LOCAL=ZoneInfo('Europe/Budapest')
START=datetime(2025,1,1,tzinfo=UTC)
END=datetime(2026,1,1,tzinfo=UTC)
SCENARIO='SCN-B07-E2-20PCT-RESERVATION-NO-ACTIVATION-20261026'
INITIAL=1.5144
PROTECTED=1.5144
H,S='SCN-MODEL-HH1','SCN-NETWORK-RESERVATION-ACTOR'
SERVICE='SCN-RESERVATION-ONLY-NO-ACTIVATION'
DEFAULT_HOUSEHOLD='HOUSEHOLD_16_22_LOAD_LIMIT'
EVENING_HOUSEHOLD='HOUSEHOLD_18_22_MAX_1KW'
CAPACITY10_HOUSEHOLD='CAPACITY_10KWH_20PCT_18_22_MAX_1_5KW'
EVENING_PRIORITY='CAPACITY_10KWH_20PCT_18_22_MAX_1_5KW_HOUSEHOLD_PRIORITY'
WINTER_PRIORITY='CAPACITY_10KWH_20PCT_DJF_15_22_OTHER_18_22_MAX_1_5KW_PRIORITY'
IDENTICAL_HP='TWO_IDENTICAL_BASE_PLUS_HP'
MIXED_HP_BASE='HH1_BASE_PLUS_HP_HH2_BASE_ONLY'
ONE_SIGNAL='SCN_ONE_PREDECLARED_EVENT_20250103_10_11_BUDAPEST'
THREE_SIGNALS='SCN_THREE_PREDECLARED_EVENTS_20250103_05_10_11_BUDAPEST'
THREE_SIGNALS_FULL_BLOCK=THREE_SIGNALS+':PREVIOUS_COMPLETE_DJF_15_22_BUDGET'
THREE_SIGNALS_TWO_BLOCKS=THREE_SIGNALS+':MAX_TWO_PREVIOUS_COMPLETE_DJF_15_22_BLOCKS'

@dataclass(frozen=True)
class Signal:
    signal_id: str
    issued_at: datetime
    valid_from: datetime
    valid_until: datetime
    truth: str = 'SCN'

def approved_signal():
    return Signal(ONE_SIGNAL,datetime(2025,1,3,8,tzinfo=UTC),
                  datetime(2025,1,3,9,tzinfo=UTC),datetime(2025,1,3,10,tzinfo=UTC))

def _validated_signal_schedule(signals):
    """Reject ambiguous schedules before any native execution; never merge events."""
    signals=tuple(signals);seen=set();previous_end=None
    for sig in signals:
        _require(isinstance(sig,Signal) and sig.truth=='SCN','Explicit SCN Signal required')
        _require(isinstance(sig.signal_id,str) and bool(sig.signal_id.strip()) and sig.signal_id not in seen,
                 'Duplicate or empty signal identity')
        clocks=(sig.issued_at,sig.valid_from,sig.valid_until)
        _require(all(isinstance(t,datetime) and t.tzinfo is not None and t.utcoffset() is not None for t in clocks),
                 'Aware signal clocks required')
        _require(sig.issued_at<=sig.valid_from and sig.valid_until-sig.valid_from==timedelta(hours=1)
                 and sig.valid_from.minute==sig.valid_from.second==sig.valid_from.microsecond==0,
                 'One whole physical hour issued before validity required')
        _require(previous_end is None or sig.valid_from>=previous_end,'Unordered or overlapping signal schedule')
        previous_end=sig.valid_until;seen.add(sig.signal_id)
    return signals

def approved_signals(signal_case):
    """Only the two separately approved, frozen calendar schedules are executable."""
    _require(signal_case in (None,ONE_SIGNAL,THREE_SIGNALS,THREE_SIGNALS_FULL_BLOCK,THREE_SIGNALS_TWO_BLOCKS),'Unknown signal schedule')
    if signal_case is None:return ()
    if signal_case==ONE_SIGNAL:return _validated_signal_schedule((approved_signal(),))
    return _validated_signal_schedule(tuple(
        Signal(THREE_SIGNALS+':202501'+str(day).zfill(2),datetime(2025,1,day,8,tzinfo=UTC),
               datetime(2025,1,day,9,tzinfo=UTC),datetime(2025,1,day,10,tzinfo=UTC))
        for day in (3,4,5)))

def _signal_active(signal,load):
    if not isinstance(signal,Signal) or signal.truth!='SCN':return False
    clocks=(signal.issued_at,signal.valid_from,signal.valid_until,load.start,load.end)
    if any(not isinstance(t,datetime) or t.tzinfo is None or t.utcoffset() is None for t in clocks):return False
    return (bool(signal.signal_id) and signal.issued_at<=load.start
            and signal.valid_from<=load.start<load.end<=signal.valid_until
            and load.end-load.start==timedelta(hours=1))

def _signal_policy(signal_case,household_policy,profile_case):
    _require(signal_case in (None,ONE_SIGNAL,THREE_SIGNALS,THREE_SIGNALS_FULL_BLOCK,THREE_SIGNALS_TWO_BLOCKS),'Only exact approved SCN signal cases are supported')
    if signal_case is not None:
        _require(household_policy==WINTER_PRIORITY and profile_case==MIXED_HP_BASE,
                 'Signal case requires the approved winter mixed pair')

def _ceil_fraction(value):
    result=float(value)
    return math.nextafter(result,math.inf) if Fraction.from_float(result)<value else result

def _evening_budget(ref,history,decision,*,start_hour=18):
    """Most recent closed local start_hour-22 own load, never battery delivery.

    Stock is discharge-equivalent DC: use only the discharge inverse curve.
    No second cycle/charging loss, safety factor or synthetic missing value.
    """
    _require(start_hour in (15,18),'Only approved history block starts supported')
    def missing(reason):return {'status':'Q','reason':reason,'estimated_dc_kwh':None,'floor_kwh':None}
    if not isinstance(decision,datetime) or decision.tzinfo is None:return missing('INVALID_DECISION_CLOCK')
    local=decision.astimezone(LOCAL);date=local.date()
    if local<datetime.combine(date,time(22),tzinfo=LOCAL):date-=timedelta(days=1)
    starts=[datetime.combine(date,time(h),tzinfo=LOCAL).astimezone(UTC) for h in range(start_hour,22)]
    found={}
    for row in history:
        if type(row) is not LoadHour:return missing('INVALID_HISTORY_RECORD')
        if any(not isinstance(t,datetime) or t.tzinfo is None or t.utcoffset() is None for t in (row.start,row.end)):
            return missing('INVALID_HISTORY_CLOCK')
        if row.end>decision:continue
        if row.start in starts:
            try:_inputs((row,),(Fraction(0),))
            except (ValueError,TypeError):return missing('INVALID_EVENING_LOAD')
            if row.start in found:return missing('DUPLICATE_EVENING_HOUR')
            if row.end-row.start!=timedelta(hours=1):return missing('INVALID_EVENING_DURATION')
            found[row.start]=row
    if set(found)!=set(starts):return missing('INCOMPLETE_LAST_CLOSED_EVENING')
    parts=[];dc_exact=Fraction(0)
    for start in starts:
        row=found[start]
        try:own=Fraction(row.base_kw)+Fraction(row.hp_kw)
        except (ValueError,OverflowError,TypeError):return missing('INVALID_OWN_LOAD')
        if own<0:return missing('INVALID_OWN_LOAD')
        target=min(Fraction(3,2),own)
        if target==0:dc=0.
        else:
            ac=_ceil_fraction(target)
            if ac>ref.discharge_ac_source_limit_kw:return missing('UNSUPPORTED_DISCHARGE_SOURCE_LIMIT')
            try:dc=ref.discharge.point(ac)[0]
            except ValueError:return missing('UNSUPPORTED_DISCHARGE_CURVE_POINT')
            if not math.isfinite(dc) or dc<0:return missing('INVALID_DISCHARGE_CURVE_POINT')
        dc_exact+=Fraction.from_float(dc)
        parts.append({'start_utc':start.isoformat(),'end_utc':row.end.isoformat(),
                      'own_load_kw_exact':str(own),'capped_ac_kw_exact':str(target),'dc_requirement_kwh':dc})
    return {'status':'SCN_PERSISTENCE_ESTIMATE_NOT_GUARANTEE','reason':None,
            'decision_utc':decision.isoformat(),'source_local_date':date.isoformat(),
            'estimated_dc_kwh_exact_binary':str(dc_exact),'estimated_dc_kwh':_ceil_fraction(dc_exact),
            'floor_kwh':_ceil_fraction(Fraction(2)+dc_exact),'parts':parts}

def _two_block_budget(ref,history,decision):
    """Maximum of the last TWO complete local15-22 own blocks; never skip gaps."""
    latest=_evening_budget(ref,history,decision,start_hour=15)
    blocks=[latest]
    if latest['floor_kwh'] is not None:
        date=datetime.fromisoformat(latest['source_local_date']).date()-timedelta(days=1)
        previous_close=datetime.combine(date,time(22),tzinfo=LOCAL).astimezone(UTC)
        blocks.append(_evening_budget(ref,history,previous_close,start_hour=15))
    if len(blocks)!=2 or any(b['floor_kwh'] is None for b in blocks):
        return {'status':'Q','reason':'INCOMPLETE_OR_INVALID_TWO_BLOCK_HISTORY','blocks':blocks,
                'estimated_dc_kwh':None,'floor_kwh':None}
    # Compare the exact sum BEFORE the existing conservative binary projection.
    selected=max(blocks,key=lambda b:Fraction(b['estimated_dc_kwh_exact_binary']))
    return {**selected,'status':'SCN_TWO_BLOCK_MAXIMUM_NOT_GUARANTEE','decision_utc':decision.isoformat(),'blocks':blocks,
            'selected_source_local_date':selected['source_local_date'],
            'selection_rule':'Larger exact DC requirement; latest block wins an exact tie'}

def _scenario(policy):
    _require(policy in (DEFAULT_HOUSEHOLD,EVENING_HOUSEHOLD,CAPACITY10_HOUSEHOLD,EVENING_PRIORITY,WINTER_PRIORITY),'Explicit supported household policy required')
    return SCENARIO if policy==DEFAULT_HOUSEHOLD else SCENARIO+':'+policy

@dataclass(frozen=True)
class LoadHour:
    start: datetime
    end: datetime
    base_kw: Fraction
    hp_kw: Fraction

def _require(ok,message):
    if not ok:raise ValueError(message)

def reference(*,household_policy=DEFAULT_HOUSEHOLD):
    _scenario(household_policy)
    if household_policy in (CAPACITY10_HOUSEHOLD,EVENING_PRIORITY,WINTER_PRIORITY):return native.capacity_sensitivity_reference()
    return native.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)

def initial_and_protected(policy):
    _scenario(policy)
    return (2.,2.) if policy in (CAPACITY10_HOUSEHOLD,EVENING_PRIORITY,WINTER_PRIORITY) else (INITIAL,PROTECTED)

def load_profile():
    qualified=a1.load_reference(ROOT)
    path=ROOT/'data/processed/b12/a1_minimal5/REFERENCE_HOURLY_5.csv'
    raw=path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest()=='24b26302b04cd6fc3da2f2b99d5adf8428dfcc0e9996422d6dadcf6e5680a047','Accepted hourly profile drift')
    rows=[]
    for row in csv.DictReader(io.StringIO(raw.decode('utf-8'),newline='')):
        rows.append(LoadHour(datetime.fromisoformat(row['interval_start_utc']),datetime.fromisoformat(row['interval_end_utc']),
            Fraction(Decimal(row['common_base_reference_kw'])),Fraction(Decimal(row['unit_incremental_W55_device_reference_kw']))))
    _require(len(rows)==8760,'8760 original load rows required')
    return tuple(rows),qualified,{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}

def _inputs(loads,prices):
    _require(bool(loads) and len(loads)==len(prices),'Aligned nonempty loads/prices required')
    for i,(load,price) in enumerate(zip(loads,prices)):
        _require(type(load) is LoadHour,'Explicit load records required')
        _require(load.start.utcoffset()==load.end.utcoffset()==timedelta(0),'UTC load required')
        _require(load.end-load.start==timedelta(hours=1) and (i==0 or loads[i-1].end==load.start),'Consecutive physical hours required')
        _require(load.base_kw>=0 and load.hp_kw>=0,'Nonnegative exogenous loads required')
        _require(type(price) is Fraction,'Exact finite price Fraction required, negative prices allowed')

def _hour_record(ref,load,price,past_median,household_policy,x,floor,*,charge_permitted=True,charge_budget_kw=None,extra_self_use=False):
    """One native controller step; coordinator may withhold only charging."""
    local=load.start.astimezone(LOCAL);hour=local.hour
    _require(type(extra_self_use) is bool and (not extra_self_use or household_policy==WINTER_PRIORITY),
             'Extra self-use is only the explicit winter SCN exception')
    winter=household_policy==WINTER_PRIORITY and local.month in (12,1,2)
    charge=(past_median is not None and price<past_median and (0<=hour<6 or 10<=hour<16))
    if winter and hour==15:charge=False
    discharge=(past_median is not None and (household_policy in (EVENING_PRIORITY,WINTER_PRIORITY) or price>past_median)
               and (extra_self_use or (15 if winter else 16 if household_policy==DEFAULT_HOUSEHOLD else 18)<=hour<22))
    wanted_c=ref.charge.point(ref.charge.upper)[0] if charge else 0.
    wanted_d=float(load.base_kw+load.hp_kw) if discharge else 0.
    if household_policy==EVENING_HOUSEHOLD:wanted_d=min(wanted_d,1.)
    if household_policy in (CAPACITY10_HOUSEHOLD,EVENING_PRIORITY,WINTER_PRIORITY):wanted_d=min(wanted_d,1.5)
    if charge_budget_kw is not None:
        _require(type(charge_budget_kw) in (int,float) and math.isfinite(charge_budget_kw) and charge_budget_kw>=0,
                 "Finite nonnegative charge budget required")
    c,d=wanted_c if charge_permitted else 0.,0.
    if charge_budget_kw is not None:c=min(c,charge_budget_kw)
    if discharge:
        # Restrict the native curve to free inventory, never borrow pool R.
        cap=max(0.,math.nextafter(wanted_d,0.))
        d=ref.discharge.largest_output(max(0.,x-floor),min(cap,ref.discharge_ac_source_limit_kw)) or 0.
        c=0.
    trial=native.step(ref,native.Inventory(x),charge_ac_kw=c,discharge_ac_kw=d,hours=1.,idle_convention=native.SCN_IDLE_ZERO)
    for _ in range(16):
        if trial['x_end_kwh']>=floor or not d:break
        d=math.nextafter(d,0.)
        if d<ref.discharge.lower:d=0.
        trial=native.step(ref,native.Inventory(x),charge_ac_kw=0.,discharge_ac_kw=d,hours=1.,idle_convention=native.SCN_IDLE_ZERO)
    _require(trial['x_end_kwh']>=floor,'Conservative protected-pool clipping failed')
    if trial['admitted_charge_ac_kwh']==trial['delivered_discharge_ac_kwh']==0.:
        # A declined unsupported request is recorded, but is not an active
        # command/duty cycle. This interval receives AC standby once.
        c=d=0.
        trial=native.step(ref,native.Inventory(x),charge_ac_kw=0.,discharge_ac_kw=0.,hours=1.,idle_convention=native.SCN_IDLE_ZERO)
    _require(not (c and d),'Opposing commands')
    _require(trial['delivered_discharge_ac_kwh']<=float(load.base_kw+load.hp_kw),'No-export controller exceeded load')
    return {'load':load,'charge_kw':c,'discharge_kw':d,'native':trial,
        'control_price_exact':str(price),'previous24_median_exact':None if past_median is None else str(past_median),
        'warmup_hold':past_median is None,'controller_requested_charge_kw':wanted_c,
        'controller_requested_discharge_kw':wanted_d,
        'unserved_controller_discharge_kWh':max(0.,wanted_d-trial['delivered_discharge_ac_kwh'])}


def schedules(loads,prices,*,household_policy=DEFAULT_HOUSEHOLD):
    """Generate both supplied schedules with native feasibility, no future reads.

    Low-level explicit SCN input function, not source admission. run_annual binds
    the qualified wholesale producer and profile before invoking this function.
    The first 24 observations are a hold-only warmup; no invented prior price.
    """
    _scenario(household_policy)
    loads,prices=tuple(loads),tuple(prices)
    _inputs(loads,prices)
    ref=reference(household_policy=household_policy); history=deque(maxlen=24)
    initial,protected=initial_and_protected(household_policy)
    inventories={'household_only':initial,'reserved':initial}
    output={key:[] for key in inventories}
    for index,(load,price) in enumerate(zip(loads,prices)):
        past_median=median(history) if len(history)==24 else None
        for leg in inventories:
            item=_hour_record(ref,load,price,past_median,household_policy,
                inventories[leg],protected if leg=='reserved' else 0.)
            inventories[leg]=item['native']['x_end_kwh']
            output[leg].append(item)
        history.append(price) # Current and future prices excluded from median.
    return ref,output

def _known(x,scenario=SCENARIO):return shared.Term('SCN',x,scenario)
def _q(reason):return shared.Term('Q',None,reason)
def _qualified(scenario=SCENARIO):return shared.Term('SCN',None,scenario)
def _seal(x):return replace(x,content_sha256=shared.content_digest(x))

def build_case(ref,records,*,household_policy=DEFAULT_HOUSEHOLD,entity_id=None,coordination=None,profile_case=IDENTICAL_HP,signal_case=None):
    """Translate generated requests into existing shared-use money/rights schema."""
    scenario=_scenario(household_policy)
    _signal_policy(signal_case,household_policy,profile_case)
    _require(profile_case in (IDENTICAL_HP,MIXED_HP_BASE),'Explicit supported profile assignment required')
    if profile_case==MIXED_HP_BASE:
        _require(entity_id in ('HH1','HH2') and coordination=='SHARED_BUDGET','Mixed profile requires the explicit shared pair')
        scenario+=':'+profile_case
    if signal_case is not None:scenario+=':'+signal_case
    _require(entity_id in (None,'HH1','HH2') and coordination in (None,'INDEPENDENT','COORDINATED','SHARED_BUDGET'),
             'Exact two-household identity/scope required')
    _require((entity_id is None)==(coordination is None),'Entity and coordination scope must be paired')
    if entity_id is not None:
        _require(household_policy in (EVENING_PRIORITY,WINTER_PRIORITY),'Pair uses only explicit approved priority policy')
        scenario+=':TWO_HOUSEHOLDS:'+entity_id+':'+coordination
    hh=H if entity_id is None else 'SCN-COORD-'+entity_id
    network=S if entity_id is None else S+':'+entity_id
    connection='SCN-HH1-A1-CONNECTION' if entity_id is None else 'SCN-COORD-'+entity_id+'-CONNECTION'
    initial,protected=initial_and_protected(household_policy)
    # Preserve all existing agreement/source-use identities. Only the new
    # capacity-transfer SCN introduces a new Term qualification lineage.
    term_scenario=scenario if household_policy in (CAPACITY10_HOUSEHOLD,EVENING_PRIORITY,WINTER_PRIORITY) else SCENARIO
    known=lambda x:_known(x,term_scenario)
    qualified=lambda:_qualified(term_scenario)
    expected=reference(household_policy=household_policy)
    _require(ref==expected,'Household policy and exact reference configuration differ')
    loads=[x['load'] for x in records['reserved']]
    start,end=loads[0].start.isoformat(),loads[-1].end.isoformat();hours=len(loads)
    device=native.CAPACITY_SCN_ID if household_policy in (CAPACITY10_HOUSEHOLD,EVENING_PRIORITY,WINTER_PRIORITY) else 'SAX_2026_A1_V23.50'
    identity=shared.Identity(device,connection,hh,network,shared.REFERENCE,
        'DC_DISCHARGE_EQUIVALENT_CAPACITY_KWH',ref.capacity_dc_output_equiv_kwh,shared.digest(ref))
    ident=shared.digest(identity)
    # A finite physical throughput ceiling, not a chosen commercial entitlement.
    ceiling=initial+ref.battery_dc_cycle_efficiency*ref.charge.upper*hours
    budgets=(shared.Budget('B:H',hh,start,end,known(0.),'ATTRIBUTED_CHARGE_CREDIT'),
             shared.Budget('B:S',network,start,end,known(protected),'NONE'))
    right_h=shared.RightsWindow('R:H',hh,start,end,start,end,known(ref.charge.point(ref.charge.upper)[0]),
        known(min(ref.discharge.upper,ref.discharge_ac_source_limit_kw)),known(ceiling),known(float(hours)),'B:H')
    # No invented state power or activation duration; kWh reservation is separate.
    right_s=shared.RightsWindow('R:S',network,start,end,start,end,known(0.),_q('No state dispatch power selected'),
        known(protected),_q('No state activation duration selected'),'B:S')
    agreement=_seal(shared.Agreement('SCN-20PCT-RESERVATION','1','',ident,shared.PROTECTED,known(protected),
        known(0.),budgets,(right_h,right_s),(),qualified()))
    def leg(key,contract):
        intervals=[];idle=[]
        for n,item in enumerate(records[key]):
            load=item['load'];r=item['native'];c=r['admitted_charge_dc_kwh'];d=r['admitted_discharge_dc_kwh']
            acin=r['admitted_charge_ac_kwh'];acout=r['delivered_discharge_ac_kwh']
            reqs=(shared.Request(hh,'HOUSEHOLD_SELF_USE',item['charge_kw'],item['discharge_kw']),shared.Request(network,SERVICE,0.,0.))
            alloc=(shared.Allocation(hh,'HOUSEHOLD_SELF_USE',acin,acout,ref.battery_dc_cycle_efficiency*c,d,
                acin-c,(1-ref.battery_dc_cycle_efficiency)*c,d-acout),shared.Allocation(network,SERVICE,0.,0.,0.,0.,0.,0.,0.))
            iid=f'h{n:04d}'
            if not item['charge_kw'] and not item['discharge_kw']:idle.append(iid)
            intervals.append(shared.Interval(iid,key+':'+iid,ident,load.start.isoformat(),load.end.isoformat(),1.,
                (float(load.base_kw),float(load.hp_kw),0.),reqs,alloc))
        idle_account=shared.IdleAccounting(tuple(idle),float(len(idle)),shared.Unknown('Financial actor allocation of standby not selected'),False)
        return shared.Leg(key,ident,initial,contract,tuple(intervals),idle_account)
    b=leg('household_only','HOUSEHOLD_ONLY');actual=leg('reserved',agreement)
    descriptor=shared.Baseline(scenario+':baseline','Approved causal price-median SCN controller',
        ('Winter household-only reference vs shared reserved signal response; not reserve-only causality or grid activation'
         if signal_case is not None else 'Reservation agreement vs household-only, not grid activation'),
        '1',shared.AGREEMENT,shared.digest(b),qualified())
    case=shared.SharedUseCase(scenario,shared.VERSION,'','SCN',identity,ref,tuple(native.PINS.items()),scenario,
        native.SCN_IDLE_ZERO,shared.AGREEMENT,SERVICE,descriptor,b,actual,_q('Real connection import rating not selected'),
        known(0.),tuple(shared.Permission(op,'Q','No actual-site operation permission inferred') for op in shared.OPERATIONS),
        shared.FinancialInputs(tuple((key,_q('No monetary allocation selected')) for key in shared.MONEY_FIELDS),
            shared.Unknown('Complete household protection/finance remains Q')),(), 'SUPPLIED_REBOUND_HORIZON',1e-9,1e-12)
    return _seal(case)

def evaluate(loads,prices,*,household_policy=DEFAULT_HOUSEHOLD):
    ref,records=schedules(loads,prices,household_policy=household_policy)
    return _evaluate_records(ref,records,household_policy=household_policy)

def _evaluate_records(ref,records,*,household_policy,entity_id=None,coordination=None,profile_case=IDENTICAL_HP,signal_case=None):
    case=build_case(ref,records,household_policy=household_policy,entity_id=entity_id,coordination=coordination,profile_case=profile_case,signal_case=signal_case)
    audit=shared.evaluate_shared_use(case)
    for key,items in records.items():
        authoritative=audit['legs'][key]
        _require(authoritative['physical_status']=='PASS_SCN' and authoritative['allocation_status']=='PASS_SCN','Native audit mismatch')
        _require(authoritative['rights']['status']!='FAIL','Reservation rights failed')
        for planned,observed in zip(items,authoritative['rows']):
            for a,b in [('x_end_kwh','inventory_after_kwh'),('admitted_charge_ac_kwh','charge_ac_kwh'),('delivered_discharge_ac_kwh','discharge_ac_kwh')]:
                _require(planned['native'][a]==observed[b],'Controller/replay mismatch')
    output={'scenario':case.scenario_reference,'case':case,'audit':audit,'controller_records':records,
            'retail_pricing':None,'wholesale_valuation':None,'ROI':None,'actual_activation':False,
            'idle_convention':native.SCN_IDLE_ZERO,'warmup_policy':'HOLD_FIRST_24_PHYSICAL_HOURS_NO_INVENTED_PRICES',
            'terminal_policy':'REPORT_EACH_ACTUAL_ENDING_INVENTORY_NO_RESET_OR_FREE_CREDIT',
            'no_lookahead_scope':'Current price vs previous24closed prices; retrospective revision vintage, not verified live backtest'}
    if household_policy in (CAPACITY10_HOUSEHOLD,EVENING_PRIORITY,WINTER_PRIORITY):
        output['parameter_transfer']={'truth':'SCN_OWNER_APPROVED_NOT_PRODUCT_OBSERVATION',
            'identity':native.CAPACITY_SCN_ID,'source_capacity_kWh_DC_discharged_usable':7.572,
            'scenario_capacity_kWh_DC_discharged_usable':10.,'initial_and_protected_kWh':2.,
            'unchanged_assumed_parameters':['Converter curves and supported power ranges','Battery DC cycle efficiency0.958183','Source power limit','4.07W AC idle proxy'],
            'proportional_scaling':False,'cell_self_discharge':'Explicit approved zero SCN',
            'actual_product_10kWh_validated':False}
    return output

def annual(source_paths,*,household_policy=DEFAULT_HOUSEHOLD):
    """Real annual entry requires every pinned wholesale original; no substitute."""
    prices=wholesale.read_wholesale_reference(source_paths,window='utc2025')
    loads,qualified,profile_provenance=load_profile()
    _require(len(prices.records)==8760 and all((r.start_utc,r.end_utc)==(x.start,x.end) for r,x in zip(prices.records,loads)),
             'Exact source-price/load UTC2025 join required')
    result=evaluate(loads,tuple(r.price_eur_per_mwh for r in prices.records),household_policy=household_policy)
    result['price_provenance']=prices.evidence
    result['wholesale_reference']=prices
    result['profile_provenance']=profile_provenance
    result['A1_reference']=qualified
    return result


def coordinated_pair(loads,prices):
    """Exactly two explicit SCN clones, not a population-weight inference."""
    return _pair_from_independent(evaluate(loads,prices,household_policy=EVENING_PRIORITY))


def _pair_from_independent(independent):
    policy=EVENING_PRIORITY
    ref=independent['case'].executor
    base=independent['controller_records']
    names=('HH1','HH2');state={name:2. for name in names};records={name:[] for name in names}
    turn=0;selection=[]
    for i,original in enumerate(base['reserved']):
        load=original['load'];price=Fraction(original['control_price_exact'])
        med=original['previous24_median_exact'];med=None if med is None else Fraction(med)
        # Pure native trials do not advance state. A full/unsupported candidate
        # is skipped; never split this physical hour into hidden duty cycles.
        trial={name:_hour_record(ref,load,price,med,policy,state[name],2.) for name in names}
        eligible=[name for name in names if trial[name]['native']['admitted_charge_ac_kwh']>0.]
        chosen=next((names[(turn+j)%2] for j in range(2) if names[(turn+j)%2] in eligible),None)
        before=names[turn]
        if chosen is not None:turn=1-names.index(chosen)
        for name in names:
            item=trial[name] if chosen==name else _hour_record(ref,load,price,med,policy,state[name],2.,charge_permitted=False)
            state[name]=item['native']['x_end_kwh'];records[name].append(item)
        _require(sum(records[name][-1]['native']['admitted_charge_ac_kwh']>0 for name in names)<=1,'Concurrent coordinated charging')
        selection.append({'index':i,'start_utc':load.start.isoformat(),'turn_before':before,
            'physically_chargeable':eligible,'selected':chosen,'turn_after':names[turn]})
    output={'scope':'TWO_EXPLICIT_HOUSEHOLDS_STAGGERED_CHARGE_SCN','source_baseline':independent,
        'independent':{},'coordinated':{},'selection':selection,
        'rule':'HH1 first; alternate after actual admitted charge; skip full/unsupported; no turn change without admission',
        'battery_charge_cap_kw':ref.charge.point(ref.charge.upper)[0],
        'feeder_capacity_kw':None,'national_result':None,'actual_activation':False,'ROI':None,
        'internal_audit_scope':'Each entity uses native reservation-vs-household-only audit; the main controller comparison is independent vs coordinated reserved schedules'}
    for name in names:
        for mode in ('independent','coordinated'):
            supplied={'household_only':base['household_only'],
                      'reserved':base['reserved'] if mode=='independent' else records[name]}
            result=_evaluate_records(ref,supplied,household_policy=policy,entity_id=name,coordination=mode.upper())
            for key in ('wholesale_reference','price_provenance','profile_provenance','A1_reference'):
                if key in independent:result[key]=independent[key]
            output[mode][name]=result
    return output


def annual_coordinated_pair(source_paths):
    """Same exact source-qualified UTC2025 panel as the accepted single case."""
    return _pair_from_independent(annual(source_paths,household_policy=EVENING_PRIORITY))

def priced_summary(result,parameter_sheet_bytes):
    """Accepted A1 replay and separate EUR energy-only valuation; no cash events."""
    _require(hashlib.sha256(parameter_sheet_bytes).hexdigest()=='8520ac4b3c93c1b2934ce3a5c6b6ba259996a92f99e9e37a5ebbea53660d402c',
             'Exact accepted day-proportional parameter sheet required')
    params=json.loads(parameter_sheet_bytes.decode('utf-8'))
    rows=result['controller_records']
    _require(all(len(items)==8760 and items[0]['load'].start==START and items[-1]['load'].end==END for items in rows.values()),
             'Annual pricing requires exact UTC2025, not test fixture')
    def dec(value):
        f=Fraction(value);return Decimal(f.numerator)/Decimal(f.denominator)
    summary={}
    with localcontext() as ctx:
        ctx.prec=50;ctx.rounding=ROUND_HALF_EVEN
        for name,items in rows.items():
            audit=result['audit']['legs'][name]
            energy={p['id']:Fraction(0) for p in params['windows']}
            market=Fraction(0);standby=Fraction(0);imports=Fraction(0);no_battery=Fraction(0);valued_imports=[]
            for item in items:
                load=item['load'];r=item['native']
                idle=item['charge_kw']==item['discharge_kw']==0.
                debit=Fraction(407,100000) if idle else Fraction(0) # 4.07W x 1h, explicit SCN allocation
                q=load.base_kw+load.hp_kw+Fraction(Decimal(str(r['admitted_charge_ac_kwh'])))-Fraction(Decimal(str(r['delivered_discharge_ac_kwh'])))+debit
                _require(q>=0,'Unexpected reference export')
                matched=[p for p in params['windows'] if datetime.fromisoformat(p['start_utc'])<=load.start<datetime.fromisoformat(p['end_utc_exclusive'])]
                _require(len(matched)==1,'Each hour requires exactly one billing portion')
                energy[matched[0]['id']]+=q;imports+=q;standby+=debit
                no_battery+=load.base_kw+load.hp_kw
                market+=q*Fraction(item['control_price_exact'])/1000
                valued_imports.append(wholesale.ImportedEnergy(load.start,load.end,q/1000))
            canonical_market=wholesale._value(result['wholesale_reference'],valued_imports,convention=wholesale.CONVENTION,
                within_hour_profile='FLAT',energy_unit='MWh',profile_id=result.get('scenario',SCENARIO)+':'+name)
            value=canonical_market['wholesale_reference_eur']
            _require(market==Fraction(int(value['numerator']),int(value['denominator'])),'Wholesale reference replay mismatch')
            _require(abs(float(standby)-audit['idle_ac']['ac_energy_debit_kwh'])<=1e-10,'Standby allocated more than once or wrong exposure')
            bills={}
            for p in params['windows']:
                bill=tariff.price_a1(dec(energy[p['id']]),dec(Fraction(p['q_allocation_kWh']['exact'])),
                    dec(Fraction(p['m_allocation_month']['exact'])),a1.AREA)
                bills[p['id']]={'import_kWh_exact':str(energy[p['id']]),'consumption_gross_HUF':str(bill.consumption_charge_huf),
                    'fixed_gross_HUF':str(bill.fixed_charge_huf),'total_gross_HUF':str(bill.total_huf)}
            summary[name]={'initial_dc_equivalent_kWh':audit['initial_inventory_kwh'],'terminal_dc_equivalent_kWh':audit['terminal_inventory_kwh'],
                'terminal_minus_initial_kWh':audit['terminal_minus_initial_kwh'],'native_active_totals':audit['totals'],
                'standby_AC_kWh_exact':str(standby),'total_meter_import_kWh_exact':str(imports),
                'no_battery_profile_kWh_exact':str(no_battery),'A1_portions':bills,
                'A1_total_gross_HUF':str(sum((Decimal(v['total_gross_HUF']) for v in bills.values()),Decimal(0))),
                'wholesale_EUR_exact':str(market),'wholesale_boundary':wholesale.CONVENTION,
                'wholesale_source_reference':canonical_market['reference_id'],
                'standby_hourly_allocation':'Explicit SCN4.07W on actual idle intervals; source aggregate is not all-state observation',
                'state_dispatched_kWh':0,'actual_legal_execution':False,'ROI':None}
    summary['comparison']={'foregone_household_discharge_kWh':result['audit']['response']['foregone_household_discharge_kwh'],
        'terminal_actual_minus_baseline_kWh':result['audit']['response']['actual_minus_baseline_terminal_kwh'],
        'A1_bill_difference_not_stock_adjusted_saving_HUF_exact':str(Fraction(Decimal(summary['reserved']['A1_total_gross_HUF']))-Fraction(Decimal(summary['household_only']['A1_total_gross_HUF']))),
        'net_benefit':None,'ROI':None,'note':'Different terminal stocks are retained; no free stock credit, no complete arbitrage or grid-service value.'}
    case=result.get('case')
    network=case.identity.state_actor_id if case else S
    available=[x['actors'][network]['available_before_kwh'] for x in result['audit']['legs']['reserved']['rights']['intervals']]
    target=case.actual_leg.agreement.initial_protected_kwh.value if case else PROTECTED
    capacity=case.identity.capacity_kwh if case else 7.572
    summary['reserved']['energy_reservation']={'target_dc_equivalent_kWh':target,'capacity_fraction':target/capacity,
        'minimum_available_dc_equivalent_kWh':min(available),'maximum_available_dc_equivalent_kWh':max(available),
        'hourly_available_capacity_fraction':[x/capacity for x in available],
        'conditional_only':'No activation, explicit zero cell self-discharge, initially filled protected pool; not a real availability guarantee or AC-kW commitment.'}
    return summary


def _remaining_charge_budget(cap,used):
    """Conservative binary64 subtraction, not a physical tolerance waiver."""
    available=cap-used
    while Fraction.from_float(available)+Fraction.from_float(used)>Fraction.from_float(cap):
        available=math.nextafter(available,0.)
    return available


def _shared_hour(ref,load,price,med,states,*,household_policy=EVENING_PRIORITY,household_loads=None):
    """Equal AC budgets; redistribute actually unused power, never inventory.

    Native constant-hour trials are pure. No subhour switching or future load.
    Lower present inventory, then HH1, breaks a single-support tie.
    """
    _require(household_policy in (EVENING_PRIORITY,WINTER_PRIORITY),'Explicit shared priority policy required')
    names=('HH1','HH2');policy=household_policy
    if household_loads is None:
        household_loads={name:load for name in names}
    else:
        _require(isinstance(household_loads,dict) and set(household_loads)==set(names),'Exactly two named household loads required')
        for item in household_loads.values():
            _inputs((item,),(price,))
            _require((item.start,item.end)==(load.start,load.end),'Household interval mismatch')
    cap=ref.charge.point(ref.charge.upper)[0]
    def trial(name,budget):
        return _hour_record(ref,household_loads[name],price,med,policy,states[name],2.,charge_budget_kw=budget)
    rows={n:trial(n,cap/2) for n in names}
    # Each reallocation consumes only the other's unused actual AC budget.
    # Two deterministic passes suffice for two members; no power extrapolation.
    order=sorted(names,key=lambda n:(states[n],n))
    for name in order:
        other=names[1-names.index(name)]
        available=_remaining_charge_budget(cap,rows[other]['native']['admitted_charge_ac_kwh'])
        rows[name]=trial(name,available)
    _require(sum((Fraction.from_float(rows[n]['native']['admitted_charge_ac_kwh']) for n in names),Fraction(0))<=Fraction.from_float(cap),
             'Shared AC charging budget exceeded')
    return rows


def _shared_pair_from_independent(independent,*,household_policy=EVENING_PRIORITY,profile_case=IDENTICAL_HP,signal_case=None):
    """Three matched local SCN arms; original alternating arm is unchanged."""
    _require(household_policy in (EVENING_PRIORITY,WINTER_PRIORITY),'Explicit shared priority policy required')
    _require(profile_case in (IDENTICAL_HP,MIXED_HP_BASE),'Explicit supported profile assignment required')
    _signal_policy(signal_case,household_policy,profile_case)
    out=(_pair_from_independent(independent) if household_policy==EVENING_PRIORITY and profile_case==IDENTICAL_HP else
         {'source_baseline':independent,'battery_charge_cap_kw':independent['case'].executor.charge.point(independent['case'].executor.charge.upper)[0]})
    ref=independent['case'].executor;names=('HH1','HH2')
    source_records={name:independent['controller_records'] for name in names}
    if profile_case==MIXED_HP_BASE:
        hh2_loads=tuple(replace(item['load'],hp_kw=Fraction(0)) for item in independent['controller_records']['reserved'])
        prices=tuple(Fraction(item['control_price_exact']) for item in independent['controller_records']['reserved'])
        hh2_ref,hh2_records=schedules(hh2_loads,prices,household_policy=household_policy)
        _require(hh2_ref==ref,'Mixed pair must use the same approved battery reference')
        source_records['HH2']=hh2_records
    states={n:2. for n in names};records={n:[] for n in names};selection=[]
    histories={n:[] for n in names};signal_notes=[]
    signals=approved_signals(signal_case);processed=set()
    for i,item in enumerate(independent['controller_records']['reserved']):
        load=item['load'];price=Fraction(item['control_price_exact'])
        med=item['previous24_median_exact'];med=None if med is None else Fraction(med)
        supplied_loads=None if profile_case==IDENTICAL_HP else {n:source_records[n]['reserved'][i]['load'] for n in names}
        before=dict(states)
        active=[sig for sig in signals if _signal_active(sig,load)]
        _require(len(active)<=1,'More than one signal covers a physical hour')
        if active:
            sig=active[0]
            _require(sig.signal_id not in processed,'Signal processed more than once')
            processed.add(sig.signal_id)
            rows={};note={'start_utc':load.start.isoformat(),'end_utc':load.end.isoformat(),'households':{}}
            if signal_case in (THREE_SIGNALS,THREE_SIGNALS_FULL_BLOCK,THREE_SIGNALS_TWO_BLOCKS):note['signal_id']=sig.signal_id
            for name in names:
                ownload=supplied_loads[name]
                budget=(_two_block_budget(ref,histories[name],load.start) if signal_case==THREE_SIGNALS_TWO_BLOCKS else
                        _evening_budget(ref,histories[name],load.start,start_hour=15)
                        if signal_case==THREE_SIGNALS_FULL_BLOCK else _evening_budget(ref,histories[name],load.start))
                floor=budget['floor_kwh'];eligible=(med is not None and floor is not None and states[name]>=floor)
                rows[name]=_hour_record(ref,ownload,price,med,household_policy,states[name],
                    floor if eligible else 2.,charge_permitted=False,extra_self_use=eligible)
                note['households'][name]={'budget':budget,'extra_eligible':eligible,
                    'inventory_before_kwh':states[name],
                    'actual_discharge_ac_kwh':rows[name]['native']['delivered_discharge_ac_kwh'],
                    'charging_disabled':True}
            signal_notes.append(note)
        else:
            rows=_shared_hour(ref,load,price,med,states,household_policy=household_policy,household_loads=supplied_loads)
        for name in names:
            records[name].append(rows[name]);states[name]=rows[name]['native']['x_end_kwh']
            histories[name].append(rows[name]['load'])
        selection.append({'index':i,'start_utc':load.start.isoformat(),'inventory_before_kWh':before,
            'charge_AC_kW':{n:rows[n]['native']['admitted_charge_ac_kwh'] for n in names}})
    out['shared_budget']={}
    for name in names:
        supplied={'household_only':source_records[name]['household_only'],'reserved':records[name]}
        result=_evaluate_records(ref,supplied,household_policy=household_policy,entity_id=name,coordination='SHARED_BUDGET',profile_case=profile_case,signal_case=signal_case)
        for key in ('wholesale_reference','price_provenance','profile_provenance','A1_reference'):
            if key in independent:result[key]=independent[key]
        if profile_case==MIXED_HP_BASE:
            result.pop('A1_reference',None) # Upstream qualified pair is not HH2's full load profile.
            result['profile_provenance']={**independent.get('profile_provenance',{}),
                'profile_case':profile_case,'entity_id':name,
                'selected_columns':['common_base_reference_kw']+(['unit_incremental_W55_device_reference_kw'] if name=='HH1' else []),
                'assignment_status':'OWNER_APPROVED_SCN_NOT_TWO_OBSERVED_HOUSEHOLDS',
                'scaling':'NONE; existing component selection only'}
        out['shared_budget'][name]=result
    out['shared_selection']=selection
    out['shared_rule']='Equal AC shares; actual unused budget reallocated; lower inventory then HH1 priority; no subhour switching'
    out['shared_scope']='TWO_EXPLICIT_HOUSEHOLDS_SHARED_CHARGE_BUDGET_SCN'
    if profile_case==MIXED_HP_BASE:
        out['shared_scope']='TWO_EXPLICIT_MIXED_REFERENCE_HOUSEHOLDS_SHARED_CHARGE_BUDGET_SCN'
        out['profile_case']=profile_case
    if signal_case is not None:
        sig=signals[0]
        out['signal_provenance']={'signal_id':sig.signal_id,'truth':sig.truth,'issued_at':sig.issued_at.isoformat(),
            'valid_from':sig.valid_from.isoformat(),'valid_until_exclusive':sig.valid_until.isoformat(),
            'selection':'First local10-11 after48physical hours, fixed before run; not historical top100 selection',
            'outside_validity':'SCN_ZERO','actual_operator_signal':False,'price_original_vintage_verified':False,
            'own_load_following':'Existing hourly E2 response approximation, not live instantaneous meter evidence'}
        if signal_case in (THREE_SIGNALS,THREE_SIGNALS_FULL_BLOCK,THREE_SIGNALS_TWO_BLOCKS):
            out['signal_provenance']={
                'schedule_id':THREE_SIGNALS,'truth':'SCN',
                'events':[{'signal_id':s.signal_id,'issued_at':s.issued_at.isoformat(),
                           'valid_from':s.valid_from.isoformat(),'valid_until_exclusive':s.valid_until.isoformat()}
                          for s in signals],
                'selection':'January3-5 local09 issue/local10-11 valid, fixed before run; not historical peak selection',
                'outside_validity':'SCN_ZERO','actual_operator_signal':False,'price_original_vintage_verified':False,
                'own_load_following':'Existing hourly E2 response approximation, not live instantaneous meter evidence',
                'state_continuity':'Native end stock carried to next physical hour without reset',
                'processed_signal_ids':[s.signal_id for s in signals if s.signal_id in processed]}
            if signal_case==THREE_SIGNALS_FULL_BLOCK:
                out['signal_provenance']['reserve_estimation']={
                    'scenario_reference':THREE_SIGNALS_FULL_BLOCK,
                    'history_block':'Previous complete local15-22 own-consumption block',
                    'applies_to':'The same three January3-5 DJF events only',
                    'meaning':'Persistence SCN, not guaranteed future demand; all other controls unchanged'}
            if signal_case==THREE_SIGNALS_TWO_BLOCKS:
                out['signal_provenance']['reserve_estimation']={
                    'scenario_reference':THREE_SIGNALS_TWO_BLOCKS,
                    'history_block':'Maximum exact DC requirement of last TWO complete local15-22 own-consumption blocks',
                    'missing_history':'Q/no extra discharge; no skipping a missing or invalid block',
                    'applies_to':'The same three January3-5 DJF events only',
                    'meaning':'Two-block SCN, not guaranteed future demand; all other controls unchanged'}
        out['signal_selection']=signal_notes
        out['internal_audit_scope']='Winter household-only versus shared reserved signal response, not reserve-only effect'
    return out


def shared_budget_pair(loads,prices,*,household_policy=EVENING_PRIORITY,profile_case=IDENTICAL_HP,signal_case=None):
    return _shared_pair_from_independent(evaluate(loads,prices,household_policy=household_policy),household_policy=household_policy,profile_case=profile_case,signal_case=signal_case)


def annual_shared_budget_pair(source_paths,*,household_policy=EVENING_PRIORITY,profile_case=IDENTICAL_HP,signal_case=None):
    return _shared_pair_from_independent(annual(source_paths,household_policy=household_policy),household_policy=household_policy,profile_case=profile_case,signal_case=signal_case)
