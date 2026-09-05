# B01-P2 — National programme rollout pathway

## Purpose

B01-P2 makes national rollout mathematics executable while removing the original
2,000,000-household working hypothesis from current baseline semantics.

Core boundary:

`LEGACY 2M HYPOTHESIS != OBSERVED GAS-CONSUMER UNIVERSE != TECHNICALLY ELIGIBLE STOCK != POLICY TARGET != REAL SELECTED HOUSEHOLDS`

## Correction of the original 2M assumption

The original August programme concept and P1-A carried **2,000,000 households**
as an early policy/work hypothesis. It was never an observed national stock and
must not be used as the current programme baseline or national ceiling.

Current repository evidence contains stronger national population context:

- **3,241,811** household gas consumers in 2024 (`OBS`), from KSH national gas
  supply statistics (`SRC-B11-KSH-KOR0043-2024`);
- **3,022,115** heating consumers in 2024 (`OBS`), obtained by exact summation of
  the 20 KSH county/capital rows materialized under
  `SRC-B11-KSH-TERSTAT-610-2024`;
- **4,008,541** occupied dwellings in the 2022 WBL011 population universe
  (`OBS`) used by B02.

These three numbers have different semantics. In particular:

`3,241,811 GAS CONSUMERS != 3,022,115 HEATING CONSUMERS != TECHNICALLY ELIGIBLE HEAT-PUMP STOCK`

B02 technical eligibility remains unresolved, so B01-P2 does not rename any of
these population counts as eligible stock.

The **canonical programme target is currently UNSET/Q**. Future scenarios must
supply an explicit `POL`/`SCN` target and, when they rely on a population
ceiling, must name the exact OBS/DER population reference and semantics.

The legacy 2M value is retained only for audit/history so old calculations can be
identified; it has no current baseline or ceiling authority.

## Time/profile envelope retained from P1-A

The numerical target assumptions are corrected above, but the generic pathway
shape contract remains useful:

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
- exact national observed population context without semantic promotion;
- a machine gate separating scenario paths from real national selection.

B01-P2 does **not** provide:

- a fixed 2M baseline;
- a 2.5M programme ceiling;
- final programme target;
- national technically eligible household stock;
- real annual installation capacity;
- real selected households;
- settlement-level rollout;
- DSO service-area rollout;
- exact DSO node demand;
- B10 headroom, reinforcement or CAPEX claims.

B01 remains `IN_PROGRESS`. Readiness is not increased solely because rollout
mathematics is executable.
