"""B02-P70 KSH NHEAT distribution-nonreuse authority.

P70 turns an already-canonical source-native KSH topology control into a
programme-path lower bound for the central hydronic air-to-water route.

Authority chain:

B02-P13 exact WBL011 FUTES_TOH=NHEAT national control = 1,173,639 dwellings
B02-P22 NHEAT semantics = ROOM_BY_ROOM_OR_NO_HEAT
P69 programme path = REUSE_EXISTING_DISTRIBUTION vs
                     NEW_OR_REPLACE_DISTRIBUTION_REQUIRED

For a CENTRAL_HYDRONIC_AIR_TO_WATER programme route, a source-native
room-by-room/no-heat dwelling does not have a proven reusable central
distribution. Therefore the complete NHEAT branch belongs to the top-level
NEW_OR_REPLACE_DISTRIBUTION_REQUIRED set.

This does NOT identify whether the required path is NEW versus REPLACE, and it
does not identify room-grain emitter actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from modules.B02.heating_system_assignment import build_heating_system_assignment


PROGRAMME_ROUTE = "CENTRAL_HYDRONIC_AIR_TO_WATER"
NHEAT_CLASS = "ROOM_BY_ROOM_OR_NO_HEAT"
CENTRAL_CLASS = "CENTRAL_HEATING"
DISTRICT_CLASS = "DISTRICT_HEATING"

EXPECTED_OCCUPIED_DWELLINGS = 4_008_541
EXPECTED_NHEAT_DWELLINGS = 1_173_639
EXPECTED_CENTRAL_DWELLINGS = 2_216_178
EXPECTED_DISTRICT_DWELLINGS = 618_724

NHEAT_NONREUSE_SHARE = EXPECTED_NHEAT_DWELLINGS / EXPECTED_OCCUPIED_DWELLINGS


@dataclass(frozen=True)
class NheatNonreuseAuthority:
    occupied_dwellings: int
    nheat_dwellings: int
    nheat_share: float
    central_dwellings: int
    district_dwellings: int
    programme_route: str
    evidence_status: str
    authority_status: str


@dataclass(frozen=True)
class DistributionAssignmentDecision:
    status: str
    distribution_path: str | None
    blockers: tuple[str, ...]


def classify_heating_topology_for_programme(
    heating_system_class: str,
    *,
    programme_route: str = PROGRAMME_ROUTE,
) -> DistributionAssignmentDecision:
    """Classify only what KSH topology proves for the specified programme route."""

    if programme_route != PROGRAMME_ROUTE:
        return DistributionAssignmentDecision(
            status="Q",
            distribution_path=None,
            blockers=("PROGRAMME_ROUTE_NOT_P70_AUTHORIZED",),
        )

    if heating_system_class == NHEAT_CLASS:
        return DistributionAssignmentDecision(
            status="QUALIFIED",
            distribution_path="NEW_OR_REPLACE_DISTRIBUTION_REQUIRED",
            blockers=(),
        )

    if heating_system_class in {CENTRAL_CLASS, DISTRICT_CLASS}:
        return DistributionAssignmentDecision(
            status="Q",
            distribution_path=None,
            blockers=("CURRENT_DISTRIBUTION_REUSE_NOT_IDENTIFIED",),
        )

    return DistributionAssignmentDecision(
        status="Q",
        distribution_path=None,
        blockers=("HEATING_SYSTEM_CLASS_UNKNOWN",),
    )


@lru_cache(maxsize=1)
def build_nheat_nonreuse_authority() -> NheatNonreuseAuthority:
    """Reproduce the exact P22 topology totals and freeze the P70 lower bound."""

    _rows, summary = build_heating_system_assignment()

    if summary.occupied_dwellings != EXPECTED_OCCUPIED_DWELLINGS:
        raise ValueError("occupied-dwelling control drift")
    if summary.room_by_room_or_no_heat_dwellings != EXPECTED_NHEAT_DWELLINGS:
        raise ValueError("NHEAT national control drift")
    if summary.central_heating_dwellings != EXPECTED_CENTRAL_DWELLINGS:
        raise ValueError("central-heating national control drift")
    if summary.district_heating_dwellings != EXPECTED_DISTRICT_DWELLINGS:
        raise ValueError("district-heating national control drift")
    if (
        summary.central_heating_dwellings
        + summary.district_heating_dwellings
        + summary.room_by_room_or_no_heat_dwellings
        != summary.occupied_dwellings
    ):
        raise ValueError("P22 topology partition does not reconcile")

    return NheatNonreuseAuthority(
        occupied_dwellings=summary.occupied_dwellings,
        nheat_dwellings=summary.room_by_room_or_no_heat_dwellings,
        nheat_share=summary.room_by_room_or_no_heat_dwellings
        / summary.occupied_dwellings,
        central_dwellings=summary.central_heating_dwellings,
        district_dwellings=summary.district_heating_dwellings,
        programme_route=PROGRAMME_ROUTE,
        evidence_status="DER",
        authority_status="QUALIFIED_LOWER_BOUND",
    )
