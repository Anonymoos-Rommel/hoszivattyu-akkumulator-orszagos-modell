# B05 – Hőszivattyú fizikai és teljesítménymodell

## Cél

A B05 egy explicit hőigény- és időjárás-profilra alkalmazott, operating-point teljesítménytérképes hőszivattyú-fizikai motor. Nem egyetlen éves SCOP/COP értékkel helyettesíti az üzemi viselkedést.

## Bemeneti szerződés

- órás `timestamp` és `outdoor_temperature_C` időjárási input;
- `space_heating_required_kW` és külön `dhw_required_kW` hőigény;
- `required_supply_temperature_C` és külön HMV előremenő hőmérséklet;
- berendezés-azonosító, technológia és source-native/certified operating-point teljesítménytérkép; a B05-P2 adatcsomag Vaillant aroTHERM és STIEBEL ELTRON HPA-O EU-origin-gated pontokat tartalmaz, utóbbinál teljes -7/2/7 × W35/W45 surface-szel;
- explicit backup-konfiguráció, ha van;
- opcionális páratartalom csak bizonyított defrost-modellhez.

## Kimeneti szerződés

- operating-point COP, hőteljesítmény, teljes egység villamos teljesítménye;
- elérhető kapacitás, igényelt kapacitás, részterhelési arány és kapacitáshiány;
- órás hőleadás, hőszivattyú-villamos energia, backup-villamos energia és összes villamos energia;
- szezonális hő, villamos energia, `seasonal_cop_simulated`, `spf_simulated` és fizikai csúcsteljesítmény;
- HMV és térfűtés külön inputmezőként, valamint explicit Q státusz, ha a módválasztás vagy a teljesítménytérkép nem bizonyított.

## Fizikai határ

B05 nem fogyaszt és nem számol Ft/kWh, Ft/MJ, gázárat, tarifát, számlát, megtérülést, finanszírozást, támogatást, fiskális vagy importértéket, akkumulátor/VPP dispatch-et. A B04 registry csak downstream komponens; nem módosíthatja a COP-ot vagy az energiaigényt.

## Módszer és fail-closed szabályok

- A V1 motor determinisztikus, bounded bilineáris interpolációt használ a teljesítménytérkép teljes téglalap-rácsán.
- Ismert pontot változtatás nélkül reprodukál; hiányzó sarokpont vagy tartományon kívüli hőmérséklet `Q / OUT_OF_PERFORMANCE_DOMAIN` vagy `Q / MISSING_GRID_POINT`.
- A kapacitás, teljes egység-input és COP közül kettőből a harmadik `DER`; három forrásérték inkonzisztenciája validációs hiba. A gyártói, két tizedesre kerekített táblákhoz legfeljebb 0,05 COP-eltérés tolerált; nagyobb eltérés Q/validációs hiba.
- Modulation-floor hiányában nincs kitalált degradációs együttható; a motor csak `CYCLING_REQUIRED` állapotot jelez, implicit büntetést nem ad.
- Defrost büntetés nincs beégetve: a defrost kimenetek Q-k, amíg bizonyított modell nem áll rendelkezésre.
- Backup csak explicit engedélyezéssel, típussal, kapacitással és hatásfokkal működik, és külön fogyasztásként jelenik meg.
- HMV eltérő hőmérsékleten egyidejű térfűtéssel csak explicit priority-konfigurációval fut; egyébként Q.

## SCOP / SPF szemantika

`scop_en14825_declared` (forrásban deklarált szezonális érték), `scop_en14825_calculated` (szabványos számítás, jelenleg nincs implementálva) és `seasonal_cop_simulated`/`spf_simulated` (saját órás szimuláció) külön fogalom. A jelenlegi szimulált COP a hőszivattyú által leadott hő és a hőszivattyú teljes egység-villamos energiájának aránya; az SPF a backup-ágat is tartalmazza.

## Időjárás és forgatókönyvek

Az engine csak explicit órás időjárási inputot fogad. A normal/reference, 1-in-10 cold és multi-day extreme címkék nem kerülnek OBS státuszba: a jelenlegi tesztadatok `SCN`, a hivatalos magyar órás és extrém-időjárási bizonyíték Q. A HungaroMet nyílt adattára az adatbeszerzés elsődleges kapuja.

## Readiness és Q-k

`PERFORMANCE_MAP=PARTIAL (72%)`; `THERMAL_DEMAND_INTERFACE=PARTIAL`; `WEATHER_INPUT=Q`; `DEFROST=Q`; `PART_LOAD_MODULATION=PARTIAL (45%)`; `OPERATING_ENVELOPE=PARTIAL (55%)`; `PRODUCT_DIVERSITY=PARTIAL (45%)`; `DHW_MODE=PARTIAL`; `PRODUCT_SCALING=Q`. A B05 státusza ezért `IN_PROGRESS`, nem `VALIDATED`. A jelenlegi B02/B03/B04 dependency edge megmarad orchestration-gate-ként, de a fizikai runtime nem használ tarifát vagy pénzértéket.

## Kanonikus artefaktumok

- `docs/source_packs/B05_HEAT_PUMP_PHYSICAL_MODEL.md`
- `modules/B05/engine.py`
- `registry/heat_pump_sources.csv`
- `registry/heat_pump_variables.csv`
- `registry/heat_pump_formulas.csv`
- `registry/heat_pump_scenarios.csv`
- `registry/heat_pump_readiness.csv`
- `data/processed/heat_pump_performance_points.csv`
- `data/processed/heat_pump_performance_coverage.csv`
- `data/processed/heat_pump_weather_scenarios.csv`
