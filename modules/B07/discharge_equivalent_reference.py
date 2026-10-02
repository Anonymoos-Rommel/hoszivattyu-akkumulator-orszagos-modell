"""Owner-adopted conditional discharged-DC-equivalent reference method.

Test-domain source facts, E2 constant-parameter applicability and DER balances
remain distinct. This is a separately named reference, not the legacy stored-SOC
engine or a complete annual battery model. Unknown physical idle drain remains
unknown; a separate provisional aggregate AC debit does not manufacture a DC
inventory transition.
"""
from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from modules.B07 import sax_source_reference as source

ENERGY_TOL = 1e-9
PINS = {
    'modules/B07/sax_source_reference.py': 'c6f6cce1f0514784c20cf63d58bf4e22ad9dd2a8f12981536a086ea0054cc95c',
    'registry/b07_sax_reference_manifest.json': '76ab8d0558622e095cd9093725c5a4a9f174422739a5f2291f2314f9c439d7ba',
    'data/processed/b07/sax_2026_converter_curves.csv': '87d1b6b91950792c429746f71770237afd227e26ff5afd3bc5eb4d2b943ebfd6',
    'data/processed/b07/sax_2026_source_controls.json': 'bed133fe134b6559f074ca85ee55cf2043c26bf0792903b04b86866cc582b5de',
}


def number(value,name,*,positive=False):
    if (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value)
            or (value<=0 if positive else value<0)):
        raise ValueError('finite '+('positive ' if positive else 'nonnegative ')+name+' required')
    return value


@dataclass(frozen=True)
class Curve:
    identity: str
    points: tuple[tuple[float,float],...]
    direction: str

    def __post_init__(self):
        if not isinstance(self.identity,str) or not self.identity or self.direction not in ('AC_TO_DC','DC_TO_AC'):
            raise ValueError('explicit curve identity and path boundary required')
        if ((self.identity=='AC2BAT_STANDARD' and self.direction!='AC_TO_DC')
                or (self.identity in ('BAT2AC_STANDARD','BAT2AC_LOW_LOAD') and self.direction!='DC_TO_AC')):
            raise ValueError('named source curve cannot be retagged to a different path')
        if not isinstance(self.points,tuple) or any(not isinstance(p,tuple) or len(p)!=2 for p in self.points):
            raise ValueError('immutable paired source coordinates required')
        if len(self.points)<2:raise ValueError('at least two source supports required')
        for q,eta in self.points:
            number(q,'output power',positive=True);number(eta,'efficiency',positive=True)
            if eta>1:raise ValueError('efficiency above one')
        for (qa,ea),(qb,eb) in zip(self.points,self.points[1:]):
            if qb<=qa or qb/eb<=qa/ea:
                raise ValueError('strictly monotone output and input support required')

    @property
    def lower(self):return self.points[0][0]

    @property
    def upper(self):return self.points[-1][0]

    def point(self,q):
        number(q,'path output',positive=True)
        if not self.lower<=q<=self.upper:raise ValueError('outside selected curve support')
        xs=tuple(x[0] for x in self.points);i=bisect_left(xs,q)
        if i==0 or xs[i]==q:eta=self.points[i][1]
        else:
            (a,ea),(b,eb)=self.points[i-1:i+1]
            eta=ea+(eb-ea)*(q-a)/(b-a)
        return q/eta,eta

    def largest_output(self,input_budget,output_limit):
        """Largest supported constant output within an input/output envelope."""
        number(input_budget,'path input budget');number(output_limit,'path output limit')
        hi=min(output_limit,self.upper)
        if hi<self.lower or input_budget<self.point(self.lower)[0]:return None
        if self.point(hi)[0]<=input_budget:return hi
        lo=self.lower
        for _ in range(80):
            mid=(lo+hi)/2
            if mid==lo or mid==hi:break
            if self.point(mid)[0]<=input_budget:lo=mid
            else:hi=mid
        return lo


@dataclass(frozen=True)
class Reference:
    capacity_dc_output_equiv_kwh: float
    battery_dc_cycle_efficiency: float
    reserve_dc_output_equiv_kwh: float
    charge: Curve
    discharge: Curve
    discharge_ac_source_limit_kw: float
    empty_ac_test_kw: float | None
    identity: str

    def __post_init__(self):
        if (not isinstance(self.charge,Curve) or not isinstance(self.discharge,Curve)
                or self.charge.direction!='AC_TO_DC' or self.discharge.direction!='DC_TO_AC'):
            raise ValueError('charge/discharge converter boundaries cannot be swapped')
        if not isinstance(self.identity,str) or not self.identity:
            raise ValueError('explicit experiment/source identity required')
        number(self.capacity_dc_output_equiv_kwh,'capacity',positive=True)
        eta=number(self.battery_dc_cycle_efficiency,'cycle efficiency',positive=True)
        if eta>1:raise ValueError('cycle efficiency above one')
        number(self.reserve_dc_output_equiv_kwh,'explicit reserve')
        if self.reserve_dc_output_equiv_kwh>self.capacity_dc_output_equiv_kwh:raise ValueError('reserve exceeds capacity')
        number(self.discharge_ac_source_limit_kw,'discharge AC limit',positive=True)
        if self.empty_ac_test_kw is not None:number(self.empty_ac_test_kw,'empty-state AC power')


@dataclass(frozen=True)
class Inventory:
    dc_output_equiv_kwh: float | None
    unknown_reason: str | None = None

    def __post_init__(self):
        if self.dc_output_equiv_kwh is not None:
            number(self.dc_output_equiv_kwh,'inventory')
            if self.unknown_reason is not None:
                raise ValueError('unknown inventory cannot also be a numeric state')
        if self.unknown_reason is not None and (not isinstance(self.unknown_reason,str) or not self.unknown_reason):
            raise ValueError('unknown reason must be explicit text')


def source_reference(*,discharge_curve_id,reserve_dc_output_equiv_kwh):
    if discharge_curve_id not in ('BAT2AC_STANDARD','BAT2AC_LOW_LOAD'):
        raise ValueError('explicit separate discharge fit required')
    for name,digest in PINS.items():
        if digest is not None and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('pinned source/adapter changed')
    control=source.source_controls()
    if (control['edition'],control['system_id'],control['product'],control['firmware'])!=(2026,'A1','SAX Power Home Plus','V23.50'):
        raise ValueError('year/product/firmware mismatch')
    units=control['native_numeric_units']
    if (units['E_BAT_usable'],units['eta_BAT'],units['P_BAT2AC_out'],units['P_SYS_SOC0'])!=('kWh_DC_discharged_usable','percent','kW_AC_output','W'):
        raise ValueError('source unit mismatch')
    v=control['native_numeric_fields']
    return Reference(v['E_BAT_usable'],v['eta_BAT']/100,reserve_dc_output_equiv_kwh,
                     Curve('AC2BAT_STANDARD',source.curve_points('AC2BAT_STANDARD'),'AC_TO_DC'),
                     Curve(discharge_curve_id,source.curve_points(discharge_curve_id),'DC_TO_AC'),
                     v['P_BAT2AC_out'],v['P_SYS_SOC0']/1000,
                     'SAX_2026_A1_V23.50_DISCHARGE_EQUIVALENT_E2_REFERENCE')


def _idle(ref,state,charge_kw,discharge_kw,hours,reason):
    known_empty=state.dc_output_equiv_kwh is not None and state.dc_output_equiv_kwh<=ENERGY_TOL
    empty_ac=ref.empty_ac_test_kw*hours if known_empty and ref.empty_ac_test_kw is not None else None
    if empty_ac is not None:number(empty_ac,'conditional empty-state AC component')
    return dict(status='Q_IDLE_INVENTORY',reason=reason,
                x_start_kwh=state.dc_output_equiv_kwh,x_end_kwh=None,
                admitted_charge_ac_kwh=0.,admitted_charge_dc_kwh=0.,
                admitted_discharge_dc_kwh=0.,delivered_discharge_ac_kwh=0.,
                unused_active_charge_request_kwh=charge_kw*hours,
                unserved_battery_ac_request_kwh=discharge_kw*hours,
                conditional_empty_ac_component_kwh=empty_ac,
                idle_dc_drain_kwh=None,actual_system_electricity_kwh=None,
                inventory_balance_residual_kwh=None,selected_curve_id=None)


def step(ref,state,*,charge_ac_kw,discharge_ac_kw,hours):
    """Conditional constant-power step; no implicit duty cycle or idle zero."""
    if not isinstance(ref,Reference) or not isinstance(state,Inventory):
        raise ValueError('explicit reference and inventory objects required')
    number(charge_ac_kw,'AC charge request');number(discharge_ac_kw,'AC discharge request')
    number(hours,'duration',positive=True)
    number(charge_ac_kw*hours,'requested charge energy')
    number(discharge_ac_kw*hours,'requested discharge energy')
    if charge_ac_kw and discharge_ac_kw:raise ValueError('simultaneous charge/discharge is not this experiment')
    x=state.dc_output_equiv_kwh
    if x is None:
        return dict(status='Q_PREVIOUS_INVENTORY',reason=state.unknown_reason,
                    x_start_kwh=None,x_end_kwh=None,admitted_charge_ac_kwh=None,
                    admitted_charge_dc_kwh=None,admitted_discharge_dc_kwh=None,
                    delivered_discharge_ac_kwh=None,unused_active_charge_request_kwh=None,
                    unserved_battery_ac_request_kwh=None,conditional_empty_ac_component_kwh=None,
                    idle_dc_drain_kwh=None,actual_system_electricity_kwh=None,
                    inventory_balance_residual_kwh=None,selected_curve_id=None)
    number(x,'initial inventory')
    if not 0<=x<=ref.capacity_dc_output_equiv_kwh:
        raise ValueError('initial inventory outside usable capacity')
    if not charge_ac_kw and not discharge_ac_kw:
        return _idle(ref,state,charge_ac_kw,discharge_ac_kw,hours,'NO_ACTIVE_COMMAND_IDLE_DRAIN_UNQUALIFIED')
    eta=ref.battery_dc_cycle_efficiency
    if charge_ac_kw:
        room=(ref.capacity_dc_output_equiv_kwh-x)/eta
        output=ref.charge.largest_output(charge_ac_kw,room/hours)
        curve=ref.charge
        if output is None:return _idle(ref,state,charge_ac_kw,0.,hours,'CHARGE_CAPACITY_OR_SELECTED_SUPPORT_DECLINED')
        # Solve the operating point before admitting any energy, including ULPs.
        for _ in range(16):
            input_kw,efficiency=curve.point(output)
            c=output*hours;charge_ac=input_kw*hours;new_x=x+eta*c
            if new_x<=ref.capacity_dc_output_equiv_kwh and input_kw<=charge_ac_kw:break
            output=math.nextafter(output,0.)
            if output<curve.lower:return _idle(ref,state,charge_ac_kw,0.,hours,'CLIPPED_CONSTANT_POWER_BELOW_SOURCE_SUPPORT')
        else:raise ValueError('conservative charge clipping failed')
        d=discharge_ac=0.
    else:
        # Reserve limits available discharge; it does not forbid charging an
        # initially depleted reference state back toward that explicit reserve.
        available=max(0.,x-ref.reserve_dc_output_equiv_kwh)
        curve=ref.discharge
        output=curve.largest_output(available/hours,min(discharge_ac_kw,ref.discharge_ac_source_limit_kw))
        if output is None:return _idle(ref,state,0.,discharge_ac_kw,hours,'DISCHARGE_INVENTORY_OR_SELECTED_SUPPORT_DECLINED')
        for _ in range(16):
            input_kw,efficiency=curve.point(output)
            d=input_kw*hours;discharge_ac=output*hours;new_x=x-d
            if new_x>=ref.reserve_dc_output_equiv_kwh:break
            output=math.nextafter(output,0.)
            if output<curve.lower:return _idle(ref,state,0.,discharge_ac_kw,hours,'CLIPPED_CONSTANT_POWER_BELOW_SOURCE_SUPPORT')
        else:raise ValueError('conservative discharge clipping failed')
        c=charge_ac=0.
    residual=new_x-x-eta*c+d
    if abs(residual)>ENERGY_TOL:raise ValueError('reference DC inventory imbalance')
    return dict(status='SCN_ACTIVE_REFERENCE_ONLY',reason=None,x_start_kwh=x,x_end_kwh=new_x,
                admitted_charge_ac_kwh=charge_ac,admitted_charge_dc_kwh=c,
                admitted_discharge_dc_kwh=d,delivered_discharge_ac_kwh=discharge_ac,
                unused_active_charge_request_kwh=max(0.,charge_ac_kw*hours-charge_ac),
                unserved_battery_ac_request_kwh=max(0.,discharge_ac_kw*hours-discharge_ac),
                conditional_empty_ac_component_kwh=None,idle_dc_drain_kwh=None,
                actual_system_electricity_kwh=None,inventory_balance_residual_kwh=residual,
                selected_curve_id=curve.identity,actual_curve_output_kw=output,
                actual_curve_input_kw=input_kw,post_clipping_conversion_efficiency=efficiency)


def _cycle_closure(ref,initial,terminal,records):
    """Resolve closure at the scale of admitted flow, never initial stock.

    One ULP per materialized DC product, one for eta*c and one for fsum
    conservatively cover their binary64 rounding. This is a numerical bound,
    not an observed physical tolerance or an operating-time/energy minimum.
    Both the flow ledger and represented endpoints must close within it.
    """
    if terminal is None:
        return dict(status='Q_INCOMPLETE_INVENTORY',resolved_closed=False,
                    net_dc_flow_kwh=None,endpoint_delta_kwh=None,
                    arithmetic_allowance_kwh=None,relative_roundoff_resolved=None,
                    positive_two_way_flow=None)
    eta=ref.battery_dc_cycle_efficiency
    charged=[];discharged=[];rounding=[]
    for record in records:
        row=record['result']
        c=row['admitted_charge_dc_kwh'];d=row['admitted_discharge_dc_kwh']
        if c>0:
            gain=eta*c
            charged.append(gain)
            rounding.extend((eta*math.ulp(c),math.ulp(gain)))
        if d>0:
            discharged.append(d)
            rounding.append(math.ulp(d))
    net=math.fsum((*charged,*(-d for d in discharged)))
    allowance=math.fsum((*rounding,math.ulp(net)))
    delta=math.fsum((terminal,-initial))
    charge_total=math.fsum(charged);discharge_total=math.fsum(discharged)
    positive=charge_total>0 and discharge_total>0
    # A subnormal ULP can be a large fraction of the entire transfer. The
    # accumulated allowance must also fit the nominal binary64 relative-error
    # envelope for the two charge products, discharge product, and final sum.
    # Exact rational comparison prevents this precision budget underflowing.
    relative_budget=Fraction(math.ulp(1.0))*(2*Fraction(charge_total)
                                           +Fraction(discharge_total)+Fraction(abs(net)))
    precision_resolved=positive and Fraction(allowance)<=relative_budget
    resolved=(precision_resolved and allowance<min(charge_total,discharge_total)
              and abs(net)<=allowance and abs(delta)<=allowance)
    return dict(status=('RESOLVED_CLOSED' if resolved else
                        'NOT_CLOSED_OR_NUMERICALLY_UNRESOLVED' if positive else
                        'NO_POSITIVE_TWO_WAY_FLOW'),resolved_closed=resolved,
                net_dc_flow_kwh=net,endpoint_delta_kwh=delta,
                arithmetic_allowance_kwh=allowance,relative_roundoff_resolved=precision_resolved,
                positive_two_way_flow=positive)


def _reference_evidence(ref):
    identity='SAX_2026_A1_V23.50_DISCHARGE_EQUIVALENT_E2_REFERENCE'
    if ref.identity!=identity:
        return 'E3','SCN_DECLARED_MATHEMATICAL_REFERENCE'
    expected=source_reference(discharge_curve_id=ref.discharge.identity,
                              reserve_dc_output_equiv_kwh=ref.reserve_dc_output_equiv_kwh)
    if ref!=expected:
        raise ValueError('declared source reference differs from pinned source values')
    return 'E2','PROVISIONAL_TESTED_PRODUCT_APPLICABILITY'


def run(ref,*,initial_dc_output_equiv_kwh,commands):
    """One contiguous declared experiment; an unknown state is never restarted."""
    if not isinstance(ref,Reference) or commands is None:
        raise ValueError('explicit reference and command sequence required')
    tier,applicability=_reference_evidence(ref)
    number(initial_dc_output_equiv_kwh,'explicit initial inventory')
    if not 0<=initial_dc_output_equiv_kwh<=ref.capacity_dc_output_equiv_kwh:
        raise ValueError('initial inventory outside bounds')
    commands=tuple(commands)
    if not commands:raise ValueError('nonempty conditional experiment required')
    state=Inventory(initial_dc_output_equiv_kwh);records=[]
    for command in commands:
        if not isinstance(command,dict) or set(command)!= {'charge_ac_kw','discharge_ac_kw','hours'}:
            raise ValueError('explicit charge, discharge and duration fields required')
        r=step(ref,state,**command);records.append(dict(command=dict(command),result=r))
        state=Inventory(r['x_end_kwh'],r['reason'])
    complete=all(r['result']['x_end_kwh'] is not None for r in records)
    fields=('admitted_charge_ac_kwh','admitted_charge_dc_kwh','admitted_discharge_dc_kwh','delivered_discharge_ac_kwh')
    totals={key:sum(r['result'][key] for r in records) if complete else None for key in fields}
    identity=None;ratio=None;losses=None
    closure=_cycle_closure(ref,initial_dc_output_equiv_kwh,state.dc_output_equiv_kwh,records)
    cyclic=closure['resolved_closed']
    if complete:
        c=totals['admitted_charge_dc_kwh'];d=totals['admitted_discharge_dc_kwh']
        acin=totals['admitted_charge_ac_kwh'];acout=totals['delivered_discharge_ac_kwh']
        identity=d-ref.battery_dc_cycle_efficiency*c-initial_dc_output_equiv_kwh+state.dc_output_equiv_kwh
        if abs(identity)>ENERGY_TOL:raise ValueError('finite-horizon inventory identity failed')
        if cyclic and acin>0:ratio=acout/acin
        losses=dict(charge_converter_kwh=acin-c,
                    battery_cycle_bookkeeping_kwh=(1-ref.battery_dc_cycle_efficiency)*c,
                    discharge_converter_kwh=d-acout,
                    terminal_minus_initial_inventory_kwh=state.dc_output_equiv_kwh-initial_dc_output_equiv_kwh)
        if abs(acin-acout-sum(losses.values()))>ENERGY_TOL:raise ValueError('AC/DC component accounting failed')
    return dict(scope='CONDITIONAL_DISCHARGE_EQUIVALENT_REFERENCE',evidence_status='DER',
                input_scenario_status='SCN',applicability_evidence_tier=tier,
                applicability_status=applicability,
                validation_debt_id='Q-B07-003',
                declared_reference_identity=ref.identity,explicit_discharge_curve=ref.discharge.identity,
                capacity_dc_output_equiv_kwh=ref.capacity_dc_output_equiv_kwh,
                battery_dc_cycle_efficiency=ref.battery_dc_cycle_efficiency,
                explicit_reserve_dc_output_equiv_kwh=ref.reserve_dc_output_equiv_kwh,
                initial_dc_output_equiv_kwh=initial_dc_output_equiv_kwh,
                terminal_dc_output_equiv_kwh=state.dc_output_equiv_kwh,
                active_reference_ledger_complete=complete,cyclic_inventory_within_numerical_tolerance=cyclic,
                conditional_active_roundtrip_ratio=ratio,cycle_closure=closure,finite_horizon_residual_kwh=identity,
                active_reference_totals=totals,conditional_accounting_components=losses,records=records,
                actual_roundtrip_efficiency=None,actual_total_system_energy_kwh=None,
                transient_energy_kwh=None,complete_hardware_admission=False,
                actual_bms_soc=None,annual_result=None,national_admission=False,
                conditional_method_adopted=True,legacy_contract_replaced=False,
                limitations=('Constant C and battery cycle eta are explicit reference approximations',
                             'Constant power within steps and instantaneous boundary switches are conditional',
                             'Selected source-fit support is not an inferred complete hardware rating',
                             'Unmeasured cell-powered standby BMS/idle drain is not observed zero',
                             'Measured battery-cycle eta already includes its test-boundary BMS contribution; no extra active BMS penalty',
                             'No automatic curve join, duty cycle, reserve policy, tariff or B08 handoff',
                             'Bookkeeping loss assignment does not locate physical chemical heat release'))


def provisional_standby_ac_energy(*,idle_hours):
    """One E2 aggregate AC-energy debit for explicitly supplied idle hours.

    The exact-system empty-state observation (4.07 W) and manufacturer approx.
    4 W system statement support this provisional proxy. State/revision/BMS
    applicability remains validation debt, not a proven upper bound or zero
    cell-side drain. No active converter or battery-cycle loss is added twice.
    """
    number(idle_hours,'explicit idle exposure')
    for name,digest in PINS.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('pinned source/adapter changed')
    controls=source.source_controls()
    if (controls['edition'],controls['system_id'],controls['product'],controls['firmware'])!=(2026,'A1','SAX Power Home Plus','V23.50'):
        raise ValueError('year/product/firmware mismatch')
    if controls['native_numeric_units']['P_SYS_SOC0']!='W':
        raise ValueError('source unit mismatch')
    power_w=number(controls['native_numeric_fields']['P_SYS_SOC0'],'source idle power')
    energy_kwh=power_w/1000*idle_hours
    number(energy_kwh,'provisional idle energy')
    return dict(scope='SAX_REFERENCE_AGGREGATE_AC_IDLE_ENERGY_ONLY',
                evidence_status='DER',evidence_tier='E2',base_status='PROVISIONAL_BASE',
                base_power_w=power_w,idle_hours=idle_hours,ac_energy_debit_kwh=energy_kwh,
                source_id='SRC-B07-HTW-SAX-REFERENCE-2026',
                corroboration_source_id='SRC-B07-SAX-HOME-PLUS-STANDBY-DATASHEET-2026',
                validation_debt_id='Q-B07-003',
                dc_inventory_drain_kwh=None,physical_inventory_path_admitted=False,
                cell_bms_inclusion_verified=False,all_state_measurement_verified=False,
                is_upper_bound=False,complete_annual_system_result_admitted=False,
                national_admission=False,
                limitations=('Idle duration is explicit, never inferred from national households or a year',
                             'Approximation of aggregate AC-accounted loss; no asserted chemical or DC allocation',
                             'No separate active BMS penalty; measured cycle losses already include their active test boundary',
                             'Revision, state transfer, cell-powered idle loss and materiality remain E1 validation debt'))
