"""B02-P65 set-identified heat-emitter population model.

The model keeps overlapping emitter memberships explicit.  It intentionally
does not force a mutually exclusive radiator/surface/convector partition where
the evidence does not provide one.

Evidence constraints currently admitted:
- EHI 2024 Hungary surface-heating/cooling presence: [0.33, 0.66] (DER band);
- P39 calibrated primary gas-convector share: 0.233 (ASS model target).

KSH topology shares are validation controls only and are not converted into
emitter subtype shares.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose


SURFACE_LOWER = 0.33
SURFACE_UPPER = 0.66
PRIMARY_GAS_CONVECTOR_SHARE = 0.233

# KSH Statistical Yearbook 2022, table 3.2.6; 2021+ survey topology controls.
KSH_DISTRICT_HEATING_SHARE = 0.160
KSH_BUILDING_CENTRAL_SHARE = 0.063
KSH_ONE_DWELLING_CENTRAL_SHARE = 0.484
KSH_INDIVIDUAL_FIXED_SHARE = 0.289
KSH_CENTRAL_OR_DISTRICT_CONTROL = (
    KSH_DISTRICT_HEATING_SHARE
    + KSH_BUILDING_CENTRAL_SHARE
    + KSH_ONE_DWELLING_CENTRAL_SHARE
)

EVIDENCE_STATUS = "BOUNDED_MULTI_SOURCE"
MODEL_STATUS = "CANDIDATE"


@dataclass(frozen=True)
class Interval:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.lower <= self.upper <= 1.0):
            raise ValueError("interval must satisfy 0 <= lower <= upper <= 1")


@dataclass(frozen=True)
class MembershipScenario:
    """One admissible multi-label national membership scenario.

    Shares are membership probabilities, not mutually exclusive stock bins.
    """

    surface_presence: float
    radiator_presence: float
    surface_radiator_overlap: float
    other_emitter_presence: float
    primary_gas_convector_share: float = PRIMARY_GAS_CONVECTOR_SHARE


@dataclass(frozen=True)
class ScenarioDiagnostics:
    surface_only: float
    radiator_only: float
    surface_or_radiator_union: float
    minimum_overlap_by_frechet: float
    maximum_overlap_by_frechet: float
    ksh_fixed_minus_primary_convector_pp: float


@dataclass(frozen=True)
class IdentifiedSet:
    surface_presence: Interval
    primary_gas_convector_share: Interval
    radiator_presence: Interval
    other_emitter_presence: Interval
    overlap_rule: str
    evidence_status: str
    model_status: str


def identified_set() -> IdentifiedSet:
    """Return currently identified marginal bounds.

    Radiator and other-emitter prevalence remain unbounded by direct numeric
    national evidence.  They are deliberately [0,1], with radiator/surface
    overlap constrained relationally by Frechet bounds in scenario validation.
    """

    return IdentifiedSet(
        surface_presence=Interval(SURFACE_LOWER, SURFACE_UPPER),
        primary_gas_convector_share=Interval(
            PRIMARY_GAS_CONVECTOR_SHARE, PRIMARY_GAS_CONVECTOR_SHARE
        ),
        radiator_presence=Interval(0.0, 1.0),
        other_emitter_presence=Interval(0.0, 1.0),
        overlap_rule="FRECHET_SURFACE_RADIATOR",
        evidence_status=EVIDENCE_STATUS,
        model_status=MODEL_STATUS,
    )


def frechet_overlap_bounds(a: float, b: float) -> Interval:
    """Sharp overlap bounds for two memberships with marginals a and b."""

    if not (0.0 <= a <= 1.0 and 0.0 <= b <= 1.0):
        raise ValueError("membership shares must lie in [0,1]")
    return Interval(max(0.0, a + b - 1.0), min(a, b))


def validate_scenario(scenario: MembershipScenario) -> ScenarioDiagnostics:
    """Validate one scenario against current admitted evidence.

    This function does not assert independence between memberships.
    """

    for value in (
        scenario.surface_presence,
        scenario.radiator_presence,
        scenario.surface_radiator_overlap,
        scenario.other_emitter_presence,
        scenario.primary_gas_convector_share,
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError("membership shares must lie in [0,1]")

    if not SURFACE_LOWER <= scenario.surface_presence <= SURFACE_UPPER:
        raise ValueError("surface presence outside EHI Hungary validation band")

    if not isclose(
        scenario.primary_gas_convector_share,
        PRIMARY_GAS_CONVECTOR_SHARE,
        abs_tol=1e-12,
    ):
        raise ValueError("primary gas-convector share must retain P39 target")

    overlap = frechet_overlap_bounds(
        scenario.surface_presence, scenario.radiator_presence
    )
    if not overlap.lower - 1e-12 <= scenario.surface_radiator_overlap <= overlap.upper + 1e-12:
        raise ValueError("surface/radiator overlap violates Frechet bounds")

    surface_only = scenario.surface_presence - scenario.surface_radiator_overlap
    radiator_only = scenario.radiator_presence - scenario.surface_radiator_overlap
    union = (
        scenario.surface_presence
        + scenario.radiator_presence
        - scenario.surface_radiator_overlap
    )

    if surface_only < -1e-12 or radiator_only < -1e-12 or union > 1.0 + 1e-12:
        raise ValueError("invalid surface/radiator membership decomposition")

    return ScenarioDiagnostics(
        surface_only=max(0.0, surface_only),
        radiator_only=max(0.0, radiator_only),
        surface_or_radiator_union=min(1.0, union),
        minimum_overlap_by_frechet=overlap.lower,
        maximum_overlap_by_frechet=overlap.upper,
        ksh_fixed_minus_primary_convector_pp=(
            KSH_INDIVIDUAL_FIXED_SHARE - PRIMARY_GAS_CONVECTOR_SHARE
        )
        * 100.0,
    )


def ksh_topology_controls() -> dict[str, float]:
    """Return source-native KSH survey topology controls.

    These values are validation controls only.  They may not be re-labelled as
    radiator, surface-heating, or other emitter shares.
    """

    return {
        "district_heating": KSH_DISTRICT_HEATING_SHARE,
        "building_central": KSH_BUILDING_CENTRAL_SHARE,
        "one_dwelling_central": KSH_ONE_DWELLING_CENTRAL_SHARE,
        "individual_fixed": KSH_INDIVIDUAL_FIXED_SHARE,
        "central_or_district_control": KSH_CENTRAL_OR_DISTRICT_CONTROL,
    }
