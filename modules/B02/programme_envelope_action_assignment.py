"""B02-P81 bounded national envelope-action population inference contract.

P80 needs an action-conditioned population surface, but that does NOT require
household-by-household exact national identification.

Primary path:
representative public evidence -> semantic/freshness admission ->
multi-source bounded population inference -> uncertainty propagation.

Optional path:
an owner/policy scenario may provide an exact programme split, but that split
remains SCN/POL and is never promoted to observed Hungarian stock truth.

Critical boundaries:

FULL HOUSEHOLD ACTION IDENTIFICATION != REQUIRED
REPRESENTATIVE MULTI-SOURCE POPULATION INFERENCE = ADMISSIBLE
EVIDENCE-DERIVED ACTION MIX != EXACT POINT ASSIGNMENT
EVIDENCE-DERIVED ACTION MIX = BOUNDED / SET-VALUED / PROBABILISTIC
EXACT PROGRAMME ACTION MIX = SCENARIO / POLICY INPUT ONLY
OLD SOURCE != CURRENT STOCK WITHOUT TEMPORAL BRIDGE
THREE SOURCES != SIMPLE AVERAGE WITHOUT SEMANTIC COMPATIBILITY
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
class PopulationActionEvidence:
    source_id: str
    independent_source_family: str
    metric_key: str
    population_scope_key: str
    observation_year: int
    lower_share: float
    upper_share: float
    central_share: float | None = None
    aggregation_weight: float | None = None


@dataclass(frozen=True)
class PopulationInferenceAssessment:
    status: str
    metric_key: str
    population_scope_key: str
    reference_year: int
    freshness_floor_year: int
    fresh_source_count: int
    independent_fresh_source_count: int
    historical_compatible_source_count: int
    lower_share: float | None
    upper_share: float | None
    weighted_central_share: float | None
    source_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProgrammeActionAssignment:
    population_key: str
    assigned_dwelling_equivalents: float
    action: str
    assignment_class: str
    authority: str


@dataclass(frozen=True)
class ScenarioOverrideAssessment:
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
    """Return only source-supported current KEHOP policy constraints."""

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


def assess_bounded_population_action_inference(
    evidence: tuple[PopulationActionEvidence, ...],
    *,
    metric_key: str,
    population_scope_key: str,
    reference_year: int,
    freshness_floor_year: int,
    preferred_independent_sources: int = 3,
) -> PopulationInferenceAssessment:
    """Admit compatible fresh evidence into a bounded national inference.

    Only evidence matching the requested estimand and population scope enters
    the current inference. Older compatible evidence is counted as historical
    calibration but is not silently pooled into the current estimate.

    The primary result is always a conservative evidence envelope. An optional
    weighted centre is derived only when every admitted fresh source supplies a
    central estimate and an explicit positive aggregation weight, and the
    admitted rows represent independent source families.
    """

    blockers: list[str] = []
    warnings: list[str] = []

    if not metric_key:
        blockers.append("METRIC_KEY_REQUIRED")
    if not population_scope_key:
        blockers.append("POPULATION_SCOPE_KEY_REQUIRED")
    if freshness_floor_year > reference_year:
        blockers.append("FRESHNESS_FLOOR_AFTER_REFERENCE_YEAR")
    if preferred_independent_sources < 1:
        blockers.append("PREFERRED_INDEPENDENT_SOURCE_COUNT_MUST_BE_POSITIVE")

    compatible_fresh: list[PopulationActionEvidence] = []
    compatible_historical: list[PopulationActionEvidence] = []

    seen_source_ids: set[str] = set()
    for row in evidence:
        if not row.source_id:
            blockers.append("SOURCE_ID_REQUIRED")
            continue
        if row.source_id in seen_source_ids:
            blockers.append("DUPLICATE_SOURCE_ID")
            continue
        seen_source_ids.add(row.source_id)

        if not row.independent_source_family:
            blockers.append("INDEPENDENT_SOURCE_FAMILY_REQUIRED")
            continue
        if not (0.0 <= row.lower_share <= row.upper_share <= 1.0):
            blockers.append("SOURCE_SHARE_BOUNDS_OUTSIDE_UNIT_INTERVAL")
            continue
        if row.central_share is not None and not (
            row.lower_share <= row.central_share <= row.upper_share
        ):
            blockers.append("CENTRAL_SHARE_OUTSIDE_SOURCE_BOUNDS")
            continue
        if row.aggregation_weight is not None and row.aggregation_weight <= 0.0:
            blockers.append("AGGREGATION_WEIGHT_MUST_BE_POSITIVE")
            continue
        if row.observation_year > reference_year:
            blockers.append("FUTURE_EVIDENCE_YEAR_FORBIDDEN")
            continue

        if row.metric_key != metric_key or row.population_scope_key != population_scope_key:
            warnings.append(f"EXCLUDED_SEMANTICALLY_INCOMPATIBLE_SOURCE:{row.source_id}")
            continue

        if row.observation_year >= freshness_floor_year:
            compatible_fresh.append(row)
        else:
            compatible_historical.append(row)

    if blockers:
        return PopulationInferenceAssessment(
            status="Q",
            metric_key=metric_key,
            population_scope_key=population_scope_key,
            reference_year=reference_year,
            freshness_floor_year=freshness_floor_year,
            fresh_source_count=len(compatible_fresh),
            independent_fresh_source_count=len(
                {row.independent_source_family for row in compatible_fresh}
            ),
            historical_compatible_source_count=len(compatible_historical),
            lower_share=None,
            upper_share=None,
            weighted_central_share=None,
            source_ids=tuple(row.source_id for row in compatible_fresh),
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    if not compatible_fresh:
        blockers.append("FRESH_COMPARABLE_POPULATION_EVIDENCE_REQUIRED")
        return PopulationInferenceAssessment(
            status="Q",
            metric_key=metric_key,
            population_scope_key=population_scope_key,
            reference_year=reference_year,
            freshness_floor_year=freshness_floor_year,
            fresh_source_count=0,
            independent_fresh_source_count=0,
            historical_compatible_source_count=len(compatible_historical),
            lower_share=None,
            upper_share=None,
            weighted_central_share=None,
            source_ids=(),
            blockers=tuple(blockers),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    independent_families = {
        row.independent_source_family for row in compatible_fresh
    }
    independent_count = len(independent_families)

    if independent_count < preferred_independent_sources:
        warnings.append(
            "FEWER_THAN_PREFERRED_INDEPENDENT_FRESH_SOURCES"
        )

    lower = min(row.lower_share for row in compatible_fresh)
    upper = max(row.upper_share for row in compatible_fresh)

    weighted_central: float | None = None
    all_independent = independent_count == len(compatible_fresh)
    all_weighted = all(
        row.central_share is not None
        and row.aggregation_weight is not None
        and row.aggregation_weight > 0.0
        for row in compatible_fresh
    )
    if all_independent and all_weighted:
        total_weight = sum(row.aggregation_weight or 0.0 for row in compatible_fresh)
        weighted_central = sum(
            (row.central_share or 0.0) * (row.aggregation_weight or 0.0)
            for row in compatible_fresh
        ) / total_weight
    else:
        if not all_independent:
            warnings.append(
                "DEPENDENT_SOURCE_DUPLICATION_PREVENTS_CENTRAL_AGGREGATE"
            )
        if not all_weighted:
            warnings.append(
                "EXPLICIT_WEIGHTED_CENTRAL_ESTIMATE_NOT_AVAILABLE"
            )

    status = (
        "QUALIFIED_MULTI_SOURCE_BOUNDED_INFERENCE"
        if independent_count >= preferred_independent_sources
        else "PARTIAL_MULTI_SOURCE_BOUNDED_INFERENCE"
    )

    return PopulationInferenceAssessment(
        status=status,
        metric_key=metric_key,
        population_scope_key=population_scope_key,
        reference_year=reference_year,
        freshness_floor_year=freshness_floor_year,
        fresh_source_count=len(compatible_fresh),
        independent_fresh_source_count=independent_count,
        historical_compatible_source_count=len(compatible_historical),
        lower_share=lower,
        upper_share=upper,
        weighted_central_share=weighted_central,
        source_ids=tuple(row.source_id for row in compatible_fresh),
        blockers=(),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def assess_explicit_programme_scenario_override(
    assignments: tuple[ProgrammeActionAssignment, ...],
    *,
    declared_programme_population: float,
) -> ScenarioOverrideAssessment:
    """Validate an optional exact SCN/POL override.

    Exact closure is required only for this explicit scenario/policy route.
    This function is not the evidence-derived national population inference.
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
        blockers.append("EXPLICIT_SCENARIO_OVERRIDE_REQUIRED_FOR_OVERRIDE_PATH")

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
        blockers.append("SCENARIO_OVERRIDE_MUST_CLOSE_TO_DECLARED_POPULATION")

    if blockers:
        return ScenarioOverrideAssessment(
            status="Q",
            declared_programme_population=declared_programme_population,
            assigned_population=assigned,
            coverage_share=coverage,
            hp_only_population=hp_only,
            envelope_plus_awhp_population=envelope_plus_awhp,
            blockers=tuple(dict.fromkeys(blockers)),
        )

    return ScenarioOverrideAssessment(
        status="QUALIFIED_EXPLICIT_PROGRAMME_SCENARIO_OVERRIDE",
        declared_programme_population=declared_programme_population,
        assigned_population=assigned,
        coverage_share=coverage,
        hp_only_population=hp_only,
        envelope_plus_awhp_population=envelope_plus_awhp,
        blockers=(),
    )
