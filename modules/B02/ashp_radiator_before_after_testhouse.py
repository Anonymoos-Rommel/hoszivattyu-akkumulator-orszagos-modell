"""B02-P55 bounded residential ASHP radiator before/after contract.

P55 materializes a controlled residential test-house ASHP retrofit documented by
EA Technology / Energy Saving Trust Report No. 6507. The same room grain carries
an original radiator schedule and an upgraded low-temperature radiator schedule.

This is an implemented engineering test-house precedent, not an occupied-household
sample and not Hungarian or national stock authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class AshpRadiatorBeforeAfterError(ValueError):
    """Raised when P55 evidence is malformed or overstated."""


QUALIFIED_BOUNDED_ASHP_PAIR = "QUALIFIED_BOUNDED_ASHP_PAIR"
SOURCE_ROLE = "EST_EA_TECHNOLOGY_CONTROLLED_RESIDENTIAL_TEST_HOUSE"
TARGET_FLOW_C = 45.0
TARGET_RETURN_C = 35.0
WHOLE_HOUSE_DESIGN_HEAT_LOSS_KW = 4.4
HEAT_PUMP_CAPACITY_KW = 6.0
ORIGINAL_TOTAL_OUTPUT_KW = 6.445
UPGRADED_TOTAL_OUTPUT_KW = 6.421
ORIGINAL_AT_45_35_20_TOTAL_OUTPUT_KW = 1.6


@dataclass(frozen=True)
class AshpRadiatorPair:
    evidence_id: str
    room: str
    residential_scope: bool
    implemented_ashp_scope: bool
    source_role: str
    original_type: str
    original_height_mm: int
    original_length_mm: int
    original_output_w: int
    original_output_basis: str
    proposed_type: str
    proposed_height_mm: int
    proposed_length_mm: int
    proposed_output_w: int
    design_room_temp_c: int
    target_flow_c: float
    target_return_c: float
    source_url: str
    source_locator: str
    source_date: str
    occupied_household_claimed: bool = False
    hungarian_stock_authority_claimed: bool = False
    national_p42_authority_claimed: bool = False
    programme_use_claimed: bool = False


@dataclass(frozen=True)
class AshpRadiatorPairSummary:
    rooms: int
    changed_rooms: int
    unchanged_rooms: int
    original_total_output_kw: float
    upgraded_total_output_kw: float
    target_flow_c: float
    target_return_c: float
    whole_house_design_heat_loss_kw: float
    heat_pump_capacity_kw: float
    original_at_target_total_output_kw: float
    implemented_ashp_precedent: bool = True
    occupied_household_authority: bool = False
    hungarian_stock_authority: bool = False
    national_p42_authority: bool = False
    programme_use_allowed: bool = False


def validate_ashp_radiator_pair(row: AshpRadiatorPair) -> str:
    if not row.evidence_id.strip() or not row.room.strip():
        raise AshpRadiatorBeforeAfterError("MISSING_EVIDENCE_ID_OR_ROOM")
    if not row.residential_scope:
        raise AshpRadiatorBeforeAfterError("NON_RESIDENTIAL_ROW_FORBIDDEN")
    if not row.implemented_ashp_scope:
        raise AshpRadiatorBeforeAfterError("IMPLEMENTED_ASHP_SCOPE_REQUIRED")
    if row.source_role != SOURCE_ROLE:
        raise AshpRadiatorBeforeAfterError("SOURCE_ROLE_MISMATCH")
    for value in (
        row.original_height_mm,
        row.original_length_mm,
        row.original_output_w,
        row.proposed_height_mm,
        row.proposed_length_mm,
        row.proposed_output_w,
        row.design_room_temp_c,
    ):
        if value <= 0:
            raise AshpRadiatorBeforeAfterError("NON_POSITIVE_PHYSICAL_OR_OUTPUT_VALUE")
    if row.target_flow_c != TARGET_FLOW_C or row.target_return_c != TARGET_RETURN_C:
        raise AshpRadiatorBeforeAfterError("TARGET_FLOW_RETURN_MUST_BE_EXACT_45_35")
    if not row.original_type.strip() or not row.proposed_type.strip():
        raise AshpRadiatorBeforeAfterError("MISSING_RADIATOR_TYPE")
    if not row.original_output_basis.strip():
        raise AshpRadiatorBeforeAfterError("MISSING_ORIGINAL_OUTPUT_BASIS")
    if not row.source_url.startswith("https://"):
        raise AshpRadiatorBeforeAfterError("SOURCE_URL_NOT_HTTPS")
    if not row.source_locator.strip() or not row.source_date.strip():
        raise AshpRadiatorBeforeAfterError("MISSING_SOURCE_LOCATOR_OR_DATE")

    if row.occupied_household_claimed:
        raise AshpRadiatorBeforeAfterError("CONTROLLED_TEST_HOUSE_IS_NOT_OCCUPIED_HOUSEHOLD_SAMPLE")
    if row.hungarian_stock_authority_claimed:
        raise AshpRadiatorBeforeAfterError("UK_TEST_HOUSE_IS_NOT_HUNGARIAN_STOCK_AUTHORITY")
    if row.national_p42_authority_claimed:
        raise AshpRadiatorBeforeAfterError("BOUNDED_TEST_HOUSE_IS_NOT_NATIONAL_P42_AUTHORITY")
    if row.programme_use_claimed:
        raise AshpRadiatorBeforeAfterError("ENGINEERING_PRECEDENT_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE")

    return QUALIFIED_BOUNDED_ASHP_PAIR


def summarize_ashp_radiator_pairs(rows: Iterable[AshpRadiatorPair]) -> AshpRadiatorPairSummary:
    materialized = list(rows)
    if not materialized:
        raise AshpRadiatorBeforeAfterError("EMPTY_PAIR_SET")
    for row in materialized:
        validate_ashp_radiator_pair(row)
    ids = [row.evidence_id for row in materialized]
    if len(ids) != len(set(ids)):
        raise AshpRadiatorBeforeAfterError("DUPLICATE_EVIDENCE_ROW")
    rooms = [row.room for row in materialized]
    if len(rooms) != len(set(rooms)):
        raise AshpRadiatorBeforeAfterError("DUPLICATE_ROOM_PAIR")
    changed = sum(
        1
        for row in materialized
        if (
            row.original_type != row.proposed_type
            or row.original_height_mm != row.proposed_height_mm
            or row.original_length_mm != row.proposed_length_mm
        )
    )
    return AshpRadiatorPairSummary(
        rooms=len(materialized),
        changed_rooms=changed,
        unchanged_rooms=len(materialized) - changed,
        original_total_output_kw=sum(row.original_output_w for row in materialized) / 1000.0,
        upgraded_total_output_kw=sum(row.proposed_output_w for row in materialized) / 1000.0,
        target_flow_c=TARGET_FLOW_C,
        target_return_c=TARGET_RETURN_C,
        whole_house_design_heat_loss_kw=WHOLE_HOUSE_DESIGN_HEAT_LOSS_KW,
        heat_pump_capacity_kw=HEAT_PUMP_CAPACITY_KW,
        original_at_target_total_output_kw=ORIGINAL_AT_45_35_20_TOTAL_OUTPUT_KW,
    )


def pairs_grant_occupied_household_authority(_: AshpRadiatorPairSummary) -> bool:
    return False


def pairs_grant_hungarian_stock_authority(_: AshpRadiatorPairSummary) -> bool:
    return False


def pairs_grant_national_p42_authority(_: AshpRadiatorPairSummary) -> bool:
    return False
