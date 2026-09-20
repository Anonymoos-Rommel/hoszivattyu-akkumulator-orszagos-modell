# Project-wide population inference policy

**Status:** CANONICAL  
**Effective:** 2026-09-20  
**Scope:** B01-B20 national-stock, prevalence, distribution and aggregate-effect claims

## 1. Purpose

This project is an auditable national decision model, not a requirement to reconstruct a complete technical micro-record for every Hungarian dwelling.

A missing full-population microdataset is not by itself a reason to stop national modelling when the target quantity can be estimated defensibly from observed samples or calibrated multi-source evidence.

Canonical rule:

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

The policy does **not** weaken record-level technical, legal, contractual or network gates.

## 2. Two evidence planes

### 2.1 Population plane

Used for national or regional prevalence, distributions, totals, programme sizing and uncertainty-aware portfolio modelling.

Admissible evidence can include a representative survey/sample or a calibrated multi-source model.

### 2.2 Record/project plane

Used to decide whether a specific dwelling, building, meter, connection point, substation, permit, tariff condition or intervention may pass a gate.

A population probability cannot make a record pass.

`POPULATION ESTIMATE != RECORD PASS/FAIL`

## 3. Population-evidence classes

### A. EXHAUSTIVE_ADMIN_CENSUS

Complete or near-complete administrative/census coverage at the claim's required grain.

Permitted use: direct population controls and, when source semantics support it, direct population distribution.

### B. REPRESENTATIVE_OBSERVED_SAMPLE

Observed sample with a documented target population and a defensible sampling/weighting design.

Required, where applicable:
- target population and inclusion/exclusion rules;
- sample frame and selection method;
- sample size and effective sample size when weighting materially changes precision;
- strata/clusters/weights;
- reference period;
- non-response and missingness treatment;
- calibration to known population controls;
- uncertainty interval or equivalent distributional output.

The sample observations remain `OBS`; a national estimate calculated from them is normally `DER`, not a fabricated population-wide `OBS`.

### C. CALIBRATED_MULTI_SOURCE_INFERENCE

A statistical or engineering-statistical model combining multiple observed/modelled sources and known population controls.

Required:
- explicit model ID and version;
- calibration sources and target population;
- validation diagnostics;
- marginal/control reconciliation;
- controlled independence assumptions;
- uncertainty propagation;
- structural sensitivity;
- reproducible output.

The output must retain its model-derived status such as `DER`, `MODELLED` or the module's approved model-output status. It does not inherit `OBS`.

### D. BOUNDED_ENGINEERING_VALIDATION

Real measured/designed buildings, technical surveys, test campaigns or engineering documents that validate physical relationships, ranges or method shape.

Permitted use: physics validation, applicability bounds, calibration checks.

Not permitted by itself: national prevalence/share.

### E. ASS / SCN

Explicit assumption or scenario when population evidence is insufficient.

Permitted use: sensitivity/stress testing with clear labelling.

Not permitted: observed-prevalence claim.

## 4. Admission gate for a national estimate

A national or regional inference is admissible only when the material items below are explicit and auditable:

1. claim and target population;
2. unit and geography/time grain;
3. source/sample selection mechanism;
4. coverage and missingness;
5. weighting, post-stratification or calibration controls;
6. estimator/model and transformations;
7. representativeness/validation diagnostics;
8. uncertainty method;
9. sensitivity to structural assumptions;
10. provenance and reference period.

An exact full joint distribution is preferred when it exists, but is **not mandatory** if a defensible inferential route establishes the target claim.

## 5. Joint distributions and marginals

Separate observed marginals may not be multiplied into a synthetic joint and presented as fact.

A joint may be estimated only through an admitted statistical/calibrated model that:
- identifies the dependence assumptions;
- reconciles to known controls;
- validates against independent or held-out evidence when feasible;
- propagates uncertainty.

`MARGINALS != JOINT` remains canonical.

## 6. Uncertainty reporting

Material sample-based or model-based national outputs must not be presented as false point precision.

Report, as appropriate:
- central estimate plus confidence/credible interval; or
- `P10/P50/P90`; and
- structural sensitivity where model form or independence assumptions matter.

Rounding must reflect the evidence precision.

## 7. What this policy changes

The following is no longer a valid blocker by itself:

> We do not have an exact technical record for every dwelling in the national stock.

The valid blocker is:

> We do not yet have a defensible method and evidence base to infer the target population quantity within a stated uncertainty range.

Therefore national stock questions may close through:
- exhaustive administrative evidence;
- a representative observed sample; or
- a validated calibrated multi-source inference.

## 8. What this policy does not change

The policy does not allow:
- a national emitter share to decide that a particular dwelling is low-temperature-ready;
- a sampled network pattern to certify a specific substation's headroom;
- a prevalence estimate to establish a legal/permit/tariff condition;
- a modelled average to overwrite measured record evidence;
- arbitrary cross-multiplication of unrelated marginals;
- hiding uncertainty behind a single precise number.

B02/P65-style room/building evidence, DSO-specific connection decisions, legal authorities, tariffs, contracts and other discrete record-level gates remain record/site/source specific.

## 9. Module interpretation

This policy applies project-wide whenever the output is a stock/population quantity.

Examples:
- **B01/B02:** target-stock composition and technical prevalence may use admitted population inference.
- **B05/B06:** representative/calibrated building evidence may support national distributions/effect surfaces; specific sizing and S-state transitions remain record-level.
- **B08/B09/B10:** aggregate/regional patterns may use spatial/temporal inference when justified, but individual network-node facts remain node-specific.
- **B11-B19:** national economic, fiscal, labour, health and capacity quantities may use representative or calibrated evidence with uncertainty; legal/accounting identities still require exact authority.

## 10. Historical slices

Historical source-pack documents remain evidence of the decision state when they were written. A historical note that required a full joint is not automatically rewritten as if that joint existed.

From this policy's effective date forward, current gates and new slices must distinguish:

`FULL COVERAGE MISSING`

from

`DEFENSIBLE INFERENCE MISSING`.

Only the second condition is a general population-modelling blocker.
