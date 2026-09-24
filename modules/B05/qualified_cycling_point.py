"""B05-P20 exact qualified cycling-ready product point."""
from __future__ import annotations
from dataclasses import dataclass

from modules.B05.cycling_degradation_method import water_side_cycling_cop
from modules.B05.cycling_input_colocation import MEASUREMENT_DETERMINED

QUALIFIED_POINT="QUALIFIED_CYCLING_READY_POINT"
OUTSIDE_EXACT_POINT="Q / OUTSIDE_QUALIFIED_CYCLING_POINT"

@dataclass(frozen=True)
class QualifiedCyclingPoint:
    manufacturer_model_identifier: str
    certified_model_identifier: str
    outdoor_temperature_c: float
    supply_temperature_c: float
    minimum_capacity_kw: float
    minimum_input_kw: float
    declared_minimum_cop: float
    cdh: float
    cdh_status: str
    identity_correlated: bool
    point_pairing_explicit: bool

    def validate(self, *, cop_tolerance: float=0.05) -> None:
        if not self.manufacturer_model_identifier or not self.certified_model_identifier:
            raise ValueError("product identity is required")
        if not self.identity_correlated:
            raise ValueError("manufacturer/certification identity bridge is required")
        if not self.point_pairing_explicit:
            raise ValueError("minimum capacity/input/COP point pairing must be explicit")
        if self.minimum_capacity_kw <= 0 or self.minimum_input_kw <= 0:
            raise ValueError("minimum capacity and input must be positive")
        if self.declared_minimum_cop <= 0:
            raise ValueError("declared minimum COP must be positive")
        derived=self.minimum_capacity_kw/self.minimum_input_kw
        if abs(derived-self.declared_minimum_cop)>cop_tolerance:
            raise ValueError("minimum point COP is inconsistent beyond tolerance")
        if self.cdh_status != MEASUREMENT_DETERMINED:
            raise ValueError("measurement-determined product Cdh is required")
        if not (0 < self.cdh <= 1):
            raise ValueError("Cdh must be in (0,1]")
        if abs(self.cdh-0.9) <= 1e-12:
            raise ValueError("exact regulatory default Cdh remains ambiguous")

@dataclass(frozen=True)
class QualifiedCyclingEvaluation:
    status: str
    capacity_ratio: float
    cop_bin: float
    electrical_input_kw: float

def evaluate_exact_cycling_point(point: QualifiedCyclingPoint, *, required_capacity_kw: float) -> QualifiedCyclingEvaluation:
    point.validate()
    if required_capacity_kw <= 0:
        raise ValueError("required capacity must be positive")
    if required_capacity_kw >= point.minimum_capacity_kw:
        raise ValueError("qualified cycling calculation is only below the exact minimum capacity")
    cr=required_capacity_kw/point.minimum_capacity_kw
    cop_bin=water_side_cycling_cop(point.declared_minimum_cop,cr,point.cdh)
    return QualifiedCyclingEvaluation(
        status=QUALIFIED_POINT,
        capacity_ratio=cr,
        cop_bin=cop_bin,
        electrical_input_kw=required_capacity_kw/cop_bin,
    )

def p20_boundary() -> tuple[str,...]:
    return (
        "EXACT_PRODUCT_REQUIRED",
        "EXACT_A7_W35_COORDINATE_ONLY",
        "MIN_CAPACITY_INPUT_COP_POSITIONAL_PAIR_REQUIRED",
        "NONDEFAULT_MEASUREMENT_DETERMINED_CDH_REQUIRED",
        "NO_MODULATION_FLOOR_INTERPOLATION",
        "NO_MODULATION_FLOOR_EXTRAPOLATION",
        "ONE_QUALIFIED_POINT_IS_NOT_A_SURFACE",
    )
