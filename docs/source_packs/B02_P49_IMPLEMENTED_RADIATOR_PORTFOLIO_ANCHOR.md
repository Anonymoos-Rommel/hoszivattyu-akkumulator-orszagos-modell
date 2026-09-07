# B02-P49 — IMPLEMENTED RADIATOR PORTFOLIO + CURRENT DWELLING QUANTITY CALIBRATION

## Purpose

P49 adds two source-bounded Hungarian quantity observations needed for the radiator-stock programme chain:

`CURRENT / IMPLEMENTED COHORT -> EMITTER QUANTITY -> TYPE BOUNDARY -> LATER KEEP / UPSIZE / CHANGE`

It does **not** turn either observation into national P42 authority.

## 1. Large implemented ZFR portfolio

Primary source:

- Lehel Radiátorgyár, *Az Otthon Melege — Cégbemutató és műszaki katalógus*
- URL: `https://lehelradiator.hu/_user/file/lehel_muszaki_katalogus_2023.pdf`
- exact locator: PDF page 4/20, section headed `A ZFR-TÁV/2019 és ZFR-ÉMI-TÁV/2020 programokban elért eredményeink`

The manufacturer reports for the completed ZFR-TÁV/2019 and ZFR-ÉMI-TÁV/2020 portfolio:

- 3,621 dwellings receiving full mechanical refurbishment;
- `közel 6000` new Lehel Viking radiators installed;
- 12,500 cost-allocation devices installed;
- HUF 1.9 billion investment value.

The same catalogue states that the winning-project workflow includes every dwelling being surveyed, mechanical works being performed, technical handover and final accounting. It also states that MOM-LEHEL was formed to read and evaluate the cost allocators installed by Aluradiátor Projekt Kft. in the ZFR programmes.

Per-emitter semantic support is independently explicit on the current MOM-LEHEL technical service page:

- URL: `https://mom-lehel.hu/koltsegmegosztas`
- exact locator: `Technikai háttér -> Egyedi méréstechnika – hőmennyiségmérők és költségosztók`
- source statement: the heat meter measures an apartment, while the cost allocator is installed on the **individual radiators** (`az egyes radiátorokra szerelve`).

This preserves the distinction:

`APARTMENT HEAT METER != PER-RADIATOR COST ALLOCATOR`

### Canonical quantity treatment

`12,500` is source-native and exact. The ZFR portfolio source proves installation of 12,500 cost allocators and the MOM-LEHEL technical source proves that this device class is installed on individual radiators. P49 therefore admits **12,500 exact bounded radiator/emitter positions for this implemented portfolio**.

This does not prove that every device position belongs to a residential dwelling rather than a common or other premises, so it is not converted to a residential per-dwelling ratio.

`közel 6000` is not exact. P49 stores `6000` only as the source's approximate reference magnitude and sets:

`replacement_count_status = APPROXIMATE_REFERENCE_ONLY`

Therefore:

`NEARLY 6000 != EXACT 6000`

and P49 exposes no exact replacement-radiator count from this source.

The source names the installed radiator family as **Lehel Viking**. That is a bounded implemented type anchor. The same catalogue publishes the available Viking height/length family, but it does not publish the installed size mix of the ZFR portfolio. Therefore:

`PRODUCT CATALOG SIZE OPTIONS != INSTALLED PORTFOLIO SIZE MIX`

and P49 does not promote this evidence to `RADIATOR_TYPE_SIZE_DISTRIBUTION`.

## 2. 2025 manufacturer cross-check and publication drift

Later manufacturer presentation:

- `Radiátorcserétől a digitalizációig`, 2025-04-02 presentation
- URL: `https://letesz.hu/msites/letesz/UserFiles/Sajtofigyeles/Hirlevel%202025/Korlevel/tavaszi%20akademia/eloadok%20anyagai/L%C3%89T%C3%89SZ_LEHEL_Sales_20250402.pdf`

The detailed, explicitly programme-labelled ZFR slide (PDF page 4/10) reports:

- **38** district-heated apartment buildings;
- **3,621** dwellings;
- `közel 6000` new Lehel Viking radiators;
- **12,500** cost allocators installed and read;
- HUF **1.9 billion** investment.

Thus the detailed 2025 ZFR slide independently repeats the primary catalogue's dwelling, radiator-magnitude, cost-allocator and investment quantities, but conflicts on building count: **38 vs 36**.

P49 does not choose one building count by preference. It records:

`building_count_status = Q_SOURCE_VERSION_CONFLICT`

The presentation also contains a preceding high-level results slide (PDF page 3/10) with approximately **4,000 dwellings**, **6,000 radiators**, **13,500 cost allocators** and **2+ billion HUF**. These are not silently substituted for the explicitly programme-labelled detailed ZFR line. The summary may represent a different/cumulative reporting scope or later aggregation; the public deck does not provide enough lineage to equate it with the detailed programme cohort.

Canonical boundary:

`HIGH-LEVEL COMPANY SUMMARY != DETAILED PROGRAMME-SPECIFIC COHORT`

The conflict and summary drift do not erase the repeated detailed 3,621 / 12,500 programme quantities, but neither the building denominator nor the high-level 13,500 figure is used for derived stock intensity.

## 3. Per-dwelling ratio is withheld for the portfolio

The programme-specific publication does not explicitly prove that all 12,500 installed device positions are exclusively inside the 3,621 dwellings, with no common or other premises included. Consequently P49 does not compute `12,500 / 3,621` as a residential radiator-per-dwelling ratio.

Canonical boundary:

`PORTFOLIO DEVICE TOTAL + DWELLING TOTAL != RESIDENTIAL-ONLY PER-DWELLING RATIO WITHOUT NUMERATOR-SCOPE PROOF`

This is deliberately stricter than arithmetic availability.

## 4. Independent current/recent dwelling-level control

Source:

- public Dunakeszi panel-apartment listing
- URL: `https://www.ingatlantajolo.hu/ingatlan/kiado%2Bpanellakas%2Bdunakeszi/8097040`
- exact locator: listing body, meter description

The listing states that the apartment has radiator-by-radiator cost allocators and gives the count explicitly as **4 devices**.

Because the source itself binds the count `radiátoronként (4 db)`, P49 admits for this one dwelling:

- dwelling count = 1;
- radiator positions = 4;
- bounded ratio = 4 radiators/dwelling.

This is a public listing, not an inspected statistical observation. It is useful only as an independent household-level quantity control.

`ONE PUBLIC DWELLING != REPRESENTATIVE PANEL STOCK`

## 5. Relationship to P44 and P48

P44 already contains exact panel/district evidence, including:

- Árpádhídfő: 432 dwellings -> 1,680 in-dwelling radiators;
- Lehel 2021 implemented reference: 2,122 dwellings -> 3,307 replacement radiators + 6,709 cost allocators.

P49 does **not** add the P44 Lehel project quantities to the broad ZFR portfolio total because the publication does not prove disjointness. The 2021 implementation may overlap the broader ZFR programme population.

`P44 LEHEL PROJECT + P49 LEHEL PORTFOLIO != ADDITIVE WITHOUT DISJOINTNESS PROOF`

P48 contains a different current six-building Békásmegyer cohort with 6,024 exact emitter positions, but a contaminated residential denominator. P49 does not rewrite that state.

## 6. P42 status

All five national programme claims remain `Q` and `programme_use_allowed=NO`:

1. `RADIATOR_STOCK_DWELLING_COUNT`
2. `RADIATOR_STOCK_UNIT_COUNT`
3. `RADIATOR_TYPE_SIZE_DISTRIBUTION`
4. `RADIATOR_REUSE_UPGRADE_REQUIREMENT`
5. `RADIATOR_REPLACEMENT_QUANTITY`

P49 contributes calibration evidence only.

## 7. Hard boundaries

`IMPLEMENTED PORTFOLIO != CURRENT NATIONAL STOCK`

`APARTMENT HEAT METER != PER-RADIATOR COST ALLOCATOR`

`EXACT COST-ALLOCATOR COUNT != EXACT REPLACEMENT-RADIATOR COUNT`

`NEARLY 6000 != EXACT 6000`

`BUILDING-COUNT SOURCE CONFLICT != SILENTLY RESOLVED METADATA`

`HIGH-LEVEL COMPANY SUMMARY != DETAILED PROGRAMME-SPECIFIC COHORT`

`PORTFOLIO DEVICE TOTAL != RESIDENTIAL-ONLY PER-DWELLING RATIO`

`ONE CURRENT PUBLIC LISTING != REPRESENTATIVE STOCK`

`PRODUCT FAMILY != INSTALLED SIZE DISTRIBUTION`

`COUNT CONSISTENCY != REPRESENTATIVENESS`

`P44/P48/P49 BOUNDED ANCHORS != P42 NATIONAL AUTHORITY`

No external request, email or purchase is performed in P49. No external source binary is committed to the public repository.
