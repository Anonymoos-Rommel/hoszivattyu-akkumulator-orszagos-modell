# P1-L OÉNY Data Request Release Gate

**Állapot:** `READY_FOR_HUMAN_REVIEW / NOT SENT`

**Verzió:** 2026-08-17 / v1.0

**Hatókör:** kizárólag a P1F adatigénylési tervezet tényleges kiküldésének biztonságos előkészítése. Új energetikai kutatás, külső adatbekérés és adatátvétel nem történt.

A publikus gépi hozzáférés ellenőrzése a [P1-M OÉNY Public Machine Access Audittal](../source_packs/P1M_OENY_PUBLIC_MACHINE_ACCESS_AUDIT.md) lezárult. Mivel a P1K 22 mezőjéből egyetlen sem bizonyított teljes, P1K-kompatibilis publikus gépi forrásként, a célzott pilot-adatkérés indokolt.

## 1. Csomag tartalma

- [Végleges, de nem küldött levél](P1L_OENY_FINAL_REQUEST_LETTER.md)
- [P1L-FINAL hivatalos levél](P1L_FINAL_OENY_REQUEST_LETTER.md)
- [P1L-FINAL rövid e-mail-kísérő](P1L_FINAL_EMAIL_COVER.md)
- [P1L-FINAL 1. számú melléklet](P1L_FINAL_ATTACHMENT_1_REQUESTED_FIELDS.md)
- [P1L-FINAL Joseph approval sheet](P1L_FINAL_JOSEPH_APPROVAL_SHEET.md)
- [Joseph approval sheet](P1L_JOSEPH_APPROVAL_SHEET.md)
- [Requested-field manifest](../../registry/oeny_requested_field_manifest.csv)
- [Jogi/adatvédelmi checklist](P1L_LEGAL_PRIVACY_CHECKLIST.md)
- [Címzett- és csatornajavaslat](P1L_RECIPIENT_CHANNEL_PROPOSAL.md)

Az `P1L_OENY_FINAL_REQUEST_LETTER.md` és a `P1L_JOSEPH_APPROVAL_SHEET.md` korábbi P1L gate-artefaktumok; a küldésre előkészített kanonikus dokumentumok a fenti `P1L-FINAL` fájlok. Egyik változat sem küldhető ki Joseph külön jóváhagyása nélkül.

## 2. Forrás- és határszabály

A release package a következő kanonikus artefaktumokból készült:

- P1F OÉNY adatigénylési tervezet;
- P1J B02 S0–S2 Evidence Gap Matrix;
- P1K OÉNY Pilot Acceptance Contract;
- `schemas/oeny_readiness_pilot.schema.json`;
- `registry/oeny_pilot_acceptance_contract.csv`.

A P1L a P1F korábbi, szélesebb leltárkérését scope-discipline okból szűkíti. A végleges levél nem kéri a P1K-ban nem szereplő tanúsítási ok, számítási szoftver vagy szoftververzió mezőit. Ezek kutatásilag érdekesek lehetnek, de ebben a release gate-ben nem bizonyítottan szükségesek.

## 3. Címzett és csatorna

Javasolt címzett: **Lechner Tudásközpont Nonprofit Kft. – Jogi Igazgatóság, közadat felelős szervezeti egység**.

Elsődleges csatorna: **Ügyfélkapus e-Papír**. Tartalék: **info@lechnerkozpont.hu**. A csatornákat nem használjuk párhuzamosan.

Az aktuális hivatalos Lechner-oldal szerint a Lechner jogszabályi felhatalmazás alapján működteti az OÉNY-t, a Jogi Igazgatóság a közadat-felelős szervezeti egység, és a közérdekű adat igényelhető e-mailen vagy Ügyfélkapus e-Papíron. Ez a címzési kompetenciát igazolja; az egyes belső mezők adatgazdája és átadhatósága csak a Lechner válaszával válik bizonyítottá.

## 4. Jogcím és korlátozott állítások

A javasolt út a közérdekűadat-igénylés az Infotv. 28. § (1) alapján. A levél nem állít jogosultságot személyes, üzleti titoknak minősülő, korlátozott, nem meglévő vagy új feldolgozással előállítandó adatra. A kérés minden pontja a meglévő adatra, adatszótárra, aggregált leltárra vagy jogszerűen anonimizálható pilot lehetőségére korlátozott.

## 5. Adatminimalizálás és újraazonosítás

Az exact address, coordinate, HET-ID, name, contact data, free text, photo, PDF, original certificate and linkage key kizárt. A kombinált ritka cellákra a szolgáltató saját elnyomási/összevonási szabálya irányadó. P1L nem talál ki univerzális k-számot; elnyomott cella ismeretlen, nem nulla.

## 6. Pilot-kérés

Egyszeri, legfeljebb **500 rekordos** strukturált pilot, lehetőleg disclosure-safe rétegzéssel. Kisebb arányos minta elfogadható; 500 fölé külön Joseph-jóváhagyás nélkül nem megyünk. Elsődleges formátum UTF-8 CSV/JSON a schema 1.0 szerint; PDF/fotó/dokumentum-pilot nincs ebben a kérésben.

## 7. Felhasználás, megőrzés és törlés

Az eredeti rekordok nem kerülnek publikálásra vagy továbbadásra. Származtatott aggregátum csak jogszerű licenc- és forrásfeltételek mellett publikálható. A nyers fájlra javasolt belső szabály: korlátozott helyi quarantine, Git és publikációs OneDrive-útvonal nélkül; legfeljebb 180 nap, majd törlés, miközben a hash, manifest és aggregált reprodukciós napló megőrizhető. Ez `PROPOSED_POL`, nem rejtett szolgáltatói feltétel; rövidebb szolgáltatói határidő vagy jogi hold elsőbbséget élvez.

## 8. Pre-send döntés

**`READY_FOR_HUMAN_REVIEW`**

A P1M audit lezárult, és `PATH_B_HYBRID` eredményt adott. A P1L-FINAL a teljes P1K-mezőkészletet kéri, mert egyik mező sem bizonyított teljes, P1K-kompatibilis publikus gépi forrásként. A tényleges küldéshez Josephnek kell kitöltenie az igénylő nevét/szervezetét és válaszcímét, választania kell az e-Papír és e-mail között, majd külön send approvalt adnia.

**`REVISE`** szükséges, ha a címzett/csatorna eltér, új mező kerülne a levélbe, 500-nál nagyobb mintát kérnének, nincs disclosure-control, vagy a Lechner válasza új jogi/adatvédelmi feltételt támaszt.

**`NO_GO`** szükséges, ha a küldés jogalapja, az anonimizálás, a biztonságos átadás vagy a kérés tényleges teljesíthetősége nem tartható fenn.

## 9. Külső műveleti tilalom

E csomag elkészítése nem küldött e-mailt, nem nyitott e-Papír-ügyet, nem indított telefonhívást és nem vett át külső adatot. A küldés külön, exact-head Joseph-jóváhagyási kapu.

## Hivatalos források

- [Lechner – Közérdekű adatok](https://lechnerkozpont.hu/oldal/kozerdeku-adatok)
- [Lechner – E-építésügy / OÉNY](https://lechnerkozpont.hu/oldal/e-epitesugy)
- [Infotv. – Nemzeti Jogszabálytár](https://njt.hu/jogszabaly/2011-112-00-00.10)
- [e-Papír](https://epapir.gov.hu)
