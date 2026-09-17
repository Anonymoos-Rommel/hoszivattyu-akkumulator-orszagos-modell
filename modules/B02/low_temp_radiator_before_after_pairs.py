"""B02-P54 bounded residential before/after radiator-pair contract.

P54 materializes an official Westminster City Council / AECOM residential
engineering report in which the same apartment-room grain carries an existing
radiator schedule and a proposed lower-temperature radiator schedule.

The evidence is a design precedent, not an implementation record, not a heat-pump
project, and not a Hungarian or national stock authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class LowTempRadiatorPairError(ValueError):
    """Raised when P54 pair evidence is malformed or overstated."""


OFFICIAL_ENGINEERING_REPORT = "OFFICIAL_ENGINEERING_REPORT"
DISTRICT_HEATING_RETROFIT_DESIGN = "DISTRICT_HEATING_RETROFIT_DESIGN"
QUALIFIED_BOUNDED_BEFORE_AFTER_PAIR = "QUALIFIED_BOUNDED_BEFORE_AFTER_PAIR"


@dataclass(frozen=True)
class RadiatorBeforeAfterPair:
    evidence_id: str
    dwelling_id: str
    room: str
    residential_scope: bool
    source_role: str
    heating_context: str
    source_url: str
    source_locator: str
    source_date: str

    existing_type: str
    existing_size: str
    existing_flow_c: float
    existing_return_c: float
    existing_mean_c: float
    existing_sample_model: str
    existing_sample_size: str
    existing_estimated_capacity_kw: float
    existing_sample_model_exact_identity_claimed: bool = False

    proposed_model: str = ""
    proposed_size: str = ""
    proposed_count: int = 0
    proposed_mean_c: float = 0.0
    proposed_flow_c: float = 0.0
    proposed_return_c: float = 0.0
    proposed_required_capacity_kw: float = 0.0
    proposed_estimated_capacity_source_token: str = ""
    proposed_estimated_capacity_kw: float | None = None
    proposed_capacity_source_unit_anomaly: bool = False

    implemented_claimed: bool = False
    heat_pump_claimed: bool = False
    hungarian_stock_authority_claimed: bool = False
    national_p42_authority_claimed: bool = False
    programme_use_claimed: bool = False


@dataclass(frozen=True)
class RadiatorPairSummary:
    dwelling_count: int
    room_pair_count: int
    existing_radiator_positions: int
    proposed_radiator_units: int
    clean_numeric_proposed_capacity_rows: int
    source_unit_anomaly_rows: int
    existing_flow_return: tuple[float, float]
    proposed_flow_return: tuple[float, float]
    existing_mean_c: float
    proposed_mean_c: float
    mean_water_temperature_drop_c: float
    implementation_authority: bool = False
    heat_pump_authority: bool = False
    hungarian_stock_authority: bool = False
    national_p42_authority: bool = False
    programme_use_allowed: bool = False


def _assert_mean(flow_c: float, return_c: float, mean_c: float, label: str) -> None:
    if flow_c <= return_c:
        raise LowTempRadiatorPairError(f"{label}_FLOW_NOT_ABOVE_RETURN")
    calculated = (flow_c + return_c) / 2.0
    if abs(calculated - mean_c) > 1e-9:
        raise LowTempRadiatorPairError(f"{label}_MEAN_TEMPERATURE_MISMATCH")


def validate_radiator_before_after_pair(row: RadiatorBeforeAfterPair) -> str:
    """Validate one room-grain existing -> proposed radiator pair."""

    if not row.evidence_id.strip() or not row.dwelling_id.strip() or not row.room.strip():
        raise LowTempRadiatorPairError("MISSING_PAIR_IDENTITY")
    if not row.residential_scope:
        raise LowTempRadiatorPairError("NON_RESIDENTIAL_PAIR_FORBIDDEN")
    if row.source_role != OFFICIAL_ENGINEERING_REPORT:
        raise LowTempRadiatorPairError("UNSUPPORTED_SOURCE_ROLE")
    if row.heating_context != DISTRICT_HEATING_RETROFIT_DESIGN:
        raise LowTempRadiatorPairError("HEATING_CONTEXT_MISMATCH")
    if not row.source_url.startswith("https://"):
        raise LowTempRadiatorPairError("SOURCE_URL_NOT_HTTPS")
    if not row.source_locator.strip() or not row.source_date.strip():
        raise LowTempRadiatorPairError("MISSING_SOURCE_LOCATOR_OR_DATE")

    for value, label in (
        (row.existing_type, "EXISTING_TYPE"),
        (row.existing_size, "EXISTING_SIZE"),
        (row.existing_sample_model, "EXISTING_SAMPLE_MODEL"),
        (row.existing_sample_size, "EXISTING_SAMPLE_SIZE"),
        (row.proposed_model, "PROPOSED_MODEL"),
        (row.proposed_size, "PROPOSED_SIZE"),
        (row.proposed_estimated_capacity_source_token, "PROPOSED_CAPACITY_TOKEN"),
    ):
        if not value.strip():
            raise LowTempRadiatorPairError(f"MISSING_{label}")

    if row.existing_estimated_capacity_kw <= 0 or row.proposed_required_capacity_kw <= 0:
        raise LowTempRadiatorPairError("NON_POSITIVE_CAPACITY")
    if row.proposed_count <= 0:
        raise LowTempRadiatorPairError("NON_POSITIVE_PROPOSED_COUNT")

    _assert_mean(
        row.existing_flow_c,
        row.existing_return_c,
        row.existing_mean_c,
        "EXISTING",
    )
    _assert_mean(
        row.proposed_flow_c,
        row.proposed_return_c,
        row.proposed_mean_c,
        "PROPOSED",
    )
    if row.proposed_mean_c >= row.existing_mean_c:
        raise LowTempRadiatorPairError("PROPOSED_MEAN_NOT_LOWER_THAN_EXISTING")

    if abs(row.proposed_required_capacity_kw - row.existing_estimated_capacity_kw) > 1e-9:
        raise LowTempRadiatorPairError("PAIR_REQUIRED_CAPACITY_DOES_NOT_BIND_EXISTING_ESTIMATE")

    if row.proposed_capacity_source_unit_anomaly:
        if row.proposed_estimated_capacity_kw is not None:
            raise LowTempRadiatorPairError("SOURCE_UNIT_ANOMALY_MUST_NOT_BE_SILENTLY_NORMALIZED")
    else:
        if row.proposed_estimated_capacity_kw is None or row.proposed_estimated_capacity_kw <= 0:
            raise LowTempRadiatorPairError("MISSING_CLEAN_PROPOSED_CAPACITY")

    if row.existing_sample_model_exact_identity_claimed:
        raise LowTempRadiatorPairError("SAMPLE_MODEL_IS_NOT_EXACT_EXISTING_SKU_IDENTITY")
    if row.implemented_claimed:
        raise LowTempRadiatorPairError("DESIGN_SCHEDULE_IS_NOT_IMPLEMENTATION_EVIDENCE")
    if row.heat_pump_claimed:
        raise LowTempRadiatorPairError("DISTRICT_HEATING_DESIGN_IS_NOT_HEAT_PUMP_EVIDENCE")
    if row.hungarian_stock_authority_claimed:
        raise LowTempRadiatorPairError("UK_PROJECT_IS_NOT_HUNGARIAN_STOCK_AUTHORITY")
    if row.national_p42_authority_claimed:
        raise LowTempRadiatorPairError("BOUNDED_PAIR_TABLE_IS_NOT_NATIONAL_P42_AUTHORITY")
    if row.programme_use_claimed:
        raise LowTempRadiatorPairError("BOUNDED_PAIR_TABLE_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE")

    return QUALIFIED_BOUNDED_BEFORE_AFTER_PAIR


def summarize_radiator_before_after_pairs(
    rows: Iterable[RadiatorBeforeAfterPair],
) -> RadiatorPairSummary:
    """Summarize the bounded pair table without population promotion."""

    materialized = list(rows)
    if not materialized:
        raise LowTempRadiatorPairError("EMPTY_PAIR_SET")

    for row in materialized:
        validate_radiator_before_after_pair(row)

    evidence_ids = [row.evidence_id for row in materialized]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise LowTempRadiatorPairError("DUPLICATE_EVIDENCE_ROW")

    room_keys = [(row.dwelling_id, row.room) for row in materialized]
    if len(room_keys) != len(set(room_keys)):
        raise LowTempRadiatorPairError("DUPLICATE_DWELLING_ROOM_PAIR")

    existing_temp_sets = {
        (row.existing_flow_c, row.existing_return_c, row.existing_mean_c)
        for row in materialized
    }
    proposed_temp_sets = {
        (row.proposed_flow_c, row.proposed_return_c, row.proposed_mean_c)
        for row in materialized
    }
    if len(existing_temp_sets) != 1 or len(proposed_temp_sets) != 1:
        raise LowTempRadiatorPairError("MIXED_TEMPERATURE_BASIS")

    existing_flow, existing_return, existing_mean = next(iter(existing_temp_sets))
    proposed_flow, proposed_return, proposed_mean = next(iter(proposed_temp_sets))

    clean_numeric = sum(
        1 for row in materialized if row.proposed_estimated_capacity_kw is not None
    )
    anomaly_rows = sum(
        1 for row in materialized if row.proposed_capacity_source_unit_anomaly
    )

    return RadiatorPairSummary(
        dwelling_count=len({row.dwelling_id for row in materialized}),
        room_pair_count=len(materialized),
        existing_radiator_positions=len(materialized),
        proposed_radiator_units=sum(row.proposed_count for row in materialized),
        clean_numeric_proposed_capacity_rows=clean_numeric,
        source_unit_anomaly_rows=anomaly_rows,
        existing_flow_return=(existing_flow, existing_return),
        proposed_flow_return=(proposed_flow, proposed_return),
        existing_mean_c=existing_mean,
        proposed_mean_c=proposed_mean,
        mean_water_temperature_drop_c=existing_mean - proposed_mean,
    )


def pair_table_grants_implementation_authority(_: RadiatorPairSummary) -> bool:
    return False


def pair_table_grants_heat_pump_authority(_: RadiatorPairSummary) -> bool:
    return False


def pair_table_grants_hungarian_stock_authority(_: RadiatorPairSummary) -> bool:
    return False


def pair_table_grants_national_p42_authority(_: RadiatorPairSummary) -> bool:
    return False
