"""Audit two supplied, generation-free schedules for one shared battery.

Commands, rights and accounting allocations are inputs, never dispatch choices.
The native B07 executors retain their coordinate, clipping and unknown-state
semantics. A physical SCN result grants no site, market or financial authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path

from modules.B07.engine import BatteryEngine, BatterySpec, compute_household_balance
from modules.B07 import discharge_equivalent_reference as reference
from modules.B01 import benefit_metric_contract as benefit

ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.0.0"
STORED = "STORED_USABLE_KWH_SCN"
REFERENCE = "DC_DISCHARGE_EQUIVALENT_REFERENCE"
ACTIVATION = "ACTIVATION_WITH_EXISTING_RESERVATION"
AGREEMENT = "RIGHTS_AGREEMENT_VS_HOUSEHOLD_ONLY"
ACCESS = "SHARED_CAPACITY_ACCESS"
PROTECTED = "PROTECTED_INVENTORY_POOL"
FLOW_FIELDS = ("charge_ac_kwh", "discharge_ac_kwh", "inventory_credit_kwh",
               "inventory_debit_kwh", "charge_converter_loss_kwh",
               "cycle_bookkeeping_loss_kwh", "discharge_converter_loss_kwh")
MONEY_FIELDS = ("tariff_energy_component", "wear", "compensation",
                "reservation_opportunity", "recharge_payment", "terminal_valuation")
OPERATIONS = ("CHARGE", "DISCHARGE", "EXPORT", "AGGREGATION")


class SharedUseError(ValueError):
    """Malformed or contradictory input identity; no admission is produced."""


def _require(ok, message):
    if not ok:
        raise SharedUseError(message)


def _text(value, name):
    _require(isinstance(value, str) and bool(value.strip()), name + ": explicit text required")


def _number(value, name, *, signed=False, positive=False):
    _require(type(value) in (int, float) and math.isfinite(value)
             and (signed or value >= 0) and (not positive or value > 0),
             name + ": finite numeric value in domain required; bool is not a quantity")
    return value



def _sum(values):
    try:
        result = math.fsum(values)
    except (OverflowError, TypeError) as exc:
        raise SharedUseError("aggregate arithmetic must remain finite") from exc
    return _number(result, "aggregate arithmetic", signed=True)

def _time(value):
    _text(value, "UTC timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SharedUseError("ISO UTC timestamp required") from exc
    _require(result.tzinfo is not None and result.utcoffset().total_seconds() == 0,
             "explicit UTC timestamp required")
    return result


def _window(start, end):
    a, b = _time(start), _time(end)
    _require(a < b, "nonempty half-open window required")
    return a, b


def _tuple(value, name):
    _require(type(value) is tuple, name + ": immutable tuple required")


def _unique(rows, attr, name):
    _tuple(rows, name)
    result = {}
    for row in rows:
        key = getattr(row, attr, None)
        _text(key, name)
        _require(key not in result, "duplicate " + name + ": " + key)
        result[key] = row
    return result


def digest(value):
    """Exact supplied-content identity, never evidence of truth or permission."""
    return benefit.fingerprint(value)


@dataclass(frozen=True)
class Unknown:
    reason: str


@dataclass(frozen=True)
class Term:
    status: str  # SCN, Q or NOT_APPLICABLE; applicability is never implicit.
    value: float | None
    reference: str


@dataclass(frozen=True)
class Identity:
    device_id: str
    connection_id: str
    household_actor_id: str
    state_actor_id: str
    coordinate: str
    capacity_denominator: str
    capacity_kwh: float
    executor_sha256: str


@dataclass(frozen=True)
class Request:
    actor_id: str
    service_id: str
    charge_ac_kw: float
    discharge_ac_kw: float


@dataclass(frozen=True)
class Allocation:
    actor_id: str
    service_id: str
    charge_ac_kwh: float
    discharge_ac_kwh: float
    inventory_credit_kwh: float
    inventory_debit_kwh: float
    charge_converter_loss_kwh: float
    cycle_bookkeeping_loss_kwh: float
    discharge_converter_loss_kwh: float


@dataclass(frozen=True)
class Interval:
    interval_id: str
    physical_event_id: str
    identity_sha256: str
    start: str
    end: str
    hours: float
    loads_kw: tuple[float, float, float]  # household, heat pump, other; no generation
    requests: tuple[Request, ...]
    allocations: tuple[Allocation, ...] | Unknown


@dataclass(frozen=True)
class Budget:
    budget_id: str
    actor_id: str
    start: str
    end: str
    draw_kwh: Term
    replenishment: str  # NONE, ATTRIBUTED_CHARGE_CREDIT or Q; no implicit reset


@dataclass(frozen=True)
class RightsWindow:
    right_id: str
    actor_id: str
    start: str
    end: str
    service_start: str
    service_end: str
    charge_ac_kw: Term
    discharge_ac_kw: Term
    draw_kwh: Term
    callable_hours: Term
    budget_id: str


@dataclass(frozen=True)
class Transfer:
    event_id: str
    at: str
    direction: str  # FREE_TO_PROTECTED or PROTECTED_TO_FREE
    inventory_kwh: float


@dataclass(frozen=True)
class Agreement:
    agreement_id: str
    version: str
    content_sha256: str
    identity_sha256: str
    mode: str
    initial_protected_kwh: Term
    minimum_total_retained_kwh: Term
    budgets: tuple[Budget, ...]
    rights: tuple[RightsWindow, ...]
    transfers: tuple[Transfer, ...]
    qualification: Term  # SCN with no number, or Q with no number


@dataclass(frozen=True)
class IdleAccounting:
    interval_ids: tuple[str, ...]
    idle_hours: float
    actor_ac_debits_kwh: tuple[tuple[str, float], ...] | Unknown
    include_native_empty_component: bool


@dataclass(frozen=True)
class Leg:
    leg_id: str
    identity_sha256: str
    initial_inventory_kwh: float
    agreement: Agreement | Unknown | str  # HOUSEHOLD_ONLY only in agreement baseline
    intervals: tuple[Interval, ...]
    idle_accounting: IdleAccounting | Unknown


@dataclass(frozen=True)
class Baseline:
    baseline_id: str
    method: str
    purpose: str
    version: str
    scope: str
    leg_sha256: str
    qualification: Term


@dataclass(frozen=True)
class ResponseClaim:
    scope: str
    comparison_sha256: str
    baseline_sha256: str
    meaning: str  # CONDITIONAL_TOTAL_CONNECTION_RESPONSE only
    truth_context: str  # SCN only
    automatic_b10_projection: bool


@dataclass(frozen=True)
class Permission:
    operation: str
    status: str  # Q or FAIL; this consumer has no real-site approval route
    reference: str


@dataclass(frozen=True)
class QualifiedProtection:
    actor_id: str
    comparison_sha256: str
    candidate: benefit.Candidate
    frame: benefit.ComparisonFrame
    candidate_sha256: str
    frame_sha256: str
    cash_scope_sha256: str
    supplied_status: str
    full_agreement_effects: Term
    correspondence: benefit.Evidence


@dataclass(frozen=True)
class FinancialInputs:
    components: tuple[tuple[str, Term], ...]
    protection: QualifiedProtection | Unknown


@dataclass(frozen=True)
class SharedUseCase:
    case_id: str
    version: str
    content_sha256: str
    truth_context: str
    identity: Identity
    executor: BatterySpec | reference.Reference
    source_pins: tuple[tuple[str, str], ...]
    scenario_reference: str
    stored_standing_loss_condition: str
    scope: str
    state_service_id: str
    baseline: Baseline
    baseline_leg: Leg
    actual_leg: Leg
    connection_import_limit_kw: Term
    connection_export_limit_kw: Term
    permissions: tuple[Permission, ...]
    financial: FinancialInputs
    response_claims: tuple[ResponseClaim, ...]
    horizon_completeness: str  # SERVICE_ONLY or SUPPLIED_REBOUND_HORIZON
    absolute_tolerance_kwh: float
    relative_tolerance: float


def content_digest(value):
    """Hash a case/agreement with its own digest field blanked."""
    _require(type(value) in (SharedUseCase, Agreement), "case or agreement required")
    return digest(replace(value, content_sha256=""))


def comparison_digest(case):
    """Bind both full schedules and baseline meaning, independent of claims."""
    return digest((case.version, case.case_id, case.identity, case.scope,
                   case.state_service_id, case.baseline, case.baseline_leg, case.actual_leg))


def _unknown(value):
    _require(type(value) is Unknown, "explicit Unknown required; bare null is not Q")
    _text(value.reason, "Q acquisition/qualification reason")


def _term(term, *, na=False, signed=False, qualification=False):
    _require(type(term) is Term, "explicit Term required; bare null is not Q or unlimited")
    _text(term.reference, "term reference")
    _require(term.status in ({"SCN", "Q", "NOT_APPLICABLE"} if na else {"SCN", "Q"}),
             "term status/applicability")
    if term.status == "SCN" and not qualification:
        _number(term.value, "term", signed=signed)
    else:
        _require(term.value is None, "Q/inapplicable/qualification term has no numeric value")
    return term.value


def _status(failures, unknowns):
    return "FAIL" if failures else "Q" if unknowns else "PASS_SCN"


def _allowance(case, *values):
    # Only the quantity currently reconciled, never initial stock or national totals.
    scale = max((abs(v) for v in values), default=0.)
    return case.absolute_tolerance_kwh * min(1., scale) + case.relative_tolerance * scale


def _agreement_validate(case, leg, start, end):
    g = leg.agreement
    if type(g) is Unknown:
        _unknown(g)
        return
    if g == "HOUSEHOLD_ONLY":
        _require(case.scope == AGREEMENT and leg is case.baseline_leg,
                 "household-only is exclusively the agreement-effect baseline")
        return
    _require(type(g) is Agreement, "explicit agreement or Q required")
    _require(g.content_sha256 == content_digest(g), "agreement content digest mismatch")
    _require(g.identity_sha256 == digest(case.identity), "agreement coordinate/device/denominator mismatch")
    _text(g.agreement_id, "agreement ID"); _text(g.version, "agreement version")
    _require(g.mode in (ACCESS, PROTECTED), "unsupported rights/pool borrowing mode")
    _term(g.qualification, qualification=True)
    _term(g.initial_protected_kwh, na=g.mode == ACCESS)
    _require(g.mode != ACCESS or g.initial_protected_kwh.status == "NOT_APPLICABLE",
             "access cap cannot claim protected inventory")
    _term(g.minimum_total_retained_kwh, na=True)
    budgets = _unique(g.budgets, "budget_id", "draw budget")
    # Narrow supported contract: one continuous budget per actor, shared across
    # adjacent rights revisions. Changing IDs cannot replenish that obligation.
    actors = {case.identity.household_actor_id, case.identity.state_actor_id}
    _require(len({b.actor_id for b in budgets.values()}) == len(budgets),
             "one continuous budget per actor; split/alias/reset budget rejected")
    _require({b.actor_id for b in budgets.values()} == actors, "explicit continuous budget for each actor required")
    for budget in budgets.values():
        _require(type(budget) is Budget and budget.actor_id in actors, "budget actor/type")
        a, b = _window(budget.start, budget.end)
        _term(budget.draw_kwh)
        _require(budget.replenishment in ("NONE", "ATTRIBUTED_CHARGE_CREDIT", "Q"), "budget reset rule")
    rights = _unique(g.rights, "right_id", "rights window")
    for right in rights.values():
        _require(type(right) is RightsWindow and right.actor_id in actors, "right actor/type")
        a, b = _window(right.start, right.end)
        s, e = _window(right.service_start, right.service_end)
        _require(a <= s < e <= b, "service window must fit effective rights window")
        _require(right.budget_id in budgets and budgets[right.budget_id].actor_id == right.actor_id,
                 "exact actor's continuous budget required")
        for name in ("charge_ac_kw", "discharge_ac_kw", "draw_kwh", "callable_hours"):
            _term(getattr(right, name))
    for actor in actors:
        sequence = sorted((r for r in rights.values() if r.actor_id == actor), key=lambda r: _time(r.start))
        for left, right in zip(sequence, sequence[1:]):
            _require(_time(left.end) <= _time(right.start), "overlapping rights double claim")
    events = _unique(g.transfers, "event_id", "transfer event")
    boundaries = {_time(i.start) for i in leg.intervals} | {end}
    previous = None
    for transfer in events.values():
        _require(type(transfer) is Transfer and g.mode == PROTECTED, "transfers require protected-pool mode")
        at = _time(transfer.at)
        _require(at in boundaries and (previous is None or previous < at),
                 "strict chronological boundary transfers; same-instant cycles/implicit subintervals rejected")
        previous = at
        _require(transfer.direction in ("FREE_TO_PROTECTED", "PROTECTED_TO_FREE"), "unsupported pool transfer")
        _number(transfer.inventory_kwh, "pool transfer")
    _require(not (set(events) & {r.physical_event_id for r in leg.intervals}), "duplicate physical/transfer event")


def _validate(case):
    _require(type(case) is SharedUseCase, "SharedUseCase required")
    _require(case.version == VERSION and case.truth_context == "SCN", "versioned SCN run context required")
    _text(case.case_id, "case ID"); _text(case.scenario_reference, "scenario lineage")
    _require(case.content_sha256 == content_digest(case), "case content digest mismatch")
    identity = case.identity
    _require(type(identity) is Identity, "identity type")
    for name in ("device_id", "connection_id", "household_actor_id", "state_actor_id", "capacity_denominator"):
        _text(getattr(identity, name), name)
    _require(identity.household_actor_id != identity.state_actor_id, "two distinct actor IDs required")
    _number(identity.capacity_kwh, "capacity denominator", positive=True)
    _require(identity.executor_sha256 == digest(case.executor), "executor/source hash mismatch")
    _tuple(case.source_pins, "source pins")
    _require(len(dict(case.source_pins)) == len(case.source_pins), "duplicate source pin")
    if identity.coordinate == STORED:
        _require(type(case.executor) is BatterySpec and case.executor.status == "SCN"
                 and case.executor.efficiency_boundary == "SCN_ONE_WAY"
                 and case.executor.capacity_boundary == "USABLE" and case.executor.power_boundary == "AC",
                 "unchanged stored SCN executor and AC/usable boundary required")
        _require(identity.capacity_denominator == "STORED_USABLE_CAPACITY_KWH"
                 and identity.capacity_kwh == case.executor.usable_capacity_kwh, "stored capacity denominator mismatch")
        _require(case.stored_standing_loss_condition == "CONDITIONAL_OMITTED_STANDING_LOSS",
                 "explicit omitted standing-loss condition required")
        _require(not case.source_pins, "SCN one-way engine cannot acquire source authority from pins")
        for f in fields(case.executor):
            v = getattr(case.executor, f.name)
            if type(v) in (int, float, bool):
                _number(v, "BatterySpec." + f.name, signed="temp" in f.name)
        case.executor.__post_init__()
    elif identity.coordinate == REFERENCE:
        _require(type(case.executor) is reference.Reference, "native reference required")
        case.executor.__post_init__()
        _require(identity.capacity_denominator == "DC_DISCHARGE_EQUIVALENT_CAPACITY_KWH"
                 and identity.capacity_kwh == case.executor.capacity_dc_output_equiv_kwh,
                 "reference capacity denominator mismatch")
        _require(case.stored_standing_loss_condition == "NOT_APPLICABLE_REFERENCE_IDLE_Q", "reference idle boundary")
        source_ref = case.executor.identity == "SAX_2026_A1_V23.50_DISCHARGE_EQUIVALENT_E2_REFERENCE"
        _require(dict(case.source_pins) == (reference.PINS if source_ref else {}), "exact native source pins required")
    else:
        raise SharedUseError("unsupported coordinate or implicit conversion")
    _number(case.absolute_tolerance_kwh, "absolute numerical tolerance")
    _number(case.relative_tolerance, "relative numerical tolerance")
    _require(case.absolute_tolerance_kwh <= reference.ENERGY_TOL and case.relative_tolerance <= 1e-12,
             "tolerance cannot exceed native/flow-scale numerical envelope")
    _require(case.scope in (ACTIVATION, AGREEMENT), "explicit supported comparison scope required")
    _text(case.state_service_id, "state service ID")
    _require(case.state_service_id != "HOUSEHOLD_SELF_USE", "separate household/state service IDs")
    _require(type(case.baseline) is Baseline and case.baseline.scope == case.scope, "baseline scope mismatch")
    for name in ("baseline_id", "method", "purpose", "version"):
        _text(getattr(case.baseline, name), "baseline " + name)
    _term(case.baseline.qualification, qualification=True)
    _require(case.baseline.leg_sha256 == digest(case.baseline_leg), "baseline schedule hash mismatch")
    _require(case.baseline_leg.leg_id != case.actual_leg.leg_id, "distinct physical legs required")
    for leg in (case.baseline_leg, case.actual_leg):
        _require(type(leg) is Leg and leg.identity_sha256 == digest(identity), "leg identity mismatch")
        _text(leg.leg_id, "leg ID"); _number(leg.initial_inventory_kwh, "initial inventory")
        _require(leg.initial_inventory_kwh <= identity.capacity_kwh, "initial inventory exceeds capacity")
        intervals = _unique(leg.intervals, "interval_id", "interval")
        _require(bool(intervals), "nonempty schedule required")
        _unique(leg.intervals, "physical_event_id", "physical event")
        previous = None
        for interval in leg.intervals:
            _require(type(interval) is Interval and interval.identity_sha256 == digest(identity), "interval identity mismatch")
            start, end = _window(interval.start, interval.end)
            _number(interval.hours, "interval duration", positive=True)
            _require((end-start).total_seconds()/3600 == interval.hours, "timestamp/duration mismatch")
            _require(previous is None or start == previous, "contiguous schedule required; gaps need explicit idle intervals")
            previous = end
            _tuple(interval.loads_kw, "matched exogenous loads")
            _require(len(interval.loads_kw) == 3, "three generation-free load components required")
            for load in interval.loads_kw: _number(load, "load kW")
            requests = _unique(interval.requests, "actor_id", "actor request")
            _require(set(requests) == {identity.household_actor_id, identity.state_actor_id}, "exact two actor requests required")
            for actor, request in requests.items():
                _require(type(request) is Request, "request type")
                service = "HOUSEHOLD_SELF_USE" if actor == identity.household_actor_id else case.state_service_id
                _require(request.service_id == service, "actor/service identity mismatch")
                _number(request.charge_ac_kw, "charge request"); _number(request.discharge_ac_kw, "discharge request")
                _number(request.charge_ac_kw*interval.hours, "charge request energy")
                _number(request.discharge_ac_kw*interval.hours, "discharge request energy")
            _require(not (any(r.charge_ac_kw > 0 for r in requests.values())
                          and any(r.discharge_ac_kw > 0 for r in requests.values())),
                     "opposing simultaneous commands rejected before netting")
            if leg is case.baseline_leg:
                s = requests[identity.state_actor_id]
                _require(s.charge_ac_kw == 0 and s.discharge_ac_kw == 0, "baseline cannot contain state activation")
            if type(interval.allocations) is Unknown:
                _unknown(interval.allocations)
            else:
                allocations = _unique(interval.allocations, "actor_id", "actor allocation")
                _require(set(allocations) <= set(requests), "unknown allocation actor")
                for actor, allocation in allocations.items():
                    _require(type(allocation) is Allocation and allocation.service_id == requests[actor].service_id,
                             "one allocation per actor/event; service identity mismatch")
                    for name in FLOW_FIELDS: _number(getattr(allocation, name), "allocation " + name)
        _agreement_validate(case, leg, _time(leg.intervals[0].start), _time(leg.intervals[-1].end))
    left, right = case.baseline_leg, case.actual_leg
    _require(left.initial_inventory_kwh == right.initial_inventory_kwh, "counterfactual initial inventory mismatch")
    _require([(i.start, i.end, i.hours, i.loads_kw) for i in left.intervals] ==
             [(i.start, i.end, i.hours, i.loads_kw) for i in right.intervals], "matched time/load boundary required")
    if case.scope == ACTIVATION:
        _require(left.agreement == right.agreement, "activation baseline must retain exact reservation/amendments")
    else:
        _require(left.agreement == "HOUSEHOLD_ONLY" and right.agreement != "HOUSEHOLD_ONLY",
                 "agreement comparison needs explicit household-only baseline")
    _term(case.connection_import_limit_kw); _term(case.connection_export_limit_kw)
    permissions = _unique(case.permissions, "operation", "permission operation")
    _require(set(permissions) == set(OPERATIONS), "four independent permissions required")
    for p in permissions.values():
        _require(type(p) is Permission and p.status in ("Q", "FAIL"), "no actual-site permission admission route")
        _text(p.reference, "permission qualification/exclusion")
    _tuple(case.response_claims, "response claims")
    for claim in case.response_claims:
        _require(type(claim) is ResponseClaim and claim.scope == case.scope
                 and claim.comparison_sha256 == comparison_digest(case)
                 and claim.baseline_sha256 == digest(case.baseline), "response claim scope/hash reuse mismatch")
        _require(claim.meaning == "CONDITIONAL_TOTAL_CONNECTION_RESPONSE" and claim.truth_context == "SCN"
                 and claim.automatic_b10_projection is False,
                 "no programme-scope substitution, automatic B10 projection or REAL promotion")
    _require(case.horizon_completeness in ("SERVICE_ONLY", "SUPPLIED_REBOUND_HORIZON"), "explicit horizon scope")


def _execute(case, leg):
    commands = [dict(charge_ac_kw=_sum(r.charge_ac_kw for r in i.requests),
                     discharge_ac_kw=_sum(r.discharge_ac_kw for r in i.requests), hours=i.hours)
                for i in leg.intervals]
    rows = []
    if case.identity.coordinate == REFERENCE:
        native_run = reference.run(case.executor, initial_dc_output_equiv_kwh=leg.initial_inventory_kwh,
                                   commands=commands)
        for entry in native_run["records"]:
            r = entry["result"]
            c, d = r["admitted_charge_dc_kwh"], r["admitted_discharge_dc_kwh"]
            acin, acout = r["admitted_charge_ac_kwh"], r["delivered_discharge_ac_kwh"]
            credit = None if c is None else case.executor.battery_dc_cycle_efficiency*c
            values = (acin, acout, credit, d, None if c is None else acin-c,
                      None if c is None else (1-case.executor.battery_dc_cycle_efficiency)*c,
                      None if d is None else d-acout)
            rows.append(dict(zip(FLOW_FIELDS, values), inventory_before_kwh=r["x_start_kwh"],
                             inventory_after_kwh=r["x_end_kwh"], native=r,
                             physical_status="Q" if r["x_end_kwh"] is None else "PASS_SCN"))
    else:
        executor = BatteryEngine(case.executor, leg.initial_inventory_kwh)
        for command in commands:
            # Explicit subinterval duration; state and cumulative counters survive.
            executor.spec = replace(case.executor, timestep_hours=command["hours"])
            r = executor.step(command["charge_ac_kw"], command["discharge_ac_kw"])
            values = (r.charge_energy_from_grid_kwh, r.discharge_energy_to_load_grid_kwh,
                      r.energy_added_to_storage_kwh, r.energy_removed_from_storage_kwh,
                      r.charge_energy_from_grid_kwh-r.energy_added_to_storage_kwh, 0.,
                      r.energy_removed_from_storage_kwh-r.discharge_energy_to_load_grid_kwh)
            rows.append(dict(zip(FLOW_FIELDS, values), inventory_before_kwh=r.soc_before_kwh,
                             inventory_after_kwh=r.soc_after_kwh, native=asdict(r), physical_status="PASS_SCN"))
        native_run = dict(state=asdict(executor.state), standing_loss="CONDITIONAL_OMITTED_STANDING_LOSS")
    return rows, native_run


def _allocate(case, interval, row):
    failures, unknowns, residuals, actors = [], [], {}, {}
    requests = {r.actor_id: r for r in interval.requests}
    supplied = {} if type(interval.allocations) is Unknown else {a.actor_id: a for a in interval.allocations}
    if set(supplied) != set(requests): unknowns.append("Q_ACTOR_ALLOCATION")
    for actor, request in requests.items():
        allocation = supplied.get(actor)
        if allocation is None:
            actors[actor] = dict(request=asdict(request), allocation=None, status="Q_ACTOR_ALLOCATION")
            continue
        actor_failure_start = len(failures)
        a = asdict(allocation)
        checks = {
            "charge_identity": a["charge_ac_kwh"]-a["inventory_credit_kwh"]-a["charge_converter_loss_kwh"]-a["cycle_bookkeeping_loss_kwh"],
            "discharge_identity": a["inventory_debit_kwh"]-a["discharge_ac_kwh"]-a["discharge_converter_loss_kwh"],
        }
        for name, residual in checks.items():
            residuals[actor+":"+name] = residual
            involved = (a["charge_ac_kwh"], a["inventory_credit_kwh"]) if name == "charge_identity" else (a["discharge_ac_kwh"], a["inventory_debit_kwh"])
            if abs(residual) > _allowance(case, *involved): failures.append(actor+":"+name)
        for direction in ("charge", "discharge"):
            requested = getattr(request, direction+"_ac_kw")*interval.hours
            admitted = a[direction+"_ac_kwh"]
            if admitted-requested > _allowance(case, requested, admitted): failures.append(actor+":"+direction+"_exceeds_request")
            a[direction+"_ac_kw"] = admitted/interval.hours
            a[("curtailed_charge" if direction == "charge" else "unserved_discharge")+"_kwh"] = max(0., requested-admitted)
        # A missing other row cannot hide already-known over-allocation.
        for name in FLOW_FIELDS:
            if row[name] is not None and a[name]-row[name] > _allowance(case, a[name], row[name]):
                failures.append(actor+":"+name+"_exceeds_device")
        requested_power = request.charge_ac_kw+request.discharge_ac_kw
        admitted_energy = a["charge_ac_kwh"]+a["discharge_ac_kwh"]
        a["requested_active_hours"] = interval.hours if requested_power else 0.
        a["admitted_active_hours"] = interval.hours if admitted_energy > 0 else 0.
        a["unserved_full_power_equivalent_hours"] = (max(0., interval.hours-admitted_energy/requested_power)
                                                     if requested_power else 0.)
        actor_failures = failures[actor_failure_start:]
        actor_unknowns = ["NATIVE_FLOW_Q:"+name for name in FLOW_FIELDS if row[name] is None]
        actors[actor] = dict(request=asdict(request), allocation=a,
                             status=_status(actor_failures, actor_unknowns),
                             failures=actor_failures, unknowns=actor_unknowns)
    for name in FLOW_FIELDS:
        if row[name] is None:
            unknowns.append("NATIVE_FLOW_Q:"+name)
        else:
            total = _sum(getattr(a, name) for a in supplied.values())
            residuals[name] = total-row[name]
            if ((len(supplied) == 2 and abs(total-row[name]) > _allowance(case, total, row[name]))
                    or total-row[name] > _allowance(case, total, row[name])):
                failures.append("ALLOCATION_SUM:"+name)
    return dict(status=_status(failures, unknowns), failures=failures, unknowns=unknowns,
                residuals_kwh=residuals, actors=actors, supplied=interval.allocations)


def _connection(case, interval, row):
    """Separate the active-converter contribution from the included AC boundary."""
    c, d = row["charge_ac_kwh"], row["discharge_ac_kwh"]
    component_scope = "MATCHED_LOAD_PLUS_ADMITTED_ACTIVE_CONVERTER_AC"
    if c is None or d is None:
        component = dict(scope=component_scope, status="Q", signed_kw=None, import_kw=None,
                         export_kw=None, failures=[], unknowns=["NATIVE_ACTIVE_AC_FLOW_Q"])
        return dict(status="Q", signed_kw=None, import_kw=None, export_kw=None,
                    failures=[], unknowns=["NATIVE_ACTIVE_AC_FLOW_Q"], active_component=component)
    native = compute_household_balance(*interval.loads_kw, 0., c/interval.hours, d/interval.hours)
    _number(native.grid_import_kw, "connection import")
    _number(native.grid_export_kw, "connection export")
    # No export clip was supplied. All three active-component views preserve the
    # native arithmetic order; an omitted idle component cannot become zero.
    signed = native.grid_import_kw-native.grid_export_kw
    failures, unknowns = [], []
    for name, value, limit in (("IMPORT", native.grid_import_kw, case.connection_import_limit_kw),
                               ("EXPORT", native.grid_export_kw, case.connection_export_limit_kw)):
        if limit.status == "Q": unknowns.append(name+"_ENVELOPE_Q")
        elif value-limit.value > _allowance(case, value*interval.hours, limit.value*interval.hours)/interval.hours:
            failures.append(name+"_ENVELOPE_EXCEEDED")
    component = dict(scope=component_scope, status=_status(failures, unknowns), signed_kw=signed,
                     import_kw=native.grid_import_kw, export_kw=native.grid_export_kw,
                     failures=failures, unknowns=unknowns, native=asdict(native))
    unresolved_idle_ac = (case.identity.coordinate == REFERENCE
                          and row["native"]["status"] != "SCN_ACTIVE_REFERENCE_ONLY")
    if unresolved_idle_ac:
        # A separate E2 horizon debit supplies no instantaneous total AC path.
        # Keep any component-envelope failure at its own precise scope.
        return dict(status="Q", signed_kw=None, import_kw=None, export_kw=None,
                    failures=[], unknowns=["REFERENCE_IDLE_TOTAL_AC_COMPONENT_Q", *unknowns],
                    active_component=component)
    return dict(status=component["status"], signed_kw=signed,
                import_kw=native.grid_import_kw, export_kw=native.grid_export_kw,
                failures=failures, unknowns=unknowns, native=asdict(native), active_component=component)


def _drawable_inventory(case, agreement, inventory, pool, energy_right, budget):
    """Conditional actor ceiling under one unsplit shared retained floor."""
    reserve = (case.executor.soc_min_kwh if case.identity.coordinate == STORED
               else case.executor.reserve_dc_output_equiv_kwh)
    physical = None if inventory is None else max(0., inventory-reserve)
    minimum = agreement.minimum_total_retained_kwh
    if inventory is None or minimum.status == "Q":
        shared_headroom = None
    else:
        floor = max(reserve, minimum.value if minimum.status == "SCN" else 0.)
        shared_headroom = max(0., inventory-floor)
    available = (None if None in (shared_headroom, pool, energy_right, budget)
                 else max(0., min(shared_headroom, pool, energy_right, budget)))
    return physical, shared_headroom, available


def _rights(case, leg, rows):
    g = leg.agreement
    if type(g) is Unknown:
        return dict(status="Q", reason=g.reason, intervals=[], transfers=[])
    if g == "HOUSEHOLD_ONLY":
        return dict(status="NOT_APPLICABLE_HOUSEHOLD_ONLY", intervals=[], transfers=[])
    all_fail, all_q, result, transfers = [], [], [], []
    if g.qualification.status == "Q": all_q.append("AGREEMENT_QUALIFICATION_Q")
    budget_remaining = {b.budget_id: b.draw_kwh.value for b in g.budgets}
    budget_by_id = {b.budget_id: b for b in g.budgets}
    drawn = {r.right_id: 0. for r in g.rights}
    called = {r.right_id: 0. for r in g.rights}
    # Lower bounds contain only locally established nonnegative use. They are
    # not reconstructed exact ledgers and survive missing earlier allocations.
    known_drawn = {r.right_id: 0. for r in g.rights}
    known_called = {r.right_id: 0. for r in g.rights}
    known_budget_drawn = {b.budget_id: 0. for b in g.budgets}
    r_pool = g.initial_protected_kwh.value if g.mode == PROTECTED else None
    f_pool = None if r_pool is None else leg.initial_inventory_kwh-r_pool
    if g.mode == PROTECTED:
        if r_pool is None: all_q.append("INITIAL_POOL_Q")
        elif f_pool < -_allowance(case, r_pool, leg.initial_inventory_kwh): all_fail.append("INITIAL_PROTECTED_TARGET_UNMET")
    if (g.minimum_total_retained_kwh.status == "SCN"
            and g.minimum_total_retained_kwh.value-leg.initial_inventory_kwh > case.absolute_tolerance_kwh):
        all_fail.append("INITIAL_MINIMUM_TOTAL_RETAINED_FAILED")
    event_map = {_time(t.at): t for t in g.transfers}

    def boundary(at, x):
        nonlocal r_pool, f_pool
        event = event_map.get(at)
        if event is None: return
        fail, q = [], []
        before = (r_pool, f_pool)
        if r_pool is None or f_pool is None or x is None:
            q.append("TRANSFER_INVENTORY_Q"); r_pool = f_pool = None
        else:
            signed = event.inventory_kwh if event.direction == "FREE_TO_PROTECTED" else -event.inventory_kwh
            r_pool += signed; f_pool -= signed
            if min(r_pool, f_pool) < -_allowance(case, event.inventory_kwh): fail.append("TRANSFER_SOURCE_SHORTAGE")
        transfers.append(dict(event=asdict(event), before=before, after=(r_pool, f_pool), status=_status(fail, q)))
        all_fail.extend(fail); all_q.extend(q)

    for interval, row in zip(leg.intervals, rows):
        start, end = _time(interval.start), _time(interval.end)
        boundary(start, row["inventory_before_kwh"])
        fail, q, actor_rows = [], [], {}
        pool_before = (r_pool, f_pool)
        valid_allocation = row["allocation"]["status"] == "PASS_SCN"
        if not valid_allocation:
            (fail if row["allocation"]["status"] == "FAIL" else q).append("ACTOR_ALLOCATION_"+row["allocation"]["status"])
        for request in interval.requests:
            matches = [r for r in g.rights if r.actor_id == request.actor_id
                       and _time(r.start) <= start and end <= _time(r.end)]
            active = request.charge_ac_kw > 0 or request.discharge_ac_kw > 0
            allocation = row["allocation"]["actors"][request.actor_id].get("allocation")
            if not matches:
                if active: fail.append(request.actor_id+":OUTSIDE_RIGHTS_WINDOW")
                actor_rows[request.actor_id] = dict(remaining_available_inventory_kwh=0., status="EXPIRED_OR_ABSENT_RIGHT", requested_active_hours=interval.hours if active else 0.)
                continue
            right = matches[0]
            b = budget_by_id[right.budget_id]
            outside_service = not (_time(right.service_start) <= start and end <= _time(right.service_end))
            outside_budget = not (_time(b.start) <= start and end <= _time(b.end))
            if active and outside_budget: fail.append(request.actor_id+":OUTSIDE_BUDGET_WINDOW")
            if active and outside_service: fail.append(request.actor_id+":OUTSIDE_SERVICE_WINDOW")
            for direction in ("charge", "discharge"):
                term = getattr(right, direction+"_ac_kw")
                requested = getattr(request, direction+"_ac_kw")
                if term.status == "Q": q.append(request.actor_id+":"+direction+"_POWER_Q")
                elif requested-term.value > _allowance(case, requested*interval.hours, term.value*interval.hours)/interval.hours:
                    fail.append(request.actor_id+":"+direction+"_REQUEST_POWER_EXCEEDED")
                if allocation is not None and term.value is not None and allocation[direction+"_ac_kwh"]-term.value*interval.hours > _allowance(case, allocation[direction+"_ac_kwh"]):
                    fail.append(request.actor_id+":"+direction+"_ADMITTED_POWER_EXCEEDED")
            duration_before = None if right.callable_hours.value is None or called[right.right_id] is None else right.callable_hours.value-called[right.right_id]
            known_draw_before = known_drawn[right.right_id]
            known_called_before = known_called[right.right_id]
            known_budget_before = known_budget_drawn[right.budget_id]
            duration_upper_before = None if right.callable_hours.value is None else right.callable_hours.value-known_called_before
            energy_upper_before = None if right.draw_kwh.value is None else right.draw_kwh.value-known_draw_before
            # Only NONE rules have a fixed initial whole-window budget ceiling.
            # Possible past credited recharge forbids this bound for other rules.
            budget_upper_before = (b.draw_kwh.value-known_budget_before
                                   if b.replenishment == "NONE" and b.draw_kwh.value is not None else None)
            if duration_before is None: q.append(request.actor_id+":DURATION_Q")
            if active and any(bound is not None and interval.hours-bound > 1e-12
                              for bound in (duration_before, duration_upper_before)):
                fail.append(request.actor_id+":REQUEST_DURATION_EXCEEDED")
            right_remaining = None if right.draw_kwh.value is None or drawn[right.right_id] is None else right.draw_kwh.value-drawn[right.right_id]
            before_budget = budget_remaining[right.budget_id]
            inventory = row["inventory_before_kwh"]
            pool = (r_pool if request.actor_id == case.identity.state_actor_id else f_pool) if g.mode == PROTECTED else inventory
            physical_available, shared_headroom, available = _drawable_inventory(
                case, g, inventory, pool, right_remaining, before_budget)
            if outside_service or outside_budget or (duration_before is not None and duration_before <= 0): available = 0.
            actor_allocation = row["allocation"]["actors"][request.actor_id]
            local_use_known = actor_allocation["status"] == "PASS_SCN"
            # A locally reconciled, exactly identified submitted use may already
            # contradict its own right. Another actor's missing row cannot hide
            # that fact, and does not authorize advancing the uncertain ledger.
            if local_use_known:
                debit, credit = allocation["inventory_debit_kwh"], allocation["inventory_credit_kwh"]
                if any(bound is not None and debit-bound > _allowance(case, debit, bound)
                       for bound in (before_budget, budget_upper_before)):
                    fail.append(request.actor_id+":DRAW_BUDGET_EXCEEDED")
                if any(bound is not None and debit-bound > _allowance(case, debit, bound)
                       for bound in (right_remaining, energy_upper_before)):
                    fail.append(request.actor_id+":ENERGY_RIGHT_EXCEEDED")
                if any(bound is not None and allocation["admitted_active_hours"]-bound > 1e-12
                       for bound in (duration_before, duration_upper_before)):
                    fail.append(request.actor_id+":ADMITTED_DURATION_EXCEEDED")
                if g.mode == PROTECTED and pool is not None and pool+credit-debit < -_allowance(case, credit, debit):
                    fail.append(request.actor_id+":PROTECTED_POOL_BORROWING_OR_SHORTAGE")
                known_drawn[right.right_id] = _sum((known_draw_before, debit))
                known_called[right.right_id] = _sum((known_called_before, allocation["admitted_active_hours"]))
                known_budget_drawn[right.budget_id] = _sum((known_budget_before, debit))
            if valid_allocation:
                debit, credit = allocation["inventory_debit_kwh"], allocation["inventory_credit_kwh"]
                drawn[right.right_id] = None if drawn[right.right_id] is None else drawn[right.right_id]+debit
                # Debit is checked before any unknown replenishment or future credit.
                after_debit = None if before_budget is None else before_budget-debit
                if before_budget is None or b.replenishment == "Q":
                    budget_remaining[right.budget_id] = after_debit if credit == 0 else None
                    q.append(request.actor_id+":BUDGET_Q")
                else:
                    budget_remaining[right.budget_id] = after_debit+(credit if b.replenishment == "ATTRIBUTED_CHARGE_CREDIT" and not outside_budget else 0.)
                if right_remaining is None: q.append(request.actor_id+":ENERGY_RIGHT_Q")
                called[right.right_id] = None if called[right.right_id] is None else called[right.right_id]+allocation["admitted_active_hours"]
            else:
                drawn[right.right_id] = None
                called[right.right_id] = None
                budget_remaining[right.budget_id] = None
            actor_rows[request.actor_id] = dict(right_id=right.right_id, budget_id=right.budget_id,
                available_before_kwh=available,
                physical_drawable_inventory_before_kwh=physical_available,
                shared_retained_floor_headroom_before_kwh=shared_headroom,
                availability_is_conditional_actor_ceiling_not_additive=True,
                submitted_actor_use_known=local_use_known,
                known_draw_lower_bound_before_kwh=known_draw_before,
                known_draw_lower_bound_after_kwh=known_drawn[right.right_id],
                energy_right_remaining_upper_bound_before_kwh=energy_upper_before,
                energy_right_remaining_upper_bound_after_kwh=None if right.draw_kwh.value is None else right.draw_kwh.value-known_drawn[right.right_id],
                known_budget_draw_lower_bound_before_kwh=known_budget_before,
                known_budget_draw_lower_bound_after_kwh=known_budget_drawn[right.budget_id],
                non_replenishing_budget_remaining_upper_bound_before_kwh=budget_upper_before,
                non_replenishing_budget_remaining_upper_bound_after_kwh=(b.draw_kwh.value-known_budget_drawn[right.budget_id]
                    if b.replenishment == "NONE" and b.draw_kwh.value is not None else None),
                known_admitted_hours_lower_bound_before=known_called_before,
                known_admitted_hours_lower_bound_after=known_called[right.right_id],
                callable_hours_upper_bound_before=duration_upper_before,
                callable_hours_upper_bound_after=None if right.callable_hours.value is None else right.callable_hours.value-known_called[right.right_id],
                budget_before_kwh=before_budget,
                budget_after_kwh=budget_remaining[right.budget_id], energy_right_before_kwh=right_remaining,
                callable_hours_before=duration_before, callable_hours_after=None if right.callable_hours.value is None or called[right.right_id] is None else right.callable_hours.value-called[right.right_id],
                charge_power_cap_kw=right.charge_ac_kw.value, discharge_power_cap_kw=right.discharge_ac_kw.value,
                requested_active_hours=interval.hours if active else 0., window_end=right.service_end)
        if g.mode == PROTECTED:
            if not valid_allocation or row["inventory_after_kwh"] is None or r_pool is None:
                r_pool = f_pool = None; q.append("PROTECTED_FREE_DECOMPOSITION_Q")
            else:
                for actor, pool_name in ((case.identity.state_actor_id, "R"), (case.identity.household_actor_id, "F")):
                    a = row["allocation"]["actors"][actor]["allocation"]
                    delta = a["inventory_credit_kwh"]-a["inventory_debit_kwh"]
                    if pool_name == "R": r_pool += delta
                    else: f_pool += delta
                if min(r_pool, f_pool) < -_allowance(case, row["inventory_credit_kwh"], row["inventory_debit_kwh"]): fail.append("PROTECTED_POOL_BORROWING_OR_SHORTAGE")
                residual = r_pool+f_pool-row["inventory_after_kwh"]
                if abs(residual) > _allowance(case, row["inventory_credit_kwh"], row["inventory_debit_kwh"]): fail.append("POOL_CONSERVATION")
        minimum = g.minimum_total_retained_kwh
        if minimum.status == "Q": q.append("MINIMUM_TOTAL_RETAINED_Q")
        elif minimum.status == "SCN":
            if row["inventory_after_kwh"] is None: q.append("TOTAL_INVENTORY_Q")
            elif minimum.value-row["inventory_after_kwh"] > _allowance(case, row["inventory_credit_kwh"], row["inventory_debit_kwh"]): fail.append("MINIMUM_TOTAL_RETAINED_FAILED")
        # Remaining availability is at this exact boundary after BOTH admitted
        # actors, not another copy of the pre-use inventory. It is coordinate
        # energy only; independent power/duration/window fields remain visible.
        for request in interval.requests:
            actor_row = actor_rows[request.actor_id]
            right_id = actor_row.get("right_id")
            if right_id is None:
                actor_row["remaining_available_inventory_kwh"] = 0.
                continue
            right = next(r for r in g.rights if r.right_id == right_id)
            energy_left = None if right.draw_kwh.value is None or drawn[right_id] is None else right.draw_kwh.value-drawn[right_id]
            budget_left = budget_remaining[right.budget_id]
            x_after = row["inventory_after_kwh"]
            pool_after = (r_pool if request.actor_id == case.identity.state_actor_id else f_pool) if g.mode == PROTECTED else x_after
            physical_after, shared_after, remaining = _drawable_inventory(
                case, g, x_after, pool_after, energy_left, budget_left)
            actor_row["physical_drawable_inventory_after_kwh"] = physical_after
            actor_row["shared_retained_floor_headroom_after_kwh"] = shared_after
            if (end >= _time(right.service_end) or not (_time(budget_by_id[right.budget_id].start) <= end < _time(budget_by_id[right.budget_id].end))
                    or (actor_row["callable_hours_after"] is not None and actor_row["callable_hours_after"] <= 0)):
                remaining = 0.
            actor_row["remaining_available_inventory_kwh"] = remaining
            actor_row["energy_right_after_kwh"] = energy_left
        result.append(dict(interval_id=interval.interval_id, status=_status(fail, q), failures=fail, unknowns=q,
                           protected_free_before_kwh=pool_before, protected_free_after_kwh=(r_pool, f_pool), actors=actor_rows))
        all_fail.extend(fail); all_q.extend(q)
    boundary(_time(leg.intervals[-1].end), rows[-1]["inventory_after_kwh"])
    return dict(status=_status(all_fail, all_q), failures=all_fail, unknowns=all_q,
                intervals=result, transfers=transfers, remaining_budgets_kwh=budget_remaining,
                terminal_protected_free_kwh=(r_pool, f_pool))


def _idle(case, leg, rows):
    supplied = leg.idle_accounting
    if type(supplied) is Unknown:
        _unknown(supplied)
        return dict(status="Q", reason=supplied.reason, ac_energy_debit_kwh=None, dc_inventory_drain_kwh=None)
    _require(type(supplied) is IdleAccounting and case.identity.coordinate == REFERENCE,
             "E2 idle proxy requires explicit reference exposure")
    _require(case.executor.identity == "SAX_2026_A1_V23.50_DISCHARGE_EQUIVALENT_E2_REFERENCE",
             "synthetic reference cannot acquire SAX idle authority")
    _tuple(supplied.interval_ids, "idle exposure interval IDs")
    _require(len(set(supplied.interval_ids)) == len(supplied.interval_ids), "duplicate idle exposure")
    by_id = {i.interval_id: (i, r) for i, r in zip(leg.intervals, rows)}
    _require(set(supplied.interval_ids) <= set(by_id), "idle exposure outside supplied horizon")
    selected = [by_id[k] for k in supplied.interval_ids]
    _require(all(not any(q.charge_ac_kw or q.discharge_ac_kw for q in i.requests) for i, _ in selected),
             "idle exposure cannot double-count active loss")
    _number(supplied.idle_hours, "explicit idle exposure")
    _require(supplied.idle_hours == _sum(i.hours for i, _ in selected), "idle duration must match exact exposure")
    _require(type(supplied.include_native_empty_component) is bool, "explicit empty-component accounting choice")
    _require(not supplied.include_native_empty_component or not any(r["native"].get("conditional_empty_ac_component_kwh") is not None for _, r in selected),
             "proxy plus same conditional empty-state component double count")
    result = reference.provisional_standby_ac_energy(idle_hours=supplied.idle_hours)
    result["status"] = "E2_AGGREGATE_ONLY"
    result["native_empty_components"] = "DIAGNOSTIC_ONLY_NOT_ADDED"
    if type(supplied.actor_ac_debits_kwh) is Unknown:
        _unknown(supplied.actor_ac_debits_kwh); result["actor_allocation_status"] = "Q"
    else:
        _tuple(supplied.actor_ac_debits_kwh, "idle accounting allocation")
        values = dict(supplied.actor_ac_debits_kwh)
        _require(len(values) == len(supplied.actor_ac_debits_kwh) and set(values) == {case.identity.household_actor_id, case.identity.state_actor_id}, "exact two idle accounting actors")
        for value in values.values(): _number(value, "idle AC overhead allocation")
        residual = _sum(values.values())-result["ac_energy_debit_kwh"]
        result.update(actor_allocation_status="FAIL" if abs(residual) > _allowance(case, result["ac_energy_debit_kwh"]) else "PASS_SCN",
                      actor_ac_debits_kwh=values, allocation_residual_kwh=residual)
    return result


def _financial(case):
    _require(type(case.financial) is FinancialInputs, "explicit financial Q/qualified inputs required")
    _tuple(case.financial.components, "financial components")
    components = dict(case.financial.components)
    _require(len(components) == len(case.financial.components) and set(components) == set(MONEY_FIELDS), "exact separate financial component inventory")
    for value in components.values(): _term(value, na=True, signed=True)
    supplied = case.financial.protection
    status, binding, native_diagnostic = "Q", None, None
    if type(supplied) is Unknown:
        _unknown(supplied)
    else:
        _require(type(supplied) is QualifiedProtection, "qualified native protection or explicit Q required")
        _require(type(supplied.candidate) is benefit.Candidate and type(supplied.frame) is benefit.ComparisonFrame,
                 "native V65 candidate/frame protection input required")
        _require(supplied.actor_id == case.identity.household_actor_id
                 and supplied.comparison_sha256 == comparison_digest(case), "financial actor/counterfactual mismatch")
        _require(supplied.candidate_sha256 == digest(supplied.candidate)
                 and supplied.frame_sha256 == digest(supplied.frame)
                 and supplied.cash_scope_sha256 == benefit.cash_scope_digest(supplied.candidate), "financial candidate/frame/period content mismatch")
        supplied.frame.validate(); supplied.candidate.identity.validate(supplied.frame)
        _require(supplied.frame.claim_scope == "HOUSEHOLD", "population result cannot protect this household")
        supplied.correspondence.validate()
        _term(supplied.full_agreement_effects, qualification=True)
        native_status = benefit._protection(supplied.candidate, supplied.frame)
        _require(native_status == supplied.supplied_status, "claimed protection differs from unchanged native assessment")
        mapped = supplied.correspondence.ready
        status = native_status if mapped and (native_status == "FAIL" or supplied.full_agreement_effects.status == "SCN") else "Q"
        native_diagnostic = dict(status=native_status, native_subject_scope_id=supplied.candidate.identity.scope_id,
                                 candidate_sha256=supplied.candidate_sha256, frame_sha256=supplied.frame_sha256,
                                 cash_scope_sha256=supplied.cash_scope_sha256,
                                 correspondence_mode=supplied.correspondence.mode,
                                 subject_correspondence_qualified=mapped)
        binding = supplied
    return dict(components=components, complete_household_protection_status=status,
                qualified_protection=binding, upstream_protection_diagnostic=native_diagnostic,
                financial_allocation_status="Q",
                calculation_performed=False, monetary_result=None)


def evaluate_shared_use(case):
    """Execute aggregate supplied legs once, then audit allocation and claims."""
    _validate(case)
    legs = {}
    for leg in (case.baseline_leg, case.actual_leg):
        rows, native = _execute(case, leg)
        for interval, row in zip(leg.intervals, rows):
            for key in (*FLOW_FIELDS, "inventory_before_kwh", "inventory_after_kwh"):
                if row[key] is not None: _number(row[key], "native " + key, signed="loss" in key)
            row.update(interval_id=interval.interval_id, physical_event_id=interval.physical_event_id,
                       coordinate=case.identity.coordinate, hours=interval.hours,
                       requested_charge_ac_kw=_sum(r.charge_ac_kw for r in interval.requests),
                       requested_discharge_ac_kw=_sum(r.discharge_ac_kw for r in interval.requests))
            row["allocation"] = _allocate(case, interval, row)
            row["connection"] = _connection(case, interval, row)
            for direction, loss_name in (("charge", "curtailed_charge"), ("discharge", "unserved_discharge")):
                admitted = row[direction+"_ac_kwh"]
                row[loss_name+"_kwh"] = None if admitted is None else max(0., row["requested_"+direction+"_ac_kw"]*interval.hours-admitted)
        terminal = rows[-1]["inventory_after_kwh"]
        legs[leg.leg_id] = dict(rows=rows, native=native, rights=_rights(case, leg, rows), idle_ac=_idle(case, leg, rows),
            physical_status=_status([], [r for r in rows if r["physical_status"] == "Q"]),
            allocation_status=_status([r for r in rows if r["allocation"]["status"] == "FAIL"], [r for r in rows if r["allocation"]["status"] == "Q"]),
            connection_status=_status([r for r in rows if r["connection"]["status"] == "FAIL"], [r for r in rows if r["connection"]["status"] == "Q"]),
            requested_schedule_fulfillment_status=_status(
                [r for r in rows if any(r[k] is not None and r[k] > _allowance(case, r[k]) for k in ("curtailed_charge_kwh", "unserved_discharge_kwh"))],
                [r for r in rows if any(r[k] is None for k in ("curtailed_charge_kwh", "unserved_discharge_kwh"))]),
            initial_inventory_kwh=leg.initial_inventory_kwh, terminal_inventory_kwh=terminal,
            terminal_minus_initial_kwh=None if terminal is None else terminal-leg.initial_inventory_kwh,
            totals={name: None if any(r[name] is None for r in rows) else _sum(r[name] for r in rows) for name in FLOW_FIELDS})
    baseline, actual = legs[case.baseline_leg.leg_id], legs[case.actual_leg.leg_id]
    response, active_response = [], []
    for b, a in zip(baseline["rows"], actual["rows"]):
        bj, aj = b["connection"]["signed_kw"], a["connection"]["signed_kw"]
        kw = None if bj is None or aj is None else bj-aj
        response.append(dict(interval_id=a["interval_id"], response_up_kw=kw,
                             response_up_kwh=None if kw is None else kw*a["hours"],
                             baseline_signed_connection_kw=bj, actual_signed_connection_kw=aj))
        bc, ac = b["connection"]["active_component"]["signed_kw"], a["connection"]["active_component"]["signed_kw"]
        component_kw = None if bc is None or ac is None else bc-ac
        active_response.append(dict(interval_id=a["interval_id"], response_up_kw=component_kw,
                                    response_up_kwh=None if component_kw is None else component_kw*a["hours"],
                                    baseline_active_component_connection_kw=bc,
                                    actual_active_component_connection_kw=ac))
    bterm, aterm = baseline["terminal_inventory_kwh"], actual["terminal_inventory_kwh"]
    h = case.identity.household_actor_id
    foregone = []
    for b, a in zip(baseline["rows"], actual["rows"]):
        ba, aa = b["allocation"]["actors"][h].get("allocation"), a["allocation"]["actors"][h].get("allocation")
        foregone.append(None if ba is None or aa is None or b["allocation"]["status"] != "PASS_SCN" or a["allocation"]["status"] != "PASS_SCN" else ba["discharge_ac_kwh"]-aa["discharge_ac_kwh"])
    response_q = any(r["response_up_kw"] is None for r in response) or case.baseline.qualification.status == "Q"
    active_response_q = any(r["response_up_kw"] is None for r in active_response) or case.baseline.qualification.status == "Q"
    return dict(schema_version=VERSION, case_id=case.case_id, case_sha256=case.content_sha256,
        comparison_sha256=comparison_digest(case), baseline_binding=case.baseline, scope=case.scope,
        coordinate=case.identity.coordinate, input_status="PASS_SCN", legs=legs,
        response=dict(status="Q" if response_q else "CONDITIONAL_SUPPLIED_SCHEDULE_DIFFERENCE",
                      meaning="CONDITIONAL_TOTAL_CONNECTION_RESPONSE",
                      active_component=dict(meaning="CONDITIONAL_ACTIVE_CONVERTER_COMPONENT_RESPONSE",
                          status="Q" if active_response_q else "CONDITIONAL_ACTIVE_CONVERTER_COMPONENT_DIFFERENCE",
                          records=active_response,
                          energy_kwh=None if any(r["response_up_kwh"] is None for r in active_response) else _sum(r["response_up_kwh"] for r in active_response)),
                      records=response, energy_kwh=None if any(r["response_up_kwh"] is None for r in response) else _sum(r["response_up_kwh"] for r in response),
                      actual_minus_baseline_terminal_kwh=None if None in (aterm, bterm) else aterm-bterm,
                      foregone_household_discharge_kwh=None if None in foregone else _sum(foregone)),
        inventory_rebound=dict(scope=case.horizon_completeness, complete_inventory=bterm is not None and aterm is not None,
                              automatic_recharge=False, sustained_availability_status="Q", cycle_adjusted_benefit_status="Q"),
        actual_permissions={p.operation: asdict(p) for p in case.permissions},
        actual_execution_admitted=False, commercial_commitment_status="Q", activation_authority_status="Q",
        actual_delivery_status="Q", automatic_b10_projection=None, real_delivery_admitted=False,
        financial=_financial(case), national_network_value_status="Q",
        physical_dispatch_priority=None, financial_dispatch_priority=None)


def load_shared_use_contract():
    data = json.loads((ROOT/"registry/b07_shared_use_schedule_contract.json").read_text())
    _require(data["schema_version"] == VERSION and data["contract_id"] == "B07-SHARED-USE-SCHEDULE",
             "shared-use registry identity/version")
    _require(data["canonical_entrypoint"] == "modules.B07.shared_use_schedule_contract.evaluate_shared_use"
             and data["coordinates"] == [STORED, REFERENCE] and data["comparison_scopes"] == [ACTIVATION, AGREEMENT]
             and data["rights_modes"] == [ACCESS, PROTECTED], "shared-use registry boundary")
    _require(data["numeric_defaults"] == {} and data["automatic_b10_projection"] is False
             and data["financial_engine"] is False and data["original_task_acceptance_changed"] is False,
             "shared-use registry cannot grant downstream authority")
    _require([r["group"] for r in data["acceptance_map"]] == list(range(1, 21)), "20-group acceptance map required")
    for binding in data["source_bindings"]:
        _require(sha256((ROOT/binding["path"]).read_bytes()).hexdigest() == binding["sha256"],
                 "shared-use native dependency bytes changed: " + binding["path"])
    _require(all(row["tests"] for row in data["acceptance_map"]), "every acceptance group needs executable tests")
    return data
