"""B02-P48 bounded current emitter-stock anchor.

P48 materialises one current Hungarian district-heated housing cohort where a
beneficiary publishes exact building/cohort counts and exact current emitter-
position quantities. The source also explicitly says the device population
includes dwellings and rental premises, so per-dwelling ratios remain withheld
unless a residential-only denominator binding is separately proven.

The result is a bounded empirical stock anchor, not national P42 authority.
"""

from __future__ import annotations

from dataclasses import dataclass


P42_CLAIMS = (
    "RADIATOR_STOCK_DWELLING_COUNT",
    "RADIATOR_STOCK_UNIT_COUNT",
    "RADIATOR_TYPE_SIZE_DISTRIBUTION",
    "RADIATOR_REUSE_UPGRADE_REQUIREMENT",
    "RADIATOR_REPLACEMENT_QUANTITY",
)


@dataclass(frozen=True)
class CurrentEmitterStockCandidate:
    anchor_id: str
    country: str
    segment: str
    dwelling_count: int
    building_count: int
    installed_cost_allocator_count: int
    bathroom_radiator_place_count: int
    cost_allocator_is_per_emitter: bool
    bathroom_places_are_additional: bool
    same_cohort_binding: bool
    device_population_includes_non_dwelling_premises: bool
    residential_only_device_denominator_proven: bool
    current_tkm_all_buildings_awarded: bool
    tkm_award_amount_huf: int | None
    tkm_execution_started: bool
    tkm_execution_completed: bool
    current_stock_source_url: str
    tkm_execution_source_url: str
    reproducible_binding: bool


@dataclass(frozen=True)
class CurrentEmitterStockDecision:
    status: str
    reasons: tuple[str, ...]
    emitter_position_count: int | None
    cost_allocators_per_dwelling: float | None
    emitter_positions_per_dwelling: float | None
    ratio_status: str
    tkm_execution_status: str
    p42_national_authority: bool
    unresolved_p42_claims: tuple[str, ...]


def assess_current_emitter_stock_anchor(
    candidate: CurrentEmitterStockCandidate,
) -> CurrentEmitterStockDecision:
    """Qualify exact bounded stock quantities without national promotion."""

    reasons: list[str] = []
    if not candidate.anchor_id.strip():
        reasons.append("NO_ANCHOR_ID")
    if candidate.country != "HU":
        reasons.append("NOT_HUNGARY")
    if not candidate.segment.strip():
        reasons.append("NO_SEGMENT")
    if candidate.dwelling_count <= 0:
        reasons.append("INVALID_DWELLING_COUNT")
    if candidate.building_count <= 0:
        reasons.append("INVALID_BUILDING_COUNT")
    if candidate.installed_cost_allocator_count < 0:
        reasons.append("INVALID_COST_ALLOCATOR_COUNT")
    if candidate.bathroom_radiator_place_count < 0:
        reasons.append("INVALID_BATHROOM_RADIATOR_PLACE_COUNT")
    if not candidate.cost_allocator_is_per_emitter:
        reasons.append("COST_ALLOCATOR_NOT_BOUND_PER_EMITTER")
    if not candidate.bathroom_places_are_additional:
        reasons.append("BATHROOM_PLACE_OVERLAP_UNRESOLVED")
    if not candidate.same_cohort_binding:
        reasons.append("STOCK_COUNTS_NOT_SAME_COHORT")
    if not candidate.current_stock_source_url.strip():
        reasons.append("NO_CURRENT_STOCK_SOURCE")
    if not candidate.tkm_execution_source_url.strip():
        reasons.append("NO_TKM_EXECUTION_SOURCE")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")
    if candidate.tkm_award_amount_huf is not None and candidate.tkm_award_amount_huf < 0:
        reasons.append("INVALID_TKM_AWARD_AMOUNT")

    qualified = not reasons
    emitter_position_count = None
    cost_allocators_per_dwelling = None
    emitter_positions_per_dwelling = None
    ratio_status = "Q"

    if qualified:
        emitter_position_count = (
            candidate.installed_cost_allocator_count
            + candidate.bathroom_radiator_place_count
        )

        # A published residential-unit denominator is insufficient when the
        # device numerator explicitly also covers rental/non-dwelling premises.
        # Ratios become admissible only after a residential-only device binding
        # is independently proven.
        ratio_admissible = bool(
            not candidate.device_population_includes_non_dwelling_premises
            or candidate.residential_only_device_denominator_proven
        )
        if ratio_admissible:
            cost_allocators_per_dwelling = (
                candidate.installed_cost_allocator_count / candidate.dwelling_count
            )
            emitter_positions_per_dwelling = (
                emitter_position_count / candidate.dwelling_count
            )
            ratio_status = "QUALIFIED_RESIDENTIAL_RATIO"
        else:
            ratio_status = "Q_NON_DWELLING_NUMERATOR_CONTAMINATION"

    if candidate.tkm_execution_completed:
        tkm_execution_status = "COMPLETED"
    elif candidate.tkm_execution_started:
        tkm_execution_status = "STARTED_NOT_COMPLETED"
    elif candidate.current_tkm_all_buildings_awarded:
        tkm_execution_status = "AWARDED_NOT_COMPLETED"
    else:
        tkm_execution_status = "NO_PROVEN_TKM_EXECUTION"

    # P48 is one bounded district-heated cohort. It cannot establish the
    # national radiator dwelling/unit stock, type/size distribution, reuse
    # classification or programme replacement quantity.
    return CurrentEmitterStockDecision(
        status="QUALIFIED_BOUNDED_CURRENT_STOCK_ANCHOR" if qualified else "Q",
        reasons=tuple(reasons),
        emitter_position_count=emitter_position_count,
        cost_allocators_per_dwelling=cost_allocators_per_dwelling,
        emitter_positions_per_dwelling=emitter_positions_per_dwelling,
        ratio_status=ratio_status,
        tkm_execution_status=tkm_execution_status,
        p42_national_authority=False,
        unresolved_p42_claims=P42_CLAIMS,
    )
