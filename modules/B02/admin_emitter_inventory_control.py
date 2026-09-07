"""B02-P47 administrative emitter-inventory and market-flow unit controls.

P47 distinguishes a real current administrative per-emitter record surface from
public aggregate stock authority. It also prevents a market-flow quantity whose
authoritative trade unit is kilograms from being interpreted as a physical
radiator piece count.

ADMIN RECORD SCHEMA != PUBLIC AGGREGATE != NATIONAL P42 STOCK AUTHORITY.
"""

from __future__ import annotations

from dataclasses import dataclass


P42_CLAIMS = (
    "RADIATOR_STOCK_DWELLING_COUNT",
    "RADIATOR_STOCK_UNIT_COUNT",
    "RADIATOR_TYPE_SIZE_DISTRIBUTION",
    "RADIATOR_REUSE_UPGRADE_REQUIREMENT",
    "RADIATOR_REPLACEMENT_QUANTITY",
)


@dataclass(frozen=True)
class AdminEmitterInventoryCandidate:
    surface_id: str
    programme: str
    country: str
    authority_url: str
    exact_locator: str
    current_surface: bool
    dwelling_level_binding: bool
    cost_allocator_route: bool
    apartment_heat_meter_route: bool
    emitter_count_field: bool
    installed_device_type_field: bool
    realised_count_field: bool
    radiator_valve_type_count_field: bool
    heat_emitter_count_auditable: bool
    public_aggregate_emitter_count: bool
    national_stock_complete: bool
    reproducible_binding: bool


@dataclass(frozen=True)
class AdminEmitterInventoryDecision:
    surface_status: str
    reasons: tuple[str, ...]
    per_emitter_inventory_surface: bool
    public_numeric_execution: bool
    p42_national_authority: bool
    unresolved_p42_claims: tuple[str, ...]


def assess_admin_emitter_inventory(
    candidate: AdminEmitterInventoryCandidate,
) -> AdminEmitterInventoryDecision:
    """Qualify a per-emitter administrative surface without stock promotion."""

    reasons: list[str] = []
    if not candidate.surface_id.strip():
        reasons.append("NO_SURFACE_ID")
    if not candidate.programme.strip():
        reasons.append("NO_PROGRAMME")
    if candidate.country != "HU":
        reasons.append("NOT_HUNGARY")
    if not candidate.authority_url.strip():
        reasons.append("NO_AUTHORITY_URL")
    if not candidate.exact_locator.strip():
        reasons.append("NO_EXACT_LOCATOR")
    if not candidate.current_surface:
        reasons.append("SURFACE_NOT_CURRENT")
    if not candidate.dwelling_level_binding:
        reasons.append("NO_DWELLING_LEVEL_BINDING")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    # A cost allocator is installed on a heat emitter. An apartment heat meter
    # can instead measure the apartment independently and therefore cannot be
    # treated as proof of one record per radiator.
    per_emitter = bool(
        candidate.cost_allocator_route
        and not candidate.apartment_heat_meter_route
        and candidate.emitter_count_field
        and candidate.installed_device_type_field
        and candidate.realised_count_field
        and candidate.heat_emitter_count_auditable
    )
    if not per_emitter:
        reasons.append("NO_PROVEN_PER_EMITTER_RECORD_SURFACE")

    surface_status = "QUALIFIED_ADMIN_EMITTER_INVENTORY" if not reasons else "Q"
    public_numeric_execution = bool(
        surface_status == "QUALIFIED_ADMIN_EMITTER_INVENTORY"
        and candidate.public_aggregate_emitter_count
    )

    # Even a public project aggregate would cover only the admitted programme
    # population and would not by itself establish national type/size, reuse or
    # replacement requirements. P42 therefore cannot self-authorize here.
    p42_authority = False
    return AdminEmitterInventoryDecision(
        surface_status=surface_status,
        reasons=tuple(reasons),
        per_emitter_inventory_surface=per_emitter,
        public_numeric_execution=public_numeric_execution,
        p42_national_authority=p42_authority,
        unresolved_p42_claims=P42_CLAIMS,
    )


@dataclass(frozen=True)
class MarketFlowUnitCandidate:
    control_id: str
    source_label: str
    reported_quantity: float
    reported_quantity_label: str
    hs_code: str
    authoritative_quantity_unit: str
    authoritative_unit_url: str
    physical_piece_mapping_proven: bool
    reproducible_binding: bool


@dataclass(frozen=True)
class MarketFlowUnitDecision:
    status: str
    reasons: tuple[str, ...]
    physical_radiator_piece_count_authority: bool


def assess_market_flow_unit(candidate: MarketFlowUnitCandidate) -> MarketFlowUnitDecision:
    """Prevent market-flow mass quantities from becoming physical piece counts."""

    reasons: list[str] = []
    if not candidate.control_id.strip():
        reasons.append("NO_CONTROL_ID")
    if not candidate.source_label.strip():
        reasons.append("NO_SOURCE_LABEL")
    if candidate.reported_quantity < 0:
        reasons.append("NEGATIVE_REPORTED_QUANTITY")
    if not candidate.reported_quantity_label.strip():
        reasons.append("NO_REPORTED_QUANTITY_LABEL")
    if not candidate.hs_code.strip():
        reasons.append("NO_HS_CODE")
    if not candidate.authoritative_quantity_unit.strip():
        reasons.append("NO_AUTHORITATIVE_QUANTITY_UNIT")
    if not candidate.authoritative_unit_url.strip():
        reasons.append("NO_AUTHORITATIVE_UNIT_URL")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    piece_authority = bool(
        not reasons
        and candidate.authoritative_quantity_unit == "PIECE"
        and candidate.physical_piece_mapping_proven
    )
    if candidate.reported_quantity_label.upper() in {"UNIT", "UNITS"} and not piece_authority:
        reasons.append("GENERIC_UNIT_LABEL_NOT_PIECE_AUTHORITY")
    if candidate.authoritative_quantity_unit == "KG":
        reasons.append("AUTHORITATIVE_TRADE_UNIT_IS_KG")

    status = "QUALIFIED_FLOW_UNIT_CONTROL" if candidate.reproducible_binding else "Q"
    return MarketFlowUnitDecision(
        status=status,
        reasons=tuple(reasons),
        physical_radiator_piece_count_authority=piece_authority,
    )
