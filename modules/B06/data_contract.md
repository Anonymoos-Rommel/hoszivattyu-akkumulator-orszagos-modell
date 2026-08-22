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
