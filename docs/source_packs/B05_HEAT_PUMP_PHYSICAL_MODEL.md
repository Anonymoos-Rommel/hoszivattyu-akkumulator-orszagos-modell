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
| −7 °C | OBS | OBS | Q |
| +2 °C | OBS | OBS | Q |
| +7 °C | OBS | OBS | OBS |

A Vaillant térképekben a hiányzó cellák explicit `Q`-k maradnak; ezek nem kerültek interpolációval feltöltésre.

## B05-P3 Hungarian hourly weather evidence

Az `data/processed/heat_pump_weather_hourly.csv` fájlban öt állomás (Szombathely 15310, Budapest Pestszentlőrinc 44527, Szeged 58102, Kecskemét K-puszta 46304, Miskolc Diósgyőr 52744) station-specific `OBS` sora található. A referencia-profil a legutóbbi közös teljes megfigyelt év (2025), de nem minősül automatikusan 1991–2020 normálnak. A `ta → outdoor_temperature_C` leképezés explicit `DER`; a source-native `t` és `u` megmarad. `-999` üres értékké válik, nincs forward/backward fill, interpoláció vagy más állomással pótlás.

Az `OBSERVED_EXTREME_COLD_SPELL` profil a teljes elérhető panel-archívumból a leghidegebb, folytonos 72 órás `ta` ablakot materializálja (Szombathely, 2005-02-07 09:00Z – 2005-02-10 08:00Z); ez nem 1-in-10 visszatérési idő. A 1991–2020 homogenizált normál-klíma evidence layer külön marad a raw observed hourly eseményrétegtől. Nincs országos vagy népességsúlyozás.

A `data/processed/heat_pump_weather_coverage.csv` az aktuális STIEBEL `−7…+7 °C` performance-map tartomány órás lefedettségét méri. A tartományon kívüli órák `Q / OUT_OF_PERFORMANCE_DOMAIN` állapotot kapnak; operating envelope-ból nem következik teljesítmény-map extrapoláció.

## Output boundary

Az operating-point outputok: `cop`, `thermal_capacity_kW`, `electrical_input_kW`, `available_capacity_kW`, `part_load_ratio`, `capacity_shortfall_kW`. Az órás outputok külön tartják a térfűtést, HMV-t, hőszivattyú-villamos energiát, backup-villamos energiát és összes villamos energiát.

`seasonal_cop_simulated = hp_heat_delivered / hp_electricity` és `spf_simulated = total_useful_heat / total_electricity`. Egyik sem `scop_en14825_declared`, és `scop_en14825_calculated` sincs állítva, mert a szabvány teljes számítása nincs implementálva.

## Q-k és tilalmak

1. A STIEBEL HPA-O 4/8 CS Plus int már használható teljes `-7/2/7 × W35/W45` `OBS` surface-ként; a Vaillant pontkészletek és a W55 hideg-oldali kombinációk továbbra is sparse-ok.
2. A megfigyelt 72 órás extrém esemény már materializálva van; a hivatalos, reprodukálható magyar `1-in-10` visszatérési idő, winter-metrika és stationarity gate továbbra is `Q`.
3. Defrost-adat és külön modell hiányában nincs büntetés.
4. Vaillantnál egy numeric minimum-modulation pont, STIEBEL HPA-O 4/8-nál A−7/A2/A7 W35 min/max kimeneti tartomány érhető el; part-load COP és cycling degradation továbbra is hiányzik, a motor csak állapotot jelez.
5. HMV priority és magasabb előremenő üzemmód csak explicit termékadat esetén használható.
6. Egy termék teljesítménytérképe nem skálázható automatikusan 6/8/10/12/16 kW gépekre.
7. B04 tarifa, ár, gázár, számla, támogatás, finanszírozás, battery/VPP dispatch és pénzérték nem szerepel a B05 runtime-ban.
8. A HungaroMet felhasználási feltételei forrásmegjelölést írnak elő, és a módosított adat közléséhez előzetes engedélyt kérnek; ezért raw ZIP nem kerül a public repóba, csak bounded derived materialization, hash-olható source reference és acquisition tooling.

## Downstream interface

B02/B06 explicit hőigény- és readiness-kaput adhat; B04 és későbbi B12 csak a B05 által leadott hő- és villamos-idősor után alkalmazhat ár- vagy gazdasági modellt. A jelenlegi `B02;B03;B04` module dependency orchestration gate-ként megmarad, de a fizikai engine nem fogyaszt B03/B04 numerikus értéket.
