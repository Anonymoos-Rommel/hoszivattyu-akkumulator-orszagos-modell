"""B05-P38 bounded public S2125 direct-event acquisition contract."""

from __future__ import annotations

from dataclasses import dataclass


Q_COMPLETE_EVENT_PACKAGE = "Q_S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED"
PUBLIC_FLEET_AUDIT_BOUNDED = "PUBLIC_FLEET_AUDIT_BOUNDED_NO_DIRECT_EVENT_EXPOSED"
COMPLETE_EVENT_PACKAGE_ADMITTED = "COMPLETE_S2125_DIRECT_EVENT_PACKAGE_ADMITTED"


@dataclass(frozen=True)
class PublicFleetAuditEvidence:
    public_system_count: int
    s2125_system_ids: tuple[int, ...]
    audited_system_ids: tuple[int, ...]
    direct_candidate_counts: tuple[int, ...]
    energy_keys_present_for_all: bool
    underlying_public_routes_audited: bool


@dataclass(frozen=True)
class PublicFleetAuditQualification:
    complete_public_event_acquired: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    global_absence_proven: bool
    reason: str


@dataclass(frozen=True)
class CompleteEventPackageEvidence:
    exact_s2125_system: bool
    raw_timestamped_direct_state: bool
    state_values_subset_0_1_2: bool
    complete_off_event_off_boundary: bool
    electric_energy_observed: bool
    thermal_energy_observed: bool
    common_timebase: bool
    machine_readable: bool


@dataclass(frozen=True)
class CompleteEventPackageQualification:
    admitted: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


def qualify_public_fleet_audit(
    evidence: PublicFleetAuditEvidence,
) -> PublicFleetAuditQualification:
    ids_match = (
        len(evidence.s2125_system_ids) > 0
        and tuple(sorted(evidence.s2125_system_ids))
        == tuple(sorted(evidence.audited_system_ids))
    )
    counts_match = (
        len(evidence.direct_candidate_counts) == len(evidence.audited_system_ids)
        and all(count == 0 for count in evidence.direct_candidate_counts)
    )
    if (
        evidence.public_system_count > 0
        and ids_match
        and counts_match
        and evidence.energy_keys_present_for_all
        and evidence.underlying_public_routes_audited
    ):
        return PublicFleetAuditQualification(
            complete_public_event_acquired=False,
            status=PUBLIC_FLEET_AUDIT_BOUNDED,
            evidence_status="DER",
            residual_gaps=(Q_COMPLETE_EVENT_PACKAGE,),
            global_absence_proven=False,
            reason=(
                "Every currently identified public S2125 HeatpumpMonitor surface "
                "was audited and none exposed direct-state timeseries. This is a "
                "bounded public-surface result, never proof of global absence."
            ),
        )

    return PublicFleetAuditQualification(
        complete_public_event_acquired=False,
        status="Q / PUBLIC_FLEET_AUDIT_INCOMPLETE",
        evidence_status="Q",
        residual_gaps=(Q_COMPLETE_EVENT_PACKAGE,),
        global_absence_proven=False,
        reason="The current public S2125 fleet audit is incomplete.",
    )


def qualify_complete_event_package(
    evidence: CompleteEventPackageEvidence,
) -> CompleteEventPackageQualification:
    if (
        evidence.exact_s2125_system
        and evidence.raw_timestamped_direct_state
        and evidence.state_values_subset_0_1_2
        and evidence.complete_off_event_off_boundary
        and evidence.electric_energy_observed
        and evidence.thermal_energy_observed
        and evidence.common_timebase
        and evidence.machine_readable
    ):
        return CompleteEventPackageQualification(
            admitted=True,
            status=COMPLETE_EVENT_PACKAGE_ADMITTED,
            evidence_status="OBS",
            residual_gaps=(),
            reason=(
                "One exact S2125 system supplies a machine-readable complete "
                "direct-state event and same-system electric/thermal energy on "
                "a common timebase."
            ),
        )

    return CompleteEventPackageQualification(
        admitted=False,
        status="Q / COMPLETE_DIRECT_EVENT_PACKAGE_NOT_ADMITTED",
        evidence_status="Q",
        residual_gaps=(Q_COMPLETE_EVENT_PACKAGE,),
        reason=(
            "Exact system identity, raw direct 0/1/2 state, complete event "
            "boundary, same-system electric/thermal energy and common timebase "
            "are jointly mandatory."
        ),
    )


def p38_boundary() -> tuple[str, ...]:
    return (
        "PUBLIC_FLEET_SCAN_WITH_ZERO_DIRECT_FEEDS != GLOBAL_SOURCE_ABSENCE",
        "FORUM_HISTORY_GRAPH != RAW_MACHINE_READABLE_EXPORT",
        "DIRECT_STATE_HISTORY_EXISTS != COMPLETE_EVENT_ENERGY_PACKAGE_EXISTS",
        "STATE_FROM_SYSTEM_A + ENERGY_FROM_SYSTEM_B != ADMISSIBLE_EVENT_ENERGY",
        "PUBLIC_ACQUISITION_ATTACK_COMPLETE -> NEXT_PRIORITY_WEATHER_TO_BT16",
    )
