# P1-I: B02 → V1.2 readiness-átadási híd

Állapot: **CONTRACTED BRIDGE – országos alkalmasság és readiness még nincs kiszámítva**

Ez a csomag azt rögzíti, hogy a jelenlegi B02 kimenetekből mi adható át a V1.2 `S0`–`S2` állapotkapukhoz. Nem képez új lakásszámot, nem gyárt teljes archetípus-jointot, és nem minősít automatikusan hőszivattyúra alkalmasnak egyetlen lakást sem.

## Forrásalap

A híd a két projektalapító belső dokumentum követelményeit alkalmazza:

- `Hoszivattyu_akkumulator_program_Codex_kutatasi_prompt_V1.2.docx`;
- `Hoszivattyu_akkumulator_program_javaslat_V1.1_munkapeldany.docx`.

A B02 tény- és modellalapját a KSH V67 WBL-projekciók, a KSH 2025 energetikai modellkimenetei, a 2015-ös épülettípus-proxy és az OÉNY-audit dokumentumai adják. A teljes lineage a meglévő B02 source packekben és a registryben van.

## Kapuértékelés

| V1.2 kapu | B02-ból jelenleg átadható | Státusz | Amit nem szabad levezetni |
|---|---|---|---|
| `S0 BASELINE_AUDITED` | terület, lakottság, kor, falazat, alapterület-kategória, komfort, fűtési mód, tüzelőanyag, meglévő HOSZIV-jelző, energetikai modellkimenet és lefedettség | **PARTIAL** | a meglévő HOSZIV nem műszaki alkalmasság; a külön WBL-projekciók nem kapcsolhatók össze |
| `S1 DEMAND_REDUCED` | előzetes energetikai baseline/archetípusos hőigény-jelölt | **BLOCKED** | utólagos keresletcsökkentési hatás, mért megtakarítás vagy „nem szükséges” állapot |
| `S2 TECHNICALLY_READY` | readiness-hez szükséges hiánymezők és kizárási okok listája | **BLOCKED** | hőleadó, hőfoklépcső, hidraulika, villamos csatlakozás vagy engedély megléte |

Az egyes mezők gépi állapota a [`registry/b02_readiness_bridge.csv`](../../registry/b02_readiness_bridge.csv) fájlban van. A hídban szereplő `Q` és `GAP` nem nulla és nem automatikus kizárás; azt jelenti, hogy a kapuhoz bizonyíték hiányzik.

## S0: baseline-audit szabály

Egy B02-re épülő S0-jelölt csak akkor adható tovább, ha a rekord vagy aggregátum:

1. rögzíti a kanonikus területi és lakottsági grain-t;
2. minden mezőn megőrzi az OBS/DER/ASS/MODELLED/Q lineage-et;
3. külön jelöli a WBL011, WBL017 és energetikai projekció eredetét;
4. kimutatja a nem visszaadott kombinációkat és a lefedetlenségi maradékot;
5. nem keresztbeszorozza a külön margókat.

Az `S0` itt auditált **jelölt** állapotot jelent, nem programjogosultságot. A jogi, műszaki és gazdasági jogosultság külön downstream szabály.

## S1: keresletcsökkentési kapu

B02 jelenlegi kimenetei csak kiinduló energetikai becslést adnak. Az `S1 DEMAND_REDUCED` kapuhoz új, fázishoz kötött bizonyíték kell:

- beavatkozás azonosítója és befejezési ideje;
- előtte/utána azonos definíciójú hőigény vagy energiafogyasztás;
- mérési vagy dokumentált számítási módszer;
- bizonytalanság és az elkerült duplaelszámolás;
- ha a fázis nem szükséges, ennek külön műszaki bizonyítéka.

Ezek hiányában a rekord `BLOCKED_DATA_GAP`, nem `S1`.

## S2: műszaki readiness kapu

Az OÉNY-audit alapján jelenleg nincs bizonyított, országosan aggregálható mező a jelenlegi hőleadó típusára vagy a tervezési előremenő/visszatérő hőmérsékletre. Ezért a következő mezők mind `Q/GAP`:

- hőleadó típusa és beépített kapacitása;
- tervezési hőfoklépcső;
- hidraulikai topológia és szabályozhatóság;
- villamos csatlakozás, mérés és szükséges hálózati kapacitás;
- engedélyezési és kivitelezési readiness.

Fűtési mód, tüzelőanyag, épülettípus-proxy vagy meglévő hőszivattyú-jelző alapján egyik mező sem imputálható.

## Következő bizonyítási sorrend

1. OÉNY adatszótár, mezőkitöltöttség és anonimizált strukturált pilot — Joseph jóváhagyási kapujával;
2. ha nincs reprodukálható hőleadó/hőfokmező, rétegzett reprezentatív műszaki felmérés terve;
3. S1 előtte/utána mérési és intervention-eredmény szerződés;
4. regionális villamos és engedélyezési readiness mezők B08/B10/B18 felé;
5. csak ezek után B02 archetipusos jelöltek átadása az intervention catalog számára.

## Tiltott kimenetek

- `VAR-B02-ELIGIBLE-DWELLINGS` nem tölthető ki a jelenlegi B02-adatokból;
- `HOSZIV=1` nem válhat `S2` vagy `S3` állapottá;
- WBL011/WBL017/energetikai margók keresztbeszorzása nem képezhet `DER` vagy `OBS` teljes jointot;
- az S1 vagy S2 hiányzó kapuja nem kezelhető nulla költségként vagy automatikus kizárásként;
- a híd nem adhat éves portfólió-prioritást és nem dönthet támogatási összegről.

## Következő kapu

A B02 readiness-híd számszerű kapuja csak akkor nyitható, ha az új bizonyítékokhoz forrás, snapshot/lineage, grain, lefedettség és bizonytalanság tartozik, valamint a megfelelő Q-kérdések lezárása megtörténik.
