# B02-P16 — Current building-type direct-link authority hardening

**Status:** `CURRENT CLASSIFICATION EXISTS / NO PUBLIC OCCUPIED-WBL DIRECT LINK AUTHORITY / Q-B02-002 REMAINS OPEN`

**Base:** B02-P15 merged main `25f9b1aae0fd18f80ee34c3c818a412e4c7f00c7`

**Audit date:** 2026-09-05

## Purpose

B02-P15 materialized the complete source-native WBL011 occupied-stock joint. The next current-stock blocker is the building-type link.

P16 re-audits the strongest already-registered current KSH evidence and hardens the direct-authority gate so that a coarse building-type margin cannot be silently expanded across WBL subcells.

Canonical boundaries:

`CURRENT BUILDING-TYPE CLASSIFICATION EXISTS != PUBLIC OCCUPIED-STOCK DISTRIBUTION != WBL DIRECT-LINK AUTHORITY`

`COARSE BUILDING-TYPE MARGIN != WBL SUBCELL JOINT`

`MATCHED MARGINS != DIRECT LINK`

`MODELLED ENERGY-BIN COUNTS != COMPLETE BUILDING-TYPE STOCK DISTRIBUTION`

`OCCUPANCY FIELD EXISTS != OCCUPIED BUILDING-TYPE TABLE PUBLISHED`

## 1. Strongest current KSH evidence

Existing source IDs:

- `SRC-B02-KSH-ENERGY-2025`;
- `SRC-B02-KSH-ENERGY-METHOD-2025`.

The KSH experimental-statistics methodology states that the 2022 Census enumerated the complete housing stock and that the energy-certificate linkage was performed against the 2022 census dwelling-stock table through address identifiers. It reports **4,580,538 dwellings** in the census stock and **279,020** linked dwelling records with energy certificates.

The methodology also proves that current building-type classification exists in the KSH analytical surface:

- separate models were fitted for `családi ház` and `társasházi lakás`;
- settlement type and construction period are model variables;
- the apartment model uses the number of dwellings in the building and building height;
- occupancy information is available in the census database and is used in the published analysis.

This is stronger than the P8 questionnaire/static-table finding. It proves that KSH can distinguish current building types inside its 2022 full-stock analytical data environment.

It does **not** prove that the repository has a public occupied-stock building-type distribution or a reproducible WBL-compatible join key.

## 2. Existing published chart counts are not a complete stock authority

The already materialized KSH energy benchmark rows contain published energy-bin dwelling counts by building type and construction period.

Exact current repository controls:

- `FAMILY_HOUSE`: **2,881,310** dwellings in the published energy bins;
- `MULTI_DWELLING`: **1,694,480** dwellings in the published energy bins;
- combined published-bin total: **4,575,790**;
- KSH 2022 census dwelling-stock total: **4,580,538**;
- residual: **4,748** dwellings.

These counts are attached to the KSH modelled primary-energy distribution and do not form an exact complete building-type stock margin. More importantly, they are not restricted to the `DW_OC` occupied-dwelling universe and are not published jointly with the full WBL011 dimensions.

Therefore:

`4,575,790 MODELLED ENERGY-BIN DWELLINGS != 4,580,538 CENSUS STOCK != 4,008,541 OCCUPIED WBL011 STOCK`

No count is promoted to `OBS` or `DER` building-type assignment by aggregation alone.

## 3. P8 direct-authority gate was too permissive after P15

The P8 gate allowed `SETTLEMENT_TYPE` and `COUNTY_X_SETTLEMENT_TYPE` as possible direct-authority grains when a WBL-compatible key was asserted.

After P15 this is not sufficient for a populated current-stock archetype. A building-type distribution at county × settlement-type grain has multiple building-type rows for the same WBL geography key. Joining that margin to construction period × wall × floor area × comfort × heating mode × fuel requires an allocation rule.

That allocation is a statistical linkage, not a direct observation.

P16 therefore restricts direct `OBS`/`DER` building-type authority to:

1. `WBL_FULL_JOINT` — building type is published jointly with the WBL stock dimensions at the occupied-stock grain; or
2. `DWELLING_RECORD` — a reproducible record-level key permits deterministic linkage to the WBL dimensions.

A coarse marginal can still be used as a calibration/control source, but only through the separately admitted P12 calibrated-linkage path.

## 4. Current KSH candidate gate result

The KSH 2025 methodology candidate remains `Q` for direct P9 building-type linkage because:

- the published universe is the full census dwelling stock, not an exposed `DW_OC` occupied-stock building-type table;
- no complete occupied-stock building-type distribution is published;
- no public reproducible WBL-compatible record join key is exposed.

The methodological fact that KSH internally has occupancy and building-type information does not authorize the repository to reconstruct or infer the missing joint.

## 5. Direct closure path

The clean non-model closure path is now sharply defined: obtain an official KSH aggregate or approved extract in which building type is bound to the occupied WBL stock.

Preferred aggregate grain:

- reference year: `2022`;
- universe/filter: `LAKAS_OCS = DW_OC`;
- geography: `TERUL_GEO3` county/Budapest;
- settlement type: `TERUL_TELTIP2`;
- construction period: `EPEV_POC1`;
- wall material: `FALA_V`;
- floor area: `LAT_V`;
- comfort: `KOMF`;
- heating mode: `FUTES_TOH`;
- heating fuel: `FUTAGOK`;
- building type: taxonomy reproducibly mapped to `FAMILY_HOUSE` / `MULTI_DWELLING`;
- measure: dwelling count.

A record-level extract is also admissible only if privacy/reuse controls are satisfied and a reproducible non-PII linkage key is supplied. P16 does not request, receive or authorize transmission of microdata.

No external request is sent by this slice.

## 6. P9 effect

`NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY` remains open, but its cause is now more precise:

`CURRENT KSH CLASSIFICATION EXISTS / PUBLIC OCCUPIED-WBL DIRECT LINK MISSING`

The P12 calibrated-linkage route remains available if Joseph separately approves a model and all P12 representativeness, validation and uncertainty gates are satisfied.

The current-stock blockers therefore remain:

- `NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`;
- `NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY`.

Technical-readiness additionally remains blocked by:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

## State

- `Q-B02-001`: OPEN;
- `Q-B02-002`: OPEN;
- `Q-B02-004`: OPEN;
- current-stock archetype: `Q`;
- technical-readiness archetype: `Q`;
- national technical/final eligible count: blank / `Q`;
- B02 readiness: **55%**;
- **no readiness uplift**;
- OÉNY request remains unsent.
