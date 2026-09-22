"""B02-P96 pitched-roof post-state U authority.

P80/P83 intentionally left pitched-roof post-state U unresolved because the
Csoknyai Table 9.1 reference-retrofit table had no explicit pitched-roof row.

P96 resolves that narrow gap from the current official 9/2023 (V.25.) EKM
regulation, Annex 1 section 1.1, which gives:

- flat roof: 0.17 W/m2K
- structures enclosing heated attic space: 0.17 W/m2K
- ceiling below attic/crawl space: 0.17 W/m2K

The same annex states the element requirement applies to designed structures
for new buildings and renovations.

For the prospective reference programme, P96 therefore admits 0.17 W/m2K as
the pitched/heated-attic enclosing-structure U upper bound.

P91 already established the simplified non-internal-insulation thermal-bridge
correction class for built-in attic enclosing structures:
    zeta in [0.10, 0.20]

Thus the conservative corrected upper is:
    U_R,max = 0.17 * (1 + 0.20) = 0.204 W/m2K

Critical boundaries:

REGULATORY_U_REQUIREMENT != OBSERVED_REALIZED_U
HEATED_ATTIC_ENCLOSURE != ALL_ROOF_GEOMETRY
PITCHED_ROOF_U_BOUND != ROOF_TYPE_PREVALENCE
PITCHED_ROOF_U_BOUND != REALIZED_PROJECT_ACCEPTANCE
P91_ZETA_SIMPLIFIED_ROUTE != DETAILED_PSI_CHI_ROUTE
P96_SUPERSEDES_P80_PITCHED_GAP != P80_SOURCE_REWRITE
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P93_SURFACE = (
    ROOT / "data" / "processed" / "b02"
    / "p93_hungarian_top_envelope_area.csv"
)

PITCHED_ROOF_BASE_U_UPPER_W_M2K = 0.17
PITCHED_ROOF_ZETA_LOWER = 0.10
PITCHED_ROOF_ZETA_UPPER = 0.20
PITCHED_ROOF_CORRECTED_U_UPPER_W_M2K = (
    PITCHED_ROOF_BASE_U_UPPER_W_M2K * (1.0 + PITCHED_ROOF_ZETA_UPPER)
)

QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U = (
    "QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U"
)
REALIZED_PITCHED_ROOF_U_VERIFICATION_REQUIRED = (
    "REALIZED_PITCHED_ROOF_U_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class PitchedRoofUConstraint:
    base_u_upper_w_m2k: float
    zeta_lower: float
    zeta_upper: float
    corrected_u_upper_w_m2k: float
    status: str
    evidence_status: str
    blocker: str | None


@dataclass(frozen=True)
class StratumTopEnvelopeThermalBound:
    surface_id: str
    wbl_period_code: str
    building_group: str
    candidate_type_ids: str
    top_envelope_area_lower_m2_per_dwelling: float
    top_envelope_area_upper_m2_per_dwelling: float
    base_u_upper_w_m2k: float
    zeta_lower: float
    zeta_upper: float
    corrected_u_upper_w_m2k: float
    top_envelope_h_upper_w_per_k_per_dwelling: float
    status: str
    evidence_status: str


def reference_programme_pitched_roof_u() -> PitchedRoofUConstraint:
    return PitchedRoofUConstraint(
        base_u_upper_w_m2k=PITCHED_ROOF_BASE_U_UPPER_W_M2K,
        zeta_lower=PITCHED_ROOF_ZETA_LOWER,
        zeta_upper=PITCHED_ROOF_ZETA_UPPER,
        corrected_u_upper_w_m2k=PITCHED_ROOF_CORRECTED_U_UPPER_W_M2K,
        status=QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U,
        evidence_status="POL/DER/SCN",
        blocker=None,
    )


@lru_cache(maxsize=None)
def reference_programme_top_envelope_thermal_surface() -> tuple[
    StratumTopEnvelopeThermalBound, ...
]:
    with P93_SURFACE.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    if len(rows) != 14:
        raise ValueError(f"expected 14 P93 strata, got {len(rows)}")

    u = reference_programme_pitched_roof_u()
    out: list[StratumTopEnvelopeThermalBound] = []
    for index, row in enumerate(rows, start=1):
        area_lo = float(row["top_envelope_area_lower_m2_per_dwelling"])
        area_hi = float(row["top_envelope_area_upper_m2_per_dwelling"])
        if area_lo <= 0 or area_hi <= 0 or area_lo > area_hi:
            raise ValueError("invalid P93 top-envelope interval")

        out.append(
            StratumTopEnvelopeThermalBound(
                surface_id=f"B02-P96-T{index:02d}",
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                candidate_type_ids=row["candidate_type_ids"],
                top_envelope_area_lower_m2_per_dwelling=area_lo,
                top_envelope_area_upper_m2_per_dwelling=area_hi,
                base_u_upper_w_m2k=u.base_u_upper_w_m2k,
                zeta_lower=u.zeta_lower,
                zeta_upper=u.zeta_upper,
                corrected_u_upper_w_m2k=u.corrected_u_upper_w_m2k,
                top_envelope_h_upper_w_per_k_per_dwelling=(
                    area_hi * u.corrected_u_upper_w_m2k
                ),
                status=QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U,
                evidence_status="POL/DER/SCN",
            )
        )
    return tuple(out)


def p96_state() -> dict[str, object]:
    rows = reference_programme_top_envelope_thermal_surface()
    return {
        "stratum_count": len(rows),
        "pitched_roof_base_u_upper_w_m2k": PITCHED_ROOF_BASE_U_UPPER_W_M2K,
        "pitched_roof_zeta_range": (
            PITCHED_ROOF_ZETA_LOWER,
            PITCHED_ROOF_ZETA_UPPER,
        ),
        "pitched_roof_corrected_u_upper_w_m2k": (
            PITCHED_ROOF_CORRECTED_U_UPPER_W_M2K
        ),
        "top_envelope_h_upper_global_w_per_k_per_dwelling": max(
            row.top_envelope_h_upper_w_per_k_per_dwelling for row in rows
        ),
        "status": QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U,
        "pitched_roof_blocker": None,
        "realized_claim_residual": (
            REALIZED_PITCHED_ROOF_U_VERIFICATION_REQUIRED
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "REGULATORY_U_REQUIREMENT_IS_NOT_OBSERVED_REALIZED_U",
        "HEATED_ATTIC_ENCLOSURE_IS_NOT_ALL_ROOF_GEOMETRY",
        "PITCHED_ROOF_U_BOUND_IS_NOT_ROOF_TYPE_PREVALENCE",
        "PITCHED_ROOF_U_BOUND_IS_NOT_REALIZED_PROJECT_ACCEPTANCE",
        "P91_ZETA_SIMPLIFIED_ROUTE_IS_NOT_DETAILED_PSI_CHI_ROUTE",
        "P96_SUPERSEDES_P80_PITCHED_GAP_IS_NOT_P80_SOURCE_REWRITE",
    )
