"""B02-P79 set-valued crosswalk from P21/WBL to the public KEOP23 archetypes.

The public Csoknyai 23-type matrix is strong enough to provide a national
archetype *model basis*, but WBL and KEOP23 do not share identical categories.

P79 therefore refuses a point type assignment.  It maps each canonical WBL
construction-period x P21 building-group state to the complete set of KEOP23
types whose source-native construction periods overlap.

The geometry table is a synthetic-average calibration surface.  Min/max values
over candidate type means are model-set envelopes, not observed household
bounds and not within-type statistical intervals.

Critical boundaries:

FULL TYPE-SOURCE COVERAGE != POINT TYPE IDENTIFICATION
KEOP23 SYNTHETIC TYPE MEAN != HOUSEHOLD OBSERVATION
CANDIDATE-TYPE MIN/MAX != WITHIN-TYPE POPULATION CONFIDENCE INTERVAL
WBL DWELLING FLOOR AREA != KEOP BUILDING USEFUL FLOOR AREA
WBL WALL CODE != KEOP WALL TECHNOLOGY WITHOUT AN ADMITTED CODE CROSSWALK
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage


ROOT = Path(__file__).resolve().parents[2]
TYPE_PATH = ROOT / "data" / "processed" / "b02" / "keop23_synthetic_geometry.csv"
RULE_PATH = ROOT / "registry" / "b02_p79_wbl_keop23_crosswalk.csv"

EXPECTED_TYPE_COUNT = 23
EXPECTED_RULE_COUNT = 14
EXPECTED_WBL_ROWS = 116_452
EXPECTED_OCCUPIED = 4_008_541

WBL_PERIOD_INTERVALS: dict[str, tuple[int | None, int | None]] = {
    "Y_LT1919": (None, 1918),
    "Y1919-1945": (1919, 1945),
    "Y1946-1960": (1946, 1960),
    "Y1961-1980": (1961, 1980),
    "Y1981-2000": (1981, 2000),
    "Y2001-2010": (2001, 2010),
    "Y_GE2011": (2011, None),
}
GROUPS = ("FAMILY_HOUSE", "MULTI_DWELLING")
SCENARIOS = ("CENTRAL", "FLAT")


@dataclass(frozen=True)
class KeopType:
    type_id: int
    building_group: str
    dwelling_count_model: int
    construction_start_year: int | None
    construction_end_year: int | None
    size_class: str
    wall_technology: str
    occupants_per_dwelling: float
    storeys: int
    ceiling_height_m: float
    bbox_x_m: float
    bbox_y_m: float
    total_floor_area_m2: float
    heated_floor_area_m2: float
    heated_floor_area_per_dwelling_m2: float
    max_usable_roof_area_m2: float


@dataclass(frozen=True)
class CrosswalkRule:
    wbl_period_code: str
    building_group: str
    candidate_type_ids: tuple[int, ...]
    heated_floor_area_per_dwelling_min_m2: float
    heated_floor_area_per_dwelling_max_m2: float


@dataclass(frozen=True)
class CrosswalkSummary:
    wbl_row_count: int
    occupied_dwellings: int
    rule_count: int
    type_count: int
    all_period_group_states_covered: bool
    minimum_candidate_count: int
    maximum_candidate_count: int
    point_identified_period_group_states: int
    central_family_expected: float
    central_multi_expected: float
    flat_family_expected: float
    flat_multi_expected: float
    central_candidate_set_covered_expected: float
    flat_candidate_set_covered_expected: float
    central_geometry_calibration_mean_lower_m2_per_dwelling: float
    central_geometry_calibration_mean_upper_m2_per_dwelling: float
    flat_geometry_calibration_mean_lower_m2_per_dwelling: float
    flat_geometry_calibration_mean_upper_m2_per_dwelling: float


def _int_or_none(value: str) -> int | None:
    return None if value == "" else int(value)


@lru_cache(maxsize=1)
def load_types() -> dict[int, KeopType]:
    with TYPE_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_TYPE_COUNT:
        raise ValueError(f"expected {EXPECTED_TYPE_COUNT} KEOP types, got {len(rows)}")
    result: dict[int, KeopType] = {}
    for row in rows:
        type_id = int(row["type_id"])
        if type_id in result:
            raise ValueError(f"duplicate KEOP type {type_id}")
        result[type_id] = KeopType(
            type_id=type_id,
            building_group=row["building_group"],
            dwelling_count_model=int(row["dwelling_count_model"]),
            construction_start_year=_int_or_none(row["construction_start_year"]),
            construction_end_year=_int_or_none(row["construction_end_year"]),
            size_class=row["size_class"],
            wall_technology=row["wall_technology"],
            occupants_per_dwelling=float(row["occupants_per_dwelling"]),
            storeys=int(row["storeys"]),
            ceiling_height_m=float(row["ceiling_height_m"]),
            bbox_x_m=float(row["bbox_x_m"]),
            bbox_y_m=float(row["bbox_y_m"]),
            total_floor_area_m2=float(row["total_floor_area_m2"]),
            heated_floor_area_m2=float(row["heated_floor_area_m2"]),
            heated_floor_area_per_dwelling_m2=float(
                row["heated_floor_area_per_dwelling_m2"]
            ),
            max_usable_roof_area_m2=float(row["max_usable_roof_area_m2"]),
        )
    if set(result) != set(range(1, 24)):
        raise ValueError("KEOP type IDs must be exactly 1..23")
    return result


def _intervals_overlap(
    a: tuple[int | None, int | None],
    b: tuple[int | None, int | None],
) -> bool:
    a0, a1 = a
    b0, b1 = b
    low = max(x for x in (a0, b0) if x is not None) if a0 is not None or b0 is not None else None
    highs = [x for x in (a1, b1) if x is not None]
    high = min(highs) if highs else None
    if low is None or high is None:
        return True
    return low <= high


@lru_cache(maxsize=1)
def load_rules() -> dict[tuple[str, str], CrosswalkRule]:
    types = load_types()
    with RULE_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_RULE_COUNT:
        raise ValueError(f"expected {EXPECTED_RULE_COUNT} rules, got {len(rows)}")

    rules: dict[tuple[str, str], CrosswalkRule] = {}
    for row in rows:
        key = (row["wbl_period_code"], row["building_group"])
        if key in rules:
            raise ValueError(f"duplicate crosswalk rule {key}")
        candidate_ids = tuple(int(x) for x in row["candidate_type_ids"].split(";"))
        if int(row["candidate_count"]) != len(candidate_ids):
            raise ValueError(f"candidate_count drift for {key}")
        if not candidate_ids:
            raise ValueError(f"empty candidate set for {key}")
        if key[0] not in WBL_PERIOD_INTERVALS or key[1] not in GROUPS:
            raise ValueError(f"unsupported rule key {key}")

        for type_id in candidate_ids:
            item = types[type_id]
            if item.building_group != key[1]:
                raise ValueError(f"group mismatch: {key} -> type {type_id}")
            type_interval = (
                item.construction_start_year,
                item.construction_end_year,
            )
            if not _intervals_overlap(WBL_PERIOD_INTERVALS[key[0]], type_interval):
                raise ValueError(f"non-overlapping period mapping: {key} -> type {type_id}")

        all_overlapping = tuple(
            type_id
            for type_id, item in sorted(types.items())
            if item.building_group == key[1]
            and _intervals_overlap(
                WBL_PERIOD_INTERVALS[key[0]],
                (item.construction_start_year, item.construction_end_year),
            )
        )
        if candidate_ids != all_overlapping:
            raise ValueError(
                f"candidate set is not the complete period-overlap set for {key}: "
                f"declared={candidate_ids} expected={all_overlapping}"
            )

        areas = [types[type_id].heated_floor_area_per_dwelling_m2 for type_id in candidate_ids]
        lower = min(areas)
        upper = max(areas)
        if abs(lower - float(row["heated_floor_area_per_dwelling_min_m2"])) > 1e-9:
            raise ValueError(f"lower geometry envelope drift for {key}")
        if abs(upper - float(row["heated_floor_area_per_dwelling_max_m2"])) > 1e-9:
            raise ValueError(f"upper geometry envelope drift for {key}")

        rules[key] = CrosswalkRule(
            wbl_period_code=key[0],
            building_group=key[1],
            candidate_type_ids=candidate_ids,
            heated_floor_area_per_dwelling_min_m2=lower,
            heated_floor_area_per_dwelling_max_m2=upper,
        )

    expected_keys = {
        (period, group)
        for period in WBL_PERIOD_INTERVALS
        for group in GROUPS
    }
    if set(rules) != expected_keys:
        raise ValueError("crosswalk does not cover every WBL period x building group")
    return rules


def candidates_for(wbl_period_code: str, building_group: str) -> CrosswalkRule:
    try:
        return load_rules()[(wbl_period_code, building_group)]
    except KeyError as exc:
        raise ValueError(
            f"unsupported WBL period/building group: {wbl_period_code}/{building_group}"
        ) from exc


def _family_probability(row: dict[str, object], scenario: str) -> float:
    if scenario == "CENTRAL":
        return float(row["central_family_probability"])
    if scenario == "FLAT":
        return float(row["flat_family_probability"])
    raise ValueError(f"unsupported scenario {scenario}")


@lru_cache(maxsize=1)
def build_crosswalk_summary() -> CrosswalkSummary:
    rules = load_rules()
    linkage_rows, linkage_summary = build_calibrated_linkage()

    if len(linkage_rows) != EXPECTED_WBL_ROWS:
        raise ValueError("P21/WBL row-count drift")
    if int(linkage_summary.occupied_dwellings) != EXPECTED_OCCUPIED:
        raise ValueError("P21/WBL occupied control drift")

    family_expected = {scenario: 0.0 for scenario in SCENARIOS}
    multi_expected = {scenario: 0.0 for scenario in SCENARIOS}
    covered_expected = {scenario: 0.0 for scenario in SCENARIOS}
    geometry_lower_weighted = {scenario: 0.0 for scenario in SCENARIOS}
    geometry_upper_weighted = {scenario: 0.0 for scenario in SCENARIOS}

    for row in linkage_rows:
        period = str(row["construction_period_code"])
        count = int(row["dwelling_count"])
        family_rule = rules[(period, "FAMILY_HOUSE")]
        multi_rule = rules[(period, "MULTI_DWELLING")]

        for scenario in SCENARIOS:
            p_family = _family_probability(row, scenario)
            if not 0.0 <= p_family <= 1.0:
                raise ValueError("P21 family probability outside [0,1]")
            family_weight = count * p_family
            multi_weight = count * (1.0 - p_family)
            family_expected[scenario] += family_weight
            multi_expected[scenario] += multi_weight
            covered_expected[scenario] += family_weight + multi_weight
            geometry_lower_weighted[scenario] += (
                family_weight * family_rule.heated_floor_area_per_dwelling_min_m2
                + multi_weight * multi_rule.heated_floor_area_per_dwelling_min_m2
            )
            geometry_upper_weighted[scenario] += (
                family_weight * family_rule.heated_floor_area_per_dwelling_max_m2
                + multi_weight * multi_rule.heated_floor_area_per_dwelling_max_m2
            )

    candidate_counts = [len(rule.candidate_type_ids) for rule in rules.values()]
    return CrosswalkSummary(
        wbl_row_count=len(linkage_rows),
        occupied_dwellings=EXPECTED_OCCUPIED,
        rule_count=len(rules),
        type_count=len(load_types()),
        all_period_group_states_covered=True,
        minimum_candidate_count=min(candidate_counts),
        maximum_candidate_count=max(candidate_counts),
        point_identified_period_group_states=sum(count == 1 for count in candidate_counts),
        central_family_expected=family_expected["CENTRAL"],
        central_multi_expected=multi_expected["CENTRAL"],
        flat_family_expected=family_expected["FLAT"],
        flat_multi_expected=multi_expected["FLAT"],
        central_candidate_set_covered_expected=covered_expected["CENTRAL"],
        flat_candidate_set_covered_expected=covered_expected["FLAT"],
        central_geometry_calibration_mean_lower_m2_per_dwelling=(
            geometry_lower_weighted["CENTRAL"] / EXPECTED_OCCUPIED
        ),
        central_geometry_calibration_mean_upper_m2_per_dwelling=(
            geometry_upper_weighted["CENTRAL"] / EXPECTED_OCCUPIED
        ),
        flat_geometry_calibration_mean_lower_m2_per_dwelling=(
            geometry_lower_weighted["FLAT"] / EXPECTED_OCCUPIED
        ),
        flat_geometry_calibration_mean_upper_m2_per_dwelling=(
            geometry_upper_weighted["FLAT"] / EXPECTED_OCCUPIED
        ),
    )


def assess_geometry_use(requested_use: str) -> tuple[str, tuple[str, ...]]:
    if requested_use == "ARCHETYPE_CALIBRATION_SET":
        return "QUALIFIED_SET_VALUED_CALIBRATION", ()
    if requested_use == "NATIONAL_POINT_TYPE_ASSIGNMENT":
        return "Q", (
            "WITHIN_SET_KEOP23_TYPE_ASSIGNMENT_NOT_IDENTIFIED",
        )
    if requested_use == "HOUSEHOLD_HEATED_AREA_BOUND":
        return "Q", (
            "SYNTHETIC_TYPE_MEAN_IS_NOT_HOUSEHOLD_BOUND",
            "WITHIN_TYPE_GEOMETRY_DISTRIBUTION_REQUIRED",
        )
    if requested_use == "B06_COMPONENT_AREA_INPUT":
        return "Q", (
            "COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED",
        )
    return "Q", ("UNSUPPORTED_GEOMETRY_USE",)


def as_log_dict() -> dict[str, object]:
    x = build_crosswalk_summary()
    return x.__dict__
