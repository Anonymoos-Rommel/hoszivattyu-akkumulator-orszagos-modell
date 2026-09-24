"""B05-P17 exact-coordinate modulation anchor contract."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from modules.B05.part_load_runtime_contract import PartLoadRuntimeState, classify_part_load_runtime

ANCHOR_NOT_QUALIFIED = "Q / MODULATION_FLOOR_ANCHOR_NOT_QUALIFIED"
SURFACE_CONTRACT_REQUIRED = "MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED"

@dataclass(frozen=True)
class ModulationAnchor:
    model_identifier: str
    outdoor_temperature_c: float
    supply_temperature_c: float
    min_modulation_kw: float
    max_modulation_kw: float
    source_id: str
    def validate(self) -> None:
        if not self.model_identifier: raise ValueError("model_identifier is required")
        if self.min_modulation_kw <= 0: raise ValueError("min_modulation_kw must be positive")
        if self.max_modulation_kw <= 0: raise ValueError("max_modulation_kw must be positive")
        if self.min_modulation_kw > self.max_modulation_kw: raise ValueError("minimum modulation cannot exceed maximum modulation")
        if not self.source_id: raise ValueError("source_id is required")

@dataclass(frozen=True)
class AnchorResolution:
    status: str
    anchor: ModulationAnchor | None
    residual_gap: str | None

def resolve_exact_anchor(anchors: Iterable[ModulationAnchor], *, model_identifier: str, outdoor_temperature_c: float, supply_temperature_c: float, tolerance: float = 1e-9) -> AnchorResolution:
    matches = []
    for anchor in anchors:
        anchor.validate()
        if anchor.model_identifier == model_identifier and abs(anchor.outdoor_temperature_c-outdoor_temperature_c) <= tolerance and abs(anchor.supply_temperature_c-supply_temperature_c) <= tolerance:
            matches.append(anchor)
    if not matches:
        return AnchorResolution(ANCHOR_NOT_QUALIFIED,None,SURFACE_CONTRACT_REQUIRED)
    if len(matches) > 1:
        raise ValueError("duplicate exact modulation anchors")
    return AnchorResolution("EXACT_MODULATION_ANCHOR",matches[0],None)

def classify_at_exact_anchor(anchors: Iterable[ModulationAnchor], *, model_identifier: str, outdoor_temperature_c: float, supply_temperature_c: float, required_capacity_kw: float, available_capacity_kw: float) -> tuple[AnchorResolution, PartLoadRuntimeState | None]:
    resolution = resolve_exact_anchor(anchors,model_identifier=model_identifier,outdoor_temperature_c=outdoor_temperature_c,supply_temperature_c=supply_temperature_c)
    if resolution.anchor is None:
        return resolution,None
    return resolution,classify_part_load_runtime(required_capacity_kw,available_capacity_kw,resolution.anchor.min_modulation_kw)

def p17_boundary() -> tuple[str,...]:
    return ("EXACT_MODEL_IDENTITY_REQUIRED","EXACT_OUTDOOR_SUPPLY_COORDINATE_REQUIRED","NO_MIN_MODULATION_INTERPOLATION","NO_MIN_MODULATION_EXTRAPOLATION","NO_CROSS_PRODUCT_TRANSFER","NUMERIC_CYCLING_METHOD_REMAINS_SEPARATE")
