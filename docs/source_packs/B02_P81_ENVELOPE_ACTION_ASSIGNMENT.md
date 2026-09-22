# B02-P81 — explicit programme envelope-action assignment contract

**State:** `NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED -> PARTIAL_RESOLVED_CONTRACTED`

**Canonical base:** `7ac15e0531ffca88c2943e16d719f93c0835638b`

**Implementation date:** 2026-09-22

## 1. Purpose

P80 materialized source-native action-conditioned post-state U constraints for:

- `AIR_TO_WATER_HP_ONLY`;
- `REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP`.

The remaining national blocker was:

`NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED`.

P81 does not invent a national envelope-retrofit percentage. It defines the exact fail-closed input required before P80 action-conditioned post-state U values may be aggregated over a declared programme population.

## 2. Current Hungarian programme calibration

The already registered official MFB authority:

`SRC-B02-HU-KEHOP-417-418-SCOPE-2026`

supports a current scope-limited policy calibration for occupied one- and multi-dwelling family houses built and permitted before 2007.

The current programme material also requires at least **30% primary-energy saving per building** and lists, among eligible intervention families:

- external-envelope insulation;
- roof/ceiling insulation;
- window replacement or upgrade;
- air-to-water heat-pump heating.

These facts constrain programme design, but they do not identify the action mix of the proposed national programme.

Canonical boundaries:

`ELIGIBLE MEASURE MENU != NATIONAL ACTION ASSIGNMENT`

`AGE / ELIGIBILITY SCOPE != ACTION FREQUENCY`

`30% PRIMARY-ENERGY SAVING REQUIREMENT != ENVELOPE-RETROFIT SHARE`

## 3. Explicit assignment domain

P81 admits exactly two P80-compatible envelope action states:

1. `AIR_TO_WATER_HP_ONLY`
2. `REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP`

Every assignment row must contain:

- an explicit population key;
- assigned dwelling-equivalents;
- one admitted action;
- an explicit assignment class;
- non-empty authority/provenance.

Allowed assignment classes:

- `SCN_EXPLICIT_PROGRAMME_ASSIGNMENT`
- `POL_EXPLICIT_PROGRAMME_RULE`

A programme scenario assignment is not promoted to observed current-stock evidence.

`PROGRAMME SCENARIO ASSIGNMENT != OBSERVED CURRENT STOCK`

## 4. Coverage gate

For a declared programme population `N`:

`sum(assigned dwelling-equivalents) == N`

is mandatory.

The gate rejects:

- empty assignment;
- duplicate population keys;
- negative assigned populations;
- unsupported actions;
- missing assignment authority;
- unsupported assignment class;
- incomplete or over-complete population closure.

No unassigned remainder is silently mapped to HP-only, envelope retrofit, midpoint, or majority action.

`INCOMPLETE ASSIGNMENT != HIDDEN DEFAULT`

## 5. Blocker effect

Previous:

`NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED`

P81:

`PARTIAL_RESOLVED_CONTRACTED`

The vague national-assignment blocker is replaced by the exact residual:

`EXPLICIT_PROGRAMME_ACTION_ASSIGNMENT_REQUIRED`

This is now a programme-policy/scenario input rather than a missing external stock statistic.

P81 therefore narrows the P80 U-state chain without fabricating national action prevalence.

## 6. Remaining P80/P78 physical residuals

Still open include:

- `EXPLICIT_PROGRAMME_ACTION_ASSIGNMENT_REQUIRED`;
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

## 7. Non-claims

P81 does not claim:

- that all pre-2007 family houses receive envelope retrofit;
- that 30% primary-energy saving implies a 30% envelope action share;
- that current KEHOP participant frequencies represent the national stock;
- that the proposed two-million-household programme has a known HP-only/envelope+HP split;
- that a scenario assignment is OBS evidence;
- that Q-B02-004 is closed;
- that B02 readiness should increase.

B02 readiness remains **55%**.
