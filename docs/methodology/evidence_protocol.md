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
