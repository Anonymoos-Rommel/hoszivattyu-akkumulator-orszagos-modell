"""B02-P115 official 23-type population weighting for envelope calibration.

P102 produced a conservative calibrated retrofit floor by mapping exact WBL
period x building-group strata to complete *sets* of compatible KEOP23 types.
That was fail-closed, but it intentionally discarded source-native national
type-mixture information.

Hungary's First Biennial Transparency Report (BTR1), submitted to UNFCCC,
publishes the same 23-type Hungarian residential building typology together
with occupied-dwelling counts for every type. The table cites the same 2015
Csoknyai/Farkas/Formanek/Horvath Building Typology Study used by the P79-P102
chain.

P115 therefore uses:
- P21 exact canonical FAMILY_HOUSE / MULTI_DWELLING masses over 4,008,541
  occupied dwellings;
- BTR1 source-native *within-group* type shares;
- P102 exact type-level calibrated envelope-deficit floors.

This avoids treating the BTR1 3,727,164 model total as the canonical Census
denominator. BTR1 supplies conditional type mixture only; P21 retains the
canonical national group totals.

Result:
- official-type-weighted calibrated deficit floor = 96.6151829747%;
- HP_ONLY candidate upper edge = 3.38481702535%;
- previous P102 floor = 82.7861029945%;
- tightening = 13.8290799802 percentage points.

This remains calibrated population inference, not household-level observation.
The remaining uncertainty is concentrated in types 11, 15, 16 and 23, where
P102 lacks historical renovated-wall U and/or realized replaced-window Uw.

Critical boundaries:
BTR_TYPE_WEIGHT != CENSUS_DWELLING_IDENTITY
WITHIN_GROUP_TYPE_SHARE != RAW_BTR_TOTAL_AS_CANONICAL_DENOMINATOR
OFFICIAL_MODEL_WEIGHTED_CALIBRATION != OBSERVED_HOUSEHOLD_FAIL_RATE
NATIONAL_TYPE_MIX != LOCAL_WBL_POINT_TYPE_ASSIGNMENT
TYPE_11_15_16_23_RESIDUAL != WHOLE_STOCK_MULTIGLAZED_UW_BLOCKER
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage
from modules.B02.renovated_envelope_u_quality import type_renovated_wall_quality


ROOT = Path(__file__).resolve().parents[2]
WEIGHT_PATH = ROOT / "data" / "processed" / "b02" / "p115_unfccc_btr_type_weights.csv"

EXPECTED_TYPE_IDS = tuple(range(1, 24))
EXPECTED_BTR_FAMILY_TOTAL = 2_333_452
EXPECTED_BTR_MULTI_TOTAL = 1_393_712
EXPECTED_BTR_TOTAL = 3_727_164
EXPECTED_CANONICAL_OCCUPIED = 4_008_541
EXPECTED_P21_FAMILY = 2_423_136
EXPECTED_P21_MULTI = 1_585_405

PREVIOUS_P102_FLOOR = 0.8278610299446981
PREVIOUS_P102_HP_ONLY_UPPER = 0.17213897005530188

P115_STATUS = "QUALIFIED_OFFICIAL_TYPE_WEIGHTED_ENVELOPE_CALIBRATION"
PRIMARY_NEXT_RESIDUAL = "TYPES_11_15_16_23_CURRENT_ENVELOPE_POSTSTATE_REQUIRED"
WINDOW_RESIDUAL = "TYPES_11_15_16_REPLACED_WINDOW_UW_QUALITY_REQUIRED"
WALL_RESIDUAL = "TYPES_11_15_16_23_RENOVATED_WALL_U_QUALITY_REQUIRED"

PROBLEM_TYPE_IDS = (11, 15, 16, 23)


@dataclass(frozen=True)
class BtrTypeWeight:
    type_id: int
    building_group: str
    occupied_dwellings: int


@dataclass(frozen=True)
class GroupCalibration:
    building_group: str
    btr_group_total: int
    p21_canonical_group_total: float
    calibrated_deficit_floor_share: float
    calibrated_deficit_upper_share: float


@dataclass(frozen=True)
class NationalCalibration:
    occupied_dwellings: float
    calibrated_deficit_floor_dwellings: float
    calibrated_deficit_floor_share: float
    calibrated_deficit_upper_share: float
    hp_only_share_lower: float
    hp_only_share_upper: float
    previous_floor_share: float
    floor_gain: float
    previous_hp_only_upper: float
    hp_only_upper_reduction: float


@lru_cache(maxsize=1)
def load_btr_type_weights() -> dict[int, BtrTypeWeight]:
    with WEIGHT_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if tuple(sorted(int(r["type_id"]) for r in rows)) != EXPECTED_TYPE_IDS:
        raise ValueError("BTR type IDs must be exactly 1..23")

    result: dict[int, BtrTypeWeight] = {}
    for row in rows:
        type_id = int(row["type_id"])
        group = row["building_group"]
        count = int(row["btr_occupied_dwellings"])
        if group not in ("FAMILY_HOUSE", "MULTI_DWELLING"):
            raise ValueError(f"unsupported group {group}")
        if count <= 0:
            raise ValueError("BTR occupied count must be positive")
        result[type_id] = BtrTypeWeight(type_id, group, count)

    family = sum(x.occupied_dwellings for x in result.values() if x.building_group == "FAMILY_HOUSE")
    multi = sum(x.occupied_dwellings for x in result.values() if x.building_group == "MULTI_DWELLING")
    if family != EXPECTED_BTR_FAMILY_TOTAL:
        raise ValueError("BTR family total drift")
    if multi != EXPECTED_BTR_MULTI_TOTAL:
        raise ValueError("BTR multi total drift")
    if family + multi != EXPECTED_BTR_TOTAL:
        raise ValueError("BTR total drift")
    return result


def _group_type_ids(group: str) -> tuple[int, ...]:
    weights = load_btr_type_weights()
    return tuple(sorted(i for i, x in weights.items() if x.building_group == group))


def _weighted_group(group: str, *, use_upper: bool) -> float:
    weights = load_btr_type_weights()
    ids = _group_type_ids(group)
    denominator = sum(weights[i].occupied_dwellings for i in ids)
    numerator = 0.0
    for type_id in ids:
        state = type_renovated_wall_quality(type_id)
        share = (
            state.combined_calibrated_deficit_upper_share
            if use_upper
            else state.combined_calibrated_deficit_floor_share
        )
        numerator += weights[type_id].occupied_dwellings * share
    return numerator / denominator


@lru_cache(maxsize=1)
def group_calibrations() -> tuple[GroupCalibration, ...]:
    _, p21 = build_calibrated_linkage()
    if int(p21.occupied_dwellings) != EXPECTED_CANONICAL_OCCUPIED:
        raise ValueError("P21 occupied denominator drift")
    if int(round(p21.family_target_dwellings)) != EXPECTED_P21_FAMILY:
        raise ValueError("P21 family target drift")
    if int(round(p21.multi_target_dwellings)) != EXPECTED_P21_MULTI:
        raise ValueError("P21 multi target drift")

    weights = load_btr_type_weights()
    output = []
    for group, canonical in (
        ("FAMILY_HOUSE", float(p21.family_target_dwellings)),
        ("MULTI_DWELLING", float(p21.multi_target_dwellings)),
    ):
        ids = _group_type_ids(group)
        source_total = sum(weights[i].occupied_dwellings for i in ids)
        output.append(
            GroupCalibration(
                building_group=group,
                btr_group_total=source_total,
                p21_canonical_group_total=canonical,
                calibrated_deficit_floor_share=_weighted_group(group, use_upper=False),
                calibrated_deficit_upper_share=_weighted_group(group, use_upper=True),
            )
        )
    return tuple(output)


@lru_cache(maxsize=1)
def national_calibration() -> NationalCalibration:
    groups = {x.building_group: x for x in group_calibrations()}
    occupied = sum(x.p21_canonical_group_total for x in groups.values())
    if abs(occupied - EXPECTED_CANONICAL_OCCUPIED) > 1e-6:
        raise ValueError("canonical occupied total drift")

    lo_dw = sum(
        x.p21_canonical_group_total * x.calibrated_deficit_floor_share
        for x in groups.values()
    )
    hi_dw = sum(
        x.p21_canonical_group_total * x.calibrated_deficit_upper_share
        for x in groups.values()
    )
    lo = lo_dw / occupied
    hi = hi_dw / occupied
    hp_upper = 1.0 - lo

    return NationalCalibration(
        occupied_dwellings=occupied,
        calibrated_deficit_floor_dwellings=lo_dw,
        calibrated_deficit_floor_share=lo,
        calibrated_deficit_upper_share=hi,
        hp_only_share_lower=0.0,
        hp_only_share_upper=hp_upper,
        previous_floor_share=PREVIOUS_P102_FLOOR,
        floor_gain=lo - PREVIOUS_P102_FLOOR,
        previous_hp_only_upper=PREVIOUS_P102_HP_ONLY_UPPER,
        hp_only_upper_reduction=PREVIOUS_P102_HP_ONLY_UPPER - hp_upper,
    )


def problematic_type_surface() -> tuple[dict[str, object], ...]:
    weights = load_btr_type_weights()
    output = []
    for type_id in PROBLEM_TYPE_IDS:
        state = type_renovated_wall_quality(type_id)
        output.append(
            {
                "type_id": type_id,
                "building_group": weights[type_id].building_group,
                "btr_occupied_dwellings": weights[type_id].occupied_dwellings,
                "wall_deficit_share": state.calibrated_wall_deficit_share,
                "window_not_replaced_deficit_share": (
                    state.current_window_not_replaced_deficit_share
                ),
                "combined_floor_share": state.combined_calibrated_deficit_floor_share,
                "combined_upper_share": state.combined_calibrated_deficit_upper_share,
                "residuals": state.residuals,
            }
        )
    return tuple(output)


def p115_state() -> dict[str, object]:
    n = national_calibration()
    weights = load_btr_type_weights()
    problem_source_total = sum(weights[i].occupied_dwellings for i in PROBLEM_TYPE_IDS)
    return {
        "status": P115_STATUS,
        "source_type_count": len(weights),
        "btr_family_total": EXPECTED_BTR_FAMILY_TOTAL,
        "btr_multi_total": EXPECTED_BTR_MULTI_TOTAL,
        "btr_total": EXPECTED_BTR_TOTAL,
        "p21_family_total": EXPECTED_P21_FAMILY,
        "p21_multi_total": EXPECTED_P21_MULTI,
        "canonical_occupied_total": EXPECTED_CANONICAL_OCCUPIED,
        "btr_total_used_as_canonical_denominator": False,
        "within_group_source_native_type_weights_used": True,
        "problem_type_ids": PROBLEM_TYPE_IDS,
        "problem_type_btr_total": problem_source_total,
        "problem_type_btr_share": problem_source_total / EXPECTED_BTR_TOTAL,
        "national_calibration": n.__dict__,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "window_residual": WINDOW_RESIDUAL,
        "wall_residual": WALL_RESIDUAL,
        "national_point_type_mix_blocker_resolved": True,
        "p115_numeric_tightening": True,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "BTR_TYPE_WEIGHT_IS_NOT_CENSUS_DWELLING_IDENTITY",
        "WITHIN_GROUP_TYPE_SHARE_IS_NOT_RAW_BTR_TOTAL_AS_CANONICAL_DENOMINATOR",
        "OFFICIAL_MODEL_WEIGHTED_CALIBRATION_IS_NOT_OBSERVED_HOUSEHOLD_FAIL_RATE",
        "NATIONAL_TYPE_MIX_IS_NOT_LOCAL_WBL_POINT_TYPE_ASSIGNMENT",
        "TYPE_11_15_16_23_RESIDUAL_IS_NOT_WHOLE_STOCK_MULTIGLAZED_UW_BLOCKER",
    )
