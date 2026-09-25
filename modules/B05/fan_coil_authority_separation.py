"""B05-P31 fan-coil HEM policy/observation authority separation.

The current HEM technical document and current official reference
implementation disagree on the fan-coil emitter response-time class.  P31 does
not reconcile the sources.  Instead it makes each policy authority explicit
and keeps a separate evidence path for physical emitter observations.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.B05.hourly_cycling_method import onoff_inertia_power_kw
from modules.B05.hourly_onoff_parameter_policy import resolve_tau_eq

HEM_TP12_V3_DOCUMENT_POLICY = "HEM_TP12_V3_DOCUMENT_POLICY"
HEM_REFERENCE_CODE_5A3AC972 = "HEM_REFERENCE_CODE_5A3AC972"

DOCUMENT_POLICY_RESPONSE_TIME_S = 1370.0
REFERENCE_CODE_RESPONSE_TIME_S = 360.0

Q_AUTHORITY_OR_OBS_REQUIRED = "Q / FANCOIL_AUTHORITY_SELECTION_OR_OBS_EVIDENCE_REQUIRED"
Q_OBS_SOURCE_ID_REQUIRED = "Q / FANCOIL_OBS_EMITTER_RESPONSE_SOURCE_ID_REQUIRED"
Q_MIXED_POL_OBS_AUTHORITY = "Q / MIXED_FANCOIL_POL_OBS_AUTHORITY_NOT_ALLOWED"
Q_UNSUPPORTED_AUTHORITY = "Q / UNSUPPORTED_FANCOIL_AUTHORITY"

UPSTREAM_DIVERGENCE_FACT = "CONFIRMED_CURRENT_DIVERGENCE"
GOVERNANCE_TRANSITION = "RESOLVED_BY_AUTHORITY_SEPARATION_NO_SILENT_SELECTION"


@dataclass(frozen=True)
class FanCoilResponseResolution:
    status: str
    value_s: float | None
    evidence_status: str
    authority: str | None
    source_id: str | None
    reason: str


@dataclass(frozen=True)
class FanCoilOnOffResult:
    status: str
    onoff_inertia_power_kw: float | None
    tau_eq_s: float | None
    emitter_response_time_s: float | None
    evidence_status: str
    fan_coil_authority: str | None
    residual_gap: str | None


def resolve_fan_coil_response_time(
    *,
    authority: str | None = None,
    obs_response_time_s: float | None = None,
    obs_source_id: str | None = None,
) -> FanCoilResponseResolution:
    """Resolve one explicit fan-coil response-time authority.

    Policy branches reproduce source-specific HEM behavior and remain POL.
    Physical OBS input is admitted only with an explicit source identity.
    Mixing an OBS input with a HEM policy authority in one call fails closed.
    """

    if obs_response_time_s is not None:
        if obs_response_time_s <= 0:
            raise ValueError("obs_response_time_s must be positive")
        if authority is not None:
            return FanCoilResponseResolution(
                Q_MIXED_POL_OBS_AUTHORITY,
                None,
                "Q",
                None,
                None,
                "Select either a HEM policy-reproduction branch or an explicit OBS emitter record, not both.",
            )
        if not obs_source_id:
            return FanCoilResponseResolution(
                Q_OBS_SOURCE_ID_REQUIRED,
                None,
                "Q",
                None,
                None,
                "An explicit physical response time requires exact source identity.",
            )
        return FanCoilResponseResolution(
            "QUALIFIED_EXPLICIT_FANCOIL_OBS_RESPONSE_TIME",
            float(obs_response_time_s),
            "OBS",
            "EXPLICIT_EMITTER_OR_LAB_RECORD",
            obs_source_id,
            "Exact source-bound emitter response time; independent of HEM document/code policy divergence.",
        )

    if authority == HEM_TP12_V3_DOCUMENT_POLICY:
        return FanCoilResponseResolution(
            "QUALIFIED_HEM_TP12_V3_DOCUMENT_POLICY",
            DOCUMENT_POLICY_RESPONSE_TIME_S,
            "POL",
            HEM_TP12_V3_DOCUMENT_POLICY,
            "SRC-B05-UK-HEM-TP12-HOURLY-ONOFF-2026",
            "HEM-TP-12 v3 assigns Light embedded to all heat pumps with wet distribution.",
        )

    if authority == HEM_REFERENCE_CODE_5A3AC972:
        return FanCoilResponseResolution(
            "QUALIFIED_HEM_REFERENCE_CODE_5A3AC972",
            REFERENCE_CODE_RESPONSE_TIME_S,
            "POL",
            HEM_REFERENCE_CODE_5A3AC972,
            "SRC-B05-UK-HEM-RUST-ONOFF-CONSTANTS-2026",
            "Pinned current official reference code maps FanCoils to 360 s.",
        )

    if authority is not None:
        return FanCoilResponseResolution(
            Q_UNSUPPORTED_AUTHORITY,
            None,
            "Q",
            authority,
            None,
            "The requested authority is outside the bounded P31 mapping.",
        )

    return FanCoilResponseResolution(
        Q_AUTHORITY_OR_OBS_REQUIRED,
        None,
        "Q",
        None,
        None,
        "P31 forbids silently selecting either 1370 s or 360 s for fan coils.",
    )


def evaluate_fan_coil_onoff(
    *,
    minimum_continuous_compressor_power_kw: float,
    load_ratio: float,
    minimum_continuous_load_ratio: float,
    tau_policy: str | None,
    product_specific_tau_eq_s: float | None = None,
    fan_coil_authority: str | None = None,
    obs_emitter_response_time_s: float | None = None,
    obs_emitter_source_id: str | None = None,
) -> FanCoilOnOffResult:
    """Evaluate P24 inertia only after both tau_eq and fan-coil authority resolve."""

    tau = resolve_tau_eq(
        policy=tau_policy,
        product_specific_tau_eq_s=product_specific_tau_eq_s,
    )
    emitter = resolve_fan_coil_response_time(
        authority=fan_coil_authority,
        obs_response_time_s=obs_emitter_response_time_s,
        obs_source_id=obs_emitter_source_id,
    )

    if tau.value_s is None:
        return FanCoilOnOffResult(
            tau.status,
            None,
            None,
            emitter.value_s,
            "Q",
            emitter.authority,
            tau.status.removeprefix("Q / "),
        )

    if emitter.value_s is None:
        return FanCoilOnOffResult(
            emitter.status,
            None,
            tau.value_s,
            None,
            "Q",
            emitter.authority,
            emitter.status.removeprefix("Q / "),
        )

    result = onoff_inertia_power_kw(
        minimum_continuous_compressor_power_kw=minimum_continuous_compressor_power_kw,
        load_ratio=load_ratio,
        minimum_continuous_load_ratio=minimum_continuous_load_ratio,
        tau_eq_s=tau.value_s,
        emitter_response_time_s=emitter.value_s,
    )

    if tau.evidence_status == "POL" or emitter.evidence_status == "POL":
        evidence = "POL"
    else:
        evidence = "DER_FROM_EXPLICIT_PHYSICAL_INPUTS"

    return FanCoilOnOffResult(
        result.status,
        result.onoff_inertia_power_kw,
        tau.value_s,
        emitter.value_s,
        evidence,
        emitter.authority,
        result.residual_gap,
    )


def p31_boundary() -> tuple[str, ...]:
    return (
        "UPSTREAM_DOC_CODE_DIVERGENCE_IS_PRESERVED",
        "DOCUMENT_POLICY_1370_IS_POL_NOT_OBS",
        "REFERENCE_CODE_360_IS_POL_NOT_OBS",
        "NO_SILENT_FANCOIL_POLICY_SELECTION",
        "OBS_EMITTER_RESPONSE_REQUIRES_EXPLICIT_SOURCE_ID",
        "OBS_PATH_DOES_NOT_REQUIRE_UPSTREAM_HEM_RECONCILIATION",
        "PRODUCT_TAU_EQ_REMAINS_SEPARATE",
    )
