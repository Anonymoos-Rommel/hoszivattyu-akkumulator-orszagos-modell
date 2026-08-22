# P1-L jogi és adatvédelmi checklist

**Állapot:** HOLD_PUBLIC_ACCESS_AUDIT / NEM KÜLDÖTT

Ez a checklist nem jogi vélemény és nem adatszolgáltatási engedély. Azt dokumentálja, hogy a kérés milyen korlátokkal készíthető elő.

| Ellenőrzési pont | P1L állapot | Bizonyíték / feltétel | Joseph előtti teendő |
|---|---|---|---|
| Adatkezelő és adatgazda | `CONFIRMED_FOR_ADDRESSING` | A Lechner hivatalos oldala szerint a Lechner jogszabályi felhatalmazás alapján működteti az OÉNY-t; a Jogi Igazgatóság a közadat-felelős egység. Az egyes belső mezők tényleges adatgazdája nincs nyilvánosan bizonyítva. | A levélben csak a Lechner kezelésében lévő meglévő adatok megismerését kérjük; a mezőgazda és átadhatóság megerősítését a Lechnertől kérjük. |
| Jogcím | `CONDITIONALLY_READY` | A közérdekű adat megismerése iránti igény szóban, írásban vagy elektronikusan benyújtható az Infotv. 28. § (1) alapján; a Lechner ezt a saját oldalán is megjelöli. | Nem állítunk alanyi jogot személyes, üzleti titoknak minősülő, korlátozott vagy nem meglévő adatra; új elemzést és új adatbázisépítést nem kérünk. |
| Kért adat meglévősége | `CONDITIONALLY_READY` | Az Infotv.-alapú igény meglévő közérdekű adatra irányul. A mezők létezése és normalizáltsága jelenleg részben Q/GAP. | A levél minden pontján szerepel: meglévő adat esetén; ha nem létezik, elegendő a nemlétezés/legközelebbi meglévő adat rövid jelzése. |
| Közvetlen azonosítók | `PASS` | A P1K-022 tiltja a nevet, címet, HET-ID-t, koordinátát, e-mailt, telefont, szabad szöveget, fotót és linkage key-t. | A küldendő levélben ezek kifejezetten kizárva maradnak. |
| Álnevesítés és kapcsolati kulcs | `PASS_WITH_CONDITION` | A pilot_record_id technikai, nem visszafejthető ID; kulcstábla nem kérhető. | Nem kérünk ugyanazon ingatlan/tanúsítvány újrafelismerésére alkalmas kulcsot; csak a szolgáltató általános, személyes adatot nem tartalmazó kapcsolati szabály-leírását kérjük, ha az meglévő dokumentáció. |
| Ritka cellák és újraazonosítás | `PASS_WITH_CONDITION` | A kombinált durva terület × épületkategória × időszak × alapterület cellák újraazonosítási kockázatot hordozhatnak. Nincs igazolt, minden esetre alkalmazható k-szám a projektben. | A Lechner saját elnyomási/összevonási szabálya irányadó; ritka cellát ne adjon ki; az elnyomást és összevonást röviden dokumentálja. P1L nem kényszerít ki saját k-számot. |
| Mintaméret | `PASS_WITH_CONDITION` | Egy egyszeri, legfeljebb 500 rekordos strukturált pilot; kisebb arányos minta elfogadható, 500 fölé új Joseph-jóváhagyás nélkül nem megyünk. | Lehetőleg rétegzett kiválasztás durva régió/településtípus, épületkategória és építési-időszak szerint; súlyt és reprezentativitási garanciát nem kérünk. |
| Adatformátum | `PASS` | Elsődleges UTF-8 CSV vagy JSON, a P1K schema 1.0, kódtáblák és verzió szükséges. | PDF, fénykép, szabad szöveg és eredeti tanúsítvány nem része ennek a kérésnek. |
| Adatminimalizálás | `PASS` | A requested-field manifest kizárólag a P1K 22 property-jét és a szükséges kísérő metaadatot tartalmazza. | A P1F korábbi extra változói nem kerülnek a végleges levélbe. |
| Felhasználási cél | `PASS_WITH_CONDITION` | Belső módszertani kutatás, reprodukálható feldolgozás és származtatott aggregátumok készítése. | A cél nem jelent automatikus újrahasznosítási vagy publikációs engedélyt. |
| Publikáció | `PASS_WITH_CONDITION` | Eredeti rekordok és dokumentumok nem kerülnek újraközlésre; csak jogszerű, aggregált/származtatott eredmény publikálható. | A Lechner által közölt licenc-, forrásmegjelölési és további feltételeket írásban el kell fogadni vagy el kell utasítani Joseph döntése alapján. |
| Biztonságos átadás | `OPEN_UNTIL_RESPONSE` | A levél biztonságos átadási mód megjelölését kéri; kéretlen mellékletet nem kérünk. | Valós fájl átvétele előtt külön intake- és biztonságos átadási kapu szükséges. |
| Helyi tárolás | `PROPOSED_POL` | Nyers pilot csak korlátozott, nem verziókezelt, helyi quarantine-ban; Gitbe, public repo-ba, OneDrive-szinkronizált publikációs útvonalra nem kerülhet. | Joseph hagyja jóvá a tényleges helyi tárolási útvonalat és hozzáférési listát; jelen csomag nem hoz létre nyers adatot. |
| Megőrzés és törlés | `PROPOSED_POL` | Alapértelmezett belső javaslat: nyers fájl csak a reprodukálhatósági ellenőrzésig, legfeljebb 180 napig; utána törlés, a hash/manifest/aggregátum maradhat. Szolgáltatói rövidebb határidő vagy jogi megőrzés elsőbbséget élvez. | A tényleges retentiont Joseph és a szolgáltató feltételei alapján kell rögzíteni; jogi hold esetén a törlés felfüggesztendő. |
| Külső adatbekérés | `PASS` | E csomag létrehozása nem küld e-mailt, e-Papírt és nem indít külső megkeresést. | A küldés kizárólag külön Joseph-approval után történhet. |

## Jogalapi korlát

A P1L a közérdekűadat-igénylés útját javasolja a Lechner hivatalos tájékoztatása és az Infotv. 28. § (1) alapján. Ez nem bizonyítja, hogy a kért pilotrekordok valamennyi mezője közérdekű adatként kiadható, hogy személyes adatot jogszerűen lehetne átadni, vagy hogy a Lechner új aggregációt köteles létrehozni. A levél ezért meglévő adatot, meglévő adatszótárt és adatvédelmi szempontból átadható anonimizált mintát kér, és elfogadja a részleges választ vagy a nemlétezés közlését.

## Ritka cella döntési szabály

A P1L nem állít univerzális minimum-cellaméretet. Ha bármely kombinációból természetes személy, konkrét ingatlan, tanúsító vagy rendeltetési egység ésszerű eséllyel visszakövetkeztethető, az adott cellát a szolgáltató saját szabálya szerint el kell nyomni vagy durvább kategóriába kell összevonni. Elnyomott cella ismeretlen adat, nem nulla.

## Hivatalos források

- [Lechner – Közérdekű adatok](https://lechnerkozpont.hu/oldal/kozerdeku-adatok)
- [Lechner – E-építésügy / OÉNY](https://lechnerkozpont.hu/oldal/e-epitesugy)
- [Infotv. – Nemzeti Jogszabálytár](https://njt.hu/jogszabaly/2011-112-00-00.10)
- [Lechner ügyfélkapcsolati adatkezelési tájékoztató](https://lechnerkozpont.hu/sites/default/files/doc/adatvedelem/adatkezelesi-tajekoztato-a-lechner-tudaskozpont-ugyfelszolgalatanak-mukodtetesevel-kapcsolatos-adatekezelesekrol.pdf)
