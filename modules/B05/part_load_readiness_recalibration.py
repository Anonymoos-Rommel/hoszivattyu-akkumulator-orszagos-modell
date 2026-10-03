"""B05-P59 successor-aware PART_LOAD_MODULATION readiness recalibration.

P15-P58 accumulated product-specific modulation, cycling, field-runtime and
fan-coil transient evidence while deliberately keeping the component at 45.
P59 historically scored that evidence at 75. V1-035 retains 67 supported
points and leaves the original 8-point exact-bin cycling criterion unassessed.
The current total is Q/None pending explicit reassessment; neither 67 nor 75
is a current score. B05 module-level aggregation remains undefined.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessGate:
    gate_id: str
    weight: int
    earned: int | None
    status: str
    residual: str

    def validate(self) -> None:
        if self.weight <= 0:
            raise ValueError("weight must be positive")
        if self.status not in {"RESOLVED", "PARTIAL", "OPEN", "UNASSESSED"}:
            raise ValueError("invalid gate status")
        if self.status == "UNASSESSED":
            if self.earned is not None or not self.residual:
                raise ValueError("unassessed gate requires no earned score and an explicit residual")
        elif self.earned is None or not 0 <= self.earned <= self.weight:
            raise ValueError("assessed earned must be within [0, weight]")


GATES = (
    ReadinessGate(
        "SOURCE_NATIVE_MINIMUM_MODULATION_SURFACES",
        14, 14, "RESOLVED", "",
    ),
    ReadinessGate(
        "POINT_PAIRED_MINIMUM_CAPACITY_COP",
        8, 8, "RESOLVED", "",
    ),
    ReadinessGate(
        "MULTI_MANUFACTURER_BOUNDED_PRODUCT_EVIDENCE",
        8, 8, "RESOLVED", "",
    ),
    ReadinessGate(
        "CERTIFIED_PART_LOAD_CDH_EVIDENCE",
        10, 10, "RESOLVED", "",
    ),
    ReadinessGate(
        "EN14825_STANDARD_BIN_CYCLING_METHOD",
        8, None, "UNASSESSED",
        "EXACT_FIXED_WATER_MINIMUM_POINT_TO_CERTIFIED_CDH_PHYSICAL_JOIN_REQUIRED",
    ),
    ReadinessGate(
        "HOURLY_CYCLING_METHOD_SEPARATION",
        8, 8, "RESOLVED", "",
    ),
    ReadinessGate(
        "EXPLICIT_BOUNDED_DEFAULT_RUNTIME_POLICY",
        6, 6, "RESOLVED", "",
    ),
    ReadinessGate(
        "COLD_HIGH_SUPPLY_COORDINATE_COVERAGE",
        8, 5, "PARTIAL",
        "EXACT_SOURCE_NATIVE_A_MINUS15_W50_2D_OPERATING_OR_PERFORMANCE_RECORD_REQUIRED",
    ),
    ReadinessGate(
        "DIRECT_FIELD_CYCLING_MODULATION_VALIDATION",
        8, 5, "PARTIAL",
        "CROSS_PRODUCT_FIELD_CYCLING_VALIDATION_REQUIRED",
    ),
    ReadinessGate(
        "EXACT_FCU_TRANSIENT_PHYSICS_AND_DIRECT_RUNTIME",
        8, 3, "PARTIAL",
        "EXACT_CITED_EDITION_FCC06_WATER_CONTENT_OR_DIRECT_WATER_MASS_REQUIRED_FOR_OBS_TRANSIENT_VALIDATION",
    ),
    ReadinessGate(
        "PRODUCT_SPECIFIC_HEAT_PUMP_TRANSIENT_AUTHORITY",
        8, 0, "OPEN",
        "EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED;EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED",
    ),
    ReadinessGate(
        "EXACT_FCC06_OBS_TRANSIENT_MASS_BINDING",
        6, 0, "OPEN",
        "EXACT_CITED_EDITION_FCC06_WATER_CONTENT_OR_DIRECT_WATER_MASS_REQUIRED_FOR_OBS_TRANSIENT_VALIDATION",
    ),
)

# Original P59 weights and awarded points are historical facts, not a new
# allocation between conditional mathematics and a qualified physical join.
HISTORICAL_GATE_CREDITS = {
    "SOURCE_NATIVE_MINIMUM_MODULATION_SURFACES": (14, 14),
    "POINT_PAIRED_MINIMUM_CAPACITY_COP": (8, 8),
    "MULTI_MANUFACTURER_BOUNDED_PRODUCT_EVIDENCE": (8, 8),
    "CERTIFIED_PART_LOAD_CDH_EVIDENCE": (10, 10),
    "EN14825_STANDARD_BIN_CYCLING_METHOD": (8, 8),
    "HOURLY_CYCLING_METHOD_SEPARATION": (8, 8),
    "EXPLICIT_BOUNDED_DEFAULT_RUNTIME_POLICY": (6, 6),
    "COLD_HIGH_SUPPLY_COORDINATE_COVERAGE": (8, 5),
    "DIRECT_FIELD_CYCLING_MODULATION_VALIDATION": (8, 5),
    "EXACT_FCU_TRANSIENT_PHYSICS_AND_DIRECT_RUNTIME": (8, 3),
    "PRODUCT_SPECIFIC_HEAT_PUMP_TRANSIENT_AUTHORITY": (8, 0),
    "EXACT_FCC06_OBS_TRANSIENT_MASS_BINDING": (6, 0),
}
UNASSESSED_GATE_ID = "EN14825_STANDARD_BIN_CYCLING_METHOD"
TOTAL_WEIGHT = sum(g.weight for g in GATES)
HISTORICAL_READINESS_SCORE = sum(earned for _, earned in HISTORICAL_GATE_CREDITS.values())
SUPPORTED_EARNED_SUBTOTAL = sum(g.earned for g in GATES if g.earned is not None)
UNASSESSED_WEIGHT = sum(g.weight for g in GATES if g.earned is None)
READINESS_SCORE: int | None = None
READINESS_STATUS = "Q"


def validate_scorecard() -> None:
    if tuple(g.gate_id for g in GATES) != tuple(HISTORICAL_GATE_CREDITS):
        raise ValueError("original P59 gate IDs must be preserved exactly")
    for gate in GATES:
        gate.validate()
        original_weight, original_earned = HISTORICAL_GATE_CREDITS[gate.gate_id]
        if gate.weight != original_weight:
            raise ValueError("original P59 gate weights must be preserved")
        if gate.gate_id == UNASSESSED_GATE_ID:
            if gate.earned is not None or gate.status != "UNASSESSED":
                raise ValueError("original exact-bin cycling criterion must remain unassessed")
        else:
            if gate.earned != original_earned:
                raise ValueError("unaffected P59 earned points must be preserved")
            expected_status = (
                "RESOLVED" if original_earned == original_weight
                else "OPEN" if original_earned == 0 else "PARTIAL"
            )
            if gate.status != expected_status:
                raise ValueError("unaffected P59 gate status must be preserved")
    if TOTAL_WEIGHT != 100 or sum(g.weight for g in GATES) != 100:
        raise ValueError("PART_LOAD_MODULATION readiness scorecard must total 100")
    if HISTORICAL_READINESS_SCORE != 75:
        raise ValueError("historical P59 score must remain 75")
    if SUPPORTED_EARNED_SUBTOTAL != 67 or sum(g.earned for g in GATES if g.earned is not None) != 67:
        raise ValueError("supported unaffected subtotal must remain 67")
    if UNASSESSED_WEIGHT != 8 or sum(g.weight for g in GATES if g.earned is None) != 8:
        raise ValueError("original unassessed criterion must retain weight 8")
    if READINESS_SCORE is not None or READINESS_STATUS != "Q":
        raise ValueError("current PART_LOAD_MODULATION readiness must remain Q/unassessed")


def unresolved_gate_ids() -> tuple[str, ...]:
    return tuple(g.gate_id for g in GATES if g.status != "RESOLVED")


def open_gate_ids() -> tuple[str, ...]:
    return tuple(g.gate_id for g in GATES if g.status == "OPEN")
