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

## B02-P2 executable technical eligibility gate

`modules/B02/technical_eligibility_contract.py` végrehajtható, fail-closed
műszaki alkalmassági kaput ad a P1-I/P1-J/P1-K bizonyítékszerződésekhez.

A kanonikus szeparáció:

`PHYSICAL SCREENING SCOPE != TECHNICAL ELIGIBILITY != S2 TRANSITION READINESS != LEGAL/ECONOMIC PROGRAMME ELIGIBILITY`

A jelenlegi fizikai screening reference B01-P3-ból **3 389 817** nem
távfűtött lakott lakás (`DER_FROM_OBS_WBL011_CELLS`). Ez nem technikai
alkalmassági darabszám.

Egy real rekord technikai `ELIGIBLE` státuszához mind a négy komponens explicit
`PASS` döntése szükséges `OBS`/`DER` bizonyítékkal:

- `THERMAL_DISTRIBUTION`;
- `HYDRAULIC`;
- `ELECTRICAL`;
- `PERMIT`.

`FAIL` szintén csak explicit `OBS`/`DER` evidence mellett lehetséges. Hiányzó
bizonyíték `Q`, nem automatikus kizárás. `OUT_OF_SCOPE` külön marad a műszaki
`BLOCKED` döntéstől.

Az S2 állapotátmenet külön kapu: technikai `ELIGIBLE` mellett az S1
`demand_reduction_measured_or_not_required` predecessornek is explicit
`PASS` kell. Ezért `TECHNICALLY_ELIGIBLE != S2_TRANSITION_READY`.

A current repository gate továbbra is `Q`: hőleadó/hőfok, hidraulika, villamos
és permit bizonyíték hiányzik. A kanonikus gépi összegzés:
`registry/b02_technical_eligibility_gate.csv`.

## Állapot

`IN_PROGRESS` – a KSH V67 népszámlálási adatfolyamok három elkülönített,
közösen megfigyelt projekcióban materializáltak; a FAMILY_HOUSE/MULTI_DWELLING
épülettípusok, a modellezett primerenergia-eloszlás és a településtípusos `ASS`
épülettípus-proxy reprodukálható. B02-P2 a technikai eligibility/S2 admission
szabályt gépileg lezárja, de **nem** ad országos eligible-stock számot. A
projekciók és a proxy nem kapcsolhatók cellaszinten; `Q-B02-001` és
`Q-B02-004` nyitott.

Részletes szerződés: [`data_contract.md`](data_contract.md).
