# B02-P87 — bounded post-retrofit ventilation / infiltration H_vent surface

**State:** `14-STRATUM H_VENT + Q_VENT MATERIALIZED / POPULATION PREVALENCE STILL Q`

## 1. Purpose

P87 converts the previous broad ventilation blocker into an executable physical
design-load component.

Inputs already available before P87:

- P85: 14-stratum heated-volume envelopes;
- P86: current-standard design-outdoor-temperature domain `-12..-10 C`;
- current Hungarian building-energy calculation method;
- BME 2026 Type-5 empirical ventilation/infiltration calibration.

P87 does not turn a Type-5 distribution into an all-Hungary distribution.

## 2. Current Hungarian method authority

Source:

`SRC-B06-HU-ENERGY-METHOD-2023`

The official government calculation method states:

### 2.1 Residential required ventilation

Appendix 2 Table 2.1:

`n_szüks = 0.5 1/h`

for the whole residential building.

The same table gives a residential heating reference temperature of:

`20 C`.

These are calculation-method/service-reference values.

Therefore:

`REQUIRED RESIDENTIAL AIR CHANGE != OBSERVED POPULATION AIR CHANGE`

and:

`20 C METHOD REFERENCE != OBSERVED HOUSEHOLD SETPOINT`

### 2.2 Air volumetric heat capacity

Appendix 1 section 6.2 uses:

`0.35 Wh/m3K`

for ventilation heat-transfer calculations.

### 2.3 Natural ventilation and infiltration

The current method separates required ventilation from additional infiltration.

For natural ventilation:

`H_vent = 0.35 * (n_required + n_filt) * V`

for full-use residential operation.

Appendix 2 Table 2.4 provides infiltration values by:

- airtightness quality;
- opening/facade arrangement;
- storey/exposure condition.

Across the listed method cases:

`0.00 <= n_filt <= 1.00 1/h`.

The method also provides a good-airtightness sensitivity:

- one-facade case: `0.03 1/h`;
- multiple-facade / ventilation-shaft case: `0.06 1/h`.

P87 does not assume that every reference retrofit automatically reaches the
good-airtightness class.

## 3. BME 2026 empirical calibration

Source:

`SRC-B02-BME-RBSM-2026`

For the examined Hungarian Type-5 detached-house archetype, the BME paper
reports:

### Ventilation

The EPC database was rejected for this parameter because the default
`0.5 1/h` dominated the records.

Instead the authors derived ventilation from:

- `30 m3/h/person`;
- REKK representative building-use survey occupant counts.

They fitted a lognormal distribution and truncated sampling to the source-derived
range:

`0.110 .. 0.860 1/h`.

### Infiltration

The repaired Type-5 infiltration parameter is modelled as:

- mean: `0.280 1/h`;
- standard deviation: `0.100 1/h`;
- Normal distribution.

These are valuable empirical calibration parameters.

But:

`TYPE-5 EMPIRICAL DISTRIBUTION != ALL-ARCHETYPE POST-RETROFIT DISTRIBUTION`

Therefore the BME values validate scale and uncertainty structure; they are not
used to assign post-retrofit population prevalence to the 14 national strata.

## 4. 14-stratum current-method H_vent surface

P87 materializes:

`data/processed/b02/p87_post_retrofit_ventilation_hvent_surface.csv`

Grain:

`7 WBL periods x 2 P21 building groups = 14 strata`.

Each row inherits the P85 heated-volume candidate-set envelope.

The current-method bounded natural-ventilation calculation is:

`H_vent,lower = 0.35 * (0.5 + 0.0) * V_lower`

`H_vent,upper = 0.35 * (0.5 + 1.0) * V_upper`

Global descriptive stratum-edge range:

**25.431534722 .. 331.4115 W/K**

This is a complete 14-stratum physical scenario surface.

It is not a national probability interval.

## 5. Ventilation design-load component

Using:

- residential indoor method reference: `20 C`;
- P86 current-standard outdoor domain: `-12 .. -10 C`;

P87 materializes the ventilation-only design-load contribution.

Lower bound:

`Q_vent,lower = H_vent,lower * (20 - (-10)) / 1000`

Upper bound:

`Q_vent,upper = H_vent,upper * (20 - (-12)) / 1000`

Global descriptive stratum-edge range:

**0.762946042 .. 10.605168 kW**

This is:

`VENTILATION DESIGN-LOAD COMPONENT`

not:

`TOTAL BUILDING DESIGN HEAT LOAD`.

## 6. Good-airtightness sensitivity

P87 additionally materializes a clearly separated sensitivity layer using
the current-method good-airtightness values:

`n_filt = 0.03 .. 0.06 1/h`.

Global descriptive H_vent edge range:

**26.957426806 .. 123.72696 W/K**

Corresponding ventilation-only design-load edge range:

**0.808722804 .. 3.95926272 kW**

This branch is explicitly:

`GOOD_AIRTIGHTNESS_SENSITIVITY_ONLY`.

It is not the default state of the reference-retrofit programme.

## 7. Why the broad ventilation blocker changes

Before P87:

`DEFENSIBLE_POST_RETROFIT_VENTILATION_INFERENCE_REQUIRED`

was a generic missing physical-input blocker.

After P87:

`PARTIAL_RESOLVED_CURRENT_METHOD_HVENT_SURFACE`

because:

- required residential ventilation is numerically bound;
- air heat capacity is numerically bound;
- the official infiltration method-domain is numerically bound;
- heated volume is already materialized for 14 strata;
- H_vent is executable for all 14 strata;
- ventilation-only peak-load contribution is executable for all 14 strata;
- an empirical Hungarian Type-5 calibration exists independently.

What remains is no longer "unknown ventilation physics".

The residual is now population/system assignment:

1. `POST_RETROFIT_AIRTIGHTNESS_CLASS_PREVALENCE_REQUIRED`
2. `POST_RETROFIT_MECHANICAL_VENTILATION_PREVALENCE_REQUIRED`
3. `POST_RETROFIT_HEAT_RECOVERY_EFFICIENCY_DISTRIBUTION_REQUIRED`
4. `ACTION_TO_AIRTIGHTNESS_AND_VENTILATION_SYSTEM_MAPPING_REQUIRED`

## 8. Mechanical ventilation / HRV boundary

The official method provides separate formulas for continuous mechanical
ventilation with heat recovery.

P87 does not collapse HRV into the natural-ventilation envelope.

Therefore:

`NATURAL VENTILATION H_VENT != HRV H_VENT`.

A programme branch with mechanical ventilation must explicitly provide:

- fresh-air flow;
- infiltration;
- heat-recovery efficiency;
- system prevalence / action assignment.

## 9. B06 handoff

P87 gives B06 a usable bounded ventilation component:

- volume from P85;
- `n_required = 0.5 1/h`;
- `n_filt` bounded by current-method authority;
- `c_air = 0.35 Wh/m3K`;
- indoor reference 20 C;
- current outdoor design domain from P86.

This means a full B06 design-load calculation is no longer blocked by the
absence of any ventilation model.

It remains blocked by independent transmission / thermal-bridge / exact
population-assignment gaps.

## 10. Q-B02-004

Q-B02-004 remains:

`OPEN_NARROWED`.

P87 removes the generic ventilation-physics blocker and replaces it with
airtightness / HRV population-assignment residuals.

Still independent:

- net wall/window split;
- actual top/bottom heat-loss planes;
- bounding-geometry validation;
- pitched-roof post-state U;
- thermal-bridge correction;
- complete location-to-current-standard zone mapping;
- national P65 supply-temperature inference;
- fresh envelope-action evidence.

## 11. Readiness

B02 remains **55%**.

Reason:

P87 materializes a complete ventilation-loss component, but the total national
design-load surface is still incomplete because transmission component areas
and thermal bridges remain unresolved and post-retrofit ventilation-system
prevalence is not yet a population distribution.

No arbitrary module-level percentage uplift is applied.
