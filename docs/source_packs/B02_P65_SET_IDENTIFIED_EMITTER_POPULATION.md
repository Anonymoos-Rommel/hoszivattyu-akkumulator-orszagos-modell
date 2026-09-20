# B02-P65 — set-identified national emitter population model

**State:** `EXECUTABLE CANDIDATE / NO FALSE EXCLUSIVE MIX / Q-B02-004 OPEN`

**Canonical base:** `e638b46dd9eaf0ba474e02c78aba0a9a73334e9b`

**Implementation date:** 2026-09-20

## 1. Purpose

P62 supplied a current Hungary-specific EHI surface-heating/cooling presence interval.
P63 made post-retrofit design temperature a transition-derived output.
P64 proved that the national EHI validation interval does not require numeric house/apartment denominator weights because both source strata carry the same 33–66% interval.

The remaining problem is that the evidence does not support one mutually exclusive national split such as:

`RADIATOR + SURFACE + CONVECTOR + OTHER = 100%`.

That representation would manufacture disjointness that the sources do not prove.

P65 therefore introduces a **set-identified, multi-label membership model**.

## 2. Canonical model semantics

The model treats the following as potentially overlapping memberships:

- surface heating/cooling present;
- radiator present;
- primary gas-convector heating;
- other emitter present.

Canonical boundaries:

`EMITTER MEMBERSHIP != MUTUALLY EXCLUSIVE STOCK BIN`

`PRIMARY HEATING TYPE != COMPLETE EMITTER INVENTORY`

`SURFACE PRESENCE != SURFACE ONLY`

`GAS CONVECTOR PRIMARY != NO SECONDARY EMITTER`

`UNKNOWN OVERLAP != ZERO OVERLAP`.

A downstream exclusive transition-action allocation may be created only by an explicit scenario/policy rule that handles overlap and preserves uncertainty.

## 3. Hard admitted national constraints

### 3.1 Surface-heating/cooling presence

P62/P64:

`S in [0.33, 0.66]`

Evidence:

`DER / EXTERNAL_BINNED_VALIDATION`.

No midpoint is canonical.

### 3.2 Primary gas-convector membership

P39:

`G = 0.233`

This is the approved calibrated primary-heating gas-convector target.

Evidence:

`ASS / APPROVED / JOSEPH / QUALIFIED`.

P65 preserves that evidence class and does not promote it to OBS.

The gas-convector membership is not declared disjoint from surface or radiator membership because the current evidence does not prove the absence of secondary emitters.

## 4. Radiator presence remains partially unidentified

The repository contains substantial radiator evidence:

- P44–P55 bounded Hungarian radiator quantities, types, low-temperature calibration and retrofit portfolios;
- district/panel examples;
- current and legacy radiator schedules;
- Energiaklub qualitative Hungarian context that hot-water radiators dominate central heating.

But none of those sources supplies an admitted current national radiator-prevalence interval.

Therefore:

`R in [0,1]`

is retained as the formal empirical identification interval.

This wide bound is intentional.

The qualitative statement:

`RADIATOR DOMINANT`

is not silently converted to:

`R > 0.5`

or any other numerical threshold.

Residual:

`RADIATOR_PRESENCE_NUMERIC_BOUND`.

## 5. Mixed surface + radiator systems — mathematical identification

Let:

- S = surface presence;
- R = radiator presence;
- M = surface-and-radiator overlap.

Without assuming independence, the sharp Fréchet bounds are:

`max(0, S + R - 1) <= M <= min(S, R)`.

P65 implements this exactly.

This resolves the **mathematical** overlap rule.

It does not supply an empirical Hungarian overlap estimate.

Therefore the old broad residual:

`MIXED_SYSTEM_OVERLAP`

is refined to:

`MIXED_SYSTEM_EMPIRICAL_BOUND`.

Canonical boundaries:

`FRECHET BOUND != EMPIRICAL MIXED-SYSTEM SHARE`

`NO INDEPENDENCE ASSUMPTION`.

## 6. Other emitter membership

P23 proves that public KSH taxonomy contains categories beyond radiator/surface:

- gas convector;
- stove/fireplace/tile stove;
- electric storage heater;
- air conditioner;
- electric floor/wall heating;
- boiler and heat-pump heat generation categories.

P51 also preserves fan-coil/other possibilities.

The evidence does not provide a current complete national `OTHER` share.

Therefore:

`O in [0,1]`

as a membership dimension.

Again, this is deliberately broad rather than fabricated.

Residual:

`OTHER_EMITTER_NUMERIC_BOUND`.

## 7. KSH national topology controls

P23 already recorded KSH Statistical Yearbook 2022 table 3.2.6.

Published national primary-heating topology shares:

- district heating: 16.0%;
- building-central: 6.3%;
- one-dwelling central: 48.4%;
- individual fixed: 28.9%.

P65 records:

`CENTRAL_OR_DISTRICT_TOPOLOGY_CONTROL = 0.160 + 0.063 + 0.484 = 0.707`.

This remains:

`DER / VALIDATION_ONLY`.

The source itself says one-dwelling central includes radiator/floor/wall examples.

Therefore:

`70.7% CENTRAL_OR_DISTRICT != 70.7% HYDRONIC OBS`

`70.7% CENTRAL_OR_DISTRICT != RADIATOR SHARE`

`48.4% ONE-DWELLING CENTRAL != RADIATOR SHARE`.

No subtype split is manufactured.

## 8. Cross-source convector diagnostic

KSH yearbook individual-fixed topology control:

`0.289`.

P39 primary gas-convector calibrated target:

`0.233`.

Arithmetic difference:

`0.289 - 0.233 = 0.056`.

P65 retains this only as:

`CROSS_SOURCE MAGNITUDE DIAGNOSTIC = 5.6 percentage points`.

It is **not** interpreted as the national share of stove/fireplace/electric/other fixed heating because:

- the two values come from different evidence chains;
- survey/reference semantics differ;
- sampling uncertainty is not represented by the subtraction.

Canonical boundary:

`CROSS-SOURCE DIFFERENCE != RESIDUAL CATEGORY SHARE`.

## 9. Executable implementation

Canonical module:

`modules/B02/set_identified_emitter_population.py`.

The module:

1. exposes the identified marginal intervals;
2. enforces the EHI 33–66% surface band;
3. enforces the P39 23.3% primary-convector target;
4. leaves radiator and other memberships empirically unidentified;
5. calculates sharp Fréchet overlap bounds;
6. rejects overlap scenarios outside those bounds;
7. never requires emitter memberships to sum to one;
8. exposes KSH topology only as validation controls.

The machine-readable contract is:

`registry/b02_p65_set_identified_emitter_model.csv`.

## 10. Example of what P65 permits

A scenario may state:

- surface presence = 0.50;
- radiator presence = 0.60.

Then:

`M in [max(0, 0.50 + 0.60 - 1), min(0.50, 0.60)]`

so:

`M in [0.10, 0.50]`.

Choosing an overlap below 0.10 or above 0.50 is impossible given those marginals.

But P65 does not choose a canonical value inside that interval.

Likewise, the model does not infer radiator presence from surface presence.

## 11. Model-admission status

P65 is:

`CANDIDATE / BOUNDED_MULTI_SOURCE`.

It is not yet registered as a new APPROVED calibrated linkage.

The reason is substantive, not procedural.

The current set still has wide empirical dimensions:

- radiator national prevalence;
- mixed-system empirical overlap;
- other-emitter prevalence;
- P21/archetype conditional allocation;
- population weighting of transition outcomes.

Therefore P65 improves the uncertainty model without claiming Q-B02-004 is resolved.

## 12. Q-B02-004 impact

After P65, the uncertainty is no longer an undefined request for a perfect emitter dataset.

Known/admitted:

- gas-convector calibrated membership;
- surface national validation interval;
- denominator-invariant national EHI interval;
- KSH national topology controls;
- mathematical surface/radiator overlap bounds;
- P65-compatible post-retrofit design-temperature derivation.

Still open:

`EHI_TO_P21_SEMANTIC_COVERAGE`

`P21_STRATUM_EMITTER_ALLOCATION`

`RADIATOR_PRESENCE_NUMERIC_BOUND`

`MIXED_SYSTEM_EMPIRICAL_BOUND`

`OTHER_EMITTER_NUMERIC_BOUND`

`TRANSITION_MODEL_POPULATION_WEIGHTING`.

## 13. Non-claims

P65 does not claim:

- a national radiator percentage;
- a national mixed-system percentage;
- an other-emitter percentage;
- a mutually exclusive emitter distribution;
- 1 - surface = radiator;
- 28.9% - 23.3% = other fixed heating share;
- EHI houses/apartments equal P21 categories;
- any current emitter state is a technical eligibility FAIL;
- Q-B02-004 is resolved;
- B02 readiness should increase.

## 14. Next logical action

The next useful evidence search is now sharply defined.

The highest-value target is any source that can place a non-trivial empirical bound on one of:

1. current national radiator presence;
2. radiator + surface mixed-system prevalence;
3. other-emitter prevalence.

A second route is to build and validate the P21 conditional allocation model while preserving the national set constraints.

Until then, downstream programme modelling should propagate the identified set rather than a fabricated single emitter mix.
