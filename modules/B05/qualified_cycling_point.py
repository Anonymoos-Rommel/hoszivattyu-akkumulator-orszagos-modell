"""Product-bin mathematics and separately source-bound physical admission.

WM50 P20/P22 and Dimplex P23/P42 lack the certified test-water/MIN join authority.
Supplying booleans or asserted test metadata cannot substitute for that source.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import math
from pathlib import Path

from modules.B05.cycling_degradation_method import water_side_cycling_cop
from modules.B05.cycling_input_colocation import MEASUREMENT_DETERMINED

QUALIFIED_POINT = "QUALIFIED_CYCLING_READY_POINT"
CONDITIONAL_POINT = "CONDITIONAL_STANDARD_METHOD_CALCULATION"
SOURCE_JOIN_REQUIRED = "Q / SOURCE_BOUND_CYCLING_JOIN_REQUIRED"
OUTSIDE_EXACT_POINT = "Q / OUTSIDE_QUALIFIED_CYCLING_POINT"
MANIFEST = Path(__file__).resolve().parents[2] / "registry/b05_cycling_source_admission_manifest.json"


@dataclass(frozen=True)
class CyclingSourceContext:
    """Requested source scope; every field is checked against retained evidence."""
    observation_id: str | None = None
    source_id: str | None = None
    document_revision: str | None = None
    component: str | None = None
    climate: str | None = None
    application: str | None = None
    test_water_control: str | None = None
    test_water_temperature_c: float | None = None


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
    minimum_source_id: str | None = None
    source_context: CyclingSourceContext | None = None
    minimum_document_revision: str | None = None

    def validate(self, *, cop_tolerance: float = 0.05) -> None:
        """Check conditional numeric preconditions, not source qualification."""
        if not self.manufacturer_model_identifier or not self.certified_model_identifier:
            raise ValueError("product identity is required")
        if not self.identity_correlated:
            raise ValueError("manufacturer/certification identity bridge is required")
        if not self.point_pairing_explicit:
            raise ValueError("minimum capacity/input/COP point pairing must be explicit")
        values = (self.outdoor_temperature_c, self.supply_temperature_c,
                  self.minimum_capacity_kw, self.minimum_input_kw,
                  self.declared_minimum_cop, self.cdh, cop_tolerance)
        if not all(math.isfinite(v) for v in values) or cop_tolerance < 0:
            raise ValueError("finite numeric inputs and nonnegative tolerance required")
        if self.minimum_capacity_kw <= 0 or self.minimum_input_kw <= 0:
            raise ValueError("minimum capacity and input must be positive")
        if self.declared_minimum_cop <= 0:
            raise ValueError("declared minimum COP must be positive")
        derived = self.minimum_capacity_kw / self.minimum_input_kw
        if abs(derived - self.declared_minimum_cop) > cop_tolerance:
            raise ValueError("minimum point COP is inconsistent beyond tolerance")
        if self.cdh_status != MEASUREMENT_DETERMINED:
            raise ValueError("measurement-determined product Cdh is required")
        if not (0 < self.cdh <= 1):
            raise ValueError("Cdh must be in (0,1]")
        if abs(self.cdh - 0.9) <= 1e-12:
            raise ValueError("exact regulatory default Cdh remains ambiguous")


@dataclass(frozen=True)
class QualifiedCyclingEvaluation:
    status: str
    capacity_ratio: float
    cop_bin: float | None
    electrical_input_kw: float | None
    residual_gaps: tuple[str, ...] = ()


def _capacity_ratio(point: QualifiedCyclingPoint, required_capacity_kw: float) -> float:
    point.validate()
    if not math.isfinite(required_capacity_kw) or required_capacity_kw <= 0:
        raise ValueError("required capacity must be finite and positive")
    if required_capacity_kw >= point.minimum_capacity_kw:
        raise ValueError("cycling calculation is only below the exact minimum capacity")
    return required_capacity_kw / point.minimum_capacity_kw


def evaluate_conditional_cycling_point(point: QualifiedCyclingPoint, *, required_capacity_kw: float) -> QualifiedCyclingEvaluation:
    """P18 arithmetic conditional on inputs; not physical or hourly admission."""
    cr = _capacity_ratio(point, required_capacity_kw)
    cop_bin = water_side_cycling_cop(point.declared_minimum_cop, cr, point.cdh)
    return QualifiedCyclingEvaluation(CONDITIONAL_POINT, cr, cop_bin, required_capacity_kw / cop_bin)


def source_admission_gaps(point: QualifiedCyclingPoint) -> tuple[str, ...]:
    """Compare requested scope with the reviewed manifest, never caller flags.

    A future admitted join must bind the exact manufacturer point and carry
    its own source/revision/locator. No current observation has such a join.
    Editing that evidence is a separate reviewed source-admission change.
    """
    context = point.source_context
    if context is None:
        return ("SOURCE_CONTEXT_REQUIRED",)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    observations = [r for r in manifest["observations"]
                    if r["observation_id"] == context.observation_id]
    if len(observations) != 1:
        return ("CURRENT_SOURCE_OBSERVATION_REQUIRED",)
    obs = observations[0]
    gaps = []
    sources = [r for r in manifest["sources"] if r["source_id"] == obs["source_id"]]
    if len(sources) != 1:
        return ("CURRENT_SOURCE_IDENTITY_REQUIRED",)
    source = sources[0]
    for field in ("document_revision", "model_identifier", "component"):
        if not obs.get(field) or obs.get(field) != source.get(field):
            gaps.append("RETAINED_SOURCE_" + field.upper() + "_MISMATCH")
    manufacturers = [r for r in manifest["current_manufacturer_revisions"]
                     if r["source_id"] == point.minimum_source_id]
    if len(manufacturers) != 1:
        gaps.append("CURRENT_MANUFACTURER_REVISION_REQUIRED")
    else:
        manufacturer = manufacturers[0]
        if not point.minimum_document_revision:
            gaps.append("MANUFACTURER_DOCUMENT_REVISION_REQUIRED")
        elif point.minimum_document_revision != manufacturer["document_revision"]:
            gaps.append("MANUFACTURER_DOCUMENT_REVISION_MISMATCH")
        if point.manufacturer_model_identifier != manufacturer["manufacturer_model_identifier"]:
            gaps.append("MANUFACTURER_MODEL_MISMATCH")
    for field in ("source_id", "document_revision", "component", "climate", "application",
                  "test_water_control", "test_water_temperature_c"):
        declared, retained = getattr(context, field), obs.get(field)
        if declared is None or retained is None:
            gaps.append(field.upper() + "_AUTHORITY_REQUIRED")
        elif declared != retained:
            gaps.append(field.upper() + "_MISMATCH")
    if obs["model_identifier"] != point.certified_model_identifier:
        gaps.append("CERTIFIED_MODEL_MISMATCH")
    if obs["outdoor_temperature_c"] != point.outdoor_temperature_c:
        gaps.append("OUTDOOR_TEMPERATURE_MISMATCH")
    if obs["cdh"] != point.cdh:
        gaps.append("CDH_VALUE_MISMATCH")
    if obs.get("test_water_temperature_c") != point.supply_temperature_c:
        gaps.append("EXACT_WATER_COORDINATE_AUTHORITY_REQUIRED")
    if not obs.get("test_condition_authority"):
        gaps.append("SOURCE_BOUND_TEST_CONDITION_AUTHORITY_REQUIRED")
    join = obs.get("admitted_minimum_point_join")
    if not join:
        gaps.append("SOURCE_BOUND_MINIMUM_POINT_JOIN_REQUIRED")
    else:
        if (join.get("claim_status") != "QUALIFIED_EXACT_PHYSICAL_COORDINATE"
                or not all(join.get(k) for k in ("authority_source_id", "document_revision", "locator"))):
            gaps.append("EXACT_PHYSICAL_JOIN_AUTHORITY_REQUIRED")
        for field in ("minimum_source_id", "minimum_document_revision", "manufacturer_model_identifier", "outdoor_temperature_c",
                      "supply_temperature_c", "minimum_capacity_kw", "minimum_input_kw", "declared_minimum_cop"):
            if getattr(point, field) is None or join.get(field) != getattr(point, field):
                gaps.append("MINIMUM_POINT_" + field.upper() + "_MISMATCH")
    return tuple(gaps)


def evaluate_exact_cycling_point(point: QualifiedCyclingPoint, *, required_capacity_kw: float) -> QualifiedCyclingEvaluation:
    """Return physical Q without numeric outputs until the source join qualifies."""
    cr = _capacity_ratio(point, required_capacity_kw)
    gaps = source_admission_gaps(point)
    if gaps:
        return QualifiedCyclingEvaluation(SOURCE_JOIN_REQUIRED, cr, None, None, gaps)
    cop_bin = water_side_cycling_cop(point.declared_minimum_cop, cr, point.cdh)
    return QualifiedCyclingEvaluation(QUALIFIED_POINT, cr, cop_bin, required_capacity_kw / cop_bin)


def p20_boundary() -> tuple[str, ...]:
    return (
        "EXACT_PRODUCT_REQUIRED",
        "MIN_CAPACITY_INPUT_COP_POSITIONAL_PAIR_REQUIRED",
        "NONDEFAULT_MEASUREMENT_DETERMINED_CDH_REQUIRED",
        "SOURCE_BOUND_CLIMATE_APPLICATION_COMPONENT_REVISION_REQUIRED",
        "SOURCE_BOUND_TEST_WATER_AND_MINIMUM_POINT_JOIN_REQUIRED",
        "CALLER_BOOLEANS_DO_NOT_ESTABLISH_SOURCE_ADMISSION",
        "CONDITIONAL_MATHEMATICS_IS_NOT_PHYSICAL_QUALIFICATION",
        "NO_MODULATION_FLOOR_INTERPOLATION",
        "NO_MODULATION_FLOOR_EXTRAPOLATION",
        "ONE_QUALIFIED_POINT_IS_NOT_A_SURFACE",
    )
