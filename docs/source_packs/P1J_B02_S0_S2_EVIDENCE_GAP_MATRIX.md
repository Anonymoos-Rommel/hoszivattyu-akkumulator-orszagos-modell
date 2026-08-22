# P1-J: B02 S0-S2 Evidence Gap Matrix

Állapot: READ-ONLY EVIDENCE MAP - nincs országos alkalmassági következtetés

Ellenőrzési alap: a jelenlegi repóban rögzített KSH/WBL és OÉNY-forráscsomagok, valamint a V1.2 S0-S2 readiness-kapui. Külső adatigénylés nem történt, új nyers adat nem került be.

## Döntési szabály

Egy mező akkor fed le egy readiness-követelményt, ha a forrás ugyanazon objektumra, azonos grainben, explicit módon és visszakereshető lineage-dzsel adja a szükséges értéket. A jogszabályi vagy referenciaérték önmagában nem az adott épület megfigyelése. A külön KSH/WBL margók nem kapcsolhatók össze keresztbeszorzással.

A részletes, gépi sorok a registry/b02_s0_s2_evidence_gap_matrix.csv fájlban vannak.

## Összesített döntés

| Kapu | Jelenlegi lefedés | Döntés |
|---|---|---|
| S0 BASELINE_AUDITED | részleges: KSH/WBL adatok és KSH energetikai modell-bázis rendelkezésre áll, de a teljes közös archetípus-grain és jogi/műszaki programjogosultság hiányzik | PARTIAL |
| S1 DEMAND_REDUCED | nincs fázishoz kötött előtte/utána beavatkozási vagy mérési adat | BLOCKED_DATA_GAP |
| S2 TECHNICALLY_READY | OÉNY hivatalos sémája nem tartalmaz dedikált jelenlegi hőleadó- és hőfokmezőt; hidraulikai, villamos és engedélyezési readiness-forrás nincs azonosítva | BLOCKED_DATA_GAP |

## Mezőnkénti bizonyítás

### S0 - baseline-audit

**Lefedhető a meglévő forrásokból:** területi kulcs, lakottság, építési időszak, falazat, alapterület-kategória, komfortosság, fűtési mód, tüzelőanyag és meglévő hőszivattyú-jelző. Ezek KSH/WBL OBS mezők, de külön projekciókban. A KSH 2025 energetikai közlése épülettípus × építési időszak szerinti MODELLED/DER primerenergia-bázist ad. A 2015-ös épülettípus-proxy csak ASS.

**Nem fedhető le:** teljes WBL × épülettípus × energia × hőleadó közös rekord; jogi programjogosultság; műszaki readiness; a hőszivattyú meglétéből következő alkalmasság. Az S0 ezért csak auditált jelöltállapot, nem támogatási vagy telepítési jogosultság.

### S1 - keresletcsökkentés

A KSH energetikai modellje baseline-energiaigényre használható, de nem tartalmaz programfázishoz kötött beavatkozási azonosítót, befejezési időt, előtte/utána azonos definíciójú mérési párt vagy igazolt „nem szükséges” döntést. Az S1-kapu Q, és minden jelölt BLOCKED_DATA_GAP, amíg ilyen bizonyíték nincs.

### S2 - műszaki readiness

Az OÉNY v3.0.14801 szótár/validációs szabályok/teljes JSON-minta alapján:

- a jelenlegi hőleadó típusára nincs dedikált strukturált mező;
- a tervezési előremenő/visszatérő hőmérsékletre nincs dedikált mezőpár;
- a kötelező hőleadófotó és számítási PDF potenciális dokumentumbizonyíték, de nem országosan aggregált adat;
- a hőleadó/fan-coil strukturált elemként a korszerűsítési javaslatban szerepelhet, ez nem jelenlegi állapot;
- az OÉNY fűtési rendszerének ötfokozatú energetikai minősítése túl durva a hőleadó- és hőfoklépcső-kapuhoz;
- hidraulikai topológia/szabályozhatóság, villamos csatlakozás/mérés/headroom és engedélyezési readiness nincs B02-ban bizonyítva.

Az SRC-B02-HU-CERT-RULES-2008 és SRC-B02-HU-ENERGY-RULES-2023 jogszabályi vagy referencia-követelményt adhat, de nem tölti ki a vizsgált épület megfigyelt értékét. Az SRC-B02-HU-LTRS-FULL-2021 módszertani irányt ad, nem országos hőleadó-megoszlást.

## Minimális anonimizált pilot-séma

A minimális pilot gépi sémája: schemas/oeny_readiness_pilot.schema.json.

Kötelező adatminimalizálás:

- nincs név, cím, helyrajzi szám, HET-azonosító, koordináta, e-mail, telefonszám, fotó vagy szabad szöveg;
- csak durva terület- és időbontás maradhat;
- a pilot_record_id véletlen, nem visszafejthető munkapéldány-azonosító, kulcs vagy megfeleltetési tábla nélkül;
- minden readiness-mezőhöz OBS, Q vagy NOT_IN_SOURCE státusz kell;
- OBS hőleadó- vagy hőmérsékletértékhez explicit bizonyítéktípus és oldalhivatkozás szükséges;
- a referencia 55/45 °C érték csak REFERENCE_ASSUMPTION, nem vizsgált épület-megfigyelés.

Ez a séma kizárólag pilot-átvételi szerződés. Nem engedélyez adatbekérést, országos súlyozást vagy publikálható aggregációt.

## Mi maradna OÉNY után is bizonyítatlan?

Még egy sikeres, anonimizált, strukturált vagy kettős vak PDF-pilot után is külön kapu maradna:

1. az OÉNY-tanúsítványállomány KSH-lakásállományhoz viszonyított reprezentativitása;
2. a hőleadó- és hőfoklépcső-megoszlás országos, archetipusos és régiós kiterjesztése;
3. a KSH/WBL-projekciókkal való érvényes közös cellakapcsolat;
4. az S1 előtte/utána keresletcsökkentési hatás és fázis-időzítés;
5. hidraulikai topológia, szabályozhatóság, villamos csatlakozás, mérés és DSO headroom;
6. engedélyezési, kivitelezési és életciklus-readiness;
7. jogi/gazdasági programjogosultság, CAPEX, támogatási rés és háztartási cash-flow;
8. a nem megfigyelt, adatvédelmi okból elnyomott vagy NOT_IN_SOURCE cellák eloszlása.

Ezért az OÉNY-pilot legfeljebb a bizonyíték-kinyerhetőséget és a dokumentum-alapú mezők pontosságát tesztelheti. Nem zárja le önmagában a B02 alkalmassági modellt.

## Következő döntési kapu

Az eredmény alapján csak ezután szabad véglegesíteni a Lechner/OÉNY felé küldendő kérés mezőit. A kérés küldése továbbra is külön Joseph-jóváhagyási kapu; jelen dokumentum és a séma nem jelent külső adatbekérést.
