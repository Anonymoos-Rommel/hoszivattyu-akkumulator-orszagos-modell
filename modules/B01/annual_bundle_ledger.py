"""Dated, atomic household-bundle reservations in one owned annual SCN ledger.

This is planning arithmetic over explicit inputs, not an optimizer, cashflow
qualification producer, actual expenditure, observed completion or network
permission. Calendar-date intervals are half-open; no sub-day interpolation is
performed. The session owns the current revision so callers cannot substitute
an old snapshot when extending the same planning lineage.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import date
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from modules.B01.capability_contract import CapabilitySnapshot, assess_snapshot, load_contract


class AnnualLedgerError(ValueError):
    """Malformed, ambiguous or stale planning input."""


def load_annual_contract():
    path = Path(__file__).resolve().parents[2] / "registry/b01_annual_bundle_contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "1.0.0" or set(contract.get("resource_kinds", {})) != {"ANNUAL_FLOW", "CONCURRENT", "PUBLIC_CASH"}:
        raise AnnualLedgerError("unsupported annual planning contract")
    return contract


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise AnnualLedgerError(f"{field} requires nonempty text")


def _day(value):
    _text(value, "date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise AnnualLedgerError("calendar dates must be YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise AnnualLedgerError("calendar dates must be YYYY-MM-DD")
    return parsed


def _tuple(value, field):
    if not isinstance(value, tuple):
        raise AnnualLedgerError(f"{field} must be an immutable tuple")


def _refs(value):
    _tuple(value, "evidence_refs")
    if not value or len(set(value)) != len(value):
        raise AnnualLedgerError("nonempty unique evidence references required")
    for ref in value:
        _text(ref, "evidence_ref")


def _digest(value):
    def encode(item):
        if isinstance(item, (Decimal, Fraction)):
            return str(item)
        raise TypeError(type(item).__name__)
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=encode).encode()).hexdigest()


@dataclass(frozen=True)
class Quantity:
    value: Decimal | None
    unit: str
    basis: str
    status: str
    evidence_refs: tuple[str, ...]

    def validate(self, *, signed=False):
        _text(self.unit, "quantity unit")
        _text(self.basis, "quantity basis")
        _refs(self.evidence_refs)
        if self.status == "Q":
            if self.value is not None:
                raise AnnualLedgerError("Q quantity must remain null")
        elif self.status not in {"OBS", "DER", "ASS", "SCN", "POL"} or not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise AnnualLedgerError("known quantities require finite Decimal and explicit lineage")
        elif not signed and self.value < 0:
            raise AnnualLedgerError("negative use/release/ceiling is not a credit")


@dataclass(frozen=True)
class ResourceUse:
    use_id: str
    source_event_id: str
    pool_id: str
    quantity: Quantity
    scope_tags: tuple[tuple[str, str], ...]
    starts_on: str
    ends_before: str
    payer_or_resource_holder: str


@dataclass(frozen=True)
class CashViewRestriction:
    evidence_status: str
    evidence_refs: tuple[str, ...]
    scope_note: str


@dataclass(frozen=True)
class CashRelease:
    source_event_id: str
    available_on: str
    quantity: Quantity
    view_restriction: CashViewRestriction | None = None


@dataclass(frozen=True)
class CashPoolQualification:
    semantics: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    scope_note: str


@dataclass(frozen=True)
class ResourceConstraint:
    constraint_id: str
    pool_id: str
    kind: str
    scope_tag: tuple[str, str]
    ceiling: Quantity
    resource_holder: str
    is_pool_total: bool
    opening_on: str | None = None
    opening_balance: Quantity | None = None
    releases: tuple[CashRelease, ...] = ()
    opening_basis: str | None = None
    cash_pool_qualification: CashPoolQualification | None = None


@dataclass(frozen=True)
class PlannedAction:
    proposal_id: str
    action_type: str
    source_work_id: str
    asset_generation_id: str
    starts_on: str
    ends_before: str
    predecessors: tuple[str, ...]
    snapshot: CapabilitySnapshot
    resource_uses: tuple[ResourceUse, ...]


@dataclass(frozen=True)
class QualifiedBundle:
    scope_digest: str
    eligibility: str
    household_floor: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    scope_note: str


@dataclass(frozen=True)
class RequirementCatalogue:
    """Externally qualified complete domain universe for this bounded case."""

    catalogue_id: str
    version: str
    pool_ids: tuple[str, ...]
    completeness: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    scope_note: str


def requirement_catalogue_digest(catalogue: RequirementCatalogue) -> str:
    return _digest(asdict(catalogue))


@dataclass(frozen=True)
class RequirementCoverage:
    proposal_id: str
    pool_id: str
    applicability: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    scope_note: str


@dataclass(frozen=True)
class HouseholdBundle:
    bundle_id: str
    version: str
    household_id: str
    site_id: str
    basis_id: str
    counterfactual_ref: str
    actions: tuple[PlannedAction, ...]
    catalogue_digest: str
    requirement_coverage: tuple[RequirementCoverage, ...]
    qualification: QualifiedBundle | None = None


def bundle_scope_digest(bundle: HouseholdBundle) -> str:
    """Bind work, timing, requirements, technical inputs and comparison scope.

    The qualification is excluded to avoid a circular hash. The ledger's
    separate bundle-version digest includes the qualification as well.
    """
    value = asdict(bundle)
    value.pop("qualification")
    value["actions"] = sorted(value["actions"], key=lambda row: row["proposal_id"])
    return _digest(value)


@dataclass(frozen=True)
class ResourceCheck:
    constraint_id: str
    status: str
    used_or_peak: Fraction | None
    ceiling: Fraction | None
    remaining: Fraction | None
    first_cash_gap_on: str | None
    reason: str
    unit: str | None = None
    basis: str | None = None
    scope_tag: tuple[str, str] | None = None
    evidence_refs: tuple[str, ...] = ()
    evidence_status: str = "SCN"
    known_use_lower_bound: Fraction | None = None


@dataclass(frozen=True)
class SelectionRecord:
    prior_digest: str
    order_ref: str
    ordered_input_digest: str
    accepted_bundle_ids: tuple[str, ...]


@dataclass(frozen=True)
class LedgerState:
    ledger_id: str
    plan_year: int
    plan_basis_id: str
    calendar_timezone: str
    constraints: tuple[ResourceConstraint, ...]
    requirement_catalogue: RequirementCatalogue
    opening_uses_state: str
    opening_uses_refs: tuple[str, ...]
    opening_uses: tuple[ResourceUse, ...]
    bundles: tuple[HouseholdBundle, ...]
    selection_history: tuple[SelectionRecord, ...]
    revision: int
    prior_digest: str | None
    digest: str


@dataclass(frozen=True)
class BundleDecision:
    bundle_id: str
    status: str
    reasons: tuple[str, ...]
    resource_checks: tuple[ResourceCheck, ...] = ()


@dataclass(frozen=True)
class ReservationResult:
    status: str
    order_ref: str
    ordered_input_digest: str
    before_digest: str
    after_digest: str
    decisions: tuple[BundleDecision, ...]
    resource_checks: tuple[ResourceCheck, ...]
    distinct_planned_households: int
    planned_actions: int
    active_set_digest: str
    joint_network_status: str
    actual_funding_or_completion: bool = False


@dataclass(frozen=True)
class JointNetworkAssessment:
    active_set_digest: str
    plan_year: int
    status: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    scope_note: str


def _state_digest(state: LedgerState):
    value = asdict(state)
    value.pop("digest")
    return _digest(value)


def _compatible(quantity, ceiling):
    if quantity.unit != ceiling.unit or quantity.basis != ceiling.basis:
        raise AnnualLedgerError("resource unit/basis mismatch; conversions must be qualified upstream")


def _validate_use(use: ResourceUse, year: int):
    if not isinstance(use, ResourceUse):
        raise AnnualLedgerError("typed ResourceUse required")
    for name in ("use_id", "source_event_id", "pool_id", "payer_or_resource_holder"):
        _text(getattr(use, name), name)
    use.quantity.validate()
    start, stop = _day(use.starts_on), _day(use.ends_before)
    if not date(year, 1, 1) <= start < stop <= date(year + 1, 1, 1):
        raise AnnualLedgerError("resource interval must be explicitly contained in this annual window")
    _tuple(use.scope_tags, "scope tags")
    if not use.scope_tags or len(set(use.scope_tags)) != len(use.scope_tags):
        raise AnnualLedgerError("explicit unique resource scope tags required")
    for tag in use.scope_tags:
        if not isinstance(tag, tuple) or len(tag) != 2:
            raise AnnualLedgerError("scope tags require scheme and identifier")
        for value in tag:
            _text(value, "scope tag")
    if len({tag[0] for tag in use.scope_tags}) != len(use.scope_tags):
        raise AnnualLedgerError("one use needs one explicit location per scope scheme; qualify split allocations upstream")


def _validate_constraint(item: ResourceConstraint, year: int):
    for name in ("constraint_id", "pool_id", "resource_holder"):
        _text(getattr(item, name), name)
    if item.kind not in {"ANNUAL_FLOW", "CONCURRENT", "PUBLIC_CASH"}:
        raise AnnualLedgerError("unknown resource accounting kind")
    if type(item.is_pool_total) is not bool:
        raise AnnualLedgerError("pool-total role must be an explicit boolean")
    item.ceiling.validate()
    if not isinstance(item.scope_tag, tuple) or len(item.scope_tag) != 2:
        raise AnnualLedgerError("constraint scope needs explicit scheme and identifier")
    for value in item.scope_tag:
        _text(value, "constraint scope")
    _tuple(item.releases, "cash releases")
    if item.kind != "PUBLIC_CASH":
        if item.opening_on is not None or item.opening_balance is not None or item.releases or item.opening_basis is not None or item.cash_pool_qualification is not None:
            raise AnnualLedgerError("non-cash resources cannot contain cash funding")
        return
    if item.opening_on != f"{year:04d}-01-01" or item.opening_basis != "BEFORE_ALL_DECLARED_IN_YEAR_DEBITS":
        raise AnnualLedgerError("cash opening must be January 1 before all declared in-year debits")
    if not isinstance(item.opening_balance, Quantity):
        raise AnnualLedgerError("cash opening balance must be explicit, including Q or zero")
    item.opening_balance.validate(signed=True)
    _compatible(item.opening_balance, item.ceiling)
    qualification = item.cash_pool_qualification
    if item.is_pool_total:
        if not isinstance(qualification, CashPoolQualification) or qualification.semantics != "FUNGIBLE_POOL_NONADDITIVE_ACCESS_CEILINGS":
            raise AnnualLedgerError("cash pool requires explicit qualified fungibility and non-additive access-ceiling semantics")
        if qualification.evidence_status not in {"SCN", "DER"}:
            raise AnnualLedgerError("cash-pool semantics must be explicitly qualified SCN or DER")
        _refs(qualification.evidence_refs)
        _text(qualification.scope_note, "cash-pool qualification scope")
    elif qualification is not None:
        raise AnnualLedgerError("cash subviews inherit the pool-total qualification")
    seen = set()
    for release in item.releases:
        if not isinstance(release, CashRelease):
            raise AnnualLedgerError("typed cash receipt required")
        _text(release.source_event_id, "cash receipt identity")
        if release.source_event_id in seen:
            raise AnnualLedgerError("duplicate cash receipt in one constraint view")
        seen.add(release.source_event_id)
        release.quantity.validate()
        _compatible(release.quantity, item.ceiling)
        if _day(release.available_on).year != year:
            raise AnnualLedgerError("cash receipt belongs to another annual window")
        restriction = release.view_restriction
        if restriction is not None:
            if item.is_pool_total or not isinstance(restriction, CashViewRestriction):
                raise AnnualLedgerError("receipt view restrictions belong only to cash subviews")
            if restriction.evidence_status not in {"SCN", "DER"}:
                raise AnnualLedgerError("receipt view restriction must be qualified SCN or DER")
            _refs(restriction.evidence_refs)
            _text(restriction.scope_note, "receipt access restriction scope")


def _validate_funding_views(constraints):
    roots = {item.pool_id: {receipt.source_event_id: receipt for receipt in item.releases}
             for item in constraints if item.kind == "PUBLIC_CASH" and item.is_pool_total}
    funding_pools = {}
    for item in constraints:
        for release in item.releases:
            if release.source_event_id in funding_pools and funding_pools[release.source_event_id] != item.pool_id:
                raise AnnualLedgerError("one funding receipt cannot finance independent resource pools")
            funding_pools[release.source_event_id] = item.pool_id
            if item.is_pool_total:
                continue
            root = roots[item.pool_id].get(release.source_event_id)
            if root is None:
                raise AnnualLedgerError("cash subview receipt must bind an existing pool-total source event")
            if _day(release.available_on) < _day(root.available_on):
                raise AnnualLedgerError("cash subview cannot make a source receipt available earlier")
            if release.quantity.value is not None and (root.quantity.value is None or release.quantity.value > root.quantity.value):
                raise AnnualLedgerError("cash subview receipt cannot exceed or resolve its unknown pool-total amount")
            if (release.available_on, release.quantity) != (root.available_on, root.quantity):
                if release.view_restriction is None:
                    raise AnnualLedgerError("changed cash view facts require an explicit qualified access restriction")
                if release.quantity.status not in {"DER", "SCN", "Q"}:
                    raise AnnualLedgerError("a restricted view is derived/scenario/unknown, not a new observed source receipt")


def _all_uses(state, bundles=None):
    bundles = state.bundles if bundles is None else bundles
    return state.opening_uses + tuple(use for bundle in bundles for action in bundle.actions for use in action.resource_uses)


def _check_unique_uses(uses):
    ids, source_ids = set(), set()
    for use in uses:
        source_key = use.source_event_id
        if use.use_id in ids or source_key in source_ids:
            raise AnnualLedgerError("duplicate resource use or aliased source cost/event")
        ids.add(use.use_id)
        source_ids.add(source_key)


def _bundle_problems(bundle: HouseholdBundle, state: LedgerState) -> tuple[str, ...]:
    for name in ("bundle_id", "version", "household_id", "site_id", "basis_id", "counterfactual_ref"):
        _text(getattr(bundle, name), name)
    _tuple(bundle.actions, "bundle actions")
    if not bundle.actions:
        raise AnnualLedgerError("a work bundle needs at least one declared action")
    by_id = {}
    work_keys = set()
    problems = []
    if bundle.catalogue_digest != requirement_catalogue_digest(state.requirement_catalogue):
        raise AnnualLedgerError("bundle does not bind this exact qualified requirement-domain catalogue/version")
    if state.requirement_catalogue.completeness != "COMPLETE":
        problems.append("REQUIREMENT_DOMAIN_UNIVERSE_UNKNOWN")
    for action in bundle.actions:
        for name in ("proposal_id", "source_work_id", "asset_generation_id"):
            _text(getattr(action, name), name)
        if action.proposal_id in by_id:
            raise AnnualLedgerError("duplicate proposal ID")
        by_id[action.proposal_id] = action
        if action.action_type not in load_contract()["actions"]:
            raise AnnualLedgerError("unknown component action")
        work_key = (bundle.site_id, action.action_type, action.asset_generation_id)
        if work_key in work_keys or any(item.source_work_id == action.source_work_id for item in bundle.actions if item is not action):
            raise AnnualLedgerError("proposal alias cannot create duplicate physical work")
        work_keys.add(work_key)
        start, stop = _day(action.starts_on), _day(action.ends_before)
        if not date(state.plan_year, 1, 1) <= start < stop <= date(state.plan_year + 1, 1, 1):
            raise AnnualLedgerError("action interval must be contained in the declared year")
        _tuple(action.predecessors, "predecessors")
        if len(set(action.predecessors)) != len(action.predecessors):
            raise AnnualLedgerError("duplicate predecessor")
        identity = action.snapshot.identity
        if (identity.household_id, identity.site_id, identity.basis_id) != (bundle.household_id, bundle.site_id, bundle.basis_id):
            raise AnnualLedgerError("action household/site/comparison basis mismatch")
        if action.snapshot.as_of != action.starts_on:
            raise AnnualLedgerError("action prerequisites must be qualified at the actual planned start date")
        assessment = assess_snapshot(action.snapshot)
        decision = next(item for item in assessment.actions if item.action_id == action.action_type)
        if decision.programme_preconditions.status != "PASS":
            problems.extend(decision.programme_preconditions.failed + decision.programme_preconditions.unknown)
        _tuple(action.resource_uses, "resource uses")
        for use in action.resource_uses:
            _validate_use(use, state.plan_year)
    _tuple(bundle.requirement_coverage, "requirement-domain coverage")
    coverage = {}
    for item in bundle.requirement_coverage:
        key = (item.proposal_id, item.pool_id)
        if key in coverage or item.proposal_id not in by_id or item.pool_id not in state.requirement_catalogue.pool_ids:
            raise AnnualLedgerError("duplicate or unknown action/domain coverage")
        _refs(item.evidence_refs)
        _text(item.scope_note, "requirement-domain scope")
        if item.applicability not in {"REQUIRED", "NOT_REQUIRED", "Q"}:
            raise AnnualLedgerError("requirement domain needs REQUIRED, NOT_REQUIRED or Q")
        allowed = {"Q"} if item.applicability == "Q" else {"DER", "SCN"}
        if item.evidence_status not in allowed:
            raise AnnualLedgerError("requirement applicability has incompatible evidence status")
        coverage[key] = item
    for action in bundle.actions:
        for pool in state.requirement_catalogue.pool_ids:
            item = coverage.get((action.proposal_id, pool))
            uses = [use for use in action.resource_uses if use.pool_id == pool]
            if item is None or item.applicability == "Q":
                problems.append(f"{action.proposal_id}:{pool}:REQUIREMENT_APPLICABILITY_UNKNOWN")
            elif item.applicability == "NOT_REQUIRED":
                if uses:
                    raise AnnualLedgerError("not-required domain cannot also contain resource uses")
            elif not uses:
                problems.append(f"{action.proposal_id}:{pool}:REQUIRED_RESOURCE_USE_MISSING")
        if any(use.pool_id not in state.requirement_catalogue.pool_ids for use in action.resource_uses):
            raise AnnualLedgerError("resource use is outside the qualified requirement-domain universe")
    for action in bundle.actions:
        for predecessor in action.predecessors:
            if predecessor not in by_id or predecessor == action.proposal_id or _day(by_id[predecessor].ends_before) > _day(action.starts_on):
                raise AnnualLedgerError("missing, cyclic or later planned predecessor")
    qualification = bundle.qualification
    if qualification is None:
        problems.append("JOINT_BUNDLE_QUALIFICATION_UNKNOWN")
    else:
        if qualification.scope_digest != bundle_scope_digest(bundle):
            raise AnnualLedgerError("joint qualification does not match exact bundle work/dates/costs/basis")
        _refs(qualification.evidence_refs)
        _text(qualification.scope_note, "joint bundle scope")
        if qualification.evidence_status != "SCN":
            raise AnnualLedgerError("prospective bundle qualification must remain explicit SCN")
        for name in ("eligibility", "household_floor"):
            value = getattr(qualification, name)
            if value not in {"PASS", "FAIL", "UNKNOWN"}:
                raise AnnualLedgerError("joint bundle conditions require PASS/FAIL/UNKNOWN")
            if value != "PASS":
                problems.append(f"JOINT_BUNDLE_{name.upper()}_{value}")
    _check_unique_uses(tuple(use for action in bundle.actions for use in action.resource_uses))
    return tuple(sorted(set(problems)))


def _cash_check(limit, selected, *, unknown_opening_uses=False):
    """Preserve a definite past gap even when other nonnegative uses are Q."""
    if limit.opening_balance.value is None:
        return "UNKNOWN", None, "Opening cash remains Q."
    upper = Fraction(limit.opening_balance.value)
    upper_unbounded = False
    any_unknown = unknown_opening_uses or any(use.quantity.value is None for use in selected) or any(item.quantity.value is None for item in limit.releases)
    dates = sorted({limit.opening_on} | {use.starts_on for use in selected} | {item.available_on for item in limit.releases})
    for day in dates:
        receipts = [item for item in limit.releases if item.available_on == day]
        payments = [item for item in selected if item.starts_on == day]
        if any(item.quantity.value is None for item in receipts):
            upper_unbounded = True
        upper += sum((Fraction(item.quantity.value) for item in receipts if item.quantity.value is not None), Fraction())
        upper -= sum((Fraction(item.quantity.value) for item in payments if item.quantity.value is not None), Fraction())
        # Unknown outgoing uses can only lower cash. Unknown future receipts
        # cannot repair a gap at this earlier settlement date.
        if not upper_unbounded and upper < 0:
            return "FAIL", day, "Definite cash shortfall at a payment/debit date, even before unknown outgoing uses."
    if any_unknown:
        return "UNKNOWN", None, "Dated funding/use remains Q; no complete cash result is asserted."
    return "PASS", None, "Dated available cash covers the declared payments."


def _resource_checks(state, bundles=None):
    uses = _all_uses(state, bundles)
    _check_unique_uses(uses)
    checks = []
    unknown_opening = state.opening_uses_state == "Q"
    if unknown_opening:
        checks.append(ResourceCheck("OPENING_COMMITMENTS", "UNKNOWN", None, None, None, None,
                                    "Opening in-year uses are unknown, not zero.", evidence_refs=state.opening_uses_refs))
    for use in uses:
        views = [limit for limit in state.constraints if limit.pool_id == use.pool_id]
        totals = [limit for limit in views if limit.is_pool_total]
        schemes = {limit.scope_tag[0] for limit in views}
        missing_schemes = schemes - {tag[0] for tag in use.scope_tags}
        uncovered = {tag for tag in use.scope_tags if tag[0] in schemes} - {limit.scope_tag for limit in views}
        if len(totals) != 1 or totals[0].scope_tag not in use.scope_tags or missing_schemes or uncovered:
            checks.append(ResourceCheck("UNCOVERED:" + use.use_id, "UNKNOWN", None, None, None, None,
                                        "Missing pool-total membership, required scope tag or matching subview; no broader fallback.",
                                        use.quantity.unit, use.quantity.basis, evidence_refs=use.quantity.evidence_refs))
        if views:
            _compatible(use.quantity, views[0].ceiling)
            if use.payer_or_resource_holder != views[0].resource_holder:
                raise AnnualLedgerError("payer/resource-holder mismatch; one actor's money/capacity is not another's")
    for limit in state.constraints:
        selected = [use for use in uses if use.pool_id == limit.pool_id and (limit.is_pool_total or limit.scope_tag in use.scope_tags)]
        if not selected and not unknown_opening:
            continue
        if limit.kind == "PUBLIC_CASH" and {item.source_event_id for item in limit.releases} & {item.source_event_id for item in selected}:
            raise AnnualLedgerError("one cash movement cannot be both funding receipt and payment")
        refs = set(limit.ceiling.evidence_refs) | {ref for use in selected for ref in use.quantity.evidence_refs}
        refs.update(state.opening_uses_refs)
        if limit.kind == "PUBLIC_CASH":
            refs.update(limit.opening_balance.evidence_refs)
            refs.update(ref for item in limit.releases for ref in item.quantity.evidence_refs)
            total = next(item for item in state.constraints if item.pool_id == limit.pool_id and item.is_pool_total)
            refs.update(total.cash_pool_qualification.evidence_refs)
            refs.update(ref for item in total.releases if item.source_event_id in {view.source_event_id for view in limit.releases}
                        for ref in item.quantity.evidence_refs)
            refs.update(ref for item in limit.releases if item.view_restriction is not None for ref in item.view_restriction.evidence_refs)
        cap = None if limit.ceiling.value is None else Fraction(limit.ceiling.value)
        known = [use for use in selected if use.quantity.value is not None]
        if limit.kind == "CONCURRENT" and known:
            boundaries = sorted({_day(use.starts_on) for use in known} | {_day(use.ends_before) for use in known})
            lower = max(sum((Fraction(use.quantity.value) for use in known if _day(use.starts_on) <= day < _day(use.ends_before)), Fraction()) for day in boundaries)
        else:
            lower = sum((Fraction(use.quantity.value) for use in known), Fraction())
        used = lower if not unknown_opening and len(known) == len(selected) else None
        if cap is not None and lower > cap:
            status, reason = "FAIL", "Known use/peak lower bound already exceeds the declared ceiling."
        elif cap is None or used is None:
            status, reason = "UNKNOWN", "Resource quantity/ceiling remains Q; known lower bound is not a full total."
        else:
            status, reason = "PASS", "Within explicit resource ceiling."
        gap = None
        if limit.kind == "PUBLIC_CASH":
            cash_status, gap, cash_reason = _cash_check(limit, selected, unknown_opening_uses=unknown_opening)
            if cash_status == "FAIL" or status == "FAIL":
                status = "FAIL"
            elif cash_status == "UNKNOWN":
                status = "UNKNOWN"
            reason += " " + cash_reason
        checks.append(ResourceCheck(limit.constraint_id, status, used, cap,
                                    None if cap is None or used is None else cap - used,
                                    gap, reason, limit.ceiling.unit, limit.ceiling.basis,
                                    limit.scope_tag, tuple(sorted(refs)), "SCN", lower))
    return tuple(checks)


class AnnualPlanSession:
    """One offline ledger owner. External durable storage/locking is not implied."""

    def __init__(self, *, ledger_id: str, plan_year: int, plan_basis_id: str,
                 calendar_timezone: str, constraints: tuple[ResourceConstraint, ...],
                 requirement_catalogue: RequirementCatalogue,
                 opening_uses_state: str, opening_uses_refs: tuple[str, ...],
                 opening_uses: tuple[ResourceUse, ...]):
        load_annual_contract()
        for name, value in (("ledger_id", ledger_id), ("plan_basis_id", plan_basis_id), ("calendar_timezone", calendar_timezone)):
            _text(value, name)
        try:
            ZoneInfo(calendar_timezone)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise AnnualLedgerError("calendar timezone must be a known IANA identifier") from exc
        if type(plan_year) is not int or not 1 <= plan_year <= 9998:
            raise AnnualLedgerError("explicit valid calendar year required")
        _tuple(constraints, "constraints")
        _tuple(opening_uses, "opening uses")
        _refs(opening_uses_refs)
        if not constraints or len({item.constraint_id for item in constraints}) != len(constraints):
            raise AnnualLedgerError("explicit uniquely identified resource constraints required")
        if opening_uses_state not in {"NONE", "USES", "Q"} or (opening_uses_state == "USES") != bool(opening_uses):
            raise AnnualLedgerError("opening obligations require explicit NONE, USES or Q")
        for item in constraints:
            _validate_constraint(item, plan_year)
        if not isinstance(requirement_catalogue, RequirementCatalogue):
            raise AnnualLedgerError("explicit qualified requirement-domain catalogue required")
        for name in ("catalogue_id", "version", "scope_note"):
            _text(getattr(requirement_catalogue, name), name)
        _tuple(requirement_catalogue.pool_ids, "catalogue pools")
        _refs(requirement_catalogue.evidence_refs)
        if not requirement_catalogue.pool_ids or len(set(requirement_catalogue.pool_ids)) != len(requirement_catalogue.pool_ids):
            raise AnnualLedgerError("requirement-domain catalogue needs unique pool identities")
        if requirement_catalogue.completeness not in {"COMPLETE", "Q"} or requirement_catalogue.evidence_status not in ({"Q"} if requirement_catalogue.completeness == "Q" else {"SCN", "DER"}):
            raise AnnualLedgerError("requirement-domain completeness must be qualified or Q")
        if set(requirement_catalogue.pool_ids) != {item.pool_id for item in constraints}:
            raise AnnualLedgerError("catalogue and declared resource pools differ")
        for pool in requirement_catalogue.pool_ids:
            if sum(item.pool_id == pool and item.is_pool_total for item in constraints) != 1:
                raise AnnualLedgerError("each explicitly bounded resource pool needs exactly one total view")
        dimensions = {}
        for item in constraints:
            signature = (item.kind, item.ceiling.unit, item.ceiling.basis, item.resource_holder)
            if item.pool_id in dimensions and dimensions[item.pool_id] != signature:
                raise AnnualLedgerError("constraint views of one resource must share kind/unit/basis")
            dimensions[item.pool_id] = signature
        _validate_funding_views(constraints)
        for use in opening_uses:
            _validate_use(use, plan_year)
        _check_unique_uses(opening_uses)
        state = LedgerState(ledger_id, plan_year, plan_basis_id, calendar_timezone, constraints,
                            requirement_catalogue, opening_uses_state, opening_uses_refs, opening_uses, (), (), 0, None, "")
        self._state = replace(state, digest=_state_digest(state))
        self._history = (self._state,)

    @property
    def state(self):
        return self._state

    @property
    def history(self):
        return self._history

    @property
    def active_set_digest(self):
        return _digest({"ledger_id": self._state.ledger_id, "plan_year": self._state.plan_year,
                        "plan_basis_id": self._state.plan_basis_id, "calendar_timezone": self._state.calendar_timezone,
                        "requirement_catalogue": asdict(self._state.requirement_catalogue),
                        "opening_uses_state": self._state.opening_uses_state,
                        "opening_uses_refs": self._state.opening_uses_refs,
                        "opening_uses": asdict(self._state)["opening_uses"],
                        "bundles": asdict(self._state)["bundles"]})

    def assess_joint_network(self, assessment: JointNetworkAssessment | None):
        if assessment is None:
            return "UNKNOWN"
        _refs(assessment.evidence_refs)
        _text(assessment.scope_note, "joint network scope")
        if assessment.status not in {"PASS", "FAIL", "UNKNOWN"} or assessment.evidence_status != "SCN":
            raise AnnualLedgerError("joint network result must be an explicitly scoped SCN assessment")
        if assessment.plan_year != self._state.plan_year or assessment.active_set_digest != self.active_set_digest:
            return "UNKNOWN"
        return assessment.status

    def reserve(self, bundles: tuple[HouseholdBundle, ...], *, expected_revision: str, order_ref: str) -> ReservationResult:
        _tuple(bundles, "ordered bundles")
        _text(order_ref, "explicit order reference")
        if expected_revision != self._state.digest:
            raise AnnualLedgerError("stale revision: reserve against the session's current state")
        before = self._state
        if _state_digest(before) != before.digest:
            raise AnnualLedgerError("ledger integrity failure")
        # Validate every new candidate before changing any session state.
        problems = [(bundle, _bundle_problems(bundle, before)) for bundle in bundles]
        ordered_input_digest = _digest([asdict(bundle) for bundle in bundles])
        active = list(before.bundles)
        decisions = []
        for bundle, issues in problems:
            same_id = next((old for old in active if old.bundle_id == bundle.bundle_id), None)
            if same_id is not None:
                status = "ALREADY_RESERVED" if _digest(asdict(same_id)) == _digest(asdict(bundle)) else "REQUALIFICATION_REQUIRED"
                decisions.append(BundleDecision(bundle.bundle_id, status, ("Existing reservation is retained without a second debit.",)))
                continue
            if any(old.household_id == bundle.household_id for old in active):
                decisions.append(BundleDecision(bundle.bundle_id, "REQUALIFICATION_REQUIRED", ("One qualified bundle per household in this annual ledger; changing it requires full requalification.",)))
                continue
            if issues:
                decisions.append(BundleDecision(bundle.bundle_id, "BLOCKED_PREREQUISITE", issues))
                continue
            old_work = {(old.site_id, action.action_type, action.asset_generation_id) for old in active for action in old.actions}
            old_sources = {action.source_work_id for old in active for action in old.actions}
            if any((bundle.site_id, action.action_type, action.asset_generation_id) in old_work or action.source_work_id in old_sources for action in bundle.actions):
                raise AnnualLedgerError("aliased work/asset generation is already reserved")
            candidate = tuple(active) + (bundle,)
            checks = _resource_checks(before, candidate)
            blocked = tuple(check.constraint_id + ":" + check.reason for check in checks if check.status != "PASS")
            if blocked:
                decisions.append(BundleDecision(bundle.bundle_id, "WAIT_RESOURCE", blocked, checks))
            else:
                active.append(bundle)
                decisions.append(BundleDecision(bundle.bundle_id, "RESERVED_PLANNED", ("Whole qualified bundle reserved atomically; execution and joint network outcome remain separate.",), checks))
        if tuple(active) != before.bundles:
            journal = SelectionRecord(before.digest, order_ref, ordered_input_digest,
                                      tuple(item.bundle_id for item in decisions if item.status == "RESERVED_PLANNED"))
            new = replace(before, bundles=tuple(active), revision=before.revision + 1,
                          selection_history=before.selection_history + (journal,),
                          prior_digest=before.digest, digest="")
            self._state = replace(new, digest=_state_digest(new))
            self._history += (self._state,)
        return ReservationResult("SCN_CONDITIONAL_RESOURCE_RESERVATIONS", order_ref, ordered_input_digest, before.digest, self._state.digest,
                                 tuple(decisions), _resource_checks(self._state), len(self._state.bundles),
                                 sum(len(bundle.actions) for bundle in self._state.bundles), self.active_set_digest,
                                 "UNKNOWN")

    def request_amendment(self, bundle_id: str, *, expected_revision: str):
        if expected_revision != self._state.digest:
            raise AnnualLedgerError("stale revision")
        if not any(bundle.bundle_id == bundle_id for bundle in self._state.bundles):
            raise AnnualLedgerError("unknown reserved bundle")
        return BundleDecision(bundle_id, "REQUALIFICATION_REQUIRED", ("No reservation, payment or commitment was released; requalify the whole affected plan.",))
