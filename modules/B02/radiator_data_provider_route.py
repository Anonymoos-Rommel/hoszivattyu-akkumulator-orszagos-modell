"""B02-P46 national radiator-stock data-provider route gate.

P46 proves that a concrete current Hungary-specific data package exists that
explicitly contains a residential radiator-park surface and hydronic-radiator
market analysis. It does not pretend that paywalled numeric cells have already
been inspected or admitted to the five national P42 programme claims.

DATA-PACKAGE SCOPE MATCH != ACQUIRED NUMERIC EVIDENCE != P42 AUTHORITY.
"""

from __future__ import annotations

from dataclasses import dataclass


REQUIRED_P42_CLAIMS = (
    "RADIATOR_STOCK_DWELLING_COUNT",
    "RADIATOR_STOCK_UNIT_COUNT",
    "RADIATOR_TYPE_SIZE_DISTRIBUTION",
    "RADIATOR_REUSE_UPGRADE_REQUIREMENT",
    "RADIATOR_REPLACEMENT_QUANTITY",
)


@dataclass(frozen=True)
class RadiatorDataProviderCandidate:
    route_id: str
    provider: str
    report_ref: str
    country: str
    publication_date: str
    authority_url: str
    exact_locator: str
    current_report: bool
    national_scope: bool
    residential_radiator_park: bool
    hydronic_radiator_scope: bool
    end_use_segmentation: bool
    product_type_segmentation: bool
    direct_acquisition_route: bool
    public_numeric_stock_cells: bool
    installed_stock_type_distribution_verified: bool
    reuse_upgrade_classification_verified: bool
    replacement_quantity_verified: bool
    reproducible_binding: bool


@dataclass(frozen=True)
class RadiatorDataProviderDecision:
    route_status: str
    reasons: tuple[str, ...]
    p42_national_authority: bool
    unresolved_p42_claims: tuple[str, ...]


def assess_radiator_data_provider_route(
    candidate: RadiatorDataProviderCandidate,
) -> RadiatorDataProviderDecision:
    """Qualify a source-acquisition route without promoting uninspected cells."""

    reasons: list[str] = []
    if not candidate.route_id.strip():
        reasons.append("NO_ROUTE_ID")
    if not candidate.provider.strip():
        reasons.append("NO_PROVIDER")
    if not candidate.report_ref.strip():
        reasons.append("NO_REPORT_REF")
    if candidate.country != "HU":
        reasons.append("NOT_HUNGARY")
    if not candidate.publication_date.strip():
        reasons.append("NO_PUBLICATION_DATE")
    if not candidate.authority_url.strip():
        reasons.append("NO_AUTHORITY_URL")
    if not candidate.exact_locator.strip():
        reasons.append("NO_EXACT_LOCATOR")
    if not candidate.current_report:
        reasons.append("REPORT_NOT_CURRENT")
    if not candidate.national_scope:
        reasons.append("NO_NATIONAL_SCOPE")
    if not candidate.residential_radiator_park:
        reasons.append("NO_RESIDENTIAL_RADIATOR_PARK")
    if not candidate.hydronic_radiator_scope:
        reasons.append("NO_HYDRONIC_RADIATOR_SCOPE")
    if not candidate.direct_acquisition_route:
        reasons.append("NO_DIRECT_ACQUISITION_ROUTE")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    route_status = "QUALIFIED_PROVIDER_ROUTE" if not reasons else "Q"

    # The public catalogue/TOC can prove the route and report scope, but P42
    # authority requires the underlying numeric stock evidence to be acquired,
    # inspected and claim-specifically admitted. Reuse/upgrade and replacement
    # quantities additionally require the P42 engineering semantics, not market
    # sales labels.
    p42_authority = bool(
        route_status == "QUALIFIED_PROVIDER_ROUTE"
        and candidate.public_numeric_stock_cells
        and candidate.installed_stock_type_distribution_verified
        and candidate.reuse_upgrade_classification_verified
        and candidate.replacement_quantity_verified
    )

    unresolved = () if p42_authority else REQUIRED_P42_CLAIMS
    return RadiatorDataProviderDecision(
        route_status=route_status,
        reasons=tuple(reasons),
        p42_national_authority=p42_authority,
        unresolved_p42_claims=unresolved,
    )
