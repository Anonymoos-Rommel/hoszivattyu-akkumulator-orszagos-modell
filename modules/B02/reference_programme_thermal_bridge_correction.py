"""B02-P91 reference-programme thermal-bridge correction contract.

The current Hungarian simplified calculation method permits structural
connection thermal bridges to be represented through:

    U_R = U * (1 + zeta)

instead of explicit sum(l_k * psi_k) + sum(chi_j), subject to the method's
applicability rules.

P91 uses that route for the prospective REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP
programme branch. It does not fabricate national psi-length inventories.

Critical boundaries:

SIMPLIFIED_ZETA_ROUTE != DETAILED_PSI_CHI_ROUTE
REFERENCE_PROGRAMME_ZETA != OBSERVED_THERMAL_BRIDGE_DISTRIBUTION
INTERNAL_INSULATION != ZETA_ELIGIBLE
COMPONENT_U_ALREADY_CONTAINING_BRIDGE_EFFECT != ADD_BRIDGE_AGAIN
THERMAL_BRIDGE_CORRECTION_FACTOR != COMPONENT_AREA_GEOMETRY
REFERENCE_PROGRAMME_CORRECTION != REALIZED_PROJECT_PERFORMANCE
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from functools import lru_cache
from pathlib import Path

from modules.B02.keop23_uvalue_poststate import REFERENCE_RETROFIT_U_MAX


ROOT = Path(__file__).resolve().parents[2]
P85_SURFACE = ROOT / "data" / "processed" / "b02" / "p85_reference_retrofit_physical_input_surface.csv"

EXTERNAL_WALL = "EXTERNAL_WALL"
FLAT_ROOF = "FLAT_ROOF"
ATTIC_FLOOR = "ATTIC_FLOOR"
BASEMENT_CEILING = "BASEMENT_CEILING"
PITCHED_ROOF = "PITCHED_ROOF"
WINDOW = "WINDOW"

NON_INTERNAL_INSULATION = "NON_INTERNAL_INSULATION"
INTERNAL_INSULATION = "INTERNAL_INSULATION"

QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE = (
    "QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE"
)
DETAILED_THERMAL_BRIDGE_MODEL_REQUIRED = "DETAILED_THERMAL_BRIDGE_MODEL_REQUIRED"
REALIZED_THERMAL_BRIDGE_VERIFICATION_REQUIRED = (
    "REALIZED_THERMAL_BRIDGE_VERIFICATION_REQUIRED"
)

# Current Hungarian method, Appendix 1, section 6.1.2, Tables 6.1-6.2.
# These are method classes, not observed population distributions.
ZETA_BOUNDS = {
    # Full non-internal-insulation method envelope across:
    # - external/within-structure uninterrupted insulation: 0.15..0.30
    # - other external walls: 0.25..0.40
    EXTERNAL_WALL: (0.15, 0.40),
    FLAT_ROOF: (0.10, 0.20),
    # Table 6.1 gives a single 0.10 correction for attic floors.
    ATTIC_FLOOR: (0.10, 0.10),
    # Basement ceiling: 0.20 within-structure insulation, 0.10 lower-side.
    BASEMENT_CEILING: (0.10, 0.20),
    # Built-in attic enclosing structures use the 0.10/0.15/0.20 classes.
    PITCHED_ROOF: (0.10, 0.20),
}

# Window thermal bridges are handled by window U semantics and external-wall
# classification/edge density. P91 does not apply another generic zeta to the
# window U-value.
NO_SEPARATE_ZETA_COMPONENTS = (WINDOW,)


@dataclass(frozen=True)
class ZetaBound:
    component: str
    lower: float | None
    upper: float | None
    status: str
    evidence_status: str
    blocker: str | None


@dataclass(frozen=True)
class ComponentThermalBridgeCorrection:
    component: str
    base_u_upper_w_m2k: float | None
    zeta_lower: float | None
    zeta_upper: float | None
    corrected_u_upper_w_m2k: float | None
    delta_u_upper_w_m2k: float | None
    status: str
    evidence_status: str
    blocker: str | None


@dataclass(frozen=True)
class StratumThermalBridgeSurface:
    surface_id: str
    wbl_period_code: str
    building_group: str
    external_wall_zeta_lower: float
    external_wall_zeta_upper: float
    external_wall_corrected_u_upper_w_m2k: float
    flat_roof_zeta_lower: float
    flat_roof_zeta_upper: float
    flat_roof_corrected_u_upper_w_m2k: float
    attic_floor_zeta: float
    attic_floor_corrected_u_upper_w_m2k: float
    basement_ceiling_zeta_lower: float
    basement_ceiling_zeta_upper: float
    basement_ceiling_corrected_u_upper_w_m2k: float
    pitched_roof_zeta_lower: float
    pitched_roof_zeta_upper: float
    pitched_roof_corrected_u_upper_w_m2k: float | None
    status: str
    evidence_status: str


def zeta_bound(
    component: str,
    *,
    insulation_position: str = NON_INTERNAL_INSULATION,
) -> ZetaBound:
    if component in NO_SEPARATE_ZETA_COMPONENTS:
        return ZetaBound(
            component=component,
            lower=None,
            upper=None,
            status="NO_SEPARATE_GENERIC_ZETA",
            evidence_status="POL",
            blocker=None,
        )

    if component not in ZETA_BOUNDS:
        raise ValueError(f"unsupported component: {component}")

    if insulation_position == INTERNAL_INSULATION:
        return ZetaBound(
            component=component,
            lower=None,
            upper=None,
            status="Q_DETAILED_METHOD_REQUIRED",
            evidence_status="Q",
            blocker=DETAILED_THERMAL_BRIDGE_MODEL_REQUIRED,
        )
    if insulation_position != NON_INTERNAL_INSULATION:
        raise ValueError(f"unsupported insulation position: {insulation_position}")

    lower, upper = ZETA_BOUNDS[component]
    return ZetaBound(
        component=component,
        lower=lower,
        upper=upper,
        status=QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE,
        evidence_status="POL/SCN",
        blocker=None,
    )


def corrected_u_w_m2k(*, base_u_w_m2k: float, zeta: float) -> float:
    u = float(base_u_w_m2k)
    z = float(zeta)
    if u < 0:
        raise ValueError("base_u_w_m2k must be nonnegative")
    if z < 0:
        raise ValueError("zeta must be nonnegative")
    return u * (1.0 + z)


def equivalent_thermal_bridge_h_w_per_k(
    *,
    area_m2: float,
    base_u_w_m2k: float,
    zeta: float,
) -> float:
    """Equivalent separate H_tb term for the simplified method.

    Since:
        A * U_R = A * U * (1 + zeta)
    the bridge-only equivalent is:
        H_tb = A * U * zeta

    This permits compatibility with B06's separate H_thermal_bridge term while
    preserving exact equivalence to the simplified current method.

    Component areas remain an independent geometry input.
    """

    area = float(area_m2)
    u = float(base_u_w_m2k)
    z = float(zeta)
    if area < 0 or u < 0 or z < 0:
        raise ValueError("thermal-bridge inputs must be nonnegative")
    return area * u * z


def reference_component_correction(component: str) -> ComponentThermalBridgeCorrection:
    bound = zeta_bound(component)

    if component == PITCHED_ROOF:
        # P80/P85 still has no explicit pitched-roof reference-retrofit U bound.
        return ComponentThermalBridgeCorrection(
            component=component,
            base_u_upper_w_m2k=None,
            zeta_lower=bound.lower,
            zeta_upper=bound.upper,
            corrected_u_upper_w_m2k=None,
            delta_u_upper_w_m2k=None,
            status="PARTIAL_ZETA_KNOWN_U_BOUND_Q",
            evidence_status="POL/Q",
            blocker="PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        )

    if component in NO_SEPARATE_ZETA_COMPONENTS:
        return ComponentThermalBridgeCorrection(
            component=component,
            base_u_upper_w_m2k=REFERENCE_RETROFIT_U_MAX.get(component),
            zeta_lower=None,
            zeta_upper=None,
            corrected_u_upper_w_m2k=REFERENCE_RETROFIT_U_MAX.get(component),
            delta_u_upper_w_m2k=0.0,
            status="NO_SEPARATE_GENERIC_ZETA",
            evidence_status="POL/DER",
            blocker=None,
        )

    u_max = REFERENCE_RETROFIT_U_MAX[component]
    assert bound.upper is not None
    return ComponentThermalBridgeCorrection(
        component=component,
        base_u_upper_w_m2k=u_max,
        zeta_lower=bound.lower,
        zeta_upper=bound.upper,
        corrected_u_upper_w_m2k=corrected_u_w_m2k(
            base_u_w_m2k=u_max,
            zeta=bound.upper,
        ),
        delta_u_upper_w_m2k=u_max * bound.upper,
        status=QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE,
        evidence_status="POL/DER/SCN",
        blocker=None,
    )


@lru_cache(maxsize=None)
def reference_programme_thermal_bridge_surface() -> tuple[
    StratumThermalBridgeSurface, ...
]:
    with P85_SURFACE.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    if len(rows) != 14:
        raise ValueError(f"expected 14 P85 strata, got {len(rows)}")

    wall = reference_component_correction(EXTERNAL_WALL)
    flat = reference_component_correction(FLAT_ROOF)
    attic = reference_component_correction(ATTIC_FLOOR)
    basement = reference_component_correction(BASEMENT_CEILING)
    pitched = reference_component_correction(PITCHED_ROOF)

    out: list[StratumThermalBridgeSurface] = []
    for index, row in enumerate(rows, start=1):
        # Fail closed if the P85 U constraints drift away from P80 authority.
        expected = {
            "external_wall_u_max_w_m2k": wall.base_u_upper_w_m2k,
            "flat_roof_u_max_w_m2k": flat.base_u_upper_w_m2k,
            "attic_floor_u_max_w_m2k": attic.base_u_upper_w_m2k,
            "basement_ceiling_u_max_w_m2k": basement.base_u_upper_w_m2k,
        }
        for key, value in expected.items():
            if float(row[key]) != float(value):
                raise ValueError(f"P85/P91 U-bound drift for {key}")

        out.append(
            StratumThermalBridgeSurface(
                surface_id=f"B02-P91-T{index:02d}",
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                external_wall_zeta_lower=float(wall.zeta_lower),
                external_wall_zeta_upper=float(wall.zeta_upper),
                external_wall_corrected_u_upper_w_m2k=float(
                    wall.corrected_u_upper_w_m2k
                ),
                flat_roof_zeta_lower=float(flat.zeta_lower),
                flat_roof_zeta_upper=float(flat.zeta_upper),
                flat_roof_corrected_u_upper_w_m2k=float(
                    flat.corrected_u_upper_w_m2k
                ),
                attic_floor_zeta=float(attic.zeta_upper),
                attic_floor_corrected_u_upper_w_m2k=float(
                    attic.corrected_u_upper_w_m2k
                ),
                basement_ceiling_zeta_lower=float(basement.zeta_lower),
                basement_ceiling_zeta_upper=float(basement.zeta_upper),
                basement_ceiling_corrected_u_upper_w_m2k=float(
                    basement.corrected_u_upper_w_m2k
                ),
                pitched_roof_zeta_lower=float(pitched.zeta_lower),
                pitched_roof_zeta_upper=float(pitched.zeta_upper),
                pitched_roof_corrected_u_upper_w_m2k=None,
                status=QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE,
                evidence_status="POL/DER/SCN",
            )
        )
    return tuple(out)


def p91_state() -> dict[str, object]:
    rows = reference_programme_thermal_bridge_surface()
    return {
        "stratum_count": len(rows),
        "external_wall_zeta_range": ZETA_BOUNDS[EXTERNAL_WALL],
        "flat_roof_zeta_range": ZETA_BOUNDS[FLAT_ROOF],
        "attic_floor_zeta_range": ZETA_BOUNDS[ATTIC_FLOOR],
        "basement_ceiling_zeta_range": ZETA_BOUNDS[BASEMENT_CEILING],
        "pitched_roof_zeta_range": ZETA_BOUNDS[PITCHED_ROOF],
        "external_wall_corrected_u_upper_w_m2k": max(
            row.external_wall_corrected_u_upper_w_m2k for row in rows
        ),
        "flat_roof_corrected_u_upper_w_m2k": max(
            row.flat_roof_corrected_u_upper_w_m2k for row in rows
        ),
        "attic_floor_corrected_u_upper_w_m2k": max(
            row.attic_floor_corrected_u_upper_w_m2k for row in rows
        ),
        "basement_ceiling_corrected_u_upper_w_m2k": max(
            row.basement_ceiling_corrected_u_upper_w_m2k for row in rows
        ),
        "reference_programme_thermal_bridge_status": (
            QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE
        ),
        "reference_programme_thermal_bridge_blocker": None,
        "independent_geometry_dependency": (
            "COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED"
        ),
        "pitched_roof_dependency": "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        "realized_claim_residual": REALIZED_THERMAL_BRIDGE_VERIFICATION_REQUIRED,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "SIMPLIFIED_ZETA_ROUTE_IS_NOT_DETAILED_PSI_CHI_ROUTE",
        "REFERENCE_PROGRAMME_ZETA_IS_NOT_OBSERVED_THERMAL_BRIDGE_DISTRIBUTION",
        "INTERNAL_INSULATION_REQUIRES_DETAILED_THERMAL_BRIDGE_METHOD",
        "NO_DOUBLE_COUNT_IF_COMPONENT_U_ALREADY_INCLUDES_BRIDGE_EFFECT",
        "THERMAL_BRIDGE_CORRECTION_FACTOR_IS_NOT_COMPONENT_AREA_GEOMETRY",
        "PITCHED_ROOF_ZETA_KNOWN_DOES_NOT_RESOLVE_PITCHED_ROOF_U",
        "REFERENCE_PROGRAMME_CORRECTION_IS_NOT_REALIZED_PROJECT_PERFORMANCE",
    )
