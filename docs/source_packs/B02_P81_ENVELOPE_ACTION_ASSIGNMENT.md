# B02-P81 — bounded multi-source envelope-action population inference

**State:** `NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED -> PARTIAL_RESOLVED_AS_POPULATION_INFERENCE_CONTRACT`

**Canonical base:** `7ac15e0531ffca88c2943e16d719f93c0835638b`

**Implementation date:** 2026-09-22

## 1. Purpose

P80 materialized source-native action-conditioned post-state U constraints for:

- `AIR_TO_WATER_HP_ONLY`;
- `REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP`.

P80 then left:

`NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED`.

P81 repairs the semantics of that blocker.

The national model does **not** require exact household-by-household knowledge of which Hungarian dwelling receives which action. That would be an unnecessarily strong and generally unattainable evidence requirement.

Canonical boundary:

`FULL HOUSEHOLD ACTION IDENTIFICATION != REQUIRED`

The primary national route is:

`REPRESENTATIVE PUBLIC EVIDENCE -> MULTI-SOURCE CALIBRATION -> BOUNDED POPULATION INFERENCE -> UNCERTAINTY PROPAGATION`

Therefore:

`REPRESENTATIVE MULTI-SOURCE POPULATION INFERENCE = ADMISSIBLE`

## 2. Evidence-derived national action state

The evidence-derived action surface is not an exact point assignment.

It may be:

- interval-bounded;
- set-valued;
- probabilistic;
- stratified by building type, construction period, geography or another admitted population key.

Canonical boundaries:

`EVIDENCE-DERIVED ACTION MIX != EXACT POINT ASSIGNMENT`

`EVIDENCE-DERIVED ACTION MIX = BOUNDED / SET-VALUED / PROBABILISTIC`

The uncertainty must be propagated through the later design-load, P65 and B05 response chain instead of collapsed to an invented national percentage.

## 3. Multi-source evidence rule

Where available, the target is at least **three independent public evidence sources** for the same estimand and compatible population scope.

This is a triangulation target, not permission to average arbitrary numbers.

Before aggregation, every candidate source must pass:

1. **estimand compatibility** — the source measures the same action/state concept;
2. **population-scope compatibility** — the denominator and target population are sufficiently aligned;
3. **temporal admission** — the observation year is appropriate for the current inference;
4. **independence control** — derivative publications of the same underlying dataset do not count as independent sources;
5. **explicit uncertainty** — source interval/bounds remain visible.

Canonical boundary:

`THREE SOURCES != SIMPLE AVERAGE WITHOUT SEMANTIC COMPATIBILITY`

If three independent fresh compatible sources exist, P81 admits:

`QUALIFIED_MULTI_SOURCE_BOUNDED_INFERENCE`.

If only one or two fresh compatible independent sources exist, the model may remain:

`PARTIAL_MULTI_SOURCE_BOUNDED_INFERENCE`

rather than inventing a point value or declaring the entire model impossible.

## 4. Freshness and historical evidence

The current inference must use an explicit `freshness_floor_year`.

Sources older than that floor are not discarded. They remain:

`HISTORICAL_CALIBRATION`

but are not silently pooled into the current estimate.

Canonical boundary:

`OLD SOURCE != CURRENT STOCK WITHOUT TEMPORAL BRIDGE`

This specifically prevents a historical survey, for example from 2015, from being treated as an unchanged description of the 2026 stock.

Where fresher compatible evidence exists, it has the primary current-inference role.

## 5. Aggregation semantics

The mandatory output is a bounded evidence envelope.

For admitted fresh compatible sources:

- lower bound = conservative minimum admitted lower bound;
- upper bound = conservative maximum admitted upper bound.

This deliberately preserves between-source uncertainty.

An optional central estimate may be derived only when:

- all admitted current sources provide an explicit central estimate;
- all provide an explicit positive aggregation weight;
- the admitted rows represent independent source families.

The centre is then a **weighted derived estimate**, not OBS truth.

No hidden equal weighting is introduced.

No source with a different estimand or incompatible population scope enters the aggregate merely because it is numerically available.

## 6. Current Hungarian programme calibration

The already registered official MFB authority:

`SRC-B02-HU-KEHOP-417-418-SCOPE-2026`

remains a current scope-limited policy calibration.

It supports the existing programme scope for occupied one- and multi-dwelling family houses built and permitted before 2007 and the current minimum primary-energy-saving rule and eligible intervention families.

These facts may constrain the action model, but do not themselves identify national action frequency.

Existing boundaries remain:

`ELIGIBLE MEASURE MENU != NATIONAL ACTION ASSIGNMENT`

`AGE / ELIGIBILITY SCOPE != ACTION FREQUENCY`

`30% PRIMARY-ENERGY SAVING REQUIREMENT != ENVELOPE-RETROFIT SHARE`

## 7. Optional exact scenario / policy override

An exact split remains admissible when it is intentionally supplied as a programme scenario or explicit policy rule.

Example:

- 60% `AIR_TO_WATER_HP_ONLY`;
- 40% `REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP`.

That route must close exactly to its declared programme population and carry explicit authority.

But:

`EXACT PROGRAMME ACTION MIX = SCENARIO / POLICY INPUT ONLY`

and:

`PROGRAMME SCENARIO ASSIGNMENT != OBSERVED CURRENT STOCK`.

The exact override does not replace the evidence-derived population inference unless the scenario explicitly requests that policy case.

## 8. Blocker effect

Previous:

`NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED`

P81 corrected:

`PARTIAL_RESOLVED_AS_POPULATION_INFERENCE_CONTRACT`

The exact current residual becomes:

`FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

This residual asks for defensible current population evidence, not impossible household-level exact identification.

## 9. Relationship to existing population-inference policy

P81 is consistent with the existing B02 set-identification architecture:

- exact full-population direct observation is not mandatory;
- calibrated representative inference is admissible;
- latent/set-valued quantities remain explicit;
- point estimates are not manufactured merely to make later gates pass.

The action layer follows the same rule.

## 10. Remaining P80/P78 physical residuals

Still open include:

- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`;
- `CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED`;
- `TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW`;
- `WITHIN_TYPE_GEOMETRY_DISTRIBUTION_REQUIRED`;
- `COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED`;
- `GEOMETRY_INVARIANCE_BY_ACTION_REQUIRED`;
- `POST_RETROFIT_VENTILATION_SURFACE_REQUIRED`;
- `POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED`;
- `DESIGN_OUTDOOR_TEMPERATURE_MAPPING_REQUIRED`;
- `DESIGN_INDOOR_SERVICE_CONDITION_REQUIRED`;
- `NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED`;
- B05 product/design-point coverage residuals;
- remaining CAPEX/emitter/room-action residuals.

## 11. Non-claims

P81 does not claim:

- that every programme household can be individually identified in advance;
- that three sources are automatically comparable;
- that three numbers should be equally averaged;
- that historical evidence can be promoted unchanged to 2026;
- that an optional weighted centre is exact truth;
- that current KEHOP participant frequencies represent national prevalence;
- that an exact programme scenario is OBS evidence;
- that Q-B02-004 is closed;
- that B02 readiness should increase.

B02 readiness remains **55%**.
