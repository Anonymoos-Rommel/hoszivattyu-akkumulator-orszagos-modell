"""B02-P80 KEOP23 baseline U-value matrix and action-conditioned post-state gate.

Source basis:
- Csoknyai 2022 Table 8.3: survey-derived component U-value statistics for
  the 23 Hungarian synthetic building types.
- Csoknyai 2022 Table 9.1: source-native reference-retrofit component
  requirement values.
- Section 9.2.4.2 explicitly evaluates air-to-water heat-pump cases both with
  the original envelope and with the cost-optimal reference retrofit.

Critical boundaries:

TABLE 8.3 HISTORICAL BASELINE != 2026 CURRENT STOCK OBSERVATION
KEOP23 TYPE MEAN != HOUSEHOLD U-VALUE
SOURCE ZERO / N-A != PHYSICAL ZERO
REFERENCE RETROFIT U-MAX != REALIZED U-VALUE POINT
HEAT-PUMP-ONLY ACTION != ENVELOPE RETROFIT
ACTION-CONDITIONED MODEL STATE != NATIONAL ACTION ASSIGNMENT
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from modules.B02.keop23_wbl_crosswalk import candidates_for


ROOT = Path(__file__).resolve().parents[2]
UVALUE_PATH = ROOT / "data" / "processed" / "b02" / "keop23_baseline_uvalue_matrix.csv"

EXPECTED_TYPES = 23
SOURCE_ID = "SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022"

REFERENCE_ENVELOPE_RETROFIT = "REFERENCE_ENVELOPE_RETROFIT"
REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP = "REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP"
AIR_TO_WATER_HP_ONLY = "AIR_TO_WATER_HP_ONLY"

COMPONENTS = (
    "EXTERNAL_WALL",
    "ATTIC_FLOOR",
    "FLAT_ROOF",
    "PITCHED_ROOF",
    "BASEMENT_CEILING",
    "WINDOW",
)

REFERENCE_RETROFIT_U_MAX = {
    "EXTERNAL_WALL": 0.24,
    "FLAT_ROOF": 0.17,
    "ATTIC_FLOOR": 0.17,
    "BASEMENT_CEILING": 0.26,
    "WINDOW": 1.15,
}

COMPONENT_FIELDS = {
    "EXTERNAL_WALL": {
        "occurrence": None,
        "renovated_share": "external_wall_insulated_share",
        "baseline": "external_wall_u_uninsulated",
        "historical_renovated": "external_wall_u_insulated",
    },
    "ATTIC_FLOOR": {
        "occurrence": "attic_floor_occurrence_share",
        "renovated_share": "attic_floor_insulated_share",
        "baseline": "attic_floor_u_uninsulated",
        "historical_renovated": "attic_floor_u_insulated",
    },
    "FLAT_ROOF": {
        "occurrence": "flat_roof_occurrence_share",
        "renovated_share": "flat_roof_insulated_share",
        "baseline": "flat_roof_u_uninsulated",
        "historical_renovated": "flat_roof_u_insulated",
    },
    "PITCHED_ROOF": {
        "occurrence": "pitched_roof_occurrence_share",
        "renovated_share": "pitched_roof_insulated_share",
        "baseline": "pitched_roof_u_uninsulated",
        "historical_renovated": "pitched_roof_u_insulated",
    },
    "BASEMENT_CEILING": {
        "occurrence": "basement_ceiling_occurrence_share",
        "renovated_share": "basement_ceiling_insulated_share",
        "baseline": "basement_ceiling_u_uninsulated",
        "historical_renovated": "basement_ceiling_u_insulated",
    },
    "WINDOW": {
        "occurrence": None,
        "renovated_share": "window_replaced_share",
        "baseline": "window_u_not_replaced",
        "historical_renovated": None,
    },
}


@dataclass(frozen=True)
class UValueTypeRow:
    type_id: int
    values: dict[str, float | None]
    source_id: str


@dataclass(frozen=True)
class CandidateUValueEnvelope:
    component: str
    state: str
    lower_u_w_m2k: float | None
    upper_u_w_m2k: float | None
    candidate_type_count: int
    valid_type_count: int
    invalid_or_missing_type_ids: tuple[int, ...]
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PostStateUValueConstraint:
    component: str
    action: str
    lower_u_w_m2k: float | None
    upper_u_w_m2k: float | None
    status: str
    evidence_status: str
    blockers: tuple[str, ...]


def _maybe_float(value: str) -> float | None:
    return None if value == "" else float(value)


@lru_cache(maxsize=1)
def load_uvalue_rows() -> dict[int, UValueTypeRow]:
    with UVALUE_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_TYPES:
        raise ValueError(f"expected {EXPECTED_TYPES} Table-8.3 type rows, got {len(rows)}")

    result: dict[int, UValueTypeRow] = {}
    for row in rows:
        type_id = int(row["type_id"])
        if type_id in result:
            raise ValueError(f"duplicate U-value type {type_id}")
        if row["source_id"] != SOURCE_ID:
            raise ValueError(f"unexpected U-value source for type {type_id}")

        values: dict[str, float | None] = {}
        for key, value in row.items():
            if key in {"type_id", "source_id"}:
                continue
            values[key] = _maybe_float(value)

        for key, value in values.items():
            if value is not None and ("share" in key) and not 0.0 <= value <= 1.0:
                raise ValueError(f"share outside [0,1]: type={type_id} field={key}")

        result[type_id] = UValueTypeRow(
            type_id=type_id,
            values=values,
            source_id=row["source_id"],
        )

    if set(result) != set(range(1, 24)):
        raise ValueError("Table-8.3 type IDs must be exactly 1..23")
    return result


def _physical_u(row: UValueTypeRow, field: str | None) -> float | None:
    if field is None:
        return None
    value = row.values[field]
    # Preserve source-native zero in the CSV, but do not promote it to a
    # physical heat-transfer coefficient.
    if value is None or value <= 0.0:
        return None
    return value


def candidate_baseline_uvalue_envelope(
    wbl_period_code: str,
    building_group: str,
    component: str,
    state: str = "BASELINE_UNRENOVATED",
) -> CandidateUValueEnvelope:
    if component not in COMPONENT_FIELDS:
        raise ValueError(f"unsupported component {component}")

    fields = COMPONENT_FIELDS[component]
    if state == "BASELINE_UNRENOVATED":
        field = fields["baseline"]
    elif state == "HISTORICAL_RENOVATED":
        field = fields["historical_renovated"]
        if field is None:
            return CandidateUValueEnvelope(
                component=component,
                state=state,
                lower_u_w_m2k=None,
                upper_u_w_m2k=None,
                candidate_type_count=len(candidates_for(wbl_period_code, building_group).candidate_type_ids),
                valid_type_count=0,
                invalid_or_missing_type_ids=candidates_for(wbl_period_code, building_group).candidate_type_ids,
                status="Q",
                blockers=("SOURCE_HAS_NO_HISTORICAL_RENOVATED_U_VALUE_FOR_COMPONENT",),
            )
    else:
        raise ValueError(f"unsupported baseline state {state}")

    rule = candidates_for(wbl_period_code, building_group)
    source = load_uvalue_rows()
    valid: list[float] = []
    invalid: list[int] = []
    for type_id in rule.candidate_type_ids:
        value = _physical_u(source[type_id], field)
        if value is None:
            invalid.append(type_id)
        else:
            valid.append(value)

    if not valid:
        return CandidateUValueEnvelope(
            component=component,
            state=state,
            lower_u_w_m2k=None,
            upper_u_w_m2k=None,
            candidate_type_count=len(rule.candidate_type_ids),
            valid_type_count=0,
            invalid_or_missing_type_ids=tuple(invalid),
            status="Q",
            blockers=("NO_VALID_SOURCE_U_VALUE_IN_CANDIDATE_SET",),
        )

    blockers: list[str] = []
    status = "QUALIFIED_SET_VALUED_BASELINE_CALIBRATION"
    if invalid:
        status = "PARTIAL_SET_VALUED_BASELINE_CALIBRATION"
        blockers.append("CANDIDATE_SET_HAS_MISSING_OR_NONPHYSICAL_SOURCE_U_VALUES")

    return CandidateUValueEnvelope(
        component=component,
        state=state,
        lower_u_w_m2k=min(valid),
        upper_u_w_m2k=max(valid),
        candidate_type_count=len(rule.candidate_type_ids),
        valid_type_count=len(valid),
        invalid_or_missing_type_ids=tuple(invalid),
        status=status,
        blockers=tuple(blockers),
    )


def reference_retrofit_constraint(
    component: str,
    *,
    action: str = REFERENCE_ENVELOPE_RETROFIT,
) -> PostStateUValueConstraint:
    if action not in {
        REFERENCE_ENVELOPE_RETROFIT,
        REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    }:
        raise ValueError(f"unsupported reference retrofit action {action}")

    if component == "PITCHED_ROOF":
        return PostStateUValueConstraint(
            component=component,
            action=action,
            lower_u_w_m2k=None,
            upper_u_w_m2k=None,
            status="Q",
            evidence_status="Q",
            blockers=("TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW",),
        )

    if component not in REFERENCE_RETROFIT_U_MAX:
        raise ValueError(f"unsupported component {component}")

    return PostStateUValueConstraint(
        component=component,
        action=action,
        lower_u_w_m2k=None,
        upper_u_w_m2k=REFERENCE_RETROFIT_U_MAX[component],
        status="QUALIFIED_SOURCE_NATIVE_REFERENCE_RETROFIT_UPPER_BOUND",
        evidence_status="DER",
        blockers=(),
    )


def assess_post_state_uvalue(
    *,
    action: str,
    component: str,
) -> PostStateUValueConstraint:
    if action in {
        REFERENCE_ENVELOPE_RETROFIT,
        REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    }:
        return reference_retrofit_constraint(component, action=action)

    if action == AIR_TO_WATER_HP_ONLY:
        return PostStateUValueConstraint(
            component=component,
            action=action,
            lower_u_w_m2k=None,
            upper_u_w_m2k=None,
            status="Q",
            evidence_status="Q",
            blockers=(
                "HEAT_PUMP_ONLY_PRESERVES_ENVELOPE_BUT_CURRENT_2026_BASELINE_U_SURFACE_IS_NOT_MATERIALIZED",
            ),
        )

    return PostStateUValueConstraint(
        component=component,
        action=action,
        lower_u_w_m2k=None,
        upper_u_w_m2k=None,
        status="Q",
        evidence_status="Q",
        blockers=("ACTION_TO_COMPONENT_POST_STATE_U_MAPPING_REQUIRED",),
    )


def assess_national_post_state_u_surface(
    *,
    national_action_assignment_materialized: bool,
    current_no_action_baseline_materialized: bool,
    component_area_surface_materialized: bool,
) -> tuple[str, tuple[str, ...]]:
    blockers: list[str] = []
    if not national_action_assignment_materialized:
        blockers.append("NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED")
    if not current_no_action_baseline_materialized:
        blockers.append("CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED")
    if not component_area_surface_materialized:
        blockers.append("COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED")

    if blockers:
        return "Q", tuple(blockers)
    return "QUALIFIED_ACTION_CONDITIONED_POST_STATE_U_SURFACE", ()
