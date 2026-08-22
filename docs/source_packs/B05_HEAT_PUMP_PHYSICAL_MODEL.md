# B05 – Hőszivattyú fizikai és teljesítménymodell

Snapshot: 2026-08-22. A B05 fizikai modul; nem tarifa- vagy háztartási gazdaságossági modul.

## Forrás- és módszertani kapuk

- **JRC COP-definíció (`OBS`)**: a COP hasznos hőleadás / villamos input aránya. A B05 total-unit electrical input határt használ; compressor-only adatot nem emel teljes rendszerinputtá.
- **EN 14511 / EN 14825 metadata (`OBS`)**: az EN 14511 operating-point méréshez, az EN 14825 szezonális számításhoz ad módszertani keretet. A szabvány szövege nem kerül a repositoryba, csak a hivatkozott módszertani tény és URL.
- **EPREL (`OBS`)**: az Európai Bizottság nyilvános termékregisztere a modellek energia- és teljesítményadatainak acquisition gate-je. A nyilvános rated output vagy declared SCOP önmagában nem operating-point capacity/input térkép.
- **HungaroMet/OMSZ (`OBS` source gate)**: nyílt meteorológiai archívum és órás állomásadatok. A magyar 1-in-10 hideg tél és többnapos extrém esemény reprodukálható definíciója még `Q`.
- **Vaillant aroTHERM Split (`OBS`, EU-origin-gated)**: a gyártói műszaki PDF 3,5/7/12 kW méretosztályban A−7/W35, A2/W35, A7/W35 és A7/W55 pontokat közöl; ugyanaz a dokumentum a gyártást kizárólag EU-sként jelöli.
- **Vaillant aroTHERM plus (`OBS`, EU-origin-gated)**: a gyártói műszaki PDF a VWL 55/6 A-hoz A−7/W35, A2/W35, A7/W35, A7/W45 és A7/W55 pontokat közöl, továbbá A7/W35-nél 2,10 kW minimum-modulációs értéket; külön Vaillant Group-origin forrás az EU-s (Franciaország/Szlovákia) termelési láncot rögzíti.
- **Synthetic grid (`SCN`)**: a hatpontos air-to-water rács kizárólag motor- és tesztfixture; nem termék- vagy országos bizonyíték.

## Engine contract

`modules/B05/engine.py` explicit `HourlyDemand` és `PerformancePoint` inputokat fogad. A teljes téglalap-rácson determinisztikus bounded bilineáris interpolációt végez. Ismert pontot exact módon ad vissza; a rácson kívül vagy hiányzó sarokpontnál `Q / OUT_OF_PERFORMANCE_DOMAIN` illetve `Q / MISSING_GRID_POINT` eredményt ad.

Ha a thermal capacity, total electrical input és COP közül csak kettő forrásolt, a harmadik `DER`. Ha mindhárom meg van adva és nem egyeznek, a térkép validációja megáll. Az engine nem extrapolál és nem alkalmaz rejtett defrost- vagy cycling-penalty-t.

## Output boundary

Az operating-point outputok: `cop`, `thermal_capacity_kW`, `electrical_input_kW`, `available_capacity_kW`, `part_load_ratio`, `capacity_shortfall_kW`. Az órás outputok külön tartják a térfűtést, HMV-t, hőszivattyú-villamos energiát, backup-villamos energiát és összes villamos energiát.

`seasonal_cop_simulated = hp_heat_delivered / hp_electricity` és `spf_simulated = total_useful_heat / total_electricity`. Egyik sem `scop_en14825_declared`, és `scop_en14825_calculated` sincs állítva, mert a szabvány teljes számítása nincs implementálva.

## Q-k és tilalmak

1. A Vaillant pontkészlet már `OBS`, de a térképek sparse-ok; nincs teljes rectangular grid vagy általános termékskálázás.
2. Nincs reprodukálható magyar 1-in-10/extreme weather sorozat.
3. Defrost-adat és külön modell hiányában nincs büntetés.
4. Egy numeric minimum-modulation pont elérhető az aroTHERM plus VWL 55/6 A-hoz; a többi termék floorja, part-load COP és cycling degradation adata hiányzik, a motor csak állapotot jelez.
5. HMV priority és magasabb előremenő üzemmód csak explicit termékadat esetén használható.
6. Egy termék teljesítménytérképe nem skálázható automatikusan 6/8/10/12/16 kW gépekre.
7. B04 tarifa, ár, gázár, számla, támogatás, finanszírozás, battery/VPP dispatch és pénzérték nem szerepel a B05 runtime-ban.

## Downstream interface

B02/B06 explicit hőigény- és readiness-kaput adhat; B04 és későbbi B12 csak a B05 által leadott hő- és villamos-idősor után alkalmazhat ár- vagy gazdasági modellt. A jelenlegi `B02;B03;B04` module dependency orchestration gate-ként megmarad, de a fizikai engine nem fogyaszt B03/B04 numerikus értéket.
