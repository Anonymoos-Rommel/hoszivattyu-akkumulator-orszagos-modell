"""B02-P65 set-identified national emitter population model.

The model combines only already-admitted aggregate evidence:

- exact 2022 KSH WBL heating-topology partition from B02-P22;
- P39 approved calibrated primary gas-convector margin;
- P62/P64 EHI Hungary residential surface-heating presence band.

It deliberately does not fabricate an exclusive radiator/surface/other split.

Unknown radiator presence, radiator+surface overlap, OTHER presence and P21/WBL
allocation remain latent nuisance parameters. They are admissible when they
satisfy hard set-theoretic and aggregate evidence constraints.

Canonical boundaries:

POINT ESTIMATE NOT IDENTIFIED != MODEL BLOCKED
LATENT COMPOSITION != OBSERVATION
SURFACE PRESENCE != SURFACE ONLY
RADIATOR SHARE != 1 - SURFACE SHARE
P21 CELL ALLOCATION != EHI SOURCE OBSERVATION
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from modules.B02.ehi_surface_band_aggregation import (
    ehi_hungary_residential_validation_envelope,
)
from modules.B02.emitter_marginal_reconciliation import (
    PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
)
from modules.B02.heating_system_assignment import build_heating_system_assignment


EVIDENCE_STATUS = "SET_IDENTIFIED"
MODEL_ID = "B02-P65-EMITTER-POPULATION-SET"


@dataclass(frozen=True)
class EmitterPopulationEnvelope:
    model_id: str
    occupied_dwellings: int
    central_heating_dwellings: int
    district_heating_dwellings: int
    room_by_room_or_no_heat_dwellings: int
    surface_presence_lower: float
    surface_presence_upper: float
    primary_gas_convector_share: float
    primary_gas_convector_expected_dwellings: float
    radiator_presence_identified: bool
    mixed_radiator_surface_identified: bool
    other_emitter_presence_identified: bool
    p21_cell_allocation_identified: bool
    evidence_status: str


@dataclass(frozen=True)
class CandidateEmitterComposition:
    """One admissibility candidate in the non-exclusive emitter set.

    All quantities are population shares over the common national occupied
    dwelling universe. Presence variables are deliberately non-exclusive.

    mixed_radiator_surface_share is the overlap R intersection S.
    other_emitter_present_share may overlap any other presence variable.
    """

    surface_present_share: float
    radiator_present_share: float
    mixed_radiator_surface_share: float
    other_emitter_present_share: float
    primary_gas_convector_share: float = PRIMARY_HEATING_GAS_CONVECTOR_SHARE


@dataclass(frozen=True)
class CandidateAssessment:
    admissible: bool
    blockers: tuple[str, ...]
    radiator_surface_union_share: float | None


def _unit_interval(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be within [0,1]")


def build_emitter_population_envelope() -> EmitterPopulationEnvelope:
    """Return the current sharp aggregate evidence envelope."""

    _rows, topology = build_heating_system_assignment()
    ehi = ehi_hungary_residential_validation_envelope()

    if (
        topology.central_heating_dwellings
        + topology.district_heating_dwellings
        + topology.room_by_room_or_no_heat_dwellings
        != topology.occupied_dwellings
    ):
        raise ValueError("P22 topology partition does not reconcile")

    if not (0.0 <= ehi.lower <= ehi.upper <= 1.0):
        raise ValueError("invalid EHI surface-presence envelope")

    return EmitterPopulationEnvelope(
        model_id=MODEL_ID,
        occupied_dwellings=topology.occupied_dwellings,
        central_heating_dwellings=topology.central_heating_dwellings,
        district_heating_dwellings=topology.district_heating_dwellings,
        room_by_room_or_no_heat_dwellings=topology.room_by_room_or_no_heat_dwellings,
        surface_presence_lower=ehi.lower,
        surface_presence_upper=ehi.upper,
        primary_gas_convector_share=PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
        primary_gas_convector_expected_dwellings=(
            topology.occupied_dwellings * PRIMARY_HEATING_GAS_CONVECTOR_SHARE
        ),
        radiator_presence_identified=False,
        mixed_radiator_surface_identified=False,
        other_emitter_presence_identified=False,
        p21_cell_allocation_identified=False,
        evidence_status=EVIDENCE_STATUS,
    )


def assess_candidate(
    candidate: CandidateEmitterComposition,
    *,
    tolerance: float = 1e-12,
) -> CandidateAssessment:
    """Assess a non-exclusive national emitter composition candidate."""

    values = {
        "surface_present_share": candidate.surface_present_share,
        "radiator_present_share": candidate.radiator_present_share,
        "mixed_radiator_surface_share": candidate.mixed_radiator_surface_share,
        "other_emitter_present_share": candidate.other_emitter_present_share,
        "primary_gas_convector_share": candidate.primary_gas_convector_share,
    }
    for name, value in values.items():
        _unit_interval(float(value), name)

    envelope = ehi_hungary_residential_validation_envelope()
    blockers: list[str] = []

    if candidate.surface_present_share < envelope.lower - tolerance:
        blockers.append("SURFACE_PRESENCE_BELOW_EHI_BAND")
    if candidate.surface_present_share > envelope.upper + tolerance:
        blockers.append("SURFACE_PRESENCE_ABOVE_EHI_BAND")

    if not isclose(
        candidate.primary_gas_convector_share,
        PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
        abs_tol=tolerance,
    ):
        blockers.append("PRIMARY_GAS_CONVECTOR_MARGIN_DRIFT")

    r = candidate.radiator_present_share
    s = candidate.surface_present_share
    mixed = candidate.mixed_radiator_surface_share

    frechet_lower = max(0.0, r + s - 1.0)
    frechet_upper = min(r, s)
    if mixed < frechet_lower - tolerance:
        blockers.append("RADIATOR_SURFACE_OVERLAP_BELOW_FRECHET")
    if mixed > frechet_upper + tolerance:
        blockers.append("RADIATOR_SURFACE_OVERLAP_ABOVE_FRECHET")

    union = r + s - mixed
    if union < -tolerance or union > 1.0 + tolerance:
        blockers.append("RADIATOR_SURFACE_UNION_OUTSIDE_UNIT_INTERVAL")

    return CandidateAssessment(
        admissible=not blockers,
        blockers=tuple(blockers),
        radiator_surface_union_share=union,
    )


def global_latent_bounds() -> dict[str, tuple[float, float] | str]:
    """Return only bounds sharp without extra unsupported assumptions."""

    envelope = ehi_hungary_residential_validation_envelope()
    return {
        "surface_present_share": (envelope.lower, envelope.upper),
        "primary_gas_convector_share": (
            PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
            PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
        ),
        "radiator_present_share": (0.0, 1.0),
        "mixed_radiator_surface_share": (0.0, envelope.upper),
        "other_emitter_present_share": (0.0, 1.0),
        "p21_stratum_emitter_allocation": "LATENT_SIMPLEX_WITH_AGGREGATE_CONSTRAINTS",
    }
