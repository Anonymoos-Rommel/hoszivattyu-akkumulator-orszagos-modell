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

Az intervention megléte vagy katalógusba vétele nem teljesíti az S1 kaput.
P60 előtt az engine egy OBS completion-státusz + source jelenlétét vizsgálta;
ez túl gyenge volt és eltért a household state model OBS/DER szerződésétől.
P60-tól csak linked outcome gate nyithat S1-et: normalizált mért `OBS`,
azonos módszerű hiteles számítási `DER`, vagy explicit source-backed
`NOT_REQUIRED`. A hiányzó adat nem jelent „retrofit nem szükséges”
állapotot.

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
- P60 két magyar bounded kalibrációs útvonalat ad hozzá. A keszthelyi
  tanúsítvány-jellegű 220 -> 126-129 kWh/m2a pár `DER` kontextus marad és
  nem lesz engine-faktor; a 41-42,5%-os hőközponti és a 3600 -> 1600 m3
  családi házas mért eset normalizálási/end-use hiány miatt `Q` marad.

Az időjárási és end-use szeparációs korlátokat a JRC renovációs mérési
útmutatója alapján kezeljük: HDD/occupancy/üzemviteli normalizálás és DHW-
leválasztás nélkül a forrásmegfigyelés önmagában nem ad `OBS` outcome authority-t
vagy engine-usable állapotot. A forrásban ténylegesen megfigyelt adat ettől még
lehet saját kontextusában `OBS`; a target-effect authority külön `Q` marad.

### Peak, supply temperature és S1 kapu

P2-ben nem került be hiteles, intervention-linked design-peak before/after
eset. A telepített kazán- vagy hőszivattyú-kapacitás nem helyettesíti a
tervezési hőterhelést. Emiatt `PEAK_LOAD_EFFECT` csak részleges marad, a B05
design-point handoff peak mezője valós esetben továbbra is `Q`, és sem az
envelope evidence, sem a katalógus nem emel automatikusan W35/W45/W55
readiness-t. Az ex-post completion bizonyítéka külön marad; a P2 evidence
önmagában nem nyitja az `S1_DEMAND_REDUCED` kaput.


## V1-067 paired primary references

The two new family pointers reuse `registry/retrofit_sources.csv` and
`data/processed/retrofit_effect_evidence.csv`. Exact source provenance and typed
source facts are in `registry/b06_paired_retrofit_reference_manifest.json`.
Global `registry/sources.csv` mirrors the document identities. Original source
bytes are external-only, with hashes and actual retrieval timestamps retained.
There is no repository copy, source default, engine adapter or new physical
calculation. Existing legacy evidence is unchanged.

The CSV `status=Q` is target-effect authority. It does not make the qualified
source observations unknown. The manifest separately records SOLANOVA reported
observations as `OBS` and NEED attributed savings as `DER`. Applicability and
outcome authority remain `Q`; both handoffs have `usable_for_engine=NO`.

### SOLANOVA: historical Hungarian district-heated package

`SRC-B06-SOLANOVA-TREES-CASE` supplies the observed narrative; the TREES slides
and `SRC-B06-SOLANOVA-ACEEE-2006` are the same source family, not independent
corroboration. One selected 42-flat panel building includes ground-floor shops.
The 2005 package combines insulation, windows/shading, radiators/distribution,
controls, heat-recovery ventilation and solar-supported DHW. It is neither an
isolated fabric effect nor a heat-pump trial.

TREES p8 reports `OBS` 2100 GJ (two-pre-season average) and 394 GJ (2005-06),
with separately rounded publisher `DER` 81.3% saving. Its pp8-9 intensities
are `OBS` 213 to 39 kWh/m²a including shops. No reduction fraction is generated
from either pair. The separate p4 `DER` 210 kWh/m²a 2004-05 baseline is explicitly
mean-winter corrected; matching post correction is not documented. Do not join
that baseline to another pair or force earlier area figures into later rounded
intensities. Missing meter/loss, normalization, completeness and service
boundaries limit subsequent model calibration, not retention of these facts.

The p12 `OBS` 24.7°C February 2006 mean includes stairs and excludes ground
floor/cellar; it is not an annual setpoint. Comfort/use changed and no isolated
rebound factor is known. ACEEE's `SCN` 29.4 kWh/m²a and 87% are planned after
values. TREES' 78 MWh Sankey has unresolved measurement status (`Q`), with
possible plan lineage only an inference; none is admitted as observed outcome.
Historical cost amounts have differing tax/area bases and confer no current
CAPEX or payback authority. Filename dates and PDF creation dates are preserved
separately from unknown formal TREES publication dates.

### NEED: foreign whole-property meter-based matched estimates

`SRC-B06-DESNZ-NEED-HEADLINE-EW-2026` is the original 11 June 2026 release.
The estimates concern the first year after installation (Cover sheet A3);
persistent lifetime savings are not demonstrated. The gas periods are
mid-May 2022–23 before, mid-May 2023–24 installation,
and mid-May 2024–25 after (Annex D p12; Annex A p10). Xoserve's weather-corrected
annualised AQ is derived from meter readings; EPC supplies matching attributes,
not the energy baseline. The service is whole-property gas, not isolated space
heat, useful heat or kWh/m². Every inapplicable CSV numeric field is empty.

The manifest retains exact Table1/Table2 numeric cells with typed publisher
sample counts (`OBS`) and weighted mean/median savings (`DER`). Its Solar PV
row remains electricity context outside the fabric/heating handoff. Percentage
and kWh medians are separate estimators and cannot form one household's baseline
or before/after pair. Single and combination cohorts cannot be summed or
causally ranked. For orientation, the solid-wall cohort reports 2411 properties,
17.3% and 1857 kWh weighted median savings; those rounded displays do not
replace the exact cells or acquire Hungarian target authority. Notes B4 defines
Loft Insulation to include roof and room-in-roof insulation, including in
combination labels.

Annex D p16, Variations in estimated savings between years, states that a full
uncertainty assessment has not been completed: estimates are indicative rather
than precise. Exact XML decimal strings preserve source cells, not statistical
precision. Cover sheet A4 warns that methodological changes can prevent direct
comparison with previous releases; a later temporal comparison should use the
source-coherent Impact of Measures by year of installation: England and Wales
tables.

Selection excludes flats/rare types, missing attributes, implausible or suspected
imputed readings, specified smart-meter installation windows, and for insulation
post-1999 buildings. The source filters large annual changes, matches eligible
properties, trims both 2.5% tails of paired savings, reweights and averages 50
random matching/statistic runs. Source weights target eligible England/Wales
stock; they are neither Hungarian population nor owner planning weights. Hidden
measures, use/comfort changes and selection sensitivity remain. No per-measure
recruitment-to-final attrition funnel is supplied. Published Table3 quantiles
are averaged summaries of trimmed/reweighted matching runs, not estimator
confidence intervals or one raw cohort distribution.

Table3's signed change labels and Annex D's signed-change formula do not
reconcile literally. Only explicitly labelled positive savings are retained
as quantitative references; no raw sign repair or reconstruction occurs. The
Annex D p15 Year0 wording also differs from its dated p12 example. These narrow
ambiguities are preserved without blocking the clearly labelled savings.

### Remaining transfer work

B06-D03 is `RESEARCHING`, not accepted. The original acceptance contract is
unchanged. Manifest debt records distinguish normalized-effect, useful-heat,
target-transfer and raw-sign-reconstruction needs. Neither reference supplies
Hungarian weights/default savings, target-building applicability, current costs,
HP installed duty, household economics or national economics. Explicit
claim-matched calibration or defensible representative inference with uncertainty
is a valid next route. Private household bills, exhaustive census coverage,
exact cross-document denominator reconciliation and raw sign resolution are
not universal prerequisites for retaining these scoped references.
