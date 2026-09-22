"""B02-P90 explicit reference-programme airtightness target.

P89 established measured airtightness response and Hungarian pressure-transfer
calibration, but correctly left the prospective national model without an
absolute post-retrofit airtightness state.

P90 closes that *prospective reference-programme* gap by explicitly adopting
the current Hungarian calculation method's GOOD_AIRTIGHTNESS class as a
scenario target, not as an observed or guaranteed future outcome.

Current-method target:
- one facade: n_filt = 0.03 1/h
- multiple facades / ventilation shaft: n_filt = 0.06 1/h

Where facade condition is unresolved nationally, P90 preserves the set-valued
0.03..0.06 target. It never inserts a midpoint.

Critical boundary:

REFERENCE_PROGRAMME_TARGET != OBSERVED_POST_RETROFIT_STATE
REFERENCE_PROGRAMME_TARGET != CURRENT_MFB_N50_REQUIREMENT
DESIGN_TARGET != REALIZED_COMMISSIONED_PERFORMANCE

The current MFB programme page is useful as a non-equivalence control: it
publishes programme measures and >=30% primary-energy saving, but does not
supply a building-level n50 target on the inspected public page. P90 therefore
labels the target SCN/POL-method-based, not an MFB eligibility requirement.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P87_SURFACE = ROOT / "data" / "processed" / "b02" / "p87_post_retrofit_ventilation_hvent_surface.csv"

ONE_FACADE = "ONE_FACADE"
MULTIPLE_FACADES_OR_VENTILATION_SHAFT = "MULTIPLE_FACADES_OR_VENTILATION_SHAFT"
UNRESOLVED_FACADE_CONDITION = "UNRESOLVED_FACADE_CONDITION"

GOOD_AIRTIGHTNESS_ONE_FACADE_NFILT_H = 0.03
GOOD_AIRTIGHTNESS_MULTI_OR_SHAFT_NFILT_H = 0.06

QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET = (
    "QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET"
)
REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED = (
    "REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class AirtightnessTargetBound:
    lower_h: float
    upper_h: float
    condition: str
    status: str
    evidence_status: str


@dataclass(frozen=True)
class ReferenceProgrammeVentilationTargetRow:
    surface_id: str
    wbl_period_code: str
    building_group: str
    heated_volume_lower_m3_per_dwelling: float
    heated_volume_upper_m3_per_dwelling: float
    n_filt_target_lower_h: float
    n_filt_target_upper_h: float
    h_vent_target_lower_w_per_k: float
    h_vent_target_upper_w_per_k: float
    q_vent_target_lower_kw: float
    q_vent_target_upper_kw: float
    status: str
    evidence_status: str


def reference_target_infiltration_bound(condition: str) -> AirtightnessTargetBound:
    if condition == ONE_FACADE:
        return AirtightnessTargetBound(
            lower_h=GOOD_AIRTIGHTNESS_ONE_FACADE_NFILT_H,
            upper_h=GOOD_AIRTIGHTNESS_ONE_FACADE_NFILT_H,
            condition=condition,
            status=QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET,
            evidence_status="POL/SCN",
        )
    if condition == MULTIPLE_FACADES_OR_VENTILATION_SHAFT:
        return AirtightnessTargetBound(
            lower_h=GOOD_AIRTIGHTNESS_MULTI_OR_SHAFT_NFILT_H,
            upper_h=GOOD_AIRTIGHTNESS_MULTI_OR_SHAFT_NFILT_H,
            condition=condition,
            status=QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET,
            evidence_status="POL/SCN",
        )
    if condition == UNRESOLVED_FACADE_CONDITION:
        return AirtightnessTargetBound(
            lower_h=GOOD_AIRTIGHTNESS_ONE_FACADE_NFILT_H,
            upper_h=GOOD_AIRTIGHTNESS_MULTI_OR_SHAFT_NFILT_H,
            condition=condition,
            status=QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET,
            evidence_status="POL/SCN",
        )
    raise ValueError(f"unsupported facade condition: {condition}")


@lru_cache(maxsize=None)
def reference_programme_ventilation_target_surface() -> tuple[
    ReferenceProgrammeVentilationTargetRow, ...
]:
    """Materialize the P87 good-airtightness surface as an explicit target.

    This function changes semantics, not numeric physics:
    P87 = sensitivity only.
    P90 = explicit prospective reference-programme target.

    No realized-outcome claim follows from this promotion.
    """

    with P87_SURFACE.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))

    if len(rows) != 14:
        raise ValueError(f"expected 14 P87 strata, got {len(rows)}")

    target = reference_target_infiltration_bound(UNRESOLVED_FACADE_CONDITION)
    out: list[ReferenceProgrammeVentilationTargetRow] = []

    for index, row in enumerate(rows, start=1):
        source_lo = float(row["good_airtightness_infiltration_lower_h"])
        source_hi = float(row["good_airtightness_infiltration_upper_h"])
        if source_lo != target.lower_h or source_hi != target.upper_h:
            raise ValueError("P87 good-airtightness bounds drifted")

        out.append(
            ReferenceProgrammeVentilationTargetRow(
                surface_id=f"B02-P90-T{index:02d}",
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                heated_volume_lower_m3_per_dwelling=float(
                    row["heated_volume_lower_m3_per_dwelling"]
                ),
                heated_volume_upper_m3_per_dwelling=float(
                    row["heated_volume_upper_m3_per_dwelling"]
                ),
                n_filt_target_lower_h=source_lo,
                n_filt_target_upper_h=source_hi,
                h_vent_target_lower_w_per_k=float(
                    row["good_airtightness_hvent_lower_w_per_k"]
                ),
                h_vent_target_upper_w_per_k=float(
                    row["good_airtightness_hvent_upper_w_per_k"]
                ),
                q_vent_target_lower_kw=float(
                    row["good_airtightness_qvent_lower_kw"]
                ),
                q_vent_target_upper_kw=float(
                    row["good_airtightness_qvent_upper_kw"]
                ),
                status=QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET,
                evidence_status="POL/DER/SCN",
            )
        )

    return tuple(out)


def reference_programme_target_state() -> dict[str, object]:
    rows = reference_programme_ventilation_target_surface()
    return {
        "stratum_count": len(rows),
        "n_filt_target_lower_h": min(row.n_filt_target_lower_h for row in rows),
        "n_filt_target_upper_h": max(row.n_filt_target_upper_h for row in rows),
        "h_vent_target_global_lower_w_per_k": min(
            row.h_vent_target_lower_w_per_k for row in rows
        ),
        "h_vent_target_global_upper_w_per_k": max(
            row.h_vent_target_upper_w_per_k for row in rows
        ),
        "q_vent_target_global_lower_kw": min(
            row.q_vent_target_lower_kw for row in rows
        ),
        "q_vent_target_global_upper_kw": max(
            row.q_vent_target_upper_kw for row in rows
        ),
        "prospective_reference_programme_status": (
            QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET
        ),
        "prospective_reference_programme_blocker": None,
        "realized_claim_residual": REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "REFERENCE_PROGRAMME_TARGET_IS_NOT_OBSERVED_POST_RETROFIT_STATE",
        "REFERENCE_PROGRAMME_TARGET_IS_NOT_CURRENT_MFB_N50_REQUIREMENT",
        "GOOD_AIRTIGHTNESS_METHOD_CLASS_IS_NOT_BLOWER_DOOR_N50",
        "UNRESOLVED_FACADE_CONDITION_REMAINS_SET_VALUED_003_TO_006",
        "DESIGN_TARGET_IS_NOT_REALIZED_COMMISSIONED_PERFORMANCE",
        "REALIZED_CLAIM_REQUIRES_PROJECT_OR_MEASUREMENT_EVIDENCE",
    )
