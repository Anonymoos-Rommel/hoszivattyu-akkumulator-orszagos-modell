"""B02-P101 bounded current-baseline U inference.

P100 made the programme envelope-action selection crosswalk executable, but the
current national component-performance surface remained unresolved.

P101 admits the source-native TARKI-REKK 2022 type-level renovation-state
surface on the same 23-type taxonomy already used by P79/P80. The TARKI final
sample was weighted by KSH region and building type, and the report explicitly
states that type-level weighted averages were used in the residential model.

The current-state categories still do not identify renovated-component U
values. P101 therefore uses only the branches whose physical calibration is
already available without a renovation-quality assumption:

- facade NOT insulated -> P80 historical uninsulated external-wall U calibration;
- window NOT replaced -> P80 historical not-replaced window U calibration.

For all 23 synthetic types those two P80 baseline U means exceed the P100
reference-programme limits (0.24 W/m2K wall, 1.15 W/m2K window).

Because the TARKI-REKK source does not publish overlap between facade
insulation and window replacement, the calibrated baseline-deficit union is
set-valued:
    lower = max(uninsulated facade share, not-replaced window share)
    upper = min(1, sum of those shares)

This is a calibrated synthetic-type population inference, NOT a household fail
rate. Renovated/replaced branches remain unresolved for U quality.

Critical boundaries:

TARKI_TYPE_WEIGHTED_SHARE != HOUSEHOLD_STATE
P80_SYNTHETIC_TYPE_MEAN_U != HOUSEHOLD_U
CALIBRATED_DEFICIT_FLOOR != OBSERVED_HOUSEHOLD_FAIL_SHARE
INSULATED_OR_REPLACED != REFERENCE_U_COMPLIANCE
2022_CURRENT_STATE_CALIBRATION != 2026_POINT_STATE
HP_ONLY_LOWER_BOUND_REMAINS_ZERO_WITHOUT_RENOVATED_U_QUALITY
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage
from modules.B02.fresh_envelope_action_evidence import (
    REKK_SOURCE_ID,
    union_bounds_without_overlap_information,
)
from modules.B02.keop23_uvalue_poststate import load_uvalue_rows
from modules.B02.keop23_wbl_crosswalk import (
    SCENARIOS,
    WBL_PERIOD_INTERVALS,
    candidates_for,
)
from modules.B02.programme_envelope_action_selection_crosswalk import (
    REFERENCE_COMPONENT_U_MAX,
)


ROOT = Path(__file__).resolve().parents[2]
TABLE38_PATH = (
    ROOT / "data" / "processed" / "b02"
    / "p101_rekk_table38_type_state_2022.csv"
)

EXPECTED_TYPES = 23
EXPECTED_STRATA = 14
EXPECTED_OCCUPIED = 4_008_541

P101_STATUS = "QUALIFIED_BOUNDED_CURRENT_BASELINE_U_INFERENCE"
STRATUM_STATUS = "QUALIFIED_SET_VALUED_CURRENT_BASELINE_U_INFERENCE"
NEXT_RESIDUAL = (
    "CURRENT_RENOVATED_ENVELOPE_U_QUALITY_TIGHTENING_REQUIRED_FOR_HP_ONLY_LOWER_BOUND"
)


@dataclass(frozen=True)
class CurrentTypeState:
    type_id: int
    facade_insulated_share: float
    attic_insulated_share: float
    window_replaced_share: float
    wall_uninsulated_u_w_m2k: float
    window_not_replaced_u_w_m2k: float
    wall_baseline_deficit_share: float
    window_baseline_deficit_share: float
    calibrated_deficit_union_lower_share: float
    calibrated_deficit_union_upper_share: float
    unresolved_after_floor_share: float
    status: str
    evidence_status: str


@dataclass(frozen=True)
class StratumCurrentState:
    wbl_period_code: str
    building_group: str
    candidate_type_ids: tuple[int, ...]
    calibrated_deficit_floor_lower_share: float
    calibrated_deficit_floor_upper_share: float
    calibrated_baseline_deficit_union_upper_lower_share: float
    calibrated_baseline_deficit_union_upper_upper_share: float
    status: str
    evidence_status: str
    residual: str


@dataclass(frozen=True)
class ScenarioPopulationBounds:
    scenario: str
    occupied_dwellings: float
    calibrated_retrofit_floor_lower_dwellings: float
    calibrated_retrofit_floor_upper_dwellings: float
    calibrated_retrofit_floor_lower_share: float
    calibrated_retrofit_floor_upper_share: float
    hp_only_share_lower: float
    hp_only_share_upper: float
    status: str
    residual: str


def _share(value: str) -> float:
    out = float(value)
    if not 0.0 <= out <= 1.0:
        raise ValueError("renovation-state share outside [0,1]")
    return out


@lru_cache(maxsize=1)
def load_table38_type_state() -> dict[int, tuple[float, float, float]]:
    with TABLE38_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_TYPES:
        raise ValueError(f"expected {EXPECTED_TYPES} TARKI-REKK type rows, got {len(rows)}")

    result: dict[int, tuple[float, float, float]] = {}
    for row in rows:
        type_id = int(row["type_id"])
        if type_id in result:
            raise ValueError(f"duplicate TARKI-REKK type row {type_id}")
        if row["source_id"] != REKK_SOURCE_ID:
            raise ValueError(f"unexpected source for type {type_id}")
        if row["evidence_status"] != "OBS/DER":
            raise ValueError(f"unexpected evidence status for type {type_id}")
        result[type_id] = (
            _share(row["facade_insulated_share_2022"]),
            _share(row["attic_insulated_share_2022"]),
            _share(row["window_replaced_share_2022"]),
        )

    if set(result) != set(range(1, 24)):
        raise ValueError("TARKI-REKK type IDs must be exactly 1..23")
    return result


@lru_cache(maxsize=None)
def type_current_state(type_id: int) -> CurrentTypeState:
    if type_id not in range(1, 24):
        raise ValueError(f"unsupported type_id {type_id}")

    facade_insulated, attic_insulated, window_replaced = (
        load_table38_type_state()[type_id]
    )
    urow = load_uvalue_rows()[type_id]

    wall_u = urow.values["external_wall_u_uninsulated"]
    window_u = urow.values["window_u_not_replaced"]
    if wall_u is None or wall_u <= 0.0:
        raise ValueError(f"missing/nonphysical wall baseline U for type {type_id}")
    if window_u is None or window_u <= 0.0:
        raise ValueError(f"missing/nonphysical window baseline U for type {type_id}")

    wall_target = REFERENCE_COMPONENT_U_MAX["EXTERNAL_WALL"]
    window_target = REFERENCE_COMPONENT_U_MAX["WINDOW"]

    # These are synthetic-type mean calibration checks, not household proofs.
    if wall_u <= wall_target:
        raise ValueError(
            f"type {type_id} uninsulated wall no longer exceeds reference target"
        )
    if window_u <= window_target:
        raise ValueError(
            f"type {type_id} not-replaced window no longer exceeds reference target"
        )

    wall_deficit = 1.0 - facade_insulated
    window_deficit = 1.0 - window_replaced
    lower, upper = union_bounds_without_overlap_information(
        (wall_deficit, window_deficit)
    )

    return CurrentTypeState(
        type_id=type_id,
        facade_insulated_share=facade_insulated,
        attic_insulated_share=attic_insulated,
        window_replaced_share=window_replaced,
        wall_uninsulated_u_w_m2k=float(wall_u),
        window_not_replaced_u_w_m2k=float(window_u),
        wall_baseline_deficit_share=wall_deficit,
        window_baseline_deficit_share=window_deficit,
        calibrated_deficit_union_lower_share=lower,
        calibrated_deficit_union_upper_share=upper,
        unresolved_after_floor_share=1.0 - lower,
        status="QUALIFIED_TYPE_WEIGHTED_CURRENT_BASELINE_U_CALIBRATION",
        evidence_status="OBS/DER/ASS",
    )


@lru_cache(maxsize=None)
def stratum_current_state(
    wbl_period_code: str,
    building_group: str,
) -> StratumCurrentState:
    rule = candidates_for(wbl_period_code, building_group)
    states = [type_current_state(type_id) for type_id in rule.candidate_type_ids]

    floor_values = [
        state.calibrated_deficit_union_lower_share for state in states
    ]
    union_upper_values = [
        state.calibrated_deficit_union_upper_share for state in states
    ]

    return StratumCurrentState(
        wbl_period_code=wbl_period_code,
        building_group=building_group,
        candidate_type_ids=rule.candidate_type_ids,
        calibrated_deficit_floor_lower_share=min(floor_values),
        calibrated_deficit_floor_upper_share=max(floor_values),
        calibrated_baseline_deficit_union_upper_lower_share=min(
            union_upper_values
        ),
        calibrated_baseline_deficit_union_upper_upper_share=max(
            union_upper_values
        ),
        status=STRATUM_STATUS,
        evidence_status="OBS/DER/ASS",
        residual=NEXT_RESIDUAL,
    )


@lru_cache(maxsize=1)
def all_stratum_current_states() -> tuple[StratumCurrentState, ...]:
    rows = tuple(
        stratum_current_state(period, group)
        for period in WBL_PERIOD_INTERVALS
        for group in ("FAMILY_HOUSE", "MULTI_DWELLING")
    )
    if len(rows) != EXPECTED_STRATA:
        raise ValueError(f"expected {EXPECTED_STRATA} current-state strata")
    return rows


def _family_probability(row: dict[str, object], scenario: str) -> float:
    if scenario == "CENTRAL":
        return float(row["central_family_probability"])
    if scenario == "FLAT":
        return float(row["flat_family_probability"])
    raise ValueError(f"unsupported scenario {scenario}")


@lru_cache(maxsize=1)
def national_population_bounds() -> tuple[ScenarioPopulationBounds, ...]:
    linkage_rows, summary = build_calibrated_linkage()
    if summary.occupied_dwellings != EXPECTED_OCCUPIED:
        raise ValueError("P21 occupied control drift")

    states = {
        (row.wbl_period_code, row.building_group): row
        for row in all_stratum_current_states()
    }
    output: list[ScenarioPopulationBounds] = []

    for scenario in SCENARIOS:
        floor_lower_dwellings = 0.0
        floor_upper_dwellings = 0.0
        occupied = 0.0

        for row in linkage_rows:
            period = str(row["construction_period_code"])
            count = float(row["dwelling_count"])
            p_family = _family_probability(row, scenario)
            if not 0.0 <= p_family <= 1.0:
                raise ValueError("P21 family probability outside [0,1]")

            family_weight = count * p_family
            multi_weight = count * (1.0 - p_family)
            family = states[(period, "FAMILY_HOUSE")]
            multi = states[(period, "MULTI_DWELLING")]

            floor_lower_dwellings += (
                family_weight * family.calibrated_deficit_floor_lower_share
                + multi_weight * multi.calibrated_deficit_floor_lower_share
            )
            floor_upper_dwellings += (
                family_weight * family.calibrated_deficit_floor_upper_share
                + multi_weight * multi.calibrated_deficit_floor_upper_share
            )
            occupied += count

        if abs(occupied - EXPECTED_OCCUPIED) > 1e-6:
            raise ValueError("national occupied weight drift")

        floor_lower_share = floor_lower_dwellings / occupied
        floor_upper_share = floor_upper_dwellings / occupied

        output.append(
            ScenarioPopulationBounds(
                scenario=scenario,
                occupied_dwellings=occupied,
                calibrated_retrofit_floor_lower_dwellings=floor_lower_dwellings,
                calibrated_retrofit_floor_upper_dwellings=floor_upper_dwellings,
                calibrated_retrofit_floor_lower_share=floor_lower_share,
                calibrated_retrofit_floor_upper_share=floor_upper_share,
                hp_only_share_lower=0.0,
                hp_only_share_upper=1.0 - floor_lower_share,
                status="QUALIFIED_BOUNDED_PROGRAMME_ACTION_CALIBRATION",
                residual=NEXT_RESIDUAL,
            )
        )

    return tuple(output)


def p101_state() -> dict[str, object]:
    scenario_rows = national_population_bounds()
    lower_shares = [
        row.calibrated_retrofit_floor_lower_share for row in scenario_rows
    ]
    upper_floor_shares = [
        row.calibrated_retrofit_floor_upper_share for row in scenario_rows
    ]
    conservative_floor = min(lower_shares)

    return {
        "status": P101_STATUS,
        "type_count": len(load_table38_type_state()),
        "stratum_count": len(all_stratum_current_states()),
        "occupied_dwellings": EXPECTED_OCCUPIED,
        "scenario_bounds": tuple(row.__dict__ for row in scenario_rows),
        "structural_calibrated_retrofit_floor_lower_share": conservative_floor,
        "structural_calibrated_retrofit_floor_upper_share": max(
            upper_floor_shares
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": 1.0 - conservative_floor,
        "current_baseline_u_inference_blocker": None,
        "national_point_action_share_identified": False,
        "residual": NEXT_RESIDUAL,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "TARKI_TYPE_WEIGHTED_SHARE_IS_NOT_HOUSEHOLD_STATE",
        "P80_SYNTHETIC_TYPE_MEAN_U_IS_NOT_HOUSEHOLD_U",
        "CALIBRATED_DEFICIT_FLOOR_IS_NOT_OBSERVED_HOUSEHOLD_FAIL_SHARE",
        "INSULATED_OR_REPLACED_IS_NOT_REFERENCE_U_COMPLIANCE",
        "2022_CURRENT_STATE_CALIBRATION_IS_NOT_2026_POINT_STATE",
        "HP_ONLY_LOWER_BOUND_REMAINS_ZERO_WITHOUT_RENOVATED_U_QUALITY",
    )
