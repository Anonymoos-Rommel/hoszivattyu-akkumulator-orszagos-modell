# B01 – Programterjedelem és penetráció

## Cél

Éves telepítési és kumulált állománypálya előállítása országos és területi bontásban.

## Bemeneti szerződés

- célháztartások száma (`VAR-B01-TARGET-HOUSEHOLDS`);
- programhorizont (`VAR-B01-HORIZON-YEARS`);
- felfutási profil (`VAR-B01-RAMP-PROFILE`);
- területi felbontás (`VAR-B01-REGIONAL-RESOLUTION`);
- B02 technikailag alkalmas állománykorlátja;
- később B18 éves kivitelezési kapacitása.

## Kimeneti szerződés

- éves új telepítések, `household/year`;
- év végi kumulált állomány, `household`;
- régiónkénti éves és kumulált állomány;
- kielégítetlen szakpolitikai cél kapacitáskorlát esetén.

## Invariánsok

- a kumulált állomány nem csökkenhet;
- nem haladhatja meg sem a szakpolitikai célt, sem a B02 alkalmas állományát;
- az országos érték a területi értékek összege;
- minden pálya ugyanazon kezdő- és záródefinícióval hasonlítható össze.

## Állapot

`IN_PROGRESS` – a paraméterek és kérdések regisztrálva, de célállomány és felfutási képletek még nincsenek validálva.
