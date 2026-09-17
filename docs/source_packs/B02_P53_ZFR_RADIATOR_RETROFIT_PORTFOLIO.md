# B02-P53 — ZFR implemented radiator-retrofit portfolio anchor

**State:** `OFFICIAL BEFORE/AFTER SCHEMA PROVEN / IMPLEMENTED 3621-DWELLING RETROFIT PORTFOLIO QUANTIFIED / FILLED PAIR TABLE NOT RECOVERED / NATIONAL P42 STILL Q`

**Canonical base:** `5cdb166655a52efcc40b09d13a7eafa80590be20`

**Implementation date:** 2026-09-17

## 1. Purpose

P53 advances the original programme chain without manufacturing a national stock weight:

`CURRENT EMITTER -> RETROFIT DECISION -> KEEP / REPLACE -> REPLACEMENT QUANTITY -> OUTPUT / PRODUCT / CAPEX`

P52 recovered a filled eight-dwelling new-build radiator schedule but could not speak to pre-retrofit stock. P53 moves into an actually implemented residential retrofit portfolio under ZFR-TÁV/2019 and ZFR-ÉMI-TÁV/2020.

The strongest available public evidence is split across two levels:

1. the official ZFR-TÁV/2019 rules prove that radiator-change projects had to create an original-versus-new per-radiator technical matrix;
2. LEHEL/Aluradiátor/Energyszol implementation sources publish aggregate realised quantities for a 3621-dwelling ZFR portfolio.

The filled beneficiary-level original-to-new matrix itself has **not** been recovered publicly. P53 freezes that distinction.

## 2. Official ZFR before/after documentation schema

Primary source:

`https://tav2019.nffku.hu/data/webfiles/ZFR-TAV-2019_PU_190617.pdf`

The ZFR-TÁV/2019 technical-documentation requirements state that planned radiator replacements must be documented with an aggregate table identifying the location/function and the **current and replacement radiator type, size, material and nominal heat output**. The technical description additionally requires, for radiator replacement, an **every-radiator original/new size table together with the change in heat output and water-temperature values**.

Therefore the programme-level evidence schema is proven:

`ORIGINAL RADIATOR -> NEW RADIATOR`

with at least:

`LOCATION + TYPE + SIZE + MATERIAL + NOMINAL OUTPUT + WATER-TEMPERATURE CHANGE`.

This is exactly the technical grain needed for later KEEP/UPSIZE/CHANGE calibration.

However:

`MANDATORY DOCUMENTATION SCHEMA != RECOVERED FILLED BENEFICIARY TABLE`.

P53 therefore records `official_before_after_matrix_schema=True` while keeping `exact_before_after_pair_recovered=False`.

## 3. Implemented LEHEL/Aluradiátor ZFR portfolio

Primary implementation source:

`https://alurad.hu/_user/page/webshop/12/documents/lehel_muszaki_katalogus_2023.pdf`

The LEHEL technical catalogue reports the achieved results of the ZFR-TÁV/2019 and ZFR-ÉMI-TÁV/2020 programmes as:

- **3621 dwellings** receiving comprehensive mechanical renovation;
- **nearly 6000 new LEHEL Viking radiators** installed;
- **12,500 cost-allocation devices** installed;
- **HUF 1.9 billion** investment;
- catalogue version: **36 district-heated apartment buildings**.

P53 materializes the first three physical programme quantities. The new-radiator count retains `APPROXIMATE` precision because the source itself says "nearly 6000".

The catalogue also states that every dwelling was surveyed before implementation.

## 4. Independent implementation-page cross-check

Current Energyszol implementation page:

`https://energyszol.hu/tarsashazaknak-lakasszovetkezeteknek/`

The page reports the same ZFR-TÁV/2019 and ZFR-ÉMI-TÁV/2020 implementation portfolio as **3621 dwellings**, and describes the winning-project workflow as an itemized preliminary survey of **every dwelling** before installation. It also states that radiator replacement was optional rather than universal.

This independently supports:

- the stable `3621 dwelling` portfolio denominator;
- dwelling-level survey activity;
- interpreting the new-radiator quantity as a replacement subset rather than a universal one-radiator-per-position intervention.

But the current page reports **38 buildings**, whereas the LEHEL 2023 catalogue reports **36 buildings**.

P53 does not choose between them.

Canonical rule:

`36 BUILDINGS vs 38 BUILDINGS -> SOURCE-VERSION CONFLICT -> BUILDING DENOMINATOR BLOCKED`.

The summary therefore returns:

- `reported_building_counts=(36, 38)`;
- `building_count_conflict=True`;
- `building_count=None`.

## 5. Bounded derived indicators

Within this contractor implementation portfolio only, P53 computes three transparent ratios from the published counts.

### 5.1 New radiators per dwelling

Using the source-native approximate radiator magnitude:

`~6000 / 3621 = ~1.657 new radiators per dwelling`.

This is a **bounded implemented-portfolio intensity**, not a national stock parameter.

### 5.2 Cost-allocation devices per dwelling

`12500 / 3621 = ~3.452 devices per dwelling`.

This stays a device-based quantity. P53 does not silently rename it as an exact installed-radiator census.

### 5.3 Replacement-intensity proxy

`~6000 / 12500 = ~0.48`.

This can be useful as a **device-based replacement-intensity proxy** because the same implementation portfolio reports both quantities and radiator replacement was optional.

It is deliberately **not** an exact replacement fraction because:

- the numerator is approximate;
- a cost-allocation device count is not itself an audited pre-retrofit physical radiator census;
- portfolio coverage and device installation semantics can differ from a strict one-before/one-after emitter pairing;
- the contractor portfolio is selected and not nationally representative;
- no filled same-radiator before/after matrix has been recovered.

Therefore:

`~6000 NEW / 12500 COST ALLOCATORS != EXACT SAME-RADIATOR REPLACEMENT FRACTION`.

## 6. Hard boundaries

P53 freezes all of the following:

`CONTRACTOR ZFR PORTFOLIO != NATIONAL RESIDENTIAL STOCK`

`COST-ALLOCATOR COUNT != PRE-RETROFIT INSTALLED-RADIATOR CENSUS`

`~6000 NEW / 12500 COST ALLOCATORS != EXACT SAME-RADIATOR REPLACEMENT FRACTION`

`IMPLEMENTED RETROFIT QUANTITY != ORIGINAL->NEW TYPE/SIZE PAIR TABLE`

`MANDATORY DOCUMENTATION SCHEMA != RECOVERED FILLED BENEFICIARY TABLE`

`36 vs 38 BUILDING COUNT CONFLICT -> BUILDING DENOMINATOR BLOCKED`

`BOUNDED IMPLEMENTED-PORTFOLIO RATIO != NATIONAL P42 WEIGHT`

All five P42 national radiator claims remain `Q / programme_use_allowed=NO`.

## 7. Executable contract

`modules/B02/zfr_radiator_retrofit_portfolio.py` provides:

- `ZfrRetrofitEvidence`;
- `ZfrRetrofitPortfolioSummary`;
- `validate_zfr_retrofit_evidence()`;
- `summarize_zfr_retrofit_portfolio()`;
- `portfolio_grants_exact_before_after_pair_authority()`;
- `portfolio_grants_national_p42_authority()`.

The contract:

1. requires residential scope;
2. separates official schema evidence from implemented quantities;
3. requires the `~6000` new-radiator quantity to retain approximate precision;
4. preserves the `36 vs 38` building-count conflict instead of resolving it by preference;
5. rejects national P42 promotion;
6. rejects exact before/after-pair authority;
7. rejects self-authorized programme use.

## 8. Effect on the programme

P53 is material evidence progress because it moves from design schedules and isolated precedents to a **large, actually implemented residential retrofit cohort**:

- 3621 dwellings;
- ~6000 new radiators;
- 12,500 cost-allocation devices;
- every-dwelling preliminary survey reported;
- official programme rules requiring per-radiator original/new technical mapping.

This gives the programme a bounded empirical replacement-intensity anchor while remaining fail-closed on the unresolved national stock problem.

The next highest-value target remains the public recovery of one or more **filled beneficiary technical tables** satisfying the official ZFR schema, so that exact source-native rows can be materialized as:

`ORIGINAL TYPE/SIZE/OUTPUT -> NEW TYPE/SIZE/OUTPUT`.

Until that is recovered, `exact_before_after_pair_recovered=False` and all national P42 claims remain `Q`.

No external source binary is committed. No product price or CAPEX value is created in P53.
