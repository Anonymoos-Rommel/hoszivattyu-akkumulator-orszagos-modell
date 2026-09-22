"""B02-P81 explicit programme envelope-action assignment contract.

This slice does not infer a national retrofit action share from building age,
eligibility, U-values, or the current KEHOP programme.  It contracts the exact
input that P80 requires before action-conditioned post-state U-values may be
aggregated nationally.

Critical boundaries:

ELIGIBLE MEASURE MENU != NATIONAL ACTION ASSIGNMENT
AGE / ELIGIBILITY SCOPE != ACTION FREQUENCY
30% PRIMARY-ENERGY SAVING REQUIREMENT != ENVELOPE-RETROFIT SHARE
PROGRAMME SCENARIO ASSIGNMENT != OBSERVED CURRENT STOCK
INCOMPLETE ASSIGNMENT != HIDDEN DEFAULT
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose


AIR_TO_WATER_HP_ONLY = "AIR_TO_WATER_HP_ONLY"
REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP = "REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP"

ALLOWED_ACTIONS = (
    AIR_TO_WATER_HP_ONLY,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
)

SCN_EXPLICIT_PROGRAMME_ASSIGNMENT = "SCN_EXPLICIT_PROGRAMME_ASSIGNMENT"
POL_EXPLICIT_PROGRAMME_RULE = "POL_EXPLICIT_PROGRAMME_RULE"

ALLOWED_ASSIGNMENT_CLASSES = (
    SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
    POL_EXPLICIT_PROGRAMME_RULE,
)

KEHOP_SCOPE_SOURCE = "SRC-B02-HU-KEHOP-417-418-SCOPE-2026"
KEHOP_MIN_PRIMARY_ENERGY_SAVING_SHARE = 0.30


@dataclass(frozen=True)
class ProgrammeActionAssignment:
    population_key: str
    assigned_dwelling_equivalents: float
    action: str
    assignment_class: str
    authority: str


@dataclass(frozen=True)
class AssignmentAssessment:
    status: str
    declared_programme_population: float
    assigned_population: float
    coverage_share: float
    hp_only_population: float
    envelope_plus_awhp_population: float
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ScopeLimitedPolicyCalibration:
    source_id: str
    status: str
    construction_cutoff: str
    building_scope: str
    minimum_primary_energy_saving_share: float
    eligible_measure_families: tuple[str, ...]
    forbidden_uses: tuple[str, ...]


def current_kehop_policy_calibration() -> ScopeLimitedPolicyCalibration:
    """Return only the source-supported current KEHOP policy constraints.

    The existing registered MFB source covers occupied family houses built and
    permitted before 2007.  The current programme page also states a minimum
    30% primary-energy saving requirement and lists envelope measures and
    air-to-water heat pumps among eligible intervention families.

    These facts are calibration/scope constraints only.  They do not identify
    the action mix of the proposed national programme.
    """

    return ScopeLimitedPolicyCalibration(
        source_id=KEHOP_SCOPE_SOURCE,
        status="QUALIFIED_SCOPE_LIMITED_POLICY_CALIBRATION",
        construction_cutoff="BUILT_AND_PERMITTED_BEFORE_2007",
        building_scope="OCCUPIED_ONE_OR_MULTI_DWELLING_FAMILY_HOUSE",
        minimum_primary_energy_saving_share=KEHOP_MIN_PRIMARY_ENERGY_SAVING_SHARE,
        eligible_measure_families=(
            "ENVELOPE_INSULATION",
            "ROOF_OR_CEILING_INSULATION",
            "WINDOW_REPLACEMENT_OR_UPGRADE",
            "AIR_TO_WATER_HEAT_PUMP",
        ),
        forbidden_uses=(
            "NATIONAL_ENVELOPE_ACTION_SHARE",
            "TWO_MILLION_PROGRAMME_ACTION_ASSIGNMENT",
            "CURRENT_STOCK_OBSERVATION",
        ),
    )


def assess_national_envelope_action_assignment(
    assignments: tuple[ProgrammeActionAssignment, ...],
    *,
    declared_programme_population: float,
) -> AssignmentAssessment:
    """Fail closed unless an explicit assignment covers the declared programme.

    The contract is intentionally agnostic about how policy selects households.
    It requires the selection result to be explicit and provenance-bearing
    rather than silently inferring it from age, building type, or eligibility.
    """

    blockers: list[str] = []

    if declared_programme_population <= 0:
        blockers.append("DECLARED_PROGRAMME_POPULATION_REQUIRED")

    seen_keys: set[str] = set()
    hp_only = 0.0
    envelope_plus_awhp = 0.0
    assigned = 0.0

    for row in assignments:
        if not row.population_key:
            blockers.append("POPULATION_KEY_REQUIRED")
        elif row.population_key in seen_keys:
            blockers.append("DUPLICATE_POPULATION_KEY")
        else:
            seen_keys.add(row.population_key)

        if row.assigned_dwelling_equivalents < 0:
            blockers.append("NEGATIVE_ASSIGNED_POPULATION_FORBIDDEN")
            continue

        if row.action not in ALLOWED_ACTIONS:
            blockers.append("UNSUPPORTED_ENVELOPE_ACTION")
        if row.assignment_class not in ALLOWED_ASSIGNMENT_CLASSES:
            blockers.append("EXPLICIT_POLICY_OR_SCENARIO_ASSIGNMENT_CLASS_REQUIRED")
        if not row.authority:
            blockers.append("ASSIGNMENT_AUTHORITY_REQUIRED")

        assigned += row.assigned_dwelling_equivalents
        if row.action == AIR_TO_WATER_HP_ONLY:
            hp_only += row.assigned_dwelling_equivalents
        elif row.action == REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP:
            envelope_plus_awhp += row.assigned_dwelling_equivalents

    if not assignments:
        blockers.append("EXPLICIT_PROGRAMME_ACTION_ASSIGNMENT_REQUIRED")

    coverage = (
        assigned / declared_programme_population
        if declared_programme_population > 0
        else 0.0
    )

    if declared_programme_population > 0 and not isclose(
        assigned,
        declared_programme_population,
        rel_tol=0.0,
        abs_tol=1e-6,
    ):
        blockers.append("PROGRAMME_ACTION_ASSIGNMENT_MUST_CLOSE_TO_DECLARED_POPULATION")

    if blockers:
        return AssignmentAssessment(
            status="Q",
            declared_programme_population=declared_programme_population,
            assigned_population=assigned,
            coverage_share=coverage,
            hp_only_population=hp_only,
            envelope_plus_awhp_population=envelope_plus_awhp,
            blockers=tuple(dict.fromkeys(blockers)),
        )

    return AssignmentAssessment(
        status="QUALIFIED_EXPLICIT_PROGRAMME_SCENARIO_ASSIGNMENT",
        declared_programme_population=declared_programme_population,
        assigned_population=assigned,
        coverage_share=coverage,
        hp_only_population=hp_only,
        envelope_plus_awhp_population=envelope_plus_awhp,
        blockers=(),
    )
