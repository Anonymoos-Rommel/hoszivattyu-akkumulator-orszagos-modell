"""B02-P102 historical-renovated U-quality calibration.

P101 established a bounded current-baseline envelope deficit floor from 2022
TARKI-REKK type-level current state plus P80 baseline U calibration.

P102 asks a narrower question: can P80's already-admitted historical renovated
U statistics tighten the current calibrated deficit floor without pretending
that historical synthetic type means are current household observations?

The Csoknyai source explicitly separates renovated and unrenovated component
U-values by type, but also warns that renovated averages must be treated with
caution where renovated sample counts are low and omits values where occurrence
is very low or zero. P102 preserves that limitation.

Binding current-state tightening is limited to EXTERNAL_WALL because:
- TARKI-REKK 2022 exposes a source-native type-level "insulated facade" share;
- P80 exposes a matching renovated external-wall mean U for 19/23 types;
- all 19 valid renovated external-wall means exceed the P100 0.24 W/m2K
  reference target.

P102 does not bind the single current "insulated attic" metric to P80's
ATTIC_FLOOR/FLAT_ROOF/PITCHED_ROOF split, and it cannot bind replaced windows
to a renovated U value because P80 contains no replaced-window U statistic.

This remains calibrated model inference:

HISTORICAL RENOVATED TYPE MEAN U != CURRENT RENOVATED HOUSEHOLD U
RENOVATED TYPE MEAN ABOVE TARGET != ALL RENOVATED HOUSEHOLDS FAIL TARGET
CALIBRATED TYPE-BRANCH DEFICIT != OBSERVED HOUSEHOLD FAIL SHARE
CURRENT INSULATED ATTIC != IDENTIFIED P80 TOP-ENVELOPE COMPONENT
WINDOW REPLACED SHARE != REPLACED WINDOW U
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage
from modules.B02.current_baseline_u_inference import (
    EXPECTED_OCCUPIED,
    type_current_state,
)
from modules.B02.keop23_uvalue_poststate import (
    COMPONENT_FIELDS,
    COMPONENTS,
    load_uvalue_rows,
)
from modules.B02.keop23_wbl_crosswalk import (
    SCENARIOS,
    WBL_PERIOD_INTERVALS,
    candidates_for,
)
from modules.B02.programme_envelope_action_selection_crosswalk import (
    REFERENCE_COMPONENT_U_MAX,
)


P102_STATUS = "QUALIFIED_HISTORICAL_RENOVATED_U_QUALITY_CALIBRATION"
STRATUM_STATUS = "QUALIFIED_SET_VALUED_RENOVATED_U_QUALITY_CALIBRATION"

NEXT_RESIDUALS = (
    "CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED",
    "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED",
)
PRIMARY_NEXT_RESIDUAL = NEXT_RESIDUALS[0]

DIRECT_CURRENT_BINDABLE_COMPONENT = "EXTERNAL_WALL"


@dataclass(frozen=True)
class HistoricalRenovatedComponentAudit:
    component: str
    reference_u_max_w_m2k: float
    valid_type_count: int
    deficit_mean_type_count: int
    compliant_or_equal_mean_type_count: int
    missing_or_nonphysical_type_count: int
    deficit_mean_type_ids: tuple[int, ...]
    compliant_or_equal_mean_type_ids: tuple[int, ...]
    missing_or_nonphysical_type_ids: tuple[int, ...]
    status: str
    current_2022_binding_status: str
    residual: str | None


@dataclass(frozen=True)
class TypeRenovatedWallQuality:
    type_id: int
    current_facade_insulated_share: float
    historical_renovated_wall_u_w_m2k: float | None
    historical_renovated_wall_state: str
    calibrated_wall_deficit_share: float
    current_window_not_replaced_deficit_share: float
    combined_calibrated_deficit_floor_share: float
    combined_calibrated_deficit_upper_share: float
    status: str
    evidence_status: str
    residuals: tuple[str, ...]


@dataclass(frozen=True)
class StratumRenovatedWallQuality:
    wbl_period_code: str
    building_group: str
    candidate_type_ids: tuple[int, ...]
    calibrated_deficit_floor_lower_share: float
    calibrated_deficit_floor_upper_share: float
    calibrated_deficit_union_upper_lower_share: float
    calibrated_deficit_union_upper_upper_share: float
    status: str
    evidence_status: str
    residuals: tuple[str, ...]


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
    residuals: tuple[str, ...]


def _physical(value: float | None) -> float | None:
    if value is None or value <= 0.0:
        return None
    return float(value)


@lru_cache(maxsize=1)
def historical_renovated_component_audits() -> tuple[HistoricalRenovatedComponentAudit, ...]:
    source = load_uvalue_rows()
    output: list[HistoricalRenovatedComponentAudit] = []

    for component in COMPONENTS:
        target = REFERENCE_COMPONENT_U_MAX[component]
        field = COMPONENT_FIELDS[component]["historical_renovated"]

        deficit: list[int] = []
        compliant: list[int] = []
        missing: list[int] = []

        for type_id in range(1, 24):
            value = None if field is None else _physical(source[type_id].values[field])
            if value is None:
                missing.append(type_id)
            elif value > target:
                deficit.append(type_id)
            else:
                compliant.append(type_id)

        if component == "EXTERNAL_WALL":
            binding = "DIRECT_CURRENT_2022_FACADE_SHARE_BINDING_ADMITTED"
            residual = (
                "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"
                if missing else None
            )
        elif component == "WINDOW":
            binding = "NO_HISTORICAL_REPLACED_WINDOW_U_VALUE"
            residual = "CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED"
        else:
            binding = "NO_DIRECT_CURRENT_COMPONENT_SEMANTIC_BINDING_IN_P102"
            residual = "CURRENT_TOP_OR_BOTTOM_ENVELOPE_COMPONENT_MAPPING_REQUIRED"

        output.append(
            HistoricalRenovatedComponentAudit(
                component=component,
                reference_u_max_w_m2k=target,
                valid_type_count=len(deficit) + len(compliant),
                deficit_mean_type_count=len(deficit),
                compliant_or_equal_mean_type_count=len(compliant),
                missing_or_nonphysical_type_count=len(missing),
                deficit_mean_type_ids=tuple(deficit),
                compliant_or_equal_mean_type_ids=tuple(compliant),
                missing_or_nonphysical_type_ids=tuple(missing),
                status=(
                    "NO_HISTORICAL_RENOVATED_U_VALUE"
                    if not deficit and not compliant
                    else "QUALIFIED_HISTORICAL_RENOVATED_TYPE_MEAN_AUDIT"
                ),
                current_2022_binding_status=binding,
                residual=residual,
            )
        )

    return tuple(output)


@lru_cache(maxsize=None)
def type_renovated_wall_quality(type_id: int) -> TypeRenovatedWallQuality:
    if type_id not in range(1, 24):
        raise ValueError(f"unsupported type_id {type_id}")

    current = type_current_state(type_id)
    source = load_uvalue_rows()[type_id]
    value = _physical(source.values["external_wall_u_insulated"])
    target = REFERENCE_COMPONENT_U_MAX["EXTERNAL_WALL"]

    if value is None:
        renovated_state = "HISTORICAL_RENOVATED_WALL_U_MISSING"
        # Only the current uninsulated branch remains calibrated deficient.
        wall_deficit_share = 1.0 - current.facade_insulated_share
        residuals = (
            "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED",
            "CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED",
        )
    elif value > target:
        renovated_state = "HISTORICAL_RENOVATED_TYPE_MEAN_ABOVE_REFERENCE"
        # Synthetic-type calibration: both current wall-state branches are
        # calibrated deficient at the type-mean model layer. This is NOT a
        # household failure statement.
        wall_deficit_share = 1.0
        residuals = ("CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED",)
    else:
        renovated_state = "HISTORICAL_RENOVATED_TYPE_MEAN_AT_OR_BELOW_REFERENCE"
        wall_deficit_share = 1.0 - current.facade_insulated_share
        residuals = ("CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED",)

    window_deficit_share = current.window_baseline_deficit_share
    lower = max(wall_deficit_share, window_deficit_share)
    upper = min(1.0, wall_deficit_share + window_deficit_share)

    return TypeRenovatedWallQuality(
        type_id=type_id,
        current_facade_insulated_share=current.facade_insulated_share,
        historical_renovated_wall_u_w_m2k=value,
        historical_renovated_wall_state=renovated_state,
        calibrated_wall_deficit_share=wall_deficit_share,
        current_window_not_replaced_deficit_share=window_deficit_share,
        combined_calibrated_deficit_floor_share=lower,
        combined_calibrated_deficit_upper_share=upper,
        status="QUALIFIED_TYPE_MEAN_RENOVATED_WALL_CALIBRATION",
        evidence_status="OBS/DER/ASS",
        residuals=residuals,
    )


@lru_cache(maxsize=None)
def stratum_renovated_wall_quality(
    wbl_period_code: str,
    building_group: str,
) -> StratumRenovatedWallQuality:
    rule = candidates_for(wbl_period_code, building_group)
    states = [type_renovated_wall_quality(i) for i in rule.candidate_type_ids]

    lower = [x.combined_calibrated_deficit_floor_share for x in states]
    upper = [x.combined_calibrated_deficit_upper_share for x in states]
    residuals = tuple(sorted({r for x in states for r in x.residuals}))

    return StratumRenovatedWallQuality(
        wbl_period_code=wbl_period_code,
        building_group=building_group,
        candidate_type_ids=rule.candidate_type_ids,
        calibrated_deficit_floor_lower_share=min(lower),
        calibrated_deficit_floor_upper_share=max(lower),
        calibrated_deficit_union_upper_lower_share=min(upper),
        calibrated_deficit_union_upper_upper_share=max(upper),
        status=STRATUM_STATUS,
        evidence_status="OBS/DER/ASS",
        residuals=residuals,
    )


@lru_cache(maxsize=1)
def all_stratum_renovated_wall_quality() -> tuple[StratumRenovatedWallQuality, ...]:
    return tuple(
        stratum_renovated_wall_quality(period, group)
        for period in WBL_PERIOD_INTERVALS
        for group in ("FAMILY_HOUSE", "MULTI_DWELLING")
    )


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
        (x.wbl_period_code, x.building_group): x
        for x in all_stratum_renovated_wall_quality()
    }
    output: list[ScenarioPopulationBounds] = []

    for scenario in SCENARIOS:
        lo_dw = 0.0
        hi_dw = 0.0
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

            lo_dw += (
                family_weight * family.calibrated_deficit_floor_lower_share
                + multi_weight * multi.calibrated_deficit_floor_lower_share
            )
            hi_dw += (
                family_weight * family.calibrated_deficit_floor_upper_share
                + multi_weight * multi.calibrated_deficit_floor_upper_share
            )
            occupied += count

        if abs(occupied - EXPECTED_OCCUPIED) > 1e-6:
            raise ValueError("national occupied weight drift")

        lo = lo_dw / occupied
        hi = hi_dw / occupied
        output.append(
            ScenarioPopulationBounds(
                scenario=scenario,
                occupied_dwellings=occupied,
                calibrated_retrofit_floor_lower_dwellings=lo_dw,
                calibrated_retrofit_floor_upper_dwellings=hi_dw,
                calibrated_retrofit_floor_lower_share=lo,
                calibrated_retrofit_floor_upper_share=hi,
                hp_only_share_lower=0.0,
                hp_only_share_upper=1.0 - lo,
                status="QUALIFIED_BOUNDED_RENOVATED_U_QUALITY_CALIBRATION",
                residuals=NEXT_RESIDUALS,
            )
        )

    return tuple(output)


def p102_state() -> dict[str, object]:
    scenarios = national_population_bounds()
    conservative_floor = min(x.calibrated_retrofit_floor_lower_share for x in scenarios)

    return {
        "status": P102_STATUS,
        "historical_component_audits": tuple(
            x.__dict__ for x in historical_renovated_component_audits()
        ),
        "type_count": 23,
        "stratum_count": len(all_stratum_renovated_wall_quality()),
        "occupied_dwellings": EXPECTED_OCCUPIED,
        "scenario_bounds": tuple(x.__dict__ for x in scenarios),
        "structural_calibrated_retrofit_floor_lower_share": conservative_floor,
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": 1.0 - conservative_floor,
        "previous_p101_floor": 0.37781217722501986,
        "incremental_floor_gain": conservative_floor - 0.37781217722501986,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "residuals": NEXT_RESIDUALS,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "HISTORICAL_RENOVATED_TYPE_MEAN_U_IS_NOT_CURRENT_RENOVATED_HOUSEHOLD_U",
        "RENOVATED_TYPE_MEAN_ABOVE_TARGET_IS_NOT_ALL_RENOVATED_HOUSEHOLDS_FAIL",
        "CALIBRATED_TYPE_BRANCH_DEFICIT_IS_NOT_OBSERVED_HOUSEHOLD_FAIL_SHARE",
        "CURRENT_INSULATED_ATTIC_IS_NOT_IDENTIFIED_P80_TOP_ENVELOPE_COMPONENT",
        "WINDOW_REPLACED_SHARE_IS_NOT_REPLACED_WINDOW_U",
    )
