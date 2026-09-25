"""B05-P35 defrost identity source-separation contract.

Direct controller state, a heat-loss proxy, an owner screenshot and a remote
access error are different evidence classes. Only a raw timestamped direct
controller-state series can satisfy the event-identity side of the P34
event-energy admission gate.
"""

from __future__ import annotations

from dataclasses import dataclass


DIRECT_CONTROLLER_RAW = "DIRECT_CONTROLLER_RAW"
NEGATIVE_HEAT_PROXY = "NEGATIVE_HEAT_PROXY"
OWNER_VISUAL_LOG = "OWNER_VISUAL_LOG"
PUBLIC_APP_FEED = "PUBLIC_APP_FEED"
REMOTE_ACCESS_RESULT = "REMOTE_ACCESS_RESULT"

DIRECT_STATE_ADMITTED = "DIRECT_STATE_ADMITTED"
PROXY_ONLY = "PROXY_ONLY"
CONTEXT_ONLY = "CONTEXT_ONLY"
Q_RAW_EXPORT_REQUIRED = "Q_RAW_DIRECT_STATE_EXPORT_REQUIRED"

Q_OWNER_STATE_EXPORT = "Q_SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED"
Q_COTIMED_METER_EXPORT = "Q_SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED"


@dataclass(frozen=True)
class DefrostIdentityEvidence:
    source_kind: str
    exact_system_bound: bool
    raw_timestamped_series: bool
    direct_controller_semantics: bool
    state_values_explicit: bool
    public_feed_binding_proven: bool
    note: str = ""


@dataclass(frozen=True)
class DefrostIdentityQualification:
    direct_identity_admitted: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class CotimedJoinQualification:
    ready_for_p34_event_energy_gate: bool
    status: str
    residual_gaps: tuple[str, ...]
    reason: str


def qualify_defrost_identity(
    evidence: DefrostIdentityEvidence,
) -> DefrostIdentityQualification:
    """Classify one evidence source without upgrading proxies to direct state."""

    if evidence.source_kind == NEGATIVE_HEAT_PROXY:
        return DefrostIdentityQualification(
            direct_identity_admitted=False,
            status=PROXY_ONLY,
            evidence_status="DER",
            residual_gaps=(Q_OWNER_STATE_EXPORT,),
            reason=(
                "Negative thermal power can quantify heat loss under an explicit "
                "meter/sign boundary but cannot identify a NIBE controller defrost "
                "state by itself."
            ),
        )

    if evidence.source_kind == OWNER_VISUAL_LOG:
        return DefrostIdentityQualification(
            direct_identity_admitted=False,
            status=CONTEXT_ONLY,
            evidence_status="OBS",
            residual_gaps=(Q_OWNER_STATE_EXPORT,),
            reason=(
                "Owner visual/log evidence can establish that direct defrost state "
                "is observed in the field, but a screenshot or narrative is not a "
                "raw timestamped state series."
            ),
        )

    if evidence.source_kind == REMOTE_ACCESS_RESULT:
        return DefrostIdentityQualification(
            direct_identity_admitted=False,
            status=CONTEXT_ONLY,
            evidence_status="OBS",
            residual_gaps=(Q_OWNER_STATE_EXPORT, Q_COTIMED_METER_EXPORT),
            reason=(
                "HTTP access success/failure describes the retrieval path only and "
                "cannot establish presence or absence of the underlying source data."
            ),
        )

    if evidence.source_kind in {PUBLIC_APP_FEED, DIRECT_CONTROLLER_RAW}:
        if evidence.source_kind == PUBLIC_APP_FEED and not evidence.public_feed_binding_proven:
            return DefrostIdentityQualification(
                direct_identity_admitted=False,
                status=Q_RAW_EXPORT_REQUIRED,
                evidence_status="Q",
                residual_gaps=(Q_OWNER_STATE_EXPORT,),
                reason=(
                    "A public app feed cannot be treated as direct NIBE state unless "
                    "the feed-to-controller-state binding is explicitly proven."
                ),
            )

        if (
            evidence.exact_system_bound
            and evidence.raw_timestamped_series
            and evidence.direct_controller_semantics
            and evidence.state_values_explicit
        ):
            return DefrostIdentityQualification(
                direct_identity_admitted=True,
                status=DIRECT_STATE_ADMITTED,
                evidence_status="OBS",
                residual_gaps=(),
                reason=(
                    "Raw timestamped same-system controller state with explicit state "
                    "semantics is admissible as direct event identity, independent "
                    "of whether the bound raw feed is public or owner-exported."
                ),
            )
        return DefrostIdentityQualification(
            direct_identity_admitted=False,
            status=Q_RAW_EXPORT_REQUIRED,
            evidence_status="Q",
            residual_gaps=(Q_OWNER_STATE_EXPORT,),
            reason=(
                "Direct-state semantics exist, but exact system binding, raw "
                "timestamps or explicit state values are incomplete."
            ),
        )

    return DefrostIdentityQualification(
        direct_identity_admitted=False,
        status=Q_RAW_EXPORT_REQUIRED,
        evidence_status="Q",
        residual_gaps=(Q_OWNER_STATE_EXPORT,),
        reason="Unrecognized or insufficient defrost-identity evidence source.",
    )


def qualify_cotimed_join(
    *,
    direct_state: DefrostIdentityQualification,
    electric_raw_obs: bool,
    thermal_raw_obs: bool,
    same_system: bool,
    common_timebase: bool,
    meter_boundaries_explicit: bool,
) -> CotimedJoinQualification:
    """Gate the handoff from P35 source identity into the P34 energy contract."""

    gaps: list[str] = []
    if not direct_state.direct_identity_admitted:
        gaps.append(Q_OWNER_STATE_EXPORT)
    if not electric_raw_obs or not thermal_raw_obs:
        gaps.append(Q_COTIMED_METER_EXPORT)
    if not same_system or not common_timebase or not meter_boundaries_explicit:
        gaps.append(Q_COTIMED_METER_EXPORT)

    gaps = list(dict.fromkeys(gaps))
    if gaps:
        return CotimedJoinQualification(
            ready_for_p34_event_energy_gate=False,
            status="Q / OWNER_EXPORT_AND_JOIN_INCOMPLETE",
            residual_gaps=tuple(gaps),
            reason=(
                "P34 event-energy admission requires admitted direct state plus raw "
                "same-system electrical/thermal observations on a common timebase "
                "with explicit meter boundaries."
            ),
        )

    return CotimedJoinQualification(
        ready_for_p34_event_energy_gate=True,
        status="READY_FOR_P34_EVENT_ENERGY_GATE",
        residual_gaps=(),
        reason=(
            "Source identity and raw meter-series prerequisites are complete; the "
            "actual event must still pass the P34 complete-event interval gate."
        ),
    )


def p35_boundary() -> tuple[str, ...]:
    return (
        "NEGATIVE_HEAT_PROXY != DIRECT_NIBE_DEFROST_STATE",
        "OWNER_SCREENSHOT_OR_VISUAL_LOG != RAW_STATE_SERIES",
        "PUBLIC_APP_CONFIG_FEED != OWNER_CUSTOM_MODBUS_FEED",
        "REMOTE_HTTP_403 != SOURCE_ABSENCE",
        "TECHNICAL_ACQUISITION_PATH_EXISTS != ACQUIRED_JOINED_SERIES",
        "DIRECT_RAW_STATE_EXPORT_PLUS_COTIMED_METER_EXPORT_REQUIRED",
    )
