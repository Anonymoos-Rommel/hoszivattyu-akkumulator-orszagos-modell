# B02-P86 — current Hungarian design-outdoor-temperature authority

**State:** `CURRENT STANDARD DOMAIN MATERIALIZED / PUBLIC CITY ANCHORS MATERIALIZED / COMPLETE NATIONAL ZONE GEOMETRY Q`

## 1. Purpose

P86 repairs an important temporal error risk in the national design-load chain.

The old Hungarian three-zone practice:

`-15 / -13 / -11 C`

is not treated as the current 2026 standard map.

Current authority:

`MSZ 24140:2026`

valid from:

`2026-04-01`

The official MSZT metadata identifies MSZ 24140:2026 as the current standard and states that it replaced MSZ 24140:2015.

The official MSZT public news states that the revised standard contains a new map of guiding design outdoor temperatures for heating heat-load calculation.

## 2. Public current-standard numeric domain

The exact copyrighted F1 map is not copied into the repository.

A current public engineering interpretation of MSZ 24140:2026 reports three map values:

- **-12 C**
- **-11 C**
- **-10 C**

Therefore P86 admits the bounded current-standard domain:

`CURRENT_STANDARD_DESIGN_OUTDOOR_DOMAIN = [-12, -10] C`

This is a valid bounded design-temperature input for current-standard sensitivity work.

It is not a national single point.

## 3. Public map control points

P86 materializes:

`data/processed/b02/p86_current_design_temperature_city_anchors.csv`

Twenty named city/map control points are preserved from the public technical interpretation.

### -12 C anchors

- Békéscsaba
- Debrecen
- Nyíregyháza
- Sopron area

### -11 C anchors

- Budapest
- Eger
- Győr
- Kecskemét
- Miskolc
- Salgótarján
- Szeged
- Szolnok
- Szombathely
- Tatabánya
- Zalaegerszeg

### -10 C anchors

- Kaposvár
- Pécs
- Székesfehérvár
- Szekszárd
- Veszprém

The public interpretation additionally reports a smaller -10 C area north of Győr.

P86 does not reconstruct a national polygon from prose.

## 4. Application boundary

The public technical interpretation reports that the map baseline is intended for:

- settlements above 30,000 population;
- elevations not exceeding 300 m.

It also reports that local urban heat-island, sensitive-function and risk considerations may justify project-specific deviations.

P86 therefore does not turn those adjustment ranges into population defaults.

Outside the baseline scope:

`LOCAL DESIGN AUTHORITY REQUIRED`

For a specific project, an explicit current-standard zone or project design authority remains the preferred record-level input.

## 5. Fail-closed resolver

New module:

`modules/B02/design_outdoor_temperature_current.py`

It can:

1. return the current standard national zone domain;
2. resolve the 20 named public city anchors;
3. accept an explicitly supplied current-standard zone value;
4. require settlement-population and elevation admission;
5. accept a project adjustment only when that adjustment has explicit authority.

Unknown non-anchor locations remain:

`Q_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE`

with residual:

`MACHINE_READABLE_CURRENT_STANDARD_ZONE_GEOMETRY_REQUIRED`

## 6. Critical layer separation

### 6.1 Government 2023 Meteo standard year

The Energiaügyi Minisztérium 2023 calculation-method page publishes a `Meteo` standard-year dataset for building-energy calculations.

That layer is retained.

But:

`GOVERNMENT METEO STANDARD YEAR != DESIGN OUTDOOR TEMPERATURE MAP`

The standard-year hourly distribution must not be substituted for the MSZ 24140:2026 design-temperature map.

### 6.2 B05-P9 historical extreme weather

B05-P9 materialized a project-derived empirical 10-year cold-stress envelope:

`-13.331944 .. -9.644444 C`

for the coldest 72-hour mean across five stations.

That is a stress-scenario layer.

Therefore:

`B05-P9 HISTORICAL EXTREME STRESS != DESIGN OUTDOOR TEMPERATURE`

The two layers may both be used in the programme:

- MSZ 24140:2026 for current design-load boundary conditions;
- B05-P9 for historical extreme-weather stress testing.

They are not interchangeable.

## 7. Old map retirement

P86 explicitly retires:

`-15 / -13 / -11 C`

as the current-standard map.

Historical project documents using -13 C remain valid historical evidence for their own calculation cases.

They are not silently rewritten.

Example:

- the 2015 Zalavár calculation remains a valid 2015 source-native 20/-13 C case;
- it does not authorize -13 C as the current 2026 national default.

## 8. Blocker effect

Previous broad blocker:

`DEFENSIBLE_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE_MODEL_REQUIRED`

P86 state:

`PARTIAL_RESOLVED_CURRENT_STANDARD_DOMAIN`

Resolved/narrowed:

- current standard identity;
- effective date;
- current zone value set;
- current national bounded domain;
- public named city anchors;
- old-map retirement;
- standard-year / observed-weather separation;
- fail-closed location resolver.

Remaining:

1. `COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`
2. `LOCAL_DESIGN_AUTHORITY_REQUIRED_OUTSIDE_BASELINE_SCOPE`

The full national polygon assignment is not fabricated from a copyrighted map.

## 9. B06 handoff

The B02/P78 design-load input coverage now changes from:

`DESIGN_OUTDOOR_TEMPERATURE = Q / unknown map`

to:

`DESIGN_OUTDOOR_TEMPERATURE = PARTIAL_CURRENT_STANDARD_ZONE_DOMAIN / -12..-10 C`

This allows bounded B06 design-load sensitivity over the current-standard zone domain before the exact national spatial crosswalk is complete.

It does not authorize a location-specific point unless the exact current-standard zone is admitted.

## 10. Q-B02-004

Q-B02-004 remains:

`OPEN_NARROWED`

P86 removes an outdated/current-standard ambiguity and materializes a numeric physical input range.

Still independent:

- net wall/window split;
- top/bottom heat-loss planes;
- pitched-roof U;
- ventilation;
- thermal bridges;
- national P65 supply-temperature inference;
- fresh envelope-action evidence.

## 11. Readiness

B02 remains **55%**.

Reason:

the design-temperature dimension is materially stronger, but the complete national B06 design-load and B05/P65 response surface is still not executable.

No arbitrary readiness uplift is applied.
