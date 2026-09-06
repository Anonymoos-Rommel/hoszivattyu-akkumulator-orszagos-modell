# B02-P29 — Calibrated emitter-linkage uncertainty method

**State:** `UNCERTAINTY METHOD DEFINED / EXECUTION DATA PENDING / LINKAGE Q`

**Base:** `1cfb77962cb5e8c7e40251217409f0950b0987de`

## Purpose

P28 left `NO_UNCERTAINTY_METHOD` open because the public REKK report does not publish subgroup design variance inputs. P29 closes only the method-definition blocker by predeclaring a design-aware procedure that remains non-executable until suitable released survey metadata arrive.

Canonical boundaries:

`METHOD DEFINED != UNCERTAINTY ESTIMATED`

`FULL-SAMPLE 3.4% MOE != N=657 GAS-HEATING SUBGROUP UNCERTAINTY`

`WEIGHTED SURVEY != SIMPLE RANDOM SAMPLE`

## Method

For gas-convector prevalence, the point estimator is the Hájek weighted proportion using the released final household/case weights.

Variance must be estimated by one of two source-supported routes:

1. design-based linearization when anonymized stratum/PSU design variables are supplied; or
2. valid source-provided replicate weights when those are supplied.

If neither design-variable route nor replicate weights are available, P29 forbids substituting a naive binomial/SRS interval merely because the unweighted subgroup size is N=657.

The full-sample approximately 3.4% margin of error is never inherited by the gas-heating subgroup.

## Propagation

When the calibrated emitter model becomes executable, uncertainty must propagate jointly through the calibrated probabilities by Monte Carlo draws from the estimated covariance structure, preserving probability bounds [0,1] and the admitted national control. Structural model sensitivity remains separate from sampling uncertainty.

## Current execution state

The method is fully specified, but current public inputs do not contain the required final microdata plus design-variance metadata. Therefore no confidence interval or WBL uncertainty surface is materialized in P29.

`NO INTERVAL != ZERO UNCERTAINTY`

## Admission impact

P29 registers a successor P12 candidate with `uncertainty_method=yes` and keeps `uncertainty_propagation=yes`.

Remaining blockers are exactly:

- `NO_JOSEPH_APPROVAL`;
- `NO_VALIDATION_METRICS`;
- `NO_MARGINAL_RECONCILIATION`;
- `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

No current-emitter WBL row and no national technical-eligibility count is created.
