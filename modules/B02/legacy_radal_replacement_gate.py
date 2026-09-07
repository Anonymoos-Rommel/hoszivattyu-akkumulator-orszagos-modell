"""B02-P51 legacy RADAL characterization and replacement-comparison gate.

This module makes legacy RADAL evidence and current replacement-product
performance machine-readable without turning historical heating surface,
non-residential reference rows, or manufacturer interchangeability claims into
current national radiator stock or automatic product selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional


P42_CLAIMS = (
    "RADIATOR_STOCK_DWELLING_COUNT",
    "RADIATOR_STOCK_UNIT_COUNT",
    "RADIATOR_TYPE_SIZE_DISTRIBUTION",
    "RADIATOR_REUSE_UPGRADE_REQUIREMENT",
    "RADIATOR_REPLACEMENT_QUANTITY",
)

ALLOWED_OUTPUT_BASES = {
    "SOURCE_NOMINAL_UNSPECIFIED_TEMP",
    "78_62_20",
    "55_45_20",
}


@dataclass(frozen=True)
class HistoricalInstalledSurfaceReference:
    anchor_id: str
    radiator_family: str
    heating_surface_m2: float
    magnitude_precision: str
    geography: str
    historical_installation: bool
    source_url: str
    exact_locator: str
    reproducible_binding: bool


@dataclass(frozen=True)
class HistoricalInstalledSurfaceDecision:
    status: str
    reasons: tuple[str, ...]
    heating_surface_m2: Optional[float]
    physical_piece_count: None
    current_stock_authority: bool
    p42_national_authority: bool


@dataclass(frozen=True)
class LegacyRadiatorReference:
    anchor_id: str
    radiator_family: str
    connection_distance_mm: int
    section_count: int
    length_mm: int
    nominal_output_w: float
    output_basis: str
    observed_unit_count: int
    residential_scope: bool
    source_url: str
    exact_locator: str
    reproducible_binding: bool


@dataclass(frozen=True)
class LegacyRadiatorDecision:
    status: str
    reasons: tuple[str, ...]
    technical_reference_qualified: bool
    residential_stock_weight_allowed: bool
    p42_national_authority: bool


@dataclass(frozen=True)
class ReplacementProductReference:
    product_id: str
    product_family: str
    material: str
    connection_distance_mm: int
    element_count: int
    length_mm: int
    output_w_78_62_20: float
    output_w_55_45_20: float
    manufacturer_family_interchangeable_with_radal: bool
    source_url: str
    exact_locator: str
    reproducible_binding: bool


@dataclass(frozen=True)
class ReplacementProductDecision:
    status: str
    reasons: tuple[str, ...]
    catalog_reference_qualified: bool
    exact_replacement_selection_authorized: bool
    p42_national_authority: bool


@dataclass(frozen=True)
class ReplacementComparisonDecision:
    status: str
    reasons: tuple[str, ...]
    connection_distance_match: bool
    output_comparison_qualified: bool
    legacy_output_w: Optional[float]
    replacement_output_w: Optional[float]
    output_delta_w: Optional[float]
    manufacturer_family_interchangeability_only: bool
    exact_replacement_selection_authorized: bool


def _positive_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and isfinite(value)
        and value > 0
    )


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def assess_historical_installed_surface(
    reference: HistoricalInstalledSurfaceReference,
) -> HistoricalInstalledSurfaceDecision:
    reasons: list[str] = []
    if not reference.anchor_id.strip():
        reasons.append("NO_ANCHOR_ID")
    if not reference.radiator_family.strip():
        reasons.append("NO_RADIATOR_FAMILY")
    if not _positive_number(reference.heating_surface_m2):
        reasons.append("INVALID_HEATING_SURFACE")
    if reference.magnitude_precision not in {"APPROXIMATE", "EXACT"}:
        reasons.append("INVALID_MAGNITUDE_PRECISION")
    if reference.geography != "HU":
        reasons.append("WRONG_GEOGRAPHY")
    if not reference.historical_installation:
        reasons.append("NOT_HISTORICAL_INSTALLATION")
    if not reference.source_url.strip():
        reasons.append("NO_SOURCE_URL")
    if not reference.exact_locator.strip():
        reasons.append("NO_EXACT_LOCATOR")
    if not reference.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    qualified = not reasons
    return HistoricalInstalledSurfaceDecision(
        status="QUALIFIED_HISTORICAL_SURFACE_MAGNITUDE" if qualified else "Q",
        reasons=tuple(reasons),
        heating_surface_m2=float(reference.heating_surface_m2) if qualified else None,
        physical_piece_count=None,
        current_stock_authority=False,
        p42_national_authority=False,
    )


def assess_legacy_radiator(reference: LegacyRadiatorReference) -> LegacyRadiatorDecision:
    reasons: list[str] = []
    if not reference.anchor_id.strip():
        reasons.append("NO_ANCHOR_ID")
    if not reference.radiator_family.strip():
        reasons.append("NO_RADIATOR_FAMILY")
    if not _positive_int(reference.connection_distance_mm):
        reasons.append("INVALID_CONNECTION_DISTANCE")
    if not _positive_int(reference.section_count):
        reasons.append("INVALID_SECTION_COUNT")
    if not _positive_int(reference.length_mm):
        reasons.append("INVALID_LENGTH")
    if not _positive_number(reference.nominal_output_w):
        reasons.append("INVALID_NOMINAL_OUTPUT")
    if reference.output_basis not in ALLOWED_OUTPUT_BASES:
        reasons.append("INVALID_OUTPUT_BASIS")
    if not _positive_int(reference.observed_unit_count):
        reasons.append("INVALID_OBSERVED_UNIT_COUNT")
    if not reference.source_url.strip():
        reasons.append("NO_SOURCE_URL")
    if not reference.exact_locator.strip():
        reasons.append("NO_EXACT_LOCATOR")
    if not reference.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    qualified = not reasons
    return LegacyRadiatorDecision(
        status="QUALIFIED_LEGACY_TECHNICAL_REFERENCE" if qualified else "Q",
        reasons=tuple(reasons),
        technical_reference_qualified=qualified,
        residential_stock_weight_allowed=qualified and reference.residential_scope,
        p42_national_authority=False,
    )


def assess_replacement_product(
    reference: ReplacementProductReference,
) -> ReplacementProductDecision:
    reasons: list[str] = []
    if not reference.product_id.strip():
        reasons.append("NO_PRODUCT_ID")
    if not reference.product_family.strip():
        reasons.append("NO_PRODUCT_FAMILY")
    if not reference.material.strip():
        reasons.append("NO_MATERIAL")
    if not _positive_int(reference.connection_distance_mm):
        reasons.append("INVALID_CONNECTION_DISTANCE")
    if not _positive_int(reference.element_count):
        reasons.append("INVALID_ELEMENT_COUNT")
    if not _positive_int(reference.length_mm):
        reasons.append("INVALID_LENGTH")
    if not _positive_number(reference.output_w_78_62_20):
        reasons.append("INVALID_78_62_20_OUTPUT")
    if not _positive_number(reference.output_w_55_45_20):
        reasons.append("INVALID_55_45_20_OUTPUT")
    if reference.output_w_55_45_20 >= reference.output_w_78_62_20:
        reasons.append("LOW_TEMP_OUTPUT_NOT_LOWER")
    if not reference.source_url.strip():
        reasons.append("NO_SOURCE_URL")
    if not reference.exact_locator.strip():
        reasons.append("NO_EXACT_LOCATOR")
    if not reference.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    qualified = not reasons
    return ReplacementProductDecision(
        status="QUALIFIED_REPLACEMENT_PRODUCT_REFERENCE" if qualified else "Q",
        reasons=tuple(reasons),
        catalog_reference_qualified=qualified,
        exact_replacement_selection_authorized=False,
        p42_national_authority=False,
    )


def compare_legacy_to_replacement(
    legacy: LegacyRadiatorReference,
    replacement: ReplacementProductReference,
    comparison_basis: str,
) -> ReplacementComparisonDecision:
    """Compare outputs only when old and new values share the exact basis.

    Family-level manufacturer interchangeability remains a mounting/geometry
    signal only. It cannot select a replacement SKU or bypass hydraulics, room
    heat loss, or B06 product/CAPEX authority.
    """

    legacy_decision = assess_legacy_radiator(legacy)
    replacement_decision = assess_replacement_product(replacement)
    reasons: list[str] = []

    if comparison_basis not in {"78_62_20", "55_45_20"}:
        reasons.append("UNSUPPORTED_COMPARISON_BASIS")
    if legacy_decision.status == "Q":
        reasons.append("UNQUALIFIED_LEGACY_REFERENCE")
    if replacement_decision.status == "Q":
        reasons.append("UNQUALIFIED_REPLACEMENT_REFERENCE")

    connection_match = (
        legacy.connection_distance_mm == replacement.connection_distance_mm
    )
    if not connection_match:
        reasons.append("CONNECTION_DISTANCE_MISMATCH")

    basis_match = legacy.output_basis == comparison_basis
    if comparison_basis in {"78_62_20", "55_45_20"} and not basis_match:
        reasons.append("LEGACY_OUTPUT_BASIS_NOT_COMPARABLE")

    output_comparison_qualified = (
        not reasons
        and connection_match
        and basis_match
        and legacy_decision.technical_reference_qualified
        and replacement_decision.catalog_reference_qualified
    )

    replacement_output: Optional[float] = None
    if output_comparison_qualified:
        replacement_output = (
            replacement.output_w_78_62_20
            if comparison_basis == "78_62_20"
            else replacement.output_w_55_45_20
        )

    legacy_output = legacy.nominal_output_w if output_comparison_qualified else None
    delta = (
        float(replacement_output) - float(legacy_output)
        if output_comparison_qualified and replacement_output is not None and legacy_output is not None
        else None
    )

    return ReplacementComparisonDecision(
        status=(
            "QUALIFIED_OUTPUT_COMPARISON_ONLY"
            if output_comparison_qualified
            else "Q"
        ),
        reasons=tuple(reasons),
        connection_distance_match=connection_match,
        output_comparison_qualified=output_comparison_qualified,
        legacy_output_w=legacy_output,
        replacement_output_w=replacement_output,
        output_delta_w=delta,
        manufacturer_family_interchangeability_only=(
            replacement.manufacturer_family_interchangeable_with_radal
        ),
        exact_replacement_selection_authorized=False,
    )


def forbid_surface_to_piece_conversion(_: float) -> None:
    """Freeze the non-equivalence required by P42/P51."""
    raise ValueError("HEATING_SURFACE_M2_TO_PHYSICAL_RADIATOR_PIECES_FORBIDDEN")
