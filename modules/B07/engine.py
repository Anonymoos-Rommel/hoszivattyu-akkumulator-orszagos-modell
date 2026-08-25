"""Bounded household-battery physics and physical-flexibility contract.

The canonical boundary is AC/grid-side power at the battery interface. A
charge command is grid energy entering the battery and a discharge command is
energy delivered from the battery to the load/grid. One-way efficiencies are
applied exactly once; tariff, market and legal decisions are outside this
module.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional


class BatteryModelError(ValueError):
    """Fail-closed validation error with an explicit evidence status."""

    status = "Q"


@dataclass(frozen=True)
class BatterySpec:
    nominal_capacity_kwh: float
    usable_capacity_kwh: float
    soc_min_fraction: float
    soc_max_fraction: float
    max_charge_power_kw: float
    max_discharge_power_kw: float
    charge_efficiency: float
    discharge_efficiency: float
    timestep_hours: float
    capacity_boundary: str = "USABLE"
    power_boundary: str = "AC"
    efficiency_boundary: str = "SCN_ONE_WAY"
    chemistry: Optional[str] = None
    operating_temp_min_c: Optional[float] = None
    operating_temp_max_c: Optional[float] = None
    standing_loss_fraction_per_timestep: Optional[float] = None
    source_ids: tuple[str, ...] = ()
    status: str = "SCN"

    def __post_init__(self) -> None:
        values = (
            self.nominal_capacity_kwh, self.usable_capacity_kwh,
            self.soc_min_fraction, self.soc_max_fraction,
            self.max_charge_power_kw, self.max_discharge_power_kw,
            self.charge_efficiency, self.discharge_efficiency, self.timestep_hours,
        )
        try:
            finite = all(isfinite(value) for value in values)
        except TypeError as exc:
            raise BatteryModelError("mandatory battery parameters must be finite") from exc
        if not finite:
            raise BatteryModelError("mandatory battery parameters must be finite")
        if self.nominal_capacity_kwh <= 0 or self.usable_capacity_kwh <= 0:
            raise BatteryModelError("capacity must be positive")
        if self.usable_capacity_kwh > self.nominal_capacity_kwh:
            raise BatteryModelError("usable capacity cannot exceed nominal capacity")
        if not 0 <= self.soc_min_fraction < self.soc_max_fraction <= 1:
            raise BatteryModelError("SOC bounds must satisfy 0 <= min < max <= 1")
        if self.max_charge_power_kw < 0 or self.max_discharge_power_kw < 0:
            raise BatteryModelError("power limits cannot be negative")
        if not 0 < self.charge_efficiency <= 1 or not 0 < self.discharge_efficiency <= 1:
            raise BatteryModelError("one-way efficiencies must be in (0, 1]")
        if self.timestep_hours <= 0:
            raise BatteryModelError("timestep must be positive")
        if self.standing_loss_fraction_per_timestep is not None and not 0 <= self.standing_loss_fraction_per_timestep < 1:
            raise BatteryModelError("standing loss must be in [0, 1)")
        if self.standing_loss_fraction_per_timestep is not None:
            raise BatteryModelError("standing-loss runtime model is Q and is not implemented in P1")
        if self.operating_temp_min_c is not None and self.operating_temp_max_c is not None:
            if self.operating_temp_min_c > self.operating_temp_max_c:
                raise BatteryModelError("temperature envelope is inverted")

    @property
    def soc_min_kwh(self) -> float:
        return self.usable_capacity_kwh * self.soc_min_fraction

    @property
    def soc_max_kwh(self) -> float:
        return self.usable_capacity_kwh * self.soc_max_fraction


@dataclass
class BatteryState:
    soc_kwh: float
    charged_energy_kwh: float = 0.0
    discharged_energy_kwh: float = 0.0
    throughput_kwh: float = 0.0

    def soc_fraction(self, spec: BatterySpec) -> float:
        return self.soc_kwh / spec.usable_capacity_kwh


@dataclass(frozen=True)
class PhysicalFlexibility:
    current_soc_kwh: float
    current_soc_fraction: float
    max_additional_charge_kw: float
    max_additional_discharge_kw: float
    charge_energy_headroom_kwh: float
    discharge_energy_available_kwh: float
    physical_up_flex_kw: float
    physical_down_flex_kw: float
    status: str = "DER"
    reason: str = ""


@dataclass(frozen=True)
class BatteryStepResult:
    soc_before_kwh: float
    soc_after_kwh: float
    requested_charge_kw: float
    actual_charge_kw: float
    requested_discharge_kw: float
    actual_discharge_kw: float
    charge_energy_from_grid_kwh: float
    energy_added_to_storage_kwh: float
    energy_removed_from_storage_kwh: float
    discharge_energy_to_load_grid_kwh: float
    charge_curtailed_kw: float
    charge_curtailed_kwh: float
    discharge_unserved_kw: float
    discharge_unserved_kwh: float
    physical_charge_flex_kw: float
    physical_discharge_flex_kw: float
    status: str
    reason: str = ""


@dataclass(frozen=True)
class HouseholdPowerBalance:
    total_load_kw: float
    grid_import_kw: float
    grid_export_kw: float
    export_curtailed_kw: float
    export_status: str
    status: str = "DER"


@dataclass(frozen=True)
class B08PhysicalHandoff:
    net_grid_import_kw: float
    net_grid_export_kw: float
    battery_charge_kw: float
    battery_discharge_kw: float
    physical_up_flex_kw: float
    physical_down_flex_kw: float
    soc_fraction: float
    status: str = "DER"
    timestep_hours: float | None = None


def _nonnegative(value: float, name: str) -> float:
    if not isfinite(value) or value < 0:
        raise BatteryModelError(f"{name} must be finite and non-negative")
    return value


class BatteryEngine:
    """Deterministic command executor for one explicit timestep."""

    def __init__(self, spec: BatterySpec, initial_soc_kwh: float):
        _nonnegative(initial_soc_kwh, "initial_soc_kwh")
        if not spec.soc_min_kwh <= initial_soc_kwh <= spec.soc_max_kwh:
            raise BatteryModelError("initial SOC is outside explicit bounds")
        self.spec = spec
        self.state = BatteryState(initial_soc_kwh)

    def _check_temperature(self, temperature_c: Optional[float]) -> None:
        if temperature_c is None:
            return
        if not isfinite(temperature_c):
            raise BatteryModelError("temperature must be finite")
        if self.spec.operating_temp_min_c is not None and temperature_c < self.spec.operating_temp_min_c:
            raise BatteryModelError("temperature is outside the supported operating envelope: NOT_ALLOWED")
        if self.spec.operating_temp_max_c is not None and temperature_c > self.spec.operating_temp_max_c:
            raise BatteryModelError("temperature is outside the supported operating envelope: NOT_ALLOWED")

    def flexibility(self) -> PhysicalFlexibility:
        headroom = max(self.spec.soc_max_kwh - self.state.soc_kwh, 0.0)
        available = max(self.state.soc_kwh - self.spec.soc_min_kwh, 0.0)
        charge_kw = min(self.spec.max_charge_power_kw, headroom / self.spec.charge_efficiency / self.spec.timestep_hours)
        discharge_kw = min(self.spec.max_discharge_power_kw, available * self.spec.discharge_efficiency / self.spec.timestep_hours)
        return PhysicalFlexibility(
            current_soc_kwh=self.state.soc_kwh,
            current_soc_fraction=self.state.soc_fraction(self.spec),
            max_additional_charge_kw=charge_kw,
            max_additional_discharge_kw=discharge_kw,
            charge_energy_headroom_kwh=headroom,
            discharge_energy_available_kwh=available,
            physical_up_flex_kw=discharge_kw,
            physical_down_flex_kw=charge_kw,
        )

    def step(self, requested_charge_kw: float = 0.0, requested_discharge_kw: float = 0.0, *, temperature_c: Optional[float] = None) -> BatteryStepResult:
        charge = _nonnegative(requested_charge_kw, "requested_charge_kw")
        discharge = _nonnegative(requested_discharge_kw, "requested_discharge_kw")
        self._check_temperature(temperature_c)
        if charge > 0 and discharge > 0:
            raise BatteryModelError("simultaneous charge and discharge is rejected: Q")

        before = self.state.soc_kwh
        dt = self.spec.timestep_hours
        requested_charge_energy = charge * dt
        requested_discharge_energy = discharge * dt
        if charge:
            actual_charge_energy = min(
                requested_charge_energy, self.spec.max_charge_power_kw * dt,
                max(self.spec.soc_max_kwh - before, 0.0) / self.spec.charge_efficiency,
            )
            stored_added = actual_charge_energy * self.spec.charge_efficiency
            removed = delivered = 0.0
        elif discharge:
            delivered = min(
                requested_discharge_energy, self.spec.max_discharge_power_kw * dt,
                max(before - self.spec.soc_min_kwh, 0.0) * self.spec.discharge_efficiency,
            )
            removed = delivered / self.spec.discharge_efficiency
            actual_charge_energy = stored_added = 0.0
        else:
            actual_charge_energy = stored_added = removed = delivered = 0.0

        after = min(max(before + stored_added - removed, self.spec.soc_min_kwh), self.spec.soc_max_kwh)
        self.state.soc_kwh = after
        self.state.charged_energy_kwh += actual_charge_energy
        self.state.discharged_energy_kwh += delivered
        self.state.throughput_kwh += actual_charge_energy + delivered
        flex = self.flexibility()
        charge_curtailed = max(requested_charge_energy - actual_charge_energy, 0.0)
        discharge_unserved = max(requested_discharge_energy - delivered, 0.0)
        status = "SCN" if self.spec.status == "SCN" else "DER"
        reason = "" if not charge_curtailed and not discharge_unserved else "PHYSICAL_LIMIT_CLIPPED"
        return BatteryStepResult(
            soc_before_kwh=before, soc_after_kwh=after,
            requested_charge_kw=charge, actual_charge_kw=actual_charge_energy / dt,
            requested_discharge_kw=discharge, actual_discharge_kw=delivered / dt,
            charge_energy_from_grid_kwh=actual_charge_energy,
            energy_added_to_storage_kwh=stored_added,
            energy_removed_from_storage_kwh=removed,
            discharge_energy_to_load_grid_kwh=delivered,
            charge_curtailed_kw=charge_curtailed / dt, charge_curtailed_kwh=charge_curtailed,
            discharge_unserved_kw=discharge_unserved / dt, discharge_unserved_kwh=discharge_unserved,
            physical_charge_flex_kw=flex.max_additional_charge_kw,
            physical_discharge_flex_kw=flex.max_additional_discharge_kw,
            status=status, reason=reason,
        )


def compute_household_balance(
    household_load_kw: float, heat_pump_load_kw: float, other_household_load_kw: float,
    onsite_generation_kw: float, battery_charge_kw: float, battery_discharge_kw: float,
    *, export_limit_kw: Optional[float] = None, export_permission_status: str = "Q",
) -> HouseholdPowerBalance:
    values = {
        "household_load_kw": household_load_kw, "heat_pump_load_kw": heat_pump_load_kw,
        "other_household_load_kw": other_household_load_kw, "onsite_generation_kw": onsite_generation_kw,
        "battery_charge_kw": battery_charge_kw, "battery_discharge_kw": battery_discharge_kw,
    }
    for name, value in values.items():
        _nonnegative(value, name)
    if export_limit_kw is not None:
        _nonnegative(export_limit_kw, "export_limit_kw")
    if export_permission_status not in {"Q", "POL", "SCN", "OBS"}:
        raise BatteryModelError("invalid export permission status")
    total_load = household_load_kw + heat_pump_load_kw + other_household_load_kw
    balance = total_load + battery_charge_kw - battery_discharge_kw - onsite_generation_kw
    grid_import = max(balance, 0.0)
    unconstrained_export = max(-balance, 0.0)
    export = unconstrained_export if export_limit_kw is None else min(unconstrained_export, export_limit_kw)
    return HouseholdPowerBalance(
        total_load_kw=total_load, grid_import_kw=grid_import, grid_export_kw=export,
        export_curtailed_kw=max(unconstrained_export - export, 0.0),
        export_status=export_permission_status,
    )


def make_b08_handoff(balance: HouseholdPowerBalance, result: BatteryStepResult, spec: BatterySpec) -> B08PhysicalHandoff:
    return B08PhysicalHandoff(
        net_grid_import_kw=balance.grid_import_kw, net_grid_export_kw=balance.grid_export_kw,
        battery_charge_kw=result.actual_charge_kw, battery_discharge_kw=result.actual_discharge_kw,
        physical_up_flex_kw=result.physical_discharge_flex_kw,
        physical_down_flex_kw=result.physical_charge_flex_kw,
        soc_fraction=result.soc_after_kwh / spec.usable_capacity_kwh,
        status=result.status,
        timestep_hours=spec.timestep_hours,
        )
