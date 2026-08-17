# V1.2 portfólió- és lépcsőzetes átállási szerződés

Állapot: **CONTRACTED SKELETON – számszerű eredmény nélkül**

## Forrásalap és elsőbbség

Ez a nyilvános szerződés a projektben kezelt belső módszertani alap két verzióját követi:

- `Hoszivattyu_akkumulator_program_Codex_kutatasi_prompt_V1.2.docx`;
- `Hoszivattyu_akkumulator_program_javaslat_V1.1_munkapeldany.docx`.

A V1.2 a V1.1-et nem törli, hanem a 25. fejezet szerinti portfólió- és fázislogikával pontosítja. Eltérés esetén a V1.2 szerinti állapotgép, éves portfólió, baseline/incremental költségszétválasztás és fiskális korlát az irányadó. A DOCX-források szándékosan nem részei a nyilvános repónak.

Ez a fájl szerződés és ellenőrzési keret, nem eredményjelentés. Ismeretlen adatot nem pótol, és nem ad fel nem validált célértéket.

## Kanonikus program-egység

Az elemzés kanonikus egysége egy **fázisokon átvezetett háztartási beavatkozás egy országos projektportfólióban**, nem az egyszeri „hőszivattyú + akkumulátor telepítés”. Egy háztartás több év alatt, kapukon keresztül léphet előre, és egyes fázisok csak bizonyított feltétel mellett hagyhatók ki.

Az országos végrehajtó nem first-come-first-served listát kezel. Minden évben a rendelkezésre álló pénz, munkaerő, beszállítói kapacitás, hálózati headroom, engedélyezés és társadalmi minimumok mellett választja ki a következő legjobb, magyarázható beavatkozást.

## Háztartási állapotgép

Az állapotdefiníciók gépi formája a [`registry/household_state_model.json`](../../registry/household_state_model.json).

| Állapot | Jelentés | Kilépési kapu |
|---|---|---|
| `S0 BASELINE_AUDITED` | A háztartás és az épület bizonyíték-alapú kiinduló állapota rögzített. | auditált alapadat, jogosultság és hiányok listája |
| `S1 DEMAND_REDUCED` | A bizonyított keresletcsökkentő/envelope beavatkozás elkészült vagy igazoltan nem szükséges. | mért vagy dokumentált hőigény-változás |
| `S2 TECHNICALLY_READY` | A hőleadó, hidraulika, villamos és engedélyezési előfeltételek teljesülnek. | műszaki readiness és kizárási okok lezárva |
| `S3 HEAT_PUMP_ACTIVE` | A hőszivattyú működik, teljesítménye és fogyasztása mérhető. | üzembe helyezés, QA és mérési adat |
| `S4 FLEX_READY` | Akkumulátor/VPP/rugalmas vezérlés csak jogszerű és műszakilag bizonyított feltételekkel aktív. | mérési, tarifális és vezérlési kapu |
| `S5 TARGET_STATE` | A jóváhagyott célállapot, garancia, QA és életciklus-követés teljesül. | ex-post mérés és visszacsatolás |

Invariánsok:

- az állapot csak előre haladhat vagy dokumentáltan `BLOCKED` marad;
- hiányzó adat nem jelent „nem szükséges” állapotot;
- a meglévő hőszivattyú-jelző nem bizonyít `S2` vagy `S3` alkalmasságot;
- minden átmenethez bizonyíték, dátum, felelős és következő kapu tartozik;
- egy fázis kihagyása csak az adott kapu bizonyított teljesülése esetén engedélyezett.

## Éves portfólió-kiválasztás

Az `intervention_catalog.csv` egy beavatkozás jelöltjét, a `portfolio_schedule.csv` pedig egy évben kiválasztott jelöltet rögzít. A választásnak legalább az alábbi komponenseket kell láthatóan kezelnie:

`SOCIAL_NEED`, `ENERGY_WASTE`, `HOUSEHOLD_GAIN`, `PUBLIC_EFFICIENCY`, `FISCAL_EFFECT`, `SYSTEM_VALUE`, `ENV_HEALTH`, `READINESS`, `REGIONAL_EQUITY`.

A súlyok, hard minimumok és objective function nem lehetnek rejtett konstansok. Ezek `POL` vagy `SCN` paraméterek, és minden futásban visszaolvashatóan kell szerepelniük. Kötelező magyarázat: **miért most, miért itt, mi a hiányzó következő kapu**.

Minimum tesztelendő kiválasztási eljárások:

1. MCDA;
2. korlátos optimalizáció;
3. lexikografikus minimumok;
4. eltérő prioritási súlyok és társadalmi minimumok stressztesztje.

Egy módszer sem válhat alapértelmezetté addig, amíg az objektívfüggvény és a hard minimumok nyitott kérdése (`Q-B01-006`) nincs lezárva.

## Támogatás és háztartási cash-flow

A V1.2 strukturális hipotézise a következő, számszerű validációra váró szerkezet:

`Required_Public_Support = max(0; Eligible_CAPEX - Affordable_Household_Financing - Confirmed_External_Grant - Monetizable_System_Value)`

Ez nem jelent egységes támogatási százalékot. A támogatási igény archetipus, állapot, év és cash-flow-floor szerint változhat. A képlet egység-, jogosultság-, duplaelszámolás- és fiskális headroom-teszt nélkül nem használható eredményként.

## Baseline és inkrementális infrastruktúra

Az infrastruktúra állapotát külön kell kódolni:

`ÜZEMEL/KIVITELEZÉS`, `SZERZŐDÖTT`, `KÖLTSÉGVETÉSBEN/PROGRAMBAN ALLOKÁLT`, `NYITOTT PÁLYÁZAT`, `BEJELENTETT, NEM FINANSZÍROZOTT`, `PROGRAM ÁLTAL GYORSÍTOTT/NAGYOBBÍTOTT`.

A már meglévő, szerződött vagy hitelesen allokált elem a program nélküli ellenforgatókönyv része. A programhoz csak a bizonyítottan többlet- vagy gyorsítási költség rendelhető. Az `baseline_infrastructure.csv` és az `incremental_capex_attribution.csv` ugyanazt a költségelemet nem számolhatja el kétszer.

## Éves korlátok és kimenetek

Minden portfóliófuttatásnak külön kell kezelnie:

- éves közpénz- és cash-flow-floor korlátot;
- maximális adósságrátát és reinvesztálható pénzáramot;
- kivitelezői FTE-, beszállítói és engedélyezési kapacitást;
- DSO MW/MVA hálózati headroomot;
- regionális méltányossági minimumot;
- tanulási és readiness-változást az időben.

Elvárt kimenetek: éves állapotállomány S0–S5 szerint, várakozási idők, kiválasztott beavatkozások, régiós hőtérkép, hatás közpénzforintonként, baseline és inkrementális CAPEX, fiskális pálya/headroom, kötő korlát és a következő kapu.

## Visszamenőleges modulhatás

- **B01:** a telepítési pálya mellett éves intervention- és state-stock pályát kell adnia; a 2 milliós cél továbbra is `POL`, nem megfigyelés.
- **B02:** archetípus, hőigény és műszaki hiányok kimenete kell az `S0–S2` jelöltekhez; a jelenlegi B02-adat nem ad automatikus alkalmasságot.
- **B05/B06:** a hőszivattyú és retrofit fázis-, csúcs- és CAPEX-hatását kell átadnia.
- **B07/B08/B09:** rugalmasság, rendszerérték és hálózati korlát csak az adott állapothoz kötve számolható.
- **B10:** regionális readiness, baseline és inkrementális infrastruktúra-szétválasztás kötelező.
- **B12/B13/B14/B15:** archetipus- és fázisfüggő finanszírozási rés, éves cash-flow és fiskális headroom; B15 továbbra is csak B12+B13+B14 után indulhat.
- **B18:** az éves kivitelezési/szállítói kapacitás kemény korlát.
- **B20:** csak stabil B01–B19 szerződések után; a B20 feladata a már kanonikus állapot- és portfóliómodell megjelenítése, nem új igazságforrás létrehozása.

## Elfogadási kapu

A V1.2 szerinti modell akkor tekinthető elfogadhatónak, ha ugyanabból a kanonikus modellből reprodukálható:

1. háztartási állapotátmeneti pálya;
2. regionális readiness;
3. éves projektportfólió;
4. baseline/incremental infrastruktúra-költség;
5. cash-flow-floor;
6. éves és kumulált fiskális pálya.

Az önmagában közölt „X millió háztartás Y év alatt” nem elfogadási bizonyíték.

## Nyitott kérdések

A V1.2 rövid H/Q címkéi a nyilvános, globálisan egyedi azonosítókra lettek leképezve a [`registry/open_questions.csv`](../../registry/open_questions.csv) fájlban. A nyitott kérdés lezárásáig az érintett kimenet `Q`, `ASS` vagy `SCN` marad; `OBS` státusz nem örökölhető.
