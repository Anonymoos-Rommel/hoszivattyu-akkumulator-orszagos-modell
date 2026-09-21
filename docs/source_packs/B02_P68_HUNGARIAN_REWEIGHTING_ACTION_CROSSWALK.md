# B02-P68 — Hungarian reweighting + set-valued action crosswalk

**State:** `P21 REWEIGHTING EXECUTABLE / EOH ACTION FAMILY PARTIAL / Q-B02-004 NARROWED`

**Canonical base:** `d213448fb1c2b5e3014286b24ff59c79293864d7`

**Implementation date:** 2026-09-21

## 1. Purpose

P67 left two primary residuals:

- `P21_HUNGARIAN_REWEIGHTING`;
- `P66_ACTION_CROSSWALK`.

P68 separates what is already computationally solvable from what still needs
new evidence.

Canonical boundaries:

`P21 CALIBRATED BUILDING-TYPE WEIGHTS -> HUNGARIAN REWEIGHTING AUTHORITY`

`FOREIGN RESPONSE INTERVAL -> TRANSFER SENSITIVITY, NOT HUNGARIAN OBSERVATION`

`POSITIVE EMITTER MEASURE -> NON-KEEP ACTION FAMILY`

`POSITIVE EMITTER MEASURE != UPSIZE/CHANGE/ADD/REPLACE SUBTYPE`

`ZERO EMITTER MEASURE != PROVEN KEEP`

## 2. Exact P21 Hungarian weights

The approved P21 calibrated linkage already reconciles the complete
4,008,541 occupied-dwelling universe to:

- FAMILY_HOUSE: **2,423,136**;
- MULTI_DWELLING: **1,585,405**.

Therefore:

- FAMILY_HOUSE weight = **0.6044932558**;
- MULTI_DWELLING weight = **0.3955067442**.

These are exact outputs of the approved calibrated P21 model and remain
`ASS`, not OBS.

The previous statement that Hungarian population weights were mechanically
missing is therefore retired.

## 3. Reweighting engine

New executable module:

`modules/B02/response_reweighting.py`

It accepts bounded FAMILY_HOUSE and MULTI_DWELLING response intervals and
applies the exact P21 national weights.

No foreign sample frequency participates in the weighting.

For P67 specifically:

- FAMILY_HOUSE response is the **convex hull across Detached, Semi-Detached,
  Mid-Terrace and End-Terrace** EoH response envelopes;
- MULTI_DWELLING uses the EoH Flat envelope but retains its small-N validation
  warning;
- only P10/P90 edges are propagated;
- P50 is not converted into a false Hungarian central estimate.

Therefore:

`P21_HUNGARIAN_REWEIGHTING -> RESOLVED_EXECUTABLE`.

## 4. Current transfer-sensitivity envelope

With the current P67 response bounds and exact P21 building-type weights:

| Metric | Lower | Upper | Meaning |
| --- | ---: | ---: | --- |
| emitter units | 2.582027 | 11.835946 | foreign-response sensitivity |
| mean SH flow | 33.046008 C | 45.388962 C | monitored-flow sensitivity |
| SPFH4 | 1.957034 | 3.484632 | measured seasonal sensitivity |

These are not Hungarian predicted quantiles.

They answer a narrower question:

> Given the exact Hungarian P21 family/multi population weights, what response
> envelope results if the foreign EoH building-type response bounds are used as
> bounded physical transfer validation?

The output is `ASS`.

## 5. P66 action crosswalk

The EoH source contains source-native emitter measure counts.

A strictly positive emitter-measure count proves that an emitter intervention
occurred. Under the exclusive P66 action taxonomy this excludes `KEEP`.

Therefore:

`positive emitter measure -> {UPSIZE, CHANGE, ADD, REPLACE}`.

But it does **not** identify which member of that set applies.

For a zero emitter-measure count P68 does not infer KEEP, because absence of a
recorded emitter measure is not explicit evidence that the existing emitter
arrangement was retained.

Therefore:

`zero emitter measure -> {KEEP, UPSIZE, CHANGE, ADD, REPLACE}`

as an uninformative set.

The broad P66 action-crosswalk blocker is consequently narrowed to:

- `P66_ACTION_SUBTYPE_SPLIT`;
- `ZERO_MEASURE_KEEP_AUTHORITY`;
- `HUNGARIAN_ACTION_ASSIGNMENT`.

## 6. Why P21 weighting does not close the national action result

P21 tells us how many Hungarian dwellings are in the FAMILY_HOUSE and
MULTI_DWELLING calibrated building-type domains.

It does not tell us which Hungarian dwelling takes which P66 transition action.

Therefore:

`POPULATION WEIGHT != ACTION ASSIGNMENT`.

P68 solves weighting mechanics but does not transfer the 92.86% UK
emitter-intervention frequency to Hungary.

## 7. Q-B02-004 effect

Retired blocker:

- `P21_HUNGARIAN_REWEIGHTING` — executable from existing approved P21.

Narrowed blocker:

- `P66_ACTION_CROSSWALK` ->
  `P66_ACTION_SUBTYPE_SPLIT + ZERO_MEASURE_KEEP_AUTHORITY + HUNGARIAN_ACTION_ASSIGNMENT`.

Optional monetary residual:

- `MARKET_REALIZED_COST_DISTRIBUTION` only if a central/expected cost estimate
  is required instead of the already-qualified KEHOP upper ceiling.

Q-B02-004 remains OPEN.

B02 readiness remains **55%** because P68 improves propagation and blocker
precision but does not yet produce a defensible national action distribution.

## 8. Non-claims

P68 does not claim:

- UK house-form frequencies are Hungarian frequencies;
- EoH 92.86% is a Hungarian intervention rate;
- P21 building-type outputs are OBS;
- the sensitivity envelope is a Hungarian confidence interval;
- P50/P90 source quantiles are Hungarian quantiles;
- zero emitter measures prove KEEP;
- positive emitter measures identify one action subtype;
- Q-B02-004 is resolved.
