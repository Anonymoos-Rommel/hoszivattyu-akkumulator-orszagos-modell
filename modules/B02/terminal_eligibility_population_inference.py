"""B02-P84 terminal technical-eligibility population inference.

P84 does not invent household PASS/FAIL records.

It turns Q-B02-001 into an executable population-inference problem over the
already-canonical record/project transition gates:

- THERMAL_DISTRIBUTION
- HYDRAULIC
- ELECTRICAL

Core boundaries:

PHYSICAL SCREENING SCOPE != TECHNICAL ELIGIBILITY
CURRENT READINESS != TERMINAL TRANSITION OUTCOME
POPULATION ESTIMATE != RECORD PASS/FAIL
MISSING TERMINAL OUTCOME EVIDENCE != PASS
NO FULL-POPULATION MICRODATA != BLOCKER
NO DEFENSIBLE TERMINAL-OUTCOME INFERENCE == BLOCKER

The current repository has exact population controls but no representative or
calibrated Hungarian terminal transition-outcome sample. Therefore the present
admissible national eligibility interval is the logically valid but
uninformative [0, physical screening scope] interval.

The module also provides the exact post-stratification surface and an executable
admission path for future stratum-specific eligibility bounds.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from modules.B02.calibrated_archetype_linkage import (
    DEFAULT_WBL,
    FULL_PROJECTION,
    EXPECTED_OCCUPIED_DWELLINGS,
    EXPECTED_WBL_ROWS,
)
from modules.B02.heating_system_assignment import HEATING_SYSTEM_CLASS


ROOT = Path(__file__).resolve().parents[2]

PHYSICAL_SCOPE_DWELLINGS = 3_389_817
DISTRICT_HEATING_DWELLINGS = 618_724
CENTRAL_HEATING_DWELLINGS = 2_216_178
NHEAT_DWELLINGS = 1_173_639

IN_SCOPE_TOPOLOGIES = frozenset(
    {
        "CENTRAL_HEATING",
        "ROOM_BY_ROOM_OR_NO_HEAT",
    }
)

Q = "Q"
QUALIFIED_BOUNDED_POPULATION_INFERENCE = (
    "QUALIFIED_BOUNDED_TERMINAL_TECHNICAL_ELIGIBILITY_INFERENCE"
)


@dataclass(frozen=True)
class PopulationControlStratum:
    county_code: str
    heating_system_class: str
    dwelling_count: int
    evidence_status: str = "DER"

    @property
    def stratum_id(self) -> str:
        return f"{self.county_code}::{self.heating_system_class}"


@dataclass(frozen=True)
class StratumEligibilityBound:
    stratum_id: str
    eligible_lower_share: float
    eligible_upper_share: float
    evidence_status: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class NationalEligibilityInference:
    status: str
    eligible_lower_dwellings: float
    eligible_upper_dwellings: float
    physical_scope_dwellings: int
    covered_population_dwellings: int
    uncovered_strata: tuple[str, ...]
    residuals: tuple[str, ...]
    warnings: tuple[str, ...]


def _read_wbl(path: Path = DEFAULT_WBL) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["projection_id"] == FULL_PROJECTION
        ]
    if len(rows) != EXPECTED_WBL_ROWS:
        raise ValueError(
            f"WBL row-count drift: expected={EXPECTED_WBL_ROWS} actual={len(rows)}"
        )
    if any(row["evidence_status"] != "OBS" for row in rows):
        raise ValueError("WBL full-joint population controls must remain OBS")
    if sum(int(row["dwelling_count"]) for row in rows) != EXPECTED_OCCUPIED_DWELLINGS:
        raise ValueError("WBL occupied-universe total drift")
    return rows


def build_population_controls(
    *,
    wbl_path: Path = DEFAULT_WBL,
) -> tuple[PopulationControlStratum, ...]:
    """Build exact county x source-native heating-topology calibration controls."""

    totals: dict[tuple[str, str], int] = {}
    district_total = 0

    for row in _read_wbl(wbl_path):
        heating_code = row["heating_mode_code"]
        if heating_code not in HEATING_SYSTEM_CLASS:
            raise ValueError(f"unexpected heating-mode code: {heating_code!r}")

        system_class = HEATING_SYSTEM_CLASS[heating_code]
        count = int(row["dwelling_count"])
        if count <= 0:
            raise ValueError("population-control dwelling count must be positive")

        if system_class == "DISTRICT_HEATING":
            district_total += count
            continue

        if system_class not in IN_SCOPE_TOPOLOGIES:
            raise ValueError(f"unexpected in-scope topology: {system_class!r}")

        county = row["county_code"].strip()
        if not county:
            raise ValueError("county_code is required")
        totals[(county, system_class)] = totals.get((county, system_class), 0) + count

    controls = tuple(
        PopulationControlStratum(
            county_code=county,
            heating_system_class=system_class,
            dwelling_count=count,
        )
        for (county, system_class), count in sorted(totals.items())
    )

    counties = {row.county_code for row in controls}
    if len(counties) != 20:
        raise ValueError(f"expected 20 county/capital codes, got {len(counties)}")

    if any(
        {row.heating_system_class for row in controls if row.county_code == county}
        != IN_SCOPE_TOPOLOGIES
        for county in counties
    ):
        raise ValueError("every county/capital must expose both in-scope topology strata")

    if len(controls) != 40:
        raise ValueError(f"expected 40 county x topology strata, got {len(controls)}")

    total = sum(row.dwelling_count for row in controls)
    central = sum(
        row.dwelling_count
        for row in controls
        if row.heating_system_class == "CENTRAL_HEATING"
    )
    nheat = sum(
        row.dwelling_count
        for row in controls
        if row.heating_system_class == "ROOM_BY_ROOM_OR_NO_HEAT"
    )

    if total != PHYSICAL_SCOPE_DWELLINGS:
        raise ValueError("non-district physical-scope population drift")
    if central != CENTRAL_HEATING_DWELLINGS:
        raise ValueError("central-heating population drift")
    if nheat != NHEAT_DWELLINGS:
        raise ValueError("NHEAT population drift")
    if district_total != DISTRICT_HEATING_DWELLINGS:
        raise ValueError("district-heating exclusion total drift")

    return controls


def current_repository_envelope() -> NationalEligibilityInference:
    """Expose only the eligibility interval justified by current evidence."""

    controls = build_population_controls()
    return NationalEligibilityInference(
        status=Q,
        eligible_lower_dwellings=0.0,
        eligible_upper_dwellings=float(PHYSICAL_SCOPE_DWELLINGS),
        physical_scope_dwellings=PHYSICAL_SCOPE_DWELLINGS,
        covered_population_dwellings=0,
        uncovered_strata=tuple(row.stratum_id for row in controls),
        residuals=(
            "REPRESENTATIVE_OR_CALIBRATED_TERMINAL_TRANSITION_OUTCOME_EVIDENCE_REQUIRED",
            "THERMAL_DISTRIBUTION_TERMINAL_OUTCOME_POPULATION_BOUND_REQUIRED",
            "HYDRAULIC_TERMINAL_OUTCOME_POPULATION_BOUND_REQUIRED",
            "ELECTRICAL_TERMINAL_OUTCOME_POPULATION_BOUND_REQUIRED",
            "JOINT_OR_CONTROLLED_DEPENDENCE_MODEL_REQUIRED",
            "POPULATION_UNCERTAINTY_PROPAGATION_REQUIRED",
        ),
        warnings=(
            "CURRENT_HEAT_PUMP_PRESENCE_IS_NOT_TECHNICAL_ELIGIBILITY",
            "CURRENT_EMITTER_OR_HYDRAULIC_READINESS_IS_NOT_TERMINAL_TRANSITION_OUTCOME",
            "PHYSICAL_SCOPE_UPPER_BOUND_IS_NOT_AN_ELIGIBLE_COUNT",
        ),
    )


def poststratify_terminal_eligibility(
    bounds: Iterable[StratumEligibilityBound],
) -> NationalEligibilityInference:
    """Post-stratify complete county x topology eligibility-share intervals.

    The input bounds must already come from an admitted representative sample or
    calibrated model. P84 only performs the population weighting and refuses to
    impute missing strata.
    """

    controls = build_population_controls()
    control_by_id = {row.stratum_id: row for row in controls}

    by_id: dict[str, StratumEligibilityBound] = {}
    for bound in bounds:
        if bound.stratum_id in by_id:
            raise ValueError(f"duplicate eligibility stratum: {bound.stratum_id}")
        if bound.stratum_id not in control_by_id:
            raise ValueError(f"unknown eligibility stratum: {bound.stratum_id}")
        if bound.evidence_status not in {"DER", "MODELLED"}:
            raise ValueError("population eligibility bounds must remain DER or MODELLED")
        if not bound.source_refs or any(not ref.strip() for ref in bound.source_refs):
            raise ValueError("population eligibility bounds require source references")
        lo = bound.eligible_lower_share
        hi = bound.eligible_upper_share
        if not (0.0 <= lo <= hi <= 1.0):
            raise ValueError("eligibility share bounds must satisfy 0 <= lower <= upper <= 1")
        by_id[bound.stratum_id] = bound

    missing = tuple(sorted(set(control_by_id) - set(by_id)))
    if missing:
        covered = sum(
            control_by_id[stratum_id].dwelling_count
            for stratum_id in by_id
        )
        return NationalEligibilityInference(
            status=Q,
            eligible_lower_dwellings=0.0,
            eligible_upper_dwellings=float(PHYSICAL_SCOPE_DWELLINGS),
            physical_scope_dwellings=PHYSICAL_SCOPE_DWELLINGS,
            covered_population_dwellings=covered,
            uncovered_strata=missing,
            residuals=("COMPLETE_CALIBRATION_STRATUM_COVERAGE_REQUIRED",),
            warnings=("NO_MISSING_STRATUM_IMPUTATION",),
        )

    lower = 0.0
    upper = 0.0
    for stratum_id, control in control_by_id.items():
        bound = by_id[stratum_id]
        lower += control.dwelling_count * bound.eligible_lower_share
        upper += control.dwelling_count * bound.eligible_upper_share

    return NationalEligibilityInference(
        status=QUALIFIED_BOUNDED_POPULATION_INFERENCE,
        eligible_lower_dwellings=lower,
        eligible_upper_dwellings=upper,
        physical_scope_dwellings=PHYSICAL_SCOPE_DWELLINGS,
        covered_population_dwellings=PHYSICAL_SCOPE_DWELLINGS,
        uncovered_strata=(),
        residuals=(),
        warnings=(
            "POPULATION_ESTIMATE_CANNOT_AUTHORIZE_A_SPECIFIC_DWELLING",
            "LEGAL_ECONOMIC_AND_FINAL_PROGRAMME_ELIGIBILITY_REMAIN_SEPARATE",
        ),
    )


def inference_boundary() -> tuple[str, ...]:
    return (
        "PHYSICAL_SCREENING_SCOPE_IS_ONLY_AN_UPPER_CANDIDATE_UNIVERSE",
        "POPULATION_ESTIMATE_CANNOT_AUTHORIZE_A_SPECIFIC_DWELLING",
        "MISSING_RECORD_EVIDENCE_REMAINS_Q",
        "EXPLICIT_RECORD_FAIL_REQUIRES_OBS_OR_DER_EVIDENCE",
        "Q_B02_004_IS_NOT_A_Q_B02_001_PRECONDITION",
        "LEGAL_ECONOMIC_AND_FINAL_PROGRAMME_ELIGIBILITY_REMAIN_SEPARATE",
    )
