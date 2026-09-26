"""B05-P42 current-revision coordinate-gap closure boundaries."""
from __future__ import annotations

DIMPLEX_CURRENT_REVISION = "SYSTEM_C_VERSION_03_2026"
DIMPLEX_CURRENT_POINT_COUNT = 30
DIMPLEX_CURRENT_CELL_COUNT = 18
DIMPLEX_A_MINUS10_MINIMUM_POINTS = {
    35.0: {"minimum_capacity_kw": 9.10, "minimum_input_kw": 2.77, "minimum_cop": 3.28},
    45.0: {"minimum_capacity_kw": 8.73, "minimum_input_kw": 3.36, "minimum_cop": 2.60},
    55.0: {"minimum_capacity_kw": 8.51, "minimum_input_kw": 4.03, "minimum_cop": 2.11},
}
MITSUBISHI_A_MINUS15_W50_CLASSIFICATION = (
    "Q_PERSISTENT_ALL_LEVELS_BLANK_EXACT_THRESHOLD_NOT_PUBLISHED"
)

def validate_dimplex_a_minus10_points() -> None:
    if set(DIMPLEX_A_MINUS10_MINIMUM_POINTS) != {35.0, 45.0, 55.0}:
        raise ValueError("exact W35/W45/W55 coordinates required")
    for point in DIMPLEX_A_MINUS10_MINIMUM_POINTS.values():
        if min(point.values()) <= 0:
            raise ValueError("all exact source-native values must be positive")

def p42_boundary() -> tuple[str, ...]:
    return (
        "CURRENT_DIMPLEX_03_2026_REVISION_IS_COHERENT_AUTHORITY",
        "NO_CROSS_VERSION_MIXING_WITH_P23",
        "DETAILED_SOURCE_NATIVE_A_MINUS10_POINTS_ARE_OBS",
        "COMPLETE_CELL_REQUIRED_FOR_DER",
        "NO_CDH_INTERPOLATION",
        "MITSUBISHI_PERSISTENT_BLANK_IS_NOT_PHYSICAL_IMPOSSIBILITY",
        "NO_GRAPH_DIGITIZATION",
        "NO_CROSS_PRODUCT_TRANSFER",
    )
