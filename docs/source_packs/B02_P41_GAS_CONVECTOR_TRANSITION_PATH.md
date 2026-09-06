# B02-P41 — gas-convector transition-path-specific thermal admission

**State:** `GAS_CONVECTOR TRANSITION PATH QUALIFIED / AGGREGATE TECHNICAL BLOCKERS STILL OPEN`

**Base:** `497114e2779052a86ae65ea47ffa8ed7ce44b167`

**Audit / implementation date:** 2026-09-06

## 1. Purpose

P40 repaired the direct-versus-calibrated heat-emitter admission asymmetry, but it still exposed the thermal-readiness question as if every current emitter had to be retained and therefore fully characterized before a heat-pump transition could be represented.

That is too strong for a current system that the programme does not reuse.

P41 introduces a transition-path-specific distinction:

`CURRENT SYSTEM REUSE != CURRENT SYSTEM REPLACEMENT`

For a reused hydronic distribution, the existing P18/P32/P40 requirements remain unchanged.

For a separately admitted current non-hydronic system that is explicitly replaced, a current hydronic supply/return design-temperature pair is structurally not applicable because no current hydronic circuit is being reused.

P41 initially applies this route to exactly one current emitter class:

`GAS_CONVECTOR`

No other emitter type is generalized into the same path by this slice.

## 2. Authority consumed

P41 does not create a new gas-convector prevalence model.

It consumes the already admitted row:

`CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P39`

with canonical state:

- approval status: `APPROVED`;
- approval authority: `JOSEPH`;
- model status: `QUALIFIED`;
- output evidence status: `ASS`.

The P39 model remains a calibrated/modelled stock assignment. P41 does not promote its output to `OBS` or `DER`.

Hard boundary:

`QUALIFIED CALIBRATED CATEGORY != DIRECT CURRENT-EMITTER OBSERVATION`

## 3. Gas-convector transition semantics

The admitted P41 path is:

- current emitter: `GAS_CONVECTOR`;
- current thermal-distribution topology: `NON_HYDRONIC_ROOM_HEATING`;
- current hydronic design-temperature applicability: `NOT_APPLICABLE`;
- programme transition path: `REPLACE_EXISTING_DISTRIBUTION`;
- replacement requirement: explicit `true`.

This means the programme does not attempt to preserve a nonexistent current hydronic supply/return circuit.

Therefore:

`GAS_CONVECTOR + REPLACE_EXISTING_DISTRIBUTION`

may satisfy the **current-system thermal transition classification** without requiring a fabricated current 55/45 C, 70/55 C or other hydronic design-temperature pair.

## 4. Executable gate

`modules/B02/archetype_admission_gate.py::assess_thermal_transition_path()`

returns `QUALIFIED` only when all P41 conditions are satisfied.

The category string cannot self-authorize the route. In particular:

- `current_emitter_type` must be exactly `GAS_CONVECTOR`;
- `emitter_category_authority_status` must be `QUALIFIED`;
- the current state must be explicit;
- topology must be `NON_HYDRONIC_ROOM_HEATING`;
- current hydronic design-temperature applicability must be `NOT_APPLICABLE`;
- transition path must be `REPLACE_EXISTING_DISTRIBUTION`;
- replacement requirement must be explicit.

Missing any condition returns `Q`.

`assess_technical_readiness_enrichment()` now consumes two thermal paths:

### REUSE_EXISTING_DISTRIBUTION

This is the default and preserves P18/P32/P40 unchanged:

- admitted current emitter authority is required;
- hydronic/applicable systems require current design-temperature authority;
- non-hydronic `NOT_APPLICABLE` still needs separate authority.

### REPLACE_EXISTING_DISTRIBUTION

The current emitter/design-temperature requirements are replaced by a separately `QUALIFIED` thermal-transition-path authority.

A route token cannot self-authorize this exception.

## 5. What P41 closes

P41 closes the semantic/modeling question for the already admitted gas-convector branch:

`GAS CONVECTOR DOES NOT REQUIRE CURRENT HYDRONIC DESIGN TEMPERATURE WHEN ITS CURRENT DISTRIBUTION IS REPLACED`

The canonical subclaim becomes:

`GAS_CONVECTOR_THERMAL_TRANSITION_PATH = QUALIFIED`

This allows the programme model to move past gas convectors and investigate the next unresolved emitter branch instead of continuing to search for a meaningless current hydronic temperature pair for gas-convector dwellings.

## 6. What P41 does not close

P41 does **not** prove:

- the new replacement emitter design;
- the new replacement emitter capacity;
- the new hydraulic circuit design;
- building-level hydraulic readiness;
- building-level electrical readiness;
- implementation cost;
- a complete current emitter assignment for all occupied dwellings;
- a complete hydronic design-temperature assignment for reused hydronic systems;
- national heat-pump technical eligibility.

Hard boundaries:

`CURRENT GAS CONVECTOR != NEW HEAT-PUMP EMITTER DESIGN`

`REPLACEMENT REQUIRED != REPLACEMENT READY`

`GAS-CONVECTOR PATH QUALIFIED != FULL-STOCK THERMAL READINESS`

`NOT_APPLICABLE CURRENT HYDRONIC TEMPERATURE != UNKNOWN HYDRONIC TEMPERATURE`

## 7. Aggregate B02 state

The gas-convector branch is now qualified as a replacement transition path, but the remaining current-stock emitter classes are not yet exhaustively classified into reuse/replacement paths.

Therefore the aggregate registry intentionally remains:

- `TECHNICAL_READINESS_ARCHETYPE = Q`;
- `NO_CURRENT_HEAT_EMITTER_EVIDENCE` remains open at full-stock scope;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE` remains open for the unresolved/reused hydronic scope;
- B02 readiness remains `55%`.

P41 narrows the unresolved domain; it does not fake aggregate closure.

## 8. Next evidence target

The next justified target is no longer gas convector.

The next unresolved branch should be selected from the central/district-heated stock where current in-dwelling heat distribution may be reused and therefore emitter class and hydronic design-temperature evidence matter materially.

Priority should be given to the largest unresolved hydronic branch for which a defensible current-stock classification can be built from public or zero-cost evidence.
