# P1-L Joseph approval sheet

**Cél:** az OÉNY-adatigénylés tényleges kiküldésének előkészítése, külső küldés nélkül.

**Csomagverzió:** 2026-08-17 / v1.0

## Döntési javaslat

**`READY_FOR_JOSEPH_APPROVAL`**

Ez nem `SENT`, nem jogi vélemény és nem adatátvételi engedély. A levél csak az alábbi feltételek teljesülése után küldhető.

## Mit ellenőriztem

- [x] P1F, P1J és P1K összehangolása.
- [x] Kizárólag a P1K 22 séma-property-je szerepel a requested-field manifestben.
- [x] Egyszeri, legfeljebb 500 rekordos pilot; kisebb arányos minta elfogadható.
- [x] Rétegzett mintavétel kérése disclosure-safe durva kategóriák szerint.
- [x] UTF-8 CSV/JSON és schema 1.0 elsődleges; PDF/fotó/eredeti tanúsítvány kizárva.
- [x] PII, cím, HET-ID, koordináta, free text és linkage key kizárva.
- [x] Ritka kombinált cellák elnyomási/összevonási feltétele dokumentálva.
- [x] Eredeti rekordok újraközlése nem feltételezett; publikáció csak jogszerű aggregátumokra.
- [x] Helyi quarantine, retention és törlés belső szabályként megjelölve, nem rejtett alapértelmezésként.
- [x] Külső e-mail/e-Papír/adatbekérés nem történt.

## Címzett és csatorna

Javasolt címzett: **Lechner Tudásközpont Nonprofit Kft. – Jogi Igazgatóság, közadat felelős szervezeti egység**.

Elsődleges csatorna: **Ügyfélkapus e-Papír**. Tartalék: **info@lechnerkozpont.hu**. A két csatornát nem küldjük párhuzamosan.

Az aktuális hivatalos Lechner-oldal a Jogi Igazgatóságot jelöli közadat-felelősként, és az OÉNY üzemeltetését a Lechnerhez köti. Az egyes belső mezők adatgazdája és átadhatósága a Lechner válaszáig nem tekinthető bizonyítottnak.

## Joseph által kitöltendő mezők

- igénylő teljes neve vagy szervezete;
- válaszcím (e-mail vagy postai cím);
- választott csatorna: e-Papír vagy e-mail;
- a származtatott aggregátumok kívánt felhasználása és publikációja;
- a javasolt 180 napos belső raw-retention elfogadása vagy módosítása;
- küldés dátuma és a végleges tárgy.

## Küldési tiltások

- Ne csatoljunk belső DOCX-et, P1J/P1K belső anyagot, nyers adatot vagy személyes adatot.
- Ne kérjünk 500 rekordnál nagyobb pilotot új jóváhagyás nélkül.
- Ne kérjünk teljes tanúsítványt, fotót, PDF-et vagy HET-/ingatlan-azonosítót.
- Ne állítsuk, hogy a Lechner köteles új adatbázist vagy új szakmai elemzést létrehozni.
- Ne tekintsük a válasz hiányait nullának, és ne engedjük a pilotból országos readiness-következtetést.

## Jóváhagyási mező

**Döntés:** `READY_FOR_JOSEPH_APPROVAL` / `REVISE` / `NO_GO`

**Joseph megjegyzése:** ________________________________________________

**Jóváhagyó neve:** ____________________________________________________

**Dátum:** ____________________  **Aláírás / megerősítés:** ____________________

## Csomagelemek

- [P1L végleges, de nem küldött levél](P1L_OENY_FINAL_REQUEST_LETTER.md)
- [Requested-field manifest](../../registry/oeny_requested_field_manifest.csv)
- [Jogi/adatvédelmi checklist](P1L_LEGAL_PRIVACY_CHECKLIST.md)
- [Címzett- és csatornajavaslat](P1L_RECIPIENT_CHANNEL_PROPOSAL.md)
