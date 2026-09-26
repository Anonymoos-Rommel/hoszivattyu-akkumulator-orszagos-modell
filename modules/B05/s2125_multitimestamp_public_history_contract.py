"""B05-P41 exact S2125 multi-timestamp public-history acquisition boundary."""

from __future__ import annotations

from dataclasses import dataclass


Q_MULTI_TIMESTAMP = "Q_S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED"
RAW_SERIES_ADMITTED = "S2125_RAW_MULTI_TIMESTAMP_FOUR_SIGNAL_SERIES_ADMITTED"


@dataclass(frozen=True)
class PublicHistoryEvidence:
    exact_s2125_system: bool
    owner_side_history_proven: bool
    public_machine_readable_rows: bool
    multiple_timestamps: bool
    bt28_present: bool
    bt16_present: bool
    compressor_present: bool
    direct_defrost_present: bool
    common_timebase: bool
    cadence_known: bool
    scaling_units_known: bool
    unknown_aggregation: bool


@dataclass(frozen=True)
class PublicHistoryQualification:
    admitted: bool
    owner_history_proven: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


def qualify_public_history(
    evidence: PublicHistoryEvidence,
) -> PublicHistoryQualification:
    owner_history = evidence.exact_s2125_system and evidence.owner_side_history_proven

    complete_public = (
        owner_history
        and evidence.public_machine_readable_rows
        and evidence.multiple_timestamps
        and evidence.bt28_present
        and evidence.bt16_present
        and evidence.compressor_present
        and evidence.direct_defrost_present
        and evidence.common_timebase
        and evidence.cadence_known
        and evidence.scaling_units_known
        and not evidence.unknown_aggregation
    )

    if complete_public:
        return PublicHistoryQualification(
            admitted=True,
            owner_history_proven=True,
            status=RAW_SERIES_ADMITTED,
            evidence_status="OBS",
            residual_gaps=(),
            reason=(
                "One exact S2125 public machine-readable multi-timestamp series "
                "contains BT28, BT16, compressor and direct Defrost on a common "
                "timebase with explicit cadence and scaling."
            ),
        )

    if (
        owner_history
        and evidence.public_machine_readable_rows
        and evidence.multiple_timestamps
    ):
        return PublicHistoryQualification(
            admitted=False,
            owner_history_proven=True,
            status="PUBLIC_RAW_S2125_ROWS_ACQUIRED_TARGET_FOUR_SIGNAL_SERIES_INCOMPLETE",
            evidence_status="OBS",
            residual_gaps=(Q_MULTI_TIMESTAMP,),
            reason=(
                "Exact S2125 public source-native multi-timestamp rows are acquired, "
                "but the published channel set does not contain the complete required "
                "BT28 + BT16 + compressor + direct Defrost series with all admission semantics."
            ),
        )

    if owner_history:
        return PublicHistoryQualification(
            admitted=False,
            owner_history_proven=True,
            status="OWNER_LOCAL_HISTORY_PROVEN_PUBLIC_RAW_SERIES_NOT_ACQUIRED",
            evidence_status="DER",
            residual_gaps=(Q_MULTI_TIMESTAMP,),
            reason=(
                "Exact S2125 owner-side history is proven, but the complete raw "
                "four-signal public row set has not been acquired."
            ),
        )

    return PublicHistoryQualification(
        admitted=False,
        owner_history_proven=False,
        status="Q / EXACT_OWNER_HISTORY_NOT_PROVEN",
        evidence_status="Q",
        residual_gaps=(Q_MULTI_TIMESTAMP,),
        reason="Neither an exact owner history nor a complete public raw series is proven.",
    )


def public_graph_admissible_as_raw_series(*, grouped_or_visual_only: bool) -> bool:
    return not grouped_or_visual_only


def viewer_offer_admissible_as_public_data(*, public_link_or_export_present: bool) -> bool:
    return public_link_or_export_present


def p41_boundary() -> tuple[str, ...]:
    return (
        "EXACT_S2125_MULTI_TIMESTAMP_HISTORY_EXISTS != PUBLIC_RAW_FOUR_SIGNAL_SERIES_ACQUIRED",
        "PUBLIC_GRAPH_OR_QUERY != RAW_SOURCE_ROWS",
        "CSV_EXPORT_CAPABILITY != PUBLIC_CSV_ACQUIRED",
        "READ_ONLY_VIEWER_OFFER != PUBLIC_DATA_ACCESS",
        "PUBLIC_RAW_OTHER_CHANNEL_S2125_TIMESERIES != PUBLIC_RAW_TARGET_FOUR_SIGNAL_SERIES",
        "OWNER_SIDE_COMPLETE_FOUR_SIGNAL_HISTORY != PUBLIC_RAW_FOUR_SIGNAL_SERIES_ACQUIRED",
        "BOUNDED_PUBLIC_TARGET_EXPORT_SEARCH_EXHAUSTED != GLOBAL_SOURCE_ABSENCE",
        "BOUNDED_PUBLIC_AUDIT_NO_EXPORT_FOUND != GLOBAL_SOURCE_ABSENCE",
    )
