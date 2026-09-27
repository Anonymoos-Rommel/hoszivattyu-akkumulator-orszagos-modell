"""B05-P50 S2125 matched active-defrost penalty contract.

This module contains only the bounded derivation contract. Raw owner data remain
EXTERNAL_ONLY and are not embedded in the repository.
"""

from __future__ import annotations

from dataclasses import dataclass

THERMAL_FACTOR_KW_PER_LPM_K = 0.0734149054505005

STRICT_CALIPERS = {
    "bt28_c": 1.0,
    "bt16_c": 1.5,
    "compressor_hz": 5.0,
    "requested_hz": 5.0,
    "bt12_c": 2.0,
    "bt3_c": 2.0,
}

HEAT_MODE_MAX_DHW_SHARE = 0.1
DHW_MODE_MIN_DHW_SHARE = 0.9


def classify_pre_mode(dhw_mean: float) -> str:
    if dhw_mean <= HEAT_MODE_MAX_DHW_SHARE:
        return "HEAT"
    if dhw_mean >= DHW_MODE_MIN_DHW_SHARE:
        return "DHW"
    return "TRANSITION"


def signed_thermal_power_kw(flow_lpm: float, bt12_c: float, bt3_c: float) -> float:
    """Source-bound signed thermal DER from BF1 and BT12-BT3.

    The factor is empirically calibrated against source-native NIBE generated
    heat power on non-defrost heating samples. This is DER, not source-native OBS.
    """

    return THERMAL_FACTOR_KW_PER_LPM_K * flow_lpm * (bt12_c - bt3_c)


def direct_electric_uplift_kwh(event_kwh: float, matched_control_kwh: float) -> float:
    return event_kwh - matched_control_kwh


def thermal_service_shortfall_kwh(
    matched_control_thermal_kwh: float,
    event_signed_thermal_kwh: float,
) -> float:
    return matched_control_thermal_kwh - event_signed_thermal_kwh


@dataclass(frozen=True)
class MatchAdmission:
    mode: str
    n_controls: int
    electrical_coverage_fraction: float
    has_defrost_in_control: bool
    stable_mode: bool

    def admitted(self) -> bool:
        return (
            self.mode in {"HEAT", "DHW"}
            and self.n_controls >= 3
            and self.electrical_coverage_fraction >= 0.98
            and not self.has_defrost_in_control
            and self.stable_mode
        )


def p50_boundaries() -> tuple[str, ...]:
    return (
        "ACTIVE_STATE_DIRECT_ELECTRIC_UPLIFT != FULL_DEFROST_CYCLE_PENALTY",
        "MATCHED_HEAT_EVENT != DHW_EVENT",
        "SIGNED_THERMAL_DER != SOURCE_NATIVE_SIGNED_HEAT_METER",
        "ONE_S2125_FIELD_SYSTEM != CROSS_PRODUCT_OR_HUNGARIAN_FLEET_PARAMETER",
        "POST_DEFROST_RECOVERY_TAIL_REMAINS_REQUIRED",
        "PASSIVE_DEFROST_BRANCH_REMAINS_SEPARATE",
        "NO_MECHANICAL_READINESS_UPLIFT",
    )
