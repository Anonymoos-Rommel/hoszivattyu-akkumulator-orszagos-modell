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

## Állapot

`IN_PROGRESS` – a state-record, transition-gate, candidate, policy és éves
capacity skeleton gépileg ellenőrizhető bounded SCN fixture-en; a Q-B01-006
objective/hard-minimum döntés, a B02 national eligible stock, valamint a
valós országos capacity path továbbra sincs lezárva.
