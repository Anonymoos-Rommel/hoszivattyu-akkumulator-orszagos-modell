"""B02-P106 non-EKR replaced-window performance calibration.

P104/P105 left:
NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED.

P106 re-audits the public Hungarian / EU evidence surface and narrows that
requirement. A direct representative Hungarian replaced-window Uw distribution
is still the strongest route, but no such public distribution was identified.

A second, explicitly model-based route exists through the 2026 TU Wien
Invert/EE-Lab EU27 residential-stock dataset. The public dataset includes HUN,
5-year stock states, source-native archetype names encoding renovation
generation, total window area, Htr_w and model stock weights. This permits an
area-weighted effective window transmission coefficient:

    U_eff = Htr_w / A_windows

at model archetype grain.

This is SCN/DER model calibration. It is NOT:
- observed product Uw;
- measured in-situ performance;
- proof that renovation generation == window replacement;
- proof of EKR exclusion;
- national replaced-window compliance share.

Population promotion requires an explicit bridge to the observed TARKI-REKK
2022 replacement-state surface and explicit EKR overlap handling.

Critical boundaries:

MODEL_EFFECTIVE_WINDOW_U != OBSERVED_REPLACED_WINDOW_UW
RENOVATION_GENERATION != WINDOW_REPLACEMENT_EVENT
INVERT_STOCK_WEIGHT != KSH_OR_TARKI_SURVEY_WEIGHT
HUN_MODEL_ARCHETYPE != OBSERVED_HOUSEHOLD
MODEL_CALIBRATION != NATIONAL_COMPLIANCE_SHARE
NON_EKR_LABEL_REQUIRES_EXPLICIT_EKR_OVERLAP_HANDLING
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from collections import defaultdict

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)


P106_STATUS = "QUALIFIED_NON_EKR_WINDOW_MODEL_CALIBRATION_ROUTE"
SUPERSEDED_SUB_BLOCKER = "NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED"
PRIMARY_NEXT_RESIDUAL = "NON_EKR_REPLACED_WINDOW_PERFORMANCE_CALIBRATION_REQUIRED"
INVERT_EXTRACT_RESIDUAL = (
    "INVERT_HUN_RENOVATION_GENERATION_WINDOW_SURFACE_EXTRACT_REQUIRED"
)
OBS_BRIDGE_RESIDUAL = "MODEL_TO_OBS_REPLACED_WINDOW_CALIBRATION_REQUIRED"
EKR_OVERLAP_RESIDUAL = "NON_EKR_EKR1103_OVERLAP_BOUND_REQUIRED"
DIRECT_OBS_RESIDUAL = "REPRESENTATIVE_HUNGARIAN_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"
WALL_SECONDARY_RESIDUAL = "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"

CURRENT_MODEL_YEAR = 2025
HISTORICAL_MODEL_YEAR = 2020
PROGRAMME_WINDOW_REFERENCE_U = 1.10


@dataclass(frozen=True)
class InvertWindowArchetype:
    country: str
    year: int
    name: str
    renovation_generation: str | None
    area_windows_m2: float
    htr_w_w_per_k: float
    number_of_buildings: float
    dwellings_per_building: float

    @property
    def dwelling_weight(self) -> float:
        return self.number_of_buildings * self.dwellings_per_building

    @property
    def effective_window_u_w_m2k(self) -> float:
        return self.htr_w_w_per_k / self.area_windows_m2


@dataclass(frozen=True)
class RenovationGenerationWindowSummary:
    generation: str
    dwelling_weight: float
    weighted_mean_effective_u_w_m2k: float
    min_effective_u_w_m2k: float
    max_effective_u_w_m2k: float
    model_share_at_or_below_1_10: float


def validate_invert_window_archetype(row: InvertWindowArchetype) -> None:
    if row.country != "HUN":
        raise ValueError("country must be HUN for the P106 Hungary route")
    if row.year not in (HISTORICAL_MODEL_YEAR, CURRENT_MODEL_YEAR):
        raise ValueError("P106 calibration admits only model years 2020 or 2025")
    if not row.name.strip():
        raise ValueError("source-native archetype name is required")
    if not isfinite(row.area_windows_m2) or row.area_windows_m2 <= 0:
        raise ValueError("area_windows_m2 must be finite and positive")
    if not isfinite(row.htr_w_w_per_k) or row.htr_w_w_per_k < 0:
        raise ValueError("htr_w_w_per_k must be finite and non-negative")
    if not isfinite(row.number_of_buildings) or row.number_of_buildings < 0:
        raise ValueError("number_of_buildings must be finite and non-negative")
    if (
        not isfinite(row.dwellings_per_building)
        or row.dwellings_per_building <= 0
    ):
        raise ValueError("dwellings_per_building must be finite and positive")
    u_eff = row.effective_window_u_w_m2k
    if not isfinite(u_eff) or u_eff < 0:
        raise ValueError("derived effective window U must be finite and non-negative")


def summarize_by_renovation_generation(
    rows: list[InvertWindowArchetype],
) -> tuple[RenovationGenerationWindowSummary, ...]:
    """Aggregate model rows by explicit renovation-generation label.

    Unknown generation labels are not silently assigned to renovated or
    unrenovated classes. Rows with missing generation are grouped as UNKNOWN.
    """

    if not rows:
        raise ValueError("at least one Invert window archetype is required")

    groups: dict[str, list[InvertWindowArchetype]] = defaultdict(list)
    for row in rows:
        validate_invert_window_archetype(row)
        generation = (
            row.renovation_generation.strip()
            if row.renovation_generation is not None
            and row.renovation_generation.strip()
            else "UNKNOWN"
        )
        groups[generation].append(row)

    result: list[RenovationGenerationWindowSummary] = []
    for generation in sorted(groups):
        group = groups[generation]
        weights = [r.dwelling_weight for r in group]
        total_weight = sum(weights)
        if total_weight <= 0:
            raise ValueError(
                f"renovation generation {generation} has no positive dwelling weight"
            )

        us = [r.effective_window_u_w_m2k for r in group]
        weighted_mean = sum(
            r.effective_window_u_w_m2k * r.dwelling_weight for r in group
        ) / total_weight
        satisfied_weight = sum(
            r.dwelling_weight
            for r in group
            if r.effective_window_u_w_m2k <= PROGRAMME_WINDOW_REFERENCE_U
        )

        result.append(
            RenovationGenerationWindowSummary(
                generation=generation,
                dwelling_weight=total_weight,
                weighted_mean_effective_u_w_m2k=weighted_mean,
                min_effective_u_w_m2k=min(us),
                max_effective_u_w_m2k=max(us),
                model_share_at_or_below_1_10=satisfied_weight / total_weight,
            )
        )
    return tuple(result)


def can_promote_invert_to_population_calibration(
    *,
    hun_extract_complete_for_declared_scope: bool,
    renovation_generation_semantics_explicit: bool,
    observed_replacement_state_bridge: bool,
    ekr_overlap_explicit_or_bounded: bool,
) -> tuple[bool, tuple[str, ...]]:
    blockers: list[str] = []
    if not hun_extract_complete_for_declared_scope:
        blockers.append(INVERT_EXTRACT_RESIDUAL)
    if not renovation_generation_semantics_explicit:
        blockers.append("RENOVATION_GENERATION_SEMANTICS_REQUIRED")
    if not observed_replacement_state_bridge:
        blockers.append(OBS_BRIDGE_RESIDUAL)
    if not ekr_overlap_explicit_or_bounded:
        blockers.append(EKR_OVERLAP_RESIDUAL)
    return (not blockers, tuple(blockers))


def p106_state() -> dict[str, object]:
    return {
        "status": P106_STATUS,
        "superseded_sub_blocker": SUPERSEDED_SUB_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "qualified_routes": (
            "DIRECT_REPRESENTATIVE_HUNGARIAN_REPLACED_WINDOW_UW",
            "INVERT_HUN_MODEL_SURFACE_PLUS_OBS_CALIBRATION",
        ),
        "invert_hun_public_dataset_identified": True,
        "invert_hun_model_years_available": (2020, 2025, 2030, 2035, 2040, 2045, 2050),
        "invert_window_effective_u_formula": "Htr_w / areawindows",
        "invert_numeric_hun_extract_materialized_in_repo": False,
        "direct_observed_replaced_window_uw_distribution_identified": False,
        "national_non_ekr_window_compliance_share_identified": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p106_numeric_national_action_tightening": False,
        "residuals": (
            INVERT_EXTRACT_RESIDUAL,
            OBS_BRIDGE_RESIDUAL,
            EKR_OVERLAP_RESIDUAL,
            DIRECT_OBS_RESIDUAL,
            WALL_SECONDARY_RESIDUAL,
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "MODEL_EFFECTIVE_WINDOW_U_IS_NOT_OBSERVED_REPLACED_WINDOW_UW",
        "RENOVATION_GENERATION_IS_NOT_WINDOW_REPLACEMENT_EVENT",
        "INVERT_STOCK_WEIGHT_IS_NOT_KSH_OR_TARKI_SURVEY_WEIGHT",
        "HUN_MODEL_ARCHETYPE_IS_NOT_OBSERVED_HOUSEHOLD",
        "MODEL_CALIBRATION_IS_NOT_NATIONAL_COMPLIANCE_SHARE",
        "NON_EKR_LABEL_REQUIRES_EXPLICIT_EKR_OVERLAP_HANDLING",
    )
