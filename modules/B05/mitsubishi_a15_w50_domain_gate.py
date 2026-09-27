"""B05-P46 Mitsubishi A-15/W50 fail-closed two-dimensional authority gate."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Q = "Q"
PERSISTENT_SOURCE_BLANK = "PERSISTENT_SOURCE_BLANK"
EXACT_2D_SUPPORTED = "EXACT_2D_SUPPORTED"
EXACT_2D_OUTSIDE = "EXACT_2D_OUTSIDE"

@dataclass(frozen=True)
class PersistentBlankEvidence:
    revision_count: int
    all_levels_blank: bool
    same_ambient_lower_supply_populated: bool
    warmer_ambient_same_supply_populated: bool

    def classify(self) -> str:
        if self.revision_count < 1:
            return Q
        if self.all_levels_blank:
            return PERSISTENT_SOURCE_BLANK
        return Q

@dataclass(frozen=True)
class CoordinateAuthority:
    exact_product: bool
    outdoor_temperature_c: float
    supply_temperature_c: float
    source_native_2d_binding: bool
    explicit_status: Literal["SUPPORTED", "OUTSIDE", "UNSPECIFIED"]

    def classify(self) -> str:
        if not (
            self.exact_product
            and self.source_native_2d_binding
            and self.outdoor_temperature_c == -15
            and self.supply_temperature_c == 50
        ):
            return Q
        if self.explicit_status == "SUPPORTED":
            return EXACT_2D_SUPPORTED
        if self.explicit_status == "OUTSIDE":
            return EXACT_2D_OUTSIDE
        return Q

def compose_one_dimensional_limits(
    max_outlet_temperature_c: float,
    minimum_ambient_temperature_c: float,
    target_outdoor_c: float,
    target_supply_c: float,
) -> str:
    """Separate 1D limits never create a 2D operating-coordinate authority."""
    _ = (
        max_outlet_temperature_c,
        minimum_ambient_temperature_c,
        target_outdoor_c,
        target_supply_c,
    )
    return Q

def p46_boundaries() -> tuple[str, ...]:
    return (
        "PERSISTENT_BLANK_IS_NOT_PHYSICAL_IMPOSSIBILITY",
        "A_MINUS15_W45_PLUS_A_MINUS10_W50_IS_NOT_A_MINUS15_W50",
        "MAX_OUTLET_PLUS_AMBIENT_RANGE_IS_NOT_2D_AUTHORITY",
        "GRAPH_DIGITIZATION_IS_FORBIDDEN",
        "BLANK_EQUALS_UNSUPPORTED_IS_FORBIDDEN",
    )
