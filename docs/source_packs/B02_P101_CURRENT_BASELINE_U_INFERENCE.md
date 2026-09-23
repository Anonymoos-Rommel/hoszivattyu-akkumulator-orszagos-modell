# B02-P101 — CURRENT BASELINE U INFERENCE

## Goal

Resolve the P100 residual:

`DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED`

without promoting renovation labels or synthetic archetype means into household
observations.

## 1. New evidence already present in the admitted REKK source

The TARKI-REKK 2022 survey is stronger than the P99 national averages alone.

The report states that the final sample was weighted with KSH data by region and
building type and is representative along those two dimensions. It also states
that the residential model used **type-level weighted averages**.

Table 38 then publishes 2022 renovation-state shares for the same **23-type**
residential taxonomy used by the building-energy model:

- insulated facade;
- insulated attic;
- window replacement.

P101 materializes all 23 rows.

This matters because the 2022 current-state evidence and the P79/P80 physical
calibration now share an explicit source-native type identifier.

## 2. What is and is not linked to U

P80 contains historical/synthetic physical calibration for the 23 types.

For every type:

- the synthetic **uninsulated external-wall** U mean is above the P100
  0.24 W/m2K reference target;
- the synthetic **not-replaced window** U mean is above the P100
  1.15 W/m2K reference target.

Therefore P101 can use the current 2022 shares of:

- facade **not insulated**;
- window **not replaced**

as calibrated baseline-deficit marginals.

It does **not** assign a U-value to the current insulated/replaced branches.

Why:

`INSULATED OR REPLACED != REFERENCE U COMPLIANCE`.

Renovation year, depth, material, workmanship and achieved U are not identified
by Table 38.

## 3. Type-level uncertainty

For each source type:

`wall_baseline_deficit_share = 1 - facade_insulated_share`

`window_baseline_deficit_share = 1 - window_replaced_share`.

Their overlap is unpublished.

Therefore:

`calibrated_deficit_union_lower = max(wall_deficit, window_deficit)`

`calibrated_deficit_union_upper = min(1, wall_deficit + window_deficit)`.

No independence assumption and no midpoint are admitted.

Examples:

- type 1 lower floor = **93.1%**;
- type 10 lower floor = **10.3%**;
- type 17 lower floor = **81.2%**;
- type 22 lower floor = **10.6%**.

These are calibrated synthetic-type population constraints.

`CALIBRATED DEFICIT FLOOR != OBSERVED HOUSEHOLD FAIL SHARE`.

## 4. P79 set-valued propagation

P79 does not point-identify a KEOP type for a WBL/P21 stratum.

P101 therefore propagates the complete candidate set.

Examples:

- pre-1919 FAMILY_HOUSE: calibrated deficit floor **77.7%-93.1%**;
- 2001-2010 FAMILY_HOUSE: **10.3%-29.8%**;
- pre-1919 MULTI_DWELLING: **60.4%-81.2%**;
- 2001-2010 MULTI_DWELLING: **10.6%-26.5%**.

All 14 WBL construction-period x P21 building-group strata are materialized.

## 5. P21 national weighting

The runtime then uses the already-approved P21 CENTRAL and FLAT calibrated
building-group probabilities on the exact 4,008,541 occupied-dwelling universe.

The model propagates:

1. WBL population weight;
2. P21 FAMILY_HOUSE/MULTI_DWELLING uncertainty;
3. P79 candidate-type uncertainty;
4. unknown facade/window overlap.

The result is a bounded **calibrated retrofit floor**, not an observed national
fail share.

The exact national values are materialized in the P101 runtime state and frozen
by regression after validation.

## 6. Blocker effect

Previous:

`DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED`

P101:

`RESOLVED_BOUNDED_CALIBRATED_INFERENCE`.

This is allowed by the P82 contract: national current U does not require
household-by-household exhaustive measurement when a representative/calibrated
bounded inference with explicit uncertainty is available.

## 7. What remains unresolved

The 2022 insulated/replaced branches still do not identify achieved component U.

Therefore:

**HP_ONLY lower bound remains 0**.

The next exact envelope residual is:

`CURRENT_RENOVATED_ENVELOPE_U_QUALITY_TIGHTENING_REQUIRED_FOR_HP_ONLY_LOWER_BOUND`.

This is materially narrower than the P100 blocker.

## 8. Temporal boundary

The survey is a 2022 current-state calibration.

`2022 CURRENT STATE CALIBRATION != 2026 POINT STATE`.

P99's later action-rate/current implementation evidence may validate direction
and activity, but it does not silently update the 2022 type-state table into a
2026 point distribution.

## 9. Readiness

P101 materially improves the executable national action bounds, but no positive
HP_ONLY lower bound is yet established.

Therefore:

- **B02 remains 55%**;
- **PEAK_LOAD_EFFECT remains 50%**;
- **Q-B02-004 remains OPEN_NARROWED**.

## 10. Canonical boundaries

`TARKI TYPE WEIGHTED SHARE != HOUSEHOLD STATE`

`P80 SYNTHETIC TYPE MEAN U != HOUSEHOLD U`

`CALIBRATED DEFICIT FLOOR != OBSERVED HOUSEHOLD FAIL SHARE`

`INSULATED OR REPLACED != REFERENCE U COMPLIANCE`

`2022 CURRENT STATE CALIBRATION != 2026 POINT STATE`

`HP_ONLY LOWER BOUND REMAINS ZERO WITHOUT RENOVATED U QUALITY`
