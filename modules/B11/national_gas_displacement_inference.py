"""B11-P6 national gas-displacement inference layer.

P6 applies the project-wide population-inference policy to gas displacement
without weakening exact participant, gas-quality-point or billing claims.

NATIONAL GAS QUALITY DISTRIBUTION != PARTICIPANT GAS-QUALITY POINT
NATIONAL APPLIANCE CLASS MIX != SEASONAL EFFICIENCY DISTRIBUTION
COUNTY GAS SALES CONTROL != PARTICIPANT GAS VOLUME
PUBLIC REPOSITORY MATERIALIZATION != MODEL USABILITY

The national/programme layer may use representative or region-weighted gas
quality and appliance-efficiency distributions with explicit calibration and
uncertainty. Exact participant/point claims remain fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass


NATIONAL_GAS_DISPLACEMENT_INFERENCE = "NATIONAL_GAS_DISPLACEMENT_INFERENCE"
EXACT_PARTICIPANT_GAS_AUTHORITY = "EXACT_PARTICIPANT_GAS_AUTHORITY"
SOURCE_ACCESS_AND_PROVENANCE = "SOURCE_ACCESS_AND_PROVENANCE"

Q_NATIONAL_GAS_DISPLACEMENT = "Q_NATIONAL_GAS_DISPLACEMENT"
QUALIFIED_NATIONAL_BOUNDED_GAS_DISPLACEMENT = (
    "QUALIFIED_NATIONAL_BOUNDED_GAS_DISPLACEMENT"
)

TARKI_REKK_GAS_HEATING_SAMPLE_N = 657
TARKI_REKK_APPLIANCE_SHARES = (
    ("TRADITIONAL_GAS_BOILER", 0.2666),
    ("CONDENSING_GAS_BOILER", 0.3273),
    ("GAS_CONVECTOR", 0.4061),
)


@dataclass(frozen=True)
class ApplianceClassShare:
    appliance_class: str
    share: float
    evidence_status: str
    source_ref: str


@dataclass(frozen=True)
class BlockerRepair:
    legacy_requirement: str
    replacement: str
    plane: str
    status: str
    exact_claim_boundary: str


@dataclass(frozen=True)
class NationalGasDisplacementAdmission:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


_REPAIRS = (
    BlockerRepair(
        "EXACT_PROGRAMME_PARTICIPANT_TO_GAS_QUALITY_POINT_MAPPING_REQUIRED",
        "DEFENSIBLE_REGION_OR_POINT_WEIGHTED_GAS_QUALITY_DISTRIBUTION_REQUIRED",
        NATIONAL_GAS_DISPLACEMENT_INFERENCE,
        "RETIRED_AS_NATIONAL_BCM_PREREQUISITE",
        "PARTICIPANT_OR_BILLING_POINT_CLAIM_STILL_REQUIRES_EXACT_MAPPING",
    ),
    BlockerRepair(
        "PROGRAMME_ALIGNED_EXACT_POINT_GCV_LHV_PANEL_REQUIRED",
        "TEMPORALLY_ALIGNED_BOUNDED_GCV_LHV_DISTRIBUTION_REQUIRED",
        NATIONAL_GAS_DISPLACEMENT_INFERENCE,
        "REFRAMED_AS_POPULATION_INFERENCE_REQUIREMENT",
        "SPECIFIC_POINT_GCV_LHV_CLAIM_REQUIRES_EXACT_POINT_PERIOD_EVIDENCE",
    ),
    BlockerRepair(
        "PUBLIC_REPOSITORY_POINT_VALUE_MATERIALIZATION_REQUIRED",
        "SOURCE_ACCESS_PROVENANCE_AND_MODEL_USE_AUTHORITY_REQUIRED",
        SOURCE_ACCESS_AND_PROVENANCE,
        "RETIRED_AS_PUBLIC_REPOSITORY_PREREQUISITE",
        "RAW_REPUBLICATION_STILL_REQUIRES_REUSE_PERMISSION",
    ),
    BlockerRepair(
        "SINGLE_NATIONAL_SEASONAL_GAS_EFFICIENCY_REQUIRED",
        "APPLIANCE_CLASS_WEIGHTED_BOUNDED_SEASONAL_EFFICIENCY_REQUIRED",
        NATIONAL_GAS_DISPLACEMENT_INFERENCE,
        "REFRAMED_AS_POPULATION_INFERENCE_REQUIREMENT",
        "SPECIFIC_APPLIANCE_FUEL_VOLUME_REQUIRES_APPLICABLE_EFFICIENCY_EVIDENCE",
    ),
)


def appliance_class_population_control() -> tuple[ApplianceClassShare, ...]:
    """Return the existing weighted Hungarian gas-heating appliance mix control."""
    source = "SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022"
    rows = tuple(
        ApplianceClassShare(
            appliance_class=name,
            share=share,
            evidence_status="OBS_WEIGHTED_SURVEY_CONTROL",
            source_ref=source,
        )
        for name, share in TARKI_REKK_APPLIANCE_SHARES
    )
    total = sum(row.share for row in rows)
    if abs(total - 1.0) > 1e-9:
        raise ValueError("appliance shares must sum to one")
    return rows


def blocker_repairs() -> tuple[BlockerRepair, ...]:
    return _REPAIRS


def repaired_requirement(legacy_requirement: str) -> BlockerRepair:
    for repair in _REPAIRS:
        if repair.legacy_requirement == legacy_requirement:
            return repair
    raise KeyError(legacy_requirement)


def assess_national_gas_displacement(
    *,
    gas_population_bound: bool,
    useful_heat_distribution: bool,
    appliance_class_weights: bool,
    class_specific_efficiency_bounds: bool,
    temporally_aligned_gas_quality_distribution: bool,
    multi_fuel_decomposition: bool,
    dhw_cooking_boundary: bool,
    rebound_boundary: bool,
    calibration_to_observed_gas_sales: bool,
    uncertainty_explicit: bool,
) -> NationalGasDisplacementAdmission:
    blockers: list[str] = []
    warnings: list[str] = []

    if not gas_population_bound:
        blockers.append("DEFENSIBLE_GAS_HEATING_POPULATION_REQUIRED")
    if not useful_heat_distribution:
        blockers.append("DEFENSIBLE_USEFUL_SPACE_HEAT_DISTRIBUTION_REQUIRED")
    if not appliance_class_weights:
        blockers.append("GAS_APPLIANCE_CLASS_WEIGHTS_REQUIRED")
    if not class_specific_efficiency_bounds:
        blockers.append(
            "APPLIANCE_CLASS_WEIGHTED_BOUNDED_SEASONAL_EFFICIENCY_REQUIRED"
        )
    if not temporally_aligned_gas_quality_distribution:
        blockers.append("TEMPORALLY_ALIGNED_BOUNDED_GCV_LHV_DISTRIBUTION_REQUIRED")
    if not multi_fuel_decomposition:
        blockers.append("MULTI_FUEL_GAS_SHARE_DECOMPOSITION_REQUIRED")
    if not dhw_cooking_boundary:
        blockers.append("DHW_COOKING_GAS_END_USE_BOUNDARY_REQUIRED")
    if not rebound_boundary:
        blockers.append("POST_RETROFIT_REBOUND_BOUND_REQUIRED")
    if not calibration_to_observed_gas_sales:
        blockers.append("OBSERVED_GAS_SALES_CALIBRATION_REQUIRED")
    if not uncertainty_explicit:
        blockers.append("GAS_DISPLACEMENT_UNCERTAINTY_REQUIRED")

    status = (
        QUALIFIED_NATIONAL_BOUNDED_GAS_DISPLACEMENT
        if not blockers
        else Q_NATIONAL_GAS_DISPLACEMENT
    )

    if appliance_class_weights and not class_specific_efficiency_bounds:
        warnings.append("APPLIANCE_MIX_AVAILABLE_BUT_EFFICIENCY_BOUNDS_MISSING")

    return NationalGasDisplacementAdmission(
        status=status,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def exact_claim_boundary() -> tuple[str, ...]:
    return (
        "NATIONAL_BCM_ESTIMATE_CANNOT_AUTHORIZE_A_PARTICIPANT_BILLING_CLAIM",
        "SPECIFIC_PARTICIPANT_GAS_QUALITY_REQUIRES_EXACT_POINT_MAPPING",
        "SPECIFIC_POINT_GCV_LHV_REQUIRES_EXACT_POINT_PERIOD_EVIDENCE",
        "SPECIFIC_APPLIANCE_FUEL_VOLUME_REQUIRES_APPLICABLE_EFFICIENCY_EVIDENCE",
    )
