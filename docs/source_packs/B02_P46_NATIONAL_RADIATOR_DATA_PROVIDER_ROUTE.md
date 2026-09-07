# B02-P46 — national radiator stock data-provider route

**State:** `CURRENT HUNGARY-SPECIFIC DATA PACKAGE FOUND / NUMERIC PARK CELLS NOT YET ACQUIRED / P42 REMAINS Q`

**Canonical base:** `80e74a473ac7f2a79662cf92cbc795fa56bc8d44`

**Research date:** 2026-09-07

## 1. Purpose

P45 proved several exact household/reference radiator anchors but intentionally did not treat public listings as a statistical sample.

P46 attacks the next programme-level question directly:

> Is there a concrete national Hungary-specific data package or provider whose published scope explicitly contains a residential radiator-stock surface, rather than merely another individual building example?

The answer is **yes**.

The strongest current route identified is BRG Building Solutions' `Hungary Heating and Cooling 2026` (`HUHC2026`).

P46 proves the existence, country scope, current publication, radiator-park scope and direct acquisition route. It does **not** fabricate or reverse-engineer paywalled numeric cells.

Hard boundary:

`DATA-PACKAGE SCOPE MATCH != ACQUIRED NUMERIC EVIDENCE != P42 NATIONAL AUTHORITY`

No external source binary is committed to the public repository.

## 2. Primary blocker-killer route — BRG Hungary Heating and Cooling 2026

Provider:

- BRG Building Solutions;
- report: `Hungary Heating and Cooling 2026`;
- reference: `HUHC2026`;
- publication date: `2026-06-30`;
- length: `212 pages`;
- authority page: `https://www.brgbuildingsolutions.com/Reports-Details?ProductID=a283546d-c5b7-4f07-9e28-16f77aaeaa73`.

The provider describes the report as compiled from its proprietary research methodology, combining primary research, secondary research and internal expert analysis in its Enterprise database.

### 2.1 Exact stock-surface locator

The public report catalogue contains a dedicated national background section:

`Residential Heating and Cooling Park`

with:

- `A.8.1 Residential Space Heating Park`;
- **`A.8.2 Residential Radiators Park`**;
- `A.8.3 Residential Water Heating Park`;
- `A.8.4 Residential Air Conditioners Park`.

This is materially different from the P44/P45 public examples. The catalogue explicitly names a Hungarian **residential radiator park** surface.

### 2.2 Exact radiator-market locator

The same report has a dedicated `HU - Radiators - Report` section containing, among other items:

- `3.1.1 Market Sector Overview : Hydronic Radiators`;
- `3.1.2 Market Outlook : Hydronic Radiators`;
- `3.2.1 Historical Trends and Forecasts : Hydronic Rads`;
- `3.3.1 Prices and Market Values : Hydronic Radiators`;
- `3.3.2 Prices and Market Values by Type of Product`;
- `3.4.1 End Use : Base Year`;
- `3.4.2 End Use : Historical and Forecasts`;
- `3.4.3 Sales by Type : Towel Warmer`;
- market-share tables for towel warmers, steel panel, decorative steel tubular and aluminium radiators;
- import/export tables for cast-iron and steel radiators;
- thermostatic-radiator-valve trade tables;
- radiator distribution-flow tables.

The public catalogue also provides a direct purchase path for the full report and for report sections. P46 does not submit the provider's sample-request or enquiry form and performs no purchase.

### 2.3 What this route definitely proves

The public catalogue is sufficient to prove that a current, Hungary-specific commercial data package exists with:

1. an explicitly named **Residential Radiators Park** surface;
2. explicit hydronic-radiator scope;
3. end-use segmentation;
4. product/type segmentation;
5. historical/forecast market-volume surfaces;
6. a reproducible direct acquisition route.

Therefore the previous practical state:

`NO IDENTIFIED NATIONAL RADIATOR-STOCK DATA PACKAGE`

is no longer defensible.

Canonical P46 result:

`NATIONAL RADIATOR DATA-PACKAGE ROUTE = QUALIFIED_PROVIDER_ROUTE`

## 3. What the public catalogue does not yet prove

The public catalogue does not expose the underlying `A.8.2 Residential Radiators Park` numeric cells.

Therefore P46 does **not** yet assert any of the following values:

- number of Hungarian radiator-heated dwellings;
- installed Hungarian radiator-unit count;
- installed-stock type/configuration/size shares;
- stock-level heat-pump reuse fraction;
- programme replacement-unit quantity.

In particular:

`REPORT TITLE/TOC != NUMERIC CELL`

`MARKET SHARE != INSTALLED PARK COMPOSITION`

`ANNUAL SALES != INSTALLED STOCK`

`ANNUAL IMPORT/EXPORT != INSTALLED STOCK`

`REPLACEMENT-MARKET SALES != HEAT-PUMP PROGRAMME REPLACEMENT REQUIREMENT`

The five canonical P42 rows therefore remain `Q` until numeric evidence is acquired and claim-specifically admitted.

## 4. Independent public calibration route — NÉER2

A second, independent line is retained for calibration rather than used as a substitute for BRG's current stock package.

Public supporting source:

`https://e-gepesz.hu/tipizalt-lakoepulet-energiaigenyenek-modellezese-dinamikus-epuletszimulacioval/`

The publication states that:

- the 2015 NÉER2 typology was based on a survey of **2000 buildings**;
- it contains building-services solutions of the surveyed buildings;
- for the examined NÉER2 type 7 archetype, heating is explicitly modelled with **radiators**.

This is useful because it establishes a national building-stock calibration lineage with actual building-services content.

It does **not** publish a complete current national radiator-unit inventory or type-size distribution in the inspected public surface.

Therefore:

`NÉER2 2000-BUILDING TYPOLOGY != CURRENT NATIONAL RADIATOR UNIT INVENTORY`

and:

`ONE NÉER2 RADIATOR ARCHETYPE != ALL NÉER2 TYPES ARE RADIATOR-HEATED`

## 5. Independent market-flow diagnostic — IndexBox

A current commercial Hungary report also exists for non-electric central-heating radiators:

`https://www.indexbox.io/store/hungary-radiators-for-central-heating-not-electrically-heated-market-analysis-forecast-size-trends-and-insights/`

Its public description explicitly covers national demand, supply and trade flows.

This is retained only as an independent flow diagnostic for later plausibility checks.

P46 deliberately forbids converting annual consumption, production, imports or exports into installed stock without a separately admitted stock-survival/retirement model.

Hard boundary:

`MARKET FLOW != INSTALLED PARK`

## 6. Executable P46 gate

`modules/B02/radiator_data_provider_route.py::assess_radiator_data_provider_route()`

qualifies a provider route only if all of the following are explicit:

- route identity;
- provider identity;
- report reference;
- Hungary country binding;
- publication date;
- authority URL;
- exact locator;
- current report state;
- national scope;
- explicit residential radiator-park surface;
- explicit hydronic-radiator scope;
- direct acquisition route;
- reproducible repository binding.

The route may be `QUALIFIED_PROVIDER_ROUTE` while all five P42 programme claims remain unresolved.

P42 authority cannot be minted from catalogue metadata. It requires the underlying numeric stock evidence plus the separate engineering classifications required by P42.

## 7. P42 impact

P46 changes the evidence-acquisition state, not the national radiator quantities.

The following canonical P42 claims remain `Q`:

- `RADIATOR_STOCK_DWELLING_COUNT`;
- `RADIATOR_STOCK_UNIT_COUNT`;
- `RADIATOR_TYPE_SIZE_DISTRIBUTION`;
- `RADIATOR_REUSE_UPGRADE_REQUIREMENT`;
- `RADIATOR_REPLACEMENT_QUANTITY`.

The first three now have a concrete current national commercial acquisition route. The last two still require P42's physical engineering logic after stock characterization.

No P42 programme use is enabled by P46 alone.

## 8. Practical next action

The smallest direct acquisition target is the `HUHC2026` content that contains:

1. `A.8.2 Residential Radiators Park` — for current installed-stock characterization;
2. `HU - Radiators - Report` — for hydronic radiator volumes, end use and product/type segmentation.

The full `HUHC2026` package contains both according to the public catalogue and therefore avoids trying to infer one surface from the other.

Once the underlying tables are legitimately available, admission must inspect the exact field definitions, units, reference year, population/stock basis, uncertainty/methodology and licensing boundary before any numeric value can enter P42.

No sample request, enquiry, email or purchase is performed in P46.
