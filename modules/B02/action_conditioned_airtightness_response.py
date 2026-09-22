"""B02-P89 action-conditioned airtightness response and pressure-transfer contract.

P88 left one ventilation residual: action-conditioned post-retrofit infiltration.
P89 admits measured pressure-test evidence without collapsing unlike metrics:

- n50 / ACH50: air changes per hour at 50 Pa;
- q50 / AP50: air permeability per envelope area at 50 Pa;
- n4: air changes per hour at a 4 Pa pressure condition;
- current Hungarian n_filt: calculation-method infiltration term.

These are not interchangeable without an explicit transfer/crosswalk.

P89 therefore makes two bounded operations executable:

1. apply a measured relative airtightness response to a same-metric baseline;
2. transfer an n50 upper bound to a 4 Pa ACH upper bound using the
   source-native Hungarian pressure-law exponent range.

It does not invent a Hungarian national post-retrofit n50/q50 distribution.

Critical boundaries:

Q50 != N50
PRESSURE_TEST_AIRTIGHTNESS != NATURAL_INFILTRATION
TYPE_A_N50_INCLUDES_INTENTIONAL_OPENINGS
FOREIGN_RETROFIT_RESPONSE != HUNGARIAN_POPULATION_WEIGHT
WINDOW_REPLACEMENT_RESPONSE != WHOLE_HOUSE_DEEP_RETROFIT_RESPONSE
IMMEDIATE_POST_RETROFIT_AIRTIGHTNESS != LONG_TERM_DURABILITY
"""

from __future__ import annotations

from dataclasses import dataclass


HUNGARIAN_PTE_PRESSURE_REFERENCE_PA = 50.0
HUNGARIAN_PTE_NATURAL_REFERENCE_PA = 4.0

# Source-native exponent range published for seven Hungarian traditional
# brickwork examples in the PTE/AIVC field study.
HUNGARIAN_PTE_FLOW_EXPONENT_MIN = 0.566
HUNGARIAN_PTE_FLOW_EXPONENT_MAX = 0.689

# Same-source observed/calculated examples. These are calibration examples,
# not population bounds.
HUNGARIAN_PTE_EXAMPLE_N50_MIN_H = 1.86
HUNGARIAN_PTE_EXAMPLE_N50_MAX_H = 8.28
HUNGARIAN_PTE_EXAMPLE_N4_MIN_H = 0.36
HUNGARIAN_PTE_EXAMPLE_N4_MAX_H = 1.52

# Window-only paired field study: 20 occupied homes / 40 blower-door tests.
# Search-visible source text is internally inconsistent on the minimum
# improvement (0.3% in highlights, 0.5% in abstract), so P89 deliberately
# does not mint a minimum effect. Mean and maximum are consistent.
WINDOW_REPLACEMENT_PAIRED_HOMES = 20
WINDOW_REPLACEMENT_MEAN_N50_REDUCTION_FRACTION = 0.061
WINDOW_REPLACEMENT_MAX_N50_REDUCTION_FRACTION = 0.193

# Retrofit for the Future pressure-test cohort.
RFTF_PAIRED_PROPERTIES = 87
RFTF_PRE_Q50_MODAL_M3_H_M2 = 8.0
RFTF_POST_Q50_MODAL_M3_H_M2 = 4.0
RFTF_PRE_Q50_LT5_COUNT = 2
RFTF_POST_Q50_LT5_COUNT = 39
RFTF_POST_Q50_LT1_COUNT = 5

# UK long-term revisit evidence.
UK_DURABILITY_REVISIT_DWELLINGS = 10
UK_DURABILITY_PAIRED_PRE_POST_CASES = 4
UK_DURABILITY_LESS_AIRTIGHT_AFTER_DECADE_COUNT = 7
UK_DURABILITY_MEAN_Q50_INCREASE_M3_H_M2 = 0.52
UK_DURABILITY_MAX_Q50_INCREASE_M3_H_M2 = 2.58
UK_DURABILITY_MIN_Q50_CHANGE_M3_H_M2 = -1.41


@dataclass(frozen=True)
class PressureTransferBound:
    n50_upper_h: float
    exponent_min: float
    exponent_max: float
    n4_factor_lower: float
    n4_factor_upper: float
    n4_upper_lower_h: float
    n4_upper_upper_h: float
    status: str
    evidence_status: str


@dataclass(frozen=True)
class RelativeResponse:
    baseline_value: float
    reduction_fraction: float
    post_value: float
    metric: str
    status: str


def apply_relative_airtightness_reduction(
    *,
    baseline_value: float,
    reduction_fraction: float,
    metric: str,
) -> RelativeResponse:
    """Apply a same-metric measured/scenario relative reduction.

    A q50 reduction stays q50. An n50 reduction stays n50. Cross-metric
    conversion is forbidden here.
    """

    baseline = float(baseline_value)
    reduction = float(reduction_fraction)
    if baseline < 0:
        raise ValueError("baseline_value must be nonnegative")
    if not 0.0 <= reduction <= 1.0:
        raise ValueError("reduction_fraction must be within [0, 1]")
    if metric not in {"n50_1_per_h", "q50_m3_h_m2"}:
        raise ValueError("unsupported airtightness metric")
    return RelativeResponse(
        baseline_value=baseline,
        reduction_fraction=reduction,
        post_value=baseline * (1.0 - reduction),
        metric=metric,
        status="SAME_METRIC_RELATIVE_RESPONSE",
    )


def pressure_transfer_factor(
    *,
    pressure_pa: float,
    reference_pressure_pa: float,
    flow_exponent: float,
) -> float:
    pressure = float(pressure_pa)
    reference = float(reference_pressure_pa)
    exponent = float(flow_exponent)
    if pressure <= 0 or reference <= 0:
        raise ValueError("pressures must be positive")
    if pressure > reference:
        raise ValueError("pressure_pa must not exceed reference_pressure_pa")
    if not 0.0 < exponent <= 1.0:
        raise ValueError("flow_exponent must be within (0, 1]")
    return (pressure / reference) ** exponent


def hungarian_n4_bound_from_n50_upper(*, n50_upper_h: float) -> PressureTransferBound:
    """Transfer an explicit n50 upper bound to a Hungarian 4 Pa ACH bound.

    This is a pressure-law calibration, not a direct conversion to the current
    Hungarian n_filt method category. The source study's Type-A measurements
    leave intentional openings active, so the result remains a calibration/
    scenario bound unless a compatible Type-B/project measurement is supplied.
    """

    n50_upper = float(n50_upper_h)
    if n50_upper < 0:
        raise ValueError("n50_upper_h must be nonnegative")

    factor_lower = pressure_transfer_factor(
        pressure_pa=HUNGARIAN_PTE_NATURAL_REFERENCE_PA,
        reference_pressure_pa=HUNGARIAN_PTE_PRESSURE_REFERENCE_PA,
        flow_exponent=HUNGARIAN_PTE_FLOW_EXPONENT_MAX,
    )
    factor_upper = pressure_transfer_factor(
        pressure_pa=HUNGARIAN_PTE_NATURAL_REFERENCE_PA,
        reference_pressure_pa=HUNGARIAN_PTE_PRESSURE_REFERENCE_PA,
        flow_exponent=HUNGARIAN_PTE_FLOW_EXPONENT_MIN,
    )
    return PressureTransferBound(
        n50_upper_h=n50_upper,
        exponent_min=HUNGARIAN_PTE_FLOW_EXPONENT_MIN,
        exponent_max=HUNGARIAN_PTE_FLOW_EXPONENT_MAX,
        n4_factor_lower=factor_lower,
        n4_factor_upper=factor_upper,
        n4_upper_lower_h=n50_upper * factor_lower,
        n4_upper_upper_h=n50_upper * factor_upper,
        status="HUNGARIAN_4PA_PRESSURE_TRANSFER_CALIBRATION",
        evidence_status="OBS/DER",
    )


def p89_state() -> dict[str, object]:
    factor = hungarian_n4_bound_from_n50_upper(n50_upper_h=1.0)
    return {
        "hungarian_field_locations": 33,
        "hungarian_example_count": 7,
        "hungarian_n50_example_range_h": (
            HUNGARIAN_PTE_EXAMPLE_N50_MIN_H,
            HUNGARIAN_PTE_EXAMPLE_N50_MAX_H,
        ),
        "hungarian_n4_example_range_h": (
            HUNGARIAN_PTE_EXAMPLE_N4_MIN_H,
            HUNGARIAN_PTE_EXAMPLE_N4_MAX_H,
        ),
        "hungarian_n50_to_n4_factor_range": (
            factor.n4_factor_lower,
            factor.n4_factor_upper,
        ),
        "window_replacement_paired_homes": WINDOW_REPLACEMENT_PAIRED_HOMES,
        "window_replacement_mean_n50_reduction_fraction": (
            WINDOW_REPLACEMENT_MEAN_N50_REDUCTION_FRACTION
        ),
        "window_replacement_max_n50_reduction_fraction": (
            WINDOW_REPLACEMENT_MAX_N50_REDUCTION_FRACTION
        ),
        "whole_house_paired_properties": RFTF_PAIRED_PROPERTIES,
        "response_engine_status": "PARTIAL_RESOLVED_MEASURED_AIRTIGHTNESS_RESPONSE",
        "current_residual": (
            "POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED"
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "Q50_IS_NOT_N50",
        "PRESSURE_TEST_AIRTIGHTNESS_IS_NOT_NATURAL_INFILTRATION",
        "TYPE_A_N50_INCLUDES_INTENTIONAL_OPENINGS",
        "FOREIGN_RETROFIT_RESPONSE_IS_NOT_HUNGARIAN_POPULATION_WEIGHT",
        "WINDOW_REPLACEMENT_RESPONSE_IS_NOT_WHOLE_HOUSE_RESPONSE",
        "RELATIVE_RESPONSE_REQUIRES_SAME_METRIC_BASELINE",
        "IMMEDIATE_POST_RETROFIT_AIRTIGHTNESS_IS_NOT_LONG_TERM_DURABILITY",
        "N4_PRESSURE_TRANSFER_IS_NOT_CURRENT_METHOD_NFILT_CLASSIFICATION",
    )
