"""B05-P21 bounded minimum-modulation surface contract."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

OUTSIDE_SURFACE="Q / OUTSIDE_MODULATION_FLOOR_SURFACE"
MISSING_CORNER="Q / MISSING_MODULATION_FLOOR_CORNER"

@dataclass(frozen=True)
class ModulationFloorPoint:
    outdoor_temperature_c: float
    supply_temperature_c: float
    minimum_capacity_kw: float
    source_id: str
    evidence_status: str="OBS"

    def validate(self) -> None:
        if self.minimum_capacity_kw <= 0:
            raise ValueError("minimum_capacity_kw must be positive")
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.evidence_status != "OBS":
            raise ValueError("P21 source-native corners must be OBS")

@dataclass(frozen=True)
class ModulationFloorResult:
    status: str
    minimum_capacity_kw: float | None
    source_ids: tuple[str,...]
    interpolation: str
    reason: str=""

class ModulationFloorSurface:
    def __init__(self, model_identifier: str, points: Iterable[ModulationFloorPoint]):
        if not model_identifier:
            raise ValueError("model_identifier is required")
        self.model_identifier=model_identifier
        self.points=tuple(points)
        if not self.points:
            raise ValueError("surface requires points")
        self._grid={}
        for point in self.points:
            point.validate()
            key=(point.outdoor_temperature_c,point.supply_temperature_c)
            if key in self._grid:
                raise ValueError("duplicate modulation-floor point")
            self._grid[key]=point
        self._outdoor=tuple(sorted({k[0] for k in self._grid}))
        self._supply=tuple(sorted({k[1] for k in self._grid}))

    @staticmethod
    def _bracket(value: float, axis: tuple[float,...]) -> tuple[float,float] | None:
        if value < axis[0] or value > axis[-1]:
            return None
        for lower,upper in zip(axis,axis[1:]):
            if lower <= value <= upper:
                return lower,upper
        return axis[-1],axis[-1]

    def evaluate(self, outdoor_temperature_c: float, supply_temperature_c: float) -> ModulationFloorResult:
        exact=self._grid.get((outdoor_temperature_c,supply_temperature_c))
        if exact is not None:
            return ModulationFloorResult("OBS",exact.minimum_capacity_kw,(exact.source_id,),"exact")

        ob=self._bracket(outdoor_temperature_c,self._outdoor)
        sb=self._bracket(supply_temperature_c,self._supply)
        if ob is None or sb is None:
            return ModulationFloorResult(OUTSIDE_SURFACE,None,(),"none","outside bounded source-native rectangle")
        o0,o1=ob
        s0,s1=sb
        keys=((o0,s0),(o1,s0),(o0,s1),(o1,s1))
        try:
            p00,p10,p01,p11=(self._grid[k] for k in keys)
        except KeyError:
            return ModulationFloorResult(MISSING_CORNER,None,(),"none","complete four-corner floor rectangle required")

        wo=0.0 if o1==o0 else (outdoor_temperature_c-o0)/(o1-o0)
        ws=0.0 if s1==s0 else (supply_temperature_c-s0)/(s1-s0)
        low=p00.minimum_capacity_kw + wo*(p10.minimum_capacity_kw-p00.minimum_capacity_kw)
        high=p01.minimum_capacity_kw + wo*(p11.minimum_capacity_kw-p01.minimum_capacity_kw)
        floor=low + ws*(high-low)
        sources=tuple(sorted({p.source_id for p in (p00,p10,p01,p11)}))
        return ModulationFloorResult("DER",floor,sources,"bilinear_bounded")

def p21_boundary() -> tuple[str,...]:
    return (
        "SOURCE_NATIVE_CORNERS_REMAIN_OBS",
        "COMPLETE_FOUR_CORNER_RECTANGLE_REQUIRED",
        "RECTANGLE_INTERIOR_IS_DER",
        "NO_MODULATION_FLOOR_EXTRAPOLATION",
        "NO_GRAPH_DIGITIZATION",
        "NO_CROSS_PRODUCT_TRANSFER",
        "COORDINATE_WEIGHTED_NOT_UNWEIGHTED_AVERAGE",
    )
