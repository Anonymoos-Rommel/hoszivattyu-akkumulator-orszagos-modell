"""B02-P103 current replaced-window U-quality evidence gate.

P102 narrowed the envelope-action uncertainty to a primary window blocker:
CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED.

P103 performs two bounded repairs.

1. Temporal target repair
   P80's 1.15 W/m2K timber/PVC window value is historical reference-retrofit
   calibration. The prospective current programme uses the current 9/2023 EKM
   wood/PVC >0.5 m2 facade glazed-opening requirement already admitted by P92:
   1.10 W/m2K.

2. Fail-closed replaced-window evidence gate
   Public Hungarian sources identify replacement status and, in the KSH survey
   instrument, replacement recency. They do not publish a national joint
   replacement-recency x frame-material x realized-Uw distribution.
   Therefore neither "window replaced" nor a legal epoch is promoted to
   realized current compliance.

BME's 2026 RBSM Type-5 example supplies an EPC-derived *full-window* U
calibration: the source data were filtered to 1.1..4.0 W/m2K and fitted with a
Normal distribution with mean 2.518 and sigma 0.670 W/m2K. This is valuable
current/Hungarian calibration, but it is not a replaced-window subset and is
not a national all-archetype population distribution.

Critical boundaries:

LEGAL_U_REQUIREMENT != VERIFIED_REALIZED_U
WINDOW_REPLACED_STATUS != REALIZED_U
KSH_REPLACEMENT_RECENCY != FRAME_MATERIAL
BME_TYPE5_FULL_WINDOW_U_DISTRIBUTION != REPLACED_WINDOW_U_DISTRIBUTION
TYPE5_EPC_CALIBRATION != NATIONAL_WINDOW_POPULATION_DISTRIBUTION
REGULATORY_LIMIT_MATCH != REALIZED_COMPLIANCE
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from modules.B02.hungarian_facade_opening_split import (
    CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
)


P80_HISTORICAL_REFERENCE_WINDOW_U_MAX_W_M2K = 1.15

OLD_GENERIC_WOOD_PVC_U_MAX_W_M2K = 1.60
OLD_GENERIC_METAL_U_MAX_W_M2K = 2.00
POST_2017_WOOD_PVC_U_MAX_W_M2K = 1.15
POST_2017_METAL_U_MAX_W_M2K = 1.40
CURRENT_WOOD_PVC_U_MAX_W_M2K = 1.10
CURRENT_METAL_U_MAX_W_M2K = 1.40

BME_TYPE5_WINDOW_U_FILTER_MIN_W_M2K = 1.10
BME_TYPE5_WINDOW_U_FILTER_MAX_W_M2K = 4.00
BME_TYPE5_WINDOW_U_MEAN_W_M2K = 2.518
BME_TYPE5_WINDOW_U_SIGMA_W_M2K = 0.670

P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR = 0.8278610299446981
P102_HP_ONLY_UPPER = 0.17213897005530188

P103_STATUS = "QUALIFIED_WINDOW_U_EVIDENCE_EPOCH_AND_FAIL_CLOSED_GATE"
CURRENT_REPLACED_WINDOW_U_UNRESOLVED = "CURRENT_REPLACED_WINDOW_U_UNRESOLVED"
REFERENCE_WINDOW_SATISFIED_VERIFIED_U = "REFERENCE_WINDOW_SATISFIED_VERIFIED_U"
REFERENCE_WINDOW_DEFICIT_VERIFIED_U = "REFERENCE_WINDOW_DEFICIT_VERIFIED_U"

PRIMARY_NEXT_RESIDUAL = "CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED"
REGULATORY_PROXY_RESIDUAL = (
    "PUBLIC_REPLACEMENT_RECENCY_X_FRAME_MATERIAL_CROSSWALK_REQUIRED_IF_REGULATORY_PROXY_USED"
)
WALL_SECONDARY_RESIDUAL = "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"

SUPPORTED_EPOCHS = (
    "PRE_2018_GENERIC",
    "POST_2017_ENERGY_SAVING",
    "CURRENT_9_2023",
)
SUPPORTED_FRAMES = ("WOOD_PVC", "METAL", "UNKNOWN")


@dataclass(frozen=True)
class WindowRegulatoryEpoch:
    epoch_id: str
    wood_pvc_u_max_w_m2k: float
    metal_u_max_w_m2k: float
    current_reference_wood_pvc_u_max_w_m2k: float
    wood_pvc_matches_current_reference: bool
    metal_matches_current_reference: bool
    status: str
    evidence_status: str


@dataclass(frozen=True)
class ReplacedWindowAssessment:
    replacement_status_confirmed: bool
    realized_uw_w_m2k: float | None
    frame_material: str | None
    regulatory_epoch: str | None
    state: str
    reference_u_max_w_m2k: float
    evidence_status: str
    regulatory_requirement_u_max_w_m2k: float | None
    regulatory_validation_state: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class Type5WindowCalibration:
    source_scope: str
    filter_min_u_w_m2k: float
    filter_max_u_w_m2k: float
    fitted_distribution: str
    mean_u_w_m2k: float
    sigma_u_w_m2k: float
    current_reference_z_from_mean: float
    status: str
    evidence_status: str
    forbidden_use: tuple[str, ...]


def regulatory_epochs() -> tuple[WindowRegulatoryEpoch, ...]:
    return (
        WindowRegulatoryEpoch(
            epoch_id="PRE_2018_GENERIC",
            wood_pvc_u_max_w_m2k=OLD_GENERIC_WOOD_PVC_U_MAX_W_M2K,
            metal_u_max_w_m2k=OLD_GENERIC_METAL_U_MAX_W_M2K,
            current_reference_wood_pvc_u_max_w_m2k=(
                CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K
            ),
            wood_pvc_matches_current_reference=False,
            metal_matches_current_reference=False,
            status="HISTORICAL_REGULATORY_REQUIREMENT",
            evidence_status="POL",
        ),
        WindowRegulatoryEpoch(
            epoch_id="POST_2017_ENERGY_SAVING",
            wood_pvc_u_max_w_m2k=POST_2017_WOOD_PVC_U_MAX_W_M2K,
            metal_u_max_w_m2k=POST_2017_METAL_U_MAX_W_M2K,
            current_reference_wood_pvc_u_max_w_m2k=(
                CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K
            ),
            wood_pvc_matches_current_reference=False,
            metal_matches_current_reference=False,
            status="HISTORICAL_STRICTER_RENOVATION_REQUIREMENT",
            evidence_status="POL",
        ),
        WindowRegulatoryEpoch(
            epoch_id="CURRENT_9_2023",
            wood_pvc_u_max_w_m2k=CURRENT_WOOD_PVC_U_MAX_W_M2K,
            metal_u_max_w_m2k=CURRENT_METAL_U_MAX_W_M2K,
            current_reference_wood_pvc_u_max_w_m2k=(
                CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K
            ),
            wood_pvc_matches_current_reference=True,
            metal_matches_current_reference=False,
            status="QUALIFIED_CURRENT_REGULATORY_REQUIREMENT",
            evidence_status="POL",
        ),
    )


def _epoch(epoch_id: str) -> WindowRegulatoryEpoch:
    for item in regulatory_epochs():
        if item.epoch_id == epoch_id:
            return item
    raise ValueError(f"unsupported regulatory_epoch {epoch_id}")


def assess_replaced_window(
    *,
    replacement_status_confirmed: bool,
    realized_uw_w_m2k: float | None = None,
    frame_material: str | None = None,
    regulatory_epoch: str | None = None,
    evidence_status: str = "Q",
) -> ReplacedWindowAssessment:
    """Fail-closed assessment against the current 1.10 W/m2K programme target.

    Only explicit realized Uw can prove SATISFIED or DEFICIT. Legal epochs and
    replacement labels are validation/proxy context only.
    """

    if frame_material is not None and frame_material not in SUPPORTED_FRAMES:
        raise ValueError(f"unsupported frame_material {frame_material}")
    if regulatory_epoch is not None and regulatory_epoch not in SUPPORTED_EPOCHS:
        raise ValueError(f"unsupported regulatory_epoch {regulatory_epoch}")

    if not replacement_status_confirmed:
        return ReplacedWindowAssessment(
            replacement_status_confirmed=False,
            realized_uw_w_m2k=None,
            frame_material=frame_material,
            regulatory_epoch=regulatory_epoch,
            state=CURRENT_REPLACED_WINDOW_U_UNRESOLVED,
            reference_u_max_w_m2k=CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
            evidence_status=evidence_status,
            regulatory_requirement_u_max_w_m2k=None,
            regulatory_validation_state="REPLACEMENT_STATUS_NOT_CONFIRMED",
            blockers=("REPLACEMENT_STATUS_REQUIRED_FOR_REPLACED_WINDOW_ROUTE",),
            warnings=(),
        )

    if realized_uw_w_m2k is not None:
        value = float(realized_uw_w_m2k)
        if not isfinite(value) or value <= 0.0:
            raise ValueError("realized_uw_w_m2k must be finite and positive")
        state = (
            REFERENCE_WINDOW_SATISFIED_VERIFIED_U
            if value <= CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K
            else REFERENCE_WINDOW_DEFICIT_VERIFIED_U
        )
        return ReplacedWindowAssessment(
            replacement_status_confirmed=True,
            realized_uw_w_m2k=value,
            frame_material=frame_material,
            regulatory_epoch=regulatory_epoch,
            state=state,
            reference_u_max_w_m2k=CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
            evidence_status=evidence_status,
            regulatory_requirement_u_max_w_m2k=None,
            regulatory_validation_state="REALIZED_UW_CONTROLS_CLASSIFICATION",
            blockers=(),
            warnings=(
                "REGULATORY_EPOCH_DOES_NOT_OVERRIDE_REALIZED_UW",
            ),
        )

    legal_limit: float | None = None
    validation = "NO_REGULATORY_PROXY_AVAILABLE"
    warnings: list[str] = []

    if regulatory_epoch is not None and frame_material is not None:
        ep = _epoch(regulatory_epoch)
        if frame_material == "WOOD_PVC":
            legal_limit = ep.wood_pvc_u_max_w_m2k
        elif frame_material == "METAL":
            legal_limit = ep.metal_u_max_w_m2k

        if frame_material == "UNKNOWN":
            validation = "FRAME_MATERIAL_UNKNOWN"
        elif legal_limit is not None:
            if (
                regulatory_epoch == "CURRENT_9_2023"
                and frame_material == "WOOD_PVC"
                and legal_limit <= CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K
            ):
                validation = (
                    "CURRENT_REGULATORY_REQUIREMENT_AT_REFERENCE_BUT_REALIZED_U_UNVERIFIED"
                )
            elif legal_limit > CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K:
                validation = (
                    "REGULATORY_LIMIT_LOOSER_THAN_CURRENT_REFERENCE"
                )
            else:
                validation = "REGULATORY_LIMIT_CONTEXT_ONLY"
    elif regulatory_epoch is not None:
        validation = "FRAME_MATERIAL_REQUIRED_FOR_REGULATORY_PROXY"
    elif frame_material is not None:
        validation = "REGULATORY_EPOCH_REQUIRED_FOR_REGULATORY_PROXY"

    if regulatory_epoch is not None or frame_material is not None:
        warnings.append("LEGAL_REQUIREMENT_IS_NOT_VERIFIED_REALIZED_U")

    return ReplacedWindowAssessment(
        replacement_status_confirmed=True,
        realized_uw_w_m2k=None,
        frame_material=frame_material,
        regulatory_epoch=regulatory_epoch,
        state=CURRENT_REPLACED_WINDOW_U_UNRESOLVED,
        reference_u_max_w_m2k=CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
        evidence_status=evidence_status,
        regulatory_requirement_u_max_w_m2k=legal_limit,
        regulatory_validation_state=validation,
        blockers=(PRIMARY_NEXT_RESIDUAL,),
        warnings=tuple(warnings),
    )


def type5_window_calibration() -> Type5WindowCalibration:
    z = (
        CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K - BME_TYPE5_WINDOW_U_MEAN_W_M2K
    ) / BME_TYPE5_WINDOW_U_SIGMA_W_M2K
    return Type5WindowCalibration(
        source_scope="BME_RBSM_TYPE5_FAMILY_HOUSE_FULL_EPC_WINDOW_SET",
        filter_min_u_w_m2k=BME_TYPE5_WINDOW_U_FILTER_MIN_W_M2K,
        filter_max_u_w_m2k=BME_TYPE5_WINDOW_U_FILTER_MAX_W_M2K,
        fitted_distribution="NORMAL",
        mean_u_w_m2k=BME_TYPE5_WINDOW_U_MEAN_W_M2K,
        sigma_u_w_m2k=BME_TYPE5_WINDOW_U_SIGMA_W_M2K,
        current_reference_z_from_mean=z,
        status="QUALIFIED_TYPE5_FULL_WINDOW_EPC_CALIBRATION_ONLY",
        evidence_status="DER",
        forbidden_use=(
            "REPLACED_WINDOW_SUBSET_DISTRIBUTION",
            "NATIONAL_WINDOW_POPULATION_DISTRIBUTION",
            "NATIONAL_REFERENCE_COMPLIANCE_SHARE",
        ),
    )


def p103_state() -> dict[str, object]:
    calibration = type5_window_calibration()
    return {
        "status": P103_STATUS,
        "p80_historical_reference_window_u_max_w_m2k": (
            P80_HISTORICAL_REFERENCE_WINDOW_U_MAX_W_M2K
        ),
        "current_reference_window_u_max_w_m2k": (
            CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K
        ),
        "window_target_temporal_repair": "RESOLVED_1_15_TO_1_10",
        "regulatory_epoch_count": len(regulatory_epochs()),
        "ksh_public_replacement_status_schema_available": True,
        "ksh_public_replacement_recency_schema_available": True,
        "ksh_public_recency_response_distribution_available": False,
        "public_frame_material_distribution_for_replaced_windows_available": False,
        "public_realized_replaced_window_uw_distribution_available": False,
        "bme_type5_full_window_calibration": calibration.__dict__,
        "national_replaced_window_reference_compliance_share_identified": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p103_numeric_national_action_tightening": False,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "secondary_residuals": (
            REGULATORY_PROXY_RESIDUAL,
            WALL_SECONDARY_RESIDUAL,
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "LEGAL_U_REQUIREMENT_IS_NOT_VERIFIED_REALIZED_U",
        "WINDOW_REPLACED_STATUS_IS_NOT_REALIZED_U",
        "KSH_REPLACEMENT_RECENCY_IS_NOT_FRAME_MATERIAL",
        "BME_TYPE5_FULL_WINDOW_U_DISTRIBUTION_IS_NOT_REPLACED_WINDOW_U_DISTRIBUTION",
        "TYPE5_EPC_CALIBRATION_IS_NOT_NATIONAL_WINDOW_POPULATION_DISTRIBUTION",
        "REGULATORY_LIMIT_MATCH_IS_NOT_REALIZED_COMPLIANCE",
    )
