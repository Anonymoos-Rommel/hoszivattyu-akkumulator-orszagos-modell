# B02 – Épületállomány és archetipizálás

## Cél

A magyar lakásállomány reprodukálható archetípusokra bontása, archetípusonkénti hőigény-, műszaki alkalmassági és retrofit-jellemzőkkel.

## Bemeneti szerződés

- KSH népszámlálási lakásjellemzők;
- energetikai tanúsítványhoz kapcsolt vagy modellből becsült energetikai jellemzők;
- épülettípus, építési időszak, alapterület, falazat, fűtési és hőleadó rendszer;
- területi azonosító és mintasúly vagy teljes állománydarabszám.

## Kimeneti szerződés

- archetípus-azonosító és definíció;
- lakásszám és bizonytalansági tartomány;
- fajlagos és teljes hőigény;
- hőszivattyús alkalmassági státusz;
- szükséges minimális retrofit-csomag vagy kizárási ok.

## Invariánsok

- a megfigyelt és becsült mezők nem keverhetők azonos státusszal;
- az archetípusok lefedettsége és maradék kategóriája kimutatandó;
- az aggregált darabszám visszaegyeztetendő a választott KSH-univerzummal;
- bizonytalan besorolás nem alakítható automatikusan alkalmas állománnyá.

## Állapot

`IN_PROGRESS` – a KSH V67 népszámlálási adatfolyamok, a FAMILY_HOUSE/MULTI_DWELLING épülettípusok, a modellezett primerenergia-eloszlás és a településtípusos `ASS` épülettípus-proxy reprodukálható. A proxy nem közvetlen cellajoin; a hőleadó és az alkalmassági szabály nincs lezárva.

Részletes szerződés: [`data_contract.md`](data_contract.md).
