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
érvényes; a P2-ben rögzített sorok jelenleg `Q` és `usable_for_engine=NO`, mert
nem áll rendelkezésre egyidejűleg reprodukálható időjárás-/üzemviteli
normalizálás, komponens-attribúció és intervention-linked design-peak evidence.
Tartomány esetén a minimum és maximum külön mező; középérték nem tölthető be.
