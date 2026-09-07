# B02-P43 — radiator data recovery routes

**State:** `THREE QUALIFIED RECOVERY ROUTES / P42 QUANTITIES REMAIN Q`

**Canonical base:** `2ca0cff12ee693a63278a42946fce8ec5592c56c`

**Implementation date:** 2026-09-06

## 1. Purpose

P42 makes the programme objective explicit:

`HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06`

P43 does not weaken that objective. It identifies concrete data assets/data holders that can recover the missing radiator stock and replacement-design inputs.

Hard boundary:

`RECOVERY ROUTE != RECOVERED DATA != P42 QUANTITY AUTHORITY`

No P42 radiator quantity is promoted by this slice.

## 2. Route A — NÉER2 raw representative building survey

### Public proof

Source ID:

`SRC-B02-NEER2-CSOKNYAI-DISSERTATION-2022`

Authority:

Tamás Csoknyai, DSc dissertation, MTA REAL-D:

`https://real-d.mtak.hu/1472/7/dc_2011_22_doktori_mu.pdf`

Exact locators:

- PDF page 127/167, Annex 1, Table 14.1 introduction;
- PDF page 128/167, Table 14.2 `Főbb gépészeti berendezések adatai`.

The dissertation explicitly says the published list of survey fields was **significantly simplified for overview purposes**, and that the same simplification was applied to the building-services systems.

The published extract still proves structured mechanical data collection including, among other fields:

- heating-system modernization year;
- central heat-producer type, count, installation year, nominal capacity, manufacturer and condition;
- individual heat-producer type, count, installation year and condition;
- longest main-pipe length;
- number of risers;
- insulation information;
- metering/settlement state.

Therefore:

`PUBLISHED EXTRACT DOES NOT SHOW RADIATOR FIELD != RAW DATABASE HAS NO RADIATOR FIELD`

The underlying NÉER2 survey is a qualified recovery route for the missing source-native schema/code lists and radiator/emitter fields, if those fields were in fact collected.

### Exact requested recovery

Request only the minimum existing source-native fields/documentation needed to answer:

- was current heat-emitter type recorded?
- was radiator presence recorded?
- was radiator/fűtőtest unit count recorded?
- were material/type/configuration recorded?
- were dimensions, section count or nominal output recorded?
- what are the exact code lists and missing/unknown semantics?
- what survey weight, typology class and stock scope belong to each record or aggregate?

Preferred disclosure-safe output:

1. source-native data dictionary/code list first;
2. if permitted, anonymised record-level extract containing only non-identifying technical fields;
3. otherwise an aggregate by NÉER2 archetype with count/weight and explicit missingness.

No address, owner, certificate identifier or other personal/direct identifier is requested.

### Boundary

The NÉER2 field campaign represents the **2015 stock state**. Even if radiator inventory is recovered, it is not automatically current-2026 stock authority.

`2015 OBSERVATION != 2026 OBSERVATION`

A current-stock use would need explicit update/calibration and uncertainty under the existing P12/P40-style governance.

## 3. Route B — BME EPBD'18 / NMTK detailed heating layouts

### Public proof

Source ID:

`SRC-B02-BME-HVAC-LCA-2025`

Publication:

L. Zs. Gergely, E. Barna, M. Horváth, Z. Szalay,
`Assessing embodied and operational carbon of residential HVAC systems: Baselines for life-cycle sustainability`, Building and Environment 269 (2025), 112442.

Authority URL:

`https://www.sciencedirect.com/science/article/pii/S0360132324012836`

Exact public facts:

- 20 single-family houses from the Hungarian National House Catalogue were assessed;
- radiator-based HVAC layouts were modelled in all relevant radiator concepts;
- detailed heating system construction/layout plans were available for each building;
- the material inventory was derived from those layout plans;
- radiator material was quantified per building;
- the article's Data availability statement is: `Data will be made available on request.`

The paper cites the layout-plan lineage to the BME/ITM 2019-2020 EPBD'18 implementation work.

Current BME project authority:

`https://epget.bme.hu/wp/ipar-palyazat/`

Exact section:

`EPBD'18 implementáció` — the Innovációs és Technológiai Minisztérium commissioned the BME department to prepare implementation background materials, including tasks related to the National House Catalogue.

The same page identifies the current 2022-2026 residential building-stock model project and Dr. Tamás Csoknyai as project leader/contact.

### Exact requested recovery

For the 20 NMTK houses, request the existing non-personal technical dataset/layout-derived table containing where available:

- house/reference-plan ID;
- room ID/type;
- design heat loss;
- radiator count per room/house;
- radiator type/configuration;
- dimensions or nominal output;
- design/rating flow-return-room temperatures;
- target system temperature;
- pipe/manifold inventory;
- any already-derived replacement-system quantity fields.

### Boundary

These are modern reference/design houses, not observations of the existing Hungarian radiator stock.

`20 NMTK DESIGNS != EXISTING NATIONAL RADIATOR INVENTORY`

Their programme value is the **replacement-design/B06 handoff**: once B02 identifies a retrofit heat-loss/output requirement, this dataset can provide real engineering reference quantities and layouts rather than guessed unit counts.

## 4. Route C — current heat-cost-allocator radiator inventories

### Legal data-model proof

Source ID:

`SRC-B02-TSZT-VHR-COST-ALLOCATOR-2026`

Current consolidated authority:

`https://njt.jog.gov.hu/jogszabaly/2005-157-20-22.21`

Exact locators:

- 157/2005. (VIII. 15.) Korm. rendelet 17/A § 8: definition of `hőleadó készülék`;
- 17/C § (1) a): where allocator-based cost sharing is used, the heat output of **all heat emitters** in the covered building parts must be determined by the common allocator system or separately metered;
- 17/C § (2): explicit treatment where an allocator cannot technically be fitted to every emitter;
- 5. melléklet 1.: an electronic heat-cost allocator can contain, or evaluation can apply by multiplier, the technical data of the particular heat emitter.

This proves that current operational allocator datasets are structurally tied to individual heat emitters and their technical evaluation.

### Provider-level proof

Techem Hungary current contact/operation:

`https://www.techem.com/hu/hu/informaciok/kapcsolat`

Current contact:

`techem@techem.hu`

Example Hungarian Techem heating-cost statement:

`https://www.techem.com/content/dam/techem-hu/documents/Magyar%C3%A1zat%20f%C5%B1t%C3%A9si%20k%C3%B6lts%C3%A9g%20elsz%C3%A1mol%C3%A1shoz.pdf.coredownload.pdf`

The example exposes radiator-specific fields including `Rad.sz.`, `Faktor` and a dimension field (`mm-ben`) for the resident's allocator rows.

### Exact requested recovery

Ask for **aggregate/anonymised research output only**, not customer records:

- number of covered residential buildings and dwellings;
- number of individual radiator/heat-emitter records;
- radiator type/model family where held;
- material/configuration where held;
- dimensions/section count where held;
- nominal output or technical evaluation factor where held;
- broad heating-system class;
- coarse geographic category;
- reference date/year;
- code lists and missingness semantics.

Preferred first output: national/regional aggregate frequency table and data dictionary. No address, name, account number, device serial number or customer identifier is requested.

### Boundary

This route covers only buildings/systems represented in cost-allocator operations.

`COST-ALLOCATOR RADIATOR INVENTORY != ALL HUNGARIAN RADIATORS`

It is nevertheless a strong **current unit-level calibration/validation source** for the district-/central-heating radiator segment and can directly inform radiator-units-per-dwelling and type/size distributions within that covered domain.

## 5. Current route matrix

| Route | Existing/current stock | Unit count potential | Type/size potential | Replacement-design potential | Current status |
|---|---:|---:|---:|---:|---|
| NÉER2 raw survey | historical 2015 representative stock | unknown until recovery | unknown until recovery | partial | `QUALIFIED_ROUTE` |
| BME NMTK HVAC layouts | no | yes for 20 designs | yes for 20 designs | strong | `QUALIFIED_ROUTE` |
| cost-allocator inventories | current covered segment | strong | strong where technical fields retained | indirect | `QUALIFIED_ROUTE` |

These statuses mean only that the recovery path is concrete and source-bound.

## 6. P42 remains unchanged

The following remain `Q` until actual recovered data are validated and admitted:

- `RADIATOR_STOCK_DWELLING_COUNT`;
- `RADIATOR_STOCK_UNIT_COUNT`;
- `RADIATOR_TYPE_SIZE_DISTRIBUTION`;
- `RADIATOR_REUSE_UPGRADE_REQUIREMENT`;
- `RADIATOR_REPLACEMENT_QUANTITY`.

Hard boundaries:

`QUALIFIED_ROUTE != QUALIFIED_STOCK`

`DATA AVAILABLE ON REQUEST != DATA RECEIVED`

`RADIATOR MASS != RADIATOR UNIT COUNT`

`COST ALLOCATOR != RADIATOR UNLESS THE PROVIDER DATA MODEL BINDS IT`

`HISTORICAL STOCK != CURRENT STOCK`

`DESIGN REFERENCE != OBSERVED STOCK`

## 7. Request governance

P43 prepares two human-gated request packages:

- `docs/data_requests/P43_BME_RADIATOR_DATA_REQUEST.md`;
- `docs/data_requests/P43_TECHEM_RADIATOR_AGGREGATE_REQUEST.md`.

Both remain:

`READY_FOR_HUMAN_REVIEW / NOT SENT`

External dispatch requires separate explicit Joseph authorization.

No external source binary or returned restricted dataset may be committed to the public repository.
