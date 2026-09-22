# B02-P90 — REFERENCE-PROGRAMME AIRTIGHTNESS TARGET

## Goal

Close the P89 residual for the **prospective national reference-programme model** without inventing an observed future airtightness distribution.

Previous residual:

`POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED`

P90 chooses the second admissible route: an explicit **programme/model target**.

Base:
`37a253889a890c75a34ff3048cb42d8fa206494f`

## Authoritative basis

### Current Hungarian energy rules

`SRC-B06-HU-ENERGY-RULES-2023`

The current 9/2023. (V. 25.) ÉKM framework defines the reference building with **good-airtightness windows**.

This is a regulatory reference-state assumption.

It is not:

- an observed national retrofit result;
- a blower-door n50 requirement;
- proof of project commissioning performance.

### Current Hungarian calculation method

`SRC-B06-HU-ENERGY-METHOD-2023`

P87 already pinned the current-method good-airtightness infiltration cases:

- one facade: `n_filt = 0.03 1/h`
- multiple facades / ventilation shaft: `n_filt = 0.06 1/h`

P90 does not change those values.

It changes their **model role**:

P87:
`GOOD_AIRTIGHTNESS_SENSITIVITY_ONLY`

P90:
`QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET`

## Why this is legitimate

The national model is prospective.

Future programme design states do not have to masquerade as future observations.

The required distinction is:

`PROGRAMME TARGET != OBSERVED FUTURE STATE`

P88 already established that ventilation-system path can be a programme/project state rather than a future prevalence observation.

P90 applies the same principle to airtightness.

## Current MFB programme non-equivalence control

`SRC-B06-HU-OFP-KEHOP-2026`

The inspected current official MFB programme page states:

- at least 30% primary-energy saving per building;
- eligible measures including insulation and window replacement.

The inspected public page does **not** state a building-level `n50` target.

Therefore P90 does not call the 0.03..0.06 target:

- an MFB eligibility condition;
- an MFB commissioning threshold;
- a current programme legal requirement.

It is an explicit **reference-programme SCN target grounded in the current Hungarian calculation method**.

## Facade-condition uncertainty

P90 does not invent a national facade-condition share.

The target is:

- `ONE_FACADE -> 0.03 1/h`
- `MULTIPLE_FACADES_OR_VENTILATION_SHAFT -> 0.06 1/h`
- unresolved national facade condition -> **set-valued 0.03..0.06 1/h**

No midpoint is permitted.

## 14-stratum materialization

P90 promotes the exact P87 good-airtightness sensitivity surface into explicit target semantics across all 14 WBL-period x P21-building-group strata.

Global target edges:

- `n_filt = 0.03 .. 0.06 1/h`
- `H_vent = 26.957426806 .. 123.72696 W/K`
- ventilation-only `Q_vent = 0.808722804 .. 3.95926272 kW`

The Q range uses the existing:

- 20 C residential service/reference temperature;
- P86 current-standard outdoor design domain of -12..-10 C.

These are **ventilation-component** values, not total building design heat load.

## P88/P89 compatibility

P88 remains authoritative for path physics:

- natural/window ventilation;
- regulated exhaust;
- mechanical heat recovery.

P90 supplies the absolute infiltration target.

For HRV:

- P90 supplies the target infiltration component;
- P88 still requires explicit project/procurement `eta`;
- no heat recovery is silently credited to infiltration.

P89 remains authoritative for:

- measured retrofit response;
- n50/q50/n4 distinctions;
- Hungarian n50->4Pa pressure transfer;
- realized/project evidence pathways.

## Blocker result

Previous:

`POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED`

Current prospective reference-programme status:

`RESOLVED_FOR_REFERENCE_PROGRAMME_SCENARIO`

The `POST_RETROFIT_VENTILATION` input no longer blocks the prospective national reference-programme design-load surface.

## Realized/ex-post boundary

A design target does not prove attainment.

For a claim that a completed dwelling actually achieved the target:

`REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED`

Admissible routes include:

- blower-door measurement;
- qualified commissioning evidence;
- equivalent project-level measurement/evidence under an approved method.

This record-level residual does **not** block the prospective national programme scenario.

## Frozen boundaries

`REFERENCE PROGRAMME TARGET != OBSERVED POST-RETROFIT STATE`

`REFERENCE PROGRAMME TARGET != CURRENT MFB N50 REQUIREMENT`

`GOOD-AIRTIGHTNESS METHOD CLASS != BLOWER-DOOR N50`

`UNRESOLVED FACADE CONDITION -> SET 0.03..0.06, NOT MIDPOINT`

`DESIGN TARGET != REALIZED COMMISSIONED PERFORMANCE`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

The ventilation input is now qualified for the prospective reference-programme branch, but independent geometry, transmission, thermal-bridge, location and supply-temperature residuals still prevent complete national B06 design-load closure.
