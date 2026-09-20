# B06-P1 fizikai adat- és átadási szerződés

## Bemenetek

Kötelező:

- `archetype_id` és `baseline_state_id=S0`;
- éves baseline térfűtési igény (`kWh`);
- baseline tervezési/csúcshőigény (`kW`).

Opcionális, de státusszal és lineage-dzsel kezelendő:

- floor/heated floor area, building type, construction period;
- wall/roof/floor/window type és ismert felületek;
- baseline supply temperature;
- DHW éves és csúcshőigény;
- emitter, szellőzés/infiltráció, climate/station referencia.

Ezek hiánya nem pótolható floor area + építési kor + gázfogyasztás proxyból.

## Intervention

Minden interventionnek külön kell megadnia:

- `annual_reduction_fraction`;
- `peak_reduction_fraction`;
- `evidence_status` és `applicability_status`;
- opcionális `supply_temperature_after_c`;
- completion státusz és completion evidence.

Egy hiányzó faktor vagy Q applicability a teljes fizikai kimenetet `Q`-ra
zárja. Emitter-only változásnál a két redukciós faktor explicit `0.0`, a
supply-változás pedig külön mező.

## Kimenetek

Az engine külön adja:

- baseline/post annual space heat (`kWh`);
- baseline/post peak heat load (`kW`);
- éves és csúcshő-csökkenés abszolút és százalékos értéke;
- supply temperature before/after;
- változatlan DHW értékek;
- applicability, readiness gaps és `S1_CANDIDATE`/`S1_DEMAND_REDUCED` jelöltállapot;
- B05 design-point handoff.

`annual_heat_reduction_pct` nem használható `peak_heat_reduction_pct`
helyettesítőjeként.

## Evidence és scope

A KSH energetikai output baseline-modellként `DER`, az ÉKM-szabályozás
módszertani `POL`; egyik sem household-level before/after retrofit mérés.
Az intervention-katalógus ezért numerikus hatás nélkül, `Q` státusszal marad.
CAPEX csak későbbi szelet; hiánya nem blokkolja ezt a fizikai engine-t.

## P2 evidence materialization

Az intervention-specifikus audit a `data/processed/retrofit_effect_evidence.csv`
fájlban él. A sorok külön éves és peak mezőket, bizonyítékosztályt,
weather-normalization, DHW-szeparációs és applicability mezőket tartalmaznak.
Mért vagy modellezett éves before/after adat csak a saját kontextusában
érvényes. P60-tól a táblában lehet bounded `DER` kalibrációs sor is, de
`usable_for_engine=NO` marad, ha az applicability, komponens-attribúció vagy
design-peak evidence nem teljes. Mért adat időjárás-/üzemviteli normalizálás
nélkül nem emelhető `OBS` outcome authority-vá. Tartomány esetén a minimum és
maximum külön mező; középérték nem tölthető be.

## P3 design-load contract

A P3 canonical peak layer a `modules/B06/design_load.py` fizikai számítását és
a `data/processed/retrofit_peak_design_evidence.csv` lineage-t használja. A
baseline és post state nem faktorral módosul, hanem külön, explicit
geometriával/U-értékekkel/szellőzéssel újraszámolódik:

```text
H_trans = Σ(U_i × A_i × boundary_correction_i)
H_vent = air_volumetric_heat_capacity × airflow × (1 − heat_recovery)
Q_design = (H_trans + H_vent + H_thermal_bridge) × (T_i − T_o)
```

Minden komponensnél kötelező az U (W/m²K), a felület (m²), a határ és a
korrekció. A szellőzésnél kötelező a térfogat és pontosan egy explicit ACH vagy
m³/h légáram, továbbá a hővisszanyerés és a levegő térfogati hőkapacitása. A
tervezési külső hőmérséklet nem automatikus magyar országos érték: OBS
meteorológiai adat, POL szabályozási referencia és SCN stressz külön mező.
Hőhídmódszer, geometria, U, szellőzés vagy bármely tervezési hőmérséklet
hiánya `Q`; éves kWh, kazán-/hőszivattyú-kapacitás vagy full-load-hours proxy
nem input.

A supply-temperature számítás külön gate. Csak explicit emitter névleges
teljesítmény, névleges ΔT, hőmérséklet-kitevő, helyiséghőmérséklet és jelölt
flow/return pontok mellett ad eredményt. Automatikus W35/W45/W55 váltás vagy
rejtett 5/10/20 K visszatérő-különbség tiltott; az aktuális household-level
emitter evidence hiányában a household-level B05 design-point handoff `Q`;
P4 source-native SCN fixture-e ettől külön technikai method gate.

## P4 emitter contract és B05 bridge

A P4 canonical emitter evidence külön rétegben él. Egy emitter rekordnak meg
kell őriznie a gyártót, modellt/típust, méreteket, névleges outputot, a
névleges flow/return/room feltételt, a névleges ΔT-t, az `n` kitevőt és a
korrekciós módszer forrását. A hiányzó emittermodell, output, rating condition,
exponent, korrekciós módszer, return/delta-T szabály vagy room temperature `Q`.

Az egyetlen lezárt módszer a Purmo által közölt EN 442-alapú output correction:
aritmetikai mean-water delta-T, vagy `c < 0.7` esetén logaritmikus mean-water
delta-T. A nominal rating condition nem normalizálódik univerzális 75/65/20
feltételre; a kiválasztott rekordnál ez a konkrét source-native feltétel.

Az explicit emitter-egységek outputja összeadható csak a megadott inventory-
darabszám alapján. Más modell vagy méret outputja nem skálázható feltételezéssel.
Az eredmény numeric `required_supply_temperature_c`; a W35/W45/W55 csak utólagos
riport-label lehet, fizikai input nem.

A B05 bridge a P3 post design loadot, a számított supply-t, a design Toutot,
a külön DHW értéket és a meglévő B05 performance-map operating pointját adja
át. A B05 map kívüli pont `Q`, a mapon belüli, de elégtelen kapacitás pedig
explicit `CAPACITY_SHORTFALL`; egyik sem indít automatikus termékválasztást.

## P60 linked S1 demand-outcome contract

Az S0 -> S1 állapotátmenet nem országos stock-mezőt vár, hanem rekord- és
intervention-szintű completion outcome-ot.

A kanonikus gate: `modules/B06/s1_demand_outcome_gate.py`.

Elfogadott utak:

- `MEASURED_USAGE / OBS`: azonos metrika, egység és módszer szerinti
  before/after, dokumentált normalizálással és end-use scope-pal;
- `CERTIFIED_CALCULATION / DER`: azonos számítási módszerű, fázishoz kötött
  before/after számítás;
- `NOT_REQUIRED / OBS|DER`: kizárólag explicit szabály- és authority-ref
  mellett.

Hiányzó vagy inkompatibilis pár `Q`; pozitív megtakarítás hiánya vagy explicit
minimumküszöb el nem érése `BLOCKED`. A `RetrofitIntervention` puszta
completion-státusza és source ID-ja nem nyitja az S1 kaput.

A magyar MFB Otthonfelújítási Program pre/post HET logikája a
`CERTIFIED_CALCULATION / DER` út authority-ja. A program 30%-os minimuma
programfeltétel, nem univerzális fizikai retrofit-faktor.

## P61 baseline demand evidence

`baseline_annual_space_heat_kwh` és `baseline_peak_heat_load_kw` valós
`OBS/DER` státuszban csak `BaselineDemandEvidence` mellett használható.

Kötelező:

- ugyanaz a `record_id`;
- ugyanaz a `phase_id`;
- explicit annual és peak source refs;
- annual és peak módszer külön;
- reprodukálható repository binding.

Az annual érték lehet source-native total vagy explicit
`specific_annual × heated_floor_area` DER. A peak külön direct/design
evidence; éves energiából nem származtatható.

A P61 magyar bounded rekord:
`B06-P61-HU-ZALAVAR-2015`, `PRE_RETROFIT`,
source-native `207172 kWh/a DER` + source-native `132.35 kW DER`.
A rounded specific value × area visszaszámítás nem írhatja felül a source-native
éves totalt.

## P62 real intervention-effect contract

`RetrofitIntervention.evidence_status in {OBS, DER}` esetén az annual és peak
redukciós fraction nem lehet kézzel beadott, önálló szám. Kötelező a
`PeakEffectEvidence`:

- ugyanaz a record és intervention;
- külön before/after fázis;
- azonos calculation method;
- azonos design indoor/outdoor hőmérséklet;
- külön annual before/after és peak before/after;
- intervention-scope authority;
- DHW és space-heating boundary;
- before/after source refs és reprodukálható binding.

Az engine a fractionöket az evidence-párból újraszámolja és exact módon
összeveti a beadott intervention-faktorokkal. Mismatch vagy hiányzó evidence
`Q`.

A bounded P62 magyar kalibráció:

- annual: `207172 -> 36687 kWh/a`,
  fraction `0.8229152588187593`;
- peak: `132.35 -> 46.47 kW`,
  fraction `0.6488855307895731`.

A post state tervezett, ezért `DER`, nem realized completion `OBS`.
P60 S1-completion evidence ettől külön kapu.

