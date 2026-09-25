"""B05-P34 NIBE defrost event-energy admission contract.

A visible defrost-shaped trace is not event identity, and event identity is not
event energy. Numeric event kWh is admitted only from a complete same-system,
co-timed event where direct controller state and OBS electrical/thermal
measurements share explicit interval and boundary semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


ACTIVE = "ACTIVE"
PASSIVE = "PASSIVE"
INTERVAL_MEAN = "INTERVAL_MEAN"
THERMAL_POSITIVE_TO_BUILDING = "THERMAL_POSITIVE_TO_BUILDING"
DIRECT_OFF_EVENT_OFF = "DIRECT_OFF_EVENT_OFF"
OBS = "OBS"

Q_COTIMED_SERIES = "Q_NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED"
Q_EVENT_ENERGY = "Q_NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED"


@dataclass(frozen=True)
class DefrostIntervalSample:
    event_id: str
    system_id: str
    start_epoch_s: int
    end_epoch_s: int
    direct_defrost_state: str
    event_boundary_status: str
    electric_power_w: float | None
    thermal_power_w: float | None
    interval_semantics: str
    electric_boundary: str
    thermal_boundary: str
    thermal_sign_convention: str
    state_source_id: str
    electric_source_id: str
    thermal_source_id: str
    state_evidence_status: str
    electric_evidence_status: str
    thermal_evidence_status: str


@dataclass(frozen=True)
class EventEnergyAdmission:
    admitted: bool
    status: str
    event_id: str | None
    system_id: str | None
    defrost_state: str | None
    duration_seconds: int | None
    electricity_kwh: float | None
    net_thermal_to_building_kwh: float | None
    heat_removed_kwh: float | None
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


def _q(reason: str) -> EventEnergyAdmission:
    return EventEnergyAdmission(
        admitted=False,
        status="Q / COTIMED_EVENT_SERIES_NOT_ADMITTED",
        event_id=None,
        system_id=None,
        defrost_state=None,
        duration_seconds=None,
        electricity_kwh=None,
        net_thermal_to_building_kwh=None,
        heat_removed_kwh=None,
        evidence_status="Q",
        residual_gaps=(Q_COTIMED_SERIES, Q_EVENT_ENERGY),
        reason=reason,
    )


def integrate_cotimed_defrost_event(
    samples: Iterable[DefrostIntervalSample],
) -> EventEnergyAdmission:
    """Integrate a fully admitted co-timed defrost event.

    Rows must already be in source/materializer time order. Each row represents
    an interval mean over [start_epoch_s, end_epoch_s). The event boundary must
    be independently bound by direct OFF -> ACTIVE/PASSIVE -> OFF state
    transitions; a partial event window is not admitted as complete event energy.
    """
    rows = list(samples)
    if not rows:
        return _q("No event intervals supplied.")

    event_ids = {row.event_id for row in rows}
    if "" in event_ids or len(event_ids) != 1:
        return _q("All intervals must carry one explicit event identity.")

    system_ids = {row.system_id for row in rows}
    if "" in system_ids or len(system_ids) != 1:
        return _q("All intervals must carry one explicit same-system identity.")

    if any(row.event_boundary_status != DIRECT_OFF_EVENT_OFF for row in rows):
        return _q("Complete event energy requires direct OFF-to-event-to-OFF boundary authority.")

    if any(
        row.state_evidence_status != OBS
        or row.electric_evidence_status != OBS
        or row.thermal_evidence_status != OBS
        for row in rows
    ):
        return _q("Direct state and both measurement streams must be OBS before event energy is derived.")

    states = {row.direct_defrost_state for row in rows}
    if not states or not states.issubset({ACTIVE, PASSIVE}) or len(states) != 1:
        return _q("A single directly observed active or passive defrost state is required.")

    if any(row.interval_semantics != INTERVAL_MEAN for row in rows):
        return _q("Point/instantaneous samples are not integrated as energy without interval-mean semantics.")

    if any(
        not row.electric_boundary
        or not row.thermal_boundary
        or not row.state_source_id
        or not row.electric_source_id
        or not row.thermal_source_id
        for row in rows
    ):
        return _q("State and both meter boundaries/source identities must be explicit.")

    electric_boundaries = {row.electric_boundary for row in rows}
    thermal_boundaries = {row.thermal_boundary for row in rows}
    if len(electric_boundaries) != 1 or len(thermal_boundaries) != 1:
        return _q("Meter boundaries must remain invariant across the event.")

    if any(row.thermal_sign_convention != THERMAL_POSITIVE_TO_BUILDING for row in rows):
        return _q("Thermal sign convention must be explicit and invariant.")

    previous_end = None
    for row in rows:
        if row.end_epoch_s <= row.start_epoch_s:
            return _q("Every event interval must have positive duration.")
        if previous_end is not None and previous_end != row.start_epoch_s:
            return _q("Event intervals must be source-ordered and contiguous with no gaps or overlaps.")
        previous_end = row.end_epoch_s

        if row.electric_power_w is None or row.thermal_power_w is None:
            return _q("Both electrical and thermal interval-mean powers are required.")
        if not isfinite(row.electric_power_w) or not isfinite(row.thermal_power_w):
            return _q("Non-finite power values are not admissible.")
        if row.electric_power_w < 0:
            return _q("Electrical input power cannot be negative.")

    electric_wh = 0.0
    thermal_wh = 0.0
    removed_wh = 0.0
    for row in rows:
        hours = (row.end_epoch_s - row.start_epoch_s) / 3600.0
        electric_wh += row.electric_power_w * hours
        thermal_wh += row.thermal_power_w * hours
        removed_wh += max(-row.thermal_power_w, 0.0) * hours

    duration = rows[-1].end_epoch_s - rows[0].start_epoch_s

    return EventEnergyAdmission(
        admitted=True,
        status="DER_FROM_COMPLETE_COTIMED_OBS_INTERVAL_MEANS",
        event_id=rows[0].event_id,
        system_id=rows[0].system_id,
        defrost_state=rows[0].direct_defrost_state,
        duration_seconds=duration,
        electricity_kwh=electric_wh / 1000.0,
        net_thermal_to_building_kwh=thermal_wh / 1000.0,
        heat_removed_kwh=removed_wh / 1000.0,
        evidence_status="DER",
        residual_gaps=(),
        reason=(
            "Numeric event energy is derived only from a complete directly "
            "transition-bound event with contiguous same-system OBS interval "
            "means and explicit invariant electrical/thermal boundaries."
        ),
    )


def p34_boundary() -> tuple[str, ...]:
    return (
        "EVENT_SHAPE != EVENT_IDENTITY",
        "EVENT_IDENTITY != EVENT_ENERGY",
        "PARTIAL_EVENT_WINDOW != COMPLETE_EVENT_ENERGY",
        "FORUM_OR_DASHBOARD_VISUAL != RAW_COTIMED_TIMESERIES",
        "DIRECT_DEFROST_STATE_PLUS_COTIMED_ELECTRIC_PLUS_THERMAL_REQUIRED",
        "DIRECT_OFF_EVENT_OFF_BOUNDARY_REQUIRED",
        "INSTANTANEOUS_POINT_SAMPLE != INTERVAL_ENERGY",
        "FIELD_BACK_OF_ENVELOPE != OBS_EVENT_ENERGY",
        "GENERIC_FLEET_DEFROST_SHARE != PRODUCT_EVENT_ENERGY",
        "NO_NUMERIC_EVENT_PENALTY_WITHOUT_ADMISSION",
    )
