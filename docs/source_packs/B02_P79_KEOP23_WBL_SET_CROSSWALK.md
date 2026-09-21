# B02-P79 — KEOP23 / P21-WBL set-valued archetype crosswalk

**State:** `PUBLIC 23-TYPE GEOMETRY MATERIALIZED / FULL SET COVERAGE / POINT TYPE NOT IDENTIFIED`

**Canonical base:** `80f84e4daf3fa1bb3b621b2802915b320eb8194b`

**Implementation date:** 2026-09-21

## 1. Purpose

P78 established that a public Hungarian 23-type physical model source exists.

P79 performs the next required operation:

`PUBLIC KEOP23 SOURCE -> MACHINE-READABLE TYPES -> SET-VALUED P21/WBL CROSSWALK`.

It does **not** choose one archetype where the source categories and WBL bands
do not identify one.

## 2. Source-native 23-type matrix

Primary authority:

`SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022`.

The source 6.1 matrix defines:

- types 1-12: family/row houses, 1-3 dwellings;
- types 13-16: small multifamily, 4-9 dwellings;
- types 17-23: large multifamily, 10+ dwellings.

It distinguishes:

- construction periods;
- adobe / conventional masonry / block-cast-concrete / panel technology;
- for family types 5-12, useful floor area below or at/above 120 m2.

The source 6.2 and 6.3 illustrations resolve otherwise compressed period
semantics for the pre-1944 adobe types and industrial/panel types.

## 3. Public geometry materialization

P79 materializes source Table 14.7 for all **23 types** into:

`data/processed/b02/keop23_synthetic_geometry.csv`.

Fields include:

- model dwelling count;
- occupants per dwelling;
- storeys;
- ceiling height;
- building bounding x/y;
- total floor area;
- heated floor area;
- derived heated floor area per model dwelling;
- maximum usable roof area.

Examples:

- type 1: heated **69.9 m2**;
- type 6: heated **150.1 m2**;
- type 12: heated **233.8 m2**;
- type 20: **5,513.5 m2** heated / 76 model dwellings;
- type 23: **2,963.1 m2** heated / 49 model dwellings.

The per-dwelling field is a transparent division of the source synthetic
building heated area by its source model dwelling count.

## 4. Crosswalk principle

The WBL construction-period bands are not the same as KEOP23 periods.

Examples:

- `Y1946-1960` crosses the source 1959/1960 boundary;
- `Y1961-1980` crosses the 1979/1980 boundary;
- `Y1981-2000` spans the source 1980-1989 and 1990-2005 types;
- `Y2001-2010` spans the source 1990-2005 and 2006+ types.

Therefore:

`WBL PERIOD -> KEOP23 TYPE`

is generally one-to-many.

P79 stores all **14** period x building-group rules:

`7 WBL periods x 2 P21 building groups`.

Every rule is validated against exact year-interval overlap.

## 5. Why building group does not identify the final type

P21 provides calibrated:

- `FAMILY_HOUSE`;
- `MULTI_DWELLING`.

But KEOP23 further separates:

- family building size;
- small versus large multifamily;
- conventional versus industrial/panel technology.

P21 does not directly identify those subtypes.

Accordingly all 14 source-semantic states have between **2 and 5 candidate
types**.

Canonical boundary:

`FULL TYPE-SOURCE COVERAGE != POINT TYPE IDENTIFICATION`.

## 6. Wall material is deliberately not used yet

WBL contains `WALL1..WALL6`.

KEOP23 contains explicit construction technology.

P79 does not infer the code semantics merely because both concern walls.

Therefore:

`WBL WALL CODE != KEOP WALL TECHNOLOGY WITHOUT AN ADMITTED CODE CROSSWALK`.

A future exact KSH codelist crosswalk may tighten type sets. It is not required
for a valid broad set.

## 7. Floor-area category is deliberately not used as a hard filter

KEOP types 5-12 split family buildings at **120 m2 useful building floor
area**.

WBL `LAT_V` describes a **dwelling floor-area category**.

For a multi-dwelling building, or even a 2-3 dwelling family/row building,
those semantics are not equal.

Therefore:

`WBL DWELLING FLOOR AREA != KEOP BUILDING USEFUL FLOOR AREA`.

P79 retains the KEOP size split in the candidate set instead of removing a
candidate from an unsupported semantic bridge.

## 8. Geometry use boundary

The 23 values are **synthetic average buildings** derived from the survey/model.

They are not minimum/maximum measurements for all households in a type.

P79 may therefore compute:

- candidate-set minimum synthetic type mean;
- candidate-set maximum synthetic type mean;
- P21-weighted national calibration sensitivity.

But:

`CANDIDATE-TYPE MIN/MAX != WITHIN-TYPE POPULATION CONFIDENCE INTERVAL`.

They cannot be presented as observed household bounds.

## 9. Exact national CI materialization

The full canonical P21/WBL run produces:

- WBL rows: **116,452**;
- occupied dwellings: **4,008,541**;
- KEOP23 types: **23**;
- crosswalk rules: **14**;
- candidate count per period/group state: **2 to 5**;
- point-identified period/group states: **0**.

P21 expected building-group controls reconcile to:

- FAMILY_HOUSE: **2,423,136**;
- MULTI_DWELLING: **1,585,405**.

Candidate-set population coverage is complete under both P21 structural
scenarios:

- CENTRAL: **4,008,541 / 4,008,541**;
- FLAT: **4,008,541 / 4,008,541**.

The population-weighted candidate synthetic-type mean heated-area sensitivity
is:

- CENTRAL: **75.5198943961–138.4494421084 m2/dwelling**;
- FLAT: **75.4073577378–138.7518104318 m2/dwelling**.

These intervals are deliberately labelled **synthetic-geometry calibration
envelopes**.

They are not:

- household observed ranges;
- confidence intervals;
- within-type min/max values;
- a national heated-floor-area point estimate.

## 10. P78 blocker effect

Previous:

`HEATED_AREA_OR_DIRECT_GEOMETRY_SURFACE_REQUIRED`.

P79:

`PARTIAL_RESOLVED_SET_VALUED_CALIBRATION`.

The source-acquisition part is resolved.  The full national archetype space is
covered by explicit type sets.

Remaining before production B06 design-load bounds:

1. `WITHIN_TYPE_GEOMETRY_DISTRIBUTION_REQUIRED`;
2. `COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED`.

The broader post-state geometry blocker narrows to:

- `COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED`;
- `ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED`;
- `GEOMETRY_INVARIANCE_BY_ACTION_REQUIRED`.

## 11. What P79 does not change

Still open:

- post-retrofit component U-value surface;
- post-retrofit ventilation;
- separate thermal-bridge term;
- design outdoor temperature mapping;
- explicit indoor service condition;
- action-to-post-state physical mapping;
- P65 national supply-temperature surface;
- B05 product-map coverage;
- P76 cost/action residuals.

## 12. Non-claims

P79 does not claim:

- a unique KEOP type for any WBL period/group;
- WBL wall-code semantics not yet pinned;
- equality of WBL dwelling area and KEOP building useful area;
- the synthetic mean is an observed household;
- type-min/type-max is a statistical confidence interval;
- 2015 survey state equals 2026 post-retrofit state;
- Q-B02-004 is resolved.

B02 readiness remains **55%**.
