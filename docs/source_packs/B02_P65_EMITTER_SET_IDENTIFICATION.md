# B02-P65 — set-identified national emitter population model

**State:** `EMITTER COMPOSITION SET-IDENTIFIED / POINT MIX NOT REQUIRED / Q-B02-004 OPEN ONLY FOR TRANSITION SET PROPAGATION`

**Canonical base:** `e638b46dd9eaf0ba474e02c78aba0a9a73334e9b`

**Implementation date:** 2026-09-21

## 1. Purpose

P64 proved that the EHI Hungary residential surface-presence interval remains
`[0.33, 0.66]` without a numeric KSH house/apartment denominator.

The remaining Q-B02-004 wording still treated several unknown composition
quantities as though each required an external point estimate:

- EHI -> P21 exact semantic mapping;
- P21 stratum emitter allocation;
- radiator + surface mixed-system overlap;
- OTHER emitter share.

That is stronger than the programme needs.

P65 converts those quantities into an explicit **set-identified population
model**.

Canonical rule:

`POINT ESTIMATE NOT IDENTIFIED != MODEL BLOCKED`

If a latent composition can be bounded and the complete admissible set can be
propagated through programme outcomes, the national study does not need to
invent one "best" emitter mix.

## 2. Hard evidence retained

### P22 — exact occupied-stock heating topology

P22 deterministically partitions the exact 2022 WBL011 occupied universe:

- total occupied dwellings: **4,008,541**;
- district heating: **618,724**;
- central heating: runtime-exact from the committed WBL full joint;
- room-by-room or no-heat: runtime-exact from the same joint.

The three topology classes exactly reconcile to the occupied universe.

Boundary:

`HEATING TOPOLOGY != HEAT EMITTER`.

P65 uses topology only as a control surface.

### P39 — approved calibrated gas-convector margin

P39 remains:

`APPROVED / JOSEPH / QUALIFIED`.

The canonical calibrated model reproduces the published full-sample primary
gas-convector margin:

`0.233`.

Its expected occupied-dwelling equivalent is:

`4,008,541 * 0.233 = 933,990.053`.

This is an expected calibrated population total, not an integer observation and
not a WBL topology subset.

Boundary:

`CALIBRATED GAS-CONVECTOR MARGIN != NHEAT CELL ASSIGNMENT`.

P65 deliberately does not force every calibrated convector probability into the
P22 room-by-room branch, because P39 already controls the cross-source
dependence problem under its own admitted model.

### P62/P64 — EHI Hungary surface-presence interval

The source-native EHI houses and apartments strata both carry:

`[0.33, 0.66]`.

P64 proves the national aggregate validation interval is identical for any
non-negative house/apartment denominator weights summing to one.

P65 therefore retains only:

`SURFACE_HEATING_COOLING_PRESENT in [0.33, 0.66]`

as a national external validation constraint.

Boundary:

`SURFACE PRESENCE != SURFACE ONLY`.

## 3. Latent variables instead of fake point estimates

### Radiator presence

There is still no admitted national numeric radiator prevalence.

Therefore:

`RADIATOR_PRESENT_SHARE in [0, 1]`

is retained as a latent variable.

The broad interval does not mean all values are equally plausible. Existing
P44-P55 radiator evidence and the Energiaklub qualitative prior remain useful
for engineering validation and sensitivity ranking. They do not authorize a
numeric national weight.

### Radiator + surface overlap

Let:

- `R` = radiator-presence share;
- `S` = surface-presence share;
- `M` = radiator-and-surface mixed share.

For any candidate composition, exact set theory requires the Fréchet bounds:

`max(0, R + S - 1) <= M <= min(R, S)`.

This is enough to prevent impossible overlap without inventing a mixed-system
percentage.

Across all admissible `R` and the current EHI `S` interval, the global mixed
share can range from:

`0`

to:

`0.66`.

Therefore:

`MIXED_SYSTEM_OVERLAP -> FRECHET_BOUNDED_LATENT`.

It is no longer a mandatory external point-data blocker.

### OTHER emitter presence

Fan-coils and other emitter families remain explicit.

P65 does not force a binary radiator/surface partition.

`OTHER_EMITTER_PRESENT_SHARE in [0, 1]`

is a latent residual/presence variable and may overlap other presence variables.

Boundary:

`RADIATOR + SURFACE + OTHER != 1`

unless an explicitly exclusive taxonomy is separately supplied.

## 4. EHI -> P21 mapping repair

P64 already separated:

`NUMERIC DENOMINATOR WEIGHTS != SEMANTIC CATEGORY MAPPING`.

P65 goes one step further for the national set model.

The EHI interval is used only as a **national aggregate validation
constraint**. No claim is made that:

`EHI_HOUSES = P21_FAMILY_HOUSE`

or:

`EHI_APARTMENTS = P21_MULTI_DWELLING`.

Therefore an exact EHI-to-P21 category mapping is not required merely to define
the national admissible emitter set.

Current status:

`EHI_TO_P21_SEMANTIC_COVERAGE -> RETIRED AS STANDALONE NATIONAL-SET BLOCKER`.

This does not authorize cell-level inheritance of EHI labels.

## 5. P21/WBL allocation becomes a nuisance parameter

For downstream archetype calculations, emitter state still has to be allocated
across P21/WBL strata somehow.

P65 does **not** solve that allocation by independence.

Instead:

`P21_STRATUM_EMITTER_ALLOCATION = LATENT_SIMPLEX_WITH_AGGREGATE_CONSTRAINTS`.

Allowed future allocation families must:

1. use non-negative weights/probabilities;
2. remain within unit bounds;
3. reconcile to admitted national aggregate constraints;
4. retain the P21/WBL population weights;
5. propagate structural allocation uncertainty;
6. never relabel latent allocations as OBS.

This converts a missing-data blocker into a controlled optimisation/inference
dimension.

## 6. Executable model

Canonical implementation:

`modules/B02/emitter_set_identification.py`

The module returns:

- exact P22 topology controls;
- EHI surface-presence bounds;
- the P39 calibrated gas-convector margin;
- explicit flags showing that radiator, mixed, OTHER and P21 cell allocation
  are not point-identified.

It also validates candidate national emitter compositions.

A candidate must satisfy:

1. `S in [0.33, 0.66]`;
2. primary gas-convector margin = `0.233`;
3. every share lies in `[0,1]`;
4. radiator/surface mixed share satisfies the sharp Fréchet bounds;
5. radiator + surface union remains in `[0,1]`.

It deliberately does **not** require presence variables to sum to one.

## 7. Why the gas-convector branch is not forced into P22 NHEAT

This is an important evidence boundary.

KSH source semantics associate convector heating with room-by-room heating, but
P30/P37/P38/P39 demonstrated that the current survey/Census margins cannot be
naively reconciled by the hard shortcut:

`NHEAT + GAS == ALL CURRENT GAS CONVECTOR DWELLINGS`.

P39 therefore uses an approved calibrated probability surface over the
gas-bearing WBL universe with explicit dependence controls and uncertainty.

P65 preserves that admitted model.

Therefore:

`SOURCE SEMANTIC EXAMPLE != HARD CROSS-DATASET CELL SUBSET`.

## 8. Machine-readable contract

New registry:

`registry/b02_p65_emitter_set_identification.csv`

It separates:

- point-identified controls;
- calibrated point margins;
- interval-identified evidence;
- latent variables;
- set-identified overlap;
- forbidden promotions;
- the remaining model blocker.

## 9. Q-B02-004 effect

The previous residual:

- EHI_TO_P21_SEMANTIC_COVERAGE;
- P21_STRATUM_EMITTER_ALLOCATION;
- MIXED_SYSTEM_OVERLAP;
- OTHER_EMITTER_SHARE;
- TRANSITION_MODEL_POPULATION_WEIGHTING

is reclassified.

### No longer standalone evidence blockers

- `EHI_TO_P21_SEMANTIC_COVERAGE` — retired for national aggregate set use;
- `P21_STRATUM_EMITTER_ALLOCATION` — latent constrained allocation;
- `MIXED_SYSTEM_OVERLAP` — Fréchet-bounded latent;
- `OTHER_EMITTER_SHARE` — latent residual/presence.

### Remaining real blocker

`TRANSITION_MODEL_SET_PROPAGATION + ACTION_OUTCOME_BOUNDS`.

The project must now propagate the **entire admissible emitter composition
set**, not one selected point, through:

- KEEP;
- UPSIZE;
- CHANGE;
- ADD;
- REPLACE;
- P65-compatible post-retrofit design-temperature derivation;
- B05 heat-pump COP/capacity;
- emitter/hydraulic CAPEX;
- procurement quantities.

The output must be bounded programme results with explicit uncertainty.

Q-B02-004 remains `OPEN` until that propagation exists.

## 10. Non-claims

P65 does not claim:

- a national radiator percentage;
- a national mixed-system percentage;
- a national OTHER percentage;
- a P21 cell-level emitter observation;
- independence between emitter and building characteristics;
- that the P39 gas-convector margin is an exact integer dwelling count;
- that radiator share is one minus surface share;
- that every latent composition is equally likely;
- that Q-B02-004 is resolved;
- any B02 readiness increase.

## 11. Next logical slice

The next task is now computational rather than a general web search.

Build:

`SET-IDENTIFIED EMITTER COMPOSITION`

->

`P65-COMPATIBLE TRANSITION ACTION ENVELOPE`

->

`COP / CAPEX / PROCUREMENT BOUNDS`.

Only if those output intervals remain too wide for programme decisions should
new external evidence be sought specifically to tighten the latent variables
that drive the width.
