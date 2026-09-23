# B02-P98 — NATIONAL SET-VALUED SUPPLY-TEMPERATURE ENVELOPE

## Goal

Resolve the national reference-programme residual:

`DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`

without inventing:

- one national design-flow temperature;
- a national temperature probability distribution;
- emitter-class-to-temperature point mappings;
- W35/W45/W55 snapping.

Base:

`077e4c2405a418f5e1cd0fe4a52bef55528e6fb9`

## Existing contracts that P98 must preserve

### P65 national emitter composition

B02-P65 is already set-identified.

Hard admitted information includes:

- surface-heating/cooling presence: `0.33..0.66`;
- calibrated primary gas-convector margin: `0.233`;
- exact heating-topology controls.

Still latent:

- radiator presence;
- radiator/surface overlap;
- OTHER emitter presence;
- P21/WBL emitter allocation.

Therefore:

`EMITTER COMPOSITION SET != TEMPERATURE DISTRIBUTION`

### B06-P65 building authority

B06-P65 already requires an exact building supply temperature to come from one
of three routes:

1. room-by-room heat-loss + emitter calculation;
2. signed post-retrofit MEP design;
3. design-condition measurement.

That record/project contract remains unchanged.

P98 cannot mint a project temperature.

## External method/engineering support

### MCS 021

`SRC-B06-MCS-021-2-1-2015`

The heat-emitter guide is room/dwelling-specific and publishes design-flow
bands including:

- `<=35 C`;
- `36..40 C`;
- `41..45 C`;
- `46..50 C`;
- `51..55 C`;

and also higher-temperature bands.

The guide requires emitter selection to be repeated for every heated room.

P98 therefore uses those bands as **category-shape authority**, not as
Hungarian stock frequencies.

Important:

`MCS HAS >55 C BANDS`

therefore:

`P98 55 C CEILING != MCS PHYSICAL MAXIMUM`.

### EHI technology envelope

`SRC-B02-EHI-HMR-2024-SURFACE-PENETRATION`

The admitted EHI technology context gives:

- surface heating around `35/28 C`;
- modern radiators around `55 C or lower`;
- traditional radiator systems historically at higher temperatures.

These are technology-design references, not Hungarian population temperature
weights.

### Hungarian residential design validation

`SRC-B06-HU-ULLOI411-MEP-2024`

A real Hungarian residential MEP design contains:

- underfloor-heating design `40/35 C`;
- heat-pump point `45/40 C`;
- explicit hydraulic balancing.

It validates that low-temperature hydronic designs inside the P98 envelope are
physically used in Hungarian residential engineering.

It is new-build design, not national retrofit prevalence.

### Field validation

`SRC-B02-FRAUNHOFER-HP-TEMP-META-2023`

The field meta-analysis reports distinct but overlapping mean HP temperatures
for floor, mixed and radiator systems.

P68 also already preserves a foreign-response measured mean space-heating flow
sensitivity:

`33.046008 .. 45.388962 C`

for transfer validation only.

Therefore:

`FOREIGN OPERATING MEAN != HUNGARIAN DESIGN TEMPERATURE`.

The field evidence validates low-temperature operation and overlap semantics;
it does not produce population weights.

## Prospective programme action authority

Current Hungarian programme evidence permits:

- secondary-circuit adaptation;
- emitter modernization/replacement;
- automatic controls.

Therefore a prospective reference programme can impose a low-temperature
design contract and trigger emitter/hydraulic work when necessary.

This does not mean every current building is already <=55 C capable.

## P98 national reference-programme set

The admitted design-flow categories are:

1. `LE_35` = <=35 C
2. `C36_40` = 36..40 C
3. `C41_45` = 41..45 C
4. `C46_50` = 46..50 C
5. `C51_55` = 51..55 C

No national category probabilities are assigned.

No P21 age/group temperature differences are invented.

Because the P65 P21/WBL emitter allocation remains latent, every one of the 14
reference-programme strata carries the full category set.

Status:

`LATENT_SET_PROPAGATION_NO_POINT_WEIGHTS`.

## Why 55 C is a programme ceiling

For the prospective reference-programme scenario:

`T_flow,design <= 55 C`

is adopted as an explicit low-temperature design ceiling.

If P65 room/building calculation would require:

`T_flow,design > 55 C`

the response is **not**:

`ACCEPT HIGH TEMPERATURE BY DEFAULT`.

Instead:

`EMITTER OR HYDRAULIC ADAPTATION OR EXPLICIT EXCEPTION REQUIRED`.

The building must be recalculated after the action.

This is an intervention design rule, not an observed stock fact.

## B05 relationship

P77 already audits B05 at:

- W35;
- W45;
- W55.

P98 does not turn these labels into physical building states.

Canonical boundary:

`B05 W35/W45/W55 CONTROL POINTS != BUILDING REQUIRED SUPPLY TEMPERATURE`.

For a real/project record:

- P65 produces the exact required temperature;
- B05 evaluates that exact point if the source-supported performance map
  permits it;
- no snapping is allowed.

For national set propagation, W35/W45/W55 remain useful product-domain
coverage/control anchors across the P98 envelope.

The existing independent B05 gaps remain:

- `B05_COLD_W45_PRODUCT_GRID_REQUIRED`;
- `B05_CONTINUOUS_W55_PRODUCT_SURFACE_REQUIRED`;
- extreme-scope W35 cold-domain gap where applicable.

P98 does not resolve product-map evidence.

## P77 Gate-2 effect

P77 decomposed national materialization into:

1. national post-retrofit design-load surface;
2. national P65 supply-temperature surface;
3. B05 product design-point coverage.

P98 resolves Gate 2 as:

`NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED`

->

`RESOLVED_AS_SET_VALUED_SURFACE`.

Gate 3 remains independent.

## Q-B02-004 effect

Previous current residuals after P97:

- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`;
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`.

After P98:

`DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`

->

`RESOLVED_FOR_REFERENCE_PROGRAMME_SET_PROPAGATION`.

The narrowed current Q-B02-004 reference-programme evidence residual is:

- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`.

This does not imply complete national COP materialization because the
independent B05 product-map gates still exist.

## Realized/project boundary

For a specific building:

`REALIZED_SUPPLY_TEMPERATURE_VERIFICATION_REQUIRED`.

The existing B06-P65 authority remains mandatory.

## Frozen boundaries

`NATIONAL CATEGORY SET != NATIONAL TEMPERATURE DISTRIBUTION`

`EMITTER CLASS != FIXED SUPPLY TEMPERATURE`

`REFERENCE-PROGRAMME 55 C CEILING != PHYSICAL EQUIPMENT LIMIT`

`B05 W35/W45/W55 CONTROL POINTS != BUILDING TEMPERATURE SNAPPING`

`FOREIGN MEAN OPERATING TEMPERATURE != HUNGARIAN DESIGN TEMPERATURE`

`P98 NATIONAL SURFACE != P65 RECORD-LEVEL AUTHORITY`

## Readiness

- B02 remains **55%**
- B06 `SUPPLY_TEMPERATURE_EFFECT` remains **70%**
- B06 `B05_HANDOFF` remains **65%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**

No readiness uplift is minted solely from converting the national temperature
problem into an explicit set-propagation contract.
