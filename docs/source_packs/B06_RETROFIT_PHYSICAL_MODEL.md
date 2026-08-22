# B06-P1 – Retrofit fizikai / demand-reduction szerződés

Állapot: **P1 fizikai contract és executable skeleton; országos retrofit-hatás Q**  
Lekérés: **2026-08-22**

## Források

- [KSH – A magyar lakásállomány primerenergia-igényének becslése](https://www.ksh.hu/s/kiserleti-statisztika/kiadvanyok/a-magyar-lakasallomany-primerenergia-igenyenek-becslese/) — `SRC-B06-KSH-ENERGY-BASELINE-2025`, P1/DER. B02-ból átvett, modellezett baseline-kontextus; nem household before/after retrofit mérés.
- [9/2023. (V. 25.) ÉKM rendelet](https://njt.hu/jogszabaly/2023-9-20-8X) — `SRC-B06-HU-ENERGY-RULES-2023`, P1/POL. Számítási módszertani jogforrás; a referencia 55/45 °C nem megfigyelt épületérték.
- [Hosszú Távú Felújítási Stratégia](https://energy.ec.europa.eu/system/files/2021-08/hu_2020_ltrs_en_0.pdf) — `SRC-B06-HU-LTRS-2021`, P1/POL. Alacsonyabb hőfoklépcső és korszerű hőleadó kapcsolatának szakpolitikai/módszertani kontextusa; nem ad országos retrofit-hatásfelületet.

## P1 fizikai módszer

B06-P1 nem állít fel nem bizonyított U-értékeket. A futtatható contract explicit,
külön éves és peak redukciós faktorokat fogyaszt, és szekvenciálisan alkalmazza
azokat a jelenlegi post-state-re:

```text
Q_annual,i+1 = Q_annual,i × (1 − f_annual,i)
Q_peak,i+1   = Q_peak,i   × (1 − f_peak,i)
```

Ez `SCN` fixture-ben demonstrálja a mechanikát. Valós intervention esetén a
faktorok source-native before/after mérésből, kalibrált számításból vagy külön
jóváhagyott archetype-methodból érkezhetnek; addig `Q`.

Emitter-intervention explicit supply-temperature after értéket adhat. Envelope
intervention önmagában nem jogosít fel W35/W45/W55 átállításra. DHW külön marad.

## B02 → B06 → B05

B02 adhat archetype/baseline jelöltet, de a külön projekciók és a Q mezők nem
keresztszorzódnak és nem válnak OBS-é. B06 hiányzó baseline vagy applicability
esetén fail-closed `Q`-t ad.

B05 felé a P1 handoff egy design-point szerződés: `space_heating_required_kw`
(post-retrofit peak), `required_supply_temperature_c` és külön `dhw_required_kw`.
Órás `HourlyDemand` idősor csak explicit időbeli demand-profile szeletben
képezhető; B06-P1 nem inventál ilyen profilt.

## S1 szemantika

Az intervention megléte vagy katalógusba vétele nem teljesíti az S1 kaput. Az
engine csak `S1_CANDIDATE` állapotot ad, amíg nincs OBS completion evidence és
source. A hiányzó adat nem jelent „retrofit nem szükséges” állapotot.
