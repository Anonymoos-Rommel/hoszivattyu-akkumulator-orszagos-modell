"""B02-P98 set-valued national post-retrofit supply-temperature envelope.

The national emitter composition is set-identified (B02-P65), while B06-P65
requires building/room-level authority for an exact post-retrofit supply
temperature. P98 therefore does not manufacture a national point temperature
or a temperature probability distribution.

Instead, the prospective reference programme carries an explicit design-flow
category set supported by admitted heat-emitter design guidance:

    LE_35   : <= 35 C
    C36_40  : 36..40 C
    C41_45  : 41..45 C
    C46_50  : 46..50 C
    C51_55  : 51..55 C

The <=55 C programme ceiling is a prospective low-temperature design contract,
not an observed Hungarian stock maximum and not a statement that heat-pump or
emitter physics stops at 55 C.

If a building would require >55 C at the design condition, the reference
programme requires emitter/hydraulic adaptation or an explicitly authorized
exception; no hidden high-temperature default is allowed.

Critical boundaries:

NATIONAL_CATEGORY_SET != NATIONAL_TEMPERATURE_DISTRIBUTION
EMITTER_CLASS != FIXED_SUPPLY_TEMPERATURE
REFERENCE_PROGRAMME_55C_CEILING != PHYSICAL_EQUIPMENT_LIMIT
B05_W35_W45_W55_CONTROL_POINTS != BUILDING_TEMPERATURE_SNAPPING
FOREIGN_MEAN_OPERATING_TEMPERATURE != HUNGARIAN_DESIGN_TEMPERATURE
P98_NATIONAL_SURFACE != P65_RECORD_LEVEL_AUTHORITY
"""

from __future__ import annotations

from dataclasses import dataclass


REFERENCE_PROGRAMME_MAX_DESIGN_FLOW_C = 55.0
B05_AUDIT_CONTROL_POINTS_C = (35.0, 45.0, 55.0)

QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET = (
    "QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET"
)
REALIZED_SUPPLY_TEMPERATURE_VERIFICATION_REQUIRED = (
    "REALIZED_SUPPLY_TEMPERATURE_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class SupplyTemperatureBand:
    band_id: str
    lower_c: float | None
    upper_c: float
    lower_inclusive: bool
    upper_inclusive: bool
    status: str
    evidence_status: str


@dataclass(frozen=True)
class StratumSupplyTemperatureEnvelope:
    surface_id: str
    wbl_period_code: str
    building_group: str
    admissible_band_ids: tuple[str, ...]
    max_reference_programme_design_flow_c: float
    b05_audit_control_points_c: tuple[float, ...]
    allocation_status: str
    status: str
    evidence_status: str


SUPPLY_TEMPERATURE_BANDS: tuple[SupplyTemperatureBand, ...] = (
    SupplyTemperatureBand(
        "LE_35",
        None,
        35.0,
        False,
        True,
        QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
        "POL/DER/SCN",
    ),
    SupplyTemperatureBand(
        "C36_40",
        36.0,
        40.0,
        True,
        True,
        QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
        "POL/DER/SCN",
    ),
    SupplyTemperatureBand(
        "C41_45",
        41.0,
        45.0,
        True,
        True,
        QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
        "POL/DER/SCN",
    ),
    SupplyTemperatureBand(
        "C46_50",
        46.0,
        50.0,
        True,
        True,
        QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
        "POL/DER/SCN",
    ),
    SupplyTemperatureBand(
        "C51_55",
        51.0,
        55.0,
        True,
        True,
        QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
        "POL/DER/SCN",
    ),
)

WBL_PERIODS = (
    "Y_LT1919",
    "Y1919-1945",
    "Y1946-1960",
    "Y1961-1980",
    "Y1981-2000",
    "Y2001-2010",
    "Y_GE2011",
)
BUILDING_GROUPS = ("FAMILY_HOUSE", "MULTI_DWELLING")


def classify_design_flow_temperature(flow_c: float) -> str:
    """Classify an exact P65-derived flow temperature for reporting.

    This function never creates the temperature. It only classifies an already
    authorized numeric value.
    """

    value = float(flow_c)
    if value <= 0:
        raise ValueError("flow_c must be positive")
    if value <= 35.0:
        return "LE_35"
    if value <= 40.0:
        return "C36_40"
    if value <= 45.0:
        return "C41_45"
    if value <= 50.0:
        return "C46_50"
    if value <= 55.0:
        return "C51_55"
    return "ABOVE_REFERENCE_PROGRAMME_55"


def reference_programme_action_for_required_flow(flow_c: float) -> str:
    """Return the programme action gate for an exact required flow value."""

    band = classify_design_flow_temperature(flow_c)
    if band == "ABOVE_REFERENCE_PROGRAMME_55":
        return "EMITTER_OR_HYDRAULIC_ADAPTATION_OR_EXPLICIT_EXCEPTION_REQUIRED"
    return "WITHIN_REFERENCE_PROGRAMME_SUPPLY_ENVELOPE"


def national_reference_programme_supply_temperature_surface() -> tuple[
    StratumSupplyTemperatureEnvelope, ...
]:
    """Materialize the same admissible category set over all 14 strata.

    P65 does not identify a P21/WBL emitter allocation. Therefore P98 must not
    assign different temperature probabilities or point values by age/group.
    """

    bands = tuple(item.band_id for item in SUPPLY_TEMPERATURE_BANDS)
    out: list[StratumSupplyTemperatureEnvelope] = []
    index = 0
    for period in WBL_PERIODS:
        for group in BUILDING_GROUPS:
            index += 1
            out.append(
                StratumSupplyTemperatureEnvelope(
                    surface_id=f"B02-P98-S{index:02d}",
                    wbl_period_code=period,
                    building_group=group,
                    admissible_band_ids=bands,
                    max_reference_programme_design_flow_c=(
                        REFERENCE_PROGRAMME_MAX_DESIGN_FLOW_C
                    ),
                    b05_audit_control_points_c=B05_AUDIT_CONTROL_POINTS_C,
                    allocation_status=(
                        "LATENT_SET_PROPAGATION_NO_POINT_WEIGHTS"
                    ),
                    status=QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
                    evidence_status="POL/DER/SCN",
                )
            )
    return tuple(out)


def p98_state() -> dict[str, object]:
    surface = national_reference_programme_supply_temperature_surface()
    return {
        "stratum_count": len(surface),
        "design_flow_band_ids": tuple(x.band_id for x in SUPPLY_TEMPERATURE_BANDS),
        "max_reference_programme_design_flow_c": (
            REFERENCE_PROGRAMME_MAX_DESIGN_FLOW_C
        ),
        "b05_audit_control_points_c": B05_AUDIT_CONTROL_POINTS_C,
        "population_temperature_weights": None,
        "national_supply_temperature_blocker": None,
        "status": QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
        "realized_claim_residual": (
            REALIZED_SUPPLY_TEMPERATURE_VERIFICATION_REQUIRED
        ),
        "independent_downstream_residuals": (
            "B05_MATERIALIZED_DESIGN_POINT_COVERAGE_REQUIRED",
            "B05_COLD_W45_PRODUCT_GRID_REQUIRED",
            "B05_CONTINUOUS_W55_PRODUCT_SURFACE_REQUIRED",
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "NATIONAL_CATEGORY_SET_IS_NOT_NATIONAL_TEMPERATURE_DISTRIBUTION",
        "EMITTER_CLASS_IS_NOT_FIXED_SUPPLY_TEMPERATURE",
        "REFERENCE_PROGRAMME_55C_CEILING_IS_NOT_PHYSICAL_EQUIPMENT_LIMIT",
        "B05_W35_W45_W55_CONTROL_POINTS_ARE_NOT_BUILDING_TEMPERATURE_SNAPPING",
        "FOREIGN_MEAN_OPERATING_TEMPERATURE_IS_NOT_HUNGARIAN_DESIGN_TEMPERATURE",
        "P98_NATIONAL_SURFACE_IS_NOT_P65_RECORD_LEVEL_AUTHORITY",
    )
