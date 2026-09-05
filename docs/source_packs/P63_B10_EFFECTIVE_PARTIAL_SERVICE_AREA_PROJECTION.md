# B10-P63 — Effective partial service-area projection

## Purpose

P63 stops treating national spatial usability as all-or-nothing.

The repository already contains thousands of claim-specific whole-settlement DSO memberships, one exact P61 usage-location membership, and the P62 exact supersession layer. P63 turns those artifacts into one executable **resolved-only effective projection** that downstream B10 code can consume without waiting for every unresolved special/partial settlement grain to be solved.

This is a modelling-enablement slice, not a completeness claim.

## Batch-authority acquisition result

Before building the projection, P63 tested whether the remaining partial-settlement problem could be solved efficiently from one batch authority rather than by further one-off locality hunting.

The Hungarian E-KÖZMŰ system is the correct class of source: its public documentation states that utility operators provide network map data, including network route/location metadata and operator/service-licensee identity, and that the map supports settlement, address and cadastral-number lookup. Operator map data are supplied through WMS/WFS services.

However, the residential map application requires authenticated government-account access. No authenticated E-KÖZMŰ export is available to this repository workflow, so P63 imports **zero** boundary, address, parcel, line or operator-network rows from E-KÖZMŰ.

Therefore:

`BATCH AUTHORITY IDENTIFIED != BATCH AUTHORITY MATERIALIZED`

and:

`AUTHENTICATED MAP ACCESS != REPRODUCIBLE PUBLIC REPOSITORY EVIDENCE`

No further one-settlement-at-a-time acquisition loop is opened by P63.

## Executable effective projection

`modules/B10/effective_service_area_projection.py` reconstructs the current admissible surface from the existing repository evidence:

1. full-schema whole-settlement materialization surfaces from P20-P46;
2. compact P47/P48/P49 completion pair surfaces plus their manifests;
3. identity-specific P47/P48/P49 exception source lineages;
4. exact P62 supersessions;
5. the single P61 `Tass üdülőterület` usage-location membership.

Every raw whole claim is replayed through the P62 effective-admission contract. A superseded exact `(settlement_name, operator_id)` pair is not emitted.

## Exact resolved-only surface

Effective whole-settlement rows:

- ELMŰ: 127
- E.ON DDÁSZ: 819
- E.ON ÉDÁSZ: 814
- MVM Démász: 256
- MVM Émász: 650
- OPUS TITÁSZ: 386

Total effective whole-settlement rows: **3052**.

Exact proven usage-location rows: **1**.

Total P63 resolved-only effective records: **3053**.

The usage-location record is:

`ELMU:TASS:UDULOTERULET -> ELMU:SERVICE_AREA`

It remains a partial-settlement record and never becomes a whole-Tass claim.

## Source-lineage preservation

The compact P47-P49 completion surfaces do not carry per-row source columns. P63 therefore reconstructs ordinary rows from the corresponding manifest and overrides source lineage only for the exact identity-specific exception rows already frozen by P47-P49.

Examples:

- Miskolc / Mátraterenye and the two missing-delimiter Émász pairs preserve their P47 KSH-2019 direct/split lineage;
- Gödre and Zalakomár preserve P48 KSH-2019 direct lineage;
- Jánossomorja preserves P49 KSH-2019 direct lineage;
- parser-only extraction corrections retain their exact current-M1 + current-KSH lineage.

No fuzzy, accent, edit-distance, suffix, parent, complement or cross-operator inference is introduced.

## Frozen boundaries

`RESOLVED-ONLY EFFECTIVE PROJECTION != COMPLETE NATIONAL KSH-TO-DSO CROSSWALK`

`RAW WHOLE CLAIM != EFFECTIVE CURRENT WHOLE-SETTLEMENT ADMISSION`

`SUPERSEDED WHOLE CLAIM != COUNTERPART PARTIAL MEMBERSHIP`

`PARTIAL SETTLEMENT != WHOLE-SETTLEMENT MEMBERSHIP`

`USAGE-LOCATION MEMBERSHIP != COMPLEMENT BOUNDARY`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`E-KÖZMŰ NETWORK MAP != REPOSITORY-MATERIALIZED AUTHORITY WITHOUT AUTHENTICATED EXPORT`

## Closure effect

P63 creates a machine-usable resolved spatial surface for downstream work. It does **not** clear:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`;
- `REGIONAL_READINESS_HEADER_ONLY`;
- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`;
- `NO_REAL_PROGRAMME_NODE_PANEL`.

The canonical complete crosswalk remains header-only. B10 remains `IN_PROGRESS` at **15% readiness**.
