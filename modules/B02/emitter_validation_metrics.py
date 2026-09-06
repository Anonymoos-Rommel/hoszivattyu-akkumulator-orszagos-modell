"""Independent holdout validation metrics for the B02 gas-convector linkage.

B02-P38 closes only the absence of documented validation metrics.  It does not
promote model output to observation, does not create current-emitter stock
authority, and does not approve the linkage model.

The binding holdout is a 2022 Budapest external-category upper bound.  Daikin
reports that 23% of roughly 800,000 Budapest properties use convector or stove
heating.  Gas-convector primary heating is a subset of that broader category,
so a gas-convector model share cannot robustly exceed the reported broad share.
Because the source reports a whole percentage, the contract uses the source's
own reporting precision rather than inventing a post-hoc tolerance.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from modules.B02.emitter_marginal_reconciliation import (
    HISTORICAL_MULTI_PRIOR_SCENARIOS,
    WBL_FULL_JOINT_PROJECTION,
    build_calibrated_emitter_linkage,
)


BUDAPEST_COUNTY_CODE = "HU110"
DAIKIN_BUDAPEST_BROAD_SHARE = 0.23
DAIKIN_BUDAPEST_REPORTING_STEP = 0.01
DAIKIN_NATIONAL_APPROX_AFFECTED_PROPERTIES = 800_000.0

CLEAR_PASS = "CLEAR_PASS"
CONSISTENT_WITH_REPORTED_BOUND = "CONSISTENT_WITH_REPORTED_BOUND"
FAIL = "FAIL"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


@dataclass(frozen=True)
class ScenarioHoldoutMetric:
    scenario_id: str
    model_share: float
    reported_broad_share: float
    lower_rounding_edge: float
    upper_rounding_edge: float
    decision: str

    @property
    def rejected(self) -> bool:
        return self.decision == FAIL


@dataclass(frozen=True)
class NationalDiagnosticMetric:
    model_expected_dwellings: float
    external_approx_properties: float
    absolute_difference: float
    relative_difference_to_external: float
    decision: str = DIAGNOSTIC_ONLY


@dataclass(frozen=True)
class EmitterValidationSummary:
    national_occupied_dwellings: int
    budapest_occupied_dwellings: int
    scenario_metrics: tuple[ScenarioHoldoutMetric, ...]
    retained_scenarios: tuple[str, ...]
    rejected_scenarios: tuple[str, ...]
    national_diagnostic: NationalDiagnosticMetric
    validation_metrics_present: bool


def _classify_reported_upper_bound(model_share: float) -> tuple[float, float, str]:
    """Classify against the rounding interval implied by a whole-percent source.

    For a reported 23% value, the source-compatible interval is [22.5%, 23.5%).
    This is not a statistical confidence interval.  It only prevents false
    precision when a broad-category source is published to the nearest percent.
    """

    half_step = DAIKIN_BUDAPEST_REPORTING_STEP / 2.0
    lower = DAIKIN_BUDAPEST_BROAD_SHARE - half_step
    upper = DAIKIN_BUDAPEST_BROAD_SHARE + half_step
    if model_share <= lower:
        decision = CLEAR_PASS
    elif model_share <= upper:
        decision = CONSISTENT_WITH_REPORTED_BOUND
    else:
        decision = FAIL
    return lower, upper, decision


def _load_full_joint_source_rows(wbl_path: Path) -> dict[str, dict[str, str]]:
    """Load the exact source WBL rows that carry county identity.

    P30 model rows intentionally carry only the fields needed for calibrated
    emitter probabilities.  Geographic selection therefore binds back to the
    committed WBL source row through ``cell_id`` rather than fabricating or
    copying a county field onto model output.
    """

    with wbl_path.open(encoding="utf-8", newline="") as handle:
        rows = {
            row["cell_id"]: row
            for row in csv.DictReader(handle)
            if row.get("projection_id") == WBL_FULL_JOINT_PROJECTION
        }
    if not rows:
        raise ValueError("EMPTY_WBL_FULL_JOINT")
    return rows


def build_independent_emitter_validation(wbl_path: Path) -> EmitterValidationSummary:
    """Evaluate P30 scenarios against independent current external holdouts."""

    source_rows = _load_full_joint_source_rows(wbl_path)
    model_rows, _ = build_calibrated_emitter_linkage(wbl_path)
    if not model_rows:
        raise ValueError("EMPTY_MODEL_ROWS")

    model_cell_ids = {row["cell_id"] for row in model_rows}
    if model_cell_ids != set(source_rows):
        raise ValueError("MODEL_WBL_CELL_LINEAGE_MISMATCH")

    national_occupied = sum(int(row["dwelling_count"]) for row in source_rows.values())
    budapest_cell_ids = {
        cell_id
        for cell_id, row in source_rows.items()
        if row["county_code"] == BUDAPEST_COUNTY_CODE
    }
    if not budapest_cell_ids:
        raise ValueError("NO_BUDAPEST_ROWS")
    budapest_occupied = sum(
        int(source_rows[cell_id]["dwelling_count"])
        for cell_id in budapest_cell_ids
    )

    metrics: list[ScenarioHoldoutMetric] = []
    for scenario_id in HISTORICAL_MULTI_PRIOR_SCENARIOS:
        key = f"probability__{scenario_id}"
        expected = sum(
            float(row["dwelling_count"]) * float(row[key])
            for row in model_rows
            if row["cell_id"] in budapest_cell_ids
        )
        share = expected / budapest_occupied
        lower, upper, decision = _classify_reported_upper_bound(share)
        metrics.append(
            ScenarioHoldoutMetric(
                scenario_id=scenario_id,
                model_share=share,
                reported_broad_share=DAIKIN_BUDAPEST_BROAD_SHARE,
                lower_rounding_edge=lower,
                upper_rounding_edge=upper,
                decision=decision,
            )
        )

    retained = tuple(metric.scenario_id for metric in metrics if not metric.rejected)
    rejected = tuple(metric.scenario_id for metric in metrics if metric.rejected)

    national_scenario_id = next(iter(HISTORICAL_MULTI_PRIOR_SCENARIOS))
    national_model_expected = sum(
        float(row["dwelling_count"])
        * float(row[f"probability__{national_scenario_id}"])
        for row in model_rows
    )
    absolute_difference = national_model_expected - DAIKIN_NATIONAL_APPROX_AFFECTED_PROPERTIES
    national_diagnostic = NationalDiagnosticMetric(
        model_expected_dwellings=national_model_expected,
        external_approx_properties=DAIKIN_NATIONAL_APPROX_AFFECTED_PROPERTIES,
        absolute_difference=absolute_difference,
        relative_difference_to_external=absolute_difference / DAIKIN_NATIONAL_APPROX_AFFECTED_PROPERTIES,
    )

    # P38 requires a genuinely discriminatory independent holdout: at least one
    # scenario must survive and at least one must be rejected by the external
    # logical bound.  The national point estimate is diagnostic only.
    validation_metrics_present = bool(retained) and bool(rejected)

    return EmitterValidationSummary(
        national_occupied_dwellings=national_occupied,
        budapest_occupied_dwellings=budapest_occupied,
        scenario_metrics=tuple(metrics),
        retained_scenarios=retained,
        rejected_scenarios=rejected,
        national_diagnostic=national_diagnostic,
        validation_metrics_present=validation_metrics_present,
    )
