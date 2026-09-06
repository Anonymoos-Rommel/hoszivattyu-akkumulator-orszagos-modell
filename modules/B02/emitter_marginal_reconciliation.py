"""B02-P30 bounded gas-convector marginal reconciliation.

P30 first proves that a hard ``NHEAT + network-gas`` gas-convector domain is
infeasible for the published conditional gas-convector control.  It then builds
a bounded ASS model family that uses:

* the exact 2022 WBL occupied-stock gas universe;
* the already-qualified P21 FAMILY_HOUSE / MULTI_DWELLING probabilities;
* historical KSH/TABULA building-type gas-convector shares only as structural
  priors; and
* the current 2022 primary-heating gas-convector share as the calibration
  margin.

No output is OBS/DER. No WBL emitter row is materialized by this module.

Canonical boundaries:

* GAS-HEATING MARGIN != PRIMARY-HEATING GAS-CONVECTOR MARGIN
* HEATING MODE != EMITTER
* HISTORICAL STRUCTURAL PRIOR != CURRENT STOCK OBSERVATION
* EXACT MARGINAL RECONCILIATION != VALIDATION
* EXACT MARGINAL RECONCILIATION != INDEPENDENCE CONTROL
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage


SURVEY_PRIMARY_GAS_SHARE = 0.5489
SURVEY_SECONDARY_GAS_SHARE = 0.0698
SURVEY_GAS_AT_LEAST_PARTLY_SHARE = SURVEY_PRIMARY_GAS_SHARE + SURVEY_SECONDARY_GAS_SHARE
SURVEY_CONVECTOR_WITHIN_GAS_SHARE = 0.4061

# FEANTSA 2024 Figure 5 renders the same REKK 2022 survey as a full-sample
# primary-heating-system distribution. Gas convector is published as 23.3%.
PRIMARY_HEATING_GAS_CONVECTOR_SHARE = 0.233

# KSH/TABULA historical building-type controls. These are priors only; P30 does
# not claim that the historical percentages remain current in 2022.
HISTORICAL_FAMILY_CONVECTOR_PRIOR = 0.216
HISTORICAL_MULTI_PRIOR_SCENARIOS = {
    "MULTI_PANEL_LOWER_BOUND": 0.0,
    "MULTI_SMALL_4_9": 0.180,
    "MULTI_LARGE_OTHER_10_PLUS": 0.274,
}

WBL_FULL_JOINT_PROJECTION = "WBL011_FULL_STOCK_JOINT"
GAS_FUEL_CODES = frozenset({"FUEL11", "FUEL21", "FUEL22"})
ROOM_HEATING_CODE = "NHEAT"
EXPECTED_ROWS = 116_452
EXPECTED_OCCUPIED = 4_008_541


@dataclass(frozen=True)
class MarginalReconciliationResult:
    occupied_dwellings: int
    wbl_gas_heating_dwellings: int
    wbl_room_gas_dwellings: int
    wbl_gas_share: float
    survey_gas_share: float
    gas_share_delta_pp: float
    target_convector_dwellings: float
    room_gas_probability: float | None
    marginal_residual_dwellings: float | None
    marginal_reconciled: bool
    blocker: str | None


@dataclass(frozen=True)
class CalibratedScenarioSummary:
    scenario_id: str
    target_share: float
    target_expected_dwellings: float
    calibrated_expected_dwellings: float
    marginal_residual_dwellings: float
    logit_shift: float
    minimum_probability: float
    maximum_probability: float


@dataclass(frozen=True)
class CalibratedEmitterSummary:
    row_count: int
    occupied_dwellings: int
    gas_heating_dwellings: int
    target_primary_convector_share: float
    scenarios: tuple[CalibratedScenarioSummary, ...]
    maximum_absolute_marginal_residual: float


def _read_wbl(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "projection_id",
            "cell_id",
            "heating_mode_code",
            "heating_fuel_code",
            "dwelling_count",
        }
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError("WBL joint is missing required heating fields")
        for row in reader:
            if row["projection_id"] == WBL_FULL_JOINT_PROJECTION:
                count = int(row["dwelling_count"])
                if count <= 0:
                    raise ValueError("full-joint WBL rows must have positive dwelling counts")
                rows.append(row)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"unexpected WBL full-joint row count: {len(rows)}")
    if sum(int(row["dwelling_count"]) for row in rows) != EXPECTED_OCCUPIED:
        raise ValueError("WBL occupied total drift")
    return rows


def reconcile_gas_convector_margin(path: Path) -> MarginalReconciliationResult:
    """Audit the deliberately strict NHEAT+gas domain.

    This diagnostic is retained because it falsifies a tempting but invalid
    topology shortcut. It is not the P30 calibrated stock model.
    """

    rows = _read_wbl(path)
    occupied = sum(int(row["dwelling_count"]) for row in rows)
    gas = sum(
        int(row["dwelling_count"])
        for row in rows
        if row["heating_fuel_code"] in GAS_FUEL_CODES
    )
    room_gas = sum(
        int(row["dwelling_count"])
        for row in rows
        if row["heating_fuel_code"] in GAS_FUEL_CODES
        and row["heating_mode_code"] == ROOM_HEATING_CODE
    )

    if gas <= 0 or room_gas <= 0:
        return MarginalReconciliationResult(
            occupied,
            gas,
            room_gas,
            gas / occupied,
            SURVEY_GAS_AT_LEAST_PARTLY_SHARE,
            (gas / occupied - SURVEY_GAS_AT_LEAST_PARTLY_SHARE) * 100.0,
            gas * SURVEY_CONVECTOR_WITHIN_GAS_SHARE,
            None,
            None,
            False,
            "EMPTY_REQUIRED_WBL_DOMAIN",
        )

    wbl_gas_share = gas / occupied
    target_convector = gas * SURVEY_CONVECTOR_WITHIN_GAS_SHARE
    p_room_gas = target_convector / room_gas
    if not 0.0 <= p_room_gas <= 1.0:
        return MarginalReconciliationResult(
            occupied,
            gas,
            room_gas,
            wbl_gas_share,
            SURVEY_GAS_AT_LEAST_PARTLY_SHARE,
            (wbl_gas_share - SURVEY_GAS_AT_LEAST_PARTLY_SHARE) * 100.0,
            target_convector,
            p_room_gas,
            None,
            False,
            "ROOM_GAS_DOMAIN_TOO_SMALL",
        )

    residual = room_gas * p_room_gas - target_convector
    return MarginalReconciliationResult(
        occupied,
        gas,
        room_gas,
        wbl_gas_share,
        SURVEY_GAS_AT_LEAST_PARTLY_SHARE,
        (wbl_gas_share - SURVEY_GAS_AT_LEAST_PARTLY_SHARE) * 100.0,
        target_convector,
        p_room_gas,
        residual,
        abs(residual) <= 1e-9,
        None if abs(residual) <= 1e-9 else "NONZERO_MARGINAL_RESIDUAL",
    )


def _shift_probability(base_probability: float, shift: float) -> float:
    if not 0.0 <= base_probability <= 1.0:
        raise ValueError("base probability outside [0,1]")
    if base_probability == 0.0:
        return 0.0
    if base_probability == 1.0:
        return 1.0
    logit = math.log(base_probability / (1.0 - base_probability)) + shift
    if logit >= 40.0:
        return 1.0
    if logit <= -40.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-logit))


def _solve_logit_shift(
    model_rows: list[dict[str, object]],
    prior_key: str,
    target_expected: float,
) -> float:
    def expected(shift: float) -> float:
        return sum(
            int(row["dwelling_count"])
            * _shift_probability(float(row[prior_key]), shift)
            for row in model_rows
            if bool(row["gas_present"])
        )

    maximum = sum(
        int(row["dwelling_count"])
        for row in model_rows
        if bool(row["gas_present"]) and float(row[prior_key]) > 0.0
    )
    if not 0.0 < target_expected < maximum:
        raise ValueError(
            f"published target cannot be reached for {prior_key}: "
            f"target={target_expected} maximum={maximum}"
        )

    low = -40.0
    high = 40.0
    if expected(low) > target_expected or expected(high) < target_expected:
        raise ValueError(f"unable to bracket calibration for {prior_key}")
    for _ in range(120):
        mid = (low + high) / 2.0
        if expected(mid) < target_expected:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def build_calibrated_emitter_linkage(
    wbl_path: Path,
) -> tuple[list[dict[str, object]], CalibratedEmitterSummary]:
    """Build a non-materialized ASS probability surface family.

    Every scenario uses the same current 2022 primary-heating gas-convector
    margin and must reproduce it exactly in expectation. Historical percentages
    affect only the relative FAMILY/MULTI shape before calibration.
    """

    wbl_rows = _read_wbl(wbl_path)
    wbl_by_cell = {row["cell_id"]: row for row in wbl_rows}
    if len(wbl_by_cell) != EXPECTED_ROWS:
        raise ValueError("duplicate WBL full-joint cell_id")

    p21_rows, p21_summary = build_calibrated_linkage(wbl_path=wbl_path)
    if p21_summary.row_count != EXPECTED_ROWS or p21_summary.occupied_dwellings != EXPECTED_OCCUPIED:
        raise ValueError("P21 calibrated building-type linkage drift")

    model_rows: list[dict[str, object]] = []
    for p21 in p21_rows:
        cell_id = str(p21["cell_id"])
        source = wbl_by_cell[cell_id]
        count = int(p21["dwelling_count"])
        family_p = float(p21["central_family_probability"])
        gas_present = source["heating_fuel_code"] in GAS_FUEL_CODES
        row: dict[str, object] = {
            "cell_id": cell_id,
            "dwelling_count": count,
            "gas_present": gas_present,
            "family_probability": family_p,
        }
        for scenario_id, multi_prior in HISTORICAL_MULTI_PRIOR_SCENARIOS.items():
            mixed_prior = (
                family_p * HISTORICAL_FAMILY_CONVECTOR_PRIOR
                + (1.0 - family_p) * multi_prior
            )
            row[f"prior__{scenario_id}"] = mixed_prior if gas_present else 0.0
        model_rows.append(row)

    target_expected = EXPECTED_OCCUPIED * PRIMARY_HEATING_GAS_CONVECTOR_SHARE
    gas_total = sum(
        int(row["dwelling_count"])
        for row in model_rows
        if bool(row["gas_present"])
    )

    summaries: list[CalibratedScenarioSummary] = []
    for scenario_id in HISTORICAL_MULTI_PRIOR_SCENARIOS:
        prior_key = f"prior__{scenario_id}"
        probability_key = f"probability__{scenario_id}"
        shift = _solve_logit_shift(model_rows, prior_key, target_expected)
        expected_total = 0.0
        probabilities: list[float] = []
        for row in model_rows:
            if not bool(row["gas_present"]):
                probability = 0.0
            else:
                probability = _shift_probability(float(row[prior_key]), shift)
            row[probability_key] = probability
            expected_total += int(row["dwelling_count"]) * probability
            probabilities.append(probability)
        residual = expected_total - target_expected
        summaries.append(
            CalibratedScenarioSummary(
                scenario_id=scenario_id,
                target_share=PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
                target_expected_dwellings=target_expected,
                calibrated_expected_dwellings=expected_total,
                marginal_residual_dwellings=residual,
                logit_shift=shift,
                minimum_probability=min(probabilities),
                maximum_probability=max(probabilities),
            )
        )

    maximum_residual = max(abs(item.marginal_residual_dwellings) for item in summaries)
    if maximum_residual > 1e-5:
        raise ValueError(f"emitter marginal reconciliation failed: {maximum_residual}")

    return model_rows, CalibratedEmitterSummary(
        row_count=len(model_rows),
        occupied_dwellings=EXPECTED_OCCUPIED,
        gas_heating_dwellings=gas_total,
        target_primary_convector_share=PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
        scenarios=tuple(summaries),
        maximum_absolute_marginal_residual=maximum_residual,
    )
