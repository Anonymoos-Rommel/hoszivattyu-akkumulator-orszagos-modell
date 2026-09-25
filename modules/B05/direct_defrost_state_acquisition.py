"""B05-P37 direct S2125 defrost-state acquisition boundary."""

from __future__ import annotations

from dataclasses import dataclass


Q_PRIVATE_EXPORT = (
    "Q_SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED"
)

PUBLIC_SURFACE_NO_DIRECT_STATE_ACQUIRED = (
    "PUBLIC_SURFACE_NO_DIRECT_STATE_ACQUIRED"
)
CROSS_SYSTEM_LOGGING_FEASIBLE = "CROSS_SYSTEM_DIRECT_STATE_LOGGING_FEASIBLE"
EXACT_DIRECT_STATE_ADMITTED = "EXACT_DIRECT_STATE_ADMITTED"


@dataclass(frozen=True)
class PublicDirectStateSurfaceEvidence:
    public_feed_count: int
    targeted_candidate_count: int
    candidate_operation_mode_values: tuple[int, ...]
    public_input_names: tuple[str, ...]
    direct_state_feed_bound: bool
    direct_state_input_bound: bool
    owner_private_direct_state_context: bool


@dataclass(frozen=True)
class PublicSurfaceQualification:
    direct_state_admitted: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class CrossSystemLoggingEvidence:
    official_direct_register_bound: bool
    direct_state_values_explicit: bool
    real_history_pipeline_documented: bool
    exact_silkeborg_system: bool


@dataclass(frozen=True)
class CrossSystemLoggingQualification:
    exact_event_admitted: bool
    logging_feasibility_proven: bool
    status: str
    residual_gaps: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class RawDirectStateExportEvidence:
    exact_silkeborg_system: bool
    raw_timestamped: bool
    official_or_explicit_direct_state_binding: bool
    values_subset_0_1_2: bool
    complete_off_event_off_boundary: bool


@dataclass(frozen=True)
class RawDirectStateQualification:
    admitted: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


def qualify_public_surface(
    evidence: PublicDirectStateSurfaceEvidence,
) -> PublicSurfaceQualification:
    """Audit the public surface without generalizing into private HA absence."""

    operation_mode_is_prioritisation = (
        len(evidence.candidate_operation_mode_values) > 0
        and set(evidence.candidate_operation_mode_values).issubset({10, 20, 30, 40, 60})
    )

    if evidence.direct_state_feed_bound or evidence.direct_state_input_bound:
        return PublicSurfaceQualification(
            direct_state_admitted=False,
            status="PUBLIC_DIRECT_STATE_CANDIDATE_REQUIRES_RAW_SERIES_QUALIFICATION",
            evidence_status="Q",
            residual_gaps=(Q_PRIVATE_EXPORT,),
            reason=(
                "A named public candidate is not admitted until raw timestamps, "
                "exact direct-state binding and 0/1/2 values are proven."
            ),
        )

    if (
        evidence.public_feed_count > 0
        and evidence.targeted_candidate_count >= 0
        and len(evidence.public_input_names) > 0
        and operation_mode_is_prioritisation
        and evidence.owner_private_direct_state_context
    ):
        return PublicSurfaceQualification(
            direct_state_admitted=False,
            status=PUBLIC_SURFACE_NO_DIRECT_STATE_ACQUIRED,
            evidence_status="DER",
            residual_gaps=(Q_PRIVATE_EXPORT,),
            reason=(
                "The audited public EmonCMS surface did not yield direct Defrost "
                "state. Operation Mode is prioritisation, while owner evidence keeps "
                "private Home Assistant history as a separate possible source."
            ),
        )

    return PublicSurfaceQualification(
        direct_state_admitted=False,
        status="Q / PUBLIC_SURFACE_INCOMPLETE",
        evidence_status="Q",
        residual_gaps=(Q_PRIVATE_EXPORT,),
        reason="The bounded public-surface audit is incomplete.",
    )


def qualify_cross_system_logging(
    evidence: CrossSystemLoggingEvidence,
) -> CrossSystemLoggingQualification:
    """Separate real S2125 acquisition feasibility from exact-system evidence."""

    feasible = (
        evidence.official_direct_register_bound
        and evidence.direct_state_values_explicit
        and evidence.real_history_pipeline_documented
    )
    if feasible and not evidence.exact_silkeborg_system:
        return CrossSystemLoggingQualification(
            exact_event_admitted=False,
            logging_feasibility_proven=True,
            status=CROSS_SYSTEM_LOGGING_FEASIBLE,
            residual_gaps=(Q_PRIVATE_EXPORT,),
            reason=(
                "A real S2125 direct-state history pipeline proves acquisition "
                "feasibility but cannot identify an event on the Silkeborg system."
            ),
        )
    if feasible and evidence.exact_silkeborg_system:
        return CrossSystemLoggingQualification(
            exact_event_admitted=False,
            logging_feasibility_proven=True,
            status="EXACT_SYSTEM_LOGGING_ROUTE_EXISTS_RAW_EVENT_STILL_REQUIRED",
            residual_gaps=(Q_PRIVATE_EXPORT,),
            reason="Exact-system route exists but a raw complete event is still required.",
        )
    return CrossSystemLoggingQualification(
        exact_event_admitted=False,
        logging_feasibility_proven=False,
        status="Q / DIRECT_STATE_LOGGING_FEASIBILITY_NOT_PROVEN",
        residual_gaps=(Q_PRIVATE_EXPORT,),
        reason="Direct-state historical logging feasibility is not yet proven.",
    )


def qualify_raw_direct_state(
    evidence: RawDirectStateExportEvidence,
) -> RawDirectStateQualification:
    """Only one exact complete raw 0/1/2 event closes identity."""

    if (
        evidence.exact_silkeborg_system
        and evidence.raw_timestamped
        and evidence.official_or_explicit_direct_state_binding
        and evidence.values_subset_0_1_2
        and evidence.complete_off_event_off_boundary
    ):
        return RawDirectStateQualification(
            admitted=True,
            status=EXACT_DIRECT_STATE_ADMITTED,
            evidence_status="OBS",
            residual_gaps=(),
            reason=(
                "Exact-system raw timestamped direct Defrost state contains a "
                "complete OFF-to-ACTIVE/PASSIVE-to-OFF boundary."
            ),
        )

    return RawDirectStateQualification(
        admitted=False,
        status="Q / EXACT_RAW_DIRECT_STATE_EVENT_REQUIRED",
        evidence_status="Q",
        residual_gaps=(Q_PRIVATE_EXPORT,),
        reason=(
            "Exact system identity, raw timestamps, explicit direct-state binding, "
            "0/1/2 values and a complete event boundary are all mandatory."
        ),
    )


def p37_boundary() -> tuple[str, ...]:
    return (
        "OPERATION_PRIORITISATION_10_20_30 != DIRECT_DEFROST_STATE_0_1_2",
        "PUBLIC_EMONCMS_SURFACE_AUDIT != PRIVATE_HOME_ASSISTANT_HISTORY_ABSENCE",
        "CROSS_SYSTEM_S2125_DIRECT_STATE_LOGGING != EXACT_SILKEBORG_RAW_EVENT",
        "TECHNICAL_ACQUISITION_FEASIBILITY != ACQUIRED_EXACT_EVENT_SERIES",
        "PRIVATE_HA_HISTORY_OR_NEW_1805_LOGGER_EXPORT_REQUIRED",
    )
