"""B05-P36 exact Silkeborg S2125 meter and cumulative-energy contract."""

from __future__ import annotations

from dataclasses import dataclass


Q_METER_EXPORT = "Q_SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED"
Q_DIRECT_STATE = "Q_SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED"
Q_ENERGY_SEMANTICS = (
    "Q_SILKEBORG_S2125_INTERVAL_MEAN_OR_QUALIFIED_CUMULATIVE_DELTA_REQUIRED"
)

METER_EXPORT_ADMITTED = "COTIMED_METER_EXPORT_ADMITTED"
CUMULATIVE_DELTA_ROUTE_ADMITTED = "CUMULATIVE_DELTA_ROUTE_ADMITTED"
READY_FOR_P34_EVENT_ENERGY_GATE = "READY_FOR_P34_EVENT_ENERGY_GATE"


@dataclass(frozen=True)
class CotimedMeterExportEvidence:
    exact_system_bound: bool
    public_app_binding_proven: bool
    electric_raw_timestamped_obs: bool
    thermal_raw_timestamped_obs: bool
    electric_unit_w: bool
    thermal_unit_w: bool
    electric_native_interval_s: int | None
    thermal_native_interval_s: int | None
    electric_nonnull_points: int
    thermal_nonnull_points: int
    common_nonnull_timestamps: int


@dataclass(frozen=True)
class CotimedMeterExportQualification:
    admitted: bool
    status: str
    evidence_status: str
    native_interval_s: int | None
    common_nonnull_timestamps: int
    residual_gaps: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class CumulativeDeltaEvidence:
    app_contract_electric_cumulative: bool
    app_contract_thermal_cumulative: bool
    app_contract_end_minus_start: bool
    exact_system_feed_binding: bool
    raw_timestamped_kwh_obs: bool
    common_four_feed_timestamps: int
    negative_thermal_points_checked: int
    negative_thermal_points_with_negative_kwh_delta: int
    reset_like_steps: int


@dataclass(frozen=True)
class CumulativeDeltaQualification:
    admitted: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class EventEnergyHandoff:
    ready: bool
    status: str
    residual_gaps: tuple[str, ...]
    reason: str


def qualify_cotimed_meter_export(
    evidence: CotimedMeterExportEvidence,
) -> CotimedMeterExportQualification:
    intervals_match = (
        evidence.electric_native_interval_s is not None
        and evidence.thermal_native_interval_s is not None
        and evidence.electric_native_interval_s > 0
        and evidence.electric_native_interval_s == evidence.thermal_native_interval_s
    )
    counts_valid = (
        evidence.electric_nonnull_points > 0
        and evidence.thermal_nonnull_points > 0
        and evidence.common_nonnull_timestamps > 0
        and evidence.common_nonnull_timestamps <= evidence.electric_nonnull_points
        and evidence.common_nonnull_timestamps <= evidence.thermal_nonnull_points
    )

    if not (
        evidence.exact_system_bound
        and evidence.public_app_binding_proven
        and evidence.electric_raw_timestamped_obs
        and evidence.thermal_raw_timestamped_obs
        and evidence.electric_unit_w
        and evidence.thermal_unit_w
        and intervals_match
        and counts_valid
    ):
        return CotimedMeterExportQualification(
            admitted=False,
            status="Q / COTIMED_METER_EXPORT_NOT_ADMITTED",
            evidence_status="Q",
            native_interval_s=None,
            common_nonnull_timestamps=0,
            residual_gaps=(Q_METER_EXPORT,),
            reason="Exact-system co-timed electric/thermal raw export is incomplete.",
        )

    return CotimedMeterExportQualification(
        admitted=True,
        status=METER_EXPORT_ADMITTED,
        evidence_status="OBS",
        native_interval_s=evidence.electric_native_interval_s,
        common_nonnull_timestamps=evidence.common_nonnull_timestamps,
        residual_gaps=(),
        reason=(
            "Raw same-system electric and thermal observations share a verified "
            "native interval and common timestamps. Event identity is separate."
        ),
    )


def qualify_cumulative_delta_route(
    evidence: CumulativeDeltaEvidence,
) -> CumulativeDeltaQualification:
    signed_reverse_proven = (
        evidence.negative_thermal_points_checked > 0
        and evidence.negative_thermal_points_with_negative_kwh_delta
        == evidence.negative_thermal_points_checked
    )
    if not (
        evidence.app_contract_electric_cumulative
        and evidence.app_contract_thermal_cumulative
        and evidence.app_contract_end_minus_start
        and evidence.exact_system_feed_binding
        and evidence.raw_timestamped_kwh_obs
        and evidence.common_four_feed_timestamps > 0
        and signed_reverse_proven
        and evidence.reset_like_steps == 0
    ):
        return CumulativeDeltaQualification(
            admitted=False,
            status="Q / CUMULATIVE_DELTA_ROUTE_NOT_ADMITTED",
            evidence_status="Q",
            residual_gaps=(Q_ENERGY_SEMANTICS,),
            reason=(
                "Cumulative feed semantics, exact-system binding, signed reverse "
                "behaviour and bounded no-reset evidence are required."
            ),
        )

    return CumulativeDeltaQualification(
        admitted=True,
        status=CUMULATIVE_DELTA_ROUTE_ADMITTED,
        evidence_status="DER",
        residual_gaps=(),
        reason=(
            "Pinned app semantics define cumulative electric/thermal kWh and "
            "end-minus-start calculation; exact field readback confirms signed "
            "thermal reverse behaviour and no reset-like jump in the audited window."
        ),
    )


def qualify_event_energy_handoff(
    *,
    meter_export: CotimedMeterExportQualification,
    cumulative_delta: CumulativeDeltaQualification,
    direct_state_raw_admitted: bool,
    complete_direct_off_event_off_boundary: bool,
) -> EventEnergyHandoff:
    gaps: list[str] = []
    if not meter_export.admitted:
        gaps.append(Q_METER_EXPORT)
    if not cumulative_delta.admitted:
        gaps.append(Q_ENERGY_SEMANTICS)
    if not direct_state_raw_admitted or not complete_direct_off_event_off_boundary:
        gaps.append(Q_DIRECT_STATE)

    gaps = list(dict.fromkeys(gaps))
    if gaps:
        return EventEnergyHandoff(
            ready=False,
            status="Q / EVENT_ENERGY_HANDOFF_BLOCKED",
            residual_gaps=tuple(gaps),
            reason=(
                "Numeric event energy requires the admitted meter/cumulative route "
                "plus one complete raw direct-state OFF-to-event-to-OFF boundary."
            ),
        )

    return EventEnergyHandoff(
        ready=True,
        status=READY_FOR_P34_EVENT_ENERGY_GATE,
        residual_gaps=(),
        reason=(
            "Meter acquisition, cumulative energy semantics and direct event "
            "identity/boundary are qualified. P34 must still validate exact boundary "
            "readings and event-window continuity."
        ),
    )


def p36_boundary() -> tuple[str, ...]:
    return (
        "COTIMED_METER_SERIES_EXISTS != DIRECT_DEFROST_EVENT_EXISTS",
        "DIRECT_DEFROST_EVENT_EXISTS != EVENT_ENERGY_IS_ADMISSIBLE",
        "NEGATIVE_HEAT_COMMON_POINT != DIRECT_NIBE_DEFROST_STATE",
        "PHPFINA_FIXED_INTERVAL_NO_AVERAGING != INTERVAL_MEAN_POWER",
        "CUMULATIVE_DELTA_ROUTE_ADMITTED != DIRECT_EVENT_IDENTITY_ADMITTED",
        "NO_NUMERIC_EVENT_KWH_WITHOUT_DIRECT_STATE_EVENT_BOUNDARY",
    )
