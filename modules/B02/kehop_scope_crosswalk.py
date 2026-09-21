"""B02-P75 KEHOP structural-scope crosswalk on the canonical P21/WBL grain.

The current MFB family-house programmes (KEHOP Plusz-4.1.7-24 outside
Budapest and 4.1.8-24 in Budapest) cover occupied family houses built before
2007, subject to additional programme/legal conditions.

The canonical P21/WBL construction-period axis does not isolate 2007:
Y2001-2010 straddles the cutoff. P75 therefore carries an age-censoring
envelope instead of inventing a within-band year distribution.

This module joins:
- P21 calibrated FAMILY_HOUSE probabilities by exact cell_id;
- P22 heating topology by exact cell_id;
- the P72 non-district physical-screening scope;
- the P73 latent central reuse/nonreuse model.

Critical boundaries:

STRUCTURAL-SCOPE COMPATIBILITY != LEGAL PROGRAMME ELIGIBILITY
Y2001-2010 != PROVEN PRE-2007
NHEAT -> PROVEN NONREUSE ON THE CANONICAL ROUTE
CENTRAL_HEATING -> LATENT REUSE/NONREUSE
KEHOP STRUCTURAL CANDIDATE != NATIONAL NONREUSE POINT SHARE
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage
from modules.B02.heating_system_assignment import build_heating_system_assignment
from modules.B02.programme_scope_transition import (
    EXPECTED_PHYSICAL_SCOPE_DWELLINGS,
)


DEFINITE_PRE_2007_PERIODS = frozenset(
    {
        "Y_LT1919",
        "Y1919-1945",
        "Y1946-1960",
        "Y1961-1980",
        "Y1981-2000",
    }
)
CUTOFF_STRADDLING_PERIOD = "Y2001-2010"
POST_CUTOFF_PERIOD = "Y_GE2011"

NON_DISTRICT_CLASSES = frozenset(
    {
        "CENTRAL_HEATING",
        "ROOM_BY_ROOM_OR_NO_HEAT",
    }
)
NHEAT_CLASS = "ROOM_BY_ROOM_OR_NO_HEAT"
CENTRAL_CLASS = "CENTRAL_HEATING"


@dataclass(frozen=True)
class ScenarioCrosswalk:
    scenario: str
    physical_family_definite_pre2007: float
    physical_family_possible_pre2007: float
    nheat_family_definite_pre2007: float
    nheat_family_possible_pre2007: float
    central_family_definite_pre2007: float
    central_family_possible_pre2007: float


@dataclass(frozen=True)
class KehopScopeCrosswalk:
    physical_scope_dwellings: int
    central: ScenarioCrosswalk
    flat: ScenarioCrosswalk
    structural_candidate_lower: float
    structural_candidate_upper: float
    proven_nonreuse_overlap_lower: float
    possible_nonreuse_overlap_upper: float
    evidence_status: str
    age_cutoff_status: str
    legal_eligibility_status: str


def _family_probability(row: dict[str, object], scenario: str) -> float:
    if scenario == "CENTRAL":
        return float(row["central_family_probability"])
    if scenario == "FLAT":
        return float(row["flat_family_probability"])
    raise ValueError(f"unsupported P21 scenario: {scenario}")


def _scenario_crosswalk(
    linkage_by_cell: dict[str, dict[str, object]],
    heating_by_cell: dict[str, dict[str, object]],
    *,
    scenario: str,
) -> ScenarioCrosswalk:
    physical_definite = 0.0
    physical_possible = 0.0
    nheat_definite = 0.0
    nheat_possible = 0.0
    central_definite = 0.0
    central_possible = 0.0

    if set(linkage_by_cell) != set(heating_by_cell):
        raise ValueError("P21/P22 cell_id universe mismatch")

    for cell_id, row in linkage_by_cell.items():
        heat = heating_by_cell[cell_id]
        if int(row["dwelling_count"]) != int(heat["dwelling_count"]):
            raise ValueError(f"dwelling-count mismatch for cell_id={cell_id}")

        system = str(heat["heating_system_class"])
        if system not in NON_DISTRICT_CLASSES:
            continue

        period = str(row["construction_period_code"])
        if period == POST_CUTOFF_PERIOD:
            continue

        expected_family = int(row["dwelling_count"]) * _family_probability(row, scenario)

        is_definite = period in DEFINITE_PRE_2007_PERIODS
        is_possible = is_definite or period == CUTOFF_STRADDLING_PERIOD
        if not is_possible:
            raise ValueError(f"unexpected construction period: {period}")

        if is_definite:
            physical_definite += expected_family
            if system == NHEAT_CLASS:
                nheat_definite += expected_family
            elif system == CENTRAL_CLASS:
                central_definite += expected_family

        physical_possible += expected_family
        if system == NHEAT_CLASS:
            nheat_possible += expected_family
        elif system == CENTRAL_CLASS:
            central_possible += expected_family

    return ScenarioCrosswalk(
        scenario=scenario,
        physical_family_definite_pre2007=physical_definite,
        physical_family_possible_pre2007=physical_possible,
        nheat_family_definite_pre2007=nheat_definite,
        nheat_family_possible_pre2007=nheat_possible,
        central_family_definite_pre2007=central_definite,
        central_family_possible_pre2007=central_possible,
    )


@lru_cache(maxsize=1)
def build_kehop_scope_crosswalk() -> KehopScopeCrosswalk:
    linkage_rows, _summary = build_calibrated_linkage()
    heating_rows, heating_summary = build_heating_system_assignment()

    linkage_by_cell = {str(row["cell_id"]): row for row in linkage_rows}
    heating_by_cell = {str(row["cell_id"]): row for row in heating_rows}

    physical = (
        heating_summary.central_heating_dwellings
        + heating_summary.room_by_room_or_no_heat_dwellings
    )
    if physical != EXPECTED_PHYSICAL_SCOPE_DWELLINGS:
        raise ValueError(
            "P22 non-district topology does not reconcile to P72 physical scope"
        )

    central = _scenario_crosswalk(
        linkage_by_cell,
        heating_by_cell,
        scenario="CENTRAL",
    )
    flat = _scenario_crosswalk(
        linkage_by_cell,
        heating_by_cell,
        scenario="FLAT",
    )

    # The lower structural candidate count uses only construction bands wholly
    # before 2007. The upper admits the entire straddling Y2001-2010 band as a
    # possibility. Neither output promotes legal/application eligibility.
    structural_lower = min(
        central.physical_family_definite_pre2007,
        flat.physical_family_definite_pre2007,
    )
    structural_upper = max(
        central.physical_family_possible_pre2007,
        flat.physical_family_possible_pre2007,
    )

    # NHEAT is already qualified nonreuse on the canonical route, so definite
    # pre-2007 FAMILY_HOUSE x NHEAT gives the only guaranteed structural
    # overlap under current evidence. The upper allows the cutoff-straddling
    # age band and all CENTRAL_HEATING candidates to fall on nonreuse.
    nonreuse_lower = min(
        central.nheat_family_definite_pre2007,
        flat.nheat_family_definite_pre2007,
    )
    nonreuse_upper = structural_upper

    if not (0.0 <= nonreuse_lower <= nonreuse_upper <= physical):
        raise ValueError("KEHOP/nonreuse overlap bounds outside physical scope")
    if not (0.0 <= structural_lower <= structural_upper <= physical):
        raise ValueError("KEHOP structural scope bounds outside physical scope")

    return KehopScopeCrosswalk(
        physical_scope_dwellings=physical,
        central=central,
        flat=flat,
        structural_candidate_lower=structural_lower,
        structural_candidate_upper=structural_upper,
        proven_nonreuse_overlap_lower=nonreuse_lower,
        possible_nonreuse_overlap_upper=nonreuse_upper,
        evidence_status="ASS",
        age_cutoff_status="SET_BOUNDED_BY_WBL_CONSTRUCTION_PERIOD",
        legal_eligibility_status="Q_ADDITIONAL_PROGRAMME_CONDITIONS",
    )


def as_log_dict() -> dict[str, object]:
    x = build_kehop_scope_crosswalk()
    return {
        "physical_scope_dwellings": x.physical_scope_dwellings,
        "central": x.central.__dict__,
        "flat": x.flat.__dict__,
        "structural_candidate_lower": x.structural_candidate_lower,
        "structural_candidate_upper": x.structural_candidate_upper,
        "proven_nonreuse_overlap_lower": x.proven_nonreuse_overlap_lower,
        "possible_nonreuse_overlap_upper": x.possible_nonreuse_overlap_upper,
        "evidence_status": x.evidence_status,
        "age_cutoff_status": x.age_cutoff_status,
        "legal_eligibility_status": x.legal_eligibility_status,
    }
