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

Az eredmény `S1_CANDIDATE`, amíg nincs P60 szerint ellenőrzött,
fázishoz és interventionhöz kötött S1 outcome. A gate `OBS` normalizált
mért before/after vagy `DER` azonos módszerű hiteles számítási before/after
párt fogad el; `NOT_REQUIRED` csak explicit authority-val lehetséges.
Puszta completion-státusz és source ID nem emel `S1_DEMAND_REDUCED`
állapotra. A B05 handoff csak design-point hőigényt, DHW-t és
supply-temperature jelöltet ad; órás `HourlyDemand` profil külön, explicit
upstream contract marad.

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

## P61 phase-linked baseline annual + peak gate

Valós `OBS/DER` B06 baseline esetén az éves térfűtési igény és a design-peak
többé nem adható be két független számpárként. A
[`baseline_demand_gate.py`](baseline_demand_gate.py) megköveteli ugyanazt a
rekordot és ugyanazt a pre-intervention fázist, külön annual és peak
evidence-dzsel.

Tiltott útvonalak:

- annual kWh -> peak kW visszaszámítás;
- telepített kazán/hőszivattyú teljesítménye -> design peak;
- full-load-hours proxy.

P61 bounded magyar kalibrációja egy 19 lakásos társasház 2015-ös, explicit
`Felújítás előtti állapot` számítása. P62 source-precedence javítása után a
kanonikus éves nettó fűtési igény a dokumentum source-native
`QF,1=207172 kWh/a DER`; `qF=145.9 kWh/m2a` és `AN=1419.63 m2` context.
A forrás ettől függetlenül közvetlenül `132.35 kW` design hőszükségletet ad. Ez nem országos arány és nem 2026-os
állománybecslés.

## P62 intervention-linked annual + design-peak calibration

Valós `OBS/DER` intervention numerikus annual és peak redukciós faktorai csak
[`peak_effect_gate.py`](peak_effect_gate.py) által elfogadott linked
before/after evidence mellett használhatók. A két faktor külön evidence-ből
származik; egyik sem helyettesítheti a másikat.

A bounded magyar Zalavár u. 4. projekt ugyanazon 19 lakásos épületre, azonos
`KESZ ZBR EH 09-3` módszerrel és azonos `20 / -13 C` design feltételekkel:

```text
annual net heat: 207172 -> 36687 kWh/a
annual reduction: 82.2915%

design peak:     132.35 -> 46.47 kW
peak reduction:  64.8886%
```

A POST dokumentum `Felújítás utáni állapot (tervezett)`, ezért
`PLANNED_DESIGN / DER`: fizikai kalibrációra használható, de nem completion
`OBS`, és önmagában nem nyitja az S1 kaput.

Az engine valós `OBS/DER` intervention esetén a megadott annual/peak
fractionöket visszaellenőrzi a P62 evidence-ből számított külön értékekkel.

## P63 transferable physical effect surface

A B06-P63 a retrofit-hatást nem fix százalékként, hanem explicit fizikai
before/after állapotokból számítja újra.

Az annual dimenzió a hatályos magyar havi nettó térfűtési hőmérleg, a peak
dimenzió pedig ettől független design `H × ΔT` számítás. A két output külön
marad.

A P63 surface csak explicit applicability domainben használható:

- building type;
- construction period;
- before/after state;
- azonos climate és service condition;
- explicit fizikai heat-loss/gain inputok;
- source refs;
- reprodukálható binding.

A Hungarian TABULA type/state példák a domain alakját validálják, de
`usable_for_engine=NO`: nem household OBS, nem reprezentatív országos
eloszlás, és nem szolgáltat fix megtakarítási százalékot.

Runtime-ban valós `OBS/DER` intervention numerikus hatásához pontosan egy
authority engedett: P62 linked pair **vagy** P63 physical surface. P63 esetén
a széles fizikai change-keyek (`TRANSMISSION`, `VENTILATION`, stb.) nem
számolhatók el kétszer; overlap esetén a beavatkozásokat közös fizikai
state-transitionként kell újraszámolni.

