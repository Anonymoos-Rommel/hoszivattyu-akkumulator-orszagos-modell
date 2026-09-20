"""B06-P65 fail-closed authority for post-retrofit emitter water temperature.

This gate answers a narrower question than the P4 emitter physics helper:
P4 can calculate output at explicit emitter operating points, while P65 decides
whether a *building record* has enough evidence to change the post-retrofit
supply temperature handed to B05.

No W35/W45/W55 label, boiler setpoint, HET reference system, national average,
or emitter-type name can mint a numeric building supply temperature.
"""

from __future__ import annotations

from dataclasses import dataclass

from .engine import EvidenceValue
from .design_load import (
    EmitterOperatingPoint,
    EmitterRating,
    derive_required_supply_temperature,
)


QUALIFIED = "QUALIFIED"
Q = "Q"

ROOM_BY_ROOM_DESIGN = "ROOM_BY_ROOM_EMITTER_DESIGN"
SIGNED_MEP_DESIGN = "SIGNED_POST_RETROFIT_MEP_DESIGN"
MEASURED_DESIGN_POINT = "MEASURED_POST_RETROFIT_DESIGN_POINT"

ALLOWED_ROUTES = {
    ROOM_BY_ROOM_DESIGN,
    SIGNED_MEP_DESIGN,
    MEASURED_DESIGN_POINT,
}
ALLOWED_PHASES = {"POST_RETROFIT_PLANNED", "POST_RETROFIT_REALIZED"}
ADMISSIBLE_EVIDENCE = {"OBS", "DER"}


@dataclass(frozen=True)
class RoomEmitterDesignEvidence:
    """One heated room's post-state design load and exact emitter inventory."""

    room_id: str
    design_heat_load_kw: EvidenceValue[float]
    design_indoor_temperature_c: EvidenceValue[float]
    emitter: EmitterRating
    operating_points: tuple[EmitterOperatingPoint, ...]
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EmitterTemperatureEvidence:
    """Record-linked authority for a post-retrofit hydronic design point.

    Exactly one evidence route is selected.  Fields unused by that route stay
    empty/Q; this prevents a weak source from being silently completed by
    assumptions from another route.
    """

    record_id: str
    intervention_id: str
    phase_id: str
    route: str
    evidence_status: str
    source_refs: tuple[str, ...]
    building_design_heat_load_kw: EvidenceValue[float] = EvidenceValue(None, "Q")

    # ROOM_BY_ROOM_DESIGN route.
    heated_room_count: int | None = None
    rooms: tuple[RoomEmitterDesignEvidence, ...] = ()

    # SIGNED_MEP_DESIGN and MEASURED_DESIGN_POINT routes.
    explicit_supply_temperature_c: EvidenceValue[float] = EvidenceValue(None, "Q")
    explicit_return_temperature_c: EvidenceValue[float] = EvidenceValue(None, "Q")
    design_outdoor_temperature_c: EvidenceValue[float] = EvidenceValue(None, "Q")
    design_indoor_temperature_c: EvidenceValue[float] = EvidenceValue(None, "Q")

    # Signed-design completeness assertions, evidenced by the same packet.
    room_heat_loss_complete: bool = False
    emitter_schedule_complete: bool = False
    hydraulic_design_documented: bool = False
    designer_or_engineer_id: str = ""
    design_document_signed_or_sealed: bool = False

    # Measured route: only a design-condition-or-colder observation can mint a
    # design-point temperature without an additional extrapolation authority.
    measured_outdoor_temperature_c: EvidenceValue[float] = EvidenceValue(None, "Q")
    minimum_measured_room_temperature_c: EvidenceValue[float] = EvidenceValue(None, "Q")
    measurement_room_coverage_complete: bool = False


@dataclass(frozen=True)
class EmitterTemperatureDecision:
    status: str
    required_supply_temperature_c: float | None
    required_return_temperature_c: float | None
    supported_design_heat_load_kw: float | None
    critical_room_id: str | None
    route: str | None
    source_refs: tuple[str, ...]
    gaps: tuple[str, ...]


def _numeric(value: EvidenceValue[float], name: str, *, admissible=ADMISSIBLE_EVIDENCE) -> tuple[float | None, str | None]:
    try:
        value.validate(name)
    except ValueError as exc:
        return None, str(exc)
    if value.status not in admissible or value.value is None:
        allowed = "/".join(sorted(admissible))
        return None, f"{name} requires {allowed} evidence"
    if not value.source_ids:
        return None, f"{name} requires source lineage"
    try:
        number = float(value.value)
    except (TypeError, ValueError):
        return None, f"{name} is not numeric"
    return number, None


def _q(route: str | None, source_refs: tuple[str, ...], gaps: list[str] | tuple[str, ...]) -> EmitterTemperatureDecision:
    return EmitterTemperatureDecision(Q, None, None, None, None, route, source_refs, tuple(gaps))


def assess_emitter_temperature(evidence: EmitterTemperatureEvidence) -> EmitterTemperatureDecision:
    """Assess one record without inferring missing emitter or temperature facts."""

    gaps: list[str] = []
    if not evidence.record_id:
        gaps.append("record_id is required")
    if not evidence.intervention_id:
        gaps.append("intervention_id is required")
    if evidence.phase_id not in ALLOWED_PHASES:
        gaps.append("phase_id must be a post-retrofit planned or realized state")
    if evidence.route not in ALLOWED_ROUTES:
        gaps.append("unsupported emitter-temperature evidence route")
    if evidence.evidence_status not in ADMISSIBLE_EVIDENCE:
        gaps.append("emitter-temperature authority requires OBS/DER evidence")
    if not evidence.source_refs:
        gaps.append("source_refs are required")
    if gaps:
        return _q(evidence.route or None, evidence.source_refs, gaps)

    if evidence.route == ROOM_BY_ROOM_DESIGN:
        if evidence.heated_room_count is None or evidence.heated_room_count <= 0:
            return _q(evidence.route, evidence.source_refs, ["heated_room_count must be positive"])
        if len(evidence.rooms) != evidence.heated_room_count:
            return _q(evidence.route, evidence.source_refs, ["heated-room coverage is incomplete"])
        room_ids = [room.room_id for room in evidence.rooms]
        if any(not room_id for room_id in room_ids) or len(set(room_ids)) != len(room_ids):
            return _q(evidence.route, evidence.source_refs, ["room_id coverage must be non-empty and unique"])

        room_results: list[tuple[str, float, float, tuple[str, ...]]] = []
        room_design_load_total_kw = 0.0
        all_sources = set(evidence.source_refs)
        for room in evidence.rooms:
            if not room.source_refs:
                return _q(evidence.route, evidence.source_refs, [f"{room.room_id}: source_refs are required"])
            if not room.emitter.source_ids:
                return _q(evidence.route, evidence.source_refs, [f"{room.room_id}: emitter source_ids are required"])
            emitter_fields = (
                ("nominal_output_kw", room.emitter.nominal_output_kw),
                ("nominal_flow_temperature_c", room.emitter.nominal_flow_temperature_c),
                ("nominal_return_temperature_c", room.emitter.nominal_return_temperature_c),
                ("room_temperature_c", room.emitter.room_temperature_c),
                ("temperature_exponent", room.emitter.temperature_exponent),
                ("quantity", room.emitter.quantity),
                ("correction_method", room.emitter.correction_method),
            )
            missing_emitter_lineage = [
                name for name, value in emitter_fields if not value.source_ids
            ]
            if missing_emitter_lineage:
                return _q(
                    evidence.route,
                    evidence.source_refs,
                    [f"{room.room_id}: emitter fields lack source lineage: " + ",".join(missing_emitter_lineage)],
                )
            if room.design_heat_load_kw.status not in ADMISSIBLE_EVIDENCE:
                return _q(evidence.route, evidence.source_refs, [f"{room.room_id}: design heat load requires OBS/DER"])
            room_indoor, room_indoor_gap = _numeric(
                room.design_indoor_temperature_c,
                f"{room.room_id}.design_indoor_temperature_c",
            )
            if room_indoor_gap:
                return _q(evidence.route, evidence.source_refs, [room_indoor_gap])
            result = derive_required_supply_temperature(
                room.design_heat_load_kw,
                room.emitter,
                room.operating_points,
            )
            if result.status not in ADMISSIBLE_EVIDENCE or result.required_supply_temperature_c is None:
                reason = "; ".join(result.gaps) if result.gaps else "emitter design point is Q"
                return _q(evidence.route, evidence.source_refs, [f"{room.room_id}: {reason}"])

            selected_return = None
            selected_room_temperature = None
            for point in room.operating_points:
                if (
                    point.supply_temperature_c.value is not None
                    and float(point.supply_temperature_c.value) == float(result.required_supply_temperature_c)
                    and point.return_temperature_c.value is not None
                    and point.room_temperature_c.value is not None
                ):
                    selected_return = float(point.return_temperature_c.value)
                    selected_room_temperature = float(point.room_temperature_c.value)
                    break
            if selected_return is None or selected_room_temperature is None:
                return _q(evidence.route, evidence.source_refs, [f"{room.room_id}: selected return/room temperature is Q"])
            selected_points = [
                point
                for point in room.operating_points
                if (
                    point.supply_temperature_c.value is not None
                    and float(point.supply_temperature_c.value) == float(result.required_supply_temperature_c)
                    and point.return_temperature_c.value is not None
                    and point.room_temperature_c.value is not None
                )
            ]
            selected_point = selected_points[0]
            if not all(
                value.source_ids
                for value in (
                    selected_point.supply_temperature_c,
                    selected_point.return_temperature_c,
                    selected_point.room_temperature_c,
                )
            ):
                return _q(
                    evidence.route,
                    evidence.source_refs,
                    [f"{room.room_id}: selected operating point lacks source lineage"],
                )
            all_sources.update(selected_point.supply_temperature_c.source_ids)
            all_sources.update(selected_point.return_temperature_c.source_ids)
            all_sources.update(selected_point.room_temperature_c.source_ids)
            if abs(selected_room_temperature - room_indoor) > 1e-9:
                return _q(
                    evidence.route,
                    evidence.source_refs,
                    [f"{room.room_id}: emitter room temperature does not match design heat-load indoor temperature"],
                )

            room_design_load_total_kw += float(room.design_heat_load_kw.value)
            all_sources.update(room.source_refs)
            all_sources.update(room.design_indoor_temperature_c.source_ids)
            all_sources.update(room.emitter.source_ids)
            all_sources.update(room.design_heat_load_kw.source_ids)
            room_results.append(
                (
                    room.room_id,
                    float(result.required_supply_temperature_c),
                    selected_return,
                    tuple(room.source_refs),
                )
            )

        # The warmest required room governs a common hydronic supply.  Averaging
        # room temperatures would under-serve the critical room and is forbidden.
        critical = max(room_results, key=lambda item: item[1])
        return EmitterTemperatureDecision(
            QUALIFIED,
            critical[1],
            critical[2],
            room_design_load_total_kw,
            critical[0],
            evidence.route,
            tuple(sorted(all_sources)),
            (),
        )

    temperature_admissible = {"OBS"} if evidence.route == MEASURED_DESIGN_POINT else ADMISSIBLE_EVIDENCE
    supply, supply_gap = _numeric(
        evidence.explicit_supply_temperature_c,
        "explicit_supply_temperature_c",
        admissible=temperature_admissible,
    )
    return_temp, return_gap = _numeric(
        evidence.explicit_return_temperature_c,
        "explicit_return_temperature_c",
        admissible=temperature_admissible,
    )
    design_outdoor, outdoor_gap = _numeric(evidence.design_outdoor_temperature_c, "design_outdoor_temperature_c")
    design_indoor, indoor_gap = _numeric(evidence.design_indoor_temperature_c, "design_indoor_temperature_c")
    building_load, building_load_gap = _numeric(
        evidence.building_design_heat_load_kw,
        "building_design_heat_load_kw",
    )
    gaps.extend(
        gap for gap in (supply_gap, return_gap, outdoor_gap, indoor_gap, building_load_gap) if gap
    )
    if building_load is not None and building_load <= 0:
        gaps.append("building_design_heat_load_kw must be positive")
    if not gaps and not (supply > return_temp > design_indoor):
        gaps.append("hydronic temperatures must satisfy supply > return > design indoor temperature")

    if evidence.route == SIGNED_MEP_DESIGN:
        if not evidence.room_heat_loss_complete:
            gaps.append("signed design lacks complete room heat-loss basis")
        if not evidence.emitter_schedule_complete:
            gaps.append("signed design lacks complete emitter schedule")
        if not evidence.hydraulic_design_documented:
            gaps.append("signed design lacks hydraulic design/balancing basis")
        if not evidence.designer_or_engineer_id.strip():
            gaps.append("signed design lacks designer/engineer identity")
        if not evidence.design_document_signed_or_sealed:
            gaps.append("design document is not signed or sealed")
        if gaps:
            return _q(evidence.route, evidence.source_refs, gaps)
        return EmitterTemperatureDecision(
            QUALIFIED,
            supply,
            return_temp,
            building_load,
            None,
            evidence.route,
            tuple(sorted(set(evidence.source_refs))),
            (),
        )

    # MEASURED_DESIGN_POINT
    if evidence.phase_id != "POST_RETROFIT_REALIZED":
        gaps.append("measured route requires POST_RETROFIT_REALIZED phase")
    measured_outdoor, measured_outdoor_gap = _numeric(
        evidence.measured_outdoor_temperature_c,
        "measured_outdoor_temperature_c",
        admissible={"OBS"},
    )
    minimum_room, minimum_room_gap = _numeric(
        evidence.minimum_measured_room_temperature_c,
        "minimum_measured_room_temperature_c",
        admissible={"OBS"},
    )
    gaps.extend(gap for gap in (measured_outdoor_gap, minimum_room_gap) if gap)
    if not evidence.measurement_room_coverage_complete:
        gaps.append("measured heated-room coverage is incomplete")
    if not gaps and measured_outdoor > design_outdoor:
        gaps.append("measurement is warmer than the design outdoor condition; extrapolation is forbidden")
    if not gaps and minimum_room < design_indoor:
        gaps.append("measured minimum room temperature is below the design indoor setpoint")
    if gaps:
        return _q(evidence.route, evidence.source_refs, gaps)
    return EmitterTemperatureDecision(
        QUALIFIED,
        supply,
        return_temp,
        building_load,
        None,
        evidence.route,
        tuple(sorted(set(evidence.source_refs))),
        (),
    )
