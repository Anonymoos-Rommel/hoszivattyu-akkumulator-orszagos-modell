"""B02-P77 national transition-response materialization and B05 coverage gates.

The repository already has the record/project physical method chain:

B06 post-state design load
-> B06-P65 required post-retrofit supply temperature
-> B05 PerformanceMap capacity/input/COP evaluation.

P77 does not invent a national response percentage. It decomposes the broad
national-materialization blocker into executable evidence gates and binds the
existing B05 product-domain evidence to that chain.

Critical boundaries:

METHOD EXISTS != NATIONAL INPUT SURFACE EXISTS
P21/WBL POPULATION WEIGHT != POST-RETROFIT DESIGN LOAD
EMITTER CLASS != P65 REQUIRED SUPPLY TEMPERATURE
PRODUCT OPERATING LIMIT != SOURCE-NATIVE PERFORMANCE MAP
WEATHER-DOMAIN COVERAGE != HEATING-RUNTIME COVERAGE
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEATHER_SUPPLY_COVERAGE = ROOT / "data" / "processed" / "heat_pump_weather_supply_coverage.csv"

REFERENCE_EQUIPMENT = "STIEBEL-HPA-O-4-CS-PLUS-INT"
EXTREME_PROFILE = "B05-EXTREME-OBSERVED-72H-15310"

Q = "Q"
QUALIFIED_METHOD = "QUALIFIED_TRANSITION_DERIVED_METHOD"
PARTIAL_QUANTIFIED_PRODUCT_DOMAIN = "PARTIAL_QUANTIFIED_PRODUCT_DOMAIN"


@dataclass(frozen=True)
class SupplyCoverage:
    supply_temperature_c: float
    status: str
    weather_hours_total: int
    weather_hours_inside_domain: int | None
    weather_hours_below_domain: int | None
    coverage_share: float | None
    performance_domain_min_outdoor_c: float | None
    performance_domain_max_outdoor_c: float | None
    coldest_uncovered_outdoor_c: float | None
    source_id: str


@dataclass(frozen=True)
class MaterializationDecision:
    status: str
    blockers: tuple[str, ...]


def _read_rows() -> list[dict[str, str]]:
    with WEATHER_SUPPLY_COVERAGE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def current_reference_supply_coverage() -> dict[float, SupplyCoverage]:
    """Read the already-materialized source-bounded B05 weather/domain audit."""

    selected = [
        row
        for row in _read_rows()
        if row["weather_profile_id"] == EXTREME_PROFILE
        and row["equipment_id"] == REFERENCE_EQUIPMENT
    ]
    by_supply: dict[float, SupplyCoverage] = {}
    for row in selected:
        supply = float(row["supply_temperature_C"])

        def maybe_int(name: str) -> int | None:
            return int(row[name]) if row[name] != "" else None

        def maybe_float(name: str) -> float | None:
            return float(row[name]) if row[name] != "" else None

        by_supply[supply] = SupplyCoverage(
            supply_temperature_c=supply,
            status=row["status"],
            weather_hours_total=int(row["weather_hours_total"]),
            weather_hours_inside_domain=maybe_int("weather_hours_inside_domain"),
            weather_hours_below_domain=maybe_int("weather_hours_below_domain"),
            coverage_share=maybe_float("coverage_share"),
            performance_domain_min_outdoor_c=maybe_float(
                "performance_domain_min_Tout_C"
            ),
            performance_domain_max_outdoor_c=maybe_float(
                "performance_domain_max_Tout_C"
            ),
            coldest_uncovered_outdoor_c=maybe_float("coldest_uncovered_Tout_C"),
            source_id=row["source_id"],
        )

    if set(by_supply) != {35.0, 45.0, 55.0}:
        raise ValueError("reference W35/W45/W55 coverage rows are incomplete")
    return by_supply


def assess_national_transition_response_materialization(
    *,
    post_retrofit_design_load_surface_materialized: bool,
    p65_required_supply_temperature_surface_materialized: bool,
    b05_product_design_point_coverage_complete: bool,
) -> MaterializationDecision:
    """Gate national response without substituting method availability for data."""

    blockers: list[str] = []
    if not post_retrofit_design_load_surface_materialized:
        blockers.append("NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED")
    if not p65_required_supply_temperature_surface_materialized:
        blockers.append("NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED")
    if not b05_product_design_point_coverage_complete:
        blockers.append("B05_MATERIALIZED_DESIGN_POINT_COVERAGE_REQUIRED")

    if blockers:
        return MaterializationDecision(Q, tuple(blockers))
    return MaterializationDecision(QUALIFIED_METHOD, ())


def assess_reference_product_domain() -> MaterializationDecision:
    """Expose exact remaining B05 product-map gaps from existing evidence.

    This evaluates source-domain completeness, not demand-weighted runtime
    coverage and not national product-market representativeness.
    """

    rows = current_reference_supply_coverage()
    blockers: list[str] = []

    w35 = rows[35.0]
    if w35.performance_domain_min_outdoor_c is None or w35.performance_domain_min_outdoor_c > -15:
        blockers.append("B05_W35_COLD_PRODUCT_GRID_REQUIRED")
    if (
        w35.coldest_uncovered_outdoor_c is not None
        and w35.performance_domain_min_outdoor_c is not None
        and w35.coldest_uncovered_outdoor_c < w35.performance_domain_min_outdoor_c
    ):
        blockers.append("B05_W35_BELOW_MINUS15_PRODUCT_GRID_REQUIRED_IF_EXTREME_IN_SCOPE")

    w45 = rows[45.0]
    if w45.performance_domain_min_outdoor_c is None or w45.performance_domain_min_outdoor_c > -15:
        blockers.append("B05_COLD_W45_PRODUCT_GRID_REQUIRED")

    w55 = rows[55.0]
    if w55.status == Q or w55.coverage_share is None:
        blockers.append("B05_CONTINUOUS_W55_PRODUCT_SURFACE_REQUIRED")

    if blockers:
        return MaterializationDecision(
            PARTIAL_QUANTIFIED_PRODUCT_DOMAIN,
            tuple(blockers),
        )
    return MaterializationDecision("COMPLETE_REFERENCE_PRODUCT_DOMAIN", ())


def national_materialization_method_status() -> MaterializationDecision:
    """The algorithmic bridge exists even though national input surfaces do not."""

    return MaterializationDecision(QUALIFIED_METHOD, ())
