# B02 – Épületállomány és archetipizálás

## Cél

A magyar lakásállomány reprodukálható archetípusokra bontása, archetípusonkénti hőigény-, műszaki alkalmassági és retrofit-jellemzőkkel.

## V1.2 szerep

B02 adja az `S0` baseline-audit és az `S1`–`S2` jelölt fázisok archetípusos, energetikai és műszaki bemeneteit. Nem ad automatikus állapotátmenetet: a meglévő hőszivattyú-jelző, egy fűtési mód vagy egy proxy önmagában nem bizonyít műszaki readiness-t. A portfólió- és állapotkapuk közös szerződése: [`../../docs/methodology/v12_portfolio_transition_contract.md`](../../docs/methodology/v12_portfolio_transition_contract.md).

## Bemeneti szerződés

- KSH népszámlálási lakásjellemzők;
- energetikai tanúsítványhoz kapcsolt vagy modellből becsült energetikai jellemzők;
- épülettípus, építési időszak, alapterület, falazat, fűtési és hőleadó rendszer;
- területi azonosító és mintasúly vagy teljes állománydarabszám.
- az adott állapothoz szükséges readiness- és hiánymezők bizonyíték-státusszal;
- baseline/incremental infrastruktúra-hatásra való hivatkozás, ha a B02-kimenet hálózati vagy retrofit-fázist érint.

## Kimeneti szerződés

- archetípus-azonosító és definíció;
- lakásszám és bizonytalansági tartomány;
- fajlagos és teljes hőigény;
- hőszivattyús alkalmassági státusz;
- szükséges minimális retrofit-csomag vagy kizárási ok.
- archetípus × állapot jelölt- és hiánylista, `Q` státusszal, ha a kapuhoz bizonyíték hiányzik.

## Invariánsok

- a megfigyelt és becsült mezők nem keverhetők azonos státusszal;
- az archetípusok lefedettsége és maradék kategóriája kimutatandó;
- az aggregált darabszám visszaegyeztetendő a választott KSH-univerzummal;
- bizonytalan besorolás nem alakítható automatikusan alkalmas állománnyá.
- a B02 nem tölthet ki állapotot vagy portfóliórekordot hiányzó hőleadó-, hőmérséklet-, villamos vagy engedélyezési bizonyíték helyett.

## Állapot

`IN_PROGRESS` – a KSH V67 népszámlálási adatfolyamok három elkülönített, közösen megfigyelt projekcióban materializáltak; a FAMILY_HOUSE/MULTI_DWELLING épülettípusok, a modellezett primerenergia-eloszlás és a településtípusos `ASS` épülettípus-proxy reprodukálható. A projekciók és a proxy nem kapcsolhatók cellaszinten; a hőleadó és az alkalmassági szabály nincs lezárva.

Részletes szerződés: [`data_contract.md`](data_contract.md).
