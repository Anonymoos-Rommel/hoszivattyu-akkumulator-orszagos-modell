"""B06-P62 intervention-linked annual + design-peak effect gate.

A real intervention effect may enter B06 only when annual and design-peak
before/after values are independently evidenced for the same building,
intervention, method family and design condition.

ANNUAL REDUCTION != PEAK REDUCTION
ANNUAL RATIO != PEAK RATIO
PLANNED DER != OBSERVED COMPLETION
SAME RECORD + SAME INTERVENTION + SAME DESIGN BASIS = ADMISSIBLE DER EFFECT
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"
BLOCKED = "BLOCKED"

OBS = "OBS"
DER = "DER"
REAL_EVIDENCE = frozenset({OBS, DER})

PLANNED_DESIGN = "PLANNED_DESIGN"
REALIZED = "REALIZED"
POST_STATE_KINDS = frozenset({PLANNED_DESIGN, REALIZED})


@dataclass(frozen=True)
class PeakEffectEvidence:
    record_id: str
    intervention_id: str
    evidence_status: str
    post_state_kind: str

    before_annual_space_heat_kwh: float | None
    after_annual_space_heat_kwh: float | None
    before_peak_heat_load_kw: float | None
    after_peak_heat_load_kw: float | None

    before_method_id: str
    after_method_id: str
    before_source_refs: tuple[str, ...]
    after_source_refs: tuple[str, ...]

    before_phase_id: str
    after_phase_id: str

    before_design_indoor_temperature_c: float | None
    after_design_indoor_temperature_c: float | None
    before_design_outdoor_temperature_c: float | None
    after_design_outdoor_temperature_c: float | None

    before_heated_floor_area_m2: float | None = None
    after_heated_floor_area_m2: float | None = None
    before_heated_volume_m3: float | None = None
    after_heated_volume_m3: float | None = None

    intervention_scope_documented: bool = False
    dhw_separate_from_space_heat: bool = False
    annual_to_peak_inference_used: bool = False
    reproducible_repository_binding: bool = False


@dataclass(frozen=True)
class PeakEffectDecision:
    status: str
    annual_reduction_fraction: float | None
    peak_reduction_fraction: float | None
    reasons: tuple[str, ...]


def _positive(value: float | None) -> bool:
    return value is not None and isfinite(value) and value > 0


def _refs_ok(refs: tuple[str, ...]) -> bool:
    return bool(refs) and all(isinstance(ref, str) and ref.strip() for ref in refs)


def assess_peak_effect(evidence: PeakEffectEvidence) -> PeakEffectDecision:
    reasons: list[str] = []

    if not evidence.record_id.strip():
        reasons.append("RECORD_ID_MISSING")
    if not evidence.intervention_id.strip():
        reasons.append("INTERVENTION_ID_MISSING")
    if evidence.evidence_status not in REAL_EVIDENCE:
        reasons.append("EVIDENCE_NOT_OBS_OR_DER")
    if evidence.post_state_kind not in POST_STATE_KINDS:
        reasons.append("POST_STATE_KIND_UNKNOWN")

    for value, reason in (
        (evidence.before_annual_space_heat_kwh, "BEFORE_ANNUAL_INVALID"),
        (evidence.after_annual_space_heat_kwh, "AFTER_ANNUAL_INVALID"),
        (evidence.before_peak_heat_load_kw, "BEFORE_PEAK_INVALID"),
        (evidence.after_peak_heat_load_kw, "AFTER_PEAK_INVALID"),
    ):
        if not _positive(value):
            reasons.append(reason)

    if not evidence.before_method_id.strip() or not evidence.after_method_id.strip():
        reasons.append("METHOD_ID_MISSING")
    elif evidence.before_method_id != evidence.after_method_id:
        reasons.append("METHOD_ID_MISMATCH")

    if not _refs_ok(evidence.before_source_refs):
        reasons.append("BEFORE_SOURCE_REFS_MISSING")
    if not _refs_ok(evidence.after_source_refs):
        reasons.append("AFTER_SOURCE_REFS_MISSING")

    if not evidence.before_phase_id.strip() or not evidence.after_phase_id.strip():
        reasons.append("PHASE_ID_MISSING")
    if evidence.before_phase_id == evidence.after_phase_id:
        reasons.append("BEFORE_AFTER_PHASES_NOT_DISTINCT")

    for before, after, reason in (
        (
            evidence.before_design_indoor_temperature_c,
            evidence.after_design_indoor_temperature_c,
            "DESIGN_INDOOR_TEMPERATURE_MISMATCH",
        ),
        (
            evidence.before_design_outdoor_temperature_c,
            evidence.after_design_outdoor_temperature_c,
            "DESIGN_OUTDOOR_TEMPERATURE_MISMATCH",
        ),
    ):
        if before is None or after is None:
            reasons.append(reason.replace("MISMATCH", "MISSING"))
        elif before != after:
            reasons.append(reason)

    for before, after, reason in (
        (
            evidence.before_heated_floor_area_m2,
            evidence.after_heated_floor_area_m2,
            "HEATED_FLOOR_AREA_MISMATCH",
        ),
        (
            evidence.before_heated_volume_m3,
            evidence.after_heated_volume_m3,
            "HEATED_VOLUME_MISMATCH",
        ),
    ):
        if before is not None or after is not None:
            if not _positive(before) or not _positive(after):
                reasons.append(reason.replace("MISMATCH", "INVALID"))
            elif abs(before - after) > 0.05:
                reasons.append(reason)

    if not evidence.intervention_scope_documented:
        reasons.append("INTERVENTION_SCOPE_MISSING")
    if not evidence.dhw_separate_from_space_heat:
        reasons.append("DHW_SPACE_HEAT_BOUNDARY_MISSING")
    if evidence.annual_to_peak_inference_used:
        reasons.append("ANNUAL_TO_PEAK_INFERENCE_PROHIBITED")
    if not evidence.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return PeakEffectDecision(Q, None, None, tuple(reasons))

    assert evidence.before_annual_space_heat_kwh is not None
    assert evidence.after_annual_space_heat_kwh is not None
    assert evidence.before_peak_heat_load_kw is not None
    assert evidence.after_peak_heat_load_kw is not None

    annual_fraction = (
        evidence.before_annual_space_heat_kwh - evidence.after_annual_space_heat_kwh
    ) / evidence.before_annual_space_heat_kwh
    peak_fraction = (
        evidence.before_peak_heat_load_kw - evidence.after_peak_heat_load_kw
    ) / evidence.before_peak_heat_load_kw

    if annual_fraction <= 0:
        return PeakEffectDecision(
            BLOCKED, annual_fraction, peak_fraction, ("ANNUAL_REDUCTION_NOT_ACHIEVED",)
        )
    if peak_fraction <= 0:
        return PeakEffectDecision(
            BLOCKED, annual_fraction, peak_fraction, ("PEAK_REDUCTION_NOT_ACHIEVED",)
        )

    return PeakEffectDecision(QUALIFIED, annual_fraction, peak_fraction, ())
