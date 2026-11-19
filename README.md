# Hőszigetelés + hőszivattyú + akkumulátor országos modell

**Helyzetkép frissítve: 2026. november 19.**

Nyilvános, forrásolt és reprodukálható kutatás arról, hogy **milyen feltételekkel lenne megvalósítható Magyarországon egy ütemezett lakossági energetikai korszerűsítési program**. A hőszigetelést, a hőszivattyúkat és az akkumulátoros tárolást háztartási és országos szinten is vizsgáljuk, a program nélküli alapforgatókönyvhöz képest.

## Mit vizsgál a projekt?

| Terület | Fő kérdés |
| --- | --- |
| **Épületek és energia** | Mely épülettípusoknál milyen beavatkozás jöhet szóba, mennyi energiát és földgázt válthat ki, és hogyan alakul az áramigény a hideg, illetve a csúcsidőszakokban? |
| **Háztartási számlák és finanszírozás** | Hogyan változik a gáz- és villanyszámla, ha a beruházás, az üzemeltetés és a hiteltörlesztés is számít? Milyen feltételekkel nem nő a háztartás pénzügyi terhe a belépéstől kezdve? |
| **Állami költségvetés és támogatás** | Mit jelentene a rezsitámogatás igazoltan átirányítható részének fokozatos felhasználása a belépők korszerűsítésére, miközben a programon kívül maradók támogatása megmarad? Mi a hatása az éves állami kiadásokra és adóbevételekre, beleértve az áfát? |
| **GDP, foglalkoztatás és bérek** | Mennyi hazai hozzáadott érték és nettó munkahely keletkezhet az import és a más tevékenységekből kiszoruló munka figyelembevételével? Hogyan változhat a munkaerőigény és a bértömeg? A GDP-hatás előjelét nem rögzítjük előre. |
| **Képzés és kivitelezés** | Hány szakember, munkaóra és kivitelezői csapat kell, mekkora a régiók és szakmák kapacitása, és milyen képzési utánpótlással tartható az ütem? |
| **Villamos hálózat és tárolás** | Hogyan hat a program a helyi és országos csúcsterhelésre? Mikor képes a tárolás a napelemes többletet későbbre áttenni, és ezt milyen hálózati korlátok mellett tudjuk igazolni? |
| **Klíma, levegőminőség és egészség** | Mennyivel változik a fosszilis energiaigény, a kibocsátás és a helyi légszennyezés, és milyen egészségi hatások becsülhetők az alkalmazott adatokból? |

A részletes kutatási kérdések és a módszertani korlátok a [projektalapító okiratban](PROJECT_CHARTER.md) és a [B01–B20 kutatási tervben](registry/v1_research_plan.json) követhetők.

## Hol tart a munka?

- **A nyilvános főágban** elérhető a módszertan, a modulok és források nyilvántartása, valamint több visszaellenőrzött részadat és részmodell. Például a lakott lakásállomány feldolgozása és a hazai gazdasági ágak történeti adatai már szerepelnek a [modulstátuszokban](registry/module_status.csv). Ezek önmagukban nem országos programeredmények.
- **Fejlesztés alatt** áll a B01–B19 modulok összekapcsolása. Egy elkülönített fejlesztési változaton az integrációs kódellenőrzés már lefutott; ez nem azonos a nyilvános főágba emeléssel vagy az országos eredmények igazolásával. A B20 végleges alkalmazási interfészének kidolgozása még nem indult el.
- **Még hiányzik** többek között ugyanazon háztartás azonos fogyasztási időszakra szóló gáz- és villanyelszámolása, az átcsoportosítható állami forrás igazolása, összeillő helyi hálózati mérések és régiós kivitelezési kapacitásadatok. Ezért nincs még igazolt országos beruházási ütem, megtakarítási, GDP- vagy foglalkoztatási eredmény.

## V1 végrehajtási terv

A jóváhagyott adatbeszerzési és feltételes megvalósíthatósági munka menete: [V1 végrehajtási szerződés](docs/methodology/v1_evidence_feasibility_execution.md). A [58 munkaszelet jegyzéke](registry/v1_research_plan.json) kutatási állapotot követ, nem bizonyítottságot helyettesít; a meglévő E2 és merge-szabályok változatlanok.

## Alapelv

Előbb a fizika és az adatok, utána a pénzügy. Előbb a kanonikus modell, utána a kommunikáció és az interaktív alkalmazás.

A jelenlegi program-egység egy fázisokon átvezetett háztartási beavatkozás az éves portfólióban, nem egyszeri telepítés. Az állapotgép és a portfólió-kapuk szerződése: [`docs/methodology/v12_portfolio_transition_contract.md`](docs/methodology/v12_portfolio_transition_contract.md).

Az országos modellhez nem követelmény minden magyar lakás teljes egyedi műszaki dokumentációja. Ahol teljes adminisztratív/populációs adat nincs, reprezentatív megfigyelt minta vagy validált, kalibrált többforrású inferencia használható, kötelező bizonytalanság- és érzékenységkezeléssel. Ez nem helyettesíti a konkrét háztartás állapotátmenetéhez szükséges record-level bizonyítást. Részletek: [`docs/methodology/population_inference_policy.md`](docs/methodology/population_inference_policy.md).


Adatforrás-hiány esetén a projekt E1/E2/E3 evidenciaszintet használ. Egy materialis E2 tétel egyetlen védhető `PROVISIONAL_BASE` értékkel engedheti a központi modell folytatását, miközben az exact primer bizonyíték validation debtként nyitva marad; E3 esetén nincs engedélyezett kanonikus base, ha az input szükséges. A source-gap bizonytalanságot nem alakítjuk automatikus low/base/high Cartesian forgatókönyvtérré. Részletek: [`docs/methodology/evidence_tier_and_validation_debt_policy.md`](docs/methodology/evidence_tier_and_validation_debt_policy.md).

Minden érdemi számnak visszavezethetőnek kell lennie:

1. forrásra vagy explicit feltételezésre;
2. kanonikus változóazonosítóra;
3. mértékegységre;
4. képletre vagy transzformációra;
5. érvényességi tartományra;
6. az eredményt használó modulokra.

## Projektfelépítés

- `modules/` — a B01–B20 kutatási modulok szerződése és státusza;
- `registry/` — forrás-, adatkészlet-, archetípusdimenzió-, változó-, képlet-, kérdés- és modulregiszter;
- `registry/` — a V1.2 állapot-, beavatkozás-, prioritás-, portfólió-, readiness-, baseline-, inkrementális CAPEX- és fiskális headroom-sablonok;
- `data/` — adatkezelési és reprodukciós szabályok;
- `model/` — a későbbi számítási motor;
- `scenarios/` — forgatókönyvek és stressztesztek;
- `docs/` — módszertan és generált jelentések;
- `app/` — a B20 lezárása után elkészülő alkalmazás;
- `tests/` és `tools/` — automatikus szerződés- és minőségellenőrzés.

## Közreműködés

A repository nyilvánosan olvasható. Külső közreműködők Issue, Discussion vagy forkból indított Pull Request formájában tehetnek javaslatot. A kanonikus repository írási és merge-jogosultságát Joseph gyakorolja; Aion és Codi kizárólag Joseph felhatalmazásával dolgozik. Részletek: [GOVERNANCE.md](GOVERNANCE.md) és [CONTRIBUTING.md](CONTRIBUTING.md).

## Publikációs megjegyzés

A belső kiinduló dokumentumok nem részei az első nyilvános kiadásnak. Publikálásuk csak külön tartalmi, adatvédelmi és licencellenőrzés után történhet.

## Licencelés

A repository osztott licencelést használ:

- a szoftverkód főszabály szerint **GNU AGPL-3.0-only**;
- a saját dokumentáció, módszertan, jelentések és egyéb eredeti kutatási anyag főszabály szerint **CC BY-SA 4.0**;
- a harmadik féltől származó adatok és tartalmak az eredeti forrás licenc- és felhasználási feltételei alatt maradnak;
- a repository-ban létrehozott adatkészletek licencét külön, az adott adatcsomag metadata- vagy licencbejegyzésében kell rögzíteni.

A részletes hatókört és elsőbbségi szabályokat a [`LICENSE`](LICENSE) fájl tartalmazza.

## Infó: rendszercélok, E2 akkumulátoros döntések és koordinált töltés

A [B07/B12 szakmai SCN-kontraktus](docs/checkpoints/B07_E2_OWNER_DECISIONS_20261026.md) leírja az országos termelés–igény–tárolás–hálózat vizsgálati célt, a modulkapcsolatokat és a kritikus időszakok adatfeltételeit. Elkülöníti a háztartás és a hálózat szerepét, a 10 kWh-s forgatókönyvet az eredeti forráshoz kötött referenciától, valamint a koordinált töltés feltételeit a tényleges szolgáltatási jogosultságtól. A helyi műszaki eredmények nyilvános hozzáférése nem igazolt. A dokumentáció nem módosít végrehajtható bemenetet vagy readiness-státuszt.
