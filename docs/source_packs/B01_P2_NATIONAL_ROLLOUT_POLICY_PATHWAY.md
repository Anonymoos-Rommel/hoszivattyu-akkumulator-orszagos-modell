# B01-P2 — National programme rollout policy pathway

## Purpose

B01-P2 turns the already approved P1-A policy envelope into one executable,
fail-closed national rollout-pathway contract.

It does **not** claim that 2,000,000 Hungarian households are technically
eligible and it does not create a real selected-household population.

Core boundary:

`POLICY TARGET != TECHNICALLY ELIGIBLE STOCK != REAL ANNUAL CAPACITY != REAL SELECTED HOUSEHOLDS`

## Canonical policy envelope

P1-A already fixes the following modelling envelope:

- baseline policy target: **2,000,000 households**;
- sensitivity range: **0–2,500,000 households**;
- free horizon: **8–25 years**;
- canonical report points: **12 / 15 / 20 years**;
- at least three rollout profiles:
  - `LINEAR`;
  - `LOGISTIC`;
  - `CAPACITY_LIMITED`.

These are `POL` / `SCN` parameters, not observations.

`modules/B01/national_rollout_pathway.py` now makes this envelope executable.
Every generated annual pathway row remains `SCN`.

## Explicit profile semantics

### LINEAR

A deterministic integer monotone allocation reaches the explicit policy target
exactly in the final horizon year. There is no hidden growth parameter.

### LOGISTIC

The scenario must explicitly provide both:

- `logistic_midpoint_fraction`;
- `logistic_steepness`.

No default midpoint or steepness is permitted. The logistic curve is normalized
to the selected horizon so that the path starts from the rollout origin and
reaches the explicit target at the horizon endpoint.

### CAPACITY_LIMITED

The scenario must provide exactly one non-negative annual capacity value for
every plan year. Missing annual capacity is not treated as infinite capacity or
zero. If cumulative capacity is below the policy target, the pathway finishes
with an explicit non-zero `unmet_policy_target`.

## Real national-selection gate

B01-P2 separately defines `NationalSelectionGate`.

A national real-selection claim becomes ready only when all of the following
exist:

1. numeric technically eligible stock with `OBS` or `DER` authority;
2. real annual capacity path with `OBS` or `DER` authority;
3. target-household legal/technical definition with `OBS` or `DER` authority.

Otherwise the status is:

`Q_UPSTREAM_EVIDENCE`

Current repository state remains fail-closed because:

- `Q-B01-001` remains open;
- B02 has no canonical national technically eligible stock;
- no real annual programme capacity path is validated.

Therefore:

`EXECUTABLE NATIONAL POLICY PATHWAY != REAL NATIONAL PROGRAMME SELECTION`

## Spatial handoff to B10

B10-P64 has already accepted the service-area geography as:

`OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL`

That solves the operational geography side, but B01-P2 does not infer a
settlement or DSO allocation from national totals. A future handoff must provide
an explicit regional/settlement allocation of selected households before P64 can
be used to aggregate programme households to `DSO_SERVICE_AREA`.

No population-proportional, nearest-node, equal-share or residual-imputation rule
is introduced here.

## Outputs and non-results

B01-P2 provides:

- executable annual national policy/scenario pathways;
- canonical 12/15/20-year report-point extraction;
- explicit unmet-target accounting;
- a machine gate separating policy paths from real national selection.

B01-P2 does **not** provide:

- national technically eligible household stock;
- real annual installation capacity;
- real selected households;
- settlement-level rollout;
- DSO service-area rollout;
- exact DSO node demand;
- B10 headroom, reinforcement or CAPEX claims.

B01 remains `IN_PROGRESS`. Readiness is not increased solely because the policy
rollout mathematics is now executable.
