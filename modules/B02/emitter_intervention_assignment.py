"""B02-P71 Hungarian gas-convector emitter-intervention lower bound.

P39/P41 already establish a calibrated current primary-heating gas-convector
branch and an admitted non-hydronic replacement-distribution path.

For the canonical CENTRAL_HYDRONIC_AIR_TO_WATER programme route, a current
gas convector cannot serve as the target hydronic heat emitter. Therefore this
branch requires a new hydronic heat-emission system.

This is a dwelling/system requirement, not a radiator-unit count and not a
room-grain KEEP/UPSIZE/CHANGE/ADD distribution.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.archetype_admission_gate import (
    GAS_CONVECTOR,
    NON_HYDRONIC_ROOM_HEATING,
    QUALIFIED,
    REPLACE_EXISTING_DISTRIBUTION,
)
from modules.B02.emitter_marginal_reconciliation import (
    EXPECTED_OCCUPIED,
    PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
)


PROGRAMME_ROUTE = "CENTRAL_HYDRONIC_AIR_TO_WATER"
EXPECTED_OCCUPIED_DWELLINGS = EXPECTED_OCCUPIED
GAS_CONVECTOR_EXPECTED_DWELLING_EQUIVALENTS = (
    EXPECTED_OCCUPIED_DWELLINGS * PRIMARY_HEATING_GAS_CONVECTOR_SHARE
)


@dataclass(frozen=True)
class EmitterInterventionFloor:
    occupied_dwellings: int
    required_share_lower: float
    required_share_upper: float
    required_expected_dwelling_equivalents_lower: float
    required_expected_dwelling_equivalents_upper: float
    evidence_status: str
    authority_status: str
    programme_route: str


@dataclass(frozen=True)
class EmitterRequirementDecision:
    status: str
    new_hydronic_heat_emission_required: bool | None
    blockers: tuple[str, ...]


def assess_gas_convector_emitter_requirement(
    *,
    current_emitter_type: str,
    emitter_category_authority_status: str,
    current_distribution_topology: str,
    transition_path: str,
    programme_route: str = PROGRAMME_ROUTE,
) -> EmitterRequirementDecision:
    """Admit only the proven P39/P41 gas-convector requirement."""

    blockers: list[str] = []
    if programme_route != PROGRAMME_ROUTE:
        blockers.append("PROGRAMME_ROUTE_NOT_P71_AUTHORIZED")
    if current_emitter_type != GAS_CONVECTOR:
        blockers.append("CURRENT_EMITTER_NOT_GAS_CONVECTOR")
    if emitter_category_authority_status != QUALIFIED:
        blockers.append("GAS_CONVECTOR_CATEGORY_NOT_QUALIFIED")
    if current_distribution_topology != NON_HYDRONIC_ROOM_HEATING:
        blockers.append("CURRENT_DISTRIBUTION_NOT_NON_HYDRONIC_ROOM_HEATING")
    if transition_path != REPLACE_EXISTING_DISTRIBUTION:
        blockers.append("GAS_CONVECTOR_REPLACEMENT_PATH_NOT_SELECTED")

    if blockers:
        return EmitterRequirementDecision("Q", None, tuple(blockers))

    return EmitterRequirementDecision(
        status="QUALIFIED_NEW_HYDRONIC_HEAT_EMISSION_REQUIRED",
        new_hydronic_heat_emission_required=True,
        blockers=(),
    )


def build_gas_convector_emitter_intervention_floor() -> EmitterInterventionFloor:
    """Freeze the calibrated national lower bound without OBS promotion."""

    if EXPECTED_OCCUPIED_DWELLINGS != 4_008_541:
        raise ValueError("occupied-dwelling control drift")
    if PRIMARY_HEATING_GAS_CONVECTOR_SHARE != 0.233:
        raise ValueError("gas-convector calibrated margin drift")

    return EmitterInterventionFloor(
        occupied_dwellings=EXPECTED_OCCUPIED_DWELLINGS,
        required_share_lower=PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
        required_share_upper=1.0,
        required_expected_dwelling_equivalents_lower=GAS_CONVECTOR_EXPECTED_DWELLING_EQUIVALENTS,
        required_expected_dwelling_equivalents_upper=float(EXPECTED_OCCUPIED_DWELLINGS),
        evidence_status="ASS",
        authority_status="QUALIFIED_LOWER_BOUND",
        programme_route=PROGRAMME_ROUTE,
    )
