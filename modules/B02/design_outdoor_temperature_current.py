"""B02-P86 current Hungarian design-outdoor-temperature authority.

P86 updates the design-temperature layer to the current MSZ 24140:2026
standard generation and keeps a fail-closed distinction between:

- the official existence/current validity of MSZ 24140:2026;
- public secondary interpretation of the F1 design-temperature map;
- exact project/location authority.

The public evidence supports a current three-zone domain of -12, -11 and
-10 degC plus named city control points. It does not expose a machine-readable
official polygon layer for all settlements.

CURRENT STANDARD ZONE DOMAIN != EXACT NATIONAL LOCATION MAP
PUBLIC CITY ANCHOR != RECORD-LEVEL ENGINEERING AUTHORITY
2023 GOVERNMENT METEO STANDARD YEAR != DESIGN OUTDOOR TEMPERATURE MAP
OBSERVED WEATHER EXTREME != DESIGN OUTDOOR TEMPERATURE
"""

from __future__ import annotations

from dataclasses import dataclass


CURRENT_STANDARD_ID = "MSZ_24140_2026"
CURRENT_STANDARD_EFFECTIVE_DATE = "2026-04-01"
CURRENT_ZONE_VALUES_C = (-12.0, -11.0, -10.0)

PRIMARY_SOURCE_ID = "SRC-B02-MSZ-24140-2026"
PUBLIC_MAP_INTERPRETATION_SOURCE_ID = "SRC-B02-BIMLINE-MSZ24140-2026"


CITY_ANCHORS_C: dict[str, float] = {
    "Békéscsaba": -12.0,
    "Debrecen": -12.0,
    "Nyíregyháza": -12.0,
    "Sopron": -12.0,
    "Budapest": -11.0,
    "Eger": -11.0,
    "Győr": -11.0,
    "Kecskemét": -11.0,
    "Miskolc": -11.0,
    "Salgótarján": -11.0,
    "Szeged": -11.0,
    "Szolnok": -11.0,
    "Szombathely": -11.0,
    "Tatabánya": -11.0,
    "Zalaegerszeg": -11.0,
    "Kaposvár": -10.0,
    "Pécs": -10.0,
    "Székesfehérvár": -10.0,
    "Szekszárd": -10.0,
    "Veszprém": -10.0,
}


@dataclass(frozen=True)
class DesignOutdoorTemperatureDecision:
    status: str
    lower_c: float | None
    upper_c: float | None
    point_c: float | None
    source_refs: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def current_standard_domain() -> DesignOutdoorTemperatureDecision:
    """Return the public current-standard national zone domain, not a point map."""

    return DesignOutdoorTemperatureDecision(
        status="QUALIFIED_CURRENT_STANDARD_ZONE_DOMAIN",
        lower_c=min(CURRENT_ZONE_VALUES_C),
        upper_c=max(CURRENT_ZONE_VALUES_C),
        point_c=None,
        source_refs=(PRIMARY_SOURCE_ID, PUBLIC_MAP_INTERPRETATION_SOURCE_ID),
        blockers=(),
        warnings=(
            "ZONE_DOMAIN_IS_NOT_EXACT_LOCATION_MAPPING",
            "MSZ_24140_2026_STANDARD_TEXT_AND_F1_MAP_ARE_NOT_REPUBLISHED",
        ),
    )


def resolve_named_city_anchor(city_name: str) -> DesignOutdoorTemperatureDecision:
    """Resolve only public named map-control points reported by the secondary source."""

    if city_name not in CITY_ANCHORS_C:
        return DesignOutdoorTemperatureDecision(
            status="Q_EXACT_LOCATION_ZONE",
            lower_c=min(CURRENT_ZONE_VALUES_C),
            upper_c=max(CURRENT_ZONE_VALUES_C),
            point_c=None,
            source_refs=(PRIMARY_SOURCE_ID, PUBLIC_MAP_INTERPRETATION_SOURCE_ID),
            blockers=("MACHINE_READABLE_CURRENT_STANDARD_ZONE_GEOMETRY_REQUIRED",),
            warnings=("NO_CITY_ANCHOR_IMPUTATION",),
        )

    value = CITY_ANCHORS_C[city_name]
    return DesignOutdoorTemperatureDecision(
        status="QUALIFIED_PUBLIC_CITY_ANCHOR",
        lower_c=value,
        upper_c=value,
        point_c=value,
        source_refs=(PRIMARY_SOURCE_ID, PUBLIC_MAP_INTERPRETATION_SOURCE_ID),
        blockers=(),
        warnings=(
            "PUBLIC_CITY_ANCHOR_IS_NOT_RECORD_LEVEL_ENGINEERING_AUTHORITY",
            "LOCAL_ALTITUDE_URBAN_HEAT_ISLAND_AND_RISK_ADJUSTMENTS_REMAIN_PROJECT_SPECIFIC",
        ),
    )


def assess_location(
    *,
    city_name: str | None,
    settlement_population: int | None,
    elevation_m: float | None,
    explicit_standard_zone_c: float | None = None,
    project_specific_adjustment_c: float | None = None,
    project_adjustment_authorized: bool = False,
) -> DesignOutdoorTemperatureDecision:
    """Fail-closed current-standard resolver.

    The publicly reported application caveat says the map baseline applies to
    settlements above 30,000 population and elevations not exceeding 300 m.
    Outside that baseline scope, or when an exact map-zone is not available,
    the resolver remains Q unless an explicit current-standard/project authority
    is supplied.
    """

    blockers: list[str] = []
    warnings: list[str] = []

    if settlement_population is None or settlement_population <= 30_000:
        blockers.append("LOCAL_DESIGN_AUTHORITY_REQUIRED_FOR_SMALLER_SETTLEMENT")
    if elevation_m is None or elevation_m > 300.0:
        blockers.append("LOCAL_DESIGN_AUTHORITY_REQUIRED_FOR_HIGHER_ELEVATION")

    baseline: float | None = None
    if explicit_standard_zone_c is not None:
        value = float(explicit_standard_zone_c)
        if value not in CURRENT_ZONE_VALUES_C:
            raise ValueError("explicit current-standard zone must be -12, -11 or -10 C")
        baseline = value
    elif city_name is not None and city_name in CITY_ANCHORS_C:
        baseline = CITY_ANCHORS_C[city_name]
        warnings.append("PUBLIC_CITY_ANCHOR_USED_AS_MAP_CONTROL_POINT")
    else:
        blockers.append("MACHINE_READABLE_CURRENT_STANDARD_ZONE_GEOMETRY_REQUIRED")

    if blockers:
        return DesignOutdoorTemperatureDecision(
            status="Q_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE",
            lower_c=min(CURRENT_ZONE_VALUES_C),
            upper_c=max(CURRENT_ZONE_VALUES_C),
            point_c=None,
            source_refs=(PRIMARY_SOURCE_ID, PUBLIC_MAP_INTERPRETATION_SOURCE_ID),
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )

    assert baseline is not None
    final = baseline
    if project_specific_adjustment_c is not None:
        if not project_adjustment_authorized:
            return DesignOutdoorTemperatureDecision(
                status="Q_PROJECT_SPECIFIC_ADJUSTMENT_AUTHORITY",
                lower_c=baseline,
                upper_c=baseline,
                point_c=None,
                source_refs=(PRIMARY_SOURCE_ID, PUBLIC_MAP_INTERPRETATION_SOURCE_ID),
                blockers=("PROJECT_SPECIFIC_DESIGN_ADJUSTMENT_AUTHORITY_REQUIRED",),
                warnings=tuple(warnings),
            )
        final = baseline + float(project_specific_adjustment_c)
        warnings.append("PROJECT_SPECIFIC_ADJUSTMENT_APPLIED")

    return DesignOutdoorTemperatureDecision(
        status="QUALIFIED_CURRENT_STANDARD_LOCATION_INPUT",
        lower_c=final,
        upper_c=final,
        point_c=final,
        source_refs=(PRIMARY_SOURCE_ID, PUBLIC_MAP_INTERPRETATION_SOURCE_ID),
        blockers=(),
        warnings=tuple(warnings),
    )


def mapping_boundary() -> tuple[str, ...]:
    return (
        "MSZ_24140_2026_ZONE_DOMAIN != MACHINE_READABLE_NATIONAL_POLYGON_MAP",
        "PUBLIC_CITY_ANCHOR != HOUSEHOLD_OR_PROJECT_DESIGN_AUTHORITY",
        "2023_GOVERNMENT_METEO_STANDARD_YEAR != DESIGN_OUTDOOR_TEMPERATURE_MAP",
        "HUNGAROMET_OBSERVED_EXTREME != DESIGN_OUTDOOR_TEMPERATURE",
        "OLD_MINUS15_MINUS13_MINUS11_MAP != CURRENT_STANDARD_MAP",
    )
