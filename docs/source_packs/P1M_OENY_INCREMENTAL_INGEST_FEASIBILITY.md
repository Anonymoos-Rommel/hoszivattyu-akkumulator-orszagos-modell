# P1-M OÉNY incremental ingest feasibility contract

**Állapot:** `FEASIBILITY_ONLY / NO INGESTION`

Ez a dokumentum nem engedélyez ingestion szolgáltatást, scrapinget, tömeges lekérdezést vagy adatbázis-építést. A cél annak rögzítése, hogy a jelenleg bizonyított publikus UI-csatorna alkalmas-e későbbi, jogszerű és reprodukálható frissítésre.

## Vizsgált csatorna

Az e-tanúsítás hivatalos nyilvános felülete a böngészőből egy POST XHR-t hív:

`https://www.oeny.hu/oeny/e-tanusitas/api/internal/cert-list/search`

Kérés: settlement, streetName, streetType és houseNumber JSON-mezők. A kontrollált, nem valós és nem személyes ZZZTEST/ZZZTEST keresés HTTP 200 és üres JSON-tömb választ adott. A végpont külön public API-dokumentációban nem volt igazolva; a publikus UI hívásaként lett megfigyelve.

## Incremental feasibility

| Követelmény | Megfigyelés | Feasibility |
|---|---|---|
| Módosítási/kiadási dátum | A kontrollált üres válaszban nem volt rekord-metaadat; a UI-leírás tanúsítási dátumot említ, de nem adott bulk feedet. | `Q / PARTIAL` |
| Stabil, nem személyes rekordazonosító | A P1K-hoz szükséges random pilot ID nincs a megfigyelt csatornában; HET- vagy címazonosító használata nem elfogadható. | `NO` |
| updated_since vagy cursor | Nem volt megfigyelhető ilyen paraméter vagy dokumentáció. | `NO_EVIDENCE` |
| Új rekord determinisztikus felismerése | Címmező-alapú keresésből nincs országos újrekord-jelző vagy snapshot-azonosító. | `NO` |
| Módosított/törölt rekord kezelése | Nincs változásnapló, tombstone, snapshot vagy cursor bizonyítva. | `NO_EVIDENCE` |
| Indokolt lekérdezési gyakoriság | Nincs hivatalos rate-limit/freshness/automatizálási feltétel. | `Q` |
| Snapshot/hash/lineage | Helyi audit-séma megtervezhető, de valós adat nélkül nem implementálható és nem írható elő szolgáltatói feltételként. | `POL / FEASIBLE_LATER` |
| Bulk használat | Tilos ebben a fázisban; a UI-endpoint közvetlen tömeges hívása és scrapingje nem igazolt jogszerűnek. | `NO` |

## Későbbi, csak új jóváhagyással alkalmazható minimális contract

Ha a Lechner később írásban jogszerű, gépi és reprodukálható adatcsatornát biztosít, az ingest csak az alábbiak megléte után tervezhető:

1. dokumentált endpoint- és licencfeltétel;
2. P1K-kompatibilis, nem személyes rekordazonosító;
3. explicit reference period és módosítási/snapshot-mechanizmus;
4. schema- és kódtábla-verzió;
5. rate-limit és minimális lekérdezési gyakoriság;
6. PII- és ritka-cellás disclosure-control;
7. raw quarantine, SHA-256 manifest, forrás- és lekérdezési napló;
8. törlési, retention- és reprodukciós feltételek;
9. külön Joseph-approval az első valós intake előtt.

E feltételek hiányában nincs automatikus frissítés, nincs snapshot-építés és nincs saját nyilvános adatbázis.
