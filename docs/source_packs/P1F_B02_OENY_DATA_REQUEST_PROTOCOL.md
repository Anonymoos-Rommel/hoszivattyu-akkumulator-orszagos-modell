# P1-F forráscsomag: OÉNY adatkérés és mintafeldolgozás

Állapot: **csomag elkészült; elküldés és adatátvétel még nincs**

Ellenőrzés napja: **2026-08-12**

Kapcsolódó kérdés: `Q-B02-004`

## Eredmény

A P1-E mezőaudit után elkészült a következő végrehajtható, de emberi jóváhagyáshoz kötött réteg:

- személyes adat nélküli [Lechner/OÉNY adatigénylési tervezet](../data_requests/P1F_OENY_DATA_REQUEST_DRAFT.md);
- adatminimalizáló, fail-closed [mintafeldolgozási és kettős vak annotációs protokoll](../protocols/P1F_OENY_SAMPLE_PROCESSING_PROTOCOL.md);
- gépi [annotációs séma](../../schemas/oeny_heat_emitter_annotation.schema.json);
- standard library alapú [JSONL-validátor](../../tools/validate_oeny_annotations.py) és tesztek.

## Miért lépcsőzetes a kérés?

A nyilvános OÉNY-séma alapján nem igazolt normalizált jelenlegi hőleadótípus vagy előremenő/visszatérő hőmérséklet. Ugyanakkor a számítási PDF személyes vagy ingatlanra visszavezethető adatot tartalmazhat, és a teljes tanúsítványállomány nem reprezentatív lakásminta. Ezért az első kérés csak a legkisebb kockázatú, már meglévő információkat célozza: adatszótárat, mezőkitöltöttséget, aggregált leltárt és anonimizált strukturált pilotot.

PDF csak akkor léphet be, ha:

1. a normalizált mező hiánya megerősített;
2. az adatgazda írásban rögzíti a jogszerű átadást és felhasználási feltételeket;
3. a biztonságos csatorna, megőrzés és törlés szabálya ismert;
4. a dokumentum szolgáltatói és helyi redakciós ellenőrzésen átmegy;
5. Joseph külön jóváhagyja a dokumentumkaput.

## Bizonyítékstátusz

- A Lechner hivatalos csatornái és igénylőlapjának mezői: `POL`, P1 hivatalos forrás.
- Az Infotv. benyújtási és határidőszabályai: `POL`, P1 jogforrás.
- Az 500–1000 rekordos tervezési tartomány: `SCN`, nem szolgáltatói ígéret és nem statisztikai optimumméret.
- A minőségküszöbök: `PROPOSED_POL`, Joseph döntéséig nem kötelező projektpolitika.
- OÉNY hőleadó- vagy hőmérséklet-eloszlás: továbbra is `Q`.

## Nyitott kapuk

1. Joseph jóváhagyja vagy módosítja a küldendő szöveget, az igénylő személyét/szervezetét és a csatornát.
2. A végleges, személyes adatot tartalmazó példány kizárólag nem nyilvános helyen készül el.
3. A válasz után külön döntés készül költségről, licencről, adatkezelésről és a második szakaszról.
4. Nincs országos extrapoláció reprezentativitási kapu nélkül.

## Hivatalos források

1. [Lechner – Közérdekű adatok](https://lechnerkozpont.hu/oldal/kozerdeku-adatok).
2. [Lechner hivatalos igénylőlap](https://lechnerkozpont.hu/doc/igenylolap.pdf).
3. [Lechner közadat-igénylési eljárásrend](https://lechnerkozpont.hu/sites/default/files/doc/kozerdeku-es-a-kozerdekbol-nyilvanos-adatok-elektronikus-kozzetetelenek-valamint-a-megismeresukre-iranyulo-igenyek-teljesitesenek-rendje.pdf).
4. [2011. évi CXII. törvény](https://njt.hu/jogszabaly/2011-112-00-00), különösen 28–29. §.

## Nem következik ebből

- nincs elküldött vagy befogadott adatigénylés;
- nincs Lechner-vállalás, adatátadás vagy költségbecslés;
- nincs valós OÉNY-rekord vagy dokumentum a repóban;
- nincs igazolt országos hőleadó-megoszlás;
- nincs B02 alkalmassági eredmény.
