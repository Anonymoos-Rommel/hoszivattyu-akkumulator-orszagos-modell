# B02-P78 — national post-retrofit design-load input coverage

**State:** `NATIONAL POPULATION KEYS MATERIALIZED / ARCHETYPE CALIBRATION AVAILABLE / POST-STATE PHYSICS PARTIAL-Q`

**Canonical base:** `245b5c15b7d4dec04478abf460df234be4de28fa`

**Implementation date:** 2026-09-21

## 1. Purpose

P77 established:

`METHOD EXISTS != NATIONAL INPUT SURFACE EXISTS`.

P78 audits the first ordered response gate:

`NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED`.

The objective is not to manufacture a national kW value. It is to identify the
exact B06 design-load inputs already present on the national population grain
and the exact physical fields still missing.

## 2. National population-key layer already exists

The canonical 2022 KSH WBL011 full-stock joint contains:

- county;
- settlement type;
- construction period;
- wall-material category;
- floor-area category;
- comfort;
- heating mode;
- heating fuel.

Exact controls:

- **116,452 returned full-joint cells**;
- **4,008,541 occupied dwellings**.

P21 additionally binds calibrated:

- `FAMILY_HOUSE`;
- `MULTI_DWELLING`

probabilities to those exact cells.

This means the design-load problem is no longer a generic missing-national-
archetype problem.

But:

`NATIONAL POPULATION KEY COVERAGE != PHYSICAL STATE PARAMETERIZATION`.

## 3. WBL boundaries

### Wall material

WBL carries a source-native wall-material **category**.

It does not carry the complete physical construction or post-retrofit thermal
transmittance.

Therefore:

`WALL-MATERIAL CATEGORY != COMPONENT U-VALUE`.

### Floor area

WBL carries eight floor-area bands.

That is useful as an observed constraint, but:

`WBL FLOOR-AREA BAND != HEATED FLOOR-AREA POINT`.

Especially:

`SQM_GE120`

has no source-native finite upper endpoint. No arbitrary midpoint is admitted.

## 4. Strong Hungarian archetype calibration authority

The 2026 BME Residential Building Stock Model paper states that the 2015
KEOP-7.9.0/12-2013-0019 project used a **representative detailed survey of
2,029 residential buildings** and created **23 synthetic average buildings**:

- 12 single-family types;
- 11 multi-family types.

The types are differentiated by construction period, technology and size.

The study states that geometric and building-physics characteristics were
constructed from certificate-database averages.

This is materially stronger than treating one TABULA example house as a
national archetype.

P78 therefore admits:

`23-TYPE HUNGARIAN SYNTHETIC-AVERAGE LAYER = CALIBRATION AUTHORITY`.

It does not admit:

`23-TYPE HISTORICAL SYNTHETIC AVERAGE = 2026 POST-RETROFIT STOCK OBSERVATION`.

## 5. EPISCOPE average-building semantics

EPISCOPE defines a synthetic average building as a theoretical building whose
geometrical and thermophysical characteristics equal the average of the stock
subset represented.

This validates the modelling object itself.

The Budaörs 2015 case explicitly states that national average buildings from a
BME model based on an approximately 2,000-building survey were applied.

However Budaörs is a local case study and the data are historical.

Allowed use:

- method-shape validation;
- archetype calibration;
- parameter plausibility;
- potential mapping target for a future P21/WBL crosswalk.

Forbidden use:

- current national prevalence from Budaörs;
- direct 2026 post-retrofit point values;
- automatic transfer to all WBL cells.

## 6. What the 2026 BME paper resolves and exposes

For the examined Type-5 family-house archetype the paper publishes:

- heated floor area **103.4 m2**;
- EPC-derived distributions for wall, attic, ground-floor, door and window
  U-values;
- infiltration distribution;
- survey-derived ventilation distribution.

These are useful calibration/priors for that archetype.

The same paper explicitly reports that survey databases do **not** contain
reliable distribution information for:

- thermal bridges;
- several geometry parameters.

This is useful negative evidence. Those fields remain Q rather than receiving
hidden defaults.

## 7. Current B06 peak-load input audit

B06 requires:

`Q_design = (H_trans + H_vent + H_thermal_bridge) * (T_indoor - T_outdoor)`.

The current national state is:

| Input layer | Status |
|---|---|
| geography / settlement | MATERIALIZED OBS |
| construction period | MATERIALIZED OBS |
| wall-material category | MATERIALIZED OBS |
| dwelling floor-area band | MATERIALIZED OBS / SET-BOUNDED |
| calibrated building type | MATERIALIZED ASS |
| heated area / direct geometry | Q |
| post-retrofit envelope geometry | Q |
| all-type action-conditioned post U-values | Q |
| post-retrofit ventilation | PARTIAL archetype calibration / national Q |
| post-retrofit thermal bridges | Q |
| design outdoor temperature mapping | Q |
| design indoor service condition | Q |
| action -> explicit post-state physics | Q |

## 8. Blocker repair

Old:

`NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED`.

P78:

`PARTIAL_RESOLVED_INPUT_COVERAGE_DECOMPOSED`.

Concrete residual:

1. `HEATED_AREA_OR_DIRECT_GEOMETRY_SURFACE_REQUIRED`;
2. `POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED`;
3. `POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED`;
4. `POST_RETROFIT_VENTILATION_SURFACE_REQUIRED`;
5. `POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED`;
6. `DESIGN_OUTDOOR_TEMPERATURE_MAPPING_REQUIRED`;
7. `DESIGN_INDOOR_SERVICE_CONDITION_REQUIRED`;
8. `ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED`.

This is a materially smaller research problem than “find national design
loads”.

## 9. Why P78 does not calculate national peak kW yet

The physical contract forbids:

`ANNUAL ENERGY -> DESIGN PEAK`.

P78 also forbids:

- choosing floor-area midpoints without authority;
- inferring envelope areas from dwelling area alone;
- mapping a wall-material code directly to one U-value;
- setting thermal bridges to zero;
- using 0.5 ACH as a hidden national default;
- using one indoor or outdoor design temperature without an explicit
  programme/location contract;
- turning the Type-5 archetype into all Hungary.

## 10. Next blocker attack

The highest-value next work is to reduce the eight residual fields using the
23-type Hungarian synthetic-average lineage and current Hungarian retrofit
requirements.

The preferred sequence is:

1. acquire/materialize the **23-type geometry/physical parameter table** if a
   lawful public representation can be found;
2. bind current retrofit actions to **post-state U-value / geometry /
   ventilation** outcomes;
3. materialize the national design-outdoor-temperature map;
4. make the design-indoor service condition an explicit programme contract;
5. then run B06 design load on the admissible set rather than a midpoint house.

## 11. Non-claims

P78 does not claim:

- a national post-retrofit design-load distribution;
- that the historical KEOP average buildings are current observations;
- that Type 5 represents every family house;
- that all 23 type parameter tables are publicly materialized in the repo;
- that WBL floor-area bands equal heated floor area;
- that wall material determines U-value;
- that annual primary energy determines peak load;
- that Q-B02-004 is resolved.

B02 readiness remains **55%**.
