"""B02-P72 transition denominator alignment to the canonical physical scope.

B01-P3 and the B02 eligibility-layer contract define the physical screening
population as occupied, non-district-heated dwellings.

P22 partitions the full occupied universe into:
- CENTRAL_HEATING: 2,216,178
- DISTRICT_HEATING: 618,724
- ROOM_BY_ROOM_OR_NO_HEAT: 1,173,639

Therefore the B02 central-hydronic transition-set denominator is not the full
4,008,541 occupied universe. It is the exact non-district physical screening
scope:

2,216,178 + 1,173,639 = 3,389,817.

This is a technical-screening denominator only. It is not a final programme
participant count or a legal/economic eligibility claim.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B01.non_district_population import (
    EXPECTED_DISTRICT_HEATED_DWELLINGS,
    EXPECTED_NON_DISTRICT_HEATED_DWELLINGS,
    EXPECTED_OCCUPIED_DWELLINGS,
)
from modules.B02.distribution_nonreuse_assignment import (
    CENTRAL_CLASS,
    DISTRICT_CLASS,
    EXPECTED_CENTRAL_DWELLINGS,
    EXPECTED_NHEAT_DWELLINGS,
    NHEAT_CLASS,
    PROGRAMME_ROUTE,
)


EXPECTED_PHYSICAL_SCOPE_DWELLINGS = EXPECTED_NON_DISTRICT_HEATED_DWELLINGS
NHEAT_PROGRAMME_SCOPE_SHARE = (
    EXPECTED_NHEAT_DWELLINGS / EXPECTED_PHYSICAL_SCOPE_DWELLINGS
)
CENTRAL_PROGRAMME_SCOPE_SHARE = (
    EXPECTED_CENTRAL_DWELLINGS / EXPECTED_PHYSICAL_SCOPE_DWELLINGS
)


@dataclass(frozen=True)
class ProgrammeScopeAlignment:
    occupied_universe_dwellings: int
    district_out_of_physical_scope_dwellings: int
    physical_scope_dwellings: int
    nheat_dwellings: int
    central_heating_dwellings: int
    nheat_scope_share: float
    central_scope_share: float
    evidence_status: str
    programme_route: str


@dataclass(frozen=True)
class ProgrammeScopeDecision:
    status: str
    in_physical_scope: bool | None
    distribution_path: str | None
    blockers: tuple[str, ...]


def build_programme_scope_alignment() -> ProgrammeScopeAlignment:
    if (
        EXPECTED_DISTRICT_HEATED_DWELLINGS
        + EXPECTED_NON_DISTRICT_HEATED_DWELLINGS
        != EXPECTED_OCCUPIED_DWELLINGS
    ):
        raise ValueError("B01 physical-scope partition drift")
    if (
        EXPECTED_CENTRAL_DWELLINGS + EXPECTED_NHEAT_DWELLINGS
        != EXPECTED_NON_DISTRICT_HEATED_DWELLINGS
    ):
        raise ValueError("P22 non-district topology partition drift")

    return ProgrammeScopeAlignment(
        occupied_universe_dwellings=EXPECTED_OCCUPIED_DWELLINGS,
        district_out_of_physical_scope_dwellings=EXPECTED_DISTRICT_HEATED_DWELLINGS,
        physical_scope_dwellings=EXPECTED_NON_DISTRICT_HEATED_DWELLINGS,
        nheat_dwellings=EXPECTED_NHEAT_DWELLINGS,
        central_heating_dwellings=EXPECTED_CENTRAL_DWELLINGS,
        nheat_scope_share=NHEAT_PROGRAMME_SCOPE_SHARE,
        central_scope_share=CENTRAL_PROGRAMME_SCOPE_SHARE,
        evidence_status="DER",
        programme_route=PROGRAMME_ROUTE,
    )


def classify_topology_in_physical_scope(
    heating_system_class: str,
    *,
    programme_route: str = PROGRAMME_ROUTE,
) -> ProgrammeScopeDecision:
    if programme_route != PROGRAMME_ROUTE:
        return ProgrammeScopeDecision(
            status="Q",
            in_physical_scope=None,
            distribution_path=None,
            blockers=("PROGRAMME_ROUTE_NOT_P72_AUTHORIZED",),
        )

    if heating_system_class == DISTRICT_CLASS:
        return ProgrammeScopeDecision(
            status="OUT_OF_PHYSICAL_SCREENING_SCOPE",
            in_physical_scope=False,
            distribution_path=None,
            blockers=(),
        )

    if heating_system_class == NHEAT_CLASS:
        return ProgrammeScopeDecision(
            status="IN_SCOPE_QUALIFIED_NONREUSE",
            in_physical_scope=True,
            distribution_path="NEW_OR_REPLACE_DISTRIBUTION_REQUIRED",
            blockers=(),
        )

    if heating_system_class == CENTRAL_CLASS:
        return ProgrammeScopeDecision(
            status="IN_SCOPE_Q_REUSE_ADEQUACY",
            in_physical_scope=True,
            distribution_path=None,
            blockers=("CENTRAL_HEATING_REUSE_VS_NONREUSE_ASSIGNMENT",),
        )

    return ProgrammeScopeDecision(
        status="Q",
        in_physical_scope=None,
        distribution_path=None,
        blockers=("HEATING_SYSTEM_CLASS_UNKNOWN",),
    )
