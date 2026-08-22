# P1-M OÉNY Public Machine Access Audit

**Állapot:** `CLOSED_READ_ONLY / P1L=HOLD_PUBLIC_ACCESS_AUDIT`

**Ellenőrzés dátuma:** 2026-08-17

**Fő döntés:** `PATH_B_HYBRID`

## 1. Rövid eredmény

A hivatalos e-tanúsítás nyilvános webfelülete a böngészőből egy autentikációs fejléc nélküli, UI által meghívott JSON POST XHR-t használ. Ez igazolja a `PUBLIC_UI_MACHINE_READABLE` felületi állapotot, de nem igazol dokumentált public API-t, bulk hozzáférést vagy P1K readiness-adatcsatornát.

A kontrollált teszt kizárólag a nem valós `ZZZTEST` / `ZZZTEST` értékeket küldte az official UI-n keresztül. A válasz HTTP 200 és üres JSON-tömb volt. Nem történt valós cím lekérdezése, személyes vagy címhez köthető adat gyűjtése, pagination-teszt valós rekorddal, tömeges scraping, token-/session-művelet vagy jogosultság-megkerülés.

## 2. Bizonyított hivatalos felület és végpont

| Endpoint | Módszer | Auth | Megfigyelés | Státusz |
|---|---|---|---|---|
| https://www.oeny.hu/oeny/e-tanusitas/ | GET | Nem szükséges a publikus UI betöltéséhez | Nyilvános e-tanúsítás kereső; UI-footer: v3.0.13127 | `PUBLIC_UI_MACHINE_READABLE` belépési felület |
| https://www.oeny.hu/oeny/e-tanusitas/api/internal/cert-list/search | POST | Auth fejléc nem volt a kontrollált UI-kérésben | settlement, streetName, streetType, houseNumber; HTTP 200; válasz: [] | `PUBLIC_UI_MACHINE_READABLE`, nem dokumentált public API |
| https://www.oeny.hu/oeny/e-tanusitas/api/internal/user/latest-privacy-policy-version | GET | Publikus UI-betöltéskor meghívva | JSON kontroll-metaadat; nem P1K-adatforrás | `OUT_OF_SCOPE_CONTROL_PLANE` |
| https://www.oeny.hu/oeny/e-tanusitas/api/internal/authorization | GET | Publikus UI-betöltéskor meghívva | JSON authorization/control response; nem módosítottuk és nem kerültük meg | `OUT_OF_SCOPE_CONTROL_PLANE` |

A külön `openapi`/Swagger-dokumentáció és a robots.txt állapota ebben a körben nem lett bizonyítva; a robots.txt közvetlen megnyitását a böngésző kliensblokkolta, ezért ez `Q`, nem pedig engedély vagy tiltás.

## 3. P1K 22-mezős visszamappelés

A teljes gépi mapping: [oeny_public_field_mapping.csv](../../registry/oeny_public_field_mapping.csv).

Coverage:

- **Teljesen elérhető (`PUBLIC_OBS_AVAILABLE`): 0 mező**;
- **Részlegesen elérhető (`PUBLIC_PARTIAL`): 1 mező** – `reference_year`, mert a hivatalos Lechner-leírás szerint a tanúsítás dátuma nyilvánosan lekérdezhető, de a P1K-s, biztonságos és reprodukálható bulk/pilot-mapping nem bizonyított;
- **Nem elérhető P1K-kompatibilis publikus gépi csatornán (`NOT_PUBLICLY_AVAILABLE`): 20 mező**;
- **Bizonytalan (`UNCERTAIN`): 1 mező** – `pii_check`, mert a nyilvános felület cím- és HET-orientált, P1K szerinti PII-pass payloadot nem figyeltünk meg.

A 22 mezőből tehát **0 teljes, 1 részleges, 20 nem elérhető és 1 bizonytalan**. A részleges vagy bizonytalan mező nem használható kész P1K-pilotmezőként.

Különösen nem bizonyított publikus gépi mezőként: building category, construction period band, heated floor area band, heating system quality, heating energy carrier, current emitter, emitter evidence, supply/return temperature, temperature basis, S1 demand reduction, hydraulic/electrical/permit readiness és evidence_pages.

## 4. Verzió- és forráskorlát

Az aktuális nyilvános UI footerje `v3.0.13127`, miközben a repóban auditált hivatalos GitLab-dokumentáció `v3.0.14801`. A nyilvános UI és a dokumentáció közötti sémaverzió-azonosság nem bizonyított; ezért a repository schema és a publikus runtime payload nem keresztezhető automatikusan.

## 5. Incremental ingest döntés

Az [incremental ingest feasibility contract](P1M_OENY_INCREMENTAL_INGEST_FEASIBILITY.md) szerint nincs bizonyítva:

- stabil, nem személyes rekordazonosító;
- updated_since/cursor vagy módosítási napló;
- determinisztikus új/módosított/törölt rekord-kezelés;
- rate-limit, freshness vagy bulk-licenc;
- nyilvános P1K-kompatibilis rekord-schema.

Ezért ingestion szolgáltatás, snapshot-építés vagy automatikus frissítő folyamat most nem építhető.

## 6. Reprezentativitási és readiness-korlát

Még teljes publikus rekord-hozzáférés esetén sem következne automatikusan:

- OÉNY public records → országos hőleadó-megoszlás;
- OÉNY public records → országos S1 demand-reduction hatás;
- OÉNY public records → országos S2 műszaki readiness.

Ehhez külön bizonyítani kellene a tanúsítvány-lefedettséget, kiválasztási torzítást, időbeli és területi reprezentativitást, valamint az adott readiness-mező mérési definícióját. A B02 fail-closed szabályok változatlanok: S0 csak bizonyítottan, S1 nem nyitható meg OÉNY-recordból, S2 csak explicit műszaki evidence alapján.

## 7. Döntés

**`PATH_B_HYBRID`**

Indok: van hivatalos UI által használt, autentikáció nélküli gépi keresési csatorna, és a referenciaévhez kapcsolódó tanúsítási dátum részlegesen nyilvános. Ugyanakkor a P1K 22 mezőből egy sem bizonyított teljes, P1K-kompatibilis publikus gépi forrásként; ezért célzott Lechner-adatkérés továbbra is szükséges a hiányzó és részleges mezőkre.

A P1L nem küldhető ki automatikusan. A P1L maradjon `HOLD_PUBLIC_ACCESS_AUDIT` alatt, és csak a hiányzó/részlegesen bizonyított P1K-mezők jogszerű, anonimizált, strukturált átadhatóságára kérdezzen rá. A nyilvános UI-végpontot nem használjuk bulk-pilot vagy országos adatforrásként.

## 8. Források és gépi artefaktumok

- [OÉNY public endpoints](../../registry/oeny_public_endpoints.csv)
- [P1K public field mapping](../../registry/oeny_public_field_mapping.csv)
- [Incremental ingest feasibility](P1M_OENY_INCREMENTAL_INGEST_FEASIBILITY.md)
- [Lechner – Közérdekű adatok](https://lechnerkozpont.hu/oldal/kozerdeku-adatok)
- [Lechner – E-építésügy / OÉNY](https://lechnerkozpont.hu/oldal/e-epitesugy)
- [Lechner – hiteles energiatanúsítványok nyilvános alapadatai](https://lechnerkozpont.hu/cikk/hiteles-energiatanusitvanyok-millios-nagysagrendben)
- [OÉNY e-tanúsítás public UI](https://www.oeny.hu/oeny/e-tanusitas/)

## 9. Műveleti nyilatkozat

Az audit során nem történt e-mail, e-Papír vagy más külső adatbekérés. Nem épült ingestion szolgáltatás, nem történt tömeges scraping és nem készült mesterséges public-response schema; a `schemas/oeny_public_response.schema.json` fájl ezért szándékosan nem jött létre.
