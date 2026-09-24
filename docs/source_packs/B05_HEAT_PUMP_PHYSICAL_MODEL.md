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
helyesen nem vezetett be külön termékszintű defrost-energia- vagy
cycling-degradation runtime-modellt. B05-P14 később részlegesen supersedeli a
P6 accounting-boundary következtetését: explicit EN 14511-tagged pointoknál a
rating interval alatt fellépő defrost hőhatása a heating-capacity, villamos
igénye pedig az effective-power-input accounting része, ezért külön univerzális
defrost penalty nem adható hozzá. Ez nem bizonyít tényleges defrost eseményt
minden rating pointnál és nem ad weather-driven runtime modellt. Az EU 813/2013
`Cdh=0,9` továbbra is elkülönített `POL` compliance default; nem kerül
`OBS`-ként a registrybe és nem alkalmazzuk automatikusan a runtime-ra. Az
engine ezért változatlanul nem alkalmaz rejtett defrost- vagy cycling-penaltyt,
és a humidity csak forrásnatív bemenet marad.
5. HMV priority és magasabb előremenő üzemmód csak explicit termékadat esetén használható.
6. Egy termék teljesítménytérképe nem skálázható automatikusan 6/8/10/12/16 kW gépekre.
7. B04 tarifa, ár, gázár, számla, támogatás, finanszírozás, battery/VPP dispatch és pénzérték nem szerepel a B05 runtime-ban.
8. A HungaroMet felhasználási feltételei forrásmegjelölést írnak elő, és a módosított adat közléséhez előzetes engedélyt kérnek; ezért raw ZIP nem kerül a public repóba, csak bounded derived materialization, hash-olható source reference és acquisition tooling.

## Downstream interface

B02/B06 explicit hőigény- és readiness-kaput adhat; B04 és későbbi B12 csak a B05 által leadott hő- és villamos-idősor után alkalmazhat ár- vagy gazdasági modellt. A jelenlegi `B02;B03;B04` module dependency orchestration gate-ként megmarad, de a fizikai engine nem fogyaszt B03/B04 numerikus értéket.

## B05-P11 Tekno Point cold high-supply rectangle

P11 adds two current Tekno Point ATHENA R32 equipment maps with source-native
capacity, published electrical power input and COP at the four corners
`A-15/A-7 x W35/W55`.

For each admitted product the existing B05 engine therefore has a complete
rectangle over outdoor `-15..-7 C` and supply `35..55 C`. The full P9
project-derived mean cold-stress interval `-13.331944..-9.644444 C` is inside
that rectangle. W35/W45/W55 model points across that interval are admissible
without extrapolation; source corners remain OBS and interior coordinates are
DER.

The current ATHENA R32 product page states heating-water operation to 55 C at
-20 C outdoor, but P11 does not turn that limit into a performance point.
Below -15 C therefore remains Q unless a complete colder performance surface is
later admitted.

P11 does not create national market-share weights and does not close defrost,
cycling/part-load or DHW-priority gates. The manufacturer `P assorb. / Power`
field is normalized to the B05 heat-pump product-unit electrical-input boundary;
no external system auxiliary or separable defrost-energy term is inferred.

## B05-P12 EC POWER cross-manufacturer cold surface

P12 adds EC POWER PMH 6/19 source-native heating capacity + COP points at
`A-15/A-7 x W35/W55`. The source-observation layer preserves those OBS pairs.
The source does not publish electrical input at those cold points, so P12
materializes `electrical_input = capacity / COP` as DER and marks the
canonical complete performance-point rows DER.

Together with P11 Tekno Point ATHENA R32 complete triples, this gives two
different current European manufacturer families with B05-admissible complete
physical surfaces over `-15..-7 C x W35..W55`.

The P9 `-13.331944..-9.644444 C` mean cold-stress envelope and W35/W45/W55
anchors are therefore cross-manufacturer covered without extrapolation.
P12 qualifies surface availability only: unlike product sizes are not averaged,
product count is not a market-share weight, and EC POWER Hungarian
sales/procurement presence is not asserted.

The manufacturer sheet states a wider heating operating range down to -25 C,
but this is not promoted to a performance point. Below -15 C remains Q if
hourly-extreme runtime is retained. Defrost accounting also remains Q.

## B05-P13 WAMAK observed extreme cold closure

P13 adds WAMAK AWK 35 EVI source performance at the four corners
`A-22/A-10 x W35/W55`.

Three source triples are internally consistent and remain OBS. The published
A-22/W55 `Qh=21.2 kW / P=13.0 kW / COP=1.51` triple fails the canonical B05
consistency tolerance, so the source conflict is preserved and the 13.0 kW
input is not promoted. The canonical A-22/W55 input is materialized as
`21.2 / 1.51 = 14.039735099 kW` DER; that complete canonical point is DER.

The canonical observed extreme event minimum `-21.9 C` lies inside the
admitted `-22..-10 C` outdoor rectangle and W35/W45/W55 lie inside the
`35..55 C` supply rectangle. The event minimum is therefore evaluable without
extrapolation for this bounded product map.

This resolves Q-B05-001 for the declared physical performance-map scope.
It does not convert the historical event minimum into a future design
temperature, and it does not close market/procurement, defrost, cycling or DHW
questions.

## B05-P14 EN 14511 defrost accounting boundary

P14 direct EN 14511 method authority alapján különválasztja a rating-point
accountingot a weather-driven defrost runtime modelltől.

Az explicit EN 14511-tagged canonical performance pointokra:

- a rating intervalban fellépő defrost miatt elvont hő a heating-capacity
  accounting része;
- a defrost villamos igénye az effective power input része;
- ezért egy második, univerzális defrost penalty alkalmazása tiltott, mert
  kettős elszámolást okozhat.

A jelenlegi canonical point-setben 36 explicit EN 14511-tagged pont van.
Ez a szabály csak ezekre a bizonyított test-basisú pontokra vonatkozik.

A NIBE P10 continuous capacity curves külön maradnak, mert a gyártó explicit
defrost-excluded görbeként publikálja őket. A Tekno Point P11 és EC POWER P12
pontokat P14 nem minősíti visszamenőleg EN 14511-accounted pontokká, ha a
canonical test basis nincs explicit kötve.

A product-specific/weather-driven defrost event frequency, duration, heat
removal, electricity és auxiliary-heater interaction továbbra is Q. A Vaillant
UK 12-15% design allowance kizárólag UK design context; nem magyar runtime
penalty.

Q-B05-003 ezért nem záródik, hanem
`OPEN_NARROWED_TO_WEATHER_DRIVEN_RUNTIME_MODEL` állapotba kerül.
