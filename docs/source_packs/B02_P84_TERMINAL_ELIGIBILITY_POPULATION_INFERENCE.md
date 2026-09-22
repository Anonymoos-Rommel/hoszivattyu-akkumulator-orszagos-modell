# B02-P84 — terminal technical-eligibility population inference

## Purpose

P84 turns Q-B02-001 into an executable population-inference problem without inventing household PASS/FAIL records.

Core boundaries:

`PHYSICAL SCREENING SCOPE != TECHNICAL ELIGIBILITY`

`CURRENT READINESS != TERMINAL TRANSITION OUTCOME`

`POPULATION ESTIMATE != RECORD PASS/FAIL`

`MISSING TERMINAL OUTCOME EVIDENCE != PASS`

`NO FULL-POPULATION MICRODATA != BLOCKER`

`NO DEFENSIBLE TERMINAL-OUTCOME INFERENCE == BLOCKER`

## Existing exact population controls

The canonical physical-screening universe is:

- occupied dwellings: 4,008,541;
- district-heating dwellings outside the B02 physical screen: 618,724;
- non-district physical-screening scope: **3,389,817**;
- CENTRAL_HEATING inside physical scope: **2,216,178**;
- ROOM_BY_ROOM_OR_NO_HEAT inside physical scope: **1,173,639**.

P84 derives the calibration surface directly from the already-materialized WBL011 full joint.

The population-inference calibration grain is:

`20 county/capital regions × 2 in-scope heating-topology classes = 40 strata`

The two in-scope topology classes are:

- `CENTRAL_HEATING`;
- `ROOM_BY_ROOM_OR_NO_HEAT`.

This grain is chosen because both dimensions are exact KSH/WBL controls already present in the repository and because heating topology is materially related to the allowed transition path.

No emitter, hydraulic or technical-eligibility status is inferred from the topology label.

## Why the current interval is still 0–3,389,817

The repository has strong transition-method authority:

- P65 thermal-distribution transition design;
- P57 hydraulic reuse/upgrade/replace transition gate;
- P58 electrical existing/upgrade/new-connection transition gate.

But it does not yet contain a representative or calibrated Hungarian population dataset that tells us the **terminal outcome distribution** after those allowed transitions.

In particular, the following cannot be promoted into a national terminal PASS share:

- current heat-pump presence;
- current emitter prevalence;
- current hydraulic readiness;
- foreign installed heat-pump cohorts;
- the physical screening population itself;
- a current electrical-service snapshot without DSO transition outcome.

Therefore the only currently admissible national technical-eligibility interval is:

`0 <= technically eligible dwellings <= 3,389,817`

This interval is logically valid but intentionally labelled:

`UNINFORMATIVE_BOUNDED_Q`

It is not treated as substantive closure.

## Executable post-stratification contract

P84 adds an executable future inference route.

Each of the 40 exact population strata may receive an admitted interval:

`eligible_lower_share <= eligible_share <= eligible_upper_share`

The stratum-level interval must already originate from:

- a representative observed terminal-outcome sample; or
- an admitted calibrated multi-source model.

P84 then weights those intervals against the exact KSH/WBL stratum populations.

Missing strata are not silently imputed.

If any stratum is missing, national eligibility remains Q.

If all 40 strata are covered, P84 returns a bounded national technical-eligibility interval.

## Required evidence to narrow Q-B02-001

The residual is now precise:

`REPRESENTATIVE_OR_CALIBRATED_TERMINAL_TRANSITION_OUTCOME_EVIDENCE_REQUIRED`

The evidence must support population bounds for terminal technical outcomes after the allowed transition paths.

The relevant technical components remain:

1. `THERMAL_DISTRIBUTION`
2. `HYDRAULIC`
3. `ELECTRICAL`

A useful evidence package can be a representative sample or calibrated multi-source model. It does **not** need to be a full national microdatabase.

The model must also control dependence between component outcomes. Independent multiplication of unrelated marginal PASS rates is prohibited.

## Q-B02-004 boundary

P84 preserves the P61 rule:

`Q-B02-004 OPEN != Q-B02-001 MUST WAIT`

Emitter/action-response uncertainty still matters for COP, retrofit quantities, CAPEX and procurement, but it is not a prerequisite for estimating terminal technical eligibility at population level.

## Record-level boundary

P84 changes nothing for a specific dwelling.

A specific record still requires explicit OBS/DER evidence through the canonical record/project gates.

A population estimate cannot authorize:

- a specific thermal-distribution PASS;
- a specific hydraulic PASS;
- a specific electrical PASS;
- a legal/permit PASS;
- economic eligibility;
- final programme eligibility.

## Q-B02-001 state

`OPEN_NARROWED`

The estimator, calibration grain and fail-closed missing-stratum behavior are now executable.

The remaining blocker is no longer architecture or full-population coverage.

It is the absence of defensible Hungarian terminal transition-outcome population evidence.

## Readiness

B02 remains **55%**.

P84 materializes the inference architecture and the truthful current admissible interval, but it does not produce a non-trivial eligible population estimate, so no readiness uplift is claimed.
