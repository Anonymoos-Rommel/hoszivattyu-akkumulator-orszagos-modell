# B02-P69 — action-layer semantic repair

**State:** `FALSE FIVE-WAY DWELLING SIMPLEX RETIRED / DISTRIBUTION PATH + ROOM EMITTER ACTIONS SEPARATED`

**Canonical base:** `df80430caf6b4d4f0f6871dbbf2eef6559f042b6`

**Implementation date:** 2026-09-21

## 1. Why P69 exists

P66 treated:

`KEEP + UPSIZE + CHANGE + ADD + REPLACE = 1`

as an exclusive dwelling-level action simplex.

That is inconsistent with canonical earlier repository evidence.

P41 defines a dwelling-level thermal-distribution transition:

- `REUSE_EXISTING_DISTRIBUTION`;
- `REPLACE_EXISTING_DISTRIBUTION`.

P55 defines room/emitter-level ASHP design actions:

- `KEEP`;
- `UPSIZE`;
- `CHANGE`;
- `ADD`.

The single P55 dwelling contains several of those emitter outcomes at the same time:
type changes, dimensional upsizing, retained emitters plus added emitters, and multi-emitter rooms.

Therefore:

`DWELLING DISTRIBUTION PATH != ROOM/EMITTER ACTION`

and:

`ROOM/EMITTER ACTIONS ARE NOT A DWELLING SIMPLEX`.

## 2. Correct layered model

### Layer A — dwelling distribution path

Exclusive:

`REUSE_EXISTING_DISTRIBUTION + REPLACE_EXISTING_DISTRIBUTION = 1`.

P39/P41 already qualify the primary gas-convector margin at 0.233 and require replacement of the existing non-hydronic distribution path.

Therefore:

`REPLACE_EXISTING_DISTRIBUTION >= 0.233`.

For 4,008,541 occupied dwellings:

`4,008,541 * 0.233 = 933,990.053`.

This is a calibrated expected dwelling-equivalent lower bound, not an integer OBS count.

### Layer B — room/emitter actions

Non-exclusive multi-label events:

- KEEP;
- UPSIZE;
- CHANGE;
- ADD.

A single dwelling may contain all or several of these across different rooms.

No sum-to-one rule applies at dwelling grain.

## 3. Runtime repair

`modules/B02/transition_set_propagation.py` now exposes:

- `DistributionPathCandidate`;
- `assess_distribution_path_candidate()`;
- `build_distribution_path_envelope()`;
- `distribution_count_bounds()`;
- independent `EmitterActionIncidence`;
- `assess_emitter_action_incidence()`;
- distribution-path outcome propagation.

The old five-way simplex is machine-marked:

`SUPERSEDED_BY_B02_P69_LAYERED_ACTION_MODEL`.

## 4. EoH source semantics

The official Electrification of Heat Home Surveys and Install Report, section 6.3.2, states that 93% of installed homes had new heat emitters installed and explains that emitter replacement was not always necessary.

The P67 transport snapshot independently reconciles:

- installed systems: 742;
- positive emitter-measure records: 689;
- zero emitter-measure records: 53.

Therefore:

`689 / 742 = 92.8571%`

is consistent with the official rounded 93%.

P69 admits:

- positive count -> `NEW_EMITTER_INSTALLATION_PRESENT`;
- zero count -> `NO_NEW_EMITTER_INSTALLATION`.

It does **not** infer:

- a Hungarian intervention rate;
- that every positive case is UPSIZE, CHANGE or ADD;
- that every zero case proves KEEP in every room;
- a room-level before/after subtype.

The official report explicitly notes that contractor evidence suggesting all existing emitters were generally replaced was anecdotal because existing-radiator counts were not recorded. P69 does not promote that anecdotal statement.

## 5. Blocker repair

Retired as malformed:

- `ZERO_MEASURE_KEEP_AUTHORITY`.

Reason: the source-native estimand is new-emitter installation, not room-grain KEEP classification.

Retired as wrong grain:

- `P66_ACTION_SUBTYPE_SPLIT`.

Reason: there is no defensible five-way dwelling subtype split.

Current residual becomes:

1. `HUNGARIAN_DISTRIBUTION_REPLACEMENT_ASSIGNMENT`;
2. `HUNGARIAN_EMITTER_INTERVENTION_ASSIGNMENT`;
3. `ROOM_GRAIN_ACTION_DISTRIBUTION`.

Optional monetary residual:

- `MARKET_REALIZED_COST_DISTRIBUTION` only if a central/expected cost estimate is required.

## 6. Non-claims

P69 does not claim:

- 23.3% is the total replacement-distribution share;
- 92.86% is a Hungarian emitter-intervention rate;
- 53/742 is a Hungarian KEEP rate;
- positive EoH emitter measures identify a room action subtype;
- all existing emitters were replaced in the 689 positive EoH homes;
- Q-B02-004 is closed.

B02 readiness remains 55%.
