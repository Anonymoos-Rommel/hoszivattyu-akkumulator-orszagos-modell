"""B05-P40 exact S2125 four-signal observation snapshot contract."""

from __future__ import annotations

from dataclasses import dataclass


SNAPSHOT_ADMITTED = "S2125_FOUR_SIGNAL_SAME_RESPONSE_SNAPSHOT_ADMITTED"
Q_MULTI_TIMESTAMP = "Q_S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED"


@dataclass(frozen=True)
class FourSignalSnapshotEvidence:
    exact_s2125_system: bool
    single_machine_readable_response: bool
    source_timestamp_present: bool
    bt28_raw_present: bool
    bt16_raw_present: bool
    compressor_raw_present: bool
    direct_defrost_raw_present: bool
    scaling_units_present: bool
    direct_defrost_value: int | None


@dataclass(frozen=True)
class SnapshotQualification:
    admitted: bool
    status: str
    evidence_status: str
    event_observed: bool
    timeseries_admitted: bool
    residual_gaps: tuple[str, ...]
    reason: str


def qualify_four_signal_snapshot(
    evidence: FourSignalSnapshotEvidence,
) -> SnapshotQualification:
    complete = (
        evidence.exact_s2125_system
        and evidence.single_machine_readable_response
        and evidence.source_timestamp_present
        and evidence.bt28_raw_present
        and evidence.bt16_raw_present
        and evidence.compressor_raw_present
        and evidence.direct_defrost_raw_present
        and evidence.scaling_units_present
        and evidence.direct_defrost_value in {0, 1, 2}
    )

    if not complete:
        return SnapshotQualification(
            admitted=False,
            status="Q / FOUR_SIGNAL_SNAPSHOT_INCOMPLETE",
            evidence_status="Q",
            event_observed=False,
            timeseries_admitted=False,
            residual_gaps=(Q_MULTI_TIMESTAMP,),
            reason="The same-response four-signal observation is incomplete.",
        )

    return SnapshotQualification(
        admitted=True,
        status=SNAPSHOT_ADMITTED,
        evidence_status="OBS",
        event_observed=evidence.direct_defrost_value in {1, 2},
        timeseries_admitted=False,
        residual_gaps=(Q_MULTI_TIMESTAMP,),
        reason=(
            "One exact S2125 machine-readable response contains BT28, BT16, "
            "compressor frequency and direct Defrost with source scaling. "
            "A single response remains a snapshot, not a time series."
        ),
    )


def weather_bt16_model_admissible(
    *,
    snapshot: SnapshotQualification,
    multi_timestamp_series_acquired: bool,
    validation_holdout_defined: bool,
) -> bool:
    return (
        snapshot.admitted
        and snapshot.timeseries_admitted
        and multi_timestamp_series_acquired
        and validation_holdout_defined
    )


def p40_boundary() -> tuple[str, ...]:
    return (
        "FOUR_SIGNAL_SAME_SYSTEM_OBS_SNAPSHOT_ACQUIRED != RAW_TIMESERIES_ACQUIRED",
        "RAW_TIMESERIES_ACQUIRED != WEATHER_TO_BT16_MODEL",
        "SINGLE_NONDEFROST_SNAPSHOT != DIRECT_DEFROST_EVENT",
        "UPSTREAM_CURRENT_EXPORT != UPSTREAM_HISTORY_EXPORT",
        "THIRD_PARTY_RAW_JSON_NOT_COMMITTED",
    )
