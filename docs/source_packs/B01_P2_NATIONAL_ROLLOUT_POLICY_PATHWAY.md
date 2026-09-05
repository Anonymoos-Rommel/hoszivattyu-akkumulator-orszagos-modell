# B01-P2 — National programme rollout pathway

## Purpose

B01-P2 makes national rollout mathematics executable while removing the original
2,000,000-household working hypothesis from current baseline semantics.

Core boundary:

`LEGACY 2M HYPOTHESIS != OCCUPIED-DWELLING UNIVERSE != NON-DISTRICT-HEATED DWELLING CONTEXT != TECHNICALLY ELIGIBLE STOCK != POLICY TARGET != REAL SELECTED HOUSEHOLDS`

## Correction of the original 2M assumption

The original August programme concept and P1-A carried **2,000,000 households**
as an early working hypothesis. It was not an observed national stock, and it is
not the current programme baseline or ceiling.

The stronger dwelling-side national context is:

- **4,008,541 occupied dwellings** in the 2022 KSH/WBL011 population universe
  (`OBS`);
- approximately **3,403,746 non-district-heated occupied dwellings** (`DER`),
  calculated from that occupied-dwelling universe and the KSH-published 2022
  settlement-type heating-mode shares.

The second value is deliberately marked approximate. The published heating-mode
shares are rounded percentages, so **3,403,746 is a reproducible rounded-share
estimate, not an exact census cell total**.

This approximately **3.4 million** population is the useful programme-relevant
physical starting universe because district-heated dwellings are separated from
household/building-level heating-system conversion. It still does not prove that
every remaining dwelling is technically suitable for a heat pump.

Therefore:

`~3.4M NON-DISTRICT-HEATED DWELLINGS != B02 TECHNICALLY ELIGIBLE STOCK`

Utility customer counts are not used as house counts. Gas-consumer and
electricity-consumer statistics describe service/customer relationships and may
not equal the occupied-dwelling universe.

The **canonical programme target is currently UNSET/Q**. Future scenarios must
supply an explicit `POL`/`SCN` target. If a scenario relies on a population
ceiling, it must identify the exact OBS/DER population reference and its
semantics.

The legacy 2M value is retained only for audit/history so old calculations can be
identified; it has no current baseline or ceiling authority.

## Time/profile envelope retained from P1-A

The numerical target assumption is removed, while the generic pathway shape
contract remains useful:

- free horizon: **8–25 years**;
- canonical report points: **12 / 15 / 20 years**;
- supported profiles:
  - `LINEAR`;
  - `LOGISTIC`;
  - `CAPACITY_LIMITED`.

Every generated annual pathway row remains `SCN`.

## Explicit profile semantics

### LINEAR

A deterministic integer monotone allocation reaches the explicit scenario target
exactly in the final horizon year. There is no hidden target or growth parameter.

### LOGISTIC

The scenario must explicitly provide both:

- `logistic_midpoint_fraction`;
- `logistic_steepness`.

No default midpoint or steepness is permitted.

### CAPACITY_LIMITED

The scenario must provide exactly one non-negative annual capacity value for
every plan year. Missing annual capacity is not treated as infinite capacity or
zero. If cumulative capacity is below the explicit target, the pathway finishes
with non-zero `unmet_policy_target`.

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

B10-P64 has accepted service-area geography as:

`OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL`

That solves the operational geography side, but B01-P2 does not infer a
settlement or DSO allocation from a national total. A future handoff must provide
explicit regional/settlement allocation before P64 can aggregate programme
households to `DSO_SERVICE_AREA`.

No population-proportional, nearest-node, equal-share or residual-imputation rule
is introduced here.

## Outputs and non-results

B01-P2 provides:

- an executable national rollout-path generator for an explicit target;
- canonical 12/15/20-year report-point extraction;
- explicit unmet-target accounting;
- the 4,008,541 occupied-dwelling OBS universe;
- the approximately 3.404M non-district-heated programme-relevant physical
  population context with explicit approximation status;
- a machine gate separating scenario paths from real national selection.

B01-P2 does **not** provide:

- a fixed 2M baseline;
- a 2.5M programme ceiling;
- final programme target;
- exact national non-district-heated census cell total;
- national technically eligible household stock;
- real annual installation capacity;
- real selected households;
- settlement-level rollout;
- DSO service-area rollout;
- exact DSO node demand;
- B10 headroom, reinforcement or CAPEX claims.

B01 remains `IN_PROGRESS`. Readiness is not increased solely because rollout
mathematics is executable.
