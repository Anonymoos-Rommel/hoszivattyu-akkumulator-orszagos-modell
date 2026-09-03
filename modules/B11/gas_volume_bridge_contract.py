"""B11-P3 fail-closed useful-heat to gas-volume bridge.

Core rule:

    COUNTY GAS SALES != ARCHETYPE GAS VOLUME
    USEFUL HEAT != GAS INPUT ENERGY != GAS VOLUME

Gas volume may only be derived from an explicit useful-heat requirement,
explicit seasonal gas-appliance efficiency and explicit period/location-specific
gas heating value. No county utility volume is allocated to archetypes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


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

    def numeric(self, expected_unit: str) -> float:
        if self.unit != expected_unit:
            raise ValueError(f"expected {expected_unit!r}, got {self.unit!r}")
        if self.status not in _ALLOWED:
            raise ValueError("Q evidence cannot authorize gas-volume derivation")
        if self.value is None or not math.isfinite(self.value):
            raise ValueError("missing/non-finite evidence is not zero")
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


def _combined_status(values: tuple[PhysicalEvidence, ...]) -> EvidenceStatus:
    statuses = {item.status for item in values}
    if EvidenceStatus.Q in statuses:
        return EvidenceStatus.Q
    if EvidenceStatus.SCN in statuses:
        return EvidenceStatus.SCN
    if EvidenceStatus.DER in statuses:
        return EvidenceStatus.DER
    return EvidenceStatus.OBS


def derive_gas_volume(inputs: GasVolumeBridgeInputs) -> GasVolumeBridgeResult:
    useful_heat = inputs.useful_heat_kwh_year.numeric("kWh/year")
    efficiency = inputs.seasonal_appliance_efficiency.numeric("fraction")
    heating_value = inputs.gas_lower_heating_value_mj_m3.numeric("MJ/m3")

    if useful_heat < 0:
        raise ValueError("useful heat cannot be negative")
    if not 0.0 < efficiency <= 1.0:
        raise ValueError("seasonal appliance efficiency must be within (0, 1]")
    if heating_value <= 0:
        raise ValueError("gas heating value must be positive")

    gas_input_kwh = useful_heat / efficiency
    heating_value_kwh_m3 = heating_value / 3.6
    gas_volume = gas_input_kwh / heating_value_kwh_m3

    if gas_volume < 0 or not math.isfinite(gas_volume):
        raise ValueError("derived gas volume is invalid")

    return GasVolumeBridgeResult(
        useful_heat_kwh_year=useful_heat,
        gas_input_energy_kwh_year=gas_input_kwh,
        gas_volume_m3_year=gas_volume,
        output_status=_combined_status(
            (
                inputs.useful_heat_kwh_year,
                inputs.seasonal_appliance_efficiency,
                inputs.gas_lower_heating_value_mj_m3,
            )
        ),
    )


def county_utility_volume_can_allocate_archetypes() -> bool:
    """P3 deliberately forbids utility-volume pro-rata allocation."""

    return False
