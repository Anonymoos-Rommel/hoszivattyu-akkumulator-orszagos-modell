from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
QUALIFIED = "QUALIFIED"
ALLOWED_EVIDENCE = {"OBS", "DER"}
ALLOWED_GRAINS = {
    "SETTLEMENT_TYPE",
    "COUNTY_X_SETTLEMENT_TYPE",
    "DWELLING_RECORD",
}
REQUIRED_UNIVERSE = "OCCUPIED_DWELLING_STOCK"
REQUIRED_TAXONOMY = "FAMILY_HOUSE_VS_MULTI_DWELLING_COMPATIBLE"


@dataclass(frozen=True)
class BuildingTypeAuthorityCandidate:
    source_id: str
    reference_year: int
    source_universe: str
    source_grain: str
    building_type_taxonomy: str
    evidence_status: str
    publishes_stock_distribution: bool
    wbl_compatible_join_key: bool


@dataclass(frozen=True)
class BuildingTypeAuthorityDecision:
    status: str
    reasons: tuple[str, ...]


def assess_building_type_authority(
    candidate: BuildingTypeAuthorityCandidate,
) -> BuildingTypeAuthorityDecision:
    """Fail-closed gate for a current B02 building-type authority.

    A candidate may close the WBL building-type authority gap only when it is
    current (2022+), refers to occupied dwelling stock rather than a selected
    transaction universe, uses an accepted B02 taxonomy, exposes a WBL-compatible
    grain/key, and carries OBS/DER evidence.
    """

    reasons: list[str] = []

    if candidate.reference_year < 2022:
        reasons.append("REFERENCE_YEAR_BEFORE_2022")
    if candidate.source_universe != REQUIRED_UNIVERSE:
        reasons.append("NOT_OCCUPIED_DWELLING_STOCK")
    if candidate.source_grain not in ALLOWED_GRAINS:
        reasons.append("GRAIN_NOT_WBL_COMPATIBLE")
    if candidate.building_type_taxonomy != REQUIRED_TAXONOMY:
        reasons.append("BUILDING_TYPE_TAXONOMY_NOT_COMPATIBLE")
    if candidate.evidence_status not in ALLOWED_EVIDENCE:
        reasons.append("EVIDENCE_NOT_OBS_OR_DER")
    if not candidate.publishes_stock_distribution:
        reasons.append("NO_STOCK_DISTRIBUTION")
    if not candidate.wbl_compatible_join_key:
        reasons.append("NO_WBL_COMPATIBLE_JOIN_KEY")

    if reasons:
        return BuildingTypeAuthorityDecision(status=Q, reasons=tuple(reasons))
    return BuildingTypeAuthorityDecision(status=QUALIFIED, reasons=())
