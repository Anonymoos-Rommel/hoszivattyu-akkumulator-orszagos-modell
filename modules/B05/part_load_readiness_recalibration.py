"""B05-P59 successor-aware PART_LOAD_MODULATION readiness recalibration.

P15-P58 accumulated product-specific modulation, cycling, field-runtime and
fan-coil transient evidence while deliberately keeping the component at 45.
P59 scores that canonical evidence explicitly.  It changes component maturity
only; it does not define or alter B05 module-level aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessGate:
    gate_id: str
    weight: int
    earned: int
    status: str
    residual: str

    def validate(self) -> None:
        if self.weight <= 0:
            raise ValueError("weight must be positive")
        if self.earned < 0 or self.earned > self.weight:
            raise ValueError("earned must be within [0, weight]")
        if self.status not in {"RESOLVED", "PARTIAL", "OPEN"}:
            raise ValueError("invalid gate status")


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
        8, 8, "RESOLVED", "",
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

TOTAL_WEIGHT = sum(g.weight for g in GATES)
READINESS_SCORE = sum(g.earned for g in GATES)


def validate_scorecard() -> None:
    for gate in GATES:
        gate.validate()
    if TOTAL_WEIGHT != 100:
        raise ValueError("PART_LOAD_MODULATION readiness scorecard must total 100")
    if READINESS_SCORE != 75:
        raise ValueError("P59 canonical PART_LOAD_MODULATION readiness must be 75")


def unresolved_gate_ids() -> tuple[str, ...]:
    return tuple(g.gate_id for g in GATES if g.status != "RESOLVED")


def open_gate_ids() -> tuple[str, ...]:
    return tuple(g.gate_id for g in GATES if g.status == "OPEN")
