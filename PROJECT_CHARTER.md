# Nyilvános projektalapító okirat

## Küldetés

A projekt célja egy Magyarországra szabott, auditálható döntési modell létrehozása, amely egy többéves, lépcsőzetes országos hőszigetelési, hőszivattyú- és háztartásiakkumulátor-portfóliót vizsgál. A modellnek meg kell mutatnia, hogy az egyes háztartási fázisok milyen műszaki, hálózati, pénzügyi, fiskális és társadalmi feltételek mellett hajthatók végre, és mikor kell megállni bizonyítékhiány miatt.

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
- éves háztartási állapotállomány és projektportfólió-pálya;
- baseline és programhoz rendelhető inkrementális infrastruktúra-ledger;
- regionális readiness- és fiskális headroom-kimenet;
- blokkonkénti Model Readiness értékelés.

## Függőségi sorrend

`B01+B02+B03+B04 -> B05+B06+B07 -> B08+B09+B10+B11 -> B12+B13+B14 -> B15 -> B16+B17+B18+B19 -> B20`

A B15 finanszírozási stratégia nem kezdhető el addig, amíg B12, B13 és B14 számszerű, forrásolt kimenete nem áll rendelkezésre. A végleges interaktív alkalmazás csak a B01–B19 modell-szerződéseinek stabilizálása és a B20 interfész rögzítése után készülhet.

## V1.2 végrehajtási alap

A kanonikus egység nem az egyszeri háztartási telepítés, hanem az `S0`–`S5` állapotgépen átvezetett beavatkozás az éves országos projektportfólióban. Az éves kiválasztás csak explicit prioritási komponensekkel, kemény korlátokkal, magyarázattal és bizonyíték-státusszal történhet. A V1.2 szerződés részletei: [`docs/methodology/v12_portfolio_transition_contract.md`](docs/methodology/v12_portfolio_transition_contract.md).

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
