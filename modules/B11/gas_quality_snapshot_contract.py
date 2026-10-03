"""B11-P5 programme-aligned gas-quality snapshot gate.

Core rule:

    SOURCE ACCESS != TEMPORAL AUTHORITY != LOCATION MAPPING != REPOSITORY MATERIALIZATION

A programme gas-quality snapshot may authorize the B11 physical gas-volume bridge only
when the gas-quality point, reference period, GCV/LHV pair and participant-to-point
mapping are all explicit. Public source access alone is not enough.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum

from .gas_volume_bridge_contract import PhysicalEvidence
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

    pair = GasQualityPair(
        gcv_mj_m3=replace(
            snapshot.gcv_mj_m3,
            source_ref=snapshot.gcv_mj_m3.source_ref or snapshot.source_ref,
        ),
        lhv_mj_m3=replace(
            snapshot.lhv_mj_m3,
            source_ref=snapshot.lhv_mj_m3.source_ref or snapshot.source_ref,
        ),
    )
    pair.validated_values()
    # This is a validated handoff, not arithmetic. Preserve each value's status,
    # reference state, calorific basis and lineage rather than flattening them.
    return pair



def public_source_access_authorizes_repository_materialization() -> bool:
    return False


def historical_point_value_authorizes_current_programme_period() -> bool:
    return False
