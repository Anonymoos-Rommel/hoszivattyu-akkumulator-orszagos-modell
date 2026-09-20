"""B02-P58 electrical transition gate.

The programme must not equate today's meter/service capacity with technical
heat-pump eligibility. Existing supply may be adequate, upgradeable, or
insufficient. The decisive question is whether the required heat-pump electrical
demand can be supplied through an explicit DSO-admitted transition path.

CURRENT ELECTRICAL READY != ONLY ELIGIBLE STATE
CURRENT ELECTRICAL NOT READY != AUTOMATIC INELIGIBILITY
UNKNOWN DSO FEASIBILITY != PASS
DSO REFUSAL / PROVEN UNSERVABLE DEMAND -> BLOCKED
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"
BLOCKED = "BLOCKED"
OBS = "OBS"
DER = "DER"
REAL_EVIDENCE = frozenset({OBS, DER})

USE_EXISTING_CONNECTION = "USE_EXISTING_CONNECTION"
UPGRADE_CONNECTION = "UPGRADE_CONNECTION"
NEW_DEDICATED_CONNECTION_OR_METER = "NEW_DEDICATED_CONNECTION_OR_METER"
ELECTRICAL_PATHS = frozenset(
    {
        USE_EXISTING_CONNECTION,
        UPGRADE_CONNECTION,
        NEW_DEDICATED_CONNECTION_OR_METER,
    }
)

DSO_APPROVED = "DSO_APPROVED"
DSO_NOT_REQUIRED = "DSO_NOT_REQUIRED"
DSO_PENDING = "DSO_PENDING"
DSO_REFUSED = "DSO_REFUSED"
DSO_STATUSES = frozenset(
    {DSO_APPROVED, DSO_NOT_REQUIRED, DSO_PENDING, DSO_REFUSED}
)


@dataclass(frozen=True)
class ElectricalTransitionCandidate:
    record_id: str
    transition_path: str
    current_connection_evidence_status: str
    current_phase_count: int | None
    current_available_current_a_per_phase: float | None
    heat_pump_nominal_electrical_kw: float | None
    auxiliary_electrical_kw: float | None
    starting_current_or_inverter_basis_documented: bool
    required_phase_count: int | None
    required_current_a_per_phase: float | None
    meter_or_service_upgrade_scope_documented: bool
    dedicated_heat_pump_circuit_documented: bool
    dso_status: str
    dso_evidence_refs_present: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class ElectricalTransitionDecision:
    status: str
    reasons: tuple[str, ...]


def assess_electrical_transition(
    candidate: ElectricalTransitionCandidate,
) -> ElectricalTransitionDecision:
    reasons: list[str] = []

    if not candidate.record_id.strip():
        reasons.append("RECORD_ID_MISSING")
    if candidate.transition_path not in ELECTRICAL_PATHS:
        reasons.append("ELECTRICAL_TRANSITION_PATH_UNKNOWN")
    if candidate.current_connection_evidence_status not in REAL_EVIDENCE:
        reasons.append("CURRENT_CONNECTION_EVIDENCE_NOT_OBS_OR_DER")
    if candidate.current_phase_count not in {1, 3}:
        reasons.append("CURRENT_PHASE_COUNT_INVALID")

    current_a = candidate.current_available_current_a_per_phase
    if current_a is None or not isfinite(current_a) or current_a <= 0:
        reasons.append("CURRENT_AVAILABLE_CURRENT_INVALID")

    hp_kw = candidate.heat_pump_nominal_electrical_kw
    if hp_kw is None or not isfinite(hp_kw) or hp_kw <= 0:
        reasons.append("HEAT_PUMP_ELECTRICAL_POWER_INVALID")

    aux_kw = candidate.auxiliary_electrical_kw
    if aux_kw is None or not isfinite(aux_kw) or aux_kw < 0:
        reasons.append("AUXILIARY_ELECTRICAL_POWER_INVALID")

    if not candidate.starting_current_or_inverter_basis_documented:
        reasons.append("STARTING_CURRENT_OR_INVERTER_BASIS_MISSING")
    if candidate.required_phase_count not in {1, 3}:
        reasons.append("REQUIRED_PHASE_COUNT_INVALID")

    required_a = candidate.required_current_a_per_phase
    if required_a is None or not isfinite(required_a) or required_a <= 0:
        reasons.append("REQUIRED_CURRENT_INVALID")

    if candidate.transition_path in {
        UPGRADE_CONNECTION,
        NEW_DEDICATED_CONNECTION_OR_METER,
    } and not candidate.meter_or_service_upgrade_scope_documented:
        reasons.append("METER_OR_SERVICE_UPGRADE_SCOPE_MISSING")

    if not candidate.dedicated_heat_pump_circuit_documented:
        reasons.append("HEAT_PUMP_CIRCUIT_BASIS_MISSING")

    if candidate.dso_status not in DSO_STATUSES:
        reasons.append("DSO_STATUS_UNKNOWN")
    elif candidate.dso_status == DSO_REFUSED:
        return ElectricalTransitionDecision(
            BLOCKED, ("DSO_CONNECTION_OR_CAPACITY_REFUSED",)
        )
    elif candidate.dso_status == DSO_PENDING:
        reasons.append("DSO_FEASIBILITY_PENDING")

    if candidate.dso_status in {DSO_APPROVED, DSO_NOT_REQUIRED}:
        if not candidate.dso_evidence_refs_present:
            reasons.append("DSO_EVIDENCE_REFS_MISSING")

    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return ElectricalTransitionDecision(Q, tuple(reasons))
    return ElectricalTransitionDecision(QUALIFIED, ())
