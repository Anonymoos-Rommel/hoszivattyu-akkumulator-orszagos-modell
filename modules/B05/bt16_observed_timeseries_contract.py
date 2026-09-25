"""B05-P39 observed S2125 BT16 acquisition contract."""

from __future__ import annotations

from dataclasses import dataclass


Q_RAW_SERIES = "Q_S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED"

DIRECT_MODBUS = "DIRECT_MODBUS"
USB_RAW_LOG = "USB_RAW_LOG"
RAW_INFLUX = "RAW_INFLUX"
MYUPLINK_HISTORY = "MYUPLINK_HISTORY"
GRAPH_ONLY = "GRAPH_ONLY"
PUBLIC_WEATHER_ONLY = "PUBLIC_WEATHER_ONLY"

ROUTE_QUALIFIED = "S2125_BT16_ACQUISITION_ROUTE_QUALIFIED"
RAW_SERIES_ADMITTED = "S2125_RAW_BT16_OBS_SERIES_ADMITTED"


@dataclass(frozen=True)
class Bt16AcquisitionEvidence:
    source_kind: str
    exact_s2125_system: bool
    timestamped_bt28: bool
    timestamped_bt16: bool
    compressor_state_or_frequency: bool
    direct_defrost_0_1_2: bool
    common_timebase: bool
    source_native_cadence_known: bool
    scaling_units_known: bool
    unknown_aggregation: bool
    machine_readable_rows: bool


@dataclass(frozen=True)
class Bt16AcquisitionQualification:
    admitted: bool
    route_qualified: bool
    status: str
    evidence_status: str
    residual_gaps: tuple[str, ...]
    reason: str


def qualify_bt16_acquisition(
    evidence: Bt16AcquisitionEvidence,
) -> Bt16AcquisitionQualification:
    route_allowed = evidence.source_kind in {
        DIRECT_MODBUS,
        USB_RAW_LOG,
        RAW_INFLUX,
    }

    if not route_allowed:
        return Bt16AcquisitionQualification(
            admitted=False,
            route_qualified=False,
            status="Q / SOURCE_ROUTE_NOT_ADMISSIBLE",
            evidence_status="Q",
            residual_gaps=(Q_RAW_SERIES,),
            reason=(
                "Weather-only feeds, graph-only evidence and history with "
                "unproven raw timing semantics cannot substitute for BT16 telemetry."
            ),
        )

    route_qualified = (
        evidence.exact_s2125_system
        and evidence.source_native_cadence_known
        and evidence.scaling_units_known
        and not evidence.unknown_aggregation
    )
    if not route_qualified:
        return Bt16AcquisitionQualification(
            admitted=False,
            route_qualified=False,
            status="Q / ROUTE_METADATA_INCOMPLETE",
            evidence_status="Q",
            residual_gaps=(Q_RAW_SERIES,),
            reason=(
                "Exact system identity, cadence, units/scaling and aggregation "
                "semantics are required before an acquisition route is qualified."
            ),
        )

    complete = (
        evidence.timestamped_bt28
        and evidence.timestamped_bt16
        and evidence.compressor_state_or_frequency
        and evidence.direct_defrost_0_1_2
        and evidence.common_timebase
        and evidence.machine_readable_rows
    )
    if not complete:
        return Bt16AcquisitionQualification(
            admitted=False,
            route_qualified=True,
            status=ROUTE_QUALIFIED,
            evidence_status="DER",
            residual_gaps=(Q_RAW_SERIES,),
            reason=(
                "The source route is qualified, but the complete same-system "
                "BT28+BT16+compressor+Defrost row set has not been acquired."
            ),
        )

    return Bt16AcquisitionQualification(
        admitted=True,
        route_qualified=True,
        status=RAW_SERIES_ADMITTED,
        evidence_status="OBS",
        residual_gaps=(),
        reason=(
            "Exact S2125 machine-readable rows co-time BT28, BT16, compressor "
            "state/frequency and direct Defrost 0/1/2 with known cadence and units."
        ),
    )


def weather_to_bt16_model_admissible(
    *,
    observed_series: Bt16AcquisitionQualification,
    weather_covariates_joined: bool,
    validation_holdout_defined: bool,
) -> bool:
    return (
        observed_series.admitted
        and weather_covariates_joined
        and validation_holdout_defined
    )


def p39_boundary() -> tuple[str, ...]:
    return (
        "AMBIENT_T_RH != BT16_EVAPORATOR_STATE",
        "OUTSIDE_TEMPERATURE_FEED != WEATHER_TO_BT16_MAPPING",
        "HISTORY_GRAPH != RAW_SOURCE_TIMESERIES",
        "20S_GROUPED_GRAFANA_STATE != RAW_BT16_TRANSIENT_SERIES",
        "DIRECT_MODBUS_OR_USB_OR_RAW_INFLUX = QUALIFIED_ACQUISITION_ROUTE",
        "QUALIFIED_ACQUISITION_ROUTE != ACQUIRED_OBS_SERIES",
        "NO_WEATHER_TO_BT16_MODEL_WITHOUT_OBS_SERIES_AND_HOLDOUT",
    )
