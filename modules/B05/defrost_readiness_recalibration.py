"""B05-P54 successor-aware DEFROST readiness recalibration.

This scorecard updates the component maturity only. It does not create or
change the B05 module-level aggregation rule.
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
    ReadinessGate("DIRECT_CONTROLLER_STATE", 8, 8, "RESOLVED", ""),
    ReadinessGate("SAME_SYSTEM_RAW_EVENT_BOUNDARY", 10, 10, "RESOLVED", ""),
    ReadinessGate("ELECTRIC_METER_EVENT_COVERAGE", 10, 10, "RESOLVED", ""),
    ReadinessGate("ACTIVE_HEAT_MATCHED_EFFECT", 12, 12, "RESOLVED", ""),
    ReadinessGate(
        "SIGNED_THERMAL_ACTIVE_EFFECT",
        8,
        5,
        "PARTIAL",
        "SIGNED_NEGATIVE_THERMAL_REMAINS_SOURCE_BOUND_DER",
    ),
    ReadinessGate(
        "RECOVERY_FULL_CYCLE_ADMISSION",
        14,
        7,
        "PARTIAL",
        "RECOVERY_TAIL_CENSORING_AND_FULL_CYCLE_PARAMETER_ADMISSION_REQUIRED",
    ),
    ReadinessGate(
        "PASSIVE_BRANCH",
        8,
        4,
        "PARTIAL",
        "PASSIVE_INCREMENTAL_ELECTRIC_AND_THERMAL_DOMAIN_VALIDATION_REQUIRED",
    ),
    ReadinessGate(
        "DHW_BRANCH",
        10,
        7,
        "PARTIAL",
        "SIGNED_DHW_THERMAL_AND_FULL_CYCLE_TRANSFER_NOT_ADMITTED",
    ),
    ReadinessGate(
        "STATE_CONDITIONED_PREDICTIVE_MODEL",
        5,
        2,
        "PARTIAL",
        "STATE_CONDITIONED_PREDICTIVE_MODEL_VALIDATION_REQUIRED",
    ),
    ReadinessGate(
        "CROSS_PRODUCT_REPLICATION",
        10,
        0,
        "OPEN",
        "CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED",
    ),
    ReadinessGate(
        "HUNGARIAN_WEATHER_EVENT_TRANSFER",
        5,
        0,
        "OPEN",
        "HUNGARIAN_WEATHER_TRANSFER_VALIDATION_REQUIRED",
    ),
)

TOTAL_WEIGHT = sum(g.weight for g in GATES)
READINESS_SCORE = sum(g.earned for g in GATES)
MAX_WITHOUT_INDEPENDENT_REPLICATION = 65


def validate_scorecard() -> None:
    for gate in GATES:
        gate.validate()
    if TOTAL_WEIGHT != 100:
        raise ValueError("DEFROST readiness scorecard must total 100")
    if READINESS_SCORE != 65:
        raise ValueError("P54 canonical DEFROST readiness must be 65")
    if READINESS_SCORE > MAX_WITHOUT_INDEPENDENT_REPLICATION:
        raise ValueError("independent replication ceiling exceeded")


def can_exceed_current_ceiling(*, independent_replication: bool) -> bool:
    return independent_replication
