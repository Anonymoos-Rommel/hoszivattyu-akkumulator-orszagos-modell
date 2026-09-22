"""B09-P3 dispatch/storage authority and national-generation layer.

P3 separates three concerns that were previously bundled together:

1. physical B08/B09 adequacy;
2. optional dispatch/storage scenario authority;
3. national versus regional observed-generation evidence.

HOUSEHOLD_B07_DISPATCH_ALREADY_IN_B08_LOAD != B09_SYSTEM_STORAGE
PHYSICAL_RESIDUAL_SURPLUS != DISPATCH_DECISION
NATIONAL_CONTROL_AREA_GENERATION != REGIONAL_DSO_COUNTY_GENERATION
PUBLIC_REPOSITORY_MATERIALIZATION != MODEL_USE_AUTHORITY

B09 does not invent a dispatch optimizer. The existing P1 adequacy ledger remains
the default physical baseline. Any later dispatch result requires an explicit,
separate authority and must not dispatch the same B07 household battery twice.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DispatchMode(str, Enum):
    NO_DISPATCH_BASELINE = "NO_DISPATCH_BASELINE"
    EXPLICIT_SYSTEM_STORAGE_SCHEDULE = "EXPLICIT_SYSTEM_STORAGE_SCHEDULE"


@dataclass(frozen=True)
class DispatchAdmission:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class NationalGenerationAdmission:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def assess_dispatch_authority(
    *,
    mode: DispatchMode,
    b07_household_storage_already_reflected_in_b08: bool,
    explicit_system_storage_asset_identity: bool = False,
    explicit_charge_discharge_schedule: bool = False,
    storage_power_energy_limits: bool = False,
    storage_soc_state_transition: bool = False,
    storage_efficiency_authority: bool = False,
    schedule_evidence_authority: bool = False,
) -> DispatchAdmission:
    """Assess dispatch authority without changing the P1 adequacy equations."""

    blockers: list[str] = []
    warnings: list[str] = []

    if not b07_household_storage_already_reflected_in_b08:
        blockers.append("B07_TO_B08_STORAGE_ACCOUNTING_BOUNDARY_REQUIRED")

    if mode == DispatchMode.NO_DISPATCH_BASELINE:
        return DispatchAdmission(
            status="QUALIFIED_PHYSICAL_ADEQUACY_WITHOUT_DISPATCH"
            if not blockers else "Q_DISPATCH_BOUNDARY",
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )

    if mode != DispatchMode.EXPLICIT_SYSTEM_STORAGE_SCHEDULE:
        raise ValueError(f"unsupported dispatch mode: {mode!r}")

    if not explicit_system_storage_asset_identity:
        blockers.append("SYSTEM_STORAGE_ASSET_IDENTITY_REQUIRED")
    if not explicit_charge_discharge_schedule:
        blockers.append("EXPLICIT_SYSTEM_STORAGE_SCHEDULE_REQUIRED")
    if not storage_power_energy_limits:
        blockers.append("SYSTEM_STORAGE_POWER_ENERGY_LIMITS_REQUIRED")
    if not storage_soc_state_transition:
        blockers.append("SYSTEM_STORAGE_SOC_STATE_TRANSITION_REQUIRED")
    if not storage_efficiency_authority:
        blockers.append("SYSTEM_STORAGE_EFFICIENCY_AUTHORITY_REQUIRED")
    if not schedule_evidence_authority:
        blockers.append("DISPATCH_SCHEDULE_EVIDENCE_AUTHORITY_REQUIRED")

    warnings.append("NO_MARKET_VALUE_OR_OPTIMALITY_CLAIM_FROM_PHYSICAL_DISPATCH")

    return DispatchAdmission(
        status=(
            "QUALIFIED_EXPLICIT_SYSTEM_STORAGE_DISPATCH"
            if not blockers else "Q_SYSTEM_STORAGE_DISPATCH"
        ),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def dispatch_boundaries() -> tuple[str, ...]:
    return (
        "B07_HOUSEHOLD_BATTERY_ACTION_MUST_NOT_BE_DISPATCHED_AGAIN_IN_B09",
        "B08_PHYSICAL_FLEXIBILITY_IS_CAPABILITY_NOT_DISPATCH",
        "B09_RESIDUAL_SURPLUS_IS_NOT_A_DISPATCH_INSTRUCTION",
        "SYSTEM_STORAGE_MUST_HAVE_SEPARATE_ASSET_SOC_AND_SCHEDULE_AUTHORITY",
        "PHYSICAL_DISPATCH_DOES_NOT_PROVE_MARKET_OR_MONETIZABLE_VALUE",
    )


def assess_national_generation_baseline(
    *,
    source_is_hungarian_control_area: bool,
    production_type_grain_explicit: bool,
    numeric_panel_available: bool,
    model_use_authorized: bool,
    provenance_complete: bool,
    expected_production_type_manifest_complete: bool,
    regional_mapping_available: bool,
) -> NationalGenerationAdmission:
    """Regional generation is intentionally not a national-baseline prerequisite."""

    blockers: list[str] = []
    warnings: list[str] = []

    if not source_is_hungarian_control_area:
        blockers.append("HUNGARIAN_CONTROL_AREA_GENERATION_SOURCE_REQUIRED")
    if not production_type_grain_explicit:
        blockers.append("SOURCE_NATIVE_PRODUCTION_TYPE_GRAIN_REQUIRED")
    if not numeric_panel_available:
        blockers.append("REAL_NUMERIC_GENERATION_PANEL_REQUIRED")
    if not model_use_authorized:
        blockers.append("SOURCE_SPECIFIC_MODEL_USE_AUTHORITY_REQUIRED")
    if not provenance_complete:
        blockers.append("COMPLETE_ACQUISITION_PROVENANCE_REQUIRED")
    if not expected_production_type_manifest_complete:
        blockers.append("EXPECTED_PRODUCTION_TYPE_MANIFEST_REQUIRED")
    if not regional_mapping_available:
        warnings.append("REGIONAL_DSO_COUNTY_GENERATION_REMAINS_SEPARATE_Q")

    return NationalGenerationAdmission(
        status=(
            "QUALIFIED_NATIONAL_CONTROL_AREA_GENERATION_BASELINE"
            if not blockers else "Q_NATIONAL_NUMERIC_GENERATION_BASELINE"
        ),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def regional_generation_boundary() -> tuple[str, ...]:
    return (
        "NATIONAL_CONTROL_AREA_GENERATION_CANNOT_BE_DOWNSCALED_TO_DSO_OR_COUNTY_WITHOUT_AUTHORITY",
        "PRODUCTION_TYPE_MIX_CANNOT_BE_SPATIALLY_SPLIT_WITHOUT_EVIDENCE",
        "REGIONAL_ADEQUACY_REQUIRES_LOAD_AND_GENERATION_AT_COMPATIBLE_GRAIN",
    )


def materialization_boundary() -> tuple[str, ...]:
    return (
        "MODEL_USE_AUTHORITY_IS_SEPARATE_FROM_PUBLIC_REPOSITORY_REPUBLICATION",
        "PUBLIC_REPOSITORY_RAW_SNAPSHOT_REQUIRES_REUSE_PERMISSION",
        "NO_REUSE_CLEARANCE_DOES_NOT_CREATE_A_REGIONAL_GENERATION_REQUIREMENT",
    )
