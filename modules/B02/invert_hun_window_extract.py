"""B02-P107 numeric HUN Invert window-surface extract.

P106 qualified a possible model-calibration route and left:
INVERT_HUN_RENOVATION_GENERATION_WINDOW_SURFACE_EXTRACT_REQUIRED.

P107 executes the public Zenodo extract for HUN / 2025, pins the source MD5,
materializes only derived Hungarian CSVs, and then audits whether the model
renovation-generation surface can be promoted into a replaced-window
performance distribution.

Result: the numeric extract is valid, but direct population promotion is not.

The 2025 HUN slice contains only:
- source-native no-generation-suffix rows -> BASE_GENERATION;
- explicit _gen2 rows.

No _gen3 or _gen4 rows occur in HUN 2025.

The modelled gen2 group does not improve window U_eff monotonically relative to
the base group. Its dwelling-weighted mean U_eff is higher. Only three HUN 2025
archetype rows satisfy U_eff <= 1.10 W/m2K, all source-native New_MFH_1_MFH
rows with construction years 2020, 2022, and 2025; gen2 has zero qualifying
rows.

Therefore:
WHOLE_BUILDING_RENOVATION_GENERATION != WINDOW_REPLACEMENT_EVENT
and the TARKI-REKK observed WINDOW_REPLACED share cannot be bound directly to
Invert renovation generations.

The Invert HUN surface remains useful as full-stock model validation/sensitivity
evidence, but not as a national non-EKR replaced-window compliance estimator.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)


P107_STATUS = "QUALIFIED_NUMERIC_EXTRACT_ROUTE_REJECTED_FOR_DIRECT_WINDOW_POPULATION_PROMOTION"

RESOLVED_EXTRACT_BLOCKER = "INVERT_HUN_RENOVATION_GENERATION_WINDOW_SURFACE_EXTRACT_REQUIRED"
SUPERSEDED_CALIBRATION_BLOCKER = "MODEL_TO_OBS_REPLACED_WINDOW_CALIBRATION_REQUIRED"
PRIMARY_NEXT_RESIDUAL = "COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED"
DIRECT_OBS_RESIDUAL = "REPRESENTATIVE_HUNGARIAN_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"
MEKH_RESIDUAL = "MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED"
WALL_SECONDARY_RESIDUAL = "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"

SOURCE_MD5 = "71e630ff7c575507d385208ba832513a"

HUN_2025_ARCHETYPE_ROWS = 1358
HUN_2025_MODEL_DWELLING_WEIGHT = 3515973.0
CANONICAL_OCCUPIED_DWELLINGS = 4008541
INVERT_TO_CANONICAL_DWELLING_WEIGHT_RATIO = 0.877120378711

BASE_GENERATION_ROWS = 1002
BASE_GENERATION_DWELLING_WEIGHT = 2744573.5
BASE_GENERATION_SHARE = 0.78060144186
BASE_GENERATION_DWELLING_WEIGHTED_UEFF = 3.95483899117

GEN2_ROWS = 356
GEN2_DWELLING_WEIGHT = 771399.0
GEN2_SHARE = 0.219398438931
GEN2_DWELLING_WEIGHTED_UEFF = 4.2734375
GEN2_MINUS_BASE_MEAN_UEFF = 0.31859850883

REFERENCE_1_10_ROWS = 3
REFERENCE_1_10_DWELLING_WEIGHT = 964.809265137
REFERENCE_1_10_SHARE_OF_INVERT_HUN_2025 = 0.000274407473
GEN2_REFERENCE_1_10_ROWS = 0


@dataclass(frozen=True)
class InvertGenerationIdentity:
    source_name: str
    generation: str
    explicit_renovated_generation: bool


def classify_source_generation(name: str) -> InvertGenerationIdentity:
    """Preserve the source-native generation suffix contract."""

    source_name = str(name).strip()
    if not source_name:
        raise ValueError("source name is required")

    match = re.search(r"(?i)_gen([234])$", source_name)
    if match:
        generation = f"gen{match.group(1)}"
        return InvertGenerationIdentity(
            source_name=source_name,
            generation=generation,
            explicit_renovated_generation=True,
        )

    if re.search(r"(?i)_gen\d+$", source_name):
        raise ValueError(f"unsupported explicit generation suffix: {source_name}")

    return InvertGenerationIdentity(
        source_name=source_name,
        generation="BASE_GENERATION",
        explicit_renovated_generation=False,
    )


def can_promote_invert_generation_to_replaced_window_population() -> tuple[bool, tuple[str, ...]]:
    """P107 conclusion for direct Invert-generation -> window-replacement use."""

    return (
        False,
        (
            "RENOVATION_GENERATION_IS_NOT_COMPONENT_SPECIFIC_WINDOW_REPLACEMENT",
            "GEN2_WINDOW_UEFF_IS_NOT_MONOTONIC_IMPROVEMENT_OVER_BASE",
            "REFERENCE_1_10_ROWS_ARE_NEW_CONSTRUCTION_NOT_GEN2_RENOVATION",
            "INVERT_MODEL_DWELLING_WEIGHT_IS_NOT_CANONICAL_B02_OCCUPIED_DENOMINATOR",
            PRIMARY_NEXT_RESIDUAL,
        ),
    )


def p107_state() -> dict[str, object]:
    return {
        "status": P107_STATUS,
        "source_md5": SOURCE_MD5,
        "resolved_blocker": RESOLVED_EXTRACT_BLOCKER,
        "superseded_blocker": SUPERSEDED_CALIBRATION_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "hun_2025_archetype_rows": HUN_2025_ARCHETYPE_ROWS,
        "hun_2025_model_dwelling_weight": HUN_2025_MODEL_DWELLING_WEIGHT,
        "canonical_occupied_dwellings": CANONICAL_OCCUPIED_DWELLINGS,
        "invert_to_canonical_dwelling_weight_ratio": INVERT_TO_CANONICAL_DWELLING_WEIGHT_RATIO,
        "base_generation_rows": BASE_GENERATION_ROWS,
        "base_generation_share": BASE_GENERATION_SHARE,
        "base_generation_dwelling_weighted_ueff": BASE_GENERATION_DWELLING_WEIGHTED_UEFF,
        "gen2_rows": GEN2_ROWS,
        "gen2_share": GEN2_SHARE,
        "gen2_dwelling_weighted_ueff": GEN2_DWELLING_WEIGHTED_UEFF,
        "gen2_minus_base_mean_ueff": GEN2_MINUS_BASE_MEAN_UEFF,
        "reference_1_10_rows": REFERENCE_1_10_ROWS,
        "reference_1_10_dwelling_weight": REFERENCE_1_10_DWELLING_WEIGHT,
        "reference_1_10_share_of_invert_hun_2025": REFERENCE_1_10_SHARE_OF_INVERT_HUN_2025,
        "gen2_reference_1_10_rows": GEN2_REFERENCE_1_10_ROWS,
        "invert_extract_materialized": True,
        "invert_direct_replaced_window_population_promotion_admitted": False,
        "national_non_ekr_window_compliance_share_identified": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p107_numeric_national_action_tightening": False,
        "parallel_residuals": (
            DIRECT_OBS_RESIDUAL,
            MEKH_RESIDUAL,
            WALL_SECONDARY_RESIDUAL,
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "BASE_GENERATION_IS_NOT_REPLACED_WINDOW_CLASS",
        "GEN2_IS_WHOLE_BUILDING_RENOVATION_NOT_WINDOW_REPLACEMENT",
        "MODEL_UEFF_IS_NOT_OBSERVED_PRODUCT_UW",
        "NEW_CONSTRUCTION_REFERENCE_ROWS_ARE_NOT_REPLACED_WINDOW_EVIDENCE",
        "INVERT_MODEL_WEIGHT_IS_NOT_CANONICAL_B02_POPULATION_WEIGHT",
        "TARKI_WINDOW_REPLACED_SHARE_CANNOT_BE_DIRECTLY_MAPPED_TO_INVERT_GENERATION",
    )
