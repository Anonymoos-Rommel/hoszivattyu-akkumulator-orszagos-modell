"""B05-P22 same-product minimum-point capacity/COP surface."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

OUTSIDE_SURFACE="Q / OUTSIDE_MINIMUM_POINT_SURFACE"
MISSING_CORNER="Q / MISSING_MINIMUM_POINT_CORNER"

@dataclass(frozen=True)
class MinimumPoint:
    outdoor_temperature_c: float
    supply_temperature_c: float
    minimum_capacity_kw: float
    minimum_cop: float
    source_id: str
    evidence_status: str="OBS"

    def validate(self) -> None:
        if self.minimum_capacity_kw <= 0:
            raise ValueError("minimum_capacity_kw must be positive")
        if self.minimum_cop <= 0:
            raise ValueError("minimum_cop must be positive")
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.evidence_status != "OBS":
            raise ValueError("source-native minimum points must be OBS")

@dataclass(frozen=True)
class MinimumPointResult:
    status: str
    minimum_capacity_kw: float | None
    minimum_cop: float | None
    minimum_input_kw: float | None
    source_ids: tuple[str,...]
    interpolation: str
    reason: str=""

class MinimumPointSurface:
    def __init__(self, model_identifier: str, points: Iterable[MinimumPoint]):
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
                raise ValueError("duplicate minimum point")
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

    def qualified_cell_count(self) -> int:
        count=0
        for o0,o1 in zip(self._outdoor,self._outdoor[1:]):
            for s0,s1 in zip(self._supply,self._supply[1:]):
                if all(key in self._grid for key in ((o0,s0),(o1,s0),(o0,s1),(o1,s1))):
                    count+=1
        return count

    def evaluate(self, outdoor_temperature_c: float, supply_temperature_c: float) -> MinimumPointResult:
        exact=self._grid.get((outdoor_temperature_c,supply_temperature_c))
        if exact is not None:
            return MinimumPointResult(
                "OBS",
                exact.minimum_capacity_kw,
                exact.minimum_cop,
                exact.minimum_capacity_kw/exact.minimum_cop,
                (exact.source_id,),
                "exact",
            )

        ob=self._bracket(outdoor_temperature_c,self._outdoor)
        sb=self._bracket(supply_temperature_c,self._supply)
        if ob is None or sb is None:
            return MinimumPointResult(OUTSIDE_SURFACE,None,None,None,(),"none","outside source-native axis envelope")
        o0,o1=ob
        s0,s1=sb
        keys=((o0,s0),(o1,s0),(o0,s1),(o1,s1))
        try:
            p00,p10,p01,p11=(self._grid[k] for k in keys)
        except KeyError:
            return MinimumPointResult(MISSING_CORNER,None,None,None,(),"none","complete four-corner minimum-point cell required")

        wo=0.0 if o1==o0 else (outdoor_temperature_c-o0)/(o1-o0)
        ws=0.0 if s1==s0 else (supply_temperature_c-s0)/(s1-s0)

        def bilinear(attr: str) -> float:
            a00=getattr(p00,attr); a10=getattr(p10,attr); a01=getattr(p01,attr); a11=getattr(p11,attr)
            low=a00 + wo*(a10-a00)
            high=a01 + wo*(a11-a01)
            return low + ws*(high-low)

        floor=bilinear("minimum_capacity_kw")
        cop=bilinear("minimum_cop")
        sources=tuple(sorted({p.source_id for p in (p00,p10,p01,p11)}))
        return MinimumPointResult("DER",floor,cop,floor/cop,sources,"bilinear_bounded")

def p22_boundary() -> tuple[str,...]:
    return (
        "EXACT_DATABOOK_MIN_POINTS_ARE_OBS",
        "MIN_CAPACITY_AND_COP_STAY_POINT_PAIRED",
        "COMPLETE_CELL_REQUIRED_FOR_DER",
        "BLANK_SOURCE_CELL_REMAINS_Q",
        "NO_EXTRAPOLATION",
        "NO_CDH_INTERPOLATION_IN_THIS_CONTRACT",
        "NO_CROSS_PRODUCT_TRANSFER",
    )
