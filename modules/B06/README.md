# B06 – Energetikai korszerűsítés

Állapot: **IN_PROGRESS – P1 fizikai szerződés és fail-closed engine**

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
