"""B11-P5 programme-aligned gas-quality snapshot gate.

Core rule:

    SOURCE ACCESS != TEMPORAL AUTHORITY != LOCATION MAPPING != REPOSITORY MATERIALIZATION

A programme gas-quality snapshot may authorize the B11 physical gas-volume bridge only
when the gas-quality point, reference period, GCV/LHV pair and participant-to-point
mapping are all explicit. Public source access alone is not enough.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import math

from .gas_volume_bridge_contract import EvidenceStatus, PhysicalEvidence
from .gas_efficiency_authority import GasQualityPair


class MappingStatus(str, Enum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    Q = "Q"


@dataclass(frozen=True)
class GasQualitySnapshot:
    point_id: str
    period_start: date
    period_end: date
    gcv_mj_m3: PhysicalEvidence
    lhv_mj_m3: PhysicalEvidence
    source_ref: str
    source_reference_period: str
    repository_materialization_authorized: bool


@dataclass(frozen=True)
class ParticipantGasPointMapping:
    participant_scope_id: str
    point_id: str | None
    status: MappingStatus
    source_ref: str | None = None


def _positive(value: float, label: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return float(value)


def authorize_programme_gas_quality(
    snapshot: GasQualitySnapshot,
    mapping: ParticipantGasPointMapping,
    programme_period_start: date,
    programme_period_end: date,
) -> GasQualityPair:
    """Authorize an exact programme-aligned GCV/LHV pair or fail closed."""

    if not snapshot.point_id.strip() or not snapshot.source_ref.strip():
        raise ValueError("gas-quality point and source reference are required")
    if snapshot.period_end < snapshot.period_start:
        raise ValueError("snapshot period is invalid")
    if programme_period_end < programme_period_start:
        raise ValueError("programme period is invalid")
    if snapshot.period_start > programme_period_start or snapshot.period_end < programme_period_end:
        raise ValueError("gas-quality snapshot does not cover programme period")
    if mapping.status != MappingStatus.EXACT or mapping.point_id is None:
        raise ValueError("exact participant-to-gas-quality-point mapping is required")
    if mapping.point_id != snapshot.point_id:
        raise ValueError("participant mapping and gas-quality point do not match")

    gcv = snapshot.gcv_mj_m3.numeric("MJ/m3_GCV")
    lhv = snapshot.lhv_mj_m3.numeric("MJ/m3_LHV")
    _positive(gcv, "GCV")
    _positive(lhv, "LHV")
    if gcv <= lhv:
        raise ValueError("GCV must be greater than LHV")

    statuses = {snapshot.gcv_mj_m3.status, snapshot.lhv_mj_m3.status}
    if EvidenceStatus.Q in statuses:
        raise ValueError("Q gas-quality evidence cannot authorize programme calculation")
    output_status = EvidenceStatus.SCN if EvidenceStatus.SCN in statuses else (
        EvidenceStatus.DER if EvidenceStatus.DER in statuses else EvidenceStatus.OBS
    )

    return GasQualityPair(
        gcv_mj_m3=PhysicalEvidence(gcv, "MJ/m3_GCV", output_status, snapshot.source_ref),
        lhv_mj_m3=PhysicalEvidence(lhv, "MJ/m3_LHV", output_status, snapshot.source_ref),
    )


def public_source_access_authorizes_repository_materialization() -> bool:
    return False


def historical_point_value_authorizes_current_programme_period() -> bool:
    return False
