# B05-P6: defrost- és part-load/cycling bizonyítékkapu

Állapot: **EVIDENCE AUDIT COMPLETE – runtime penalty-model Q**  
Lekérés dátuma: **2026-08-22**

## Döntési összefoglaló

P6 nem hozott létre új fizikai penalty-képletet. A források az üzemállapotot és
a készülék/hidraulika követelményeit dokumentálják, de nem adnak a jelenlegi
source-native EN 14511 pontokhoz illeszthető, külön defrost-energia- vagy
cycling-degradation idősorokat. Ezért:

- a defrost inclusion boundary és a defrost runtime penalty `Q`;
- a below-minimum-modulation állapot jelölhető, de a cycling runtime penalty `Q`;
- a mért `Cdh` `Q`;
- az EU 813/2013 szerinti `Cdh = 0,9` külön `POL` szabályozási default, nem
  termék-`OBS`, és nem kerül automatikusan a B05 órás runtime-ba.

Az engine változatlanul fail-closed: `defrost_status=Q` mellett nem von le és
nem ad hozzá rejtett energiát; cycling állapotnál a source-native COP/input
marad az egyetlen villamosenergia-alap. Így ugyanazt a veszteséget nem lehet
kétszer elszámolni.

## Forrásaudit

| Forrás | Mit bizonyít | Mit nem bizonyít |
|---|---|---|
| [STIEBEL HPA-O CS Plus manual](https://www.stiebel-eltron.com/toolbox/content/docs/anleitungen/installation/HPA_O_Plus/332107-43892-9726_HPA-O_3-8_CS_Plus_en.pdf) | A minimum flow és a defrost energy biztosítandó; kivételesen auxiliary heater aktiválódhat defrost alatt. | Nem ad pontszintű defrost-kWh-sorozatot, páratartalomfüggő modellt vagy a táblázati EN 14511 pontok defrost-boundary-jét. |
| [Vaillant aroTHERM plus technical data](https://professional.vaillant.co.uk/downloads/aproducts/renewables-1/arotherm-plus/arotherm-plus-spec-sheet-1892564.pdf) és [controls instructions](https://professional.vaillant.co.uk/downloads/aproducts/renewables-1/arotherm-plus/appliance-interface-operating-and-installation-instructions-1799367.pdf) | Minimum heating-circuit volume defrosthoz; compressor anti-cycling time és compressor modulation állapot elérhető. | Nem ad mért Cdh-t, cycling COP-t vagy point-level defrost accountingot. |
| [Commission Regulation (EU) No 813/2013](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32013R0813) | Definiálja a cycling interval mennyiségeket és kimondja, hogy mérés hiányában a szabályozási default `Cdh=0,9`. | Nem teszi a defaultot az adott termék mért értékévé, és nem engedélyez automatikus B05 runtime penalty-t. |
| [JRC EN 14511/EN 14825 method note](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC109209/kjnc28961enn.pdf) | A tesztmódszer és határfogalmak auditálhatók. | Nem tartalmazza a konkrét HPA-O/Vaillant pontok defrost inclusion boundary-ját. |

## Canonical kezelési szabály

| Fogalom | Státusz | Runtime használat |
|---|---|---|
| `defrost_accounting_boundary` | Q | Nincs automatikus korrekció |
| `defrost_runtime_penalty` | Q | Nincs hozzáadás/levonás |
| `cdh_measured` | Q | Nincs cycling-korrekció |
| `cdh_regulatory_default` | POL (`0,9`) | Csak külön compliance-method módban, nem B05 OBS/runtime |
| `cycling_penalty_runtime` | Q | Nincs hozzáadás/levonás |

A `relative_humidity_pct` bemenet megőrzött időjárási adat, nem defrost trigger:
hiánya nem tölthető ki, megléte pedig önmagában nem bizonyít defrost eseményt.

## Readiness-hatás

P6 után a `DEFROST` és `PART_LOAD_MODULATION` readiness nem emelkedik:

- `DEFROST = Q / 5%`;
- `PART_LOAD_MODULATION = PARTIAL / 45%`;
- `PERFORMANCE_MAP = PARTIAL / 80%`;
- `WEATHER_PERFORMANCE_DOMAIN_COVERAGE = PARTIAL / 50%`;
- teljes `B05 = IN_PROGRESS / 64%`.

A fennmaradó magas értékű kérdések: termékszintű defrost inclusion boundary és
defrost energy series; mért part-load/Cdh vagy cycling COP; továbbá a hideg
W45/W55 pontfelület teljessége és a B02/B06 hőigény-interfész.
