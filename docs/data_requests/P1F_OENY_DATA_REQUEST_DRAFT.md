# P1-F OÉNY adatigénylési tervezet

Állapot: **KÜLDÉSRE NEM JÓVÁHAGYOTT TERVEZET**

Verzió: **2026-08-12 / v0.1**

Ez a nyilvános példány nem tartalmaz igénylői személyes adatot. A kitöltött változatot tilos Gitbe menteni. Az elküldéshez Joseph külön tartalmi jóváhagyása szükséges.

## Hivatalos címzés

- Címzett: Lechner Tudásközpont Nonprofit Kft., Jogi Igazgatóság
- E-mail: `info@lechnerkozpont.hu`
- Alternatíva: [e-Papír](https://epapir.gov.hu)
- Postacím: 1519 Budapest, Pf. 566.
- Tárgy: Közérdekű adatigénylés – anonimizált OÉNY energetikai adatszótár és kutatási minta

A Lechner hivatalos igénylőlapja használható, de a központ tájékoztatója szerint az igény írásban vagy elektronikusan is benyújtható. A formanyomtatvány az igénylő nevét, elérhetőségét, az igény pontos leírását és a teljesítés kívánt módját kéri. Ha az adatot újrahasznosításra is kérjük, ezt külön jelezni kell.

## Küldendő szöveg

> Tisztelt Jogi Igazgatóság!
>
> Alulírott **[IGÉNYLŐ NEVE VAGY SZERVEZET NEVE]**, válaszcím: **[E-MAIL VAGY POSTAI CÍM]**, a 2011. évi CXII. törvény 28. §-a alapján kérem az alábbi, a Lechner Tudásközpont kezelésében lévő közérdekű adatok elektronikus megismerését.
>
> A kérés célja egy nyilvános, forrásolt magyarországi hőszivattyú- és háztartásiakkumulátor-kutatás módszertani megalapozása. Az átadott egyedi adatot vagy dokumentumot nem tesszük közzé. Kizárólag jogszerűen újrahasznosítható, aggregált vagy anonimizált származtatott eredmény publikálható, az Önök által közölt feltételek és forrásmegjelölés szerint.
>
> **1. Első szakasz – meglévő adatszótár és aggregált leltár**
>
> Kérem, amennyiben a kért információk meglévő adatként vagy kimutatásként rendelkezésre állnak:
>
> 1. a 2023. november 1. óta befogadott, lakóépületre vagy lakásra vonatkozó energetikai tanúsítványok strukturált mezőinek teljes adatszótárát, kódtábláit, sémaverzióit és verzióváltási dátumait;
> 2. annak megerősítését, hogy a jelenlegi hőleadó típusa, a tervezési hőfoklépcső, illetve az előremenő és visszatérő hőmérséklet létezik-e normalizált háttérmezőként akkor is, ha a nyilvános `v3.0.14801` feltöltési sémában nem szerepel;
> 3. rekordszámot és mezőnkénti kitöltöttségi darabszámot vagy hiányarányt a következő változókra: épületkategória, építési év vagy időszak, hasznos alapterület, vármegye vagy ennél kevésbé részletes területi kategória, településtípus, tanúsítás oka, fűtési rendszer energetikai minősége, energiahordozó, számítási szoftver és szoftververzió, továbbá az előző pontban felsorolt hőleadó- és hőmérsékletmezők;
> 4. a módosított, megújított vagy ugyanazon rendeltetési egységhez kapcsolódó tanúsítványok felismerésére szolgáló, személyes adatot nem tartalmazó kapcsolati szabály leírását;
> 5. a régi és az új e-tanúsítási rendszer közötti tartalmi vagy sématörések leírását;
> 6. a meglévő aggregált rekordszámokat év × épületkategória × építési időszak × településtípus × tanúsítás oka bontásban, az Önök adatvédelmi közzétételi szabályai szerint összevonva vagy elnyomva.
>
> **2. Második szakasz – anonimizált strukturált pilotminta**
>
> Ha jogilag és technikailag lehetséges, kérem egy anonimizált, géppel olvasható pilotminta átadását UTF-8 CSV vagy JSON formátumban. Tervezési tartományként 500–1000 rekordot jelölünk meg (`SCN`); kisebb, az Önök által arányosnak tartott minta is alkalmas az első kinyerhetőségi próbára.
>
> A mintában kizárólag a fenti kutatási változók, durvított idő- és területi kategóriák, valamint egy nem visszafejthető technikai rekordazonosító szerepeljen. Kifejezetten nem kérünk nevet, címet, helyrajzi számot, HET-azonosítót, e-mailt, telefonszámot, szabad szöveges megjegyzést, fényképet vagy bármely természetes személyre, tanúsítóra, tulajdonosra, megrendelőre vagy konkrét ingatlanra visszavezethető adatot.
>
> A minimális pilot-mezők és státuszok nyilvános szerződése: [`schemas/oeny_readiness_pilot.schema.json`](../../schemas/oeny_readiness_pilot.schema.json). A mezőszintű elfogadási feltételeket a [P1-K OÉNY Pilot Acceptance Contract](../source_packs/P1K_OENY_PILOT_ACCEPTANCE_CONTRACT.md) és a [gépi acceptance-regiszter](../../registry/oeny_pilot_acceptance_contract.csv) rögzíti. Ez a séma és szerződés nem kér országos alkalmassági, reprezentativitási vagy readiness-aggregációt; csak a mezők létezését, kitöltöttségét és bizonyítékalapját teszteli.
>
> **3. Külön későbbi kapu – számítási PDF pilot**
>
> Ha nincs normalizált hőleadó- vagy hőfoklépcsőmező, kérem egyelőre csak annak közlését, hogy jogszerűen és teljes anonimizálással átadható-e egy, a fenti rétegek szerint kiválasztott számítási-PDF-pilot. Ilyen dokumentumot e levél alapján még nem kérünk átadni. A pontos mintanagyságot, adatbiztonsági feltételeket és biztonságos átadási csatornát külön egyeztetés és új jóváhagyás után rögzítenénk.
>
> Az adatokból nem kérünk új szakmai minősítést vagy következtetést. Ha valamely felsorolt bontás vagy kimutatás nem létezik, kérem ennek rövid jelzését, valamint – ha lehetséges – a már meglévő, legközelebbi tartalmú adat vagy dokumentum megnevezését.
>
> Kifejezetten nem kérünk és nem tekintünk teljesítettnek: országos hőleadó- vagy hőfoklépcső-megoszlást, KSH/WBL közös archetípus-illesztést, S1 előtte/utána keresletcsökkentési hatást, hidraulikai/villamos/engedélyezési readiness-t, programjogosultságot vagy támogatási alkalmasságot.
>
> Kérem elektronikus, nem hiteles másolatban történő teljesítést. Nagy vagy korlátozott hozzáférésű állomány esetén kérem az Önök által jóváhagyott biztonságos átadási mód megjelölését; ilyen állományt kéretlen e-mail-mellékletként nem kérünk.
>
> Kérem továbbá az esetleges költség, licenc-, újrahasznosítási vagy további adatvédelmi feltételek előzetes közlését, mielőtt költséggel járó munka vagy átadás kezdődik. Ha az igény valamely része pontosításra szorul, kérem, keressenek a megadott válaszcímen. Részleges vagy szakaszos teljesítés is megfelelő.
>
> Kelt: **[DÁTUM]**
>
> Tisztelettel:
>
> **[IGÉNYLŐ NEVE / SZERVEZET]**
> **[VÁLASZCÍM]**

## Kitöltési és jóváhagyási ellenőrzőlista

1. A név és válaszcím csak a helyi, nem verziókezelt példányba kerüljön.
2. Joseph döntsön az igénylő személyéről vagy szervezetéről, az e-mail/e-Papír csatornáról és az újrahasznosítási szándék pontos szövegéről.
3. A levélhez ne csatoljunk belső kutatási dokumentumot, nyers adatot vagy személyes adatot.
4. Költségvállalás, licencelfogadás, titoktartás vagy adatfeldolgozói feltétel külön Joseph-döntést igényel.
5. PDF- vagy képminta fogadásához előbb a [feldolgozási protokoll](../protocols/P1F_OENY_SAMPLE_PROCESSING_PROTOCOL.md) kapuit kell jóváhagyni.
6. Beküldéskor külön, nem nyilvános nyilvántartásban rögzítendő a végleges szöveg, csatorna, időpont és visszaigazolás.

## Jogi-időzítési megjegyzés

Az Infotv. 28. § szerint az igény szóban, írásban vagy elektronikus úton is előterjeszthető; az azonosításhoz név és elérhetőség szükséges, a nem egyértelmű igény pontosítható. A 29. § főszabály szerint legfeljebb 15 napos teljesítési határidőt ad, amely nagy terjedelmű vagy aránytalan erőforrás-igényű kérésnél egy alkalommal 15 nappal meghosszabbítható, az igénylő első 15 napon belüli tájékoztatásával. Ez a rész nem jogi tanács; elküldés előtt a hatályos szöveg újraellenőrzendő.

## Hivatalos források

- [Lechner – Közérdekű adatok](https://lechnerkozpont.hu/oldal/kozerdeku-adatok)
- [Lechner hivatalos igénylőlap](https://lechnerkozpont.hu/doc/igenylolap.pdf)
- [Lechner közadat-igénylési eljárásrend](https://lechnerkozpont.hu/sites/default/files/doc/kozerdeku-es-a-kozerdekbol-nyilvanos-adatok-elektronikus-kozzetetelenek-valamint-a-megismeresukre-iranyulo-igenyek-teljesitesenek-rendje.pdf)
- [2011. évi CXII. törvény](https://njt.hu/jogszabaly/2011-112-00-00)
