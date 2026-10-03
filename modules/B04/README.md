# B04 – Villamosenergia-ár és tarifák

## Cél

Háztartási hőszivattyú- és akkumulátortöltési költség előállítása tarifánként, elosztói területenként és hatályidő szerint.

## Bemeneti szerződés

- A1, A2, H és ténylegesen elérhető dinamikus tarifa energiaára;
- rendszerhasználati díjelemek;
- adók és ársávok;
- elosztói terület, mérőtípus, jogosultság és hatályidő;
- fogyasztás időprofilja és mérőkör-hozzárendelése.

## Kimeneti szerződés

- hőszivattyú teljes villamosenergia-költsége, `HUF/year`;
- akkumulátortöltés teljes költsége, `HUF/year`;
- tarifa- és díjkomponensenkénti bontás;
- H tarifás és normál mérőkör fogyasztásának külön kimutatása.

## Invariánsok

- H tarifás fogyasztás csak a jogosult időszakra és mérőkörre számolható;
- energiaár, rendszerhasználati díj és adó külön tétel;
- az elosztói terület és hatálynap kötelező dimenzió;
- akkumulátoros/VPP töltés, kisütés vagy export nem rendelhető H tarifához elfogadott, topológiára és hatályra vonatkozó jogi-műszaki szabály nélkül;
- a `H_TARIFF_BATTERY_CHARGE_ALLOWED`, `H_TARIFF_BATTERY_DISCHARGE_ALLOWED` és `H_TARIFF_EXPORT_ALLOWED` kapuk egymástól függetlenek és Q esetén fail-closed.

## Állapot

`BLOCKED` – a REGULATED_RESIDENTIAL_ELECTRICITY réteg aktuális MVM snapshotja és az A1/H szabályok lezárva; a H akkumulátor charge/discharge/export/VPP négy független kapuja Q (a boundary contract auditálható), a teljes 2015–2026 HUPX history/forward licencelt adat Q, a MARKET_BASED komponenshíd részleges, a lakossági dinamikus termék Q.

## Kanonikus artefaktumok

- `docs/source_packs/B04_ELECTRICITY_PRICE_AND_TARIFFS.md`
- `registry/electricity_price_sources.csv`
- `registry/electricity_price_variables.csv`
- `registry/electricity_price_formulas.csv`
- `registry/electricity_tariff_rules.csv`
- `registry/electricity_readiness.csv`
- `data/processed/residential_electricity_tariff_schedule.csv`
- `data/processed/h_tariff_schedule.csv`
- `data/processed/electricity_price_component_bridge.csv`

Wholesale history/forward and dynamic residential pricing remain fail-closed Q. B05/B07 may use only the validated regulated tariff inputs and must not infer H battery charging or a wholesale-to-retail bridge.

## V1 canonical tariff consumer

`engine.py` consumes canonical A1, B Alap and H heating-season tariff rows, plus a separately derived outside-season H mapping restricted to profiled low-voltage connections. It returns explicitly labelled constant-2026-tariff SCN costs using supplied discounted allocations and billed-month fractions, not validated historical/future invoices; it does not grant site eligibility or authorize battery/export dispatch. H energy-only and final-price fields remain distinct. The universal outside-season A1-higher fallback stays retired: the derived mapping applies the discounted rate up to an explicit allocation and the excess rate only above it. Exact H settlement, season-crossing fee allocation and actual household-level annual settlement remain open. See [checkpoint 002](../../docs/checkpoints/V1_002_B04_TARIFF_BOUNDARY.md) and [checkpoint 014](../../docs/checkpoints/V1_014_B04_OUTSIDE_H_AND_B.md).

The optional D-tariff source intake and net-energy-only backcast consumer are documented in [checkpoint 003](../../docs/checkpoints/V1_003_B04_DYNAMIC_SOURCE_INTAKE.md). Actual application cannot start before 2027-01-01. The public retrospective series is not an observed historical D bill, a pure wholesale series or a forecast; the core programme does not require this optional extension.

## Civil2025 annual tariff reference

`annual_reference.py` joins complete standard/ambitious source-rating device profiles to the existing tariff producer. It uses an exact Europe/Budapest civil-year weather window, explicit distributor/tariff and discounted allocations, and one conserved twelve-month connection-fee ledger. A1 uses two settlement-window portions; H retains one outside-season allocation without an August reset. Price responses remain frozen2026 SCN in nominal HUF, with connection charges separate from device attribution and no installed/household bill or B12 cashflow admission. See [V1-043](../../docs/checkpoints/V1_043_ANNUAL_TARIFF_REFERENCE.md).

## Dated topology authority reference

`topology_reference.py` reads the explicit 2026-10-03 source-qualified H reference: six wiring categories and four independent charge/discharge/export/VPP-control dispositions. Actual-site permissions remain OPEN/Q; all execution is disabled. Reference-path absence differs from legal NO; foregone value is unknown, not zero. The current-law correction preserves the repealed historical source identity. Current aggregation law includes import-side response without export or supplier/BRP permission, while actual contracts, metering and protocol applicability remain open. See [V1-055](../../docs/checkpoints/V1_055_H_TOPOLOGY_AUTHORITY.md). No tariff numeric output, B07 physical operation or readiness value changes.
