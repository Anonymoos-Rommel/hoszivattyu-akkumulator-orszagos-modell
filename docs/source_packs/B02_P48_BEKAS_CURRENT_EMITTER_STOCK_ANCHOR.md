# B02-P48 — Békásmegyeri current emitter-stock anchor

**State:** `EXACT 1215-DWELLING / 6024-EMITTER-POSITION BOUNDED STOCK ANCHOR PROVEN / CURRENT TKM AWARD LINK PROVEN / TKM COMPLETION NOT PROVEN / P42 NATIONAL CLAIMS REMAIN Q`

**Canonical base:** `80ec518fbf7d839c282e2374df1c40f7702945f0`

**Research date:** 2026-09-07

## 1. Purpose

P47 proved that TKM/2025 has an administrative per-emitter quantity surface, but did not materialise any real project stock count.

P48 closes that specific evidence gap for one current, large Hungarian district-heated cohort.

The user-facing programme question remains:

`HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06`

P48 contributes a real answer to the **HOW MANY** branch for one bounded cohort. It does not pretend that a single housing cooperative is national stock authority.

Core boundaries:

`EXACT BOUNDED STOCK != NATIONAL STOCK`

`EMITTER POSITION != RADIATOR TYPE/SIZE`

`CURRENT STOCK COUNT != POST-ENVELOPE KEEP/UPSIZE/CHANGE`

`AWARDED TKM PROJECT != COMPLETED REPLACEMENT`

`TKM AWARD AMOUNT != DEVICE COUNT`

## 2. Primary current-stock source

Beneficiary/public operator source:

- Békásmegyeri 3. számú Lakásfenntartó Szövetkezet;
- page: `Fűtési tudnivalók`;
- URL: `https://bekas3.hu/futesi-tudnivalok/`.

The page states that the cooperative's cost-allocation system covers:

- **6 buildings**;
- **1215 dwellings**;
- **4809 radio-readable heating cost allocators**;
- **1215 bathroom radiator places**.

The wording separates the 4809 installed cost allocators from the 1215 bathroom radiator places. P47 already established the legal/technical semantic that a heating cost allocator on this route is a per-heat-emitter device.

Therefore the bounded cohort supports the exact arithmetic:

`4809 COST-ALLOCATOR-BEARING HEAT EMITTERS + 1215 ADDITIONAL BATHROOM RADIATOR PLACES = 6024 EMITTER POSITIONS`

Derived bounded ratios:

- `4809 / 1215 = 3.9580246913580246` cost-allocator-bearing emitters per dwelling;
- `6024 / 1215 = 4.958024691358025` total emitter positions per dwelling.

These ratios are empirical for this exact cooperative cohort, not a national multiplier.

## 3. Cohort identity

The cooperative's public `Szervezet` page identifies the same six-building population and states that it is a community of **1215 dwelling owners**:

- Jós utca 1-15;
- Jós utca 2-16;
- Sarkadi Imre utca 1-8;
- Bálint György utca 6-20;
- Hatvany Lajos utca 12;
- Hatvany Lajos utca 14.

Source:
`https://bekas3.hu/szervezet/`

This gives a stable cohort identity for the stock quantities rather than an anonymous market average.

## 4. Current TKM/2025 execution lineage

The same cooperative published a 2026-08-07 construction notice covering all six buildings and scheduling replacement of heating cost allocators building by building.

Source:
`https://bekas3.hu/2026/08/07/futesi-koltsegosztok-csereje/`

The notice says the work is part of the state-supported 100% TKM project and lists the six-building installation sequence.

A later 2026-09-01 cooperative notice states:

- **all 6 buildings won TKM support**;
- the support recorded in the award document totals **47,098,673 HUF**;
- the construction notice was withdrawn because the contractor suspended further TKM work amid delayed NEÜ payments;
- the cooperative's construction therefore had not been completed.

Source:
`https://bekas3.hu/2026/09/01/fontos-tajekoztatas-futesi-koltsegosztok-cserejenek-halasztasa/`

This creates a current lineage:

`SAME 6-BUILDING COHORT -> EXACT EXISTING EMITTER STOCK -> TKM AWARDED -> REPLACEMENT SCHEDULED -> NOT PROVEN COMPLETED`

P48 deliberately does **not** relabel the 6024 current emitter positions as 6024 realised TKM installations.

## 5. Why 6024 is admissible as a bounded emitter-position count

P47 proved from official TKM/legal sources that the cost-allocator route is per heat emitter. The Békás source separately reports 4809 cost allocators and 1215 bathroom radiator places.

The sum is admissible only because:

1. both quantities belong to the same explicitly identified 1215-dwelling / six-building cohort;
2. the bathroom radiator places are reported separately from the cost-allocator count;
3. the first quantity is semantically tied to heat emitters by the already-canonical P47 per-emitter control.

Hard boundary:

`COST ALLOCATOR COUNT + EXPLICIT ADDITIONAL BATHROOM RADIATOR PLACES = BOUNDED EMITTER POSITIONS`

but:

`6024 EMITTER POSITIONS != 6024 PROVEN RADIATOR PRODUCT UNITS OF KNOWN TYPE/SIZE`

P48 does not know the type, material, panel configuration, height, length or nominal output of those 6024 positions.

## 6. TKM funding cannot be inverted into device count

The same cohort has a public TKM award total of 47,098,673 HUF. That number is useful as current execution lineage but is **not** a device-count estimator.

TKM budgets can contain different supported activities and equipment classes. Therefore P48 freezes:

`TKM AWARD AMOUNT != COST-ALLOCATOR COUNT`

`TKM AWARD AMOUNT != RADIATOR COUNT`

`MAXIMUM UNIT PRICE != ACTUAL PROJECT UNIT PRICE`

`MIXED PROJECT BUDGET != EMITTER QUANTITY`

No inverse calculation from the grant amount is admitted.

## 7. Relationship to TKM public award universe

An official NEÜ/FEAK publication list is publicly accessible at:

`https://nffku.hu/images/tavolrol/TKM2025_Kozzeteteli_lista_20251205.pdf`

It contains 612 supported rows in its 2025-12-05 snapshot. The Békás cooperative's later 2026 award is not found in that dated snapshot, so P48 does **not** fabricate a FEAK project ID by joining a 2026 beneficiary notice to an older publication list.

Boundary:

`OLDER AWARD SNAPSHOT ABSENCE != NO LATER AWARD`

and:

`BENEFICIARY SELF-PUBLISHED CURRENT AWARD != INVENTED FEAK PROJECT ID`

## 8. Executable contract

`modules/B02/current_emitter_stock_anchor.py` exposes `assess_current_emitter_stock_anchor()`.

The gate requires:

- Hungary scope;
- positive building and dwelling counts;
- non-negative cost-allocator and bathroom-radiator-place counts;
- per-emitter cost-allocator semantics;
- explicit non-overlap of bathroom places;
- same-cohort binding;
- exact public stock and TKM execution source URLs;
- reproducible evidence binding.

Only then can it calculate the bounded 6024 emitter positions and the two per-dwelling ratios.

The gate can separately report TKM status as:

- `NO_PROVEN_TKM_EXECUTION`;
- `AWARDED_NOT_COMPLETED`;
- `STARTED_NOT_COMPLETED`;
- `COMPLETED`.

The current Békás row is intentionally `AWARDED_NOT_COMPLETED`.

## 9. P42 impact

P48 materially improves the evidence base but does not authorize any national P42 claim.

All five remain unresolved nationally:

- `RADIATOR_STOCK_DWELLING_COUNT`;
- `RADIATOR_STOCK_UNIT_COUNT`;
- `RADIATOR_TYPE_SIZE_DISTRIBUTION`;
- `RADIATOR_REUSE_UPGRADE_REQUIREMENT`;
- `RADIATOR_REPLACEMENT_QUANTITY`.

What is now proven is narrower and useful:

`CURRENT DISTRICT-HEATED COHORT: 1215 DWELLINGS -> 6024 EMITTER POSITIONS -> 4.9580 POSITIONS/DWELLING`

This can be used as a validation/calibration anchor against P44 panel ratios and against future TKM project materialisations. It must not be broadcast over the national stock without a separately admitted model/weighting method.

## 10. Next evidence target

The next justified attack is now two-pronged:

1. recover additional real TKM/current cost-allocation cohorts with exact dwelling and emitter/device counts so an empirical distribution can be built rather than relying on one cooperative;
2. recover type/size information for those cohorts or another national radiator-stock package, because P48 solves bounded quantity but **not WHAT TYPE**.

No external request, email or purchase is performed in P48.
