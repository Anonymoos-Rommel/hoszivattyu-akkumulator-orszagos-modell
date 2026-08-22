"""Evidence-aware physical retrofit and demand-reduction engine.

B06 consumes explicit baseline and intervention evidence. It does not
reconstruct buildings from floor area, construction year and fuel use, and it
does not contain tariffs, CAPEX, subsidy or financing logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, TypeVar


EVIDENCE_STATUSES = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}
T = TypeVar("T")


class RetrofitInputError(ValueError):
    """Raised when a supplied B06 physical input violates the contract."""


@dataclass(frozen=True)
class EvidenceValue(Generic[T]):
    value: T | None
    status: str = "Q"
    source_ids: tuple[str, ...] = ()

    def validate(self, name: str) -> None:
        if self.status not in EVIDENCE_STATUSES:
            raise RetrofitInputError(f"invalid evidence status for {name}: {self.status!r}")
        if self.status in {"OBS", "DER"} and self.value is None:
            raise RetrofitInputError(f"{name} cannot be empty for {self.status} evidence")


@dataclass(frozen=True)
class RetrofitBaseline:
    archetype_id: EvidenceValue[str]
    baseline_annual_space_heat_kwh: EvidenceValue[float]
    baseline_peak_heat_load_kw: EvidenceValue[float]
    baseline_state_id: str = "S0"
    floor_area_m2: EvidenceValue[float] = EvidenceValue(None, "Q")
    heated_floor_area_m2: EvidenceValue[float] = EvidenceValue(None, "Q")
    building_type: EvidenceValue[str] = EvidenceValue(None, "Q")
    construction_period: EvidenceValue[str] = EvidenceValue(None, "Q")
    wall_type: EvidenceValue[str] = EvidenceValue(None, "Q")
    roof_type: EvidenceValue[str] = EvidenceValue(None, "Q")
    floor_type: EvidenceValue[str] = EvidenceValue(None, "Q")
    window_type: EvidenceValue[str] = EvidenceValue(None, "Q")
    required_supply_temperature_before_c: EvidenceValue[float] = EvidenceValue(None, "Q")
    dhw_annual_kwh: EvidenceValue[float] = EvidenceValue(None, "Q")
    dhw_peak_heat_load_kw: EvidenceValue[float] = EvidenceValue(None, "Q")


@dataclass(frozen=True)
class RetrofitIntervention:
    intervention_id: str
    family: str
    annual_reduction_fraction: float | None
    peak_reduction_fraction: float | None
    evidence_status: str = "Q"
    applicability_status: str = "Q"
    completion_status: str = "Q"
    supply_temperature_after_c: float | None = None
    source_ids: tuple[str, ...] = ()
    completion_source_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        for name, status in (
            ("evidence_status", self.evidence_status),
            ("applicability_status", self.applicability_status),
            ("completion_status", self.completion_status),
        ):
            if status not in EVIDENCE_STATUSES:
                raise RetrofitInputError(f"invalid {name}: {status!r}")
        for name, value in (
            ("annual_reduction_fraction", self.annual_reduction_fraction),
            ("peak_reduction_fraction", self.peak_reduction_fraction),
        ):
            if value is not None and not 0 <= value <= 1:
                raise RetrofitInputError(f"{name} must be between 0 and 1")
        if self.supply_temperature_after_c is not None and self.supply_temperature_after_c <= 0:
            raise RetrofitInputError("supply temperature must be positive")


@dataclass(frozen=True)
class B05DemandHandoff:
    """Design-point handoff; hourly profile expansion remains a separate input."""

    space_heating_required_kw: float | None
    dhw_required_kw: float | None
    required_supply_temperature_c: float | None
    status: str
    notes: str


@dataclass(frozen=True)
class RetrofitResult:
    status: str
    baseline_annual_space_heat_kwh: float | None
    post_retrofit_annual_space_heat_kwh: float | None
    baseline_peak_heat_load_kw: float | None
    post_retrofit_peak_heat_load_kw: float | None
    annual_heat_reduction_kwh: float | None
    annual_heat_reduction_pct: float | None
    peak_heat_reduction_kw: float | None
    peak_heat_reduction_pct: float | None
    required_supply_temperature_before_c: float | None
    required_supply_temperature_after_c: float | None
    dhw_annual_kwh: float | None
    dhw_peak_heat_load_kw: float | None
    retrofit_applicability_status: str
    remaining_readiness_gaps: tuple[str, ...]
    post_state_candidate: str
    s1_gate: str
    b05_handoff: B05DemandHandoff
    applied_intervention_ids: tuple[str, ...]


def _status_for(values: Iterable[str]) -> str:
    statuses = tuple(values)
    if "Q" in statuses:
        return "Q"
    if "SCN" in statuses:
        return "SCN"
    if "ASS" in statuses:
        return "ASS"
    if "POL" in statuses:
        return "POL"
    return "DER"


def _empty_result(status: str, gaps: tuple[str, ...], baseline: RetrofitBaseline) -> RetrofitResult:
    return RetrofitResult(
        status,
        baseline.baseline_annual_space_heat_kwh.value,
        None,
        baseline.baseline_peak_heat_load_kw.value,
        None,
        None,
        None,
        None,
        None,
        baseline.required_supply_temperature_before_c.value,
        None,
        baseline.dhw_annual_kwh.value,
        baseline.dhw_peak_heat_load_kw.value,
        "Q",
        gaps,
        "S0_BASELINE_AUDITED",
        "BLOCKED",
        B05DemandHandoff(None, None, None, "Q", "B06 evidence is incomplete; no B05 sizing input is emitted."),
        (),
    )


def evaluate_retrofit(baseline: RetrofitBaseline, interventions: Iterable[RetrofitIntervention]) -> RetrofitResult:
    """Apply explicit annual and peak factors sequentially without double counting."""

    baseline.archetype_id.validate("archetype_id")
    baseline.baseline_annual_space_heat_kwh.validate("baseline_annual_space_heat_kwh")
    baseline.baseline_peak_heat_load_kw.validate("baseline_peak_heat_load_kw")
    baseline.required_supply_temperature_before_c.validate("required_supply_temperature_before_c")
    baseline.dhw_annual_kwh.validate("dhw_annual_kwh")
    baseline.dhw_peak_heat_load_kw.validate("dhw_peak_heat_load_kw")
    if baseline.baseline_state_id != "S0":
        raise RetrofitInputError("B06-P1 requires an S0 baseline input")
    baseline_annual = baseline.baseline_annual_space_heat_kwh.value
    baseline_peak = baseline.baseline_peak_heat_load_kw.value
    if baseline_annual is None or baseline_peak is None:
        return _empty_result("Q", ("baseline annual and peak space-heating demand are required",), baseline)
    if baseline_annual < 0 or baseline_peak < 0:
        raise RetrofitInputError("baseline demand cannot be negative")

    rows = tuple(interventions)
    for intervention in rows:
        intervention.validate()
    if not rows:
        before_supply = baseline.required_supply_temperature_before_c.value
        handoff_status = _status_for((baseline.baseline_peak_heat_load_kw.status, baseline.required_supply_temperature_before_c.status))
        handoff = B05DemandHandoff(
            baseline_peak,
            baseline.dhw_peak_heat_load_kw.value,
            before_supply,
            handoff_status if before_supply is not None else "Q",
            "No retrofit was applied; this is an S0 design-point handoff, not S1 promotion.",
        )
        return RetrofitResult(
            "Q" if before_supply is None else handoff.status,
            baseline_annual,
            baseline_annual,
            baseline_peak,
            baseline_peak,
            0.0,
            0.0,
            0.0,
            0.0,
            before_supply,
            before_supply,
            baseline.dhw_annual_kwh.value,
            baseline.dhw_peak_heat_load_kw.value,
            "Q",
            ("no completed demand-reduction intervention",),
            "S0_BASELINE_AUDITED",
            "BLOCKED",
            handoff,
            (),
        )

    current_annual, current_peak = baseline_annual, baseline_peak
    current_supply = baseline.required_supply_temperature_before_c.value
    evidence_statuses = [baseline.baseline_annual_space_heat_kwh.status, baseline.baseline_peak_heat_load_kw.status]
    gaps: list[str] = []
    for intervention in rows:
        evidence_statuses.extend((intervention.evidence_status, intervention.applicability_status))
        if intervention.evidence_status == "Q":
            gaps.append(f"{intervention.intervention_id}: effect evidence is Q")
        if intervention.applicability_status == "Q":
            gaps.append(f"{intervention.intervention_id}: applicability is Q")
        if intervention.annual_reduction_fraction is None or intervention.peak_reduction_fraction is None:
            gaps.append(f"{intervention.intervention_id}: annual and peak effects must both be explicit")
            continue
        current_annual *= 1 - intervention.annual_reduction_fraction
        current_peak *= 1 - intervention.peak_reduction_fraction
        if intervention.supply_temperature_after_c is not None:
            current_supply = intervention.supply_temperature_after_c

    if gaps:
        return _empty_result("Q", tuple(gaps), baseline)

    annual_reduction = baseline_annual - current_annual
    peak_reduction = baseline_peak - current_peak
    completion_ready = all(
        intervention.completion_status == "OBS" and intervention.completion_source_ids
        for intervention in rows
    )
    applicability_status = _status_for(intervention.applicability_status for intervention in rows)
    result_status = _status_for(evidence_statuses)
    s1_gate = "READY" if completion_ready else "BLOCKED"
    post_state = "S1_DEMAND_REDUCED" if completion_ready else "S1_CANDIDATE"
    handoff_status = result_status if current_supply is not None else "Q"
    handoff = B05DemandHandoff(
        current_peak if current_supply is not None else None,
        baseline.dhw_peak_heat_load_kw.value if current_supply is not None else None,
        current_supply,
        handoff_status,
        "Design-point bridge to B05; hourly demand profile remains a separate upstream contract.",
    )
    return RetrofitResult(
        result_status,
        baseline_annual,
        current_annual,
        baseline_peak,
        current_peak,
        annual_reduction,
        annual_reduction / baseline_annual if baseline_annual else 0.0,
        peak_reduction,
        peak_reduction / baseline_peak if baseline_peak else 0.0,
        baseline.required_supply_temperature_before_c.value,
        current_supply,
        baseline.dhw_annual_kwh.value,
        baseline.dhw_peak_heat_load_kw.value,
        applicability_status,
        tuple(gaps),
        post_state,
        s1_gate,
        handoff,
        tuple(intervention.intervention_id for intervention in rows),
    )
