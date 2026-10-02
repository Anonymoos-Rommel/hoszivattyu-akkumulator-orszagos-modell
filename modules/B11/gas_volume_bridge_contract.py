"""B11-P3 fail-closed useful-heat to gas-volume bridge.

Core rule:

    COUNTY GAS SALES != ARCHETYPE GAS VOLUME
    USEFUL HEAT != GAS INPUT ENERGY != GAS VOLUME

P4 hardens the efficiency interface: the bridge accepts only an explicitly
LHV-basis seasonal fuel-conversion efficiency. Regulatory/product metrics and
GCV-basis values must be normalized by the P4 authority layer first.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real

from .gas_reference_contract import CalorificBasis, GasReferenceState


class EvidenceStatus(str, Enum):
    OBS = "OBS"
    DER = "DER"
    SCN = "SCN"
    Q = "Q"


_ALLOWED = {EvidenceStatus.OBS, EvidenceStatus.DER, EvidenceStatus.SCN}


@dataclass(frozen=True)
class PhysicalEvidence:
    value: float | None
    unit: str
    status: EvidenceStatus
    source_ref: str | None = None
    reference_state: GasReferenceState | None = None
    calorific_basis: CalorificBasis | None = None

    def numeric(self, expected_unit: str) -> float:
        if self.unit != expected_unit:
            raise ValueError(f"expected {expected_unit!r}, got {self.unit!r}")
        if self.status not in _ALLOWED:
            raise ValueError("Q evidence cannot authorize gas-volume derivation")
        if (isinstance(self.value, bool) or not isinstance(self.value, Real)
                or not math.isfinite(self.value)):
            raise ValueError("missing/non-finite evidence is not zero")
        if expected_unit in {"MJ/m3_GCV", "MJ/m3_LHV"}:
            if not isinstance(self.reference_state, GasReferenceState):
                raise ValueError("explicit gas volume reference state is required")
        if expected_unit in {"MJ/m3_GCV", "MJ/m3_LHV", "fraction_lhv"}:
            if not isinstance(self.calorific_basis, CalorificBasis):
                raise ValueError("explicit calorific reference and gas-quality context are required")
        return float(self.value)


@dataclass(frozen=True)
class GasVolumeBridgeInputs:
    useful_heat_kwh_year: PhysicalEvidence
    seasonal_appliance_efficiency: PhysicalEvidence
    gas_lower_heating_value_mj_m3: PhysicalEvidence


@dataclass(frozen=True)
class GasVolumeBridgeResult:
    useful_heat_kwh_year: float
    gas_input_energy_kwh_year: float
    gas_volume_m3_year: float
    output_status: EvidenceStatus
    reference_state: GasReferenceState
    calorific_basis: CalorificBasis


def _combined_status(values: tuple[PhysicalEvidence, ...]) -> EvidenceStatus:
    statuses = {item.status for item in values}
    if EvidenceStatus.Q in statuses:
        return EvidenceStatus.Q
    if EvidenceStatus.SCN in statuses:
        return EvidenceStatus.SCN
    # Arithmetic is derived even when every input is observed.
    return EvidenceStatus.DER


def derive_gas_volume(inputs: GasVolumeBridgeInputs) -> GasVolumeBridgeResult:
    useful_heat = inputs.useful_heat_kwh_year.numeric("kWh/year")
    efficiency = inputs.seasonal_appliance_efficiency.numeric("fraction_lhv")
    heating_value = inputs.gas_lower_heating_value_mj_m3.numeric("MJ/m3_LHV")

    if inputs.seasonal_appliance_efficiency.calorific_basis != inputs.gas_lower_heating_value_mj_m3.calorific_basis:
        raise ValueError("efficiency and LHV calorific reference / gas-quality context do not match")

    if useful_heat < 0:
        raise ValueError("useful heat cannot be negative")
    if efficiency <= 0.0:
        raise ValueError("LHV-basis seasonal appliance efficiency must be positive")
    if heating_value <= 0:
        raise ValueError("gas lower heating value must be positive")

    gas_input_kwh = useful_heat / efficiency
    heating_value_kwh_m3 = heating_value / 3.6
    if not math.isfinite(gas_input_kwh) or heating_value_kwh_m3 <= 0:
        raise ValueError("derived gas energy or heating-value conversion is invalid")
    gas_volume = gas_input_kwh / heating_value_kwh_m3

    if gas_volume < 0 or not math.isfinite(gas_volume):
        raise ValueError("derived gas volume is invalid")

    return GasVolumeBridgeResult(
        useful_heat_kwh_year=useful_heat,
        gas_input_energy_kwh_year=gas_input_kwh,
        gas_volume_m3_year=gas_volume,
        reference_state=inputs.gas_lower_heating_value_mj_m3.reference_state,
        calorific_basis=inputs.gas_lower_heating_value_mj_m3.calorific_basis,
        output_status=_combined_status(
            (
                inputs.useful_heat_kwh_year,
                inputs.seasonal_appliance_efficiency,
                inputs.gas_lower_heating_value_mj_m3,
            )
        ),
    )


def county_utility_volume_can_allocate_archetypes() -> bool:
    return False
