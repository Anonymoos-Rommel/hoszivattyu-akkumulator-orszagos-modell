"""B02-P97 national set-valued current-standard design-temperature envelope.

P86 established the current MSZ 24140:2026 domain {-12,-11,-10 C} and 20
public city anchors, but left complete national settlement-to-zone mapping Q.

P97 repairs the national modelling requirement using the existing P82 physical
inference policy:

NO FULL-POPULATION POINT DATA != BLOCKER
NO DEFENSIBLE POPULATION INFERENCE == BLOCKER
POPULATION ESTIMATE != RECORD PASS/FAIL

The canonical KSH WBL population grain is county + settlement type, not exact
settlement identity. Therefore exact settlement-to-zone mapping cannot be
honestly joined to every national cell without inventing precision.

For the prospective reference programme P97 admits the complete current-standard
zone domain as a set-valued design input:

    theta_e in {-12,-11,-10} C

with the current residential service reference:

    theta_i = 20 C

therefore:

    delta_T in {32,31,30} K
    bounded delta_T = [30,32] K

This is sufficient for bounded national design-load propagation because heat
loss is monotone in delta_T. Exact settlement/project assignment remains a
record-level requirement and P86's fail-closed resolver is unchanged.

Critical boundaries:

NATIONAL_ZONE_SET != EXACT_SETTLEMENT_ZONE
CURRENT_STANDARD_DOMAIN != PROJECT_DESIGN_AUTHORITY
SET_VALUED_PROPAGATION != MOST_LIKELY_ZONE
COUNTY_SETTLEMENT_TYPE_GRAIN != SETTLEMENT_COORDINATE
BASELINE_MAP_SCOPE != AUTOMATIC_PROJECT_COMPLIANCE_OUTSIDE_SCOPE
NATIONAL_REFERENCE_PROGRAMME != REALIZED_PROJECT_ACCEPTANCE
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.design_outdoor_temperature_current import CURRENT_ZONE_VALUES_C


DESIGN_INDOOR_TEMPERATURE_C = 20.0
CURRENT_STANDARD_ZONE_SET_C = tuple(sorted(CURRENT_ZONE_VALUES_C))
DESIGN_DELTA_T_SET_K = tuple(
    DESIGN_INDOOR_TEMPERATURE_C - t for t in CURRENT_STANDARD_ZONE_SET_C
)
DESIGN_DELTA_T_LOWER_K = min(DESIGN_DELTA_T_SET_K)
DESIGN_DELTA_T_UPPER_K = max(DESIGN_DELTA_T_SET_K)
LOCATION_ONLY_LOAD_SPREAD_RATIO = (
    DESIGN_DELTA_T_UPPER_K / DESIGN_DELTA_T_LOWER_K
)

QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE = (
    "QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE"
)
REALIZED_LOCATION_STANDARD_ZONE_VERIFICATION_REQUIRED = (
    "REALIZED_LOCATION_STANDARD_ZONE_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class NationalDesignTemperatureEnvelope:
    outdoor_zone_values_c: tuple[float, ...]
    indoor_reference_c: float
    delta_t_values_k: tuple[float, ...]
    delta_t_lower_k: float
    delta_t_upper_k: float
    load_spread_ratio: float
    status: str
    evidence_status: str
    blocker: str | None
    warnings: tuple[str, ...]


def national_reference_programme_design_temperature() -> (
    NationalDesignTemperatureEnvelope
):
    return NationalDesignTemperatureEnvelope(
        outdoor_zone_values_c=CURRENT_STANDARD_ZONE_SET_C,
        indoor_reference_c=DESIGN_INDOOR_TEMPERATURE_C,
        delta_t_values_k=DESIGN_DELTA_T_SET_K,
        delta_t_lower_k=DESIGN_DELTA_T_LOWER_K,
        delta_t_upper_k=DESIGN_DELTA_T_UPPER_K,
        load_spread_ratio=LOCATION_ONLY_LOAD_SPREAD_RATIO,
        status=QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE,
        evidence_status="POL/DER/SCN",
        blocker=None,
        warnings=(
            "SET_VALUED_NATIONAL_INPUT_NOT_EXACT_SETTLEMENT_ZONE",
            "P86_PROJECT_LEVEL_FAIL_CLOSED_RESOLVER_REMAINS_AUTHORITATIVE",
            "SMALLER_SETTLEMENT_HIGH_ELEVATION_AND_LOCAL_ADJUSTMENTS_REMAIN_PROJECT_SPECIFIC",
        ),
    )


def design_load_bounds_from_heat_loss_coefficient(
    heat_loss_coefficient_w_per_k: float,
) -> tuple[float, float]:
    """Return national reference-programme design-load bounds in W.

    Heat loss is monotone in the positive design temperature difference, so the
    full current-standard zone set can be propagated without assigning a false
    point zone to a county/settlement-type population cell.
    """

    h = float(heat_loss_coefficient_w_per_k)
    if h < 0:
        raise ValueError("heat_loss_coefficient_w_per_k must be nonnegative")
    return (
        h * DESIGN_DELTA_T_LOWER_K,
        h * DESIGN_DELTA_T_UPPER_K,
    )


def p97_state() -> dict[str, object]:
    x = national_reference_programme_design_temperature()
    return {
        "zone_set_c": x.outdoor_zone_values_c,
        "indoor_reference_c": x.indoor_reference_c,
        "delta_t_set_k": x.delta_t_values_k,
        "delta_t_bound_k": (x.delta_t_lower_k, x.delta_t_upper_k),
        "location_only_load_spread_ratio": x.load_spread_ratio,
        "location_only_load_spread_percent": (x.load_spread_ratio - 1.0) * 100.0,
        "national_reference_programme_status": x.status,
        "national_mapping_blocker": None,
        "realized_claim_residual": (
            REALIZED_LOCATION_STANDARD_ZONE_VERIFICATION_REQUIRED
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "NATIONAL_ZONE_SET_IS_NOT_EXACT_SETTLEMENT_ZONE",
        "CURRENT_STANDARD_DOMAIN_IS_NOT_PROJECT_DESIGN_AUTHORITY",
        "SET_VALUED_PROPAGATION_IS_NOT_MOST_LIKELY_ZONE",
        "COUNTY_SETTLEMENT_TYPE_GRAIN_IS_NOT_SETTLEMENT_COORDINATE",
        "BASELINE_MAP_SCOPE_IS_NOT_AUTOMATIC_PROJECT_COMPLIANCE_OUTSIDE_SCOPE",
        "NATIONAL_REFERENCE_PROGRAMME_IS_NOT_REALIZED_PROJECT_ACCEPTANCE",
    )
