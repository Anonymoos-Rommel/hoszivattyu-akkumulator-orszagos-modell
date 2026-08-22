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
- akkumulátoros/VPP töltés nem rendelhető H tarifához elfogadott jogi-műszaki szabály nélkül.

## Állapot

`BLOCKED` – a REGULATED_RESIDENTIAL_ELECTRICITY réteg aktuális MVM snapshotja és az A1/H szabályok lezárva; a H akkumulátor/export jogosultság Q, a teljes 2015–2026 HUPX history/forward licencelt adat Q, a MARKET_BASED komponenshíd részleges, a lakossági dinamikus termék Q.

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
