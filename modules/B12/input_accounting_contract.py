"""B12 entry contract and synthetic accounting witnesses, not an admission engine.

All input amounts are Decimal. Identities use precision 50, ROUND_HALF_EVEN,
without implicit currency rounding; source rounding belongs in supplied amounts.
External review references are retained, never trusted merely because they exist.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import date
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from types import MappingProxyType, UnionType
from typing import Any, get_args, get_origin, get_type_hints


class B12ContractError(ValueError):
    pass


SYNTHETIC = "SYNTHETIC_WITNESS"
EXTERNAL_Q = "external_admission: source/quantity/scope review resolver not implemented in this slice"
LEGS = ("baseline", "programme")
COST_CATEGORIES = {"INITIAL_CAPEX", "O_AND_M", "INSURANCE", "REPLACEMENT", "DISPOSAL", "TAX"}
TRUTH = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}


def _require(condition, message):
    if not condition:
        raise B12ContractError(message)


def _text(value, name):
    _require(isinstance(value, str) and bool(value.strip()), f"{name}: nonempty reference required")


@dataclass(frozen=True)
class Period:
    start: date
    end: date

    def __post_init__(self):
        _require(type(self.start) is date and type(self.end) is date and self.start <= self.end,
                 "period: exact ordered dates required")


@dataclass(frozen=True)
class Reference:
    """A declared scenario, external review pointer, or unresolved dependency.

    EXTERNAL_ADMISSION is a reference to an upstream review, not a local assertion
    that review was verified. No owner-per-datum approval is required or created.
    """
    kind: str
    ref: str | None
    reason: str | None
    acquisition_ref: str | None

    def __post_init__(self):
        _require(self.kind in {SYNTHETIC, "EXTERNAL_ADMISSION", "Q"}, "reference kind")
        if self.kind == "Q":
            _require(self.ref is None, "Q reference cannot carry a resolved value")
            _text(self.reason, "Q reason")
            _text(self.acquisition_ref, "Q acquisition")
        else:
            _text(self.ref, "reference")
            _require(self.reason is None and self.acquisition_ref is None, "resolved reference with Q fields")
            _require((self.ref.startswith(SYNTHETIC)) == (self.kind == SYNTHETIC),
                     "fixture references cannot masquerade as external admission")


@dataclass(frozen=True)
class Scalar:
    value: Decimal | None
    unit: str
    truth: str
    reference_period: Period
    basis_id: str
    source_ids: tuple[str, ...]
    scenario_ref: str | None
    evidence_tier: str | None
    admission_ref: str | None
    reason: str | None
    acquisition_ref: str | None

    def __post_init__(self):
        _text(self.unit, "unit")
        _text(self.basis_id, "basis_id")
        _require(self.truth in TRUTH, "truth status")
        _require(type(self.source_ids) is tuple, "immutable source_ids required")
        _require(isinstance(self.reference_period, Period), "reference period required")
        if self.truth == "Q":
            _require(self.value is None, "Q scalar must have null value")
            _text(self.reason, "Q reason")
            _text(self.acquisition_ref, "Q acquisition")
            _require(not self.source_ids and self.scenario_ref is None and self.admission_ref is None,
                     "Q must not assert numerical provenance")
            return
        _require(type(self.value) is Decimal and self.value.is_finite(),
                 "material values must be finite Decimal, never bool/float/NaN/infinity")
        _require(self.reason is None and self.acquisition_ref is None, "numeric scalar with Q fields")
        _require(self.evidence_tier in {"E1", "E2", "E3"}, "evidence tier required")
        if self.truth in {"OBS", "DER"}:
            _require(bool(self.source_ids) and self.evidence_tier in {"E1", "E2"},
                     "OBS/DER requires evidence lineage")
            _text(self.admission_ref, "quantity-scoped evidence/debt review reference")
            _require(self.scenario_ref is None, "observed/derived input cannot conceal scenario lineage")
        else:
            _text(self.scenario_ref, "explicit scenario/policy/assumption reference")
        for source in self.source_ids:
            _text(source, "source_id")
            _require(not source.startswith(SYNTHETIC), "fixture is not a source_id")


@dataclass(frozen=True)
class Section:
    state: str  # NONE, ROWS, Q; even absence is an explicit declaration
    rows: tuple[Any, ...]
    authority: Reference
    absent_legs: tuple[str, ...]

    def __post_init__(self):
        _require(type(self.rows) is tuple and self.state in {"NONE", "ROWS", "Q"}, "section state/tuple required")
        _require((self.state == "ROWS") == bool(self.rows), "empty rows cannot mean zero/none")
        _require(isinstance(self.authority, Reference), "section authority required")
        _require(type(self.absent_legs) is tuple and len(set(self.absent_legs)) == len(self.absent_legs)
                 and all(leg in LEGS for leg in self.absent_legs), "explicit absent-leg declarations required")
        _require((self.state == "Q") == (self.authority.kind == "Q"), "section Q/authority contradiction")


@dataclass(frozen=True)
class PayerShare:
    household_id: str
    dwelling_id: str
    role: str
    cost_share: Scalar
    payment_share: Scalar


@dataclass(frozen=True)
class Scope:
    scope_id: str
    household_id: str
    shares: tuple[PayerShare, ...]
    mapping: Reference
    # Shares describe an explicitly enumerated payer pool, never a dwelling count.


@dataclass(frozen=True)
class MoneyBasis:
    basis_id: str
    currency: str
    nominal_real: str
    price_date: date
    convention: Reference


@dataclass(frozen=True)
class Conversion:
    original: Scalar
    converted: Scalar
    multiplier: Scalar
    conversion_date: date
    method: Reference


@dataclass(frozen=True)
class Cost:
    cost_id: str
    event_id: str
    leg: str
    component_id: str
    asset_generation_id: str
    phase_ref: str
    category: str
    quantity: Scalar
    gross: Scalar
    net: Scalar
    vat: Scalar
    vat_representation: str
    tax_treatment: Reference
    eligible_gross: Scalar
    eligibility_rule: Reference
    eligibility_caps: tuple[Scalar, ...]
    period: Period
    scope_ref: str
    payer: str
    payee: str
    settlement_ref: str
    inclusion_scope: tuple[str, ...]
    procurement_basis: str
    attribution: Reference


@dataclass(frozen=True)
class Asset:
    asset_generation_id: str
    leg: str
    component_id: str
    commissioning_date: date
    service_life: Scalar
    life_definition: str
    retired_generation_id: str | None
    replacement_cost_ids: Section
    operating_coverage: Reference
    operating_coverage_end: date
    terminal_kind: str  # NONE, CASH_SALE, NONCASH, Q
    terminal_value: Scalar
    terminal_receipt_id: str | None


@dataclass(frozen=True)
class BillInput:
    bill_id: str
    event_id: str
    leg: str
    carrier: str
    end_use: str
    tariff_load_scope: str
    tariff_connection_scope: str
    physical_ref: str
    service_basis_ref: str
    meter_id: str
    distributor: str
    tariff_layer: str
    product: str
    revision: str
    eligibility: Reference
    service_period: Period
    period: Period
    quantity: Scalar
    consumption_gross: Scalar
    fixed_gross: Scalar
    total_gross: Scalar
    billed_months: Scalar
    discounted_allocation: Scalar
    scope_ref: str
    fixed_charge_key: str
    coverage: Reference
    upstream_status: str
    upstream_price_basis: str
    upstream_source_ids: tuple[str, ...]
    gas_reference_state_ref: str | None
    allocation_ref: Reference

    @classmethod
    def from_b04(cls, bill, *, consumption_gross, fixed_gross, total_gross, **context):
        """Exact Bill-only adapter; caller supplies interval, allocation and money lineage."""
        from modules.B04.engine import Bill
        _require(type(bill) is Bill, "complete B04 Bill required; dynamic energy-only cost is not a bill")
        _require(bill.status == "SCN_CONSTANT_2026_TARIFF_SNAPSHOT" and
                 bill.price_basis == "FROZEN_2026_RATES_NOT_HISTORICAL_OR_FUTURE_INVOICE_VALIDATION",
                 "B04 snapshot labels must be preserved")
        try:
            result = cls(consumption_gross=consumption_gross, fixed_gross=fixed_gross, total_gross=total_gross,
                         upstream_status=bill.status, upstream_price_basis=bill.price_basis,
                         upstream_source_ids=bill.source_ids, **context)
        except TypeError as exc:
            raise B12ContractError("complete explicit B04 invocation context required") from exc
        _shape(result, BillInput)
        for scalar, expected in ((consumption_gross, bill.consumption_charge_huf),
                                 (fixed_gross, bill.fixed_charge_huf), (total_gross, bill.total_huf)):
            _require(scalar.value == expected and scalar.truth == "SCN", "B04 returned gross charge changed")
        _require(_known(result.quantity, result.discounted_allocation) and
                 result.quantity.value == bill.discounted_kwh + bill.excess_kwh and
                 min(result.quantity.value, result.discounted_allocation.value) == bill.discounted_kwh,
                 "B04 physical quantity and caller discount allocation must reconcile")
        _replay_b04(result)
        return result


@dataclass(frozen=True)
class DebtRow:
    event_id: str
    period: Period
    opening: Scalar
    draw: Scalar
    capitalized_interest: Scalar
    capitalized_fees: Scalar
    cash_interest: Scalar
    principal: Scalar
    cash_fees: Scalar
    extinguishment: Scalar
    closing: Scalar
    draw_route: str  # BANK or SUPPLIER
    direct_cost_id: str | None
    fee_route: str  # BANK or WITHHELD (cash_fees already gross, deduct once)
    support_event_id: str | None
    extinguishment_authority: Reference
    accrual_rate: Scalar


@dataclass(frozen=True)
class Instrument:
    instrument_id: str
    leg: str
    kind: str  # EXISTING or PROGRAMME
    lender: str
    borrower: str
    as_of: date
    terms_revision: str
    status: str  # CONDITIONAL or CONFIRMED; not a rule/cap
    amount_kind: str  # DRAW_SCHEDULE, never BORROWING_LIMIT
    access: Reference
    start: date
    maturity: date
    payment_frequency: str
    availability_grace: Reference
    interest_definition: str  # ZERO, SUPPLIED_PERIODIC_OPENING, EXTERNAL_ACCRUAL_Q
    rate_path: Reference
    day_count_compounding: Reference
    balloon_or_refinance: Reference
    rows: Section


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    event_id: str
    leg: str
    category: str  # GRANT, VAT_REFUND, OPERATING, SALE
    payer: str
    beneficiary: str
    amount: Scalar
    period: Period
    status: str  # CONDITIONAL, CONFIRMED
    award_or_contract: Reference
    route: str
    cost_id: str | None
    asset_generation_id: str | None
    allocation: Reference


@dataclass(frozen=True)
class Resource:
    resource_id: str
    event_id: str
    leg: str
    category: str  # NET_INCOME, REQUIRED_NON_ENERGY, RECURRING_RECEIPT
    amount: Scalar
    period: Period
    scope_ref: str
    source_semantics: str
    gross_to_net_or_scope_bridge: Reference
    covered_categories: tuple[str, ...]
    household_size: Scalar
    equivalence_definition: Reference


@dataclass(frozen=True)
class LiquidAsset:
    asset_id: str
    leg: str
    kind: str
    household_id: str
    scope_ref: str
    stock_date: date
    gross: Scalar
    encumbered: Scalar
    disposal_cost: Scalar
    spendable: Scalar
    access: Reference


@dataclass(frozen=True)
class PopulationBinding:
    authority: Reference
    target: str
    target_unit: str
    source_unit: str
    household_dwelling_bridge: Reference
    evidence_class: str
    selection: Reference
    missingness: Reference
    weighting: Reference
    estimator: Reference
    diagnostics: Reference
    uncertainty: Reference
    structural_sensitivity: Reference
    reference_period: Period


@dataclass(frozen=True)
class Policy:
    floor_variable: str
    horizon_variable: str
    floor_metric: Reference
    floor_actor: Reference
    floor_group_period: Reference
    floor_value: Scalar
    reserve: Scalar
    debt_constraint: Reference


@dataclass(frozen=True)
class Valuation:
    discount_rate: Scalar
    basis_id: str
    valuation_date: date
    time_convention: Reference
    terminal_debt_treatment: Reference
    escalation: Reference
    nominal_rate: Scalar
    real_rate: Scalar
    inflation: Scalar


@dataclass(frozen=True)
class Case:
    case_id: str
    mode: str
    intervention_id: str
    archetype_id: str
    region_id: str
    transition_ref: str
    identity_binding: Reference
    scope: Scope
    population: PopulationBinding
    baseline_id: str
    programme_id: str
    as_of: date
    physical_reference_period: Period
    evaluation_period: Period
    reporting_periods: tuple[Period, ...]
    time_grain: str
    service_basis_ref: str
    monetary_basis: MoneyBasis
    other_bases: tuple[MoneyBasis, ...]
    conversions: tuple[Conversion, ...]
    costs: Section
    assets: Section
    bills: Section
    instruments: Section
    receipts: Section
    resources: Section
    required_expenditure_coverage: Reference
    liquid_assets: Section
    policy: Policy
    valuation: Valuation


@dataclass(frozen=True)
class MissingInput:
    path: str
    reason: str
    acquisition_ref: str


@dataclass(frozen=True)
class ContractAssessment:
    case_id: str
    mode: str
    structural_status: str
    evidence_status: str
    individual_permission: str
    missing: tuple[MissingInput, ...]


@dataclass(frozen=True)
class AuditRow:
    leg: str
    event_id: str
    period: Period
    category: str
    unfinanced: Decimal | None
    financed: Decimal | None
    bank: Decimal | None
    recurring: Decimal | None
    input_paths: tuple[str, ...]


@dataclass(frozen=True)
class AccountingAudit:
    case_id: str
    mode: str
    time_grain: str
    basis: MoneyBasis
    truth: str
    provenance: tuple[tuple[str, Scalar | Reference], ...]
    rows: tuple[AuditRow, ...]
    amounts: Any
    liquidity: tuple[tuple[str, date, Decimal], ...]
    unavailable: Any
    unverified_checks: tuple[str, ...]


def _walk(value, path="case"):
    if isinstance(value, (Scalar, Reference)):
        yield path, value
    elif is_dataclass(value):
        for field in fields(value):
            yield from _walk(getattr(value, field.name), f"{path}.{field.name}")
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _missing(value, path):
    return tuple(MissingInput(p, v.reason, v.acquisition_ref) for p, v in _walk(value, path)
                 if (isinstance(v, Scalar) and v.truth == "Q") or (isinstance(v, Reference) and v.kind == "Q"))


def _known(*values):
    return all(v.value is not None for v in values)


def _nonnegative(value, path):
    _require(value.value is None or value.value >= 0, f"{path}: magnitude must be nonnegative")


def _money(value, case, path):
    _require(value.unit == case.monetary_basis.currency and value.basis_id == case.monetary_basis.basis_id,
             f"{path}: unbridged currency, price-date or nominal/real basis")
    _nonnegative(value, path)


def _same(a, b, message):
    if _known(a, b):
        _require(a.value == b.value, message)


def _shape(value, annotation, path="case"):
    """Runtime type checks keep malformed nested records within the contract error."""
    origin, args = get_origin(annotation), get_args(annotation)
    if annotation is Any:
        # Section rows are heterogeneous across sections, but typed records must
        # still have all their nested fields validated before semantic access.
        if is_dataclass(value):
            _shape(value, type(value), path)
        elif type(value) is str:
            _text(value, path)
        else:
            raise B12ContractError(f"{path}: typed section row or replacement-cost ID required")
        return
    if origin is UnionType:
        _require(any((value is None and t is type(None)) or (isinstance(t, type) and type(value) is t)
                     for t in args), f"{path}: wrong optional field type")
        return
    if origin is tuple:
        _require(type(value) is tuple, f"{path}: immutable tuple required")
        for i, item in enumerate(value):
            _shape(item, args[0], f"{path}[{i}]")
    elif isinstance(annotation, type):
        _require(type(value) is annotation, f"{path}: {annotation.__name__} required")
        if annotation is str:
            _text(value, path)
        if is_dataclass(value):
            hints = get_type_hints(type(value))
            for field in fields(value):
                _shape(getattr(value, field.name), hints[field.name], f"{path}.{field.name}")


def _replay_b04(b):
    """Bind the context absent from Bill by replaying its existing producer."""
    from modules.B04.engine import (TariffInputError, price_a1, price_b_alap,
                                    price_h_heating, price_h_outside)
    _require(all(value.unit == "HUF" for value in (b.consumption_gross, b.fixed_gross, b.total_gross)),
             "B04 producer charges are native HUF; retagging is not a currency conversion")
    if not _known(b.quantity, b.billed_months, b.discounted_allocation):
        return  # Missing producer inputs remain readiness Q.
    quantity, months, allowance = b.quantity.value, b.billed_months.value, b.discounted_allocation.value
    try:
        if b.product == "A1":
            expected = price_a1(quantity, allowance, months, b.distributor)
        elif b.product == "H":
            expected = price_h_heating(quantity, months, b.distributor, b.service_period.start,
                                       b.service_period.end, load_scope=b.tariff_load_scope)
        elif b.product == "H_OUTSIDE":
            expected = price_h_outside(quantity, allowance, months, b.distributor, b.service_period.start,
                                       b.service_period.end, load_scope=b.tariff_load_scope,
                                       connection_scope=b.tariff_connection_scope)
        elif b.product == "B_ALAP":
            expected = price_b_alap(quantity, allowance, months, b.distributor, load_scope=b.tariff_load_scope)
        else:
            raise B12ContractError("unsupported B04 producer product")
    except TariffInputError as exc:
        raise B12ContractError(f"B04 producer context: {exc}") from exc
    _require(b.revision == expected.tariff_snapshot_date.isoformat(), "B04 snapshot revision mismatch")
    _require(b.upstream_source_ids == expected.source_ids, "B04 producer source IDs mismatch")
    for scalar, value in ((b.consumption_gross, expected.consumption_charge_huf),
                          (b.fixed_gross, expected.fixed_charge_huf), (b.total_gross, expected.total_huf)):
        _require(scalar.value == value, "B04 charges do not match exact producer invocation context")


def _validate(case):
    _shape(case, Case)
    _require(type(case) is Case, "Case record required; omitted sections are not NONE")
    _require(case.mode in {SYNTHETIC, "CONDITIONAL_CASE", "POPULATION_ESTIMATE", "INDIVIDUAL_RECORD"}, "case mode")
    for name in ("case_id", "intervention_id", "archetype_id", "region_id", "baseline_id", "programme_id", "service_basis_ref"):
        _text(getattr(case, name), name)
    _require(case.baseline_id != case.programme_id, "distinct counterfactual legs required")
    _require(case.transition_ref in {f"S{i}_TO_S{i+1}" for i in range(5)}, "existing B01 transition ID required")
    _require(case.time_grain in {"DATED", "ANNUAL"}, "time grain")
    _require(type(case.as_of) is date, "as_of date")
    _require(case.reporting_periods and type(case.reporting_periods) is tuple, "explicit reporting periods required")
    _require(case.reporting_periods[0].start == case.evaluation_period.start and
             case.reporting_periods[-1].end == case.evaluation_period.end, "reporting coverage")
    for left, right in zip(case.reporting_periods, case.reporting_periods[1:]):
        _require(right.start.toordinal() == left.end.toordinal() + 1, "reporting periods overlap or leave gap")
    for _, item in _walk(case):
        if case.mode == SYNTHETIC:
            if isinstance(item, Scalar) and item.value is not None:
                _require(item.truth in {"SCN", "ASS", "POL"} and item.scenario_ref.startswith(SYNTHETIC)
                         and not item.source_ids, "synthetic case cannot claim observed/admitted amounts")
            elif isinstance(item, Reference):
                _require(item.kind != "EXTERNAL_ADMISSION", "synthetic case cannot claim external admission")
        elif isinstance(item, Reference):
            _require(item.kind != SYNTHETIC, "actual/conditional case cannot use fixture references")
        elif item.scenario_ref:
            _require(not item.scenario_ref.startswith(SYNTHETIC), "actual case cannot use fixture amounts")
    _require(case.monetary_basis.nominal_real == "NOMINAL", "cash/debt/liquidity contract requires nominal dated money")
    bases = {b.basis_id: b for b in (case.monetary_basis,) + case.other_bases}
    _require(len(bases) == len(case.other_bases) + 1, "duplicate monetary basis")
    for b in bases.values():
        _require(b.nominal_real in {"NOMINAL", "REAL"} and type(b.price_date) is date, "monetary basis")
        _text(b.currency, "currency")
    for c in case.conversions:
        _require(c.original.basis_id in bases and c.converted.basis_id in bases and c.multiplier.unit == "ratio",
                 "conversion bases/factor")
        _require(c.original.unit == bases[c.original.basis_id].currency and
                 c.converted.unit == bases[c.converted.basis_id].currency, "conversion currency")
        if _known(c.original, c.converted, c.multiplier):
            _require(c.multiplier.value > 0 and c.original.value * c.multiplier.value == c.converted.value,
                     "explicit FX/deflator conversion identity")
    scope = case.scope
    _text(scope.scope_id, "scope_id")
    _text(scope.household_id, "household_id")
    _require(scope.shares and type(scope.shares) is tuple, "explicit household/dwelling shares required")
    _require(len({(s.household_id, s.dwelling_id) for s in scope.shares}) == len(scope.shares), "duplicate scope mapping")
    _require(any(s.household_id == scope.household_id for s in scope.shares), "payer household missing from mapping")
    for dwelling in {s.dwelling_id for s in scope.shares}:
        shares = [s for s in scope.shares if s.dwelling_id == dwelling]
        for s in shares:
            _require(s.role in {"OWNER", "PARTIAL_OWNER", "OCCUPIER", "LANDLORD"}, "payer role")
            for value in (s.cost_share, s.payment_share):
                _require(value.unit == "ratio", "share unit")
                _require(value.value is None or 0 <= value.value <= 1, "share outside [0,1]")
        for key in ("cost_share", "payment_share"):
            vals = [getattr(s, key) for s in shares]
            if _known(*vals):
                _require(sum(v.value for v in vals) == 1, "payer shares must reconcile by dwelling")
    section_types = {"costs": Cost, "assets": Asset, "bills": BillInput, "instruments": Instrument,
                     "receipts": Receipt, "resources": Resource, "liquid_assets": LiquidAsset}
    for name, cls in section_types.items():
        section = getattr(case, name)
        _require(type(section) is Section and all(type(r) is cls for r in section.rows), f"{name}: section row type")
        present = {r.leg for r in section.rows}
        if section.state != "Q":
            _require(not present.intersection(section.absent_legs) and present.union(section.absent_legs) == set(LEGS),
                     f"{name}: each leg needs rows or an explicit absent-leg declaration")
        else:
            _require(not section.absent_legs, f"{name}: Q section cannot assert absent legs")
    events = set()
    ids = set()
    supports = set()

    def event(leg, event_id, period, identity):
        _require(leg in LEGS, "case leg")
        _text(event_id, "economic event_id")
        _require((leg, event_id) not in supports, "noncash support event cannot also be a cash/economic event")
        _require((leg, event_id) not in events and (leg, identity) not in ids, "duplicate event or row identity")
        events.add((leg, event_id))
        ids.add((leg, identity))
        _require(case.evaluation_period.start <= period.start <= period.end <= case.evaluation_period.end,
                 "cash event outside evaluation period")
        if case.time_grain == "DATED":
            _require(period.start == period.end, "dated ledger requires exact cash dates; no annual/12 interpolation")
        else:
            _require(period in case.reporting_periods, "annual event requires an exact reporting period")

    costs = {(c.leg, c.cost_id): c for c in case.costs.rows}
    assets = {(a.leg, a.asset_generation_id): a for a in case.assets.rows}
    _require(len(assets) == len(case.assets.rows), "duplicate asset generation")
    included = set()
    for c in case.costs.rows:
        event(c.leg, c.event_id, c.period, c.cost_id)
        _require(c.category in COST_CATEGORIES, "cost category excludes financing, sunk cost and grant reductions")
        _require(c.scope_ref == scope.scope_id and c.payer == scope.household_id, "household payer attribution required")
        _require(c.procurement_basis in {"PROCUREMENT", SYNTHETIC}, "B14 policy cap is not a procurement cost")
        for ref in (c.component_id, c.asset_generation_id, c.phase_ref, c.payee, c.settlement_ref):
            _text(ref, "cost identity")
        _require(c.quantity.value is None or c.quantity.value > 0, "positive cost quantity")
        _require(c.inclusion_scope and type(c.inclusion_scope) is tuple, "bundled cost inclusions required")
        for component in c.inclusion_scope:
            key = (c.leg, c.asset_generation_id, c.period, component)
            _require(key not in included, "bundled cost duplicated by component/date/generation")
            included.add(key)
        for name in ("gross", "net", "vat", "eligible_gross"):
            _money(getattr(c, name), case, f"{c.cost_id}.{name}")
        _require(c.vat_representation in {"GROSS_ONLY", "NET_VAT_GROSS"}, "VAT representation")
        if c.vat_representation == "GROSS_ONLY":
            _require(c.net.truth == c.vat.truth == "Q", "gross-only invoice cannot invent tax decomposition")
        elif _known(c.net, c.vat, c.gross):
            _require(c.net.value + c.vat.value == c.gross.value, "net + VAT must equal gross, once")
        if _known(c.eligible_gross, c.gross):
            _require(c.eligible_gross.value <= c.gross.value, "eligible cost cannot exceed same-basis payable")
        if c.eligible_gross.value is not None:
            _require(c.eligibility_rule.kind != "Q", "eligible amount requires scoped rule/revision")
        for cap in c.eligibility_caps:
            _money(cap, case, "eligibility cap")
            if _known(cap, c.eligible_gross):
                _require(c.eligible_gross.value <= cap.value, "nested eligibility cap exceeded")
        if c.category in {"INITIAL_CAPEX", "REPLACEMENT"}:
            _require((c.leg, c.asset_generation_id) in assets, "capital cost requires asset generation/lifecycle record")
            a = assets[(c.leg, c.asset_generation_id)]
            _require(a.component_id == c.component_id, "asset and cost component mismatch")
            _require((c.category == "REPLACEMENT") == bool(a.retired_generation_id),
                     "replacement/initial CAPEX must match generation retirement")
    for a in case.assets.rows:
        _require(a.leg in LEGS and type(a.commissioning_date) is date, "asset leg/date")
        _require(a.service_life.unit == "year" and (a.service_life.value is None or a.service_life.value > 0),
                 "positive asset life; warranty is not lifetime")
        _require(a.life_definition in {"EXPECTED_SERVICE_LIFE", "EXPLICIT_SCENARIO_LIFE"}, "warranty cannot become asset life")
        if a.retired_generation_id:
            _require(a.retired_generation_id != a.asset_generation_id and (a.leg, a.retired_generation_id) in assets,
                     "replacement needs a distinct existing generation")
            predecessor = assets[(a.leg, a.retired_generation_id)]
            _require(predecessor.commissioning_date <= a.commissioning_date,
                     "replacement commissioning cannot precede retired generation")
            related = [c for c in case.costs.rows if c.leg == a.leg and c.asset_generation_id == a.asset_generation_id
                       and c.category == "REPLACEMENT"]
            _require(bool(related) and all(c.cost_id in predecessor.replacement_cost_ids.rows for c in related),
                     "replacement requires reciprocal predecessor cost schedule")
        seen, cursor = set(), a
        while cursor.retired_generation_id is not None:
            key = (cursor.leg, cursor.asset_generation_id)
            _require(key not in seen, "cyclic asset retirement chain")
            seen.add(key)
            parent_key = (cursor.leg, cursor.retired_generation_id)
            _require(parent_key in assets, "retired generation missing")
            cursor = assets[parent_key]
        for cost_id in a.replacement_cost_ids.rows:
            _require((a.leg, cost_id) in costs and costs[(a.leg, cost_id)].category == "REPLACEMENT",
                     "replacement schedule must resolve cost")
            new = assets[(a.leg, costs[(a.leg, cost_id)].asset_generation_id)]
            _require(new.retired_generation_id == a.asset_generation_id, "replacement must retire linked generation")
        _require(a.terminal_kind in {"NONE", "CASH_SALE", "NONCASH", "Q"}, "terminal treatment")
        _money(a.terminal_value, case, "terminal value")
        if a.terminal_kind == "Q":
            _require(a.terminal_value.truth == "Q", "unknown terminal value")
        elif a.terminal_kind == "NONE":
            _require(a.terminal_value.value == 0 and a.terminal_receipt_id is None, "no residual needs explicit zero")
        elif a.terminal_kind == "NONCASH":
            _require(a.terminal_receipt_id is None, "noncash terminal value is not a sale receipt")
        else:
            _text(a.terminal_receipt_id, "sale receipt")
    bill_keys = []
    for b in case.bills.rows:
        event(b.leg, b.event_id, b.period, b.bill_id)
        _require(b.scope_ref == scope.scope_id and b.service_basis_ref == case.service_basis_ref,
                 "bill household/weather/service boundary mismatch")
        for ref in (b.physical_ref, b.end_use, b.meter_id, b.distributor, b.product, b.revision, b.fixed_charge_key):
            _text(ref, "bill identity")
        for name in ("consumption_gross", "fixed_gross", "total_gross"):
            _money(getattr(b, name), case, f"{b.bill_id}.{name}")
        if _known(b.consumption_gross, b.fixed_gross, b.total_gross):
            _require(b.total_gross.value == b.consumption_gross.value + b.fixed_gross.value, "bill total identity")
        _require(b.billed_months.unit == "month" and b.discounted_allocation.unit == b.quantity.unit, "bill allocation units")
        for v in (b.quantity, b.billed_months, b.discounted_allocation):
            _nonnegative(v, "bill quantity/allocation")
        if b.carrier == "GAS":
            _require(b.tariff_layer == "MARKET_RESIDENTIAL_FINAL", "B12 gas boundary is market-residential only")
            _require(b.quantity.unit == "m3", "useful heat is not billed gas")
            _text(b.gas_reference_state_ref, "gas reference state")
        else:
            _require(b.carrier == "ELECTRICITY" and b.quantity.unit == "kWh" and b.tariff_layer == "FINAL_RETAIL_GROSS",
                     "net energy-only/wholesale/system value is not a retail bill")
        if b.product == "H":
            _require(b.carrier == "ELECTRICITY" and b.tariff_load_scope == "ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES",
                     "H battery/general load excluded")
        if b.carrier == "GAS":
            _require(b.tariff_load_scope == "RESIDENTIAL_GAS_LOAD", "gas cannot be relabelled as a heat-pump load")
        if b.upstream_status == "SCN_CONSTANT_2026_TARIFF_SNAPSHOT":
            _require(b.carrier == "ELECTRICITY", "B04 electricity snapshot cannot be a gas source")
            _require(case.monetary_basis.nominal_real == "NOMINAL" and
                     case.monetary_basis.price_date.year == 2026,
                     "B04 native monetary anchor is nominal HUF 2026; unbound conversions cannot rebase its charges")
            _require(b.upstream_price_basis == "FROZEN_2026_RATES_NOT_HISTORICAL_OR_FUTURE_INVOICE_VALIDATION"
                     and all(v.truth == "SCN" for v in (b.consumption_gross, b.fixed_gross, b.total_gross)),
                     "frozen B04 snapshot cannot become observed future invoice")
            _replay_b04(b)
        for old in bill_keys:
            overlaps = b.service_period.start <= old.service_period.end and old.service_period.start <= b.service_period.end
            if b.leg == old.leg and overlaps:
                if b.meter_id == old.meter_id or b.fixed_charge_key == old.fixed_charge_key:
                    if _known(b.fixed_gross, old.fixed_gross):
                        _require(not (b.fixed_gross.value > 0 and old.fixed_gross.value > 0),
                                 "overlapping service intervals on one meter or fixed-charge identity cannot each carry fixed charges")
                    # Unknown fees may be zero; their scalar Q blocks the dependent
                    # bill/cash views without asserting a proven duplicate charge.
                _require((b.meter_id, b.end_use) != (old.meter_id, old.end_use), "overlapping bill coverage")
        bill_keys.append(b)
    direct = {}
    def supplier(leg, amount, cost_id, period):
        _require((leg, cost_id) in costs and costs[(leg, cost_id)].period == period,
                 "direct settlement must resolve exact invoice leg and date")
        if amount.value is not None:
            direct[(leg, cost_id)] = direct.get((leg, cost_id), Decimal(0)) + amount.value
    _require(len({(i.leg, i.instrument_id) for i in case.instruments.rows}) == len(case.instruments.rows),
             "duplicate instrument ID")
    for instrument in case.instruments.rows:
        _require(instrument.leg in LEGS and instrument.kind in {"EXISTING", "PROGRAMME"}, "debt scope")
        _require(instrument.borrower == scope.household_id, "borrower scope")
        _require(instrument.status in {"CONDITIONAL", "CONFIRMED"} and instrument.amount_kind == "DRAW_SCHEDULE",
                 "rule/borrowing limit is not an approved loan draw")
        _require(instrument.start <= instrument.maturity, "loan term dates")
        _require(instrument.interest_definition in {"ZERO", "SUPPLIED_PERIODIC_OPENING", "EXTERNAL_ACCRUAL_Q"},
                 "APR/THM is not a coupon or payment engine")
        for text in (instrument.instrument_id, instrument.lender, instrument.terms_revision, instrument.payment_frequency):
            _text(text, "instrument terms")
        _require(all(type(r) is DebtRow for r in instrument.rows.rows), "debt schedule rows required")
        previous = None
        for r in instrument.rows.rows:
            event(instrument.leg, r.event_id, r.period, f"{instrument.instrument_id}/{r.event_id}")
            _require(instrument.start <= r.period.start <= r.period.end <= instrument.maturity, "repayment outside loan term")
            if previous:
                _require(previous.period.end < r.period.start, "ordered non-overlapping debt schedule required")
                _same(previous.closing, r.opening, "debt opening does not reconcile to previous closing")
            elif instrument.kind == "PROGRAMME" and r.opening.value is not None:
                _require(r.opening.value == 0, "programme debt requires explicit initial draw, not hidden opening debt")
            for name in ("opening", "draw", "capitalized_interest", "capitalized_fees", "cash_interest", "principal",
                         "cash_fees", "extinguishment", "closing"):
                _money(getattr(r, name), case, f"{instrument.instrument_id}.{name}")
            vals = (r.opening, r.draw, r.capitalized_interest, r.capitalized_fees, r.principal, r.extinguishment, r.closing)
            if _known(*vals):
                _require(r.closing.value == r.opening.value + r.draw.value + r.capitalized_interest.value +
                         r.capitalized_fees.value - r.principal.value - r.extinguishment.value, "debt balance identity")
            _require(r.draw_route in {"BANK", "SUPPLIER"} and r.fee_route in {"BANK", "WITHHELD"}, "debt routes")
            if r.fee_route == "WITHHELD" and _known(r.draw, r.cash_fees):
                _require(r.draw_route == "BANK" and r.cash_fees.value <= r.draw.value, "withheld fee needs gross bank draw")
            if r.draw_route == "SUPPLIER":
                supplier(instrument.leg, r.draw, r.direct_cost_id, r.period)
            else:
                _require(r.direct_cost_id is None, "bank draw cannot also settle supplier")
            if r.extinguishment.value is not None and r.extinguishment.value > 0:
                _text(r.support_event_id, "noncash support event")
                _require(r.extinguishment_authority.kind != "Q", "noncash extinguishment authority required")
                _require((instrument.leg, r.support_event_id) not in supports
                         and (instrument.leg, r.support_event_id) not in events,
                         "noncash support counted again as an economic event")
                supports.add((instrument.leg, r.support_event_id))
            _require(r.accrual_rate.unit == "ratio" and (r.accrual_rate.value is None or r.accrual_rate.value >= 0),
                     "accrual rate requires nonnegative ratio even for zero interest")
            if instrument.interest_definition == "ZERO":
                _require(all(v.value is None or v.value == 0 for v in
                             (r.cash_interest, r.capitalized_interest, r.accrual_rate)),
                         "explicit zero-interest schedule disagrees")
            elif instrument.interest_definition == "SUPPLIED_PERIODIC_OPENING" and _known(r.opening, r.accrual_rate, r.cash_interest, r.capitalized_interest):
                _require(r.accrual_rate.unit == "ratio" and r.accrual_rate.value >= 0 and
                         r.opening.value * r.accrual_rate.value == r.cash_interest.value + r.capitalized_interest.value,
                         "supplied periodic opening-balance interest identity")
            previous = r
        if previous and previous.closing.value is not None and previous.closing.value > 0 and instrument.maturity <= case.evaluation_period.end:
            _require(instrument.balloon_or_refinance.kind != "Q", "maturity residual requires explicit balloon/refinance dependency")
    receipts = {(r.leg, r.receipt_id): r for r in case.receipts.rows}
    vat_refunds = {}
    for r in case.receipts.rows:
        event(r.leg, r.event_id, r.period, r.receipt_id)
        _require(r.category in {"GRANT", "VAT_REFUND", "OPERATING", "SALE"}, "receipt category")
        _require(r.beneficiary == scope.household_id and r.status in {"CONDITIONAL", "CONFIRMED"}, "receipt status/beneficiary")
        if case.mode == SYNTHETIC:
            _require(r.status == "CONDITIONAL", "synthetic grant is never confirmed_external_grant")
        _money(r.amount, case, "receipt")
        _require(r.award_or_contract.kind != "Q" or r.amount.truth == "Q", "rule/potential eligibility is not a receipt")
        _require((r.leg, r.event_id) not in supports, "support counted as cash grant and forgiveness")
        supports.add((r.leg, r.event_id))
        _require(r.route in {"BANK", "SUPPLIER"}, "receipt route")
        if r.route == "SUPPLIER":
            supplier(r.leg, r.amount, r.cost_id, r.period)
        elif r.category in {"GRANT", "VAT_REFUND"}:
            _require((r.leg, r.cost_id) in costs, "transfer allocation must resolve same-leg cost")
        if r.category == "VAT_REFUND":
            c = costs[(r.leg, r.cost_id)]
            if _known(r.amount, c.vat):
                vat_refunds[(r.leg, r.cost_id)] = vat_refunds.get((r.leg, r.cost_id), Decimal(0)) + r.amount.value
                _require(vat_refunds[(r.leg, r.cost_id)] <= c.vat.value, "aggregate VAT refunds cannot exceed invoice VAT")
        if r.category == "SALE":
            a = assets.get((r.leg, r.asset_generation_id))
            _require(a is not None and a.terminal_kind == "CASH_SALE" and a.terminal_receipt_id == r.receipt_id,
                     "noncash book value cannot become liquidity")
            _same(a.terminal_value, r.amount, "sale must equal net terminal receipt")
    for a in assets.values():
        if a.terminal_kind == "CASH_SALE":
            _require((a.leg, a.terminal_receipt_id) in receipts, "terminal sale receipt missing")
            sale = receipts[(a.leg, a.terminal_receipt_id)]
            _require(sale.category == "SALE" and sale.asset_generation_id == a.asset_generation_id,
                     "terminal asset must bind a reciprocal same-leg SALE receipt")
            _same(a.terminal_value, sale.amount, "terminal asset and sale receipt value mismatch")
    for cost_id, amount in direct.items():
        if costs[cost_id].gross.value is not None:
            _require(amount <= costs[cost_id].gross.value, "supplier settlement exceeds full payable invoice")
    budget_coverage = set()
    for r in case.resources.rows:
        event(r.leg, r.event_id, r.period, r.resource_id)
        _require(r.category in {"NET_INCOME", "REQUIRED_NON_ENERGY", "RECURRING_RECEIPT"}, "resource category")
        _require(r.scope_ref == scope.scope_id and r.amount.unit == case.monetary_basis.currency and
                 r.amount.basis_id == case.monetary_basis.basis_id, "resource household/period/basis bridge required")
        if r.category != "NET_INCOME":
            _nonnegative(r.amount, "required spending/receipt")
        _require(r.source_semantics in {"NET_COMPONENT", "BRIDGED_NET_COMPONENT", "DISJOINT_REQUIRED_SPENDING", "RECURRING_NET_RECEIPT"},
                 "gross HFCS income, HI0220 total, debt stock, or conditional median is not net budget input")
        if r.category == "NET_INCOME":
            _require(r.source_semantics in {"NET_COMPONENT", "BRIDGED_NET_COMPONENT"}, "net income semantics")
        if r.source_semantics == "BRIDGED_NET_COMPONENT":
            _require(r.gross_to_net_or_scope_bridge.kind != "Q", "gross-to-net temporal recipe required")
        _require(r.covered_categories and type(r.covered_categories) is tuple, "resource scope categories")
        for category in r.covered_categories:
            _require(category not in {"ENERGY", "O_AND_M", "INSURANCE", "DEBT", "CAPEX", "TOTAL_CONSUMPTION"},
                     "resource expenditure overlaps separate bill/lifecycle/debt ledger")
            key = (r.leg, "EXPENDITURE" if r.category == "REQUIRED_NON_ENERGY" else "INCOME", r.period, category)
            _require(key not in budget_coverage, "duplicate budget component")
            budget_coverage.add(key)
        _require(r.household_size.unit == "person/household" and (r.household_size.value is None or r.household_size.value > 0),
                 "household/person mapping required")
    stocks = set()
    for a in case.liquid_assets.rows:
        _require(a.leg in LEGS and (a.leg, a.asset_id) not in stocks, "duplicate liquid asset")
        stocks.add((a.leg, a.asset_id))
        _require(a.household_id == scope.household_id and a.scope_ref == scope.scope_id,
                 "liquid asset household/scope mismatch")
        _require(a.stock_date == case.evaluation_period.start, "liquidity stock needs explicit cash-start bridge")
        _require(a.kind in {"CASH_DEPOSIT", "SECURITY", "PENSION_INSURANCE", "BUSINESS_HOLDING"},
                 "total wealth/home equity is not accessible cash")
        for v in (a.gross, a.encumbered, a.disposal_cost, a.spendable):
            _money(v, case, "liquid asset")
        if _known(a.gross, a.encumbered, a.disposal_cost, a.spendable):
            _require(a.gross.value - a.encumbered.value - a.disposal_cost.value == a.spendable.value,
                     "liquid asset spendable reconciliation")
    p = case.population
    _require(p.evidence_class in {SYNTHETIC, "REPRESENTATIVE_OBSERVED_SAMPLE", "CALIBRATED_MULTI_SOURCE_INFERENCE", "Q"},
             "multiplied marginals/conditional medians are not joint population records")
    _require(p.source_unit in {"household", "person", "dwelling"} and p.target_unit in {"household", "person", "dwelling"}, "population unit")
    if p.source_unit != p.target_unit:
        _require(p.household_dwelling_bridge.kind != "Q" or p.authority.kind == "Q", "population unit bridge required")
    policy = case.policy
    _require(policy.floor_value.unit == case.monetary_basis.currency and
             policy.floor_value.basis_id == case.monetary_basis.basis_id,
             "policy floor requires case money currency/basis; its metric and sign remain owner choices")
    _money(policy.reserve, case, "policy liquidity reserve")
    _require(policy.floor_variable == "VAR-B01-CASH-FLOW-FLOOR" and policy.horizon_variable == "VAR-B01-HORIZON-YEARS",
             "reuse existing owner policy IDs; no new default")
    _require(case.valuation.basis_id in bases, "valuation basis must be declared")
    _require(case.valuation.discount_rate.basis_id == case.valuation.basis_id, "discount nominal/real basis mismatch")
    for v in (case.valuation.discount_rate, case.valuation.nominal_rate, case.valuation.real_rate, case.valuation.inflation):
        _require(v.unit == "ratio" and (v.value is None or v.value > -1), "valuation rate unit/domain")
    v = case.valuation
    if _known(v.nominal_rate, v.real_rate, v.inflation):
        _require(1 + v.nominal_rate.value == (1 + v.real_rate.value) * (1 + v.inflation.value), "nominal-real Fisher identity")
    return ContractAssessment(case.case_id, case.mode, "VALID", "SCENARIO_ONLY" if case.mode == SYNTHETIC else "Q_EXTERNAL_REVIEW_UNRESOLVED",
                              "NOT_ASSESSED", _missing(case, "case"))


def validate_case(case: Case) -> ContractAssessment:
    """Validate shape, boundaries and available identities; never certify evidence."""
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return _validate(case)


def assess_readiness(case: Case):
    """Exact missing dependencies by output, not a module-ready flag or permission."""
    validate_case(case)
    missing = {}
    def paths(parts):
        return [m.path for name, part in parts for m in _missing(part, name)]
    common = paths((("case.identity_binding", case.identity_binding), ("case.scope", case.scope),
                    ("case.monetary_basis", case.monetary_basis)))
    if case.mode != SYNTHETIC:
        common.append(EXTERNAL_Q)
    cost_all, cost_initial = list(common), list(common)
    if case.costs.state == "Q":
        section_missing = paths((("case.costs", case.costs),))
        cost_all += section_missing
        cost_initial += section_missing
    for i, c in enumerate(case.costs.rows):
        dependencies = paths(((f"case.costs.rows[{i}].gross", c.gross), (f"case.costs.rows[{i}].quantity", c.quantity),
                              (f"case.costs.rows[{i}].attribution", c.attribution)))
        cost_all += dependencies
        if c.category == "INITIAL_CAPEX":
            cost_initial += dependencies
    missing["total_initial_cost"] = tuple(cost_initial)
    eligible = list(cost_initial)
    for i, c in enumerate(case.costs.rows):
        if c.category == "INITIAL_CAPEX":
            eligible += paths(((f"case.costs.rows[{i}].eligible_gross", c.eligible_gross),
                               (f"case.costs.rows[{i}].eligibility_rule", c.eligibility_rule),
                               (f"case.costs.rows[{i}].eligibility_caps", c.eligibility_caps)))
    missing["eligible_initial_cost"] = tuple(eligible)
    tax = list(cost_all)
    for i, c in enumerate(case.costs.rows):
        tax += paths(((f"case.costs.rows[{i}].net", c.net), (f"case.costs.rows[{i}].vat", c.vat),
                      (f"case.costs.rows[{i}].tax_treatment", c.tax_treatment)))
    missing["tax_split"] = tuple(tax)
    bills = common + paths((("case.bills", case.bills),))
    for leg in LEGS:
        if case.bills.state == "ROWS" and not any(b.leg == leg for b in case.bills.rows):
            bills.append(f"case.bills.{leg}.complete_coverage")
    # Scope coverage must be explicitly comparable; changed carriers are allowed.
    scopes = [{(b.end_use, b.service_period) for b in case.bills.rows if b.leg == leg} for leg in LEGS]
    if scopes[0] != scopes[1]:
        bills.append("case.bills.matched_baseline_programme_end_use_coverage")
    missing["retail_bills"] = tuple(bills)
    lifecycle = list(cost_all)
    if case.assets.state == "Q":
        lifecycle += paths((("case.assets", case.assets),))
    for i, a in enumerate(case.assets.rows):
        lifecycle += paths(((f"case.assets.rows[{i}].service_life", a.service_life),
                            (f"case.assets.rows[{i}].replacement_cost_ids", a.replacement_cost_ids),
                            (f"case.assets.rows[{i}].operating_coverage", a.operating_coverage)))
    for i, a in enumerate(case.assets.rows):
        if a.operating_coverage_end < case.evaluation_period.end:
            lifecycle.append(f"case.assets.rows[{i}].operating_coverage_through_evaluation_end")
    missing["lifecycle_cost"] = tuple(lifecycle)
    unfinanced = lifecycle + bills
    if case.receipts.state == "Q":
        unfinanced += paths((("case.receipts", case.receipts),))
    for i, r in enumerate(case.receipts.rows):
        if r.category != "GRANT":
            unfinanced += paths(((f"case.receipts.rows[{i}]", r),))
        if r.category == "SALE":
            asset_index, linked_asset = next((j, a) for j, a in enumerate(case.assets.rows)
                                            if a.leg == r.leg and a.asset_generation_id == r.asset_generation_id)
            unfinanced += paths(((f"case.assets.rows[{asset_index}].terminal_value", linked_asset.terminal_value),))
        if r.category == "VAT_REFUND":
            invoice_index, invoice = next((j, c) for j, c in enumerate(case.costs.rows)
                                          if c.leg == r.leg and c.cost_id == r.cost_id)
            unfinanced += paths(((f"case.costs.rows[{invoice_index}].vat", invoice.vat),
                                 (f"case.costs.rows[{invoice_index}].tax_treatment", invoice.tax_treatment)))
    missing["unfinanced_cash"] = tuple(unfinanced)
    finance = unfinanced + paths((("case.instruments", case.instruments), ("case.receipts", case.receipts)))
    for i, instrument in enumerate(case.instruments.rows):
        if instrument.interest_definition == "EXTERNAL_ACCRUAL_Q":
            finance.append(f"case.instruments.rows[{i}].interest_accrual_verification")
        if (instrument.rows.rows and instrument.maturity <= case.evaluation_period.end
                and instrument.rows.rows[-1].closing.value != 0):
            finance.append(f"case.instruments.rows[{i}].dated_maturity_settlement_required")
    missing["financed_cash"] = tuple(finance)
    resources = paths((("case.resources", case.resources), ("case.required_expenditure_coverage", case.required_expenditure_coverage)))
    liquidity = finance + resources + paths((("case.liquid_assets", case.liquid_assets),))
    if case.time_grain != "DATED":
        liquidity.append("case.time_grain: intrayear liquidity requires dated cash allocations")
    for leg in LEGS:
        if case.liquid_assets.state == "ROWS" and not any(a.leg == leg for a in case.liquid_assets.rows):
            liquidity.append(f"case.liquid_assets.{leg}.opening_stock")
    missing["bank_liquidity"] = tuple(liquidity)
    recurring = common + bills + resources
    if case.costs.state == "Q":
        recurring += paths((("case.costs", case.costs),))
    for i, c in enumerate(case.costs.rows):
        if c.category in {"O_AND_M", "INSURANCE"}:
            recurring += paths(((f"case.costs.rows[{i}].gross", c.gross),
                                (f"case.costs.rows[{i}].attribution", c.attribution)))
    if case.assets.state == "Q":
        recurring += paths((("case.assets", case.assets),))
    for i, a in enumerate(case.assets.rows):
        recurring += paths(((f"case.assets.rows[{i}].operating_coverage", a.operating_coverage),))
        if a.operating_coverage_end < case.evaluation_period.end:
            recurring.append(f"case.assets.rows[{i}].operating_coverage_through_evaluation_end")
    if case.receipts.state == "Q":
        recurring += paths((("case.receipts", case.receipts),))
    for i, r in enumerate(case.receipts.rows):
        if r.category == "OPERATING":
            recurring += paths(((f"case.receipts.rows[{i}]", r),))
    if case.instruments.state == "Q":
        recurring += paths((("case.instruments", case.instruments),))
    for i, instrument in enumerate(case.instruments.rows):
        root = f"case.instruments.rows[{i}]"
        for key in ("access", "rate_path", "day_count_compounding"):
            recurring += paths(((f"{root}.{key}", getattr(instrument, key)),))
        if instrument.rows.state == "Q":
            recurring += paths(((f"{root}.rows", instrument.rows),))
        for j, row in enumerate(instrument.rows.rows):
            for key in ("principal", "cash_interest", "cash_fees"):
                recurring += paths(((f"{root}.rows.rows[{j}].{key}", getattr(row, key)),))
        if instrument.interest_definition == "EXTERNAL_ACCRUAL_Q":
            recurring.append(f"{root}.interest_accrual_verification")
        if (instrument.rows.rows and instrument.maturity <= case.evaluation_period.end
                and instrument.rows.rows[-1].closing.value != 0):
            recurring.append(f"{root}.dated_maturity_settlement_required")
    missing["recurring_budget"] = tuple(recurring)
    missing["affordability"] = tuple(liquidity + paths((("case.policy", case.policy),)) + ["affordability consumer not implemented"])
    valuation = unfinanced + paths((("case.valuation", case.valuation), ("case.assets", case.assets)))
    if case.valuation.basis_id != case.monetary_basis.basis_id:
        valuation.append("case.valuation.flow_by_flow_nominal_real_conversion_required")
    missing["valuation"] = tuple(valuation + ["valuation consumer not implemented"])
    missing["population_aggregation"] = tuple(common + paths((("case.population", case.population),)) + ["population estimator consumer not implemented"])
    return MappingProxyType({name: tuple(dict.fromkeys(refs)) for name, refs in missing.items()})


def audit_accounting(case: Case) -> AccountingAudit:
    """Return available synthetic identities; real output execution stays Q."""
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return _audit(case)


def _audit(case):
    readiness = assess_readiness(case)
    provenance = tuple(_walk(case))
    unverified = tuple(f"{i.instrument_id}: external accrual correctness unverified" for i in case.instruments.rows
                       if i.interest_definition == "EXTERNAL_ACCRUAL_Q")
    if case.mode != SYNTHETIC:
        return AccountingAudit(case.case_id, case.mode, case.time_grain, case.monetary_basis, "Q", provenance, (),
                               MappingProxyType({}), (), readiness, unverified)
    amounts = {}
    def total(name, rows, attr):
        if not readiness[name]:
            for leg in LEGS:
                amounts[f"{name}.{leg}"] = sum((getattr(r, attr).value for r in rows if r.leg == leg), Decimal(0))
    initial = tuple(c for c in case.costs.rows if c.category == "INITIAL_CAPEX")
    total("total_initial_cost", initial, "gross")
    total("eligible_initial_cost", initial, "eligible_gross")
    total("retail_bills", case.bills.rows, "total_gross")
    total("lifecycle_cost", case.costs.rows, "gross")
    if not readiness["tax_split"]:
        for leg in LEGS:
            amounts[f"vat.{leg}"] = sum((c.vat.value for c in case.costs.rows if c.leg == leg), Decimal(0))
    rows = []
    direct = {}
    ready_u = not readiness["unfinanced_cash"]
    ready_f = not readiness["financed_cash"]
    ready_b = not readiness["bank_liquidity"]
    ready_r = not readiness["recurring_budget"]
    zero = Decimal(0)
    if ready_b:
        for r in case.receipts.rows:
            if r.route == "SUPPLIER":
                direct[(r.leg, r.cost_id)] = direct.get((r.leg, r.cost_id), zero) + r.amount.value
        for i in case.instruments.rows:
            for r in i.rows.rows:
                if r.draw_route == "SUPPLIER":
                    direct[(i.leg, r.direct_cost_id)] = direct.get((i.leg, r.direct_cost_id), zero) + r.draw.value
    def add(leg, event, period, category, u, f, bank, recurring, path):
        if any(value is not None for value in (u, f, bank, recurring)):
            rows.append(AuditRow(leg, event, period, category, u, f, bank, recurring, (path,)))
    for n, c in enumerate(case.costs.rows):
        add(c.leg, c.event_id, c.period, c.category,
            -c.gross.value if ready_u else None,
            -c.gross.value if ready_f else None,
            -c.gross.value + direct.get((c.leg, c.cost_id), zero) if ready_b else None,
            (-c.gross.value if c.category in {"O_AND_M", "INSURANCE"} else zero) if ready_r else None,
            f"case.costs.rows[{n}]")
    for n, b in enumerate(case.bills.rows):
        add(b.leg, b.event_id, b.period, "RETAIL_BILL",
            -b.total_gross.value if ready_u else None, -b.total_gross.value if ready_f else None,
            -b.total_gross.value if ready_b else None, -b.total_gross.value if ready_r else None,
            f"case.bills.rows[{n}]")
    for n, r in enumerate(case.receipts.rows):
        add(r.leg, r.event_id, r.period, r.category,
            (r.amount.value if r.category != "GRANT" else zero) if ready_u else None,
            r.amount.value if ready_f else None,
            (r.amount.value if r.route == "BANK" else zero) if ready_b else None,
            (r.amount.value if r.category == "OPERATING" else zero) if ready_r else None,
            f"case.receipts.rows[{n}]")
    for n, i in enumerate(case.instruments.rows):
        for m, r in enumerate(i.rows.rows):
            service = r.principal.value + r.cash_interest.value + r.cash_fees.value if ready_f or ready_b or ready_r else None
            add(i.leg, r.event_id, r.period, f"{i.kind}_DEBT", zero if ready_u else None,
                r.draw.value - service if ready_f else None,
                (r.draw.value if r.draw_route == "BANK" else zero) - service if ready_b else None,
                -service if ready_r else None, f"case.instruments.rows[{n}].rows.rows[{m}]")
        if i.rows.rows and ready_f:
            amounts[f"outstanding_debt.{i.leg}.{i.instrument_id}"] = i.rows.rows[-1].closing.value
    for n, r in enumerate(case.resources.rows):
        x = (-r.amount.value if r.category == "REQUIRED_NON_ENERGY" else r.amount.value) if ready_b or ready_r else None
        add(r.leg, r.event_id, r.period, r.category, zero if ready_u else None, zero if ready_f else None,
            x if ready_b else None, x if ready_r else None, f"case.resources.rows[{n}]")
    for output, attr in (("unfinanced_cash", "unfinanced"), ("financed_cash", "financed"), ("recurring_budget", "recurring")):
        if not readiness[output]:
            for leg in LEGS:
                amounts[f"{output}.{leg}"] = sum((getattr(r, attr) for r in rows if r.leg == leg), zero)
            amounts[f"{output}.incremental"] = amounts[f"{output}.programme"] - amounts[f"{output}.baseline"]
    liquidity = []
    if not readiness["bank_liquidity"]:
        for leg in LEGS:
            balance = sum((a.spendable.value for a in case.liquid_assets.rows if a.leg == leg), zero)
            liquidity.append((leg, case.evaluation_period.start, balance))
            for day in sorted({r.period.start for r in rows if r.leg == leg}):
                balance += sum((r.bank for r in rows if r.leg == leg and r.period.start == day), zero)
                liquidity.append((leg, day, balance))
    # Noncash terminal value is inspectable only in its separate valuation bucket.
    for a in case.assets.rows:
        if a.terminal_kind == "NONCASH" and a.terminal_value.value is not None:
            amounts[f"noncash_terminal.{a.leg}.{a.asset_generation_id}"] = a.terminal_value.value
    # A row never supplies a numerical column whose full boundary is unavailable.
    rows = [replace(r, unfinanced=None if readiness["unfinanced_cash"] else r.unfinanced,
                    financed=None if readiness["financed_cash"] else r.financed,
                    bank=None if readiness["bank_liquidity"] else r.bank,
                    recurring=None if readiness["recurring_budget"] else r.recurring) for r in rows]
    unavailable = MappingProxyType({k: v for k, v in readiness.items() if v})
    return AccountingAudit(case.case_id, case.mode, case.time_grain, case.monetary_basis, "SCN", provenance,
                           tuple(sorted(rows, key=lambda r: (r.leg, r.period.start, r.event_id))),
                           MappingProxyType(amounts), tuple(liquidity), unavailable, unverified)
