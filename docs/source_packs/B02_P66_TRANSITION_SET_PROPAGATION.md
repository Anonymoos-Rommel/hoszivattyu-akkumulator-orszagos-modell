# B02-P66 — transition-action set propagation

**State:** `STRUCTURAL SET PROPAGATION EXECUTABLE / Q-B02-004 OPEN FOR RESPONSE ENVELOPES + PRICE AUTHORITY`

**Canonical base:** `ae01cdb39887566c08bd172a5e024c7fd1b1b984`

**Implementation date:** 2026-09-21

## 1. Purpose

P65 converted the unknown national emitter composition into an explicit admissible set. P66 carries that set into the transition-action layer without selecting a fake national point mix.

Canonical chain:

`SET-IDENTIFIED EMITTER COMPOSITION -> SET-IDENTIFIED ACTION ENVELOPE -> BOUNDED OUTCOME PROPAGATION`

P66 separates two questions:

1. what transition-action bounds already follow from admitted evidence;
2. which physical and monetary response surfaces are still genuinely missing.

## 2. Existing authority used

### P39

The approved calibrated primary gas-convector margin is `0.233` over the occupied-dwelling population. This remains ASS/calibrated population authority, not an OBS household count.

### P41

The admitted gas-convector transition path requires replacement of the existing non-hydronic room-heating distribution. Therefore a gas-convector household cannot be assigned to a KEEP-existing-distribution outcome.

P66 does **not** claim that every such household maps specifically to ADD or specifically to REPLACE. It only uses the combined constraint:

`ADD + REPLACE >= 0.233`

This preserves the transition semantics without inventing the split.

## 3. Sharp structural action bounds

The action vector is exclusive at the programme transition-decision layer:

`KEEP + UPSIZE + CHANGE + ADD + REPLACE = 1`

Together with:

`ADD + REPLACE >= 0.233`

the current sharp one-dimensional bounds are:

- KEEP: `[0, 0.767]`;
- UPSIZE: `[0, 0.767]`;
- CHANGE: `[0, 0.767]`;
- ADD: `[0, 1]`;
- REPLACE: `[0, 1]`;
- ADD + REPLACE: `[0.233, 1]`;
- NON_KEEP: `[0.233, 1]`.

For the exact P22 occupied universe of 4,008,541 dwellings:

`4,008,541 * 0.233 = 933,990.053`

So at least 933,990.053 **expected calibrated dwelling-equivalents** require a non-KEEP distribution transition under the current admitted population model.

Boundary:

`EXPECTED CALIBRATED DWELLING-EQUIVALENT != INTEGER OBSERVED DWELLING COUNT`

## 4. Executable propagation engine

New module:

`modules/B02/transition_set_propagation.py`

It provides:

- candidate action-vector validation;
- the current sharp action-share envelope;
- expected population-count bounds;
- fail-closed linear outcome propagation across the entire feasible action set;
- mandatory complete per-action outcome bounds;
- mandatory price authority for monetary metrics.

The propagator solves the coupled action constraint rather than independently multiplying five unrelated upper bounds.

## 5. Physical outcome boundary

The repository already has the record/project engineering chain needed to generate individual transition outcomes:

- B06-P65 post-retrofit emitter-temperature authority;
- B06 design-load and emitter calculation;
- B05 design-point capacity/COP bridge;
- B02-P42-P55 radiator/emitter engineering and bounded case evidence.

But those authorities do **not** currently provide a national action-by-archetype response envelope.

Therefore P66 does not assign national values for:

- design supply temperature;
- COP;
- heat-pump capacity;
- emitter units added/replaced;
- hydraulic work quantity.

The new propagator can consume such bounded response coefficients once admitted.

## 6. Monetary boundary

Q-B06-010 remains OPEN.

There is no admitted current official/market price surface with the required scope/date/region/baseline-incremental lineage for national retrofit CAPEX.

Therefore:

`PHYSICAL ACTION BOUNDS != MONETARY CAPEX BOUNDS`

and:

`NO PRICE AUTHORITY -> NO MONETARY CAPEX OUTPUT`

The propagator rejects monetary coefficient rows unless their price authority is separately QUALIFIED.

## 7. Q-B02-004 effect

P66 retires `TRANSITION_MODEL_SET_PROPAGATION` as an implementation blocker at the structural level.

The remaining real blockers are now narrower:

1. `ACTION_RESPONSE_ENVELOPE_BY_ARCHETYPE`
2. `CAPEX_PRICE_AUTHORITY`

The first is needed for actual national design-temperature/COP/procurement bounds. The second is needed only for monetary CAPEX.

Q-B02-004 remains OPEN. B02 readiness remains 55%.

## 8. Non-claims

P66 does not claim:

- a national point action mix;
- that 23.3% is an observed dwelling count;
- that gas-convector households are all ADD or all REPLACE;
- national radiator replacement quantities;
- national design-temperature or COP values;
- national monetary retrofit CAPEX;
- that foreign/single-building case studies are population weights;
- that Q-B02-004 is resolved.

## 9. Next logical slice

The next evidence target is no longer generic emitter prevalence.

It is the **action/archetype response surface**:

`ARCHETYPE + POST-RETROFIT LOAD + CURRENT/PROPOSED EMITTER -> ACTION + DESIGN TEMPERATURE + B05 RESPONSE + PROCUREMENT QUANTITY`

Once that bounded response surface exists, P66 can propagate it over the full P65/P66 admissible set and report which uncertainty dimensions actually dominate the programme output width.
