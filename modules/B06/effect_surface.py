"""B06-P63 transferable physical retrofit effect surface.

The surface is parameteric, not a lookup percentage. Annual net space-heating
demand is recalculated for before/after states using the current Hungarian
monthly heat-balance semantics, while design peak is recalculated independently
from an explicit design heat-loss coefficient.

BUILDING TYPE != EFFECT FACTOR
ANNUAL EFFECT != PEAK EFFECT
TABULA EXAMPLE != HOUSEHOLD OBSERVATION
SAME SERVICE + SAME CLIMATE + EXPLICIT PHYSICAL STATE = TRANSFERABLE DER
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
DER = "DER"
QUALIFIED = "QUALIFIED"

ALLOWED_BUILDING_TYPES = frozenset(
    {"SINGLE_FAMILY_HOUSE", "MULTI_FAMILY_HOUSE", "APARTMENT_BLOCK"}
)

CHANGE_KEYS = frozenset(
    {
        "TRANSMISSION",
        "GROUND_TRANSMISSION",
        "VENTILATION",
        "SOLAR_GAIN",
        "THERMAL_DYNAMICS",
    }
)


@dataclass(frozen=True)
class MonthlyHeatBalanceInput:
    month: int
    hours: float
    external_temperature_c: float
    annual_external_temperature_c: float
    direct_unconditioned_h_w_per_k: float
    ground_h_w_per_k: float
    ventilation_h_w_per_k: float
    solar_gain_kwh: float
    internal_gain_kwh: float
    gain_utilization_factor: float
    intermittent_operation_factor: float = 1.0


@dataclass(frozen=True)
class PhysicalState:
    record_id: str
    building_type: str
    construction_period: str
    state_id: str
    climate_id: str
    heated_floor_area_m2: float
    heated_volume_m3: float
    indoor_temperature_c: float
    design_outdoor_temperature_c: float
    design_total_h_w_per_k: float
    months: tuple[MonthlyHeatBalanceInput, ...]
    source_refs: tuple[str, ...]
    evidence_status: str = DER


@dataclass(frozen=True)
class EffectSurfaceDomain:
    domain_id: str
    allowed_building_types: tuple[str, ...]
    allowed_construction_periods: tuple[str, ...]
    allowed_before_states: tuple[str, ...]
    allowed_after_states: tuple[str, ...]
    source_refs: tuple[str, ...]
    national_prevalence_claim: bool = False


@dataclass(frozen=True)
class EffectSurfaceEvidence:
    intervention_id: str
    before: PhysicalState
    after: PhysicalState
    domain: EffectSurfaceDomain
    changed_parameter_keys: tuple[str, ...]
    applicability_source_refs: tuple[str, ...]
    reproducible_repository_binding: bool = False


@dataclass(frozen=True)
class StateDemandResult:
    annual_space_heat_kwh: float | None
    design_peak_heat_kw: float | None
    gaps: tuple[str, ...]


@dataclass(frozen=True)
class EffectSurfaceDecision:
    status: str
    annual_reduction_fraction: float | None
    peak_reduction_fraction: float | None
    claimed_parameter_keys: tuple[str, ...]
    reasons: tuple[str, ...]


def _positive(value: float) -> bool:
    return isfinite(value) and value > 0


def _refs_ok(refs: tuple[str, ...]) -> bool:
    return bool(refs) and all(isinstance(ref, str) and ref.strip() for ref in refs)


def _state_gaps(state: PhysicalState) -> list[str]:
    gaps: list[str] = []
    if not state.record_id.strip():
        gaps.append("RECORD_ID_MISSING")
    if state.building_type not in ALLOWED_BUILDING_TYPES:
        gaps.append("BUILDING_TYPE_UNSUPPORTED")
    if not state.construction_period.strip():
        gaps.append("CONSTRUCTION_PERIOD_MISSING")
    if not state.state_id.strip():
        gaps.append("STATE_ID_MISSING")
    if not state.climate_id.strip():
        gaps.append("CLIMATE_ID_MISSING")
    if state.evidence_status != DER:
        gaps.append("PHYSICAL_STATE_MUST_BE_DER")
    if not _positive(state.heated_floor_area_m2):
        gaps.append("HEATED_FLOOR_AREA_INVALID")
    if not _positive(state.heated_volume_m3):
        gaps.append("HEATED_VOLUME_INVALID")
    if not isfinite(state.indoor_temperature_c):
        gaps.append("INDOOR_TEMPERATURE_INVALID")
    if not isfinite(state.design_outdoor_temperature_c):
        gaps.append("DESIGN_OUTDOOR_TEMPERATURE_INVALID")
    elif state.indoor_temperature_c <= state.design_outdoor_temperature_c:
        gaps.append("DESIGN_TEMPERATURE_ORDER_INVALID")
    if not _positive(state.design_total_h_w_per_k):
        gaps.append("DESIGN_TOTAL_H_INVALID")
    if not _refs_ok(state.source_refs):
        gaps.append("STATE_SOURCE_REFS_MISSING")
    if len(state.months) != 12:
        gaps.append("EXACTLY_12_MONTHS_REQUIRED")
        return gaps

    month_ids = [m.month for m in state.months]
    if sorted(month_ids) != list(range(1, 13)):
        gaps.append("MONTH_SET_INVALID")

    annual_ext = {m.annual_external_temperature_c for m in state.months}
    if len(annual_ext) != 1:
        gaps.append("ANNUAL_EXTERNAL_TEMPERATURE_INCONSISTENT")

    for m in state.months:
        if not _positive(m.hours):
            gaps.append(f"MONTH_{m.month}_HOURS_INVALID")
        for value, label in (
            (m.external_temperature_c, "EXTERNAL_TEMPERATURE"),
            (m.annual_external_temperature_c, "ANNUAL_EXTERNAL_TEMPERATURE"),
        ):
            if not isfinite(value):
                gaps.append(f"MONTH_{m.month}_{label}_INVALID")
        for value, label in (
            (m.direct_unconditioned_h_w_per_k, "DIRECT_H"),
            (m.ground_h_w_per_k, "GROUND_H"),
            (m.ventilation_h_w_per_k, "VENTILATION_H"),
            (m.solar_gain_kwh, "SOLAR_GAIN"),
            (m.internal_gain_kwh, "INTERNAL_GAIN"),
        ):
            if not isfinite(value) or value < 0:
                gaps.append(f"MONTH_{m.month}_{label}_INVALID")
        if not 0 <= m.gain_utilization_factor <= 1:
            gaps.append(f"MONTH_{m.month}_GAIN_UTILIZATION_INVALID")
        if not 0 < m.intermittent_operation_factor <= 1:
            gaps.append(f"MONTH_{m.month}_INTERMITTENT_FACTOR_INVALID")
    return gaps


def calculate_state_demand(state: PhysicalState) -> StateDemandResult:
    gaps = _state_gaps(state)
    if gaps:
        return StateDemandResult(None, None, tuple(gaps))

    annual = 0.0
    for m in state.months:
        delta_outdoor = state.indoor_temperature_c - m.external_temperature_c
        delta_ground = state.indoor_temperature_c - m.annual_external_temperature_c

        q_transmission = (
            m.direct_unconditioned_h_w_per_k * delta_outdoor
            + m.ground_h_w_per_k * delta_ground
        ) * m.hours / 1000.0

        q_ventilation = (
            m.ventilation_h_w_per_k * delta_outdoor * m.hours / 1000.0
        )

        q_loss = m.intermittent_operation_factor * (
            q_transmission + q_ventilation
        )
        q_gain = m.solar_gain_kwh + m.internal_gain_kwh

        if q_loss <= 0:
            q_net = 0.0
        else:
            q_net = max(0.0, q_loss - m.gain_utilization_factor * q_gain)
        annual += q_net

    design_delta_t = (
        state.indoor_temperature_c - state.design_outdoor_temperature_c
    )
    peak = state.design_total_h_w_per_k * design_delta_t / 1000.0

    return StateDemandResult(annual, peak, ())


def _infer_changed_keys(before: PhysicalState, after: PhysicalState) -> set[str]:
    changed: set[str] = set()

    for bm, am in zip(
        sorted(before.months, key=lambda x: x.month),
        sorted(after.months, key=lambda x: x.month),
    ):
        if bm.direct_unconditioned_h_w_per_k != am.direct_unconditioned_h_w_per_k:
            changed.add("TRANSMISSION")
        if bm.ground_h_w_per_k != am.ground_h_w_per_k:
            changed.add("GROUND_TRANSMISSION")
        if bm.ventilation_h_w_per_k != am.ventilation_h_w_per_k:
            changed.add("VENTILATION")
        if bm.solar_gain_kwh != am.solar_gain_kwh:
            changed.add("SOLAR_GAIN")
        if bm.gain_utilization_factor != am.gain_utilization_factor:
            changed.add("THERMAL_DYNAMICS")
    if before.design_total_h_w_per_k != after.design_total_h_w_per_k:
        # Design H is an aggregate peak-state consequence. It does not create a
        # new claim key; the underlying monthly/state change must explain it.
        pass
    return changed


def assess_effect_surface(evidence: EffectSurfaceEvidence) -> EffectSurfaceDecision:
    reasons: list[str] = []
    before = evidence.before
    after = evidence.after
    domain = evidence.domain

    reasons.extend(f"BEFORE_{x}" for x in _state_gaps(before))
    reasons.extend(f"AFTER_{x}" for x in _state_gaps(after))

    if not evidence.intervention_id.strip():
        reasons.append("INTERVENTION_ID_MISSING")
    if before.record_id != after.record_id:
        reasons.append("RECORD_ID_MISMATCH")
    if before.building_type != after.building_type:
        reasons.append("BUILDING_TYPE_MISMATCH")
    if before.construction_period != after.construction_period:
        reasons.append("CONSTRUCTION_PERIOD_MISMATCH")
    if before.state_id == after.state_id:
        reasons.append("BEFORE_AFTER_STATE_NOT_DISTINCT")
    if before.climate_id != after.climate_id:
        reasons.append("CLIMATE_ID_MISMATCH")
    if before.heated_floor_area_m2 != after.heated_floor_area_m2:
        reasons.append("HEATED_FLOOR_AREA_MISMATCH")
    if before.heated_volume_m3 != after.heated_volume_m3:
        reasons.append("HEATED_VOLUME_MISMATCH")
    if before.indoor_temperature_c != after.indoor_temperature_c:
        reasons.append("INDOOR_TEMPERATURE_MISMATCH")
    if before.design_outdoor_temperature_c != after.design_outdoor_temperature_c:
        reasons.append("DESIGN_OUTDOOR_TEMPERATURE_MISMATCH")

    before_months = {m.month: m for m in before.months}
    after_months = {m.month: m for m in after.months}
    if set(before_months) == set(after_months) == set(range(1, 13)):
        for month in range(1, 13):
            bm = before_months[month]
            am = after_months[month]
            if bm.hours != am.hours:
                reasons.append(f"MONTH_{month}_HOURS_MISMATCH")
            if bm.external_temperature_c != am.external_temperature_c:
                reasons.append(f"MONTH_{month}_CLIMATE_MISMATCH")
            if (
                bm.annual_external_temperature_c
                != am.annual_external_temperature_c
            ):
                reasons.append(f"MONTH_{month}_ANNUAL_CLIMATE_MISMATCH")
            if bm.internal_gain_kwh != am.internal_gain_kwh:
                reasons.append(f"MONTH_{month}_INTERNAL_GAIN_MISMATCH")
            if (
                bm.intermittent_operation_factor
                != am.intermittent_operation_factor
            ):
                reasons.append(f"MONTH_{month}_SERVICE_SCHEDULE_MISMATCH")

    if not domain.domain_id.strip():
        reasons.append("DOMAIN_ID_MISSING")
    if domain.national_prevalence_claim:
        reasons.append("NATIONAL_PREVALENCE_CLAIM_PROHIBITED")
    if not _refs_ok(domain.source_refs):
        reasons.append("DOMAIN_SOURCE_REFS_MISSING")
    if before.building_type not in domain.allowed_building_types:
        reasons.append("BUILDING_TYPE_OUTSIDE_DOMAIN")
    if before.construction_period not in domain.allowed_construction_periods:
        reasons.append("CONSTRUCTION_PERIOD_OUTSIDE_DOMAIN")
    if before.state_id not in domain.allowed_before_states:
        reasons.append("BEFORE_STATE_OUTSIDE_DOMAIN")
    if after.state_id not in domain.allowed_after_states:
        reasons.append("AFTER_STATE_OUTSIDE_DOMAIN")

    declared = set(evidence.changed_parameter_keys)
    if not declared:
        reasons.append("CHANGED_PARAMETER_KEYS_MISSING")
    if not declared.issubset(CHANGE_KEYS):
        reasons.append("CHANGED_PARAMETER_KEY_UNKNOWN")
    inferred = _infer_changed_keys(before, after)
    if inferred != declared:
        reasons.append(
            "CHANGED_PARAMETER_KEYS_MISMATCH:"
            + ",".join(sorted(inferred ^ declared))
        )

    if before.design_total_h_w_per_k != after.design_total_h_w_per_k and not inferred:
        reasons.append("DESIGN_H_CHANGED_WITHOUT_PHYSICAL_STATE_CHANGE")

    if not _refs_ok(evidence.applicability_source_refs):
        reasons.append("APPLICABILITY_SOURCE_REFS_MISSING")
    if not evidence.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return EffectSurfaceDecision(Q, None, None, tuple(sorted(declared)), tuple(reasons))

    before_result = calculate_state_demand(before)
    after_result = calculate_state_demand(after)
    if before_result.gaps or after_result.gaps:
        reasons.extend(before_result.gaps)
        reasons.extend(after_result.gaps)
        return EffectSurfaceDecision(Q, None, None, tuple(sorted(declared)), tuple(reasons))

    assert before_result.annual_space_heat_kwh is not None
    assert after_result.annual_space_heat_kwh is not None
    assert before_result.design_peak_heat_kw is not None
    assert after_result.design_peak_heat_kw is not None

    if before_result.annual_space_heat_kwh <= 0 or before_result.design_peak_heat_kw <= 0:
        return EffectSurfaceDecision(
            Q, None, None, tuple(sorted(declared)), ("BASELINE_DEMAND_NOT_POSITIVE",)
        )

    annual_fraction = (
        before_result.annual_space_heat_kwh
        - after_result.annual_space_heat_kwh
    ) / before_result.annual_space_heat_kwh
    peak_fraction = (
        before_result.design_peak_heat_kw
        - after_result.design_peak_heat_kw
    ) / before_result.design_peak_heat_kw

    if not 0 <= annual_fraction <= 1:
        return EffectSurfaceDecision(
            Q, None, None, tuple(sorted(declared)), ("ANNUAL_EFFECT_OUTSIDE_REDUCTION_DOMAIN",)
        )
    if not 0 <= peak_fraction <= 1:
        return EffectSurfaceDecision(
            Q, None, None, tuple(sorted(declared)), ("PEAK_EFFECT_OUTSIDE_REDUCTION_DOMAIN",)
        )

    return EffectSurfaceDecision(
        QUALIFIED,
        annual_fraction,
        peak_fraction,
        tuple(sorted(declared)),
        (),
    )
