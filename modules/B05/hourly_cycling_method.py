"""B05-P24 hourly cycling method separation.

EN14825/DEAP Cdh is retained as an exact-bin standard-method validation track.
Generic hourly B05 runtime uses a separate on/off-transient method and never
interpolates Cdh across outdoor temperature.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

NO_EXACT_CDH_BIN="Q / NO_EXACT_CDH_BIN"
HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED="HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED"
QUALIFIED_HOURLY_ONOFF_METHOD="QUALIFIED_HOURLY_ONOFF_METHOD"

@dataclass(frozen=True)
class ExactCdhBinResult:
    status: str
    cdh: float | None
    reason: str=""

def exact_cdh_bin_lookup(outdoor_temperature_c: float, bins: Mapping[float,float], *, tolerance: float=1e-9) -> ExactCdhBinResult:
    for tj,cdh in bins.items():
        if not (0 < cdh <= 1):
            raise ValueError("Cdh values must be in (0,1]")
        if abs(outdoor_temperature_c-float(tj)) <= tolerance:
            return ExactCdhBinResult("OBS / EXACT_CDH_BIN",float(cdh))
    return ExactCdhBinResult(NO_EXACT_CDH_BIN,None,"Cdh interpolation/nearest-bin mapping is not authorized for generic hourly runtime")

@dataclass(frozen=True)
class HourlyOnOffResult:
    status: str
    onoff_inertia_power_kw: float | None
    residual_gap: str | None

def onoff_inertia_power_kw(
    *,
    minimum_continuous_compressor_power_kw: float,
    load_ratio: float,
    minimum_continuous_load_ratio: float,
    tau_eq_s: float | None,
    emitter_response_time_s: float | None,
) -> HourlyOnOffResult:
    if minimum_continuous_compressor_power_kw <= 0:
        raise ValueError("minimum continuous compressor power must be positive")
    if not (0 < load_ratio < 1):
        raise ValueError("load_ratio must be in (0,1)")
    if not (0 < minimum_continuous_load_ratio <= 1):
        raise ValueError("minimum_continuous_load_ratio must be in (0,1]")
    if load_ratio >= minimum_continuous_load_ratio:
        return HourlyOnOffResult("CONTINUOUS / NO_ONOFF_INERTIA_TERM",0.0,None)

    if tau_eq_s is None or emitter_response_time_s is None:
        return HourlyOnOffResult(
            "Q / "+HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED,
            None,
            HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED,
        )
    if tau_eq_s <= 0 or emitter_response_time_s <= 0:
        raise ValueError("transient time parameters must be positive")

    penalty=minimum_continuous_compressor_power_kw * tau_eq_s * load_ratio * (1.0-load_ratio) / emitter_response_time_s
    return HourlyOnOffResult(QUALIFIED_HOURLY_ONOFF_METHOD,penalty,None)

def p24_boundary() -> tuple[str,...]:
    return (
        "EN14825_CDH_IS_EXACT_BIN_STANDARD_METHOD_EVIDENCE",
        "NO_CDH_TEMPERATURE_INTERPOLATION_FOR_GENERIC_HOURLY_RUNTIME",
        "NO_NEAREST_CDH_BIN_FOR_GENERIC_HOURLY_RUNTIME",
        "HOURLY_RUNTIME_USES_SEPARATE_ONOFF_TRANSIENT_PATH",
        "CYCLING_STATE_MUST_BE_PROVEN_FIRST",
        "TAU_EQ_AND_EMITTER_RESPONSE_TIME_REQUIRE_AUTHORITY",
        "NO_UK_REGULATORY_TRANSFER",
    )
