# B02 – Épületállomány és archetipizálás

## Cél

A magyar lakásállomány reprodukálható archetípusokra bontása, archetípusonkénti hőigény-, műszaki alkalmassági és retrofit-jellemzőkkel.

## V1.2 szerep

B02 adja az `S0` baseline-audit és az `S1`–`S2` jelölt fázisok archetípusos, energetikai és műszaki bemeneteit. Nem ad automatikus állapotátmenetet: a meglévő hőszivattyú-jelző, egy fűtési mód vagy egy proxy önmagában nem bizonyít műszaki readiness-t. A portfólió- és állapotkapuk közös szerződése: [`../../docs/methodology/v12_portfolio_transition_contract.md`](../../docs/methodology/v12_portfolio_transition_contract.md).

## Bemeneti szerződés

- KSH népszámlálási lakásjellemzők;
- energetikai tanúsítványhoz kapcsolt vagy modellből becsült energetikai jellemzők;
- épülettípus, építési időszak, alapterület, falazat, fűtési és hőleadó rendszer;
- területi azonosító és mintasúly vagy teljes állománydarabszám;
- az adott állapothoz szükséges readiness- és hiánymezők bizonyíték-státusszal;
- baseline/incremental infrastruktúra-hatásra való hivatkozás, ha a B02-kimenet hálózati vagy retrofit-fázist érint.

## Kimeneti szerződés

- archetípus-azonosító és definíció;
- lakásszám és bizonytalansági tartomány;
- fajlagos és teljes hőigény;
- hőszivattyús alkalmassági státusz;
- szükséges minimális retrofit-csomag vagy kizárási ok;
- archetípus × állapot jelölt- és hiánylista, `Q` státusszal, ha a kapuhoz bizonyíték hiányzik.

## Invariánsok

- a megfigyelt és becsült mezők nem keverhetők azonos státusszal;
- az archetípusok lefedettsége és maradék kategóriája kimutatandó;
- az aggregált darabszám visszaegyeztetendő a választott KSH-univerzummal;
- bizonytalan besorolás nem alakítható automatikusan alkalmas állománnyá;
- a B02 nem tölthet ki állapotot vagy portfóliórekordot hiányzó hőleadó-, hőmérséklet-, villamos vagy engedélyezési bizonyíték helyett.

## B02-P2 executable technical eligibility gate

`modules/B02/technical_eligibility_contract.py` végrehajtható, fail-closed műszaki alkalmassági kaput ad a P1-I/P1-J/P1-K bizonyítékszerződésekhez.

A kanonikus szeparáció:

`PHYSICAL SCREENING SCOPE != TECHNICAL ELIGIBILITY != S2 TRANSITION READINESS != LEGAL/ECONOMIC PROGRAMME ELIGIBILITY`

A jelenlegi fizikai screening reference B01-P3-ból **3 389 817** nem távfűtött lakott lakás (`DER_FROM_OBS_WBL011_CELLS`). Ez nem technikai alkalmassági darabszám.

Egy real rekord technikai `ELIGIBLE` státuszához mind a négy komponens explicit `PASS` döntése szükséges `OBS`/`DER` bizonyítékkal:

- `THERMAL_DISTRIBUTION`;
- `HYDRAULIC`;
- `ELECTRICAL`;
- `PERMIT`.

`FAIL` szintén csak explicit `OBS`/`DER` evidence mellett lehetséges. Hiányzó bizonyíték `Q`, nem automatikus kizárás. `OUT_OF_SCOPE` külön marad a műszaki `BLOCKED` döntéstől.

Az S2 állapotátmenet külön kapu: technikai `ELIGIBLE` mellett az S1 `demand_reduction_measured_or_not_required` predecessornek is explicit `PASS` kell. Ezért `TECHNICALLY_ELIGIBLE != S2_TRANSITION_READY`.

A current repository gate továbbra is `Q`: hőleadó/hőfok, hidraulika, villamos és permit bizonyíték hiányzik. A kanonikus gépi összegzés: `registry/b02_technical_eligibility_gate.csv`.

## B02-P3 eligibility layer harmonization

A régi `VAR-B02-ELIGIBLE-DWELLINGS` jogi + műszaki + gazdasági feltételeket összemosó történeti változó. B02-P3 ezt **nem definiálja át hallgatólagosan**: numerikusan blank, státusza `Q`, és csak `DEPRECATED_UMBRELLA_ONLY` kompatibilitási jelölést kap az új rétegszerződésben.

Az új gépi authority: [`../../registry/b02_eligibility_layer_contract.csv`](../../registry/b02_eligibility_layer_contract.csv). Külön kezeli:

1. `PHYSICAL_SCREENING_SCOPE`;
2. `TECHNICAL_ELIGIBILITY`;
3. `S2_TRANSITION_READINESS`;
4. `LEGAL_PROGRAMME_ELIGIBILITY`;
5. `ECONOMIC_ELIGIBILITY`;
6. `FINAL_PROGRAMME_ELIGIBILITY`.

A részrétegek között nincs automatikus státuszöröklés. Különösen: fizikai population count nem eligibility; technikai PASS nem jogi vagy gazdasági PASS; technikai PASS önmagában nem S2; legacy umbrella változó nem claim-specific authority.

## B02-P4 technical component authority handoff

A P2 generikus eligibility-engine fölött a `modules/B02/technical_component_authority.py` ellenőrzi a real PASS/FAIL evidence producer-modulját. A machine-readable authority registry: [`../../registry/b02_technical_component_authority.csv`](../../registry/b02_technical_component_authority.csv).

Kanonikus producer-határ:

- `THERMAL_DISTRIBUTION` → B02;
- `HYDRAULIC` → B02 vagy B06;
- `ELECTRICAL` → B08 vagy B10;
- `PERMIT` → B10 vagy B18.

B02 ezért nem önigazolhat villamos vagy permit readiness-t. `Q` komponenshez producer-authority sem állítható. A mapping repository-architektúra, nem OBS/DER evidence, ezért a jelenlegi national eligible count változatlanul blank/Q.

## B02-P5 TABULA / EPISCOPE thermal-distribution boundary

A `registry/b02_tabula_thermal_distribution_audit.csv` az alternatív magyar TABULA/EPISCOPE országos tipológiai forrást fail-closed módon auditálja.

Kanonikus határ:

`HEAT GENERATION DATA != HEAT DISTRIBUTION DATA != CURRENT EMITTER EVIDENCE != DESIGN TEMPERATURE EVIDENCE != HYDRAULIC READINESS`

A magyar EPISCOPE country-page szerint az `S-2.1` heat-supply centralisation és az `S-2.3` heat generation elérhető, de az `S-2.2 Heat distribution and storage of space heating systems` nincs elérhetőként jelölve. A BME tipológiabrosúra típusra jellemző modell-gépészeti megoldásokat használ; ez nem household-level emitter OBS. A brosúrában látható radiátorszerű sematikus ábra sem emelhető current-emitter evidence-dzsé, és kazántípusból nem inferálható hőfoklépcső.

Ezért a TABULA-vonal context-only: `GAP-B02-S2-HEAT-EMITTER`, `GAP-B02-S2-DESIGN-TEMPERATURE` és `GAP-B02-S2-HYDRAULIC` továbbra is `Q`. A fő evidence-út változatlanul az OÉNY pilot/adatkérés, sikertelensége esetén külön reprezentatív műszaki felmérés.

A brosúra public-repository reuse-ja attribution mellett tisztázott; a history manifest az `evidence/history/SRC-B02-TABULA-HU-TYPOLOGY-BROCHURE-2014/manifest.csv`. A PDF byte-snapshotja jelenleg `PENDING_BINARY_ACQUISITION`, mert hash és exact byte copy nélkül nem archiválunk.

## Állapot

`IN_PROGRESS` – a KSH V67 népszámlálási adatfolyamok három elkülönített, közösen megfigyelt projekcióban materializáltak; a FAMILY_HOUSE/MULTI_DWELLING épülettípusok, a modellezett primerenergia-eloszlás és a településtípusos `ASS` épülettípus-proxy reprodukálható. B02-P2 a technikai eligibility/S2 admission szabályt gépileg lezárja, B02-P3 claim-specifikus eligibility-rétegekre bontja a korábbi umbrella fogalmat, B02-P4 a négy technikai komponens producer-authority handoffját fail-closed rögzíti, B02-P5 pedig lezárja a TABULA/EPISCOPE alternatív forráság félreértelmezési kockázatát, de **egyik sem ad országos eligible-stock számot**. `Q-B02-001` és `Q-B02-004` nyitott.

Részletes szerződés: [`data_contract.md`](data_contract.md).
