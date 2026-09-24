"""B05-P23 barrier-aware modulation-floor surface for source-native gaps."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

OUTSIDE_SURFACE="Q / OUTSIDE_MODULATION_FLOOR_SURFACE"
MISSING_CORNER="Q / MISSING_MODULATION_FLOOR_CORNER"
SOURCE_GAP_BARRIER="Q / SOURCE_GAP_BARRIER"

@dataclass(frozen=True)
class FloorPoint:
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
            raise ValueError("source-native floor points must be OBS")

@dataclass(frozen=True)
class FloorResult:
    status: str
    minimum_capacity_kw: float | None
    source_ids: tuple[str,...]
    interpolation: str
    reason: str=""

class BarrierAwareFloorSurface:
    def __init__(
        self,
        model_identifier: str,
        points: Iterable[FloorPoint],
        *,
        blocked_outdoor_nodes: Iterable[float]=(),
    ):
        if not model_identifier:
            raise ValueError("model_identifier is required")
        self.model_identifier=model_identifier
        self.points=tuple(points)
        if not self.points:
            raise ValueError("surface requires points")
        self.blocked_outdoor_nodes=tuple(sorted(set(float(v) for v in blocked_outdoor_nodes)))
        self._grid={}
        for point in self.points:
            point.validate()
            key=(point.outdoor_temperature_c,point.supply_temperature_c)
            if key in self._grid:
                raise ValueError("duplicate floor point")
            if point.outdoor_temperature_c in self.blocked_outdoor_nodes:
                raise ValueError("blocked outdoor node cannot also be an observed floor point")
            self._grid[key]=point
        self._outdoor=tuple(sorted({k[0] for k in self._grid}.union(self.blocked_outdoor_nodes)))
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
                keys=((o0,s0),(o1,s0),(o0,s1),(o1,s1))
                if all(key in self._grid for key in keys):
                    count+=1
        return count

    def evaluate(self, outdoor_temperature_c: float, supply_temperature_c: float) -> FloorResult:
        exact=self._grid.get((outdoor_temperature_c,supply_temperature_c))
        if exact is not None:
            return FloorResult("OBS",exact.minimum_capacity_kw,(exact.source_id,),"exact")
        if outdoor_temperature_c in self.blocked_outdoor_nodes:
            return FloorResult(SOURCE_GAP_BARRIER,None,(),"none","requested outdoor node is a source-native minimum-floor gap")

        ob=self._bracket(outdoor_temperature_c,self._outdoor)
        sb=self._bracket(supply_temperature_c,self._supply)
        if ob is None or sb is None:
            return FloorResult(OUTSIDE_SURFACE,None,(),"none","outside source-native axis envelope")
        o0,o1=ob
        s0,s1=sb
        keys=((o0,s0),(o1,s0),(o0,s1),(o1,s1))
        try:
            p00,p10,p01,p11=(self._grid[k] for k in keys)
        except KeyError:
            return FloorResult(MISSING_CORNER,None,(),"none","complete non-barrier four-corner cell required")

        wo=0.0 if o1==o0 else (outdoor_temperature_c-o0)/(o1-o0)
        ws=0.0 if s1==s0 else (supply_temperature_c-s0)/(s1-s0)
        low=p00.minimum_capacity_kw + wo*(p10.minimum_capacity_kw-p00.minimum_capacity_kw)
        high=p01.minimum_capacity_kw + wo*(p11.minimum_capacity_kw-p01.minimum_capacity_kw)
        floor=low + ws*(high-low)
        sources=tuple(sorted({p.source_id for p in (p00,p10,p01,p11)}))
        return FloorResult("DER",floor,sources,"bilinear_bounded")

def p23_boundary() -> tuple[str,...]:
    return (
        "SOURCE_NATIVE_FLOOR_POINTS_ARE_OBS",
        "KNOWN_SOURCE_GAP_IS_INTERPOLATION_BARRIER",
        "COMPLETE_NONBARRIER_CELL_REQUIRED",
        "NO_INTERPOLATION_ACROSS_A_MINUS10",
        "NO_EXTRAPOLATION",
        "NO_CDH_INTERPOLATION_IN_THIS_CONTRACT",
        "NO_CROSS_PRODUCT_TRANSFER",
    )
