"""B02-P55 bounded residential ASHP radiator before/after pair contract.

P55 materializes the CHO-612 Shiplake Lock Heat Engineer / RetrofitWorks
report published as a UK Contracts Finder attachment. The same dwelling-room
grain carries current radiator dimensions, room heat loss and a proposed ASHP
radiator schedule at a custom mean water temperature.

The evidence is ASHP design authority for this single dwelling only. It is not
commissioning evidence, not Hungarian stock authority and not national P42
population authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class AshpRadiatorPairError(ValueError):
    """Raised when P55 evidence is malformed or promoted beyond its scope."""


UK_GOV_CONTRACTS_FINDER_ATTACHMENT = "UK_GOV_CONTRACTS_FINDER_ATTACHMENT"
ASHP_RETROFIT_DESIGN = "ASHP_RETROFIT_DESIGN"
SOURCE_NATIVE = "SOURCE_NATIVE"
EXACT_DERIVED_FROM_SOURCE_NATIVE_FLOW_AND_MWT = (
    "EXACT_DERIVED_FROM_SOURCE_NATIVE_FLOW_AND_MWT"
)
QUALIFIED_BOUNDED_ASHP_BEFORE_AFTER_PAIR = "QUALIFIED_BOUNDED_ASHP_BEFORE_AFTER_PAIR"


@dataclass(frozen=True)
class AshpRadiatorBeforeAfterPair:
    evidence_id: str
    dwelling_id: str
    room: str
    residential_scope: bool
    source_role: str
    heating_context: str
    source_url: str
    source_locator: str
    source_date: str

    heating_type: str
    design_external_temp_c: float
    building_heat_source_required_kw: float
    heat_pump_output_design_kw: float

    max_designed_flow_c: float
    max_flow_provenance: str
    custom_mwt_c: float
    mwt_provenance: str
    derived_return_c: float
    return_provenance: str
    return_source_native_claimed: bool

    room_heat_loss_w: float
    existing_radiator_type: str
    existing_height_mm: int
    existing_length_mm: int
    proposed_emitters: str
    proposed_count: int
    proposed_output_at_custom_mwt_w: float

    implemented_claimed: bool = False
    commissioned_claimed: bool = False
    hungarian_stock_authority_claimed: bool = False
    national_p42_authority_claimed: bool = False
    programme_use_claimed: bool = False


@dataclass(frozen=True)
class AshpRadiatorPairSummary:
    dwelling_count: int
    room_pair_count: int
    rooms_meeting_or_exceeding_heat_loss: int
    rooms_below_heat_loss: int
    total_room_heat_loss_w: float
    total_proposed_output_at_custom_mwt_w: float
    aggregate_output_margin_w: float
    max_designed_flow_c: float
    custom_mwt_c: float
    exact_derived_return_c: float
    ashp_design_authority: bool = True
    implementation_authority: bool = False
    commissioning_authority: bool = False
    hungarian_stock_authority: bool = False
    national_p42_authority: bool = False
    programme_use_allowed: bool = False


def validate_ashp_radiator_before_after_pair(row: AshpRadiatorBeforeAfterPair) -> str:
    """Validate one bounded current -> proposed ASHP radiator room pair."""

    if not row.evidence_id.strip() or not row.dwelling_id.strip() or not row.room.strip():
        raise AshpRadiatorPairError("MISSING_PAIR_IDENTITY")
    if not row.residential_scope:
        raise AshpRadiatorPairError("NON_RESIDENTIAL_PAIR_FORBIDDEN")
    if row.source_role != UK_GOV_CONTRACTS_FINDER_ATTACHMENT:
        raise AshpRadiatorPairError("UNSUPPORTED_SOURCE_ROLE")
    if row.heating_context != ASHP_RETROFIT_DESIGN:
        raise AshpRadiatorPairError("HEATING_CONTEXT_MISMATCH")
    if not row.source_url.startswith("https://www.contractsfinder.service.gov.uk/"):
        raise AshpRadiatorPairError("SOURCE_NOT_CONTRACTS_FINDER")
    if not row.source_locator.strip() or not row.source_date.strip():
        raise AshpRadiatorPairError("MISSING_SOURCE_LOCATOR_OR_DATE")
    if row.heating_type != "ASHP":
        raise AshpRadiatorPairError("HEATING_TYPE_NOT_ASHP")

    for value, label in (
        (row.existing_radiator_type, "EXISTING_RADIATOR_TYPE"),
        (row.proposed_emitters, "PROPOSED_EMITTERS"),
    ):
        if not value.strip():
            raise AshpRadiatorPairError(f"MISSING_{label}")

    if row.existing_height_mm <= 0 or row.existing_length_mm <= 0:
        raise AshpRadiatorPairError("NON_POSITIVE_EXISTING_DIMENSION")
    if row.proposed_count <= 0:
        raise AshpRadiatorPairError("NON_POSITIVE_PROPOSED_COUNT")
    if row.room_heat_loss_w <= 0 or row.proposed_output_at_custom_mwt_w <= 0:
        raise AshpRadiatorPairError("NON_POSITIVE_HEAT_VALUE")
    if row.building_heat_source_required_kw <= 0 or row.heat_pump_output_design_kw <= 0:
        raise AshpRadiatorPairError("NON_POSITIVE_HEAT_SOURCE_VALUE")

    if row.max_flow_provenance != SOURCE_NATIVE:
        raise AshpRadiatorPairError("FLOW_MUST_REMAIN_SOURCE_NATIVE")
    if row.mwt_provenance != SOURCE_NATIVE:
        raise AshpRadiatorPairError("MWT_MUST_REMAIN_SOURCE_NATIVE")
    if row.return_provenance != EXACT_DERIVED_FROM_SOURCE_NATIVE_FLOW_AND_MWT:
        raise AshpRadiatorPairError("RETURN_PROVENANCE_MISMATCH")
    if row.return_source_native_claimed:
        raise AshpRadiatorPairError("DERIVED_RETURN_MUST_NOT_BE_CLAIMED_SOURCE_NATIVE")

    expected_return = (2.0 * row.custom_mwt_c) - row.max_designed_flow_c
    if abs(expected_return - row.derived_return_c) > 1e-9:
        raise AshpRadiatorPairError("RETURN_DERIVATION_MISMATCH")
    if row.max_designed_flow_c <= row.derived_return_c:
        raise AshpRadiatorPairError("FLOW_NOT_ABOVE_DERIVED_RETURN")
    expected_mwt = (row.max_designed_flow_c + row.derived_return_c) / 2.0
    if abs(expected_mwt - row.custom_mwt_c) > 1e-9:
        raise AshpRadiatorPairError("MWT_IDENTITY_MISMATCH")

    if row.implemented_claimed:
        raise AshpRadiatorPairError("DESIGN_REPORT_IS_NOT_IMPLEMENTATION_EVIDENCE")
    if row.commissioned_claimed:
        raise AshpRadiatorPairError("DESIGN_REPORT_IS_NOT_COMMISSIONING_EVIDENCE")
    if row.hungarian_stock_authority_claimed:
        raise AshpRadiatorPairError("UK_DWELLING_IS_NOT_HUNGARIAN_STOCK_AUTHORITY")
    if row.national_p42_authority_claimed:
        raise AshpRadiatorPairError("BOUNDED_ASHP_PAIR_TABLE_IS_NOT_NATIONAL_P42_AUTHORITY")
    if row.programme_use_claimed:
        raise AshpRadiatorPairError("BOUNDED_ASHP_PAIR_TABLE_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE")

    return QUALIFIED_BOUNDED_ASHP_BEFORE_AFTER_PAIR


def summarize_ashp_radiator_before_after_pairs(
    rows: Iterable[AshpRadiatorBeforeAfterPair],
) -> AshpRadiatorPairSummary:
    """Summarize the bounded P55 pair table without hiding room-level deficits."""

    materialized = list(rows)
    if not materialized:
        raise AshpRadiatorPairError("EMPTY_PAIR_SET")

    for row in materialized:
        validate_ashp_radiator_before_after_pair(row)

    evidence_ids = [row.evidence_id for row in materialized]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise AshpRadiatorPairError("DUPLICATE_EVIDENCE_ROW")

    room_keys = [(row.dwelling_id, row.room) for row in materialized]
    if len(room_keys) != len(set(room_keys)):
        raise AshpRadiatorPairError("DUPLICATE_DWELLING_ROOM_PAIR")

    project_contexts = {
        (
            row.heating_type,
            row.design_external_temp_c,
            row.building_heat_source_required_kw,
            row.heat_pump_output_design_kw,
            row.max_designed_flow_c,
            row.custom_mwt_c,
            row.derived_return_c,
        )
        for row in materialized
    }
    if len(project_contexts) != 1:
        raise AshpRadiatorPairError("MIXED_PROJECT_CONTEXT")

    (
        _,
        _,
        _,
        _,
        max_flow,
        custom_mwt,
        derived_return,
    ) = next(iter(project_contexts))

    total_heat_loss = sum(row.room_heat_loss_w for row in materialized)
    total_proposed_output = sum(
        row.proposed_output_at_custom_mwt_w for row in materialized
    )
    meeting = sum(
        1
        for row in materialized
        if row.proposed_output_at_custom_mwt_w >= row.room_heat_loss_w
    )
    below = len(materialized) - meeting

    return AshpRadiatorPairSummary(
        dwelling_count=len({row.dwelling_id for row in materialized}),
        room_pair_count=len(materialized),
        rooms_meeting_or_exceeding_heat_loss=meeting,
        rooms_below_heat_loss=below,
        total_room_heat_loss_w=total_heat_loss,
        total_proposed_output_at_custom_mwt_w=total_proposed_output,
        aggregate_output_margin_w=total_proposed_output - total_heat_loss,
        max_designed_flow_c=max_flow,
        custom_mwt_c=custom_mwt,
        exact_derived_return_c=derived_return,
    )


def pair_table_grants_ashp_design_authority(_: AshpRadiatorPairSummary) -> bool:
    return True


def pair_table_grants_implementation_authority(_: AshpRadiatorPairSummary) -> bool:
    return False


def pair_table_grants_commissioning_authority(_: AshpRadiatorPairSummary) -> bool:
    return False


def pair_table_grants_hungarian_stock_authority(_: AshpRadiatorPairSummary) -> bool:
    return False


def pair_table_grants_national_p42_authority(_: AshpRadiatorPairSummary) -> bool:
    return False
