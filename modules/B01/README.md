# B01 – Programterjedelem és penetráció

## Cél

Éves háztartási állapotállomány és országos projektportfólió-pálya előállítása országos és területi bontásban. A modul nem tekinti a programot egyszeri, azonos csomagú telepítési kampánynak.

## Bemeneti szerződés

- célháztartások száma (`VAR-B01-TARGET-HOUSEHOLDS`);
- programhorizont (`VAR-B01-HORIZON-YEARS`);
- felfutási profil (`VAR-B01-RAMP-PROFILE`);
- területi felbontás (`VAR-B01-REGIONAL-RESOLUTION`);
- B02 technikailag alkalmas állománykorlátja;
- később B18 éves kivitelezési kapacitása.
- háztartási állapotgép és az előző fázis bizonyítéka;
- beavatkozási katalógus és prioritási komponensek;
- éves közpénz-, társadalmi minimum-, hálózati- és regionális korlátok.

## Kimeneti szerződés

- éves új telepítések, `household/year`;
- év végi kumulált állomány, `household`;
- éves S0–S5 állapotállomány és fázisátmeneti darabszám;
- jelölt és kiválasztott beavatkozások, várakozási idő és kötő korlát;
- minden kiválasztáshoz „miért most / miért itt / mi hiányzik” magyarázat;
- régiónkénti éves és kumulált állomány;
- kielégítetlen szakpolitikai cél kapacitáskorlát esetén.

## Invariánsok

- a kumulált állomány nem csökkenhet;
- nem haladhatja meg sem a szakpolitikai célt, sem a B02 alkalmas állományát;
- az országos érték a területi értékek összege;
- minden pálya ugyanazon kezdő- és záródefinícióval hasonlítható össze.
- az állapotátmenet csak bizonyított kapu után haladhat előre;
- egyetlen éves kiválasztási súly vagy hard minimum sem lehet rejtett konstans;
- az országos portfólió kiválasztott darabszáma nem haladhatja meg az éves pénz-, FTE-, beszállítói-, engedélyezési- vagy hálózati korlátot.

## Executable B01-P1 contract

`registry/household_state_model.json` az egyetlen canonical state-record,
transition-, policy- és capacity-contract. A `modules/B01/engine.py` ezt a
contractot tölti be; nem tart fenn második állapotgépet és nem ad rejtett
országos optimumot.

- `HouseholdStateRecord` csak explicit state-as-of, owner, next gate,
  eligibility és transition evidence mellett értékelhető.
- `OBS`/`DER` gate evidence nélkül az átmenet `BLOCKED/Q`; `ASS`, `SCN` és
  `Q` nem teljesíthet egy observed household transitiont.
- A meglévő hőszivattyú-jelző, fogyasztás, épületkor, tarifa vagy archetípus-
  becslés önmagában nem emel állapotot.
- A kiléptetett állapot csak monotónusan változhat; a kihagyás explicit,
  már teljesült exit-gate evidence nélkül tiltott.
- A candidate intervention a state predecessorhez, gate evidence-hez,
  kilenc V1.2 komponenshez és explicit resource-needs mezőkhöz kötött.
- MCDA, lexikografikus és capacity-limited ordering csak teljes, explicit
  `POL`/`SCN`/`DER`/`OBS` policy-paraméterekkel fut; hiányzó érték nem nulla.
- A state-stock aggregáció konzervál, régiós összeget képez, és csak `SCN`
  outputot ad. A bounded fixture nem országos eligible-stock vagy rollout
  eredmény.

Bounded fixture: `data/fixtures/b01_state_stock_scn.json`.

## Executable B01-P2 national rollout pathway

`modules/B01/national_rollout_pathway.py` a nemzeti rollout matematikát teszi
gépileg végrehajthatóvá, de **nem tart fenn fix országos programme targetet**.

A korábbi `2 000 000` érték csak a kezdeti, 2026. augusztusi munkahipotézis;
nem current baseline és nem programme ceiling.

A programme target explicit `POL`/`SCN` input marad. A profil-contract:

- `LINEAR`;
- `LOGISTIC` — explicit midpoint és steepness nélkül fail-closed;
- `CAPACITY_LIMITED` — minden tervévre explicit kapacitásérték szükséges;
- horizon: 8–25 év;
- report points: 12 / 15 / 20 év.

Minden generált pathway `SCN`. A `NationalSelectionGate` csak akkor nyithat real
national selectiont, ha a B02 eligible stock, a valós éves capacity path és a
célháztartás jogi/műszaki definíciója is OBS/DER authorityval rendelkezik.

Registry: `registry/b01_national_rollout_policy_contract.csv`.

## B01-P3 exact non-district-heated population base

`modules/B01/non_district_population.py` kizárólag a commitolt
`WBL011_HEATING_FUEL` OBS projekció 7 682 celláját aggregálja. A KSH diszjunkt
fűtési mód-partíciójában `HEAT12` a távfűtés.

A kanonikus 2022-es fizikai bázis:

- lakott lakások: **4 008 541**;
- távfűtött lakott lakások: **618 724**;
- **nem távfűtött lakott lakások: 3 389 817**.

A P2-ben ideiglenesen használt **3 403 746** kerekített-share becslést P3
felülírja; az csak történeti auditérték marad. A P3-registry húsz
vármegye/Budapest DER sort és egy országos kontrollsort materializál:
`registry/b01_non_district_heated_population_2022.csv`.

A 3 389 817-es állomány programme-releváns fizikai kiinduló univerzum, de
**nem B02 technikai alkalmasság**, nem programme target és nem kiválasztott
háztartás. Utility customer count továbbra sem használható ház-/lakásszámként.

## Állapot

`IN_PROGRESS` – a B01-P1 state/portfolio contract és a B01-P2 rollout matematika
gépileg végrehajtható; B01-P3 az országos és vármegyei nem-távfűtött lakott
lakásbázist exact WBL011 cellákból rögzíti. A canonical programme target
jelenleg `Q`; a Q-B01-001 célháztartás-definíció, a B02 national eligible stock,
a valós éves capacity path, valamint a tényleges regional/settlement household
allocation továbbra sincs lezárva.
