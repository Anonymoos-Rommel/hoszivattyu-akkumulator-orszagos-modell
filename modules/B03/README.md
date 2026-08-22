# B03 – Gázár és földgáz-kitettség

## Cél

Időben változó, auditálható gázárpályák előállítása külön nagykereskedelmi/importérték- és lakossági végár-kimenettel.

## Bemeneti szerződés

- termék- és lejáratspecifikus TTF spot/forward ár, `EUR/MWh`;
- időben illesztett EUR/HUF árfolyam, `HUF/EUR`;
- hálózati pont- és időszakspecifikus alsó hőérték, `MJ/m3`;
- rendszerhasználati, tárolási, kereskedelmi, adó- és rezsivédelmi komponensek;
- importmix és hosszú távú fundamentális forgatókönyv.

## Kimeneti szerződés

- `WHOLESALE_IMPORT` nagykereskedelmi/importérték, `HUF/m3`, csak B11;
- `MARKET_RESIDENTIAL_FINAL` teljes piaci lakossági végár, `HUF/m3`, csak B12;
- `REGULATED_RESIDENTIAL_TARIFF` kedvezményes és küszöb feletti szabályozott tarifa, csak B13;
- `GAS-LOW`, `GAS-BASE`, `GAS-HIGH`, `GAS-STRESS` forward és long-run zónával;
- minden ponthoz termék-, dátum-, forrás- és státusz-lineage.

## Invariánsok

- a nagykereskedelmi proxy nem helyettesítheti a lakossági végárat;
- a forward görbe nem hosszabbítható automatikusan a teljes 15–20 éves horizontra;
- a konverzió mértékegysége és referenciaállapota explicit;
- időfüggő ár licenc és snapshot nélkül nem kanonikus megfigyelés.
- piaci lakossági végár csak teljes commodity + network + storage + commercial + tax + VAT + other híddal számolható;
- a 63 645 MJ / legalább 1 729 m3 éves küszöb a tarifastruktúrában OBS, az egységárak hiánya Q;
- B02/OÉNY artefaktumhoz ez a modul nem ír.

## Állapot

`BLOCKED` – a három réteg szerződve; a `REGULATED_RESIDENTIAL_TARIFF` réteg `VALIDATED` a 2026-08-22-i MVM snapshot alapján, miközben a licencelt TTF export és a teljes market-residential komponenshíd továbbra is Q.

## Kanonikus artefaktumok

- `docs/source_packs/B03_GAS_PRICE_AND_EXPOSURE.md`
- `registry/gas_price_sources.csv`
- `registry/gas_price_variables.csv`
- `registry/gas_price_formulas.csv`
- `data/processed/gas_price_history.csv`
- `data/processed/gas_price_forward_curve.csv`
- `data/processed/gas_price_scenarios.csv`
- `data/processed/residential_gas_tariff_schedule.csv`
- `data/processed/gas_price_component_bridge.csv`
