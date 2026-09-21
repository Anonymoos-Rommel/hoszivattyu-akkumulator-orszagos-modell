"""B02-P70 KSH/P22 distribution non-reuse assignment.

P70 consumes the exact 2022 KSH occupied-stock heating-topology assignment from
P22 and asks a programme-route-specific question:

For a CENTRAL_HYDRONIC_AWHP transition, which current heating-topology cells
cannot reuse an existing central thermal-distribution system?

KSH defines the NHEAT domain as room-by-room heating (rooms heated individually
by convector, stove or another device) and also includes dwellings where no
heating equipment / heating conditions existed at enumeration.

Therefore, on the explicitly bounded CENTRAL_HYDRONIC_AWHP route:

ROOM_BY_ROOM_OR_NO_HEAT -> NEW_OR_REPLACE_DISTRIBUTION_REQUIRED.

This does not identify the emitter subtype, the new distribution design, or
room-grain KEEP/UPSIZE/CHANGE/ADD actions.

P39 gas-convector and P22 NHEAT population constraints are not added because
their overlap is not identified. The valid national lower bound is their max.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from modules.B02.emitter_marginal_reconciliation import (
    PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
)
from modules.B02.heating_system_assignment import build_heating_system_assignment


CENTRAL_HYDRONIC_AWHP = "CENTRAL_HYDRONIC_AWHP"
QUALIFIED = "QUALIFIED"
Q = "Q"


@dataclass(frozen=True)
class DistributionNonreuseAssignment:
    occupied_dwellings: int
    room_by_room_or_no_heat_dwellings: int
    room_by_room_or_no_heat_share: float
    gas_convector_calibrated_share: float
    proven_nonreuse_lower_share: float
    proven_nonreuse_lower_dwellings: float
    reuse_upper_share: float
    route_status: str
    evidence_status: str


@dataclass(frozen=True)
class DistributionRouteDecision:
    status: str
    blockers: tuple[str, ...]


def assess_programme_route(target_route: str) -> DistributionRouteDecision:
    if target_route != CENTRAL_HYDRONIC_AWHP:
        return DistributionRouteDecision(
            Q,
            ("P70_ONLY_AUTHORIZES_CENTRAL_HYDRONIC_AWHP_ROUTE",),
        )
    return DistributionRouteDecision(QUALIFIED, ())


@lru_cache(maxsize=4)
def build_distribution_nonreuse_assignment(
    *,
    target_route: str = CENTRAL_HYDRONIC_AWHP,
) -> DistributionNonreuseAssignment:
    route = assess_programme_route(target_route)
    if route.status != QUALIFIED:
        raise ValueError(";".join(route.blockers))

    _rows, topology = build_heating_system_assignment()
    occupied = topology.occupied_dwellings
    nheat = topology.room_by_room_or_no_heat_dwellings

    if occupied <= 0:
        raise ValueError("occupied dwelling universe must be positive")
    if nheat < 0 or nheat > occupied:
        raise ValueError("P22 NHEAT count outside occupied universe")

    nheat_share = nheat / occupied

    # The P39 gas-convector calibrated marginal and the exact P22 NHEAT
    # topology control can overlap, but that overlap is not fully identified.
    # A fail-closed union lower bound is therefore max(), never sum().
    lower_share = max(nheat_share, PRIMARY_HEATING_GAS_CONVECTOR_SHARE)

    return DistributionNonreuseAssignment(
        occupied_dwellings=occupied,
        room_by_room_or_no_heat_dwellings=nheat,
        room_by_room_or_no_heat_share=nheat_share,
        gas_convector_calibrated_share=PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
        proven_nonreuse_lower_share=lower_share,
        proven_nonreuse_lower_dwellings=lower_share * occupied,
        reuse_upper_share=1.0 - lower_share,
        route_status=QUALIFIED,
        evidence_status="DER+ASS_SET_BOUND",
    )
