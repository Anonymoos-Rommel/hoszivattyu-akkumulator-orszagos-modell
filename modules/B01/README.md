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

## Állapot

`IN_PROGRESS` – a V1.2 állapot- és portfólió-szerződés vázolva, de célállomány, objektívfüggvény, hard minimumok és éves kapacitáspályák még nincsenek validálva.
