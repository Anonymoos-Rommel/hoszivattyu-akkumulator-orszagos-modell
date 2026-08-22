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

## B06-P2 – retrofit-hatás evidence calibration (2026-08-22)

A P2 a P1 scalar contractját változatlanul hagyja, és a bizonyítékot külön
`data/processed/retrofit_effect_evidence.csv` táblában tartja. A tábla minden
esetben külön kezeli az éves hőigényt és a peak/design hőterhelést. Nincs
összevont `annual = peak` faktor, nincs nemzetközi adatból képzett magyar
univerzális érték, és a csomaghatás nem kerül szétosztásra önkényesen az egyes
komponensekre.

### Forrásaudit és státuszok

- A JRC Hvar-esettanulmány öt magánlakásnál közöl előtte/utána éves
  hőigényt (a csomag jellemzően homlokzat + nyílászáró, néhol gépészeti
  korszerűsítés). Ezek `MODELLED_BEFORE_AFTER`, kontextus-specifikus és
  `Q` státuszú sorok: a jelentés nem közöl külön design-peak sorozatot, és az
  időjárási normalizálás módja nem reprodukálható.
- A timișoarai öt blokk mért fűtési tartományt közöl (130,2–167,4-ről
  101,4–128,4 kWh/m²a-ra), valamint külön DHW-tartományokat. A forrás nem
  normalizálja a before/after éveket, ezért a tartomány nyers bizonyíték,
  nem engine-faktor.
- A CONCERTO összesítő HDD18/15 korrekciót használ, de a közölt fűtési érték
  explicit módon a DHW-előkészítést is tartalmazza. A 15–65%-os tartományt
  tartományként őrizzük; középérték nincs materializálva, a sor `Q`.
- Az Uddevalla-eset 16%-os mért csökkenést említ, de a 2017-es referenciaév
  és a 2020-as utóállapot klímája eltér; ez is csak nem kalibrált `Q` evidence.

Az időjárási és end-use szeparációs korlátokat a JRC renovációs mérési
útmutatója alapján kezeljük: HDD/occupancy/üzemviteli normalizálás és DHW-
leválasztás nélkül mért adat nem léphet `OBS` vagy engine-usable állapotba.

### Peak, supply temperature és S1 kapu

P2-ben nem került be hiteles, intervention-linked design-peak before/after
eset. A telepített kazán- vagy hőszivattyú-kapacitás nem helyettesíti a
tervezési hőterhelést. Emiatt `PEAK_LOAD_EFFECT` csak részleges marad, a B05
design-point handoff peak mezője valós esetben továbbra is `Q`, és sem az
envelope evidence, sem a katalógus nem emel automatikusan W35/W45/W55
readiness-t. Az ex-post completion bizonyítéka külön marad; a P2 evidence
önmagában nem nyitja az `S1_DEMAND_REDUCED` kaput.
