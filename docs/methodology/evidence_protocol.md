# Forrás- és bizonyítási protokoll

## Forráshierarchia

- `P1` — elsődleges hivatalos forrás;
- `P2` — elsődleges piaci vagy rendszerüzemeltetői forrás;
- `P3` — peer-reviewed vagy elismert szakmai másodlagos forrás;
- `P4` — sajtó, aggregátor vagy tájékozódási forrás.

Kritikus kanonikus adat nem állhat kizárólag P4 forráson. P1/P2 adat rendelkezésre állása esetén P4 csak sanity check vagy kutatási jelzés lehet.

## Kötelező mezők

Minden forrásrekord tartalmazza az intézményt, címet, URL-t, publikációs dátumot, lekérési dátumot, vonatkozási időszakot, forrásszintet, bizonyítékstátuszt és felhasználási megjegyzést.

## Eltérő források

Eltérés esetén egyik adat sem tüntethető el magyarázat nélkül. Rögzíteni kell az eltérést, a lehetséges módszertani okot és a modellben használt tartományt vagy döntési szabályt.

## Származtatott érték

A `DER` értékhez kötelező a bemeneti változóazonosítók, a képlet, a konverzió és a kimeneti mértékegység rögzítése.


## Országos populációs inferencia

A teljes populációs mikroadat nem általános előfeltétele egy országos becslésnek. Az adott claimhez a legjobb elérhető bizonyítási út választandó:

1. `EXHAUSTIVE_ADMIN_CENSUS` — teljes vagy közel teljes adminisztratív/népszámlálási lefedettség;
2. `REPRESENTATIVE_OBSERVED_SAMPLE` — dokumentált, megfelelően rétegzett/súlyozott megfigyelt minta;
3. `CALIBRATED_MULTI_SOURCE_INFERENCE` — több forrásból, ismert populációs kontrollokra kalibrált statisztikai/modell-alapú becslés;
4. `BOUNDED_ENGINEERING_VALIDATION` — valós műszaki esetek és mérések a fizikai kapcsolat, tartomány vagy módszer validálására;
5. `ASS/SCN` — explicit feltételezés vagy forgatókönyv, ha a populációs evidencia nem elégséges.

Az 1–3. szint alkalmas lehet országos megoszlás, prevalencia vagy aggregált mennyiség becslésére. A 4. szint önmagában nem bizonyít országos gyakoriságot. Az 5. szint nem állítható be megfigyelt populációs tényként.

Kanonikus szabály:

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

Egy országos inferencia minimális dokumentációja: célpopuláció, mintavételi/szelekciós keret, referencia-időszak, mintanagyság és ha releváns effektív mintanagyság, súlyozás/kalibráció, hiányzó és kieső rekordok kezelése, validációs kontrollok, becslési módszer, bizonytalanság és szerkezeti érzékenység.

A mintából számított országos kimenet nem válik automatikusan `OBS`-szá. Direkt survey-weighted becslés tipikusan `DER`; modell-alapú imputáció/kalibráció `MODELLED` vagy az adott modul szerinti explicit model-output státusz.

## Országos inferencia != record-level döntés

Populációs becslés nem használható egy konkrét épület, háztartás, mérési pont, hálózati csomópont, engedély vagy szerződés `PASS/FAIL` döntésének helyettesítésére. Ilyen döntéshez az adott rekordhoz vagy helyszínhez kötött bizonyíték szükséges.

Ezért például:
- országos emitter-megoszlás becsülhető reprezentatív műszaki mintából;
- egy adott lakás 45 °C-os alkalmassága nem inferálható pusztán a populációs arányból;
- országos DSO-korlátkép részben becsülhető térbeli mintázatokból, de egy konkrét alállomás headroomja nem;
- jogi, tarifa- és szerződéses feltételek nem statisztikai prevalencia-kérdések, ott a hatályos forrás az authority.

## Bizonytalansági kimenetek

Ahol a populációs inferencia érdemben befolyásolja az országos eredményt, a pontbecslés mellett kötelező legalább egy bizonytalansági kimenet. A forrás és módszer függvényében ez lehet konfidenciaintervallum, bootstrap/intervallumbecslés, vagy `P10/P50/P90` eloszlási kimenet. A modell nem közölhet indokolatlan tizedesjegy-pontosságot olyan változóra, amely mintából vagy kalibrált becslésből származik.
