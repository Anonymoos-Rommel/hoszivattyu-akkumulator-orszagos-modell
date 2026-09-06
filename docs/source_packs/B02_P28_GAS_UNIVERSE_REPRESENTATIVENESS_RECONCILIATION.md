# B02-P28 — TÁRKI–REKK gas-universe representativeness reconciliation

**State:** `REPRESENTATIVENESS BLOCKER RESOLVED / EMITTER LINKAGE STILL Q`

**Base:** `2a32777f4156bdc74beef367c97f967e1f3b3112`

**Audit date:** 2026-09-06

## 1. Purpose

P27 correctly refused to broadcast the TÁRKI–REKK gas-convector share (`40.61%`, N=657 gas-heating households) across WBL cells. One of its blockers was that the survey-to-target representativeness diagnostics had not yet been made explicit in the repository.

P28 closes that blocker only.

Canonical boundary:

`SURVEY REPRESENTATIVENESS DIAGNOSTIC != EMITTER CONDITIONAL DISTRIBUTION`

`GAS-HEATING MARGINS != GAS-CONVECTOR MARGINS`

## 2. Source-native representativeness evidence

The REKK report states that the 2022 household survey used a 1,013-person/household sample and that TÁRKI weighted the final database using KSH data by **region and building type**, making the resulting database representative along those two dimensions.

The same report publishes weighted gas-heating margins for the full sample:

- primary gas heating: `54.89%`;
- secondary gas heating: `6.98%`;
- no gas heating: `38.13%`.

It also publishes source-native gas-heating characteristics by:

- construction period; and
- settlement type.

These controls are pinned in `registry/b02_tarki_rekk_gas_universe_controls.csv`.

Therefore P28 has explicit, source-backed representativeness diagnostics rather than relying on the generic statement "nationally representative" alone.

## 3. What P28 does not claim

The published construction-period and settlement-type tables condition on **gas-heating status**, not on gas-convector use.

Therefore they cannot shape a cell-level gas-convector allocation without an additional emitter-specific conditional source.

The report's settlement categories also do not have a lossless one-to-one mapping to the WBL011 settlement taxonomy because the survey includes a combined `Budapest or large-city agglomeration` category.

The construction-period bands likewise are not identical to the WBL011 bands.

Therefore P28 does **not** mark `marginal_reconciliation` as complete for the emitter linkage.

Canonical boundary:

`SOURCE-NATIVE GAS-UNIVERSE CONTROL != LOSSLESS WBL CROSSWALK`

## 4. Updated calibrated-linkage candidate

P28 registers a successor candidate:

`B02-P28-TARKI-REKK-GAS-CONVECTOR-WBL-LINKAGE-CANDIDATE`

It inherits all P27 restrictions but now has:

- `representativeness_diagnostics = yes`;
- `marginal_reconciliation = no`;
- `validation_metrics = no`;
- `uncertainty_method = no`;
- `independence_assumption_controlled = no`;
- `approval_status = NOT_APPROVED`.

The exact remaining blockers are:

1. `NO_JOSEPH_APPROVAL`;
2. `NO_VALIDATION_METRICS`;
3. `NO_MARGINAL_RECONCILIATION`;
4. `NO_UNCERTAINTY_METHOD`;
5. `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

## 5. Why this is a real blocker reduction

P27 had six blockers. P28 reduces the successor candidate to five by replacing a narrative representativeness claim with explicit source-native weighted-design evidence and published conditional diagnostics.

No stock emitter row is materialized and no technical-readiness uplift is created.

`REPRESENTATIVENESS PROVEN != LINKAGE VALIDATED`

## 6. Next hard blocker

The shortest credible route now is emitter-specific microdata or published cross-tabs that condition gas-convector use on at least one WBL-compatible shaping dimension.

The REKK project page explicitly states that the full detailed survey database can be provided to interested parties for scientific publication or policy analysis on request to the project lead.

Until such data are obtained, P28 does not manufacture:

- a WBL gas-convector surface;
- subgroup confidence intervals;
- independence-free conditional probabilities; or
- national technical-eligibility counts.
