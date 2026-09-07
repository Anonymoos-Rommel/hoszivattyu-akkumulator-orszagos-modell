# P43 — Techem current radiator aggregate research request

**Státusz:** `READY_FOR_HUMAN_REVIEW`

**Küldési állapot:** `NOT SENT`

## Címzés

**Címzett:** Techem Kft.

**Aktuális nyilvános e-mail:** `techem@techem.hu`

**Aktuális kapcsolati oldal:** `https://www.techem.com/hu/hu/informaciok/kapcsolat`

**Tárgy:** Kutatási adatkérés – anonimizált/aggregált magyar radiátor- és hőleadó műszaki állományadatok

## Levéltervezet

Tisztelt Techem Kft.!

Egy magyar lakóépület-energetikai kutatási és döntéstámogató modellen dolgozunk, amely a hőszivattyús átállás országos műszaki és beruházási igényeit vizsgálja. A modell egyik fontos hiányzó inputja a meglévő hidronikus hőleadók, különösen a radiátorok fizikai állománya: hány egység található az érintett lakásokban, milyen fő műszaki kategóriákba tartoznak, és milyen méret-/teljesítményjellemzőkkel rendelkeznek.

A 157/2005. (VIII. 15.) Korm. rendelet jelenlegi szabályai alapján a fűtési költségmegosztás a hőleadó készülékekhez kötődik; a 17/C. § és az 5. melléklet alapján az elektronikus költségmegosztók értékelése az adott hőleadó műszaki adatait is figyelembe veheti. A Techem nyilvános magyar mintafűtésiköltség-elszámolásában radiátoronként külön rekord és több műszaki/értékelési mező (`Rad.sz.`, faktor, méret) jelenik meg.

Ez alapján szeretnénk megkérdezni, hogy a Techem magyarországi működésében rendelkezésre áll-e olyan, személyes adatoktól és konkrét címektől megtisztított aggregált műszaki adat, amely kutatási célra felhasználható a radiátoros állomány jellemzésére.

## Elsődlegesen kért aggregált/adatszótár információ

Kérjük jelezni, hogy az Önök rendszerében a radiátor/hőleadó rekordokhoz az alábbi mezők közül melyek állnak rendelkezésre:

- egyedi hőleadó/radiátor rekord léte és darabszám;
- radiátor gyártmány/típus vagy típuscsalád;
- anyag (ha nyilvántartott);
- méret/méretek;
- tagszám vagy konfiguráció (ha releváns);
- névleges hőteljesítmény vagy az azt reprezentáló műszaki értékelési faktor;
- hőleadóhoz tartozó költségmegosztó értékelési paraméterei;
- épület fűtési rendszerének durva kategóriája;
- referencia-/utolsó felmérési vagy telepítési év;
- településnél durvább földrajzi kategória, ha disclosure-safe módon rendelkezésre áll.

Első körben már egy **adatszótár/kódlista és mezőkitöltöttségi összesítés** is megfelelő lenne.

## Ha aggregált műszaki táblázat kiadható

Kérjük lehetőség szerint az alábbi, kizárólag aggregált formát:

- lefedett lakóépületek száma;
- lefedett lakások/díjfizetők száma;
- nyilvántartott radiátor/hőleadó egységek száma;
- radiátoregység/lakás átlag és eloszlás (pl. medián, percentilisek vagy kategóriák);
- fő radiátortípus-/anyag-/méretkategóriák gyakorisága;
- névleges teljesítmény vagy értékelési faktor szerinti kategóriák gyakorisága, ha ez szakmailag értelmezhető;
- referenciaév vagy az állomány utolsó műszaki felmérésének időtartománya.

Ha országos összesítés nem készíthető, régiós vagy szolgáltatási terület szerinti aggregáció is hasznos lehet.

## Adatminimalizálás

Kifejezetten **nem kérünk**:

- nevet;
- címet;
- lakásazonosítót;
- ügyfélszámot;
- költségmegosztó vagy mérő egyedi gyári számát;
- fogyasztási idősorokat;
- számla- vagy díjadatot;
- olyan mezőt, amelyből természetes személy vagy konkrét ingatlan visszaazonosítható.

Egyedi ügyfél- vagy ingatlanrekordokra nincs szükségünk. A cél kizárólag az épületgépészeti állomány statisztikai jellemzése.

## Felhasználási határ

Az Önök által lefedett állományt nem tekintenénk automatikusan a teljes magyar lakásállomány reprezentatív mintájának. A modellt úgy építjük, hogy a szolgáltatói lefedettség, az épülettípus és a távhős/központi fűtési szelekció külön korlátozásként szerepeljen.

A kapott adatokat kizárólag kutatási/modellezési célra használnánk. Nem nyilvános vagy korlátozott nyers adatot nem tennénk közzé nyilvános repositoryban; ott csak forráshivatkozás, módszertan és jogszerű aggregált/származtatott eredmény jelenne meg az Önök feltételei szerint.

Elsődlegesen költségmentesen rendelkezésre bocsátható aggregált kutatási információt vagy adatszótárat keresünk. Ha a kért összesítés csak díj ellenében vagy külön megállapodással érhető el, kérjük ezt az adatátadás előtt jelezni.

Köszönjük segítségüket.

Tisztelettel:

**[IGÉNYLŐ / SZERVEZET]**

**[VÁLASZCÍM]**

## Hivatkozások

- 157/2005. (VIII. 15.) Korm. rendelet, 17/A § 8., 17/C §, 5. melléklet: `https://njt.jog.gov.hu/jogszabaly/2005-157-20-22.21`.
- Techem Hungary kapcsolat: `https://www.techem.com/hu/hu/informaciok/kapcsolat`.
- Techem magyar mintafűtésiköltség-elszámolás: `https://www.techem.com/content/dam/techem-hu/documents/Magyar%C3%A1zat%20f%C5%B1t%C3%A9si%20k%C3%B6lts%C3%A9g%20elsz%C3%A1mol%C3%A1shoz.pdf.coredownload.pdf`.
