"""B02-P68 Hungarian reweighting and set-valued EoH-to-P66 crosswalk.

P67 admitted a foreign physical-response envelope and a Hungarian official cost
ceiling but deliberately did not transfer UK frequencies to Hungary.

P68 closes the *computational* P21 reweighting gap by using the already-approved
P21 FAMILY_HOUSE / MULTI_DWELLING population totals. It also narrows the EoH
action crosswalk without inventing unsupported action subtypes.

Canonical boundaries:

P21 CALIBRATED BUILDING-TYPE WEIGHTS -> HUNGARIAN REWEIGHTING AUTHORITY
FOREIGN RESPONSE INTERVAL -> TRANSFER SENSITIVITY, NOT HUNGARIAN OBSERVATION
POSITIVE EMITTER-MEASURE COUNT -> NON-KEEP EMITTER INTERVENTION
POSITIVE EMITTER-MEASURE COUNT != UPSIZE/CHANGE/ADD/REPLACE SUBTYPE
ZERO EMITTER-MEASURE COUNT != PROVEN KEEP
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage


ROOT = Path(__file__).resolve().parents[2]
P67_RESPONSE = ROOT / "registry" / "b02_p67_eoh_response_envelope.csv"

ACTIONS = ("KEEP", "UPSIZE", "CHANGE", "ADD", "REPLACE")
NON_KEEP_ACTIONS = ("UPSIZE", "CHANGE", "ADD", "REPLACE")
EXPECTED_OCCUPIED = 4_008_541
EXPECTED_FAMILY = 2_423_136
EXPECTED_MULTI = 1_585_405


@dataclass(frozen=True)
class P21BuildingTypeWeights:
    occupied_dwellings: int
    family_dwellings: int
    multi_dwellings: int
    family_weight: float
    multi_weight: float
    evidence_status: str = "ASS"


@dataclass(frozen=True)
class ResponseInterval:
    lower: float
    upper: float


@dataclass(frozen=True)
class WeightedResponseEnvelope:
    metric: str
    lower: float
    upper: float
    evidence_status: str
    use: str


@dataclass(frozen=True)
class ActionCrosswalk:
    status: str
    allowed_actions: tuple[str, ...]
    blockers: tuple[str, ...]
    source_semantics: str


def _check_interval(interval: ResponseInterval, name: str) -> None:
    if not isfinite(interval.lower) or not isfinite(interval.upper):
        raise ValueError(f"{name} bounds must be finite")
    if interval.lower > interval.upper:
        raise ValueError(f"{name} interval is inverted")


def p21_building_type_weights() -> P21BuildingTypeWeights:
    _rows, summary = build_calibrated_linkage()
    if summary.occupied_dwellings != EXPECTED_OCCUPIED:
        raise ValueError("P21 occupied total drift")
    if summary.family_target_dwellings != EXPECTED_FAMILY:
        raise ValueError("P21 family target drift")
    if summary.multi_target_dwellings != EXPECTED_MULTI:
        raise ValueError("P21 multi target drift")
    if summary.family_target_dwellings + summary.multi_target_dwellings != EXPECTED_OCCUPIED:
        raise ValueError("P21 building-type targets do not reconcile")

    return P21BuildingTypeWeights(
        occupied_dwellings=summary.occupied_dwellings,
        family_dwellings=summary.family_target_dwellings,
        multi_dwellings=summary.multi_target_dwellings,
        family_weight=summary.family_target_dwellings / summary.occupied_dwellings,
        multi_weight=summary.multi_target_dwellings / summary.occupied_dwellings,
    )


def reweight_building_type_intervals(
    *,
    metric: str,
    family: ResponseInterval,
    multi: ResponseInterval,
) -> WeightedResponseEnvelope:
    """Apply exact P21 national building-type weights to bounded responses.

    This is a transfer-sensitivity calculation. The P21 weights are Hungarian,
    but the supplied response intervals may be foreign. The result therefore
    remains ASS and must not be promoted to a Hungarian observed distribution.
    """

    _check_interval(family, "family")
    _check_interval(multi, "multi")
    w = p21_building_type_weights()

    return WeightedResponseEnvelope(
        metric=metric,
        lower=w.family_weight * family.lower + w.multi_weight * multi.lower,
        upper=w.family_weight * family.upper + w.multi_weight * multi.upper,
        evidence_status="ASS",
        use="HUNGARIAN_WEIGHTED_FOREIGN_RESPONSE_SENSITIVITY",
    )


def crosswalk_eoh_emitter_measure_count(count: float) -> ActionCrosswalk:
    """Map only what the source-native emitter-measure count actually proves."""

    if not isfinite(float(count)) or count < 0:
        return ActionCrosswalk(
            status="Q",
            allowed_actions=(),
            blockers=("EMITTER_MEASURE_COUNT_INVALID",),
            source_semantics="INVALID",
        )

    if count > 0:
        return ActionCrosswalk(
            status="SET_IDENTIFIED_NON_KEEP",
            allowed_actions=NON_KEEP_ACTIONS,
            blockers=("P66_ACTION_SUBTYPE_NOT_IDENTIFIED",),
            source_semantics="POSITIVE_EMITTER_MEASURE_RECORDED",
        )

    return ActionCrosswalk(
        status="UNINFORMATIVE_SET",
        allowed_actions=ACTIONS,
        blockers=("ZERO_MEASURE_DOES_NOT_PROVE_KEEP",),
        source_semantics="NO_EMITTER_MEASURE_RECORDED",
    )


def _read_p67_rows() -> list[dict[str, str]]:
    with P67_RESPONSE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def current_p67_transfer_sensitivity() -> dict[str, WeightedResponseEnvelope]:
    """Build conservative P21-weighted sensitivity envelopes from P67.

    FAMILY_HOUSE uses the convex hull across the four source-native EoH house
    forms and therefore imports no UK within-house-form frequencies.
    MULTI_DWELLING uses the source-native Flat row but remains small-N foreign
    validation. Only P10/P90 envelope edges are propagated; P50 values are not
    reweighted into a false Hungarian central estimate.
    """

    rows = {row["scope_id"]: row for row in _read_p67_rows()}
    house_ids = ("EOH-DETACHED", "EOH-SEMI", "EOH-MID-TERRACE", "EOH-END-TERRACE")
    missing = [key for key in (*house_ids, "EOH-FLAT") if key not in rows]
    if missing:
        raise ValueError(f"missing P67 response rows: {missing}")

    def hull(low_col: str, high_col: str) -> ResponseInterval:
        lows = [float(rows[key][low_col]) for key in house_ids]
        highs = [float(rows[key][high_col]) for key in house_ids]
        return ResponseInterval(min(lows), max(highs))

    flat = rows["EOH-FLAT"]
    result = {
        "emitter_units": reweight_building_type_intervals(
            metric="emitter_units",
            family=hull("emitter_units_p10", "emitter_units_p90"),
            multi=ResponseInterval(
                float(flat["emitter_units_p10"]),
                float(flat["emitter_units_p90"]),
            ),
        ),
        "mean_sh_flow_c": reweight_building_type_intervals(
            metric="mean_sh_flow_c",
            family=hull("mean_sh_flow_c_p10", "mean_sh_flow_c_p90"),
            multi=ResponseInterval(
                float(flat["mean_sh_flow_c_p10"]),
                float(flat["mean_sh_flow_c_p90"]),
            ),
        ),
        "spfh4": reweight_building_type_intervals(
            metric="spfh4",
            family=hull("spfh4_p10", "spfh4_p90"),
            multi=ResponseInterval(
                float(flat["spfh4_p10"]),
                float(flat["spfh4_p90"]),
            ),
        ),
    }
    return result
