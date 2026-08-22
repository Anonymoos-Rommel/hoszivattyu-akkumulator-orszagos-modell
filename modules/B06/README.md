# B06 – Energetikai korszerűsítés

Állapot: **IN_PROGRESS – P1/P3 fizikai szerződés és fail-closed engine**

B06 a bizonyíték-alapú `S0 BASELINE_AUDITED` → `S1 DEMAND_REDUCED` jelölt
átmenet fizikai rétege. A cél a hőigény- és csúcsterhelés-változás külön
kezelése, majd a tervezési pont átadása B05 felé. B06 nem tartalmaz tarifát,
gáz- vagy villamosenergia-árat, támogatást, CAPEX-et vagy finanszírozást.

## Engine-szerződés

Az [`engine.py`](engine.py) csak explicit `EvidenceValue` bemeneteket fogyaszt.
A kötelező baseline a `baseline_annual_space_heat_kwh` és a
`baseline_peak_heat_load_kw`; hiányuk `Q`. A padlóterület, építési kor, fal,
tető, ablak, fűtés és hőleadó mezői lineage-dzsel továbbadhatók, de nem
rekonstruálnak teljes épületfizikát.

Az intervention külön éves és peak redukciós faktort kap. A komponálás
szekvenciális:

```text
annual_post = annual_before × (1 − annual_reduction_fraction)
peak_post   = peak_before   × (1 − peak_reduction_fraction)
```

Így a későbbi beavatkozás az előző post-state-re hat, és nem adódik össze
naivan ugyanarra a baseline-ra. A két faktor nem keverhető össze.

## Állapot- és downstream-kapu

Az eredmény `S1_CANDIDATE`, amíg a beavatkozás completion-evidence-e nem
`OBS` és nincs completion source. Az engine soha nem emel automatikusan
`S1_DEMAND_REDUCED` állapotra. A B05 handoff csak design-point hőigényt,
DHW-t és supply-temperature jelöltet ad; órás `HourlyDemand` profil külön,
explicit upstream contract marad.

Envelope-intervention nem változtatja meg automatikusan a supply temperature-t.
Emitter-intervention csak explicit `supply_temperature_after_c` értékkel
adhat át új hőfokot. A DHW mezők változatlanok maradnak.

A számszerű beavatkozási faktorok jelenleg csak `SCN` tesztfixture-ben
használhatók; a kanonikus katalógus valódi beavatkozási hatásai `Q`-k.

## P3 tervezési csúcshőterhelés

A [`design_load.py`](design_load.py) külön, közvetlen fizikai útvonalat ad a
P1 éves/faktoros motor mellett. A számítás kizárólag explicit adatokból készül:

```text
H_trans = Σ(U_i × A_i × correction_i)
H_vent  = c_air × explicit_airflow × (1 − heat_recovery_efficiency)
Q_design = (H_trans + H_vent + H_thermal_bridge) × (T_indoor − T_outdoor)
```

`U` W/m²K, `A` m², a hőátadási tényezők W/K, a hőterhelés kW. A levegő
térfogatárama csak explicit ACH × térfogatból vagy explicit m³/h-ból jöhet;
rejtett ACH, nulla hőhíd, alapterületből visszakövetkeztetett geometria,
éves energia és telepített kazán/hőszivattyú-kapacitás tiltott. Hiányzó
tervezési hőmérséklet, geometria, U-érték, szellőzési adat vagy hőhídmódszer
`Q`.

A before/after útvonal a baseline és post állapotot külön számolja újra, ezért
a peak-csökkenés közvetlen fizikai különbség, nem a P2 éves százalékos hatásának
átvétele. A `data/processed/retrofit_peak_design_evidence.csv` egyetlen,
átlátható `SCN` fixture-t tartalmaz; ez nem országos vagy magyar household
kalibráció.

Az emitter/supply-temperature segédút csak nominális hőleadó-teljesítmény,
névleges és jelölt előremenő/visszatérő, helyiséghőmérséklet és kitevő explicit
bizonyságával számol. Nincs automatikus W35/W45/W55 váltás. A jelenlegi
P3 önmagában még nem adott numerikus supply-hőfokot; P4 egy gyártói módszerrel
és SCN fixture-rel nyitja a technikai gate-et, miközben a household-level
eredmény és a valós kalibráció továbbra is `Q`.

## P4 emitter és B05 design-point bridge

A P4 egyetlen, forrásolt hidronikus panelradiátor-útvonalat nyit meg: PURMO
Plan Compact FC type 33, 600 × 3000 mm, gyártói névleges `6.927 kW` outputtal
`75/65/20 °C` feltételen és `n = 1.3417` kitevővel. A gyártói módszer szerint:

```text
Q = quantity × Q_nominal × (ΔT_mean / ΔT_nominal)^n
```

ahol `c = (T_return − T_room) / (T_flow − T_room)`: `c < 0.7` esetén
logaritmikus, egyébként aritmetikai mean-water delta-T kerül felhasználásra.
Az előremenő, visszatérő és helyiséghőmérséklet minden jelölt pontban explicit;
5/10/20 K visszatérő-különbség nem rejtett alapértelmezés.

A `data/processed/emitter_supply_temperature_results.csv` három SCN esetet
mutat: ugyanazzal a hat darabos explicit emitter-inventoryval a P3 baseline
6.165 kW-hoz 44.8 °C, a post-envelope 4.665 kW-hoz 43.0 °C szükséges; nyolc
explicit egység emitter-upgrade mellett ugyanaz a post-load 41.8 °C-ra csökken.
Ezek nem magyar household-observationök és nem állományi arányok.

A `build_b05_design_point_bridge` a meglévő B05 `PerformanceMap.evaluate`
útvonalát hívja meg. Nem hoz létre új interpolációt és nem kerekít W35/W45/W55
bandára. A fixture B05 oldalon `Tout=-10 °C`, `Tsupply=43.0 °C`,
`space_heating_required_kw=4.665` és `DHW=0` mellett explicit
`SCN / CAPACITY_SHORTFALL` eredményt ad; a capacity shortfall külön mező,
nem rejtett termékválasztás.
