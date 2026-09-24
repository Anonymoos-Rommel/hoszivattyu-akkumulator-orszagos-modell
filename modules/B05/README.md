# B05 – Hőszivattyú fizikai és teljesítménymodell

## Cél

A B05 egy explicit hőigény- és időjárás-profilra alkalmazott, operating-point teljesítménytérképes hőszivattyú-fizikai motor. Nem egyetlen éves SCOP/COP értékkel helyettesíti az üzemi viselkedést.

## Bemeneti szerződés

- órás `timestamp` és `outdoor_temperature_C` időjárási input;
- `space_heating_required_kW` és külön `dhw_required_kW` hőigény;
- `required_supply_temperature_C` és külön HMV előremenő hőmérséklet;
- berendezés-azonosító, technológia és source-native/certified operating-point teljesítménytérkép; a kanonikus exact point-set Vaillant aroTHERM és STIEBEL ELTRON HPA-O pontokat tartalmaz. B05-P10 külön NIBE S2125 source-native continuous W35/W45/W55 **capacity-domain** evidence-et ad a P9 hidegstressz-tartományára. B05-P11 két Tekno Point ATHENA R32 mérethez exact `A-15/A-7 × W35/W55` capacity + published power-input + COP sarkokat ad; ezekből az engine W45-öt és a P9 stressz-intervallum belső pontjait bounded DER interpolációval számolja. B05-P12 két EC POWER PMH mérethez ugyanezen sarokkoordinátákon source-native capacity + COP adatot ad; ezeket külön OBS source-layer őrzi, majd az electrical input a már meglévő two-of-three szabály szerint DER-ként materializálódik a canonical complete point-setbe;
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
- P6 audit: a `defrost_accounting_boundary`, `defrost_runtime_penalty`, `cdh_measured` és `cycling_penalty_runtime` külön Q-változók; az EU 813/2013 szerinti `cdh_regulatory_default=0,9` csak POL compliance-method érték, nem runtime-korrekció.
- Backup csak explicit engedélyezéssel, típussal, kapacitással és hatásfokkal működik, és külön fogyasztásként jelenik meg.
- HMV eltérő hőmérsékleten egyidejű térfűtéssel csak explicit priority-konfigurációval fut; egyébként Q.

## SCOP / SPF szemantika

`scop_en14825_declared` (forrásban deklarált szezonális érték), `scop_en14825_calculated` (szabványos számítás, jelenleg nincs implementálva) és `seasonal_cop_simulated`/`spf_simulated` (saját órás szimuláció) külön fogalom. A jelenlegi szimulált COP a hőszivattyú által leadott hő és a hőszivattyú teljes egység-villamos energiájának aránya; az SPF a backup-ágat is tartalmazza.

## Időjárás és forgatókönyvek

Az engine csak explicit órás időjárási inputot fogad. A HungaroMet ODP historikus automata-állomás adataiban a `Time` UTC, a `-999` hiányjel, a `ta` az elmúlt óra átlaghőmérséklete, a `t` pillanatnyi hőmérséklet, a `tn`/`tx` az óra minimuma/maximuma, az `u` pedig pillanatnyi relatív nedvesség. A canonical B05 `outdoor_temperature_C` kifejezetten `ta`-ból képzett `DER` leképezés; a source-native mezők `OBS` és a `t` nem cserélődik fel csendben.

A P3 materializáció öt állomás station-specific, legutóbbi közös teljes megfigyelt év (2025) profilját és a teljes elérhető archívumból kiválasztott, 72 órás megfigyelt hidegperiódust tartalmazza. A 2025-ös profil nem nevezhető 1991–2020 normálnak; a klimatológiai normál és a homogenizált adatsor külön evidence layer. Nincs imputáció, helyi időre/DST-re konverzió vagy országos súlyozás. P8/P9 104 teljes Dec-Feb blokk alapján project-derived empirical historical 10-year coldest-72h-mean stress envelope-et materializál `−13.331944…−9.644444 °C` tartományban; ez nem official HungaroMet 1-in-10 és nem jövőbeli gyakorisági állítás. P10 az official NIBE S2125 continuous capacity curves alapján bizonyítja, hogy W35/W45/W55 capacity-domain szinten ez a teljes mean-stress intervallum lefedett egy további gyártónál is. A P10 görbékből exact kW érték nem kerül digitizálásra. P11 viszont külön source-native teljesítménytáblából két ATHENA R32 mérethez complete `-15..-7 C × W35..W55` rectangular performance surface-et materializál; a teljes P9 mean-stress intervallumon W35/W45/W55 így extrapoláció nélkül értékelhető. Exact Tekno Point sarkok complete OBS triple-ek; az EC POWER exact capacity/COP forrásértékek OBS-k, a belőlük képzett electrical input DER. P11+P12 így két külön gyártónál ad teljes B05-admissible `-15..-7 C × W35..W55` fizikai felületet; a P9 stressz W35/W45/W55 tartománya cross-manufacturer lefedett. Az engine a complete performance-map határon kívül továbbra is fail-closed módon működik.

## Readiness és Q-k

`PERFORMANCE_MAP=PARTIAL (80%)`; `THERMAL_DEMAND_INTERFACE=PARTIAL`; `WEATHER_INPUT=PARTIAL (75%)`; `WEATHER_SOURCE=VALIDATED`; `HOURLY_WEATHER_INPUT=PARTIAL (85%)`; `REFERENCE_WEATHER=PARTIAL (60%)`; `COLD_1_IN_10=PARTIAL (80%)`; `EXTREME_COLD_EVENT=VALIDATED (90%)`; `SPATIAL_COVERAGE=PARTIAL (60%)`; `WEATHER_PERFORMANCE_DOMAIN_COVERAGE=PARTIAL (60%)`; `DEFROST=Q`; `PART_LOAD_MODULATION=PARTIAL (45%)`; `OPERATING_ENVELOPE=PARTIAL (55%)`; `PRODUCT_DIVERSITY=PARTIAL (45%)`; `DHW_MODE=PARTIAL`; `PRODUCT_SCALING=Q`. A B05 státusza ezért `IN_PROGRESS`, nem `VALIDATED`. A jelenlegi B02/B03/B04 dependency edge megmarad orchestration-gate-ként, de a fizikai runtime nem használ tarifát vagy pénzértéket.

## Kanonikus artefaktumok

- `docs/source_packs/B05_HEAT_PUMP_PHYSICAL_MODEL.md`
- `docs/source_packs/B05_P10_NIBE_COLD_HIGH_SUPPLY_CAPACITY_DOMAIN.md`
- `registry/b05_p10_nibe_cold_high_supply_capacity_domain.csv`
- `docs/source_packs/B05_P11_TEKNOPOINT_COLD_HIGH_SUPPLY_RECTANGLE.md`
- `registry/b05_p11_teknopoint_cold_high_supply_rectangle.csv`
- `docs/source_packs/B05_P12_ECPOWER_CROSS_MANUFACTURER_COLD_SURFACE.md`
- `registry/b05_p12_ecpower_cross_manufacturer_cold_surface.csv`
- `data/processed/b05_p12_ecpower_source_capacity_cop_observations.csv`
- `data/processed/b05_p12_cross_manufacturer_cold_high_supply_surface.csv`
- `modules/B05/cold_high_supply_cohort.py`
- `modules/B05/engine.py`
- `registry/heat_pump_sources.csv`
- `registry/heat_pump_variables.csv`
- `registry/heat_pump_formulas.csv`
- `registry/heat_pump_scenarios.csv`
- `registry/heat_pump_readiness.csv`
- `data/processed/heat_pump_performance_points.csv`
- `data/processed/heat_pump_performance_coverage.csv`
- `data/processed/heat_pump_weather_scenarios.csv`
- `data/processed/heat_pump_weather_hourly.csv`
- `data/processed/heat_pump_weather_profiles.csv`
- `data/processed/heat_pump_weather_coverage.csv`
- `data/processed/heat_pump_weather_supply_coverage.csv`
- `modules/B05/weather.py`
- `tools/materialize_b05_weather.py` (raw ZIP input outside Git; bounded derived output only)
