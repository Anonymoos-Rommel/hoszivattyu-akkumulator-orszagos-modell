"""B02-P43 fail-closed recovery-route contract for radiator programme data.

A recovery route is evidence that a specific data asset/data holder can be
asked for a bounded set of radiator fields.  It is not the radiator stock
claim itself and can never uplift a P42 programme quantity before data are
actually recovered, validated and admitted.
"""

from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
QUALIFIED_ROUTE = "QUALIFIED_ROUTE"

CURRENT_STOCK = "CURRENT_STOCK"
DISTRICT_HEATING_CURRENT_STOCK = "DISTRICT_HEATING_CURRENT_STOCK"
REPLACEMENT_DESIGN = "REPLACEMENT_DESIGN"

ALLOWED_ROLES = frozenset(
    {CURRENT_STOCK, DISTRICT_HEATING_CURRENT_STOCK, REPLACEMENT_DESIGN}
)

REQUIRED_FIELD_FAMILIES = frozenset(
    {
        "EMITTER_IDENTITY",
        "UNIT_QUANTITY",
        "TYPE_CONFIGURATION",
        "DIMENSION_OR_OUTPUT",
        "SCOPE_OR_WEIGHT",
    }
)


@dataclass(frozen=True)
class RadiatorRecoveryRouteCandidate:
    route_id: str
    source_id: str
    role: str
    data_holder: str
    authority_url: str
    exact_locator: str
    availability_basis: str
    requested_field_families: tuple[str, ...]
    current_reference_possible: bool
    anonymised_or_aggregate_request: bool
    personal_data_requested: bool = False
    external_binary_committed: bool = False
    claims_p42_quantity_without_recovered_data: bool = False


@dataclass(frozen=True)
class RadiatorRecoveryRouteDecision:
    status: str
    reasons: tuple[str, ...]


def assess_radiator_recovery_route(
    candidate: RadiatorRecoveryRouteCandidate,
) -> RadiatorRecoveryRouteDecision:
    """Qualify only a bounded, non-promoting, reproducible recovery route."""

    reasons: list[str] = []

    if not candidate.route_id.strip():
        reasons.append("NO_ROUTE_ID")
    if not candidate.source_id.strip():
        reasons.append("NO_SOURCE_ID")
    if candidate.role not in ALLOWED_ROLES:
        reasons.append("UNSUPPORTED_RECOVERY_ROLE")
    if not candidate.data_holder.strip():
        reasons.append("NO_DATA_HOLDER")
    if not candidate.authority_url.startswith("https://"):
        reasons.append("NO_HTTPS_AUTHORITY_URL")
    if not candidate.exact_locator.strip():
        reasons.append("NO_EXACT_SOURCE_LOCATOR")
    if not candidate.availability_basis.strip():
        reasons.append("NO_DATA_AVAILABILITY_BASIS")

    field_families = frozenset(candidate.requested_field_families)
    missing = REQUIRED_FIELD_FAMILIES - field_families
    if missing:
        reasons.extend(f"MISSING_FIELD_FAMILY:{name}" for name in sorted(missing))

    if not candidate.anonymised_or_aggregate_request:
        reasons.append("REQUEST_NOT_DATA_MINIMISED")
    if candidate.personal_data_requested:
        reasons.append("PERSONAL_DATA_REQUESTED")
    if candidate.external_binary_committed:
        reasons.append("EXTERNAL_BINARY_MUST_NOT_BE_COMMITTED")
    if candidate.claims_p42_quantity_without_recovered_data:
        reasons.append("RECOVERY_ROUTE_CANNOT_SELF_AUTHORIZE_P42")

    # Replacement-design data may legitimately be historical/current design
    # reference rather than current-stock observation.  Current-stock routes,
    # however, must at least have a plausible current-reference recovery path.
    if candidate.role in {CURRENT_STOCK, DISTRICT_HEATING_CURRENT_STOCK}:
        if not candidate.current_reference_possible:
            reasons.append("NO_CURRENT_REFERENCE_RECOVERY_PATH")

    if reasons:
        return RadiatorRecoveryRouteDecision(Q, tuple(reasons))
    return RadiatorRecoveryRouteDecision(QUALIFIED_ROUTE, ())
