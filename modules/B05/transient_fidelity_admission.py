"""B05-P43 fail-closed admission gates for OBS transient fidelity."""
from __future__ import annotations
from dataclasses import dataclass

QUALIFIED_FANCOIL_OBS = "QUALIFIED_FANCOIL_EMITTER_RESPONSE_OBS"
QUALIFIED_PRODUCT_TAU_EQ_OBS = "QUALIFIED_PRODUCT_TAU_EQ_OBS"
Q = "Q"

@dataclass(frozen=True)
class FanCoilTransientRecord:
    response_time_s: float | None
    source_id: str
    exact_emitter_identity: bool
    heating_mode: bool
    explicit_input_step: bool
    emitter_output_response: bool
    explicit_timebase: bool
    room_only_response: bool = False

    def classify(self) -> str:
        if not self.source_id or self.response_time_s is None or self.response_time_s <= 0:
            return Q
        if self.room_only_response:
            return Q
        if not (self.exact_emitter_identity and self.heating_mode and
                self.explicit_input_step and self.emitter_output_response and
                self.explicit_timebase):
            return Q
        return QUALIFIED_FANCOIL_OBS

@dataclass(frozen=True)
class HeatPumpTauEqRecord:
    tau_eq_s: float | None
    source_id: str
    exact_product_identity: bool
    manufacturer_or_named_lab: bool
    heating_onoff_or_restart_test: bool
    source_reports_tau_eq: bool = False
    seconds_scale_cadence: bool = False
    thermal_output_trace: bool = False
    electrical_input_trace: bool = False
    steady_state_reference: bool = False
    explicit_derivation_method: bool = False

    def classify(self) -> str:
        if not self.source_id or self.tau_eq_s is None or self.tau_eq_s <= 0:
            return Q
        if not (self.exact_product_identity and self.manufacturer_or_named_lab and
                self.heating_onoff_or_restart_test):
            return Q
        if self.source_reports_tau_eq:
            return QUALIFIED_PRODUCT_TAU_EQ_OBS
        if (self.seconds_scale_cadence and self.thermal_output_trace and
            self.electrical_input_trace and self.steady_state_reference and
            self.explicit_derivation_method):
            return QUALIFIED_PRODUCT_TAU_EQ_OBS
        return Q

def p43_boundaries() -> tuple[str, ...]:
    return (
        "ROOM_PLUS_FCU_RESPONSE_IS_NOT_EMITTER_ONLY_RESPONSE",
        "COOLING_RESPONSE_IS_NOT_SILENTLY_TRANSFERRED_TO_HEATING",
        "GENERIC_LITERATURE_TAU_IS_NOT_PRODUCT_TAU_EQ",
        "NAMED_TEST_LAB_IS_NOT_A_TRANSIENT_TEST_RESULT",
        "CDH_IS_NOT_TAU_EQ",
        "HEM_140S_DEFAULT_IS_NOT_PRODUCT_OBS",
    )
