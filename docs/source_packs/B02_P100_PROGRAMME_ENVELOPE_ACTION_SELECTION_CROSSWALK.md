# B02-P100 — CURRENT ENVELOPE STATE -> PROGRAMME ACTION SELECTION CROSSWALK

## Goal

Resolve:

`REFERENCE_PROGRAMME_ENVELOPE_ACTION_SELECTION_CROSSWALK_REQUIRED`

without converting P99 renovation labels into physical compliance claims.

P100 connects:

`CURRENT COMPONENT PERFORMANCE -> REFERENCE PROGRAMME TARGET -> ACTION SELECTION`.

## 1. Reference programme target

P80 already supplies the reference-retrofit component U upper bounds:

- external wall: **0.24 W/m2K**;
- flat roof: **0.17 W/m2K**;
- attic floor: **0.17 W/m2K**;
- basement ceiling: **0.26 W/m2K**;
- timber/PVC window: **1.10 W/m2K** for the current prospective programme.

P103 later repaired the window target temporally: P80's **1.15 W/m2K**
is retained as historical reference-retrofit calibration, while the current
9/2023 ÉKM requirement already admitted by P92 sets **1.10 W/m2K** for
>0.5 m2 wood/PVC facade glazed openings. The current prospective programme
therefore uses 1.10 W/m2K for that window class.

P96 independently closes the pitched/heated-attic enclosing-structure gap at:

- pitched/heated-attic enclosure: **0.17 W/m2K**.

These are prospective programme/design targets. They are not observed current-stock values and they are not guaranteed realized project performance.

## 2. Component-level crosswalk

For an applicable component with a current U interval `[U_low, U_high]` and a reference target `U_ref`:

- if `U_high <= U_ref`:
  `REFERENCE_ENVELOPE_SATISFIED`;
- if `U_low > U_ref`:
  `REFERENCE_ENVELOPE_DEFICIT`;
- otherwise:
  `CURRENT_ENVELOPE_STATE_UNRESOLVED`.

A proven non-applicable component is:

`COMPONENT_NOT_APPLICABLE`.

Missing current U, unknown applicability or an interval straddling the target remains unresolved.

P100 deliberately forbids:

`UNKNOWN != DEFICIT`

and:

`UNKNOWN != SATISFIED`.

## 3. Dwelling/programme selection rule

The programme-action rule is:

`ANY PROVEN COMPONENT DEFICIT -> REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP`

`ALL APPLICABLE COMPONENTS PROVEN SATISFIED -> AIR_TO_WATER_HP_ONLY candidate`

`OTHERWISE -> PROGRAMME_ACTION_UNRESOLVED`.

The phrase **candidate** is essential.

`HP_ONLY CANDIDATE != FINAL PROGRAMME ELIGIBILITY`.

Envelope compliance does not replace thermal-distribution, hydraulic, electrical, product operating-point or other independent programme gates.

## 4. Population uncertainty

P100 does not require every dwelling to be individually observed before national modelling.

For weighted population records:

- identified HP-only mass = `H`;
- identified retrofit mass = `R`;
- unresolved mass = `Q`;
- total = `T = H + R + Q`.

Then:

`HP_ONLY share in [H/T, (H+Q)/T]`

and:

`RETROFIT_PLUS_AWHP share in [R/T, (R+Q)/T]`.

No midpoint, independence assumption or default split is admitted.

This implements the existing P81/P82 set-valued population-inference policy.

## 5. P99 evidence crosswalk

P99 provides direct national 2022 stock-state calibration:

- insulated facade: **35.0%**;
- insulated attic/ceiling: **29.7%**;
- window replaced: **52.7%**.

P100 tests these metrics against the selection semantics and keeps all three as:

`CALIBRATION_ONLY_NOT_PROGRAMME_SELECTION_AUTHORITY`.

Why:

`INSULATED FACADE != REFERENCE U COMPLIANT WALL`

`WINDOW REPLACED != REFERENCE U COMPLIANT WINDOW`

and:

`RECENT ENVELOPE ACTION != CURRENT COMPONENT PERFORMANCE`.

Therefore P99 stock-state shares cannot be inserted directly as HP_ONLY or retrofit programme shares.

## 6. Action-to-post-state mapping

P83 had already contracted the explicit reference-retrofit action-to-post-state model.

P90, P91, P95 and P96 subsequently complete the prospective reference-programme ventilation, thermal-bridge, geometry and component-U target surfaces.

P100 binds current-state selection to that already-defined target.

Therefore the stale generic blocker:

`ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED`

is resolved for the prospective reference-programme model contract.

This does **not** create a current national HP-only U surface.

## 7. New exact residual

The former blocker:

`REFERENCE_PROGRAMME_ENVELOPE_ACTION_SELECTION_CROSSWALK_REQUIRED`

becomes:

`RESOLVED_EXECUTABLE_CROSSWALK`.

The remaining population-evidence residual is the already-defined P82 requirement:

`DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED`.

That requirement can be satisfied by a representative or calibrated bounded current-state inference. Exhaustive household-by-household U measurement is not required.

## 8. Readiness effect

P100 materially improves model structure but does not invent the missing current national component-performance distribution.

Therefore:

- **B02 remains 55%**;
- **PEAK_LOAD_EFFECT remains 50%**;
- **Q-B02-004 remains OPEN_NARROWED**.

The next evidence task is now precise: find or build a defensible current Hungarian component-performance/U-state distribution that can feed this executable crosswalk.

## 9. Canonical boundaries

`INSULATED FACADE != REFERENCE U COMPLIANT WALL`

`WINDOW REPLACED != REFERENCE U COMPLIANT WINDOW`

`RECENT ENVELOPE ACTION != CURRENT COMPONENT PERFORMANCE`

`REFERENCE ENVELOPE SATISFIED != TECHNICAL HP ELIGIBILITY`

`HP ONLY CANDIDATE != FINAL PROGRAMME ELIGIBILITY`

`UNRESOLVED != RETROFIT REQUIRED`
