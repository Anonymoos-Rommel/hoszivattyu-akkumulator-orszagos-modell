"""Evidence-aware physical retrofit and demand-reduction engine.

B06 consumes explicit baseline and intervention evidence. It does not
reconstruct buildings from floor area, construction year and fuel use, and it
does not contain tariffs, CAPEX, subsidy or financing logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, TypeVar

from modules.B06.s1_demand_outcome_gate import (
    READY as S1_OUTCOME_READY,
    S1DemandOutcomeEvidence,
    assess_s1_demand_outcome,
)
from modules.B06.baseline_demand_gate import (
    QUALIFIED as BASELINE_PAIR_QUALIFIED,
    BaselineDemandEvidence,
    assess_baseline_demand,
)
from modules.B06.peak_effect_gate import (
    QUALIFIED as PEAK_EFFECT_QUALIFIED,
    PeakEffectEvidence,
    assess_peak_effect,
)
from modules.B06.effect_surface import (
    QUALIFIED as EFFECT_SURFACE_QUALIFIED,
    EffectSurfaceEvidence,
    assess_effect_surface,
    calculate_state_demand,
)
from modules.B06.realized_completion_gate import (
    QUALIFIED as REALIZED_COMPLETION_QUALIFIED,
    RealizedCompletionEvidence,
    assess_realized_completion,
)


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
    baseline_demand_evidence: BaselineDemandEvidence | None = None


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
    completion_outcome: S1DemandOutcomeEvidence | None = None
    realized_completion: RealizedCompletionEvidence | None = None
    peak_effect_evidence: PeakEffectEvidence | None = None
    effect_surface_evidence: EffectSurfaceEvidence | None = None

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

    real_baseline_statuses = {"OBS", "DER"}
    uses_real_baseline = (
        baseline.baseline_annual_space_heat_kwh.status in real_baseline_statuses
        or baseline.baseline_peak_heat_load_kw.status in real_baseline_statuses
    )
    if uses_real_baseline:
        if baseline.baseline_demand_evidence is None:
            return _empty_result(
                "Q",
                ("P61 same-record/same-phase baseline demand evidence is required for OBS/DER annual or peak inputs",),
                baseline,
            )
        pair_decision = assess_baseline_demand(baseline.baseline_demand_evidence)
        if pair_decision.status != BASELINE_PAIR_QUALIFIED:
            return _empty_result(
                "Q",
                tuple(f"P61 baseline pair: {reason}" for reason in pair_decision.reasons),
                baseline,
            )
        pair = baseline.baseline_demand_evidence
        if abs(pair.annual_space_heat_kwh - baseline_annual) > 0.05:
            return _empty_result(
                "Q",
                ("P61 annual baseline value does not match admitted pair",),
                baseline,
            )
        if abs(pair.peak_heat_load_kw - baseline_peak) > 0.001:
            return _empty_result(
                "Q",
                ("P61 peak baseline value does not match admitted pair",),
                baseline,
            )

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
    claimed_surface_keys: set[str] = set()
    for intervention in rows:
        evidence_statuses.extend((intervention.evidence_status, intervention.applicability_status))
        if intervention.evidence_status == "Q":
            gaps.append(f"{intervention.intervention_id}: effect evidence is Q")
        if intervention.applicability_status == "Q":
            gaps.append(f"{intervention.intervention_id}: applicability is Q")
        if intervention.annual_reduction_fraction is None or intervention.peak_reduction_fraction is None:
            gaps.append(f"{intervention.intervention_id}: annual and peak effects must both be explicit")
            continue

        if intervention.evidence_status in {"OBS", "DER"}:
            authorities = (
                intervention.peak_effect_evidence is not None,
                intervention.effect_surface_evidence is not None,
            )
            if sum(authorities) == 0:
                gaps.append(
                    f"{intervention.intervention_id}: P62 linked pair or P63 physical surface evidence is required for OBS/DER intervention effects"
                )
                continue
            if sum(authorities) > 1:
                gaps.append(
                    f"{intervention.intervention_id}: MULTIPLE_EFFECT_AUTHORITIES"
                )
                continue

            if intervention.peak_effect_evidence is not None:
                effect_decision = assess_peak_effect(intervention.peak_effect_evidence)
                if effect_decision.status != PEAK_EFFECT_QUALIFIED:
                    gaps.extend(
                        f"{intervention.intervention_id}: P62 peak effect {reason}"
                        for reason in effect_decision.reasons
                    )
                    continue
                effect = intervention.peak_effect_evidence
                if effect.intervention_id != intervention.intervention_id:
                    gaps.append(
                        f"{intervention.intervention_id}: P62 intervention link mismatched"
                    )
                    continue
                if effect.evidence_status != intervention.evidence_status:
                    gaps.append(
                        f"{intervention.intervention_id}: P62 evidence status mismatched"
                    )
                    continue
                if (
                    baseline.baseline_demand_evidence is not None
                    and effect.record_id != baseline.baseline_demand_evidence.record_id
                ):
                    gaps.append(
                        f"{intervention.intervention_id}: P62 record does not match admitted baseline"
                    )
                    continue
                if effect_decision.annual_reduction_fraction is None or effect_decision.peak_reduction_fraction is None:
                    gaps.append(
                        f"{intervention.intervention_id}: P62 reduction fractions missing"
                    )
                    continue
                if abs(effect_decision.annual_reduction_fraction - intervention.annual_reduction_fraction) > 1e-9:
                    gaps.append(
                        f"{intervention.intervention_id}: annual reduction fraction does not match P62 evidence"
                    )
                    continue
                if abs(effect_decision.peak_reduction_fraction - intervention.peak_reduction_fraction) > 1e-9:
                    gaps.append(
                        f"{intervention.intervention_id}: peak reduction fraction does not match P62 evidence"
                    )
                    continue

            if intervention.effect_surface_evidence is not None:
                if intervention.evidence_status != "DER":
                    gaps.append(
                        f"{intervention.intervention_id}: P63 physical surface authority is DER"
                    )
                    continue
                surface = intervention.effect_surface_evidence
                surface_decision = assess_effect_surface(surface)
                if surface_decision.status != EFFECT_SURFACE_QUALIFIED:
                    gaps.extend(
                        f"{intervention.intervention_id}: P63 effect surface {reason}"
                        for reason in surface_decision.reasons
                    )
                    continue
                if surface.intervention_id != intervention.intervention_id:
                    gaps.append(
                        f"{intervention.intervention_id}: P63 intervention link mismatched"
                    )
                    continue
                if (
                    baseline.baseline_demand_evidence is not None
                    and surface.before.record_id != baseline.baseline_demand_evidence.record_id
                ):
                    gaps.append(
                        f"{intervention.intervention_id}: P63 record does not match admitted baseline"
                    )
                    continue
                surface_before = calculate_state_demand(surface.before)
                if (
                    surface_before.annual_space_heat_kwh is None
                    or surface_before.design_peak_heat_kw is None
                ):
                    gaps.append(
                        f"{intervention.intervention_id}: P63 before-state demand is not reproducible"
                    )
                    continue
                if abs(surface_before.annual_space_heat_kwh - current_annual) > 0.05:
                    gaps.append(
                        f"{intervention.intervention_id}: P63 before annual demand does not match current sequential state"
                    )
                    continue
                if abs(surface_before.design_peak_heat_kw - current_peak) > 0.001:
                    gaps.append(
                        f"{intervention.intervention_id}: P63 before peak demand does not match current sequential state"
                    )
                    continue
                if surface_decision.annual_reduction_fraction is None or surface_decision.peak_reduction_fraction is None:
                    gaps.append(
                        f"{intervention.intervention_id}: P63 reduction fractions missing"
                    )
                    continue
                if abs(surface_decision.annual_reduction_fraction - intervention.annual_reduction_fraction) > 1e-9:
                    gaps.append(
                        f"{intervention.intervention_id}: annual reduction fraction does not match P63 surface"
                    )
                    continue
                if abs(surface_decision.peak_reduction_fraction - intervention.peak_reduction_fraction) > 1e-9:
                    gaps.append(
                        f"{intervention.intervention_id}: peak reduction fraction does not match P63 surface"
                    )
                    continue
                surface_keys = set(surface_decision.claimed_parameter_keys)
                overlap = claimed_surface_keys & surface_keys
                if overlap:
                    gaps.append(
                        f"{intervention.intervention_id}: P63 overlapping physical effect keys: "
                        + ",".join(sorted(overlap))
                    )
                    continue
                claimed_surface_keys.update(surface_keys)

        current_annual *= 1 - intervention.annual_reduction_fraction
        current_peak *= 1 - intervention.peak_reduction_fraction
        if intervention.supply_temperature_after_c is not None:
            current_supply = intervention.supply_temperature_after_c

    if gaps:
        return _empty_result("Q", tuple(gaps), baseline)

    annual_reduction = baseline_annual - current_annual
    peak_reduction = baseline_peak - current_peak
    completion_decisions = []
    completion_gaps: list[str] = []
    for intervention in rows:
        if intervention.realized_completion is None:
            completion_decisions.append(None)
            completion_gaps.append(
                f"{intervention.intervention_id}: P64 realized completion evidence is missing"
            )
            continue
        realized = assess_realized_completion(intervention.realized_completion)
        completion_decisions.append(realized)
        if realized.status != REALIZED_COMPLETION_QUALIFIED:
            completion_gaps.append(
                f"{intervention.intervention_id}: realized completion {realized.status} "
                + ",".join(realized.reasons)
            )
            continue
        if intervention.realized_completion.intervention_id != intervention.intervention_id:
            completion_gaps.append(
                f"{intervention.intervention_id}: realized completion intervention link mismatched"
            )
            continue
        if intervention.completion_status != realized.evidence_status:
            completion_gaps.append(
                f"{intervention.intervention_id}: completion status does not match realized completion evidence"
            )
            continue
        if not intervention.completion_source_ids:
            completion_gaps.append(
                f"{intervention.intervention_id}: completion source IDs are missing"
            )
            continue

        if intervention.completion_outcome is None:
            completion_gaps.append(
                f"{intervention.intervention_id}: linked S1 demand outcome is missing"
            )
            continue
        if intervention.completion_outcome.intervention_id != intervention.intervention_id:
            completion_gaps.append(
                f"{intervention.intervention_id}: completion outcome intervention link mismatched"
            )
            continue
        if intervention.completion_outcome.record_id != intervention.realized_completion.record_id:
            completion_gaps.append(
                f"{intervention.intervention_id}: completion outcome record does not match realized completion"
            )
            continue
        outcome = assess_s1_demand_outcome(intervention.completion_outcome)
        if outcome.status != S1_OUTCOME_READY:
            completion_gaps.append(
                f"{intervention.intervention_id}: S1 outcome {outcome.status} "
                + ",".join(outcome.reasons)
            )
            continue

    completion_ready = not completion_gaps and len(completion_decisions) == len(rows)
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
        tuple(gaps + completion_gaps),
        post_state,
        s1_gate,
        handoff,
        tuple(intervention.intervention_id for intervention in rows),
    )
