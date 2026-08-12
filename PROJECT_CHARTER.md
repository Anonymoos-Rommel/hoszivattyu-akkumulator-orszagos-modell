# Nyilvános projektalapító okirat

## Küldetés

A projekt célja egy Magyarországra szabott, auditálható döntési modell létrehozása, amely megmutatja, hogy egy országos hőszivattyú- és háztartásiakkumulátor-program milyen feltételek mellett műszakilag megvalósítható, pénzügyileg fenntartható és társadalmilag igazságos.

A kutatás nem a program előzetes igazolására vagy cáfolására szolgál. Kedvezőtlen eredményt is változtatás nélkül kell közölni, az eredményt meghatározó feltételekkel és bizonytalanságokkal együtt.

## Kötelező eredménycsaládok

- forrásolt kutatási jelentés;
- géppel olvasható forrás-, változó- és képlet-regiszter;
- éves és órás fizikai forgatókönyvek;
- háztartási és államháztartási cash-flow;
- aktuális finanszírozási forrástérkép;
- finanszírozási konstrukciók és stressztesztek;
- makrogazdasági, foglalkoztatási, klíma- és egészségügyi hatások;
- alkalmazásra kész input/output- és függőségi szerződés;
- blokkonkénti Model Readiness értékelés.

## Függőségi sorrend

`B01+B02+B03+B04 -> B05+B06+B07 -> B08+B09+B10+B11 -> B12+B13+B14 -> B15 -> B16+B17+B18+B19 -> B20`

A B15 finanszírozási stratégia nem kezdhető el addig, amíg B12, B13 és B14 számszerű, forrásolt kimenete nem áll rendelkezésre. A végleges interaktív alkalmazás csak a B01–B19 modell-szerződéseinek stabilizálása és a B20 interfész rögzítése után készülhet.

## Bizonyítottsági státuszok

- `OBS` — megfigyelt tényadat;
- `DER` — forrásadatból származtatott érték;
- `ASS` — modellezési feltételezés;
- `SCN` — forgatókönyv-paraméter;
- `POL` — szakpolitikai döntési változó;
- `Q` — nyitott kérdés vagy hiányzó bizonyíték.

## Minőségi kapuk

- Minden kritikus bemenethez lehetőség szerint két független ellenőrzés tartozik.
- A történeti és az aktuális adatok nem keverhetők.
- Minden képletet dimenzió- és egységellenőrzésnek kell alávetni.
- A program nélküli baseline és a program inkrementális hatása elkülönül.
- Ugyanaz a gazdasági esemény nem számolható el több haszonkategóriában.
- Hiányzó adat helyett nyitott kérdés és adatbeszerzési terv készül.
