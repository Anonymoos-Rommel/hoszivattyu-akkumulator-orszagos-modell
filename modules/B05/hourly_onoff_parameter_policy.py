"""B05-P25 explicit HEM-default parameter policy for hourly on/off cycling."""
from __future__ import annotations
from dataclasses import dataclass

from modules.B05.hourly_cycling_method import (
    HourlyOnOffResult,
    onoff_inertia_power_kw,
)

HEM_DEFAULT_SCENARIO="HEM_DEFAULT_SCENARIO"
PRODUCT_SPECIFIC_EXPLICIT="PRODUCT_SPECIFIC_EXPLICIT"

RADIATOR_OR_UFH_WET="RADIATOR_OR_UFH_WET"
FAN_COIL="FAN_COIL"
WARM_AIR="WARM_AIR"
DHW_STORAGE="DHW_STORAGE"

HEM_FANCOIL_DIVERGENCE="Q / HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED"
TAU_EQ_POLICY_REQUIRED="Q / PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_OR_EXPLICIT_DEFAULT_POLICY_REQUIRED"

@dataclass(frozen=True)
class ParameterResolution:
    status: str
    value_s: float | None
    evidence_status: str
    reason: str=""

def resolve_tau_eq(
    *,
    policy: str | None,
    product_specific_tau_eq_s: float | None=None,
) -> ParameterResolution:
    if product_specific_tau_eq_s is not None:
        if product_specific_tau_eq_s <= 0:
            raise ValueError("product_specific_tau_eq_s must be positive")
        return ParameterResolution(
            "QUALIFIED_EXPLICIT_PRODUCT_INPUT",
            float(product_specific_tau_eq_s),
            "OBS_OR_EXPLICIT_INPUT",
            "caller must preserve the source/evidence identity of the product-specific value",
        )
    if policy == HEM_DEFAULT_SCENARIO:
        return ParameterResolution(
            "QUALIFIED_HEM_DEFAULT_SCENARIO",
            140.0,
            "POL",
            "historical UK CALCM default corroborated by current HEM reference examples; not product OBS",
        )
    return ParameterResolution(
        TAU_EQ_POLICY_REQUIRED,
        None,
        "Q",
        "no product-specific tau_eq and no explicit HEM default policy",
    )

def resolve_emitter_response_time(emitter_class: str) -> ParameterResolution:
    if emitter_class == RADIATOR_OR_UFH_WET:
        return ParameterResolution(
            "QUALIFIED_CURRENT_DOC_CODE_AGREEMENT",
            1370.0,
            "POL",
            "current HEM document and current reference code agree for bounded radiator/UFH wet class",
        )
    if emitter_class == WARM_AIR:
        return ParameterResolution(
            "QUALIFIED_CURRENT_DOC_CODE_AGREEMENT",
            120.0,
            "POL",
            "current HEM document and current reference code agree",
        )
    if emitter_class == DHW_STORAGE:
        return ParameterResolution(
            "QUALIFIED_CURRENT_DOC_CODE_AGREEMENT",
            1560.0,
            "POL",
            "current HEM document and current reference code agree",
        )
    if emitter_class == FAN_COIL:
        return ParameterResolution(
            HEM_FANCOIL_DIVERGENCE,
            None,
            "Q",
            "current HEM v3 text implies 1370 s for all wet distribution while current Rust code maps FanCoils to 360 s",
        )
    return ParameterResolution(
        "Q / UNSUPPORTED_EMITTER_CLASS",
        None,
        "Q",
        "emitter class is outside the bounded P25 mapping",
    )

@dataclass(frozen=True)
class PolicyOnOffResult:
    status: str
    onoff_inertia_power_kw: float | None
    tau_eq_s: float | None
    emitter_response_time_s: float | None
    evidence_status: str
    residual_gap: str | None

def evaluate_hourly_onoff_with_policy(
    *,
    minimum_continuous_compressor_power_kw: float,
    load_ratio: float,
    minimum_continuous_load_ratio: float,
    emitter_class: str,
    policy: str | None,
    product_specific_tau_eq_s: float | None=None,
) -> PolicyOnOffResult:
    tau=resolve_tau_eq(
        policy=policy,
        product_specific_tau_eq_s=product_specific_tau_eq_s,
    )
    emitter=resolve_emitter_response_time(emitter_class)

    if tau.value_s is None:
        return PolicyOnOffResult(
            tau.status,None,None,emitter.value_s,"Q",tau.status.removeprefix("Q / ")
        )
    if emitter.value_s is None:
        return PolicyOnOffResult(
            emitter.status,None,tau.value_s,None,"Q",emitter.status.removeprefix("Q / ")
        )

    result: HourlyOnOffResult=onoff_inertia_power_kw(
        minimum_continuous_compressor_power_kw=minimum_continuous_compressor_power_kw,
        load_ratio=load_ratio,
        minimum_continuous_load_ratio=minimum_continuous_load_ratio,
        tau_eq_s=tau.value_s,
        emitter_response_time_s=emitter.value_s,
    )
    evidence="POL" if tau.evidence_status=="POL" or emitter.evidence_status=="POL" else "DER"
    return PolicyOnOffResult(
        result.status,
        result.onoff_inertia_power_kw,
        tau.value_s,
        emitter.value_s,
        evidence,
        result.residual_gap,
    )

def p25_boundary() -> tuple[str,...]:
    return (
        "HEM_DEFAULT_POLICY_MUST_BE_EXPLICIT",
        "HEM_DEFAULT_TAU_EQ_IS_POL_NOT_PRODUCT_OBS",
        "EMITTER_CLASS_MUST_BE_EXPLICIT",
        "FANCOIL_DOC_CODE_DIVERGENCE_FAILS_CLOSED",
        "NO_DEFAULT_AS_HUNGARIAN_REGULATORY_AUTHORITY",
        "NO_DEFAULT_AS_PRODUCT_MEASUREMENT",
        "PRODUCT_SPECIFIC_TAU_EQ_OVERRIDES_DEFAULT_ONLY_WHEN_EXPLICIT",
    )
