# B05 – Hőszivattyú fizikai és teljesítménymodell

Snapshot: 2026-08-22. A B05 fizikai modul; nem tarifa- vagy háztartási gazdaságossági modul.

## Forrás- és módszertani kapuk

- **JRC COP-definíció (`OBS`)**: a COP hasznos hőleadás / villamos input aránya. A B05 total-unit electrical input határt használ; compressor-only adatot nem emel teljes rendszerinputtá.
- **EN 14511 / EN 14825 metadata (`OBS`)**: az EN 14511 operating-point méréshez, az EN 14825 szezonális számításhoz ad módszertani keretet. A szabvány szövege nem kerül a repositoryba, csak a hivatkozott módszertani tény és URL.
- **EPREL (`OBS`)**: az Európai Bizottság nyilvános termékregisztere a modellek energia- és teljesítményadatainak acquisition gate-je. A nyilvános rated output vagy declared SCOP önmagában nem operating-point capacity/input térkép.
- **HungaroMet (`OBS`)**: az ODP historikus HABP_1H állomáscsaládja az elsődleges weather truth. A dokumentáció szerint `Time` UTC (`YYYYMMDDHHmm`), `t` órás pillanatnyi hőmérséklet, `ta` elmúlt óra átlaghőmérséklete, `tn`/`tx` az óra minimuma/maximuma, `u` pillanatnyi relatív nedvesség, a hiányjel `-999`. A station metadata külön azonosítót, koordinátát, magasságot és elérhető időszakot ad.
- **Vaillant aroTHERM Split (`OBS`, EU-origin-gated)**: a gyártói műszaki PDF 3,5/7/12 kW méretosztályban A−7/W35, A2/W35, A7/W35 és A7/W55 pontokat közöl; ugyanaz a dokumentum a gyártást kizárólag EU-sként jelöli.
- **Vaillant aroTHERM plus (`OBS`, EU-origin-gated)**: a gyártói műszaki PDF a VWL 55/6 A-hoz A−7/W35, A2/W35, A7/W35, A7/W45 és A7/W55 pontokat közöl, továbbá A7/W35-nél 2,10 kW minimum-modulációs értéket; külön Vaillant Group-origin forrás az EU-s (Franciaország/Szlovákia) termelési láncot rögzíti.
- **STIEBEL ELTRON HPA-O CS Plus int (`OBS`, EU-origin-gated)**: a gyártói kézikönyv a HPA-O 4 és 8 modellekhez teljes `A−7/A2/A7 × W35/W45` téglalapot közöl capacity, total-unit input és COP értékekkel, továbbá A7/W55 pontot és W35 min/max kimeneti tartományt; a kézikönyv „Made in Germany” jelölést, a gyártó telephely-forrása pedig holzmindeni levegő-víz hőszivattyú-gyártást rögzít.
- **Synthetic grid (`SCN`)**: a hatpontos air-to-water rács kizárólag motor- és tesztfixture; nem termék- vagy országos bizonyíték.

## Engine contract

`modules/B05/engine.py` explicit `HourlyDemand` és `PerformancePoint` inputokat fogad. A teljes téglalap-rácson determinisztikus bounded bilineáris interpolációt végez. Ismert pontot exact módon ad vissza; a rácson kívül vagy hiányzó sarokpontnál `Q / OUT_OF_PERFORMANCE_DOMAIN` illetve `Q / MISSING_GRID_POINT` eredményt ad.

Ha a thermal capacity, total electrical input és COP közül csak kettő forrásolt, a harmadik `DER`. Ha mindhárom meg van adva és nem egyeznek, a térkép validációja megáll. Az engine nem extrapolál és nem alkalmaz rejtett defrost- vagy cycling-penalty-t.

## B05-P2 coverage matrix

A gépi lefedettségi mátrix a `data/processed/heat_pump_performance_coverage.csv` fájlban van. A STIEBEL HPA-O 4/8 CS Plus int termékeknél a következő téglalap minden sarka `OBS`, ezért a runtime két dimenzióban interpolálhat:

| Tout | W35 | W45 | W55 |
|---:|:---:|:---:|:---:|
| −15 °C | OBS | Q | Q |
| −7 °C | OBS | OBS | Q |
| +2 °C | OBS | OBS | Q |
| +7 °C | OBS | OBS | OBS |

A Vaillant térképekben a hiányzó cellák explicit `Q`-k maradnak; ezek nem kerültek interpolációval feltöltésre.

## B05-P3 Hungarian hourly weather evidence

Az `data/processed/heat_pump_weather_hourly.csv` fájlban öt állomás (Szombathely 15310, Budapest Pestszentlőrinc 44527, Szeged 58102, Kecskemét K-puszta 46304, Miskolc Diósgyőr 52744) station-specific `OBS` sora található. A referencia-profil a legutóbbi közös teljes megfigyelt év (2025), de nem minősül automatikusan 1991–2020 normálnak. A `ta → outdoor_temperature_C` leképezés explicit `DER`; a source-native `t` és `u` megmarad. `-999` üres értékké válik, nincs forward/backward fill, interpoláció vagy más állomással pótlás.

Az `OBSERVED_EXTREME_COLD_SPELL` profil a teljes elérhető panel-archívumból a leghidegebb, folytonos 72 órás `ta` ablakot materializálja (Szombathely, 2005-02-07 09:00Z – 2005-02-10 08:00Z); ez nem 1-in-10 visszatérési idő. A 1991–2020 homogenizált normál-klíma evidence layer külön marad a raw observed hourly eseményrétegtől. Nincs országos vagy népességsúlyozás.

A `data/processed/heat_pump_weather_coverage.csv` külön méri a régi `−7…+7 °C` és az új HPA-O 4 W35 `−15…+7 °C` performance-map tartomány weather-domain coverage értékeit. Ez nem heating-runtime coverage. A tartományon kívüli órák `Q / OUT_OF_PERFORMANCE_DOMAIN` állapotot kapnak; operating envelope-ból nem következik teljesítmény-map extrapoláció.

## B05-P4 cold-side extension

Az STIEBEL ELTRON hivatalos HPA-O CS Plus int kézikönyvének EN 14511 táblája source-native pontokat közöl `A-15/W35` mellett: HPA-O 4: 3,43 kW hőteljesítmény, 1,42 kW teljes egység-input, COP 2,41; HPA-O 8: 7,07 kW, 2,84 kW, COP 2,49. A kézikönyv az integrált segédhajtások inputját az EN 14511 output details részének tekinti, és külön jelzi a −20 °C hőforrás-alkalmazási határt; ez utóbbi nem performance point.

Az új `OBS` sarkok csak W35-re terjesztik ki a ténylegesen interpolálható tartományt `−7 °C`-ról `−15 °C`-ra. W45/W55 hidegoldali cellák továbbra is `Q`. A Szombathelyi 72 órás eseményben a W35 weather-domain coverage 9/72 (12,5%) értékről 35/72-re (48,6%) nő; 37 óra `Q` marad `Tout < −15 °C` miatt.

A kézikönyv automatikus defrostot és defrost-energiaigényt említ, de az A-15/W35 táblapontok defrost-beszámítási határa nem különül el; P4 nem vezet be defrost-penaltyt.

## B05-P5 high-supply audit

A P5 audit elsődlegesen a STIEBEL ELTRON HPA-O 4/8 család hideg W45/W55 pontjait kereste. A hivatalos HPA-O kézikönyv A-7/W45-ig közöl teljes capacity/input/COP adatot; A-15/W45 vagy A-15/W55 HPA-O 4/8 pont nincs benne. A külön STIEBEL WPL-A kiegészítő táblázat tartalmaz A-15/W45 és A-15/W55 oszlopokat, de a P5-ben ellenőrzött sorok output-only adatok és a dokumentum estimated/interpolated caveatot jelöl; teljes total-unit input/COP hármas és HPA-O 4/8 modellazonosság nélkül ez a forrás `Q`, nem canonical `OBS`.

Ezért nincs új hideg W45/W55 performance point, nincs W35→W45 fallback, és nincs readiness-emelés. A `data/processed/heat_pump_weather_supply_coverage.csv` külön W35/W45/W55 surface szerint jelenti a weather-domain lefedettséget. Az extrém 72 órás eseménynél W35: `35/72` (`48,6%`), W45: `9/72` (`12,5%`), W55: incomplete surface miatt `Q` és nem számszerűsített. Ez nem heating-runtime coverage.

## Output boundary

Az operating-point outputok: `cop`, `thermal_capacity_kW`, `electrical_input_kW`, `available_capacity_kW`, `part_load_ratio`, `capacity_shortfall_kW`. Az órás outputok külön tartják a térfűtést, HMV-t, hőszivattyú-villamos energiát, backup-villamos energiát és összes villamos energiát.

`seasonal_cop_simulated = hp_heat_delivered / hp_electricity` és `spf_simulated = total_useful_heat / total_electricity`. Egyik sem `scop_en14825_declared`, és `scop_en14825_calculated` sincs állítva, mert a szabvány teljes számítása nincs implementálva.

## Q-k és tilalmak

1. A STIEBEL HPA-O 4/8 CS Plus int W35 felülete `−15/−7/2/7 °C`, W45 felülete `−7/2/7 °C`; W55 hideg-oldali kombinációk, a P5 output-only audit candidate és a Vaillant hiányzó cellái továbbra is sparse/Q-k.
2. A megfigyelt 72 órás extrém esemény már materializálva van; a hivatalos, reprodukálható magyar `1-in-10` visszatérési idő, winter-metrika és stationarity gate továbbra is `Q`.
3. Defrost-adat és külön modell hiányában nincs büntetés.
4. Vaillantnál egy numeric minimum-modulation pont, STIEBEL HPA-O 4/8-nál A−7/A2/A7 W35 min/max kimeneti tartomány érhető el; part-load COP és cycling degradation továbbra is hiányzik, a motor csak állapotot jelez.

### P6 defrost- és cycling-audit

A P6 audit a [külön bizonyítékkapu](B05_P6_DEFROST_CYCLING_EVIDENCE.md) szerint
lezárta, hogy a jelenlegi forrásokból nem vezethető le külön, termékszintű
defrost-energia- vagy cycling-degradation runtime-modell. A STIEBEL manual
defrost-energy/hidraulikai feltételt, a Vaillant dokumentáció defrost-volume és
anti-cycling/modulation állapotot közöl, de nem a source-native performance
points elszámolási határát vagy mért Cdh-t. Az EU 813/2013 `Cdh=0,9` értéke
elkülönített `POL` compliance default; nem kerül `OBS`-ként a registrybe és nem
alkalmazzuk automatikusan a runtime-ra. A meglévő engine ezért változatlanul
nem alkalmaz rejtett defrost- vagy cycling-penaltyt, és a humidity csak
forrásnatív bemenet marad.
5. HMV priority és magasabb előremenő üzemmód csak explicit termékadat esetén használható.
6. Egy termék teljesítménytérképe nem skálázható automatikusan 6/8/10/12/16 kW gépekre.
7. B04 tarifa, ár, gázár, számla, támogatás, finanszírozás, battery/VPP dispatch és pénzérték nem szerepel a B05 runtime-ban.
8. A HungaroMet felhasználási feltételei forrásmegjelölést írnak elő, és a módosított adat közléséhez előzetes engedélyt kérnek; ezért raw ZIP nem kerül a public repóba, csak bounded derived materialization, hash-olható source reference és acquisition tooling.

## Downstream interface

B02/B06 explicit hőigény- és readiness-kaput adhat; B04 és későbbi B12 csak a B05 által leadott hő- és villamos-idősor után alkalmazhat ár- vagy gazdasági modellt. A jelenlegi `B02;B03;B04` module dependency orchestration gate-ként megmarad, de a fizikai engine nem fogyaszt B03/B04 numerikus értéket.
