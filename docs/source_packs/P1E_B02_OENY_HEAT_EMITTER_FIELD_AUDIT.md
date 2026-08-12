# P1-E forráscsomag: OÉNY hőleadó- és hőmérsékletmező-audit

Állapot: **mezőaudit lezárva; közvetlen országos hőleadó-adatmező nem igazolt**

Ellenőrzés napja: **2026-08-12**

Vizsgált OÉNY e-tanúsítási dokumentációverzió: **v3.0.14801** (`d17e08f05208aa77af62fe50455fdbfb8bd79ea4`)

## Döntési eredmény

Az OÉNY e-tanúsítás országos nyilvántartás, és a 2023. november 1. utáni tanúsítványokhoz JSON vagy XML forrásfájlt, valamint kötelező számítási PDF-mellékletet fogad. Ettől azonban a B02 számára szükséges adatok még nem válnak egységes, országosan aggregálható mezővé.

A jelenlegi hivatalos feltöltési séma:

- strukturáltan tárol épületkategóriát, építési évet, hasznos alapterületet, energiafogyasztási adatokat és a fűtési rendszer ötfokozatú energetikai minőségét;
- nem tartalmaz külön mezőt a meglévő radiátor, padló-, fal- vagy mennyezetfűtés, illetve fan-coil típusára;
- nem tartalmaz külön számszerű mezőt a tervezési előremenő vagy visszatérő hőmérsékletre;
- kötelezően tartalmaz egy vagy több, a jellemző hőleadót és szabályozását ábrázoló fényképet, de ez képi bizonyíték, nem kategorizált hőleadó-adat;
- strukturáltan felsorolhat hőleadót vagy fan-coilt a **javasolt korszerűsítés** elemeként, de ez nem bizonyítja a jelenlegi beépített rendszert.

A 176/2008. (VI. 30.) Korm. rendelet 2. melléklet 1.10.3. pontja előírja, hogy az alátámasztó munkarész épülettechnikai rendszerenként tartalmazza többek között az elosztó vezeték helyét, a hőfoklépcsőt, az elosztási veszteséget és a lefedettségi arányt. A jelenlegi OÉNY-boríték ezt a részletes számítást egy kötelező, base64-kódolt PDF-csatolmányban őrzi, nem dedikált hőmérsékletmezőkben. Ezért a hőfoklépcső dokumentumszintű adatjelölt, nem azonnal lekérdezhető strukturált adat.

## Mező- és hozzáférési mátrix

| B02-adatigény | Jogszabály vagy számítás kezeli | OÉNY JSON/XML strukturált mező | Csatolmány vagy kép | Nyilvános országos aggregáció | Minősítés |
| --- | --- | --- | --- | --- | --- |
| Jelenlegi hőleadó típusa | A jelenlegi épülettechnikai állapot és a jellemző hőleadó fotója része a tanúsításnak | **Nincs dedikált típusmező** | Kötelező hőleadófotó; leírás és számítási PDF előfordulhat | Nem azonosított | `GAP` |
| Tervezési hőfoklépcső | A 176/2008. rendelet 2. melléklet 1.10.3. pontja előírja | **Nincs dedikált számszerű mező** | A kötelező számítási PDF-ben várható | Nem azonosított | `DOCUMENT_EMBEDDED` |
| Előremenő és visszatérő hőmérséklet külön | A számítási módszer és referencia-rendszer használ ilyen értékeket | **Nincs dedikált mezőpár** | Szoftverfüggően szerepelhet a PDF-ben | Nem azonosított | `GAP` |
| Fűtési rendszer hatékonysága | Kötelező tanúsítványi értékelés | `bad/poor/average/good/excellent` | Nem szükséges | Egyedi nyilvános adatok korlátozottak; bulk export nem azonosított | `STRUCTURED_COARSE` |
| Jelenlegi hőtermelő típusa | A számítás része | **Nincs általános jelenlegi típus-enum** | Számítási PDF és egyes esetekben fotó | Nem azonosított | `DOCUMENT_EMBEDDED` |
| Hőleadó/fan-coil mint korszerűsítési javaslat | A tanúsítvány javaslati része kezeli | Strukturált javaslati elem lehet | Nem szükséges | Nem azonosított | `PROPOSAL_ONLY` |
| Épület típusa | A tanúsítvány kezeli | Strukturált `buildingCategory` | Nem szükséges | Egyedi lekérdezésben korlátozott | `STRUCTURED_BIASED_SAMPLE` |

## A negatív mezőállítás bizonyítása

A `v3.0.14801` hivatalos `dictionary.md`, `validationRules.md` és teljes JSON-minta ellenőrzésekor:

- nincs `radiator`, `supplyTemperature`, `returnTemperature` vagy ezekkel egyenértékű, jelenlegi állapotot leíró mező;
- a `buildingServicesSystemEnergeticQuality.heatingSystem` csak ötfokozatú minősítés;
- a `HeatExchangers`, `FanCoilUnits` és kapcsolódó elemek a `recommendedModernisations` blokk értékkészletében szerepelnek;
- a `photos.characteristicHeatExchanger` kategória 1–3 képet követel meg;
- a `calculationsPdfFileContent` kötelező, legfeljebb 15 MB méretű PDF-csatolmány.

A három ellenőrzött hivatalos sémafájl SHA-256 lenyomata:

- `dictionary.md`: `b95fa656b13eaac4228a2d5d7388fcfc6d7f1e483bf656a85551fb9a7b326457`;
- `validationRules.md`: `c729c53a8c223f9460d3f379669e566c9560a4ce14fc6cfd68959db7ccc0f374`;
- `functional_unit_full_data.json`: `f717b7b502abb79fa9827f38e3916e67c8b27e6c4391f3bdb22c94fc5ec159f5`.

Az audit élő, verzióhoz kötött újrafuttatása:

```powershell
python tools/audit_oeny_heat_emitter_schema.py
```

A parancs előbb ellenőrzi a három forrás SHA-256 lenyomatát, majd a teljes JSON-mintában külön vizsgálja a jelenlegi állapot mezőit, a korszerűsítési javaslat értékeit, a hőleadófotó-kategóriát és a számítási PDF jelenlétét.

## Nyilvános hozzáférés

Az OÉNY felhasználói segédlete szerint a nyilvános felület cím alapján csak korlátozott tartalmú lekérdezést ad. A forrás JSON/XML és a hiteles PDF letöltése a tanúsító saját tanúsítványlistájában érhető el; régi rendszerben készült tanúsítványok ott sem érhetők el. A nyilvános OÉNY-statisztika tanúsítványszámot és területi/időbeli bontást kínál, nem hőleadó- vagy hőfoklépcső-megoszlást.

Ezért webes címkereséssel országos adatállomány nem építhető. Egyedi tanúsítványok automatizált begyűjtése adatvédelmi, reprezentativitási és hozzáférési okból sem elfogadható beszerzési út.

## Adminisztratív mintakérés

Első kapu: írásos adatszótár- és mintakérés az OÉNY üzemeltetőjéhez. Első körben személyes adat, cím, helyrajzi szám és fotó nélkül kell kérni:

1. a 2023. november 1. utáni lakóépület-tanúsítványok rekordszámát és mezőnkénti hiányarányát;
2. a strukturált mezők teljes adatszótárát és verziótörténetét;
3. annak megerősítését, hogy a hőfoklépcső vagy az előremenő/visszatérő hőmérséklet normalizált háttérmezőként létezik-e;
4. anonimizált rekordmintát: év, vármegye vagy településtípus, `buildingCategory`, építési év, hasznos alapterület, fűtésihatékonyság-kategória, energiahordozó, tanúsítás oka és számítási szoftver/verzió;
5. ha nincs normalizált hőmérsékletmező, rétegzett, anonimizált 500–1000 darabos számítási PDF-mintát a dokumentumkinyerhetőség próbájához;
6. a mintavételi keret leírását, duplikált/kapcsolódó tanúsítványok jelzését és a régi–új rendszer közötti törést.

A PDF-próba csak akkor folytatható, ha a dokumentumok jogszerűen átadhatók, a személyes adatok eltávolíthatók, és egy kézi kettős annotációval ellenőrzött mintán a hőleadótípus és hőfoklépcső reprodukálhatóan kinyerhető.

## Reprezentativitási kapu

Az OÉNY tanúsítványok nem véletlen lakásmintát alkotnak: főként adásvételhez, bérbeadáshoz, új építéshez és pályázathoz készülnek. Ezért még teljes adminisztratív hozzáférés esetén sem számolható közvetlen országos megoszlás.

Országos becslés előtt kötelező:

- a tanúsítványállomány KSH lakásállományhoz való lefedettségi összevetése;
- épülettípus × építési időszak × településtípus × fűtési mód szerinti rétegzés;
- hiányzó és nem értelmezhető mezők külön kategóriája;
- duplikált és megújított tanúsítványok kezelése;
- mintasúly vagy kalibráció dokumentálása;
- a klasszifikáció pontosságának kézi, vak ellenőrzése.

## Források

1. [176/2008. (VI. 30.) Korm. rendelet](https://njt.hu/jogszabaly/2008-176-20-22.22), különösen 3. § (1b), 6. § (2a) és 2. melléklet 1.10.3.
2. [9/2023. (V. 25.) ÉKM rendelet](https://njt.hu/jogszabaly/2023-9-20-8X), különösen a referencia fűtési rendszer 55/45 °C hőfoklépcsője és előremenő-hőmérséklet-szabályozása.
3. [OÉNY e-tanúsítás szótár, v3.0.14801](https://git.lechnerkozpont.hu/entan/dokumentacio/-/blob/v3.0.14801/docs/dictionary.md).
4. [OÉNY e-tanúsítás validációs szabályok, v3.0.14801](https://git.lechnerkozpont.hu/entan/dokumentacio/-/blob/v3.0.14801/docs/validationRules.md).
5. [OÉNY teljes funkcionális egység JSON-minta, v3.0.14801](https://git.lechnerkozpont.hu/entan/dokumentacio/-/blob/v3.0.14801/test/system/data/json/functional_unit_full_data.json).
6. [E-tanúsítás felhasználói segédlet tanúsító szakemberek számára](https://dok.e-epites.hu/e-tanusitas/Felhasznaloi_utmutato_tanusito_szakembereknek.pdf).
7. [OÉNY nyilvános statisztikai felület](https://www.e-epites.hu/oeny-statisztika/statisztika).

## Nem következik ebből

- nincs országos radiátor-, felületfűtés- vagy fan-coil-megoszlás;
- nincs hőfoklépcső- vagy előremenőhőmérséklet-eloszlás;
- a korszerűsítési javaslat nem a jelenlegi rendszer megfigyelése;
- a hőleadófotó nem automatikusan osztályozható megfigyelés;
- nincs új technikailag alkalmas lakásszám, COP, retrofitköltség vagy programjogosultság.
