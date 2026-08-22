"""Evidence-aware heat-pump physical model.

The module has no tariff, monetary, gas, financing, battery or VPP inputs. It
evaluates an explicit operating-point performance surface against explicit
thermal-demand and weather inputs and fails closed outside the validated surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isclose
from typing import Iterable, Sequence


EVIDENCE_STATUSES = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}


class PerformanceMapError(ValueError):
    """Raised when a performance point set is internally inconsistent."""


@dataclass(frozen=True)
class PerformancePoint:
    outdoor_temperature_c: float
    supply_temperature_c: float
    thermal_capacity_kw: float | None = None
    electrical_input_kw: float | None = None
    cop: float | None = None
    min_modulation_kw: float | None = None
    return_temperature_c: float | None = None
    delta_temperature_c: float | None = None
    evidence_status: str = "SCN"
    source_id: str = ""
    unit_boundary: str = "total_unit_input"


@dataclass(frozen=True)
class OperatingPoint:
    outdoor_temperature_c: float
    supply_temperature_c: float
    thermal_capacity_kw: float
    electrical_input_kw: float
    cop: float
    min_modulation_kw: float | None
    evidence_status: str
    source_ids: tuple[str, ...]
    interpolation: str


@dataclass(frozen=True)
class OperatingPointResult:
    status: str
    point: OperatingPoint | None = None
    reason: str = ""


class PerformanceMap:
    """Rectangular operating-point grid with bounded bilinear interpolation."""

    def __init__(self, equipment_id: str, technology: str, points: Iterable[PerformancePoint]):
        self.equipment_id = equipment_id
        self.technology = technology
        self.points = tuple(points)
        if not self.points:
            raise PerformanceMapError("performance map requires at least one point")
        self._grid: dict[tuple[float, float], PerformancePoint] = {}
        for point in self.points:
            self._validate_point(point)
            key = (point.outdoor_temperature_c, point.supply_temperature_c)
            if key in self._grid:
                raise PerformanceMapError(f"duplicate performance point: {key!r}")
            self._grid[key] = point
        self._outdoor = tuple(sorted({key[0] for key in self._grid}))
        self._supply = tuple(sorted({key[1] for key in self._grid}))

    @staticmethod
    def _validate_point(point: PerformancePoint) -> None:
        if point.evidence_status not in EVIDENCE_STATUSES:
            raise PerformanceMapError(f"invalid evidence status: {point.evidence_status!r}")
        if point.thermal_capacity_kw is not None and point.thermal_capacity_kw < 0:
            raise PerformanceMapError("thermal capacity cannot be negative")
        if point.electrical_input_kw is not None and point.electrical_input_kw < 0:
            raise PerformanceMapError("electrical input cannot be negative")
        if point.electrical_input_kw == 0 and point.thermal_capacity_kw not in (None, 0):
            raise PerformanceMapError("positive thermal capacity cannot have zero electrical input")
        if point.cop is not None and point.cop <= 0:
            raise PerformanceMapError("COP must be positive")
        values = (point.thermal_capacity_kw, point.electrical_input_kw, point.cop)
        if sum(value is not None for value in values) < 2:
            raise PerformanceMapError("at least two of capacity, electrical input and COP are required")
        if all(value is not None for value in values):
            if point.electrical_input_kw == 0:
                raise PerformanceMapError("capacity / input / COP are undefined at zero input")
            expected = point.thermal_capacity_kw / point.electrical_input_kw  # type: ignore[operator]
            if not isclose(expected, point.cop, rel_tol=1e-6, abs_tol=1e-9):  # type: ignore[arg-type]
                raise PerformanceMapError("capacity / input / COP are inconsistent")
        if point.min_modulation_kw is not None and point.min_modulation_kw < 0:
            raise PerformanceMapError("minimum modulation cannot be negative")
        if point.unit_boundary != "total_unit_input":
            raise PerformanceMapError("B05 requires total-unit electrical input boundary")

    @staticmethod
    def _complete(point: PerformancePoint) -> tuple[float, float, float]:
        capacity, electrical, cop = point.thermal_capacity_kw, point.electrical_input_kw, point.cop
        if cop is None:
            cop = capacity / electrical  # type: ignore[operator]
        elif electrical is None:
            electrical = capacity / cop  # type: ignore[operator]
        elif capacity is None:
            capacity = electrical * cop
        assert capacity is not None and electrical is not None and cop is not None
        if cop <= 0 or electrical < 0 or capacity < 0:
            raise PerformanceMapError("completed performance point violates physical bounds")
        return capacity, electrical, cop

    @staticmethod
    def _completed_status(point: PerformancePoint) -> tuple[float, float, float, str]:
        completed = PerformanceMap._complete(point)
        native_complete = point.thermal_capacity_kw is not None and point.electrical_input_kw is not None and point.cop is not None
        status = point.evidence_status if native_complete else "DER"
        return (*completed, status)

    def _point(self, outdoor: float, supply: float) -> PerformancePoint:
        try:
            return self._grid[(outdoor, supply)]
        except KeyError as exc:
            raise PerformanceMapError(f"missing rectangular grid corner {(outdoor, supply)!r}") from exc

    @staticmethod
    def _bracket(value: float, axis: Sequence[float]) -> tuple[float, float] | None:
        if value < axis[0] or value > axis[-1]:
            return None
        for lower, upper in zip(axis, axis[1:]):
            if lower <= value <= upper:
                return lower, upper
        return axis[-1], axis[-1]

    def evaluate(self, outdoor_temperature_c: float, supply_temperature_c: float) -> OperatingPointResult:
        exact = self._grid.get((outdoor_temperature_c, supply_temperature_c))
        if exact is not None:
            capacity, electrical, cop, status = self._completed_status(exact)
            return OperatingPointResult(
                status=status,
                point=OperatingPoint(outdoor_temperature_c, supply_temperature_c, capacity, electrical, cop, exact.min_modulation_kw, status, (exact.source_id,) if exact.source_id else (), "exact"),
            )
        outdoor_bracket = self._bracket(outdoor_temperature_c, self._outdoor)
        supply_bracket = self._bracket(supply_temperature_c, self._supply)
        if outdoor_bracket is None or supply_bracket is None:
            return OperatingPointResult("Q / OUT_OF_PERFORMANCE_DOMAIN", reason="operating condition is outside the validated performance envelope")
        o0, o1 = outdoor_bracket
        s0, s1 = supply_bracket
        try:
            corners = ((self._point(o0, s0), self._point(o1, s0)), (self._point(o0, s1), self._point(o1, s1)))
        except PerformanceMapError as exc:
            return OperatingPointResult("Q / MISSING_GRID_POINT", reason=str(exc))
        weights = (0.0 if o1 == o0 else (outdoor_temperature_c - o0) / (o1 - o0), 0.0 if s1 == s0 else (supply_temperature_c - s0) / (s1 - s0))
        completed = [[self._complete(point) for point in row] for row in corners]

        def bilinear(index: int) -> float:
            low_supply = completed[0][0][index] + weights[0] * (completed[0][1][index] - completed[0][0][index])
            high_supply = completed[1][0][index] + weights[0] * (completed[1][1][index] - completed[1][0][index])
            return low_supply + weights[1] * (high_supply - low_supply)

        capacity, electrical, cop = bilinear(0), bilinear(1), bilinear(2)
        if electrical < 0 or capacity < 0 or cop <= 0:
            return OperatingPointResult("Q / INVALID_INTERPOLATED_POINT", reason="interpolation violated physical bounds")
        minimums = [point.min_modulation_kw for row in corners for point in row if point.min_modulation_kw is not None]
        minimum = sum(minimums) / len(minimums) if len(minimums) == 4 else None
        sources = tuple(sorted({point.source_id for row in corners for point in row if point.source_id}))
        status = "DER"
        return OperatingPointResult(status, OperatingPoint(outdoor_temperature_c, supply_temperature_c, capacity, electrical, cop, minimum, status, sources, "bilinear_bounded"))


@dataclass(frozen=True)
class HourlyDemand:
    timestamp: datetime
    outdoor_temperature_c: float | None
    space_heating_required_kw: float
    required_supply_temperature_c: float | None
    dhw_required_kw: float = 0.0
    dhw_supply_temperature_c: float | None = None
    relative_humidity_pct: float | None = None


@dataclass(frozen=True)
class OperatingConfig:
    timestep_hours: float = 1.0
    backup_enabled: bool = False
    backup_type: str = ""
    backup_capacity_kw: float = 0.0
    backup_efficiency: float | None = None
    defrost_status: str = "Q"
    dhw_priority: str = "Q"

    def validate(self) -> None:
        if self.timestep_hours <= 0 or self.backup_capacity_kw < 0:
            raise ValueError("timestep and backup capacity must be positive/non-negative")
        if self.backup_enabled and (not self.backup_type or self.backup_efficiency is None or self.backup_efficiency <= 0):
            raise ValueError("enabled backup requires type and positive efficiency")


@dataclass(frozen=True)
class HourlyResult:
    timestamp: datetime
    status: str
    space_heating_required_kwh: float
    dhw_required_kwh: float
    heat_pump_heat_delivered_kwh: float
    backup_heat_delivered_kwh: float
    heat_pump_electricity_kwh: float
    backup_electricity_kwh: float
    total_electricity_kwh: float
    available_capacity_kw: float
    required_capacity_kw: float
    delivered_heat_kwh: float
    capacity_shortfall_kwh: float
    part_load_ratio: float
    operating_state: str
    defrost_energy_penalty_kwh: float | None = None
    defrost_heat_penalty_kwh: float | None = None


@dataclass(frozen=True)
class SimulationResult:
    hourly: tuple[HourlyResult, ...]
    status: str
    seasonal_heat_delivered_kwh: float
    seasonal_heat_pump_electricity_kwh: float
    seasonal_backup_electricity_kwh: float
    seasonal_total_electricity_kwh: float
    seasonal_cop_simulated: float | None
    spf_simulated: float | None
    capacity_shortfall_kwh: float
    hours_with_capacity_shortfall: int
    peak_hourly_electrical_power_kw: float
    cold_day_peak_hourly_kw: float | None
    defrost_status: str


def _validate_demand(demand: HourlyDemand) -> None:
    if demand.space_heating_required_kw < 0 or demand.dhw_required_kw < 0:
        raise ValueError("thermal demand cannot be negative")
    if demand.outdoor_temperature_c is None and (demand.space_heating_required_kw or demand.dhw_required_kw):
        raise ValueError("weather input is mandatory for positive thermal demand")
    if demand.space_heating_required_kw and demand.required_supply_temperature_c is None:
        raise ValueError("space-heating supply temperature is mandatory for positive space load")
    if demand.dhw_required_kw and demand.dhw_supply_temperature_c is None:
        raise ValueError("DHW supply temperature is mandatory for positive DHW load")


def simulate_hourly(performance_map: PerformanceMap, demands: Iterable[HourlyDemand], config: OperatingConfig | None = None) -> SimulationResult:
    """Simulate explicit hourly demand; no monetary or tariff inputs are accepted."""
    config = config or OperatingConfig()
    config.validate()
    demand_rows = tuple(demands)
    results: list[HourlyResult] = []
    for demand in demand_rows:
        _validate_demand(demand)
        space, dhw = demand.space_heating_required_kw, demand.dhw_required_kw
        total_required = space + dhw
        required_kwh = total_required * config.timestep_hours
        if total_required == 0:
            results.append(HourlyResult(demand.timestamp, "VALID", space * config.timestep_hours, dhw * config.timestep_hours, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "NO_HEAT_DEMAND", None, None))
            continue
        if space and dhw and demand.required_supply_temperature_c != demand.dhw_supply_temperature_c and config.dhw_priority == "Q":
            results.append(HourlyResult(demand.timestamp, "Q / DHW_PRIORITY_UNMODELED", space * config.timestep_hours, dhw * config.timestep_hours, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, total_required, 0.0, required_kwh, 0.0, "Q_DHW_PRIORITY", None, None))
            continue
        supply = demand.required_supply_temperature_c if space else demand.dhw_supply_temperature_c
        operating = performance_map.evaluate(demand.outdoor_temperature_c, supply)  # type: ignore[arg-type]
        if operating.point is None:
            results.append(HourlyResult(demand.timestamp, operating.status, space * config.timestep_hours, dhw * config.timestep_hours, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, total_required, 0.0, required_kwh, 0.0, "Q_OUTSIDE_MAP", None, None))
            continue
        point = operating.point
        delivered_kw = min(total_required, point.thermal_capacity_kw)
        shortfall_kw = max(total_required - delivered_kw, 0.0)
        backup_kw = min(shortfall_kw, config.backup_capacity_kw) if config.backup_enabled else 0.0
        backup_electricity = backup_kw * config.timestep_hours / config.backup_efficiency if config.backup_enabled else 0.0  # type: ignore[operator]
        hp_electricity = delivered_kw * config.timestep_hours / point.cop
        state = "CONTINUOUS_MODULATION"
        if point.min_modulation_kw is not None and 0 < delivered_kw < point.min_modulation_kw:
            state = "BELOW_MINIMUM_MODULATION / CYCLING_REQUIRED"
        status = "VALID" if shortfall_kw <= backup_kw + 1e-12 else "VALID / CAPACITY_SHORTFALL"
        results.append(HourlyResult(demand.timestamp, status, space * config.timestep_hours, dhw * config.timestep_hours, delivered_kw * config.timestep_hours, backup_kw * config.timestep_hours, hp_electricity, backup_electricity, hp_electricity + backup_electricity, point.thermal_capacity_kw, total_required, (delivered_kw + backup_kw) * config.timestep_hours, max(shortfall_kw - backup_kw, 0.0) * config.timestep_hours, 0.0 if point.thermal_capacity_kw == 0 else delivered_kw / point.thermal_capacity_kw, state, None, None))

    hp_heat = sum(row.heat_pump_heat_delivered_kwh for row in results)
    backup_heat = sum(row.backup_heat_delivered_kwh for row in results)
    hp_electricity = sum(row.heat_pump_electricity_kwh for row in results)
    backup_electricity = sum(row.backup_electricity_kwh for row in results)
    total_electricity = hp_electricity + backup_electricity
    delivered_heat = hp_heat + backup_heat
    shortfall = sum(row.capacity_shortfall_kwh for row in results)
    powers = [row.total_electricity_kwh / config.timestep_hours for row in results]
    cold_peak = None
    if demand_rows:
        cold_day = min(demand_rows, key=lambda row: row.outdoor_temperature_c if row.outdoor_temperature_c is not None else float("inf")).timestamp.date()
        cold_indices = [index for index, demand in enumerate(demand_rows) if demand.timestamp.date() == cold_day]
        if cold_indices:
            cold_peak = max(powers[index] for index in cold_indices)
    status = "Q" if any(row.status.startswith("Q") for row in results) else ("PARTIAL" if shortfall > 0 else "VALID")
    return SimulationResult(tuple(results), status, delivered_heat, hp_electricity, backup_electricity, total_electricity, (hp_heat / hp_electricity) if hp_electricity else None, (delivered_heat / total_electricity) if total_electricity else None, shortfall, sum(1 for row in results if row.capacity_shortfall_kwh > 0), max(powers, default=0.0), cold_peak, config.defrost_status)
