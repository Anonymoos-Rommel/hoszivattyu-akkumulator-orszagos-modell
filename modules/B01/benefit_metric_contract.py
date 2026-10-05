"""Signed measurements, supplied utilities and conditional public-HUF ordering.

This consumes qualified upstream outputs, not cashflows or financial models.
No weights, valuation, currency conversion, allocation or permission is inferred.
All numerical examples belong in explicit SCN callers, never this module.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from modules.B12.input_accounting_contract import (
    AccountingAudit, B12ContractError, Case, Conversion, MoneyBasis, Reference, Scalar,
    Period as B12Period, SYNTHETIC, Valuation, _shape as _b12_shape,
    audit_accounting, validate_case,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "registry/b01_benefit_metric_contract.json"
# Exact supported output tokens, not an alias parser or a conversion catalogue.
# Currency-valued output is bounded to HUF in this public-HUF comparison slice.
# Other native currencies may remain in an explicit upstream Conversion binding.
METRIC_UNITS = {
    "MONETARY": ("HUF",),
    "NONMONETARY": ("kWh", "MWh", "GJ", "kW", "MW", "kgCO2e", "tCO2e",
                    "job-year", "household", "dwelling", "building", "person", "ratio"),
}


class BenefitContractError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise BenefitContractError(message)


def _text(value, name):
    _require(isinstance(value, str) and bool(value.strip()), f"{name}: nonempty text required")


def exact(value):
    """Finite signed exact values; None/Q differs from zero. Floats are excluded."""
    if value is None:
        return None
    _require(not isinstance(value, bool) and isinstance(value, (int, str, Decimal, Fraction)),
             "quantity requires int, decimal text, Decimal or Fraction")
    try:
        return Fraction(value)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise BenefitContractError("quantity must be finite and exact") from exc


def _canonical(value):
    if is_dataclass(value):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, (Decimal, Fraction)):
        q = exact(value)
        return {"numerator": q.numerator, "denominator": q.denominator}
    if type(value) is date:
        return value.isoformat()
    return value


def fingerprint(value):
    """Content binding, not proof of source truth or economic independence."""
    try:
        return sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"),
                                 allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError) as exc:
        raise BenefitContractError("content binding requires finite serializable values") from exc


def _hash(value, name):
    _require(isinstance(value, str) and len(value) == 64 and
             all(c in "0123456789abcdef" for c in value), f"{name}: SHA256 required")


def _tuple(value, name):
    _require(type(value) is tuple, f"{name}: immutable tuple required")


def _unique(values, key, name):
    _tuple(values, name)
    result = {}
    for v in values:
        k = key(v)
        _text(k, name)
        _require(k not in result, f"duplicate {name}: {k}")
        result[k] = v
    return result


@dataclass(frozen=True)
class Evidence:
    mode: str  # SCN, ADMITTED, EXTERNAL_ADMISSION (pointer only), Q
    reference: str
    source_pins: tuple[tuple[str, str], ...] = ()
    evidence_tier: str = "E3"
    validation_debt: tuple[str, ...] = ()

    def validate(self):
        _require(self.mode in {"SCN", "ADMITTED", "EXTERNAL_ADMISSION", "Q"}, "evidence mode")
        _text(self.reference, "qualification/scenario or Q acquisition reference")
        _require(self.evidence_tier in {"E1", "E2", "E3"}, "evidence tier")
        _tuple(self.source_pins, "source pins")
        for source, digest in self.source_pins:
            _text(source, "source_id")
            _hash(digest, "source pin")
        _require(len({s for s, _ in self.source_pins}) == len(self.source_pins), "duplicate source pin")
        _tuple(self.validation_debt, "validation debt")
        for ref in self.validation_debt:
            _text(ref, "validation debt")
        if self.mode == "ADMITTED":
            _require(bool(self.source_pins) and self.evidence_tier in {"E1", "E2"},
                     "admitted output needs source pins and E1/E2 qualification")

    @property
    def ready(self):
        self.validate()
        return self.mode in {"SCN", "ADMITTED"}


@dataclass(frozen=True)
class Period:
    start: str
    end: str
    convention: str  # INCLUSIVE or HALF_OPEN, never inferred from the dates
    timezone: str

    def validate(self):
        _require(self.convention in {"INCLUSIVE", "HALF_OPEN"}, "explicit period convention required")
        try:
            first, last = date.fromisoformat(self.start), date.fromisoformat(self.end)
            ZoneInfo(self.timezone)
        except (ValueError, TypeError, ZoneInfoNotFoundError) as exc:
            raise BenefitContractError("exact dates and IANA timezone required") from exc
        _require(first.isoformat() == self.start and last.isoformat() == self.end, "ISO dates required")
        _require(first <= last if self.convention == "INCLUSIVE" else first < last, "period order")


@dataclass(frozen=True)
class PeriodAdapter:
    original: Period
    target: Period
    evidence: Evidence

    def validate(self):
        self.original.validate()
        self.target.validate()
        _require(self.original.timezone == self.target.timezone, "period adapter cannot change timezone")
        def stop(p):
            d = date.fromisoformat(p.end)
            return d + timedelta(days=1) if p.convention == "INCLUSIVE" else d
        _require(self.original.start == self.target.start and stop(self.original) == stop(self.target),
                 "period adapter must preserve exactly the covered calendar dates")
        self.evidence.validate()


@dataclass(frozen=True)
class ComparisonFrame:
    frame_id: str
    version: str
    methodology_ref: str
    claim_scope: str  # HOUSEHOLD or POPULATION
    geography: str
    service_basis: str
    evaluation_horizon: Period
    world_id: str
    counterfactual_method: str
    valuation_method: str
    evidence: Evidence

    def validate(self):
        for name in ("frame_id", "version", "methodology_ref", "geography", "service_basis",
                     "world_id", "counterfactual_method", "valuation_method"):
            _text(getattr(self, name), name)
        _require(self.claim_scope in {"HOUSEHOLD", "POPULATION"}, "frame scope")
        self.evaluation_horizon.validate()
        self.evidence.validate()


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    version: str
    concept: str | None
    unit: str | None
    actor: str | None
    consolidation_boundary: str | None
    meaning: str | None  # INCREMENTAL / TOTAL
    native_counting_unit: str | None
    per_unit_denominator: str | None  # explicit NOT_APPLICABLE where appropriate
    accounting_basis: str | None
    time_basis: str | None
    counterfactual_method: str | None
    valuation_method: str | None
    quantity_dimension: str | None  # MONETARY / NONMONETARY; None is unresolved
    money_basis: MoneyBasis | None  # Missing monetary basis is Q, never inapplicability
    denominator_kind: str | None  # NONE / GROSS_PUBLIC_OUTLAY / NET_PUBLIC_COST / SEED_BRIDGE / Q
    historical_component: str | None
    evidence: Evidence

    def validate(self):
        _text(self.metric_id, "metric_id")
        _text(self.version, "metric version")
        for name in ("concept", "unit", "actor", "consolidation_boundary", "native_counting_unit",
                     "per_unit_denominator", "accounting_basis", "time_basis",
                     "counterfactual_method", "valuation_method", "historical_component"):
            if getattr(self, name) is not None:
                _text(getattr(self, name), name)
        _require(self.meaning in {None, "INCREMENTAL", "TOTAL"}, "metric meaning")
        _require(self.quantity_dimension in {None, "MONETARY", "NONMONETARY"},
                 "explicit monetary/nonmonetary quantity dimension required")
        if self.unit is not None:
            supported = (METRIC_UNITS[self.quantity_dimension] if self.quantity_dimension is not None
                         else METRIC_UNITS["MONETARY"] + METRIC_UNITS["NONMONETARY"])
            _require(self.unit in supported,
                     "unsupported metric output unit or dimension mismatch; aliases/compound units are not inferred")
        if self.quantity_dimension == "NONMONETARY":
            _require(self.money_basis is None, "nonmonetary metric cannot carry a monetary basis")
        _require(self.denominator_kind in {None, "NONE", "GROSS_PUBLIC_OUTLAY", "NET_PUBLIC_COST", "SEED_BRIDGE"},
                 "explicit public denominator kind")
        if self.money_basis is not None:
            _require(isinstance(self.money_basis, MoneyBasis), "reuse B12 MoneyBasis")
            for name in ("basis_id", "currency"):
                _text(getattr(self.money_basis, name), name)
            _require(self.money_basis.nominal_real in {"NOMINAL", "REAL"}, "nominal/real basis")
            _require(type(self.money_basis.price_date) is date, "money price date")
            _require(self.unit is None or self.unit == self.money_basis.currency, "money output unit/basis mismatch")
            _require(isinstance(self.money_basis.convention, Reference), "explicit B12 money convention required")
        self.evidence.validate()

    @property
    def ready(self):
        self.validate()
        semantics = (self.concept, self.unit, self.actor, self.consolidation_boundary, self.meaning,
                     self.native_counting_unit, self.per_unit_denominator, self.accounting_basis,
                     self.time_basis, self.counterfactual_method, self.valuation_method, self.denominator_kind,
                     self.quantity_dimension)
        money_ready = (self.quantity_dimension == "NONMONETARY" or
                       (self.quantity_dimension == "MONETARY" and self.money_basis is not None
                        and self.money_basis.convention.kind != "Q"))
        return all(v is not None for v in semantics) and self.evidence.ready and money_ready


@dataclass(frozen=True)
class CandidateIdentity:
    candidate_id: str
    claim_scope: str
    scope_id: str  # own household or own represented population
    record_or_project_id: str
    bundle_fingerprint: str
    baseline_id: str
    programme_id: str
    world_id: str

    def validate(self, frame):
        for f in fields(self):
            _text(getattr(self, f.name), f.name)
        _hash(self.bundle_fingerprint, "exact candidate/bundle fingerprint")
        _require(self.baseline_id != self.programme_id, "separate baseline/programme identities")
        _require(self.claim_scope == frame.claim_scope and self.world_id == frame.world_id,
                 "candidate scope/world differs from comparison frame")


@dataclass(frozen=True)
class Transformation:
    kind: str  # CONVERSION, VALUATION or AGGREGATION; calculation stays upstream
    original_output_sha256: str
    original_basis: str
    target_basis: str
    method_ref: str
    native_binding: Conversion | Valuation | None
    evidence: Evidence
    original_money_basis: MoneyBasis | None = None  # CONVERSION only; absent context is Q


@dataclass(frozen=True)
class B12Binding:
    case: Case
    audit: AccountingAudit
    output_key: str
    case_sha256: str
    audit_sha256: str
    candidate_digest: str
    correspondence: Evidence


@dataclass(frozen=True)
class Measurement:
    measurement_id: str
    metric_digest: str
    candidate_digest: str
    frame_digest: str
    quantity: object
    unit: str
    native_periods: tuple[Period, ...]
    evaluation_period: Period
    evaluation_contract: str
    native_status: str  # READY, Q, FAIL, UNIMPLEMENTED, EXTERNAL_ADMISSION
    producer: str
    output_id: str
    output_version: str
    evidence: Evidence
    transformations: tuple[Transformation, ...] = ()
    period_adapter: PeriodAdapter | None = None
    b12_binding: B12Binding | None = None

    @property
    def output_sha256(self):
        """Exact bound producer value, status and full context; no inferred scalar."""
        return fingerprint(self)


@dataclass(frozen=True)
class UtilityMapping:
    mapping_id: str
    version: str
    metric_digest: str
    frame_digest: str
    raw_direction: str  # MAXIMIZE or MINIMIZE; higher utility is always preferred
    domain: tuple[object, object]
    anchors: tuple[tuple[object, object], ...]
    evidence: Evidence


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    metric_digest: str
    frame_digest: str
    space: str  # RAW or UTILITY
    operator: str  # LOWER_BOUND, UPPER_BOUND or RANGE; inclusive endpoints
    lower: object
    upper: object
    unit: str
    utility_digest: str | None
    required: bool
    evidence: Evidence


@dataclass(frozen=True)
class CashPeriod:
    period_id: str
    kind: str  # INITIAL, INTERIM, PAYMENT, SETTLEMENT; all explicit coverage
    period: Period


@dataclass(frozen=True)
class CashCoverage:
    kind: str  # INITIAL, INTERIM, PAYMENT, SETTLEMENT
    applicability: str  # REQUIRED, NOT_APPLICABLE, Q
    period_ids: tuple[str, ...]
    evidence: Evidence


@dataclass(frozen=True)
class PeriodProtection:
    cash_period: CashPeriod
    status: str  # PASS, FAIL, Q
    evidence: Evidence


@dataclass(frozen=True)
class PopulationQualification:
    population_id: str
    model_id: str
    version: str
    output_sha256: str
    weighting_ref: str
    diagnostics_ref: str
    uncertainty_ref: str
    sensitivity_ref: str
    coverage_ref: str
    claim: str  # JOINT_QUALIFYING_POPULATION_NOT_MEAN
    evidence: Evidence


@dataclass(frozen=True)
class HouseholdProtection:
    candidate_digest: str
    frame_digest: str
    period_inventory_digest: str
    mode: str  # HOUSEHOLD_PERIODS or POPULATION_JOINT_ESTIMATE
    results: tuple[PeriodProtection, ...]
    population_qualification: PopulationQualification | None = None


@dataclass(frozen=True)
class EffectContribution:
    effect_id: str
    source_event_id: str
    economic_contribution_id: str
    included_effect_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class OverlapAssessment:
    candidate_digest: str
    frame_digest: str
    numerator_output_digest: str
    denominator_output_digest: str
    accounting_boundary: str
    coverage: str  # COMPLETE or Q; caller's qualified claim, never ID inference
    contributions: tuple[EffectContribution, ...]
    excluded_effect_ids: tuple[str, ...]
    known_overlapping_pairs: tuple[tuple[str, str], ...]
    evidence: Evidence


@dataclass(frozen=True)
class Candidate:
    identity: CandidateIdentity
    measurements: tuple[Measurement, ...]
    required_cash_periods: tuple[CashPeriod, ...]
    period_inventory_evidence: Evidence
    protection: HouseholdProtection | None
    overlap: OverlapAssessment | None
    utility_redundancy_notes: tuple[str, ...] = ()
    first_cashflow_on: str | None = None
    cash_coverage: tuple[CashCoverage, ...] = ()


def cash_scope_digest(candidate):
    """Bind supplied complete period inventory, first day and applicability."""
    return fingerprint((candidate.first_cashflow_on, candidate.required_cash_periods,
                        candidate.cash_coverage, candidate.period_inventory_evidence))


@dataclass(frozen=True)
class MetricRole:
    metric_digest: str
    role: str  # OBJECTIVE, HARD_CONSTRAINT, DIAGNOSTIC or EXCLUDED
    qualification_ref: str


@dataclass(frozen=True)
class RatioPolicy:
    policy_id: str
    version: str
    mode: str  # SCN or CANONICAL; current canonical owner definitions remain Q
    method: str
    frame_digest: str
    numerator_metric_digest: str
    denominator_metric_digest: str
    ratio_unit: str
    roles: tuple[MetricRole, ...]
    constraints: tuple[Constraint, ...]
    utility_mappings: tuple[UtilityMapping, ...]
    evidence: Evidence
    tie_presentation: str = "STABLE_CANDIDATE_ID_NO_PREFERENCE"
    unused_weights: tuple[tuple[str, object], ...] = ()


@dataclass(frozen=True)
class MetricTrace:
    definition: MetricDefinition
    measurement: Measurement | None
    raw_quantity: Fraction | None
    status: str
    reasons: tuple[str, ...]

    @property
    def definition_sha256(self):
        return fingerprint(self.definition)


@dataclass(frozen=True)
class UtilityTrace:
    mapping: UtilityMapping
    raw: MetricTrace
    status: str
    value: Fraction | None
    segment: tuple[tuple[Fraction, Fraction], ...]
    reason: str


@dataclass(frozen=True)
class ConstraintResult:
    constraint: Constraint
    status: str
    assessed_value: Fraction | None


@dataclass(frozen=True)
class RatioResult:
    status: str
    numerator: Fraction | None
    denominator: Fraction | None
    value: Fraction | None
    unit: str


@dataclass(frozen=True)
class CandidateResult:
    candidate: Candidate
    status: str
    metrics: tuple[MetricTrace, ...]
    utilities: tuple[UtilityTrace, ...]
    constraints: tuple[ConstraintResult, ...]
    protection_status: str
    overlap_status: str
    ratio: RatioResult
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonResult:
    frame: ComparisonFrame
    policy: RatioPolicy
    candidates: tuple[CandidateResult, ...]
    tie_groups: tuple[tuple[str, ...], ...]
    unresolved_candidates: tuple[str, ...]
    blocked_candidates: tuple[str, ...]
    nonpositive_denominator_candidates: tuple[str, ...]
    arithmetic_scope_complete: bool
    authority: str
    canonical_readiness: str
    selected_or_funded: bool = False
    individual_permission: bool = False


def _measurement_trace(definition, measurement, identity, frame):
    definition.validate()
    reasons = []
    if not definition.ready:
        reasons.append("METRIC_DEFINITION_Q")
    if definition.quantity_dimension == "MONETARY" and definition.money_basis is None:
        reasons.append("MONETARY_BASIS_Q")
    if measurement is None:
        return MetricTrace(definition, None, None, "Q", tuple(reasons + ["MEASUREMENT_MISSING"]))
    m = measurement
    _require(m.metric_digest == fingerprint(definition), "measurement definition digest mismatch")
    _require(m.candidate_digest == fingerprint(identity), "measurement candidate/baseline/bundle mismatch")
    _require(m.frame_digest == fingerprint(frame), "measurement comparison frame mismatch")
    for name in ("measurement_id", "unit", "producer", "output_id", "output_version", "evaluation_contract"):
        _text(getattr(m, name), name)
    _require(definition.unit is None or m.unit == definition.unit, "measurement native unit mismatch")
    _require(m.native_status in {"READY", "Q", "FAIL", "UNIMPLEMENTED", "EXTERNAL_ADMISSION"},
             "native producer status")
    raw = exact(m.quantity)
    _tuple(m.native_periods, "native event periods")
    _require(bool(m.native_periods), "native periods required")
    for period in m.native_periods:
        period.validate()
    m.evaluation_period.validate()
    m.evidence.validate()
    if m.evaluation_period != frame.evaluation_horizon:
        _require(m.period_adapter is not None, "native inclusive/half-open evaluation needs explicit adapter")
        m.period_adapter.validate()
        _require(m.period_adapter.original == m.evaluation_period and
                 m.period_adapter.target == frame.evaluation_horizon, "period adapter binding mismatch")
        if not m.period_adapter.evidence.ready:
            reasons.append("PERIOD_ADAPTER_Q")
    elif m.period_adapter is not None:
        m.period_adapter.validate()
        _require(m.period_adapter.original == m.evaluation_period and
                 m.period_adapter.target == frame.evaluation_horizon, "irrelevant period adapter")
    _require(m.evaluation_contract == frame.valuation_method, "upstream evaluation contract mismatch")
    _require(definition.counterfactual_method in {None, frame.counterfactual_method} and
             definition.valuation_method in {None, frame.valuation_method}, "metric comparison methodology mismatch")
    _tuple(m.transformations, "upstream transformations")
    for transform in m.transformations:
        _require(transform.kind in {"CONVERSION", "VALUATION", "AGGREGATION"}, "upstream transformation kind")
        _hash(transform.original_output_sha256, "original output")
        for name in ("original_basis", "target_basis", "method_ref"):
            _text(getattr(transform, name), name)
        _require(transform.kind == "CONVERSION" or transform.original_money_basis is None,
                 "original monetary context is only supported for a native Conversion")
        if transform.kind == "CONVERSION":
            _validate_native_transformation(transform.native_binding, Conversion)
            conversion = transform.native_binding
            _require(conversion.original.basis_id == transform.original_basis and
                     conversion.converted.basis_id == transform.target_basis, "conversion original/target basis mismatch")
            _require(conversion.converted.unit == m.unit and exact(conversion.converted.value) == raw,
                     "conversion must bind the actual supplied output quantity/unit")
            source_basis = transform.original_money_basis
            if source_basis is None:
                reasons.append("CONVERSION_ORIGINAL_MONEY_BASIS_Q")
            else:
                _validate_native_money_basis(source_basis)
                _require(source_basis.basis_id == conversion.original.basis_id,
                         "conversion original MoneyBasis identity mismatch")
                _require(conversion.original.unit == source_basis.currency,
                         "conversion original currency must match its declared MoneyBasis")
                if _has_b12_q(source_basis):
                    reasons.append("CONVERSION_ORIGINAL_MONEY_BASIS_Q")
        if transform.kind == "VALUATION":
            _validate_native_transformation(transform.native_binding, Valuation)
            _require(transform.native_binding.basis_id == transform.target_basis and
                     transform.method_ref == frame.valuation_method, "valuation target/method mismatch")
        if transform.kind in {"CONVERSION", "VALUATION"}:
            _require(definition.quantity_dimension != "NONMONETARY", "monetary transformation cannot supply a physical metric")
            if definition.money_basis is None:
                reasons.append("UPSTREAM_TARGET_MONEY_BASIS_Q")
            else:
                _validate_native_money_basis(definition.money_basis)
                _require(definition.money_basis.basis_id == transform.target_basis,
                         "transformed money output must retain its declared target basis")
                if transform.kind == "CONVERSION":
                    _require(transform.native_binding.converted.unit == definition.money_basis.currency,
                             "conversion target currency must match its declared MoneyBasis")
                    source_basis = transform.original_money_basis
                    target_basis = definition.money_basis
                    if source_basis is not None and source_basis.basis_id == target_basis.basis_id:
                        same_known_context = ((source_basis.currency, source_basis.nominal_real, source_basis.price_date) ==
                                              (target_basis.currency, target_basis.nominal_real, target_basis.price_date))
                        convention_unknown = "Q" in {source_basis.convention.kind, target_basis.convention.kind}
                        _require(same_known_context and (convention_unknown or source_basis.convention == target_basis.convention),
                                 "conversion cannot reuse one basis identity for conflicting monetary contexts")
            if _has_b12_q(transform.native_binding):
                reasons.append("UPSTREAM_B12_TRANSFORMATION_Q")
        if not transform.evidence.ready:
            reasons.append("UPSTREAM_TRANSFORMATION_Q")
    if m.producer == "B12" or m.b12_binding is not None:
        _validate_b12_measurement(m, identity, definition)
        if not m.b12_binding.correspondence.ready:
            reasons.append("B12_CANDIDATE_CORRESPONDENCE_Q")
    if m.native_status != "READY":
        reasons.append(f"PRODUCER_{m.native_status}")
    if raw is None:
        reasons.append("QUANTITY_Q")
    if not m.evidence.ready:
        reasons.append("OUTPUT_QUALIFICATION_Q")
    return MetricTrace(definition, m, raw, "FAIL" if m.native_status == "FAIL" else
                       "Q" if reasons else "READY", tuple(reasons))


def _validate_native_record(binding, native_type):
    """Reuse the unchanged B12 recursive type and leaf validation rules."""
    try:
        _b12_shape(binding, native_type, "transformation.native_binding")
        def validate_leaves(value):
            if type(value) in {Scalar, Reference, B12Period}:
                value.__post_init__()
            if is_dataclass(value):
                for field in fields(value):
                    validate_leaves(getattr(value, field.name))
        validate_leaves(binding)
    except B12ContractError as exc:
        raise BenefitContractError(f"invalid native B12 transformation: {exc}") from exc


def _validate_native_money_basis(basis):
    _validate_native_record(basis, MoneyBasis)
    _require(basis.nominal_real in {"NOMINAL", "REAL"}, "native monetary nominal/real basis")


def _validate_native_transformation(binding, native_type):
    """Validate supplied B12 fields and identities without computing a result.

    These are the existing Conversion/Valuation rules from B12.validate_case,
    under its precision-50 ROUND_HALF_EVEN arithmetic. Monetary basis/unit
    bindings are checked separately against the explicit source/target context;
    no unrelated Case sections or financial consumers are required.
    """
    _validate_native_record(binding, native_type)
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        if native_type is Conversion:
            _require(binding.multiplier.unit == "ratio", "native conversion factor unit")
            original, multiplier, converted = (s.value for s in (binding.original, binding.multiplier, binding.converted))
            if all(v is not None for v in (original, multiplier, converted)):
                _require(multiplier > 0 and original * multiplier == converted,
                         "supplied upstream conversion identity is inconsistent")
        elif native_type is Valuation:
            _require(binding.discount_rate.basis_id == binding.basis_id, "native discount nominal/real basis mismatch")
            for rate in (binding.discount_rate, binding.nominal_rate, binding.real_rate, binding.inflation):
                _require(rate.unit == "ratio" and (rate.value is None or rate.value > -1),
                         "native valuation rate unit/domain")
            nominal, real, inflation = (s.value for s in (binding.nominal_rate, binding.real_rate, binding.inflation))
            if all(v is not None for v in (nominal, real, inflation)):
                _require(1 + nominal == (1 + real) * (1 + inflation), "native nominal-real Fisher identity")


def _validate_mapping(mapping, definitions, frame):
    _text(mapping.mapping_id, "mapping_id")
    _text(mapping.version, "mapping version")
    _require(mapping.metric_digest in definitions and mapping.frame_digest == fingerprint(frame), "utility basis mismatch")
    _require(mapping.raw_direction in {"MINIMIZE", "MAXIMIZE"}, "utility preference direction")
    _tuple(mapping.domain, "utility domain")
    _tuple(mapping.anchors, "utility anchors")
    _require(len(mapping.domain) == 2 and len(mapping.anchors) >= 2, "explicit domain and at least two anchors")
    domain = tuple(exact(x) for x in mapping.domain)
    _require(None not in domain and domain[0] < domain[1], "ordered known utility domain")
    points = []
    for pair in mapping.anchors:
        _require(type(pair) is tuple and len(pair) == 2, "anchor is exact (raw, utility)")
        x, y = map(exact, pair)
        _require(x is not None and y is not None, "utility anchor cannot be Q")
        points.append((x, y))
    _require((points[0][0], points[-1][0]) == domain, "anchors must cover exactly the declared domain")
    for a, b in zip(points, points[1:]):
        _require(a[0] < b[0], "utility abscissae must strictly increase")
        _require(b[1] >= a[1] if mapping.raw_direction == "MAXIMIZE" else b[1] <= a[1],
                 "utility must be monotone in the declared preference direction")
    mapping.evidence.validate()
    return tuple(points)


def _utility_trace(mapping, trace, points):
    if trace.status != "READY" or not mapping.evidence.ready:
        return UtilityTrace(mapping, trace, "Q", None, (), "RAW_OR_MAPPING_Q")
    x = trace.raw_quantity
    if x < points[0][0] or x > points[-1][0]:
        return UtilityTrace(mapping, trace, "Q", None, (), "OUTSIDE_QUALIFIED_DOMAIN")
    for point in points:
        if x == point[0]:
            return UtilityTrace(mapping, trace, "READY", point[1], (point,), "EXACT_ANCHOR")
    for a, b in zip(points, points[1:]):
        if a[0] < x < b[0]:
            value = a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
            return UtilityTrace(mapping, trace, "READY", value, (a, b), "PIECEWISE_LINEAR")
    raise BenefitContractError("utility segment missing")


def _constraint_result(c, trace, utility):
    value = trace.raw_quantity if c.space == "RAW" else utility.value
    ready = trace.status == "READY" if c.space == "RAW" else utility.status == "READY"
    if not ready or not c.evidence.ready:
        return ConstraintResult(c, "Q", value)
    lower, upper = exact(c.lower), exact(c.upper)
    failed = (lower is not None and value < lower) or (upper is not None and value > upper)
    missing = (c.operator in {"LOWER_BOUND", "RANGE"} and lower is None) or (c.operator in {"UPPER_BOUND", "RANGE"} and upper is None)
    return ConstraintResult(c, "FAIL" if failed else "Q" if missing else "PASS", value)


def _protection(candidate, frame):
    inventory = _unique(candidate.required_cash_periods, lambda p: p.period_id, "cash period")
    candidate.period_inventory_evidence.validate()
    for period in inventory.values():
        _require(period.kind in {"INITIAL", "INTERIM", "PAYMENT", "SETTLEMENT"}, "cash period kind")
        period.period.validate()
    p = candidate.protection
    if p is None:
        return "Q"
    _require(p.candidate_digest == fingerprint(candidate.identity) and p.frame_digest == fingerprint(frame),
             "household protection candidate/bundle/baseline/frame mismatch")
    _require(p.period_inventory_digest == cash_scope_digest(candidate), "protection period inventory mismatch")
    expected_mode = "HOUSEHOLD_PERIODS" if frame.claim_scope == "HOUSEHOLD" else "POPULATION_JOINT_ESTIMATE"
    _require(p.mode == expected_mode, "population evidence cannot protect an individual household")
    ready = candidate.period_inventory_evidence.ready
    if frame.claim_scope == "POPULATION":
        q = p.population_qualification
        _require(isinstance(q, PopulationQualification), "joint qualifying population binding required")
        _require(q.population_id == candidate.identity.scope_id and q.claim == "JOINT_QUALIFYING_POPULATION_NOT_MEAN",
                 "population mean or unrelated population cannot establish qualifying population")
        _hash(q.output_sha256, "population output")
        for name in ("model_id", "version", "weighting_ref", "diagnostics_ref", "uncertainty_ref", "sensitivity_ref", "coverage_ref"):
            _text(getattr(q, name), name)
        ready = q.evidence.ready and ready
    else:
        _require(p.population_qualification is None, "household protection cannot inherit population qualification")
    results = _unique(p.results, lambda r: r.cash_period.period_id, "protection period result")
    statuses = []
    for key, row in results.items():
        _require(key in inventory and row.cash_period == inventory[key], "protection cash period mismatch")
        _require(row.status in {"PASS", "FAIL", "Q"}, "protection status")
        statuses.append(row.status if row.evidence.ready else "Q")
    if "FAIL" in statuses:
        return "FAIL"
    coverage = _unique(candidate.cash_coverage, lambda c: c.kind, "cash coverage")
    kinds = {"INITIAL", "INTERIM", "PAYMENT", "SETTLEMENT"}
    _require(set(coverage) <= kinds, "unknown cash coverage kind")
    covered_ids = set()
    for row in coverage.values():
        _require(row.applicability in {"REQUIRED", "NOT_APPLICABLE", "Q"}, "cash scope applicability")
        _tuple(row.period_ids, "cash coverage period IDs")
        _require(len(set(row.period_ids)) == len(row.period_ids) and set(row.period_ids) <= set(inventory),
                 "cash coverage references an absent or repeated period")
        _require(row.applicability != "NOT_APPLICABLE" or not row.period_ids, "inapplicable cash scope cannot hide periods")
        if row.applicability == "REQUIRED":
            ready = bool(row.period_ids) and ready
            covered_ids.update(row.period_ids)
        ready = row.applicability != "Q" and row.evidence.ready and ready
    initial = coverage.get("INITIAL")
    first_day_covered = False
    if candidate.first_cashflow_on is not None:
        try:
            first = date.fromisoformat(candidate.first_cashflow_on)
            _require(first.isoformat() == candidate.first_cashflow_on, "first cashflow date must be ISO")
        except (TypeError, ValueError) as exc:
            raise BenefitContractError("explicit first cashflow date") from exc
        if initial is not None and initial.applicability == "REQUIRED":
            for key in initial.period_ids:
                period = inventory[key].period
                start, end = date.fromisoformat(period.start), date.fromisoformat(period.end)
                first_day_covered |= start <= first <= end if period.convention == "INCLUSIVE" else start <= first < end
    complete = set(coverage) == kinds and covered_ids == set(inventory) and first_day_covered
    return "PASS" if ready and complete and results.keys() == inventory.keys() and "Q" not in statuses else "Q"


def _overlap(candidate, frame, numerator, denominator):
    o = candidate.overlap
    if o is None:
        return "Q"
    _require(o.candidate_digest == fingerprint(candidate.identity) and o.frame_digest == fingerprint(frame),
             "overlap candidate/frame mismatch")
    _require(o.numerator_output_digest == fingerprint(numerator.measurement) and
             o.denominator_output_digest == fingerprint(denominator.measurement), "overlap output binding mismatch")
    _text(o.accounting_boundary, "overlap accounting boundary")
    _require(o.accounting_boundary == numerator.definition.consolidation_boundary,
             "overlap review must cover numerator accounting boundary")
    _require(o.coverage in {"COMPLETE", "Q"}, "overlap coverage")
    _tuple(o.contributions, "contribution lineage")
    effects, economic_contributions, included = set(), set(), set()
    conflict = False
    for contribution in o.contributions:
        _text(contribution.effect_id, "effect_id")
        _text(contribution.source_event_id, "source_event_id")
        _text(contribution.economic_contribution_id, "economic_contribution_id")
        _tuple(contribution.included_effect_ids, "included effects")
        for effect in contribution.included_effect_ids:
            _text(effect, "included effect")
        if contribution.effect_id in effects or contribution.economic_contribution_id in economic_contributions:
            conflict = True
        effects.add(contribution.effect_id)
        economic_contributions.add(contribution.economic_contribution_id)
        declared = {contribution.effect_id, *contribution.included_effect_ids}
        if included & declared:
            conflict = True
        included |= declared
    _tuple(o.excluded_effect_ids, "excluded effects")
    for effect in o.excluded_effect_ids:
        _text(effect, "excluded effect")
    conflict |= bool(included & set(o.excluded_effect_ids))
    _tuple(o.known_overlapping_pairs, "known overlapping pairs")
    for pair in o.known_overlapping_pairs:
        _require(type(pair) is tuple and len(pair) == 2, "overlap pair")
        for effect in pair:
            _text(effect, "overlapping effect")
        conflict |= all(effect in included for effect in pair)
    o.evidence.validate()
    if conflict:
        return "FAIL_DECLARED_OVERLAP"
    if o.coverage == "Q" or not o.evidence.ready:
        return "Q"
    return "CONDITIONAL_SCN" if o.evidence.mode == "SCN" else "QUALIFIED_UPSTREAM"


def _ratio(numerator, denominator, unit):
    n = numerator.raw_quantity if numerator.status == "READY" else None
    d = denominator.raw_quantity if denominator.status == "READY" else None
    if d is None:
        return RatioResult("DENOMINATOR_Q", n, None, None, unit)
    if d == 0:
        return RatioResult("ZERO_DENOMINATOR", n, d, None, unit)
    if d < 0:
        return RatioResult("NEGATIVE_DENOMINATOR", n, d, None, unit)
    if n is None:
        return RatioResult("NUMERATOR_Q", None, d, None, unit)
    return RatioResult("READY", n, d, n / d, unit)


def compare_benefit_ratios(*, frame, definitions, policy, candidates):
    """Compose raw/utility/constraint traces and ratio tie groups, without selection."""
    load_benefit_contract()
    frame.validate()
    by_id = _unique(definitions, lambda d: d.metric_id, "metric definition")
    for definition in by_id.values():
        definition.validate()
    defs = {fingerprint(d): d for d in definitions}
    _text(policy.policy_id, "policy id")
    _text(policy.version, "policy version")
    _require(policy.method == "RATIO_ORDERING", "only explicitly declared RATIO_ORDERING is supported")
    _require(policy.mode in {"SCN", "CANONICAL"}, "comparison authority mode")
    _require(policy.frame_digest == fingerprint(frame), "policy comparison frame mismatch")
    _require(policy.tie_presentation == "STABLE_CANDIDATE_ID_NO_PREFERENCE", "tie convention")
    policy.evidence.validate()
    _tuple(policy.unused_weights, "unused weights")
    roles = _unique(policy.roles, lambda r: r.metric_digest, "metric role")
    _require(roles.keys() == defs.keys(), "every declared metric needs an explicit role")
    for key, role in roles.items():
        _require(role.role in {"OBJECTIVE", "HARD_CONSTRAINT", "DIAGNOSTIC", "EXCLUDED"}, "metric role")
        _text(role.qualification_ref, "role/exclusion qualification")
    nkey, dkey = policy.numerator_metric_digest, policy.denominator_metric_digest
    _require(nkey in defs and dkey in defs and nkey != dkey, "distinct numerator and denominator definitions required")
    _require({key for key, role in roles.items() if role.role == "OBJECTIVE"} == {nkey, dkey},
             "ratio method uses exactly its numerator and denominator")
    ndef, ddef = defs[nkey], defs[dkey]
    if ddef.ready:
        _require(ddef.denominator_kind != "NONE" and ddef.actor == "PUBLIC", "public cost denominator required")
        _require(ddef.quantity_dimension == "MONETARY" and ddef.unit == "HUF" and
                 ddef.money_basis is not None and ddef.money_basis.currency == "HUF",
                 "public denominator must use an explicit HUF money basis")
    if ndef.money_basis is not None and ddef.money_basis is not None:
        _require(ndef.money_basis == ddef.money_basis, "ratio monetary bases differ; qualify conversion upstream")
    _require(policy.ratio_unit == f"{ndef.unit or 'Q'}/HUF", "ratio units must retain numerator unit per HUF")
    mappings = _unique(policy.utility_mappings, fingerprint, "utility mapping")
    points = {key: _validate_mapping(m, defs, frame) for key, m in mappings.items()}
    constraints = _unique(policy.constraints, lambda c: c.constraint_id, "constraint")
    for c in constraints.values():
        _require(c.metric_digest in defs and c.frame_digest == fingerprint(frame), "constraint metric/frame mismatch")
        _require(type(c.required) is bool, "constraint required must be boolean")
        _require(c.space in {"RAW", "UTILITY"} and c.operator in {"LOWER_BOUND", "UPPER_BOUND", "RANGE"}, "constraint operator/space")
        low, high = exact(c.lower), exact(c.upper)
        _require((c.operator != "LOWER_BOUND" or high is None) and
                 (c.operator != "UPPER_BOUND" or low is None), "inactive bound endpoint must be absent")
        _require(low is None or high is None or low <= high, "ordered bound range")
        if c.space == "RAW":
            _require(c.utility_digest is None and c.unit == defs[c.metric_digest].unit, "raw bound unit/map mismatch")
        else:
            _require(c.utility_digest in mappings and mappings[c.utility_digest].metric_digest == c.metric_digest
                     and c.unit == "UTILITY", "utility constraint needs its exact mapping")
        if c.required:
            _require(roles[c.metric_digest].role in {"OBJECTIVE", "HARD_CONSTRAINT"}, "required constraint cannot be excluded or diagnostic")
        c.evidence.validate()
    for key, role in roles.items():
        if role.role == "HARD_CONSTRAINT":
            _require(any(c.required and c.metric_digest == key for c in constraints.values()), "hard constraint role without required bound")
    owner = json.loads((ROOT / "registry/owner_policy_decisions.json").read_text())
    selected = owner["decisions"]["selection_priority"]
    canonical_q = any(selected[key] is None for key in ("benefit_metric_definition", "public_cost_denominator"))
    # This slice cannot adopt a new policy through an API argument or a future registry edit.
    _require(canonical_q, "owner metric adoption needs a separately reviewed policy binding")
    candidate_map = _unique(candidates, lambda c: c.identity.candidate_id, "candidate")
    _require(bool(candidate_map), "comparison needs an explicit candidate universe")
    results = []
    for candidate in candidate_map.values():
        candidate.identity.validate(frame)
        measures = _unique(candidate.measurements, lambda m: m.metric_digest, "candidate measurement")
        _require(set(measures) <= set(defs), "undeclared measurement definition")
        _unique(candidate.measurements, lambda m: m.measurement_id, "measurement id")
        traces = {key: _measurement_trace(d, measures.get(key), candidate.identity, frame) for key, d in defs.items()}
        utilities = {key: _utility_trace(m, traces[m.metric_digest], points[key]) for key, m in mappings.items()}
        checks = tuple(_constraint_result(c, traces[c.metric_digest], utilities.get(c.utility_digest))
                       for c in constraints.values())
        protection = _protection(candidate, frame)
        overlap = _overlap(candidate, frame, traces[nkey], traces[dkey])
        ratio = _ratio(traces[nkey], traces[dkey], policy.ratio_unit)
        _tuple(candidate.utility_redundancy_notes, "utility redundancy notes")
        for note in candidate.utility_redundancy_notes:
            _text(note, "utility redundancy note")
        reasons = []
        required = [traces[key].status for key, role in roles.items() if role.role in {"OBJECTIVE", "HARD_CONSTRAINT"}]
        fail = protection == "FAIL" or overlap == "FAIL_DECLARED_OVERLAP" or "FAIL" in required
        fail |= any(c.status == "FAIL" and c.constraint.required for c in checks)
        unknown = protection == "Q" or overlap == "Q" or "Q" in required
        unknown |= any(c.status == "Q" and c.constraint.required for c in checks)
        unknown |= not frame.evidence.ready or not policy.evidence.ready
        if protection != "PASS":
            reasons.append(f"HOUSEHOLD_PROTECTION_{protection}")
        if overlap in {"Q", "FAIL_DECLARED_OVERLAP"}:
            reasons.append(f"MONETARY_OVERLAP_{overlap}")
        for key, role in roles.items():
            if role.role in {"OBJECTIVE", "HARD_CONSTRAINT"} and traces[key].status != "READY":
                reasons.append(f"REQUIRED_METRIC_{defs[key].metric_id}_{traces[key].status}")
        reasons.extend(f"CONSTRAINT_{c.constraint.constraint_id}_{c.status}" for c in checks
                       if c.constraint.required and c.status != "PASS")
        if policy.mode == "CANONICAL":
            unknown = True
            reasons.append("Q-B01-006_CANONICAL_METRIC_AND_DENOMINATOR_UNSET")
        if ratio.status != "READY":
            reasons.append(ratio.status)
        nonpositive = ratio.status in {"ZERO_DENOMINATOR", "NEGATIVE_DENOMINATOR"}
        status = "BLOCKED" if fail else "UNRESOLVED" if unknown else "NONPOSITIVE_DENOMINATOR" if nonpositive else "COMPARABLE"
        if status == "COMPARABLE" and ratio.status != "READY":
            status = "UNRESOLVED"
        results.append(CandidateResult(candidate, status, tuple(traces.values()), tuple(utilities.values()),
                                       checks, protection, overlap, ratio, tuple(reasons)))
    comparable = sorted((r for r in results if r.status == "COMPARABLE"),
                        key=lambda r: (-r.ratio.value, r.candidate.identity.candidate_id))
    groups = []
    last = None
    for result in comparable:
        if last != result.ratio.value:
            groups.append([])
        groups[-1].append(result.candidate.identity.candidate_id)
        last = result.ratio.value
    def ids(status):
        return tuple(sorted(r.candidate.identity.candidate_id for r in results if r.status == status))
    unknown_ids = ids("UNRESOLVED")
    nonpositive_ids = tuple(sorted(r.candidate.identity.candidate_id for r in results
                                 if r.ratio.status in {"ZERO_DENOMINATOR", "NEGATIVE_DENOMINATOR"}))
    return ComparisonResult(frame, policy, tuple(results), tuple(tuple(g) for g in groups), unknown_ids,
                            ids("BLOCKED"), nonpositive_ids, not unknown_ids and not nonpositive_ids,
                            "CONDITIONAL_SCENARIO_COMPARISON" if policy.mode == "SCN" else "CANONICAL_NOT_READY",
                            "Q-B01-006_OPEN")


def _validate_b12_measurement(m, identity, definition):
    b = m.b12_binding
    _require(m.producer == "B12" and isinstance(b, B12Binding), "exact B12 producer binding required")
    _require(fingerprint(b.case) == b.case_sha256 and fingerprint(b.audit) == b.audit_sha256,
             "B12 case/output digest mismatch")
    _require(b.candidate_digest == fingerprint(identity), "exact B12 case-to-candidate correspondence required")
    b.correspondence.validate()
    try:
        validate_case(b.case)
    except B12ContractError as exc:
        raise BenefitContractError(f"invalid native B12 Case: {exc}") from exc
    _require(fingerprint(audit_accounting(b.case)) == b.audit_sha256,
             "B12 audit must be the actual existing producer output for this exact Case")
    _require(b.audit.case_id == b.case.case_id and b.audit.mode == b.case.mode and
             b.audit.basis == b.case.monetary_basis, "B12 output context mismatch")
    _require(b.case.baseline_id == identity.baseline_id and b.case.programme_id == identity.programme_id,
             "B12 counterfactual identities mismatch")
    _require(b.case.scope.household_id == identity.scope_id and identity.claim_scope == "HOUSEHOLD",
             "B12 household output cannot become population or another household")
    _require(definition.money_basis == b.case.monetary_basis, "B12 MoneyBasis must remain exact")
    _require(m.evaluation_period.start == b.case.evaluation_period.start.isoformat() and
             m.evaluation_period.end == b.case.evaluation_period.end.isoformat() and
             m.evaluation_period.convention == "INCLUSIVE", "B12 native inclusive evaluation period must be retained")
    native_period = Period(b.case.physical_reference_period.start.isoformat(),
                           b.case.physical_reference_period.end.isoformat(), "INCLUSIVE", m.evaluation_period.timezone)
    _require(m.native_periods == (native_period,), "B12 native physical period must be retained")
    # A Case/reference is not a result. Only an actually present ready synthetic
    # accounting bucket can supply a number; valuation/affordability stay Q.
    ready = (b.case.mode == SYNTHETIC and b.audit.truth == "SCN" and
             b.output_key in b.audit.amounts and b.output_key.split(".")[0] not in b.audit.unavailable)
    expected = b.audit.amounts[b.output_key] if ready else None
    _require(exact(m.quantity) == exact(expected) and m.native_status == ("READY" if ready else "Q"),
             "B12 unresolved producer cannot be promoted to a numerical result")
    if ready:
        _require(m.evidence.mode == "SCN", "synthetic B12 output remains SCN")
        bucket, leg, *_ = b.output_key.split(".")
        native_actors = {"unfinanced_cash": "HOUSEHOLD", "financed_cash": "HOUSEHOLD",
                         "recurring_budget": "HOUSEHOLD", "retail_bills": "HOUSEHOLD",
                         "outstanding_debt": "HOUSEHOLD", "total_initial_cost": "CASE_COST_SCOPE",
                         "eligible_initial_cost": "CASE_COST_SCOPE", "lifecycle_cost": "CASE_COST_SCOPE",
                         "vat": "CASE_TAX_SCOPE", "noncash_terminal": "CASE_ASSET_SCOPE"}
        _require(definition.concept == "B12:" + b.output_key and
                 definition.actor == native_actors.get(bucket) and
                 definition.meaning == ("INCREMENTAL" if leg == "incremental" else "TOTAL"),
                 "B12 bucket cannot be relabelled as another metric, actor or incremental/total meaning")


def _has_b12_q(value):
    if isinstance(value, Reference):
        return value.kind == "Q"
    if isinstance(value, Scalar):
        return value.truth == "Q"
    if is_dataclass(value):
        return any(_has_b12_q(getattr(value, f.name)) for f in fields(value))
    if isinstance(value, tuple):
        return any(_has_b12_q(item) for item in value)
    return False


def bind_b12_output(*, case, audit, output_key, definition, identity, frame, evidence, correspondence,
                    period_adapter=None):
    """Retain exact existing B12 Case/audit; no new accounting or valuation run.

    This bounded adapter is only for the original Case's single household and
    transition context. Composite bundles should use separately qualified
    Measurement outputs, never invent a legacy S-state transition for this call.
    """
    binding = B12Binding(case, audit, output_key, fingerprint(case), fingerprint(audit),
                         fingerprint(identity), correspondence)
    ready = (case.mode == SYNTHETIC and audit.truth == "SCN" and output_key in audit.amounts
             and output_key.split(".")[0] not in audit.unavailable)
    zone = frame.evaluation_horizon.timezone
    value = Measurement(output_key, fingerprint(definition), fingerprint(identity), fingerprint(frame),
                        audit.amounts[output_key] if ready else None, definition.unit,
                        (Period(case.physical_reference_period.start.isoformat(), case.physical_reference_period.end.isoformat(), "INCLUSIVE", zone),),
                        Period(case.evaluation_period.start.isoformat(), case.evaluation_period.end.isoformat(), "INCLUSIVE", zone),
                        frame.valuation_method, "READY" if ready else "Q", "B12", case.case_id + ":" + output_key,
                        "B12_INPUT_ACCOUNTING_CONTRACT", evidence, (), period_adapter, binding)
    _measurement_trace(definition, value, identity, frame)
    return value


def load_benefit_contract():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    _require(contract["contract_id"] == "B01-BENEFIT-METRIC-CONTRACT" and contract["schema_version"] == "1.2.0", "benefit contract version")
    _require(contract["supported_metric_output_units"] == {kind: list(units) for kind, units in METRIC_UNITS.items()},
             "metric unit/dimension vocabulary differs from the bounded executable contract")
    _require(contract["supported_methods"] == ["RATIO_ORDERING"], "bounded comparison method")
    _require(not contract["numeric_defaults"] and not contract["original_task_acceptance_changed"], "no policy adoption or task acceptance")
    _require(contract["canonical_question"] == "Q-B01-006" and contract["household_floor"] == "MANDATORY_FIRST_DAY_AND_INTERIM", "owner floor and Q boundary")
    return contract
