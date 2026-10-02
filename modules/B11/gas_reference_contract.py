"""Explicit reference conventions for B11 gas-quality arithmetic.

A volume state is not a calorific reference. A dimensionless fuel efficiency
needs the latter and a gas-quality context, but no volume temperature/pressure.
No conversion between reference states is inferred by this contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real


class MoistureBasis(str, Enum):
    DRY = "DRY"
    WATER_SATURATED = "WATER_SATURATED"


def _finite_real(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite real number, not a boolean")


def _temperature(value: float, label: str) -> None:
    _finite_real(value, label)
    if value <= -273.15:
        raise ValueError(f"{label} must be above absolute zero")


@dataclass(frozen=True)
class GasReferenceState:
    """State of the cubic-metre denominator; pressure is absolute, in Pa.

    WATER_SATURATED means saturated at this volume temperature and pressure.
    An unspecified wet/unknown moisture basis cannot authorize arithmetic.
    """

    volume_reference_temperature_c: float
    reference_pressure_pa: float
    moisture_basis: MoistureBasis

    def __post_init__(self) -> None:
        _temperature(self.volume_reference_temperature_c, "volume reference temperature")
        _finite_real(self.reference_pressure_pa, "absolute reference pressure")
        if self.reference_pressure_pa <= 0:
            raise ValueError("absolute reference pressure must be positive")
        if not isinstance(self.moisture_basis, MoistureBasis):
            raise ValueError("explicit supported moisture basis is required")


@dataclass(frozen=True)
class CalorificBasis:
    """Combustion reference and the gas represented by an energy denominator.

    The context ID must identify the same composition/population and applicable
    point/region/period or synthetic scenario in its provenance. Equal source
    URLs alone do not establish a common gas-quality context. It may represent
    a defensible weighted population; an exact participant ID is not required.
    """

    calorific_reference_temperature_c: float
    gas_quality_context_id: str

    def __post_init__(self) -> None:
        _temperature(self.calorific_reference_temperature_c, "calorific reference temperature")
        if not isinstance(self.gas_quality_context_id, str) or not self.gas_quality_context_id.strip():
            raise ValueError("explicit gas-quality context ID is required")
