"""B06-P61 phase-linked baseline demand gate.

A B06 baseline is admissible only when annual space-heating demand and design
peak heat load belong to the same building/archetype record and the same
pre-intervention phase.

ANNUAL ENERGY != DESIGN PEAK
INSTALLED CAPACITY != DESIGN PEAK
FULL-LOAD-HOURS PROXY != DESIGN PEAK
SAME BUILDING + SAME PHASE + INDEPENDENT ANNUAL/PEAK EVIDENCE = ADMISSIBLE
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"

OBS = "OBS"
DER = "DER"
REAL_EVIDENCE = frozenset({OBS, DER})

DIRECT_ANNUAL = "DIRECT_ANNUAL"
SPECIFIC_TIMES_AREA = "SPECIFIC_TIMES_AREA"
ANNUAL_METHODS = frozenset({DIRECT_ANNUAL, SPECIFIC_TIMES_AREA})

DIRECT_PEAK = "DIRECT_PEAK"
PHYSICAL_DESIGN_DERIVATION = "PHYSICAL_DESIGN_DERIVATION"
PEAK_METHODS = frozenset({DIRECT_PEAK, PHYSICAL_DESIGN_DERIVATION})


@dataclass(frozen=True)
class BaselineDemandEvidence:
    record_id: str
    phase_id: str

    annual_space_heat_kwh: float | None
    annual_evidence_status: str
    annual_method: str
    annual_source_refs: tuple[str, ...]

    peak_heat_load_kw: float | None
    peak_evidence_status: str
    peak_method: str
    peak_source_refs: tuple[str, ...]

    heated_floor_area_m2: float | None = None
    specific_annual_space_heat_kwh_m2a: float | None = None

    design_indoor_temperature_c: float | None = None
    design_outdoor_temperature_c: float | None = None

    annual_record_link: str = ""
    peak_record_link: str = ""
    annual_phase_link: str = ""
    peak_phase_link: str = ""

    annual_to_peak_inference_used: bool = False
    installed_capacity_used_as_peak: bool = False
    full_load_hours_proxy_used: bool = False
    reproducible_repository_binding: bool = False


@dataclass(frozen=True)
class BaselineDemandDecision:
    status: str
    reasons: tuple[str, ...]


def _valid_positive(value: float | None) -> bool:
    return value is not None and isfinite(value) and value > 0


def _refs_ok(refs: tuple[str, ...]) -> bool:
    return bool(refs) and all(isinstance(x, str) and x.strip() for x in refs)


def assess_baseline_demand(
    evidence: BaselineDemandEvidence,
) -> BaselineDemandDecision:
    reasons: list[str] = []

    if not evidence.record_id.strip():
        reasons.append("RECORD_ID_MISSING")
    if not evidence.phase_id.strip():
        reasons.append("PHASE_ID_MISSING")

    if evidence.annual_evidence_status not in REAL_EVIDENCE:
        reasons.append("ANNUAL_EVIDENCE_NOT_OBS_OR_DER")
    if evidence.peak_evidence_status not in REAL_EVIDENCE:
        reasons.append("PEAK_EVIDENCE_NOT_OBS_OR_DER")

    if evidence.annual_method not in ANNUAL_METHODS:
        reasons.append("ANNUAL_METHOD_UNKNOWN")
    if evidence.peak_method not in PEAK_METHODS:
        reasons.append("PEAK_METHOD_UNKNOWN")

    if not _valid_positive(evidence.annual_space_heat_kwh):
        reasons.append("ANNUAL_SPACE_HEAT_INVALID")
    if not _valid_positive(evidence.peak_heat_load_kw):
        reasons.append("PEAK_HEAT_LOAD_INVALID")

    if not _refs_ok(evidence.annual_source_refs):
        reasons.append("ANNUAL_SOURCE_REFS_MISSING")
    if not _refs_ok(evidence.peak_source_refs):
        reasons.append("PEAK_SOURCE_REFS_MISSING")

    if evidence.annual_record_link != evidence.record_id:
        reasons.append("ANNUAL_RECORD_LINK_MISMATCH")
    if evidence.peak_record_link != evidence.record_id:
        reasons.append("PEAK_RECORD_LINK_MISMATCH")
    if evidence.annual_phase_link != evidence.phase_id:
        reasons.append("ANNUAL_PHASE_LINK_MISMATCH")
    if evidence.peak_phase_link != evidence.phase_id:
        reasons.append("PEAK_PHASE_LINK_MISMATCH")

    if evidence.annual_method == SPECIFIC_TIMES_AREA:
        if not _valid_positive(evidence.heated_floor_area_m2):
            reasons.append("HEATED_FLOOR_AREA_INVALID")
        if not _valid_positive(evidence.specific_annual_space_heat_kwh_m2a):
            reasons.append("SPECIFIC_ANNUAL_SPACE_HEAT_INVALID")
        if (
            _valid_positive(evidence.heated_floor_area_m2)
            and _valid_positive(evidence.specific_annual_space_heat_kwh_m2a)
            and _valid_positive(evidence.annual_space_heat_kwh)
        ):
            expected = (
                evidence.heated_floor_area_m2
                * evidence.specific_annual_space_heat_kwh_m2a
            )
            if abs(expected - evidence.annual_space_heat_kwh) > 0.05:
                reasons.append("ANNUAL_DERIVATION_MISMATCH")

    if evidence.peak_method == PHYSICAL_DESIGN_DERIVATION:
        if evidence.design_indoor_temperature_c is None:
            reasons.append("DESIGN_INDOOR_TEMPERATURE_MISSING")
        if evidence.design_outdoor_temperature_c is None:
            reasons.append("DESIGN_OUTDOOR_TEMPERATURE_MISSING")
        if (
            evidence.design_indoor_temperature_c is not None
            and evidence.design_outdoor_temperature_c is not None
            and evidence.design_indoor_temperature_c
            <= evidence.design_outdoor_temperature_c
        ):
            reasons.append("DESIGN_TEMPERATURE_ORDER_INVALID")

    if evidence.annual_to_peak_inference_used:
        reasons.append("ANNUAL_TO_PEAK_INFERENCE_PROHIBITED")
    if evidence.installed_capacity_used_as_peak:
        reasons.append("INSTALLED_CAPACITY_AS_PEAK_PROHIBITED")
    if evidence.full_load_hours_proxy_used:
        reasons.append("FULL_LOAD_HOURS_PROXY_PROHIBITED")
    if not evidence.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return BaselineDemandDecision(Q, tuple(reasons))
    return BaselineDemandDecision(QUALIFIED, ())
