"""Exact, dated population planning; never an individual permission or observation.

The adapter consumes qualified model outputs or explicit scenarios. It neither
calibrates weights nor admits a scientific model. One declared schedule is run
unchanged in each supplied joint world. The session owns cumulative reservations;
its snapshots are reports, not a means to restore availability.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "registry/b01_population_planning_contract.json"


class PopulationPlanningError(ValueError):
    """Invalid scope, ambiguity or a definition requiring requalification."""


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise PopulationPlanningError(f"{field} must be nonempty text")


def _date(value):
    _text(value, "date")
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise PopulationPlanningError("date must be YYYY-MM-DD") from exc
    if result.isoformat() != value:
        raise PopulationPlanningError("date must be YYYY-MM-DD")
    return result


def exact(value, *, unknown=False):
    """Only exact quantities; None is Q, not zero. Floats/bools are not weights."""
    if value is None and unknown:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, str, Decimal, Fraction)):
        raise PopulationPlanningError("quantity requires exact int/decimal text/Decimal/Fraction")
    try:
        result = Fraction(value)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise PopulationPlanningError("quantity must be finite and exact") from exc
    if result < 0:
        raise PopulationPlanningError("quantity must be nonnegative")
    return result


def _canonical(value):
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, (Fraction, Decimal)):
        q = exact(value)
        return {"numerator": q.numerator, "denominator": q.denominator}
    return value


def fingerprint(value):
    return sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def _unique(items, key, name):
    result = {}
    if not isinstance(items, tuple):
        raise PopulationPlanningError(f"{name} must be an immutable tuple")
    for item in items:
        k = key(item)
        _text(k, name)
        if k in result:
            raise PopulationPlanningError(f"duplicate {name}: {k}")
        result[k] = item
    return result


def _refs(values, name):
    if not isinstance(values, tuple) or not values:
        raise PopulationPlanningError(f"{name} requires explicit references")
    for value in values:
        _text(value, name)


@dataclass(frozen=True)
class SourcePin:
    source_id: str
    sha256: str


@dataclass(frozen=True)
class PopulationIdentity:
    population_id: str
    version: str
    native_unit: str
    geography: str
    reference_date: str


@dataclass(frozen=True)
class EvidenceBinding:
    mode: str  # ADMITTED_ESTIMATE or SCN; CONTROL/Q cannot supply a state model
    evidence_status: str
    evidence_tier: str
    claim_id: str
    source_pins: tuple[SourcePin, ...]
    coverage: str
    missingness: str
    joint_uncertainty_id: str
    uncertainty_method: str
    qualification_ref: str
    qualified_claims: tuple[str, ...]
    scenario_ref: str = ""
    model_id: str = ""
    model_version: str = ""
    output_sha256: str = ""
    selection_weighting_ref: str = ""
    validation_diagnostics_ref: str = ""
    structural_sensitivity_ref: str = ""
    central_definition_id: str = ""
    validation_debt: tuple[str, ...] = ()


@dataclass(frozen=True)
class TargetControl:
    """Qualified target universe, independent of which control rows arrived."""
    control_id: str
    scope_atoms: tuple[str, ...]


@dataclass(frozen=True)
class Control:
    control_id: str
    population: PopulationIdentity
    scope_atoms: tuple[str, ...]
    mass: object
    source_id: str
    artifact_sha256: str
    evidence_status: str


@dataclass(frozen=True)
class Cell:
    cell_id: str
    control_id: str
    scope_atoms: tuple[str, ...]
    region: str


@dataclass(frozen=True)
class OriginLot:
    lot_id: str
    origin_id: str
    cell_id: str
    state_id: str
    # The partition qualification asserts disjoint origin lots, including within
    # a cell. Aliases identify the same lot; they never create additional mass.
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResourceSpec:
    resource_id: str
    kind: str  # FLOW: explicit due date; OCCUPANCY: half-open interval
    unit: str
    denominator_unit: str
    pool: str
    region: str
    actor: str
    basis: str
    evidence_ref: str


@dataclass(frozen=True)
class InterventionAlternative:
    option_id: str
    version: str
    cell_id: str
    source_state: str
    destination_state: str
    eligible_claim: str
    eligibility_meaning: str  # JOINT_INTERVENTION_ELIGIBILITY, never screening/mean cash
    valid_from: str
    valid_until: str
    resources: tuple[ResourceSpec, ...]
    requirement_inventory_ref: str
    endpoint_qualification_ref: str
    # A composite endpoint is an explicit input, not an invented component order.
    endpoint_kind: str = "QUALIFIED_MILESTONE"


@dataclass(frozen=True)
class LotValue:
    world_id: str
    lot_id: str
    represented_mass: object
    unit: str


@dataclass(frozen=True)
class ResourceValue:
    world_id: str
    resource_id: str
    per_unit_quantity: object


@dataclass(frozen=True)
class EligibleOriginInterval:
    """Supplied disjoint statistical mass coordinates, never household IDs."""
    origin_id: str
    start: object
    end: object


@dataclass(frozen=True)
class OptionValue:
    world_id: str
    option_id: str
    eligible_mass: object
    unit: str
    coefficients: tuple[ResourceValue, ...]
    # None is unknown overlap/membership, even if the eligible scalar is known.
    # This must never be generated automatically from a marginal count.
    eligible_origins: tuple[EligibleOriginInterval, ...] | None = None


@dataclass(frozen=True)
class ResourceEnvelope:
    envelope_id: str
    spec: ResourceSpec
    valid_from: str
    valid_until: str
    ceiling: object
    evidence_ref: str
    world_id: str


@dataclass(frozen=True)
class JointWorld:
    world_id: str
    joint_uncertainty_id: str
    lots: tuple[LotValue, ...]
    options: tuple[OptionValue, ...]
    envelopes: tuple[ResourceEnvelope, ...] = ()
    probability: object = None


@dataclass(frozen=True)
class PlanningInputs:
    planning_set_id: str
    version: str
    population: PopulationIdentity
    as_of: str
    horizon_until: str
    timezone: str
    calendar_version: str
    state_definition_id: str
    state_version: str
    states: tuple[str, ...]
    partition_qualification_ref: str
    target_scope_id: str
    target_controls: tuple[TargetControl, ...]
    cells: tuple[Cell, ...]
    controls: tuple[Control, ...]
    lots: tuple[OriginLot, ...]
    options: tuple[InterventionAlternative, ...]
    worlds: tuple[JointWorld, ...]
    binding: EvidenceBinding
    # Controls from a different vintage need a separate explicit premise. They
    # then remain historical context, not exact current-date reconciliation.
    roll_forward_ref: str = ""
    central_world_id: str = ""


def model_output_digest(inputs):
    """Digest of supplied output/definitions, excluding its admission receipt."""
    payload = asdict(inputs)
    payload.pop("binding")
    return fingerprint(payload)


def _pin(digest):
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise PopulationPlanningError("source/output hash must be lowercase SHA256")


def _identity(population):
    if not isinstance(population, PopulationIdentity):
        raise PopulationPlanningError("population identity required")
    for field in ("population_id", "version", "geography"):
        _text(getattr(population, field), field)
    if population.native_unit not in {"DWELLING", "HOUSEHOLD", "BUILDING"}:
        raise PopulationPlanningError("native counting unit must be DWELLING/HOUSEHOLD/BUILDING, not sample weight")
    _date(population.reference_date)


def _spec(spec, unit):
    if not isinstance(spec, ResourceSpec) or spec.kind not in {"FLOW", "OCCUPANCY"}:
        raise PopulationPlanningError("resource requires FLOW or OCCUPANCY")
    for field in ("resource_id", "unit", "pool", "region", "actor", "basis", "evidence_ref"):
        _text(getattr(spec, field), field)
    if spec.denominator_unit != unit:
        raise PopulationPlanningError("resource denominator differs from native population unit")


def _resource_key(spec):
    # resource_id/evidence_ref identify a coefficient, not a second physical pool.
    return (spec.kind, spec.unit, spec.denominator_unit, spec.pool,
            spec.region, spec.actor, spec.basis)


def adapt_population_outputs(inputs):
    """Validate the admitted-output boundary and return exact control reports.

    Qualification references are inputs, not independent scientific approval by
    this code. The admitted route checks a complete claim-specific receipt,
    output digest and E1/E2 scope. A DER/source string alone cannot pass.
    """
    if not isinstance(inputs, PlanningInputs):
        raise PopulationPlanningError("PlanningInputs required; a cell is not a household")
    _identity(inputs.population)
    for field in ("planning_set_id", "version", "calendar_version", "state_definition_id", "state_version", "partition_qualification_ref", "target_scope_id"):
        _text(getattr(inputs, field), field)
    _refs(inputs.states, "states")
    if len(set(inputs.states)) != len(inputs.states):
        raise PopulationPlanningError("duplicate state")
    if _date(inputs.as_of) != _date(inputs.population.reference_date):
        raise PopulationPlanningError("stock date must equal qualified population reference date")
    if _date(inputs.horizon_until) <= _date(inputs.as_of):
        raise PopulationPlanningError("empty planning horizon")
    try:
        ZoneInfo(inputs.timezone)
    except (ZoneInfoNotFoundError, TypeError, ValueError) as exc:
        raise PopulationPlanningError("explicit IANA timezone required") from exc
    binding = inputs.binding
    if not isinstance(binding, EvidenceBinding):
        raise PopulationPlanningError("evidence binding required")
    for field in ("claim_id", "coverage", "missingness", "joint_uncertainty_id", "uncertainty_method", "qualification_ref"):
        _text(getattr(binding, field), field)
    _refs(binding.qualified_claims, "qualified claims")
    pins = _unique(binding.source_pins, lambda p: p.source_id, "source pin")
    if not pins:
        raise PopulationPlanningError("source/control or SCN artifact hashes required")
    for pin in pins.values():
        _pin(pin.sha256)
    if binding.mode == "SCN":
        if binding.evidence_status != "SCN" or binding.evidence_tier != "E3":
            raise PopulationPlanningError("SCN output must remain SCN/E3")
        _text(binding.scenario_ref, "explicit scenario premise")
    elif binding.mode == "ADMITTED_ESTIMATE":
        if binding.evidence_status not in {"DER", "MODELLED"} or binding.evidence_tier not in {"E1", "E2"}:
            raise PopulationPlanningError("admitted output requires DER/MODELLED and E1/E2")
        for field in ("model_id", "model_version", "selection_weighting_ref", "validation_diagnostics_ref",
                      "structural_sensitivity_ref", "central_definition_id"):
            _text(getattr(binding, field), field)
        _pin(binding.output_sha256)
        if binding.output_sha256 != model_output_digest(inputs):
            raise PopulationPlanningError("admission output digest mismatch; REQUALIFICATION_REQUIRED")
        if binding.evidence_tier == "E2":
            _refs(binding.validation_debt, "E2 validation debt")
        if not inputs.central_world_id:
            raise PopulationPlanningError("admitted estimator needs its selected central definition")
    else:
        raise PopulationPlanningError("CONTROL/Q is not an allocatable state/eligibility model")
    targets = _unique(inputs.target_controls, lambda x: x.control_id, "target control")
    if not targets:
        raise PopulationPlanningError("qualified target control universe required, independently of supplied controls")
    target_atoms = set()
    for target in targets.values():
        _refs(target.scope_atoms, "target scope atoms")
        if len(set(target.scope_atoms)) != len(target.scope_atoms) or target_atoms.intersection(target.scope_atoms):
            raise PopulationPlanningError("overlapping target population definitions")
        target_atoms.update(target.scope_atoms)
    controls = _unique(inputs.controls, lambda x: x.control_id, "control")
    if not set(controls) <= set(targets):
        raise PopulationPlanningError("control outside declared target universe; REQUALIFICATION_REQUIRED")
    cells = _unique(inputs.cells, lambda x: x.cell_id, "cell")
    lots = _unique(inputs.lots, lambda x: x.lot_id, "lot")
    options = _unique(inputs.options, lambda x: x.option_id, "option")
    worlds = _unique(inputs.worlds, lambda x: x.world_id, "world")
    if not cells or not lots or not worlds:
        raise PopulationPlanningError("explicit cells, lots and joint worlds required")
    if inputs.central_world_id and inputs.central_world_id not in worlds:
        raise PopulationPlanningError("unknown central world")
    required_claims = {"STATE_DISTRIBUTION", "DISJOINT_PARTITION"}
    control_atoms = set()
    for c in controls.values():
        _identity(c.population)
        exact(c.mass, unknown=True)
        _refs(c.scope_atoms, "control scope atoms")
        if set(c.scope_atoms) != set(targets[c.control_id].scope_atoms):
            raise PopulationPlanningError("control scope differs from independently qualified target")
        if len(set(c.scope_atoms)) != len(c.scope_atoms) or control_atoms.intersection(c.scope_atoms):
            raise PopulationPlanningError("overlapping control population definitions")
        control_atoms.update(c.scope_atoms)
        if (c.population.population_id, c.population.version, c.population.native_unit, c.population.geography) != (
                inputs.population.population_id, inputs.population.version, inputs.population.native_unit, inputs.population.geography):
            raise PopulationPlanningError("control population/unit/geography mismatch; REQUALIFICATION_REQUIRED")
        if c.population.reference_date != inputs.population.reference_date and not inputs.roll_forward_ref:
            raise PopulationPlanningError("control vintage relabelled; explicit roll-forward qualification required")
        if c.source_id not in pins or pins[c.source_id].sha256 != c.artifact_sha256:
            raise PopulationPlanningError("control source hash does not match bound source")
        if c.evidence_status not in {"OBS", "DER", "SCN", "Q"} or (c.mass is None) != (c.evidence_status == "Q"):
            raise PopulationPlanningError("control missingness/status mismatch")
    cell_atoms = set()
    for c in cells.values():
        _refs(c.scope_atoms, "cell scope atoms")
        _text(c.region, "region")
        if len(set(c.scope_atoms)) != len(c.scope_atoms) or cell_atoms.intersection(c.scope_atoms):
            raise PopulationPlanningError("duplicate or aliased cell scope")
        cell_atoms.update(c.scope_atoms)
        if c.control_id not in targets or not set(c.scope_atoms) <= set(targets[c.control_id].scope_atoms):
            raise PopulationPlanningError("cell outside declared control partition")
    origins, aliases = set(), set(lots)
    for lot in lots.values():
        _text(lot.origin_id, "origin identity")
        if lot.origin_id in origins:
            raise PopulationPlanningError("duplicate origin mass; initial lots must be disjoint")
        origins.add(lot.origin_id)
        if lot.cell_id not in cells or lot.state_id not in inputs.states:
            raise PopulationPlanningError("lot cell/state mismatch")
        if not isinstance(lot.aliases, tuple):
            raise PopulationPlanningError("lot aliases must be tuple")
        for alias in lot.aliases:
            _text(alias, "lot alias")
            if alias in aliases:
                raise PopulationPlanningError("conflicting lot alias")
            aliases.add(alias)
    if {x.cell_id for x in lots.values()} != set(cells):
        raise PopulationPlanningError("every covered cell needs explicit mass, including Q/zero")
    for option in options.values():
        for field in ("version", "eligible_claim", "requirement_inventory_ref", "endpoint_qualification_ref"):
            _text(getattr(option, field), field)
        if option.cell_id not in cells or option.source_state not in inputs.states or option.destination_state not in inputs.states:
            raise PopulationPlanningError("option cell/state mismatch")
        if option.source_state == option.destination_state:
            raise PopulationPlanningError("state movement needs a distinct declared endpoint")
        if option.eligibility_meaning != "JOINT_INTERVENTION_ELIGIBILITY":
            raise PopulationPlanningError("screening/mean cash cannot qualify intervention eligibility")
        if option.endpoint_kind not in {"QUALIFIED_MILESTONE", "COMPOSITE_ENDPOINT"}:
            raise PopulationPlanningError("planning endpoint cannot become observed implementation")
        if not (inputs.as_of <= option.valid_from < option.valid_until <= inputs.horizon_until):
            raise PopulationPlanningError("option dates outside horizon")
        _date(option.valid_from); _date(option.valid_until)
        resources = _unique(option.resources, lambda x: x.resource_id, "resource")
        required_claims.add(option.eligible_claim)
        for spec in resources.values():
            _spec(spec, inputs.population.native_unit)
            if spec.region != cells[option.cell_id].region:
                raise PopulationPlanningError("resource region differs from option cell")
            required_claims.add(f"RESOURCE:{option.option_id}:{spec.resource_id}")
    required_claims.update(f"CAPACITY:{e.envelope_id}" for world in worlds.values() for e in world.envelopes)
    if not required_claims <= set(binding.qualified_claims):
        raise PopulationPlanningError("claim-specific qualification omits partition, eligibility or requirements")
    probability_values = [exact(w.probability, unknown=True) for w in worlds.values()]
    if any(p is not None for p in probability_values):
        if any(p is None for p in probability_values) or sum(probability_values) != 1:
            raise PopulationPlanningError("probabilities must be all supplied and sum exactly to one")
    reports = []
    for world in worlds.values():
        if world.joint_uncertainty_id != binding.joint_uncertainty_id:
            raise PopulationPlanningError("unrelated joint uncertainty world")
        masses = _unique(world.lots, lambda x: x.lot_id, "world lot")
        values = _unique(world.options, lambda x: x.option_id, "world option")
        if set(masses) != set(lots) or set(values) != set(options):
            raise PopulationPlanningError("world semantic universe differs; no marginal stitching")
        for value in (*masses.values(), *values.values()):
            if value.world_id != world.world_id or value.unit != inputs.population.native_unit:
                raise PopulationPlanningError("world identity or mass unit mismatch")
        for value in masses.values():
            exact(value.represented_mass, unknown=True)
        for value in values.values():
            eligible_mass = exact(value.eligible_mass, unknown=True)
            option_cell = options[value.option_id].cell_id
            cell_masses = [exact(masses[l.lot_id].represented_mass, unknown=True)
                           for l in lots.values() if l.cell_id == option_cell]
            if eligible_mass is not None and all(m is not None for m in cell_masses) and eligible_mass > sum(cell_masses, Fraction()):
                raise PopulationPlanningError("joint eligible mass exceeds its cell population")
            if value.eligible_origins is not None:
                if not isinstance(value.eligible_origins, tuple):
                    raise PopulationPlanningError("eligible origin sets must be immutable tuples or Q")
                by_origin = {}
                origin_lots = {l.origin_id: l for l in lots.values()}
                for interval in value.eligible_origins:
                    if not isinstance(interval, EligibleOriginInterval) or interval.origin_id not in origin_lots:
                        raise PopulationPlanningError("unknown eligible origin identity")
                    origin_lot = origin_lots[interval.origin_id]
                    if origin_lot.cell_id != option_cell:
                        raise PopulationPlanningError("eligible origin outside option cell/source-state scope")
                    start, end = exact(interval.start), exact(interval.end)
                    if start >= end:
                        raise PopulationPlanningError("eligible origin interval must have positive length")
                    origin_mass = exact(masses[origin_lot.lot_id].represented_mass, unknown=True)
                    if origin_mass is not None and end > origin_mass:
                        raise PopulationPlanningError("eligible origin interval exceeds its world population")
                    spans = by_origin.setdefault(interval.origin_id, [])
                    if any(start < b and a < end for a, b in spans):
                        raise PopulationPlanningError("overlapping eligible origin intervals")
                    spans.append((start, end))
                interval_mass = sum((b - a for spans in by_origin.values() for a, b in spans), Fraction())
                if eligible_mass is not None and interval_mass != eligible_mass:
                    raise PopulationPlanningError("eligible origin union differs from claimed eligible mass")
            coeffs = _unique(value.coefficients, lambda x: x.resource_id, "coefficient")
            if set(coeffs) != {r.resource_id for r in options[value.option_id].resources}:
                raise PopulationPlanningError("incomplete qualified resource inventory; use explicit Q")
            for coeff in coeffs.values():
                if coeff.world_id != world.world_id:
                    raise PopulationPlanningError("coefficient from unrelated realization")
                exact(coeff.per_unit_quantity, unknown=True)
        envelopes = _unique(world.envelopes, lambda x: x.envelope_id, "envelope")
        for env in envelopes.values():
            _spec(env.spec, inputs.population.native_unit)
            _text(env.evidence_ref, "envelope evidence")
            exact(env.ceiling, unknown=True)
            if env.world_id != world.world_id:
                raise PopulationPlanningError("envelope from unrelated realization")
            if not (inputs.as_of <= env.valid_from < env.valid_until <= inputs.horizon_until):
                raise PopulationPlanningError("envelope dates outside horizon")
            _date(env.valid_from); _date(env.valid_until)
            if _resource_key(env.spec) not in {_resource_key(r) for o in options.values() for r in o.resources}:
                raise PopulationPlanningError("envelope unit/actor/region/basis does not match any requirement")
        for target in targets.values():
            control = controls.get(target.control_id)
            covered = set().union(*(set(c.scope_atoms) for c in cells.values() if c.control_id == target.control_id))
            selected = [exact(masses[l.lot_id].represented_mass, unknown=True) for l in lots.values()
                        if cells[l.cell_id].control_id == target.control_id]
            known = sum((v for v in selected if v is not None), Fraction())
            missing = any(v is None for v in selected)
            total = None if missing else known
            control_mass = exact(control.mass, unknown=True) if control else None
            compatible = control is not None and control.population.reference_date == inputs.population.reference_date
            complete = covered == set(target.scope_atoms)
            if compatible and control_mass is not None:
                if known > control_mass or (complete and total is not None and total != control_mass):
                    raise PopulationPlanningError("compatible control mass fails exact reconciliation")
            status = ("Q_CONTROL_NOT_SUPPLIED" if control is None else "HISTORICAL_CONTEXT" if not compatible else
                      "Q" if missing else "Q_CONTROL" if control_mass is None else "EXACT" if complete else "PARTIAL")
            reports.append({"world_id": world.world_id, "target_scope_id": inputs.target_scope_id,
                            "control_id": target.control_id, "control_mass": control_mass,
                            "represented_mass": total, "known_mass": known,
                            "control_missing": control_mass is None, "control_row_missing": control is None,
                            "represented_mass_missing": missing,
                            "reconciliation_residual": total - control_mass if compatible and complete and total is not None and control_mass is not None else None,
                            "unit": inputs.population.native_unit,
                            "reference_date": control.population.reference_date if control else inputs.population.reference_date,
                            "covered_atoms": tuple(sorted(covered)),
                            "uncovered_atoms": tuple(sorted(set(target.scope_atoms) - covered)), "status": status})
    return tuple(reports)


@dataclass(frozen=True)
class ResourceWindow:
    resource_id: str
    start: str  # FLOW due date, or OCCUPANCY interval start
    end: str = ""  # required only for OCCUPANCY


@dataclass(frozen=True)
class Allocation:
    allocation_id: str
    event_id: str
    source_lot_id: str
    source_offset: object
    mass: object
    unit: str
    option_id: str
    child_lot_id: str
    work_start: str
    effective_on: str
    resource_windows: tuple[ResourceWindow, ...]
    provenance_ref: str
    planning_status: str = "PROPOSED"


@dataclass(frozen=True)
class FixedSchedule:
    plan_id: str
    version: str
    definition_digest: str
    expected_revision: int
    order_ref: str
    allocations: tuple[Allocation, ...]


@dataclass(frozen=True)
class RecordCorrespondence:
    record_id: str
    household_id: str
    population_unit_id: str
    dwelling_id: str
    site_id: str
    population: PopulationIdentity
    cell_id: str
    valid_from: str
    valid_until: str
    cardinality: str  # explicit MANY_TO_MANY preserves all separate identities
    coverage_semantics: str
    mapping_ref: str
    evidence_status: str
    truth_context: str
    snapshot: object = None


def correspondence_report(inputs, records, as_of):
    """Qualified dated many-to-many relations never calibrate estimated mass.

    DWELLING/HOUSEHOLD native IDs must equal their separately declared identity;
    this is a shared canonical namespace input convention, not proof of real
    identity. Differing namespaces need an upstream qualified crosswalk.
    BUILDING uses population_unit_id as the externally qualified building
    identity, independently of site or dwelling.
    """
    from modules.B01.capability_contract import CapabilitySnapshot
    from modules.B01.engine import assess_household_capabilities
    _date(as_of)
    if not isinstance(records, tuple):
        raise PopulationPlanningError("record correspondence must be an immutable tuple")
    candidates, exceptions, assessments = [], [], []
    seen, snapshot_versions = set(), {}
    for link in records:
        if not isinstance(link, RecordCorrespondence):
            raise PopulationPlanningError("record correspondence type required")
        for field in ("record_id", "household_id", "population_unit_id", "dwelling_id", "site_id",
                      "coverage_semantics", "mapping_ref"):
            _text(getattr(link, field), field)
        _date(link.valid_from); _date(link.valid_until)
        if link.valid_from >= link.valid_until:
            raise PopulationPlanningError("empty record membership period")
        if link.cardinality != "MANY_TO_MANY" or link.truth_context not in {"REAL", "SCN"}:
            raise PopulationPlanningError("explicit correspondence cardinality/context required")
        if link.evidence_status not in {"OBS", "DER", "SCN", "Q"}:
            raise PopulationPlanningError("invalid correspondence evidence status")
        if link.truth_context == "REAL" and link.evidence_status == "SCN":
            raise PopulationPlanningError("SCN correspondence cannot become an actual record")
        reason = None
        if link.population != inputs.population or link.cell_id not in {c.cell_id for c in inputs.cells}:
            reason = "REQUALIFICATION_REQUIRED"
        elif not link.valid_from <= as_of < link.valid_until:
            reason = "STALE_MEMBERSHIP"
        elif link.evidence_status == "Q":
            reason = "UNKNOWN_MAPPING"
        key = (link.record_id, link.household_id, link.population_unit_id, link.dwelling_id,
               link.site_id, link.cell_id, link.truth_context)
        if reason:
            exceptions.append((link.record_id, reason))
        elif key not in seen:
            candidates.append(link)
            seen.add(key)
        if link.population.native_unit == "DWELLING" and link.population_unit_id != link.dwelling_id:
            raise PopulationPlanningError("dwelling population-unit identity must match source-native dwelling")
        if link.population.native_unit == "HOUSEHOLD" and link.population_unit_id != link.household_id:
            raise PopulationPlanningError("household population-unit identity must match household")
        if link.snapshot is not None:
            snapshot = link.snapshot
            if not isinstance(snapshot, CapabilitySnapshot):
                raise PopulationPlanningError("population cell cannot substitute for CapabilitySnapshot")
            if (snapshot.identity.household_id, snapshot.identity.site_id, snapshot.identity.truth_context) != (
                    link.household_id, link.site_id, link.truth_context):
                raise PopulationPlanningError("snapshot record identity differs from correspondence")
            if snapshot.as_of != as_of:
                raise PopulationPlanningError("record snapshot date differs from report date")
            # Scope is validated by the unchanged public B01 entrypoint even if
            # the population link is unresolved. A bad link cannot fix a record.
            snapshot_key = (link.truth_context, link.record_id)
            digest = fingerprint(snapshot)
            if snapshot_key in snapshot_versions and snapshot_versions[snapshot_key] != digest:
                raise PopulationPlanningError("conflicting actual record snapshots")
            snapshot_versions[snapshot_key] = digest
            assessed = assess_household_capabilities(snapshot)
            if (link.record_id, assessed) not in assessments:
                assessments.append((link.record_id, assessed))
    qualified = []
    for link in candidates:
        conflict = any(other.truth_context == link.truth_context and (
            (other.record_id == link.record_id and (other.household_id, other.site_id) != (link.household_id, link.site_id)) or
            (other.population_unit_id == link.population_unit_id and other.cell_id != link.cell_id)
        ) for other in candidates)
        if conflict:
            exceptions.append((link.record_id, "AMBIGUOUS_MEMBERSHIP"))
        else:
            qualified.append(link)
    counts = {}
    for context, label in (("REAL", "actual"), ("SCN", "scenario")):
        links = [l for l in qualified if l.truth_context == context]
        counts[label] = {name: len({getattr(l, field) for l in links}) for name, field in (
            ("records", "record_id"), ("households", "household_id"), ("dwellings", "dwelling_id"),
            ("population_units", "population_unit_id"), ("sites", "site_id"))}
    return {"as_of": as_of, "counts": counts, "exceptions": tuple(exceptions),
            "record_assessments": tuple(assessments), "population_mass_adjustment": Fraction(),
            "actual_completed_from_planning": 0}


class PopulationPlanSession:
    """Offline owner/session ledger; no distributed lock, funding or permission."""

    def __init__(self, *, inputs: PlanningInputs, plan_id: str, version: str):
        _text(plan_id, "plan ID"); _text(version, "plan version")
        self._inputs = deepcopy(inputs)
        self._reconciliation = adapt_population_outputs(self._inputs)
        self._digest = fingerprint(self._inputs)
        self._plan_id, self._version = plan_id, version
        self._revision = 0
        self._attempts, self._events, self._children, self._history = {}, {}, set(), []
        self._schedule_allocations = []
        # These are fixed decisions, including infeasible requests, not posted
        # stock/resource reservations. Failed worlds cannot choose a fallback
        # alternative for the same selected source mass.
        self._selected_source_intervals = {}
        self._aliases = {name: lot.lot_id for lot in inputs.lots for name in (lot.lot_id, *lot.aliases)}
        self._options = {o.option_id: o for o in inputs.options}
        self._worlds = {}
        for world in inputs.worlds:
            mass = {v.lot_id: exact(v.represented_mass, unknown=True) for v in world.lots}
            lots = {l.lot_id: {"origin": l.origin_id, "cell": l.cell_id, "state": l.state_id,
                    "mass": mass[l.lot_id], "root_offset": Fraction(), "available_on": inputs.as_of,
                    "reservations": []} for l in inputs.lots}
            self._worlds[world.world_id] = {"lots": lots, "accepted": [], "resources": [],
                                           "eligible_used": {}, "outcomes": []}

    @property
    def revision(self):
        return self._revision

    @property
    def definition_digest(self):
        return self._digest

    def _validate_allocation(self, allocation):
        if not isinstance(allocation, Allocation):
            raise PopulationPlanningError("Allocation required")
        for field in ("allocation_id", "event_id", "source_lot_id", "child_lot_id", "provenance_ref"):
            _text(getattr(allocation, field), field)
        if allocation.planning_status != "PROPOSED":
            raise PopulationPlanningError("planning status cannot create observed implementation")
        if allocation.unit != self._inputs.population.native_unit:
            raise PopulationPlanningError("allocation native mass unit mismatch")
        if allocation.option_id not in self._options:
            raise PopulationPlanningError("unknown option; REQUALIFICATION_REQUIRED")
        if exact(allocation.mass) == 0:
            raise PopulationPlanningError("allocation mass must be positive; zero stock remains valid")
        exact(allocation.source_offset)
        _date(allocation.work_start); _date(allocation.effective_on)
        option = self._options[allocation.option_id]
        if not option.valid_from <= allocation.work_start <= allocation.effective_on < option.valid_until:
            raise PopulationPlanningError("allocation outside qualified option dates")
        windows = _unique(allocation.resource_windows, lambda x: x.resource_id, "resource window")
        if set(windows) != {r.resource_id for r in option.resources}:
            raise PopulationPlanningError("each requirement needs its own explicit resource window")
        for spec in option.resources:
            window = windows[spec.resource_id]
            _date(window.start)
            if not self._inputs.as_of <= window.start < self._inputs.horizon_until:
                raise PopulationPlanningError("resource date outside qualified horizon")
            if spec.kind == "FLOW":
                if window.end:
                    raise PopulationPlanningError("flow has an explicit due date, not an inferred interval")
            else:
                _date(window.end)
                if not window.start < window.end <= self._inputs.horizon_until:
                    raise PopulationPlanningError("occupancy requires an explicit half-open interval")

    def submit(self, schedule: FixedSchedule):
        if not isinstance(schedule, FixedSchedule):
            raise PopulationPlanningError("FixedSchedule required; no adaptive world-specific policies")
        if type(schedule.expected_revision) is not int or schedule.expected_revision != self._revision:
            raise PopulationPlanningError("STALE_REVISION")
        if (schedule.plan_id, schedule.version, schedule.definition_digest) != (self._plan_id, self._version, self._digest):
            raise PopulationPlanningError("definition/plan changed; REQUALIFICATION_REQUIRED")
        _text(schedule.order_ref, "explicit supplied allocation order")
        _unique(schedule.allocations, lambda a: a.allocation_id, "allocation")
        attempts, events, children = dict(self._attempts), dict(self._events), set(self._children)
        selected_intervals = deepcopy(self._selected_source_intervals)
        new = []
        # Whole-request structural preflight makes malformed batches atomic.
        for allocation in schedule.allocations:
            self._validate_allocation(allocation)
            digest = fingerprint(allocation)
            if allocation.allocation_id in attempts:
                if attempts[allocation.allocation_id] != digest:
                    raise PopulationPlanningError("changed allocation; REQUALIFICATION_REQUIRED")
                continue
            if allocation.event_id in events:
                raise PopulationPlanningError("duplicate allocation event alias")
            if allocation.child_lot_id in children or allocation.child_lot_id in self._aliases:
                raise PopulationPlanningError("duplicate child lot identity")
            if allocation.source_lot_id not in self._aliases and allocation.source_lot_id not in children:
                raise PopulationPlanningError("unknown source lot or undeclared predecessor order")
            source_id = self._aliases.get(allocation.source_lot_id, allocation.source_lot_id)
            start, end = exact(allocation.source_offset), exact(allocation.source_offset) + exact(allocation.mass)
            previous = selected_intervals.setdefault(source_id, [])
            if any(start < right and left < end for left, right in previous):
                raise PopulationPlanningError("FIXED_SCHEDULE_OVERLAP: alternative/retry requires requalification, not world-specific fallback")
            previous.append((start, end))
            attempts[allocation.allocation_id] = digest
            events[allocation.event_id] = allocation.allocation_id
            children.add(allocation.child_lot_id)
            new.append(allocation)
        if not new:
            return self.report()
        worlds = deepcopy(self._worlds)
        for world in self._inputs.worlds:
            ledger = worlds[world.world_id]
            values = {v.option_id: v for v in world.options}
            for allocation in new:
                option = self._options[allocation.option_id]
                value = values[allocation.option_id]
                source_id = self._aliases.get(allocation.source_lot_id, allocation.source_lot_id)
                source = ledger["lots"].get(source_id)
                quantity, offset = exact(allocation.mass), exact(allocation.source_offset)
                eligible = exact(value.eligible_mass, unknown=True)
                status = "ADMISSIBLE"
                if source is None:
                    status = "PREDECESSOR_NOT_ADMITTED"
                elif (source["cell"], source["state"]) != (option.cell_id, option.source_state):
                    status = "SOURCE_SCOPE_MISMATCH"
                elif source["available_on"] > allocation.work_start:
                    status = "PREDECESSOR_NOT_EFFECTIVE"
                elif any(offset < end and start < offset + quantity for start, end in source["reservations"]):
                    status = "ALREADY_RESERVED"
                elif source["mass"] is not None and offset + quantity > source["mass"]:
                    status = "OVERDRAW"
                elif eligible is not None and ledger["eligible_used"].get(option.option_id, Fraction()) + quantity > eligible:
                    status = "ELIGIBILITY_OVERDRAW"
                elif source["mass"] is None or eligible is None or value.eligible_origins is None:
                    status = "UNKNOWN"
                elif not _eligible_interval_covered(value.eligible_origins, source["origin"],
                        source["root_offset"] + offset, source["root_offset"] + offset + quantity):
                    status = "ELIGIBILITY_SCOPE_MISMATCH"
                coefficients = {v.resource_id: exact(v.per_unit_quantity, unknown=True) for v in value.coefficients}
                windows = {w.resource_id: w for w in allocation.resource_windows}
                demands = [{"allocation_id": allocation.allocation_id, "spec": r,
                            "quantity": None if coefficients[r.resource_id] is None else quantity * coefficients[r.resource_id],
                            "start": windows[r.resource_id].start, "end": windows[r.resource_id].end}
                           for r in option.resources]
                population_status = status
                checks = _envelope_checks(ledger["resources"] + demands, world.envelopes)
                coverage = _envelope_coverage(demands, world.envelopes)
                resource_status = ("FAIL" if any(c["status"] == "FAIL" for c in checks) else
                    "Q" if any(d["quantity"] is None for d in demands) or any(c["status"] == "Q" for c in checks) else
                    "REQUIREMENTS_KNOWN_CAPACITY_SCOPE_INCOMPLETE" if any(c["status"] != "COVERED" for c in coverage) else
                    "FIT_TO_DECLARED_ENVELOPES")
                if status == "ADMISSIBLE":
                    if any(c["status"] == "FAIL" for c in checks):
                        status = "RESOURCE_EXCESS"
                    elif any(d["quantity"] is None for d in demands) or any(c["status"] == "Q" for c in checks):
                        status = "UNKNOWN"
                ledger["outcomes"].append({"allocation_id": allocation.allocation_id, "status": status,
                    "requested_mass": quantity, "option_id": allocation.option_id,
                    "population_status": population_status, "resource_status": resource_status,
                    "eligible_mass": eligible, "eligible_origin_set_known": value.eligible_origins is not None,
                    "resource_envelope_coverage": coverage,
                    "effective_on": allocation.effective_on, "requested_resources": tuple(demands),
                    "trial_envelope_checks": checks, "actual_completion": False})
                if status != "ADMISSIBLE":
                    continue
                source["reservations"].append((offset, offset + quantity))
                ledger["lots"][allocation.child_lot_id] = {
                    "origin": source["origin"], "cell": source["cell"], "state": option.destination_state,
                    "mass": quantity, "root_offset": source["root_offset"] + offset,
                    "available_on": allocation.effective_on, "reservations": []}
                ledger["accepted"].append((allocation, source_id))
                ledger["resources"].extend(demands)
                ledger["eligible_used"][option.option_id] = ledger["eligible_used"].get(option.option_id, Fraction()) + quantity
        self._worlds, self._attempts, self._events, self._children = worlds, attempts, events, children
        self._revision += 1
        self._schedule_allocations.extend(new)
        self._selected_source_intervals = selected_intervals
        self._history.append({"revision": self._revision, "order_ref": schedule.order_ref,
                              "schedule_digest": fingerprint(schedule), "allocation_ids": tuple(a.allocation_id for a in new)})
        return self.report()

    def report(self, *, dates=(), records=(), record_as_of=None):
        if not isinstance(dates, tuple):
            raise PopulationPlanningError("report dates must be tuple")
        for day in dates:
            _date(day)
            if not self._inputs.as_of <= day < self._inputs.horizon_until:
                raise PopulationPlanningError("stock report date outside qualified horizon")
        result = {"plan_id": self._plan_id, "version": self._version, "revision": self._revision,
                  "definition_digest": self._digest, "population": self._inputs.population,
                  "target_scope_id": self._inputs.target_scope_id, "target_controls": self._inputs.target_controls,
                  "binding": self._inputs.binding, "control_reconciliation": self._reconciliation,
                  "calendar": {"timezone": self._inputs.timezone, "date_boundary": "EFFECTIVE_AT_START_OF_DATE_HALF_OPEN"},
                  "history": tuple(self._history), "fixed_schedule_allocations": tuple(self._schedule_allocations),
                  "worlds": [], "overall_policy_verdict": None,
                  "permission_or_observation_created": False}
        for world in self._inputs.worlds:
            ledger = self._worlds[world.world_id]
            requested_dates = sorted(set(dates or (self._inputs.as_of, *(a.effective_on for a, _ in ledger["accepted"])) ))
            snapshots = tuple(_stock_at(self._inputs, ledger, day) for day in requested_dates)
            origins = {}
            for allocation, source_id in ledger["accepted"]:
                source = ledger["lots"][source_id]
                start = source["root_offset"] + exact(allocation.source_offset)
                origins.setdefault(source["origin"], []).append((start, start + exact(allocation.mass)))
            requested_demands = [d for outcome in ledger["outcomes"] for d in outcome["requested_resources"]]
            result["worlds"].append({"world_id": world.world_id,
                "joint_uncertainty_id": world.joint_uncertainty_id, "probability": exact(world.probability, unknown=True),
                "schedule_status": "ADMISSIBLE" if all(o["status"] == "ADMISSIBLE" for o in ledger["outcomes"]) else "NOT_FULLY_ADMISSIBLE",
                "outcomes": tuple(ledger["outcomes"]), "dated_stock": snapshots,
                "transition_throughput": sum((exact(a.mass) for a, _ in ledger["accepted"]), Fraction()),
                "unique_origin_planning_mass": sum((_union_length(v) for v in origins.values()), Fraction()),
                "origin_intervals": origins, "unit": self._inputs.population.native_unit,
                "resources": _resource_report(ledger["resources"]),
                "fixed_schedule_requirements": _resource_report(requested_demands),
                "fixed_schedule_envelope_checks": _envelope_checks(requested_demands, world.envelopes),
                "fixed_schedule_envelope_coverage": _envelope_coverage(requested_demands, world.envelopes),
                "envelope_checks": _envelope_checks(ledger["resources"], world.envelopes),
                "envelope_coverage": _envelope_coverage(ledger["resources"], world.envelopes),
                "capacity_claim": "FIT_ONLY_TO_EXPLICIT_ENVELOPES_NO_ACTUAL_CAPACITY_OR_FUNDING",
                "actual_household_completions": 0})
        result["worlds"] = tuple(result["worlds"])
        result["correspondence"] = correspondence_report(self._inputs, records, record_as_of or self._inputs.as_of)
        # Returning independent reports prevents caller mutation from altering the ledger.
        return deepcopy(result)


def _eligible_interval_covered(intervals, origin_id, start, end):
    reached = start
    for left, right in sorted((exact(i.start), exact(i.end)) for i in intervals if i.origin_id == origin_id):
        if right <= reached:
            continue
        if left > reached:
            return False
        reached = right
        if reached >= end:
            return True
    return False


def _union_length(intervals):
    total, end = Fraction(), None
    for start, stop in sorted(intervals):
        if end is None or start > end:
            total += stop - start
        elif stop > end:
            total += stop - end
        end = max(end, stop) if end is not None else stop
    return total


def _stock_at(inputs, ledger, day):
    masses = {l.lot_id: ledger["lots"][l.lot_id]["mass"] for l in inputs.lots}
    initial_known = sum((v for v in masses.values() if v is not None), Fraction())
    initial_total = None if any(v is None for v in masses.values()) else initial_known
    for allocation, source_id in ledger["accepted"]:
        if allocation.effective_on <= day:
            masses[source_id] -= exact(allocation.mass)
            masses[allocation.child_lot_id] = exact(allocation.mass)
    states = {(cell.cell_id, state): Fraction() for cell in inputs.cells for state in inputs.states}
    reserved = {key: Fraction() for key in states}
    for lot_id, mass in masses.items():
        lot = ledger["lots"][lot_id]
        key = (lot["cell"], lot["state"])
        states[key] = None if mass is None or states[key] is None else states[key] + mass
    for allocation, source_id in ledger["accepted"]:
        if source_id in masses and day < allocation.effective_on:
            source = ledger["lots"][source_id]
            reserved[(source["cell"], source["state"])] += exact(allocation.mass)
    total = None if any(v is None for v in masses.values()) else sum(masses.values(), Fraction())
    return {"as_of": day, "state_mass": states, "reserved_in_source": reserved,
            "lot_mass": masses, "total_mass": total, "known_initial_mass": initial_known,
            "conservation_residual": None if total is None else total - initial_total,
            "status": "Q" if total is None else "PROPOSED_POPULATION_STOCK"}


def _resource_report(demands):
    grouped = {}
    for demand in demands:
        grouped.setdefault(_resource_key(demand["spec"]), []).append(demand)
    result = []
    for key, values in grouped.items():
        annual, segments = {}, []
        if key[0] == "FLOW":
            for item in values:
                year = _date(item["start"]).year
                previous = annual.get(year, Fraction())
                annual[year] = None if previous is None or item["quantity"] is None else previous + item["quantity"]
            peak = None
        else:
            points = sorted({item["start"] for item in values} | {item["end"] for item in values})
            for start, end in zip(points, points[1:]):
                active = [v for v in values if v["start"] <= start < v["end"]]
                known = sum((v["quantity"] for v in active if v["quantity"] is not None), Fraction())
                quantity = None if any(v["quantity"] is None for v in active) else known
                segments.append({"start": start, "end": end, "quantity": quantity, "known_lower_bound": known})
            peak = None if any(s["quantity"] is None for s in segments) else max((s["quantity"] for s in segments), default=Fraction())
        result.append({"resource_key": key, "annual_flows": annual, "occupancy_segments": tuple(segments),
                       "concurrent_peak": peak, "events": tuple(values)})
    return tuple(result)


def _envelope_coverage(demands, envelopes):
    """Optional envelope gaps remain visible; absent capacity is not infinity."""
    result = []
    for demand in demands:
        matching = [e for e in envelopes if _resource_key(e.spec) == _resource_key(demand["spec"])]
        if demand["spec"].kind == "FLOW":
            covered = any(e.valid_from <= demand["start"] < e.valid_until for e in matching)
        else:
            spans = sorted((max(e.valid_from, demand["start"]), min(e.valid_until, demand["end"]))
                           for e in matching if e.valid_from < demand["end"] and demand["start"] < e.valid_until)
            reached = demand["start"]
            for start, end in spans:
                if start > reached:
                    break
                reached = max(reached, end)
            covered = reached >= demand["end"]
        result.append({"allocation_id": demand["allocation_id"], "resource_id": demand["spec"].resource_id,
                       "status": "COVERED" if covered else "Q_UNCOVERED_RESOURCE_DATES"})
    return tuple(result)


def _envelope_checks(demands, envelopes):
    results = []
    for envelope in envelopes:
        values = [d for d in demands if _resource_key(d["spec"]) == _resource_key(envelope.spec)]
        if envelope.spec.kind == "FLOW":
            values = [d for d in values if envelope.valid_from <= d["start"] < envelope.valid_until]
        else:
            values = [dict(d, start=max(d["start"], envelope.valid_from), end=min(d["end"], envelope.valid_until))
                      for d in values if d["start"] < envelope.valid_until and envelope.valid_from < d["end"]]
        # Fit is only to this explicitly declared interval; uncovered dates are
        # reported separately, never interpreted as unlimited actual capacity.
        unknown = any(v["quantity"] is None for v in values)
        if envelope.spec.kind == "FLOW":
            known = sum((v["quantity"] for v in values if v["quantity"] is not None), Fraction())
        else:
            report = _resource_report(values)
            known = max((s["known_lower_bound"] for r in report for s in r["occupancy_segments"]), default=Fraction())
        ceiling = exact(envelope.ceiling, unknown=True)
        if not values:
            status, fit_basis = "NOT_APPLICABLE", "NO_MATCHING_RESOURCE_DATE_DEMAND"
        elif ceiling is not None and known > ceiling:
            status, fit_basis = "FAIL", "KNOWN_EXCESS"
        elif not unknown and known == 0:
            # Capacities are nonnegative in this contract. This establishes a
            # zero-demand fit without estimating or changing the Q ceiling.
            status, fit_basis = "PASS", "KNOWN_ZERO_DEMAND_NONNEGATIVE_CAPACITY_DOMAIN"
        elif unknown or ceiling is None:
            status, fit_basis = "Q", "APPLICABLE_DEMAND_OR_CAPACITY_UNKNOWN"
        else:
            status, fit_basis = "PASS", "KNOWN_DEMAND_WITHIN_KNOWN_CAPACITY"
        results.append({"envelope_id": envelope.envelope_id, "resource_key": _resource_key(envelope.spec),
                        "valid_from": envelope.valid_from, "valid_until": envelope.valid_until,
                        "status": status, "applicable": bool(values), "fit_basis": fit_basis,
                        "used_or_peak": None if unknown else known, "known_lower_bound": known,
                        "ceiling": ceiling, "evidence_ref": envelope.evidence_ref})
    return tuple(results)


def p84_source_demo():
    """Read existing P84 controls and Q bounds, without creating planning shares."""
    from modules.B02.terminal_eligibility_population_inference import (
        DEFAULT_WBL, build_population_controls, current_repository_envelope,
    )
    controls = build_population_controls()
    envelope = current_repository_envelope()
    return {"mode": "CONTROL", "control_count": len(controls), "controls": controls,
            "represented_mass": sum(c.dwelling_count for c in controls), "native_unit": "DWELLING",
            "population": "2022 occupied non-district-heated dwellings", "reference_date": "2022-10-01",
            "source_id": "SRC-B02-KSH-CENSUS-API-2022", "artifact_sha256": sha256(DEFAULT_WBL.read_bytes()).hexdigest(),
            "terminal_eligibility": envelope, "planning_state_distribution": None,
            "intervention_eligible_mass": None, "record_permissions": None,
            "planning_adapter_status": "Q_STATE_ELIGIBILITY_RESOURCES_JOINT_UNCERTAINTY_NOT_SUPPLIED"}


def load_population_contract():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract["contract_id"] != "B01-POPULATION-PLANNING-BRIDGE" or contract["schema_version"] != "1.0.0":
        raise PopulationPlanningError("unknown population planning contract")
    if contract["numeric_defaults"] or contract["original_task_acceptance_changed"]:
        raise PopulationPlanningError("population bridge cannot supply defaults or accept original tasks")
    return contract
