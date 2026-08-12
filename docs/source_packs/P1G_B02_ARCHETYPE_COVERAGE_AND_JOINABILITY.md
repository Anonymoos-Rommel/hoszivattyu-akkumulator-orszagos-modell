# P1-G forráscsomag: B02 archetípus-cellalefedettség és összekapcsolhatóság

Állapot: **részgrainen lezárva; teljes közös archetípuseloszlás nem igazolt**

Ellenőrzés napja: **2026-08-12**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

## Döntési eredmény

A meglévő B02 adatcsomag három eltérő, önmagában használható, de egymással nem automatikusan összekapcsolható részgrainen áll:

1. a KSH energetikai publikáció 16 épülettípus × építési időszak cellát és cellánként 59 primerenergia-bint ad, összesen 944 bint;
2. a 2015-ös lakásfelmérésből 2022-re vetített `ASS` proxy csak négy településtípus × két épülettípus, vagyis 8 cella;
3. a WBL011 és WBL017 sémája több lakásjellemző közös megfigyelését teszi lehetővé, de a teljes levélkódos cellatábla még nincs materializálva a repóban.

Hőleadó- és tervezési hőmérsékletadat továbbra sincs. Ezért nem áll rendelkezésre teljes közös eloszlás a terület × épülettípus × építési kor × falazat × alapterület × komfort × fűtés × tüzelőanyag × primerenergia × hőleadó × hőmérséklet grainen.

## Energetikai cellalefedettség

A 16 KSH-modellezett épülettípus × építési időszak cella mindegyike pozitív lakásszámú. A publikált energiaigény-binek összege 4 575 790 lakás (`DER` a `MODELLED` cellákból).

- legkisebb benchmarkcella: 22 145 lakás;
- legnagyobb benchmarkcella: 902 651 lakás;
- publikált energiaigény-binek: 944;
- pozitív binszám: 864;
- nulla lakásszámú binszám: 80.

A 80 nulla bin nem hiányzó rekord: a teljes 2 × 8 × 59 téglalap része, amelyben a publikált modell az adott energiaintervallumhoz nulla lakást rendel. A jelentés nem nevez ki önkényes „ritka” küszöböt. Ehelyett minden cellához pontos lakásszámot, teljesállomány-részesedést, rangot, kumulatív részesedést, pozitív/nulla binszámot és pozitív energiaintervallumot közöl.

Gépi kimenet: [`b02_archetype_cell_coverage_2022.csv`](../../data/processed/b02/b02_archetype_cell_coverage_2022.csv).

## Összekapcsolhatósági mátrix

| Részgrain | Státusz | Mit szabad összekapcsolni? | Mit tilos hozzákapcsolni új bizonyíték nélkül? |
| --- | --- | --- | --- |
| WBL011 közös cella | `OBS`, szerződött, még nem materializált | terület, kor, falazat, alapterület, komfort, fűtési mód, tüzelőanyag ugyanazon API-válaszban | épülettípus, primerenergia, hőleadó, hőmérséklet |
| WBL017 közös cella | `OBS`, szerződött, még nem materializált | terület, kor, falazat, alapterület, komfort, kombinált fűtés/tüzelőanyag, meglévő hőszivattyú | műszaki alkalmasság, hőleadó, hőmérséklet |
| KSH energetikai eloszlás | `MODELLED`, materializált | épülettípus × építési időszak × primerenergia-bin | WBL földrajzi, falazati, alapterületi, komfort- vagy fűtési alcella |
| Épülettípus-proxy | `ASS`, materializált | településtípus × épülettípus összesen | vármegye, kor, falazat, alapterület, komfort, fűtés vagy tüzelőanyag szerinti alcella |
| OÉNY hőleadó/hőmérséklet | `Q`, nincs adat | semmi a P1-F kapu teljesítéséig | fűtési módból, tüzelőanyagból, javaslati mezőből vagy referencia 55/45 °C-ból való imputáció |
| Teljes B02 archetípus | `Q`, nem azonosított | csak új közös adat vagy jóváhagyott, kalibrált statisztikai modell után | külön margók dokumentálatlan függetlenségi keresztbeszorzása |

Gépi szerződés: [`b02_archetype_joinability_2022.csv`](../../data/processed/b02/b02_archetype_joinability_2022.csv).

## Miért nem készül teljes archetípustábla?

Ha például a településtípusos épülettípus-arányt minden építési korra, falazatra és fűtési módra változatlanul rávetítenénk, azzal azt feltételeznénk, hogy ezek a változók egymástól függetlenek. Erre nincs megfigyelt bizonyíték. Ugyanez vonatkozik a KSH-modellezett primerenergia-eloszlás WBL-alcellákra osztására.

A külön margók keresztbeszorzása tilos mindaddig, amíg nincs:

- ugyanazon rekordokra vagy dokumentált mintára épülő közös adat;
- vagy Joseph által jóváhagyott statisztikai összekapcsolási modell, kalibrációval, bizonytalansággal és visszaegyeztetéssel.

## Reprodukció és lineage

```powershell
python tools/build_b02_archetype_coverage.py --data-dir data/processed/b02 --retrieved-at 2026-08-12
```

A [`b02_archetype_coverage_manifest.json`](../../data/processed/b02/b02_archetype_coverage_manifest.json) rögzíti a három bemenet és két kimenet SHA-256 lenyomatát, valamint a sor-, bin-, lakásszám- és státuszkontrollokat. A futtatás csak repóban lévő feldolgozott adatot olvas; hálózatot nem használ.

## Következő B02 kapu

1. A WBL011/WBL017 levélkódos közös cellák determinisztikus materializálása és nulla/ritka celláinak leltára.
2. Az `Y_GE2011` és a KSH energetikai `2011–2015` + `2016–2022` kategóriák dokumentált hídja.
3. A településtípusos épülettípus-proxy friss vagy adminisztratív validálása.
4. A P1-F OÉNY adatigénylés Joseph által jóváhagyott elküldése vagy a műszaki felmérési fallback aktiválása.
5. Csak ezek után kalibrált archetípus-összekapcsolás és bizonytalansági elemzés.

## Nem következik ebből

- nincs új technikailag alkalmas lakásszám;
- nincs országos hőleadó- vagy hőmérséklet-eloszlás;
- nincs új hőigény, COP vagy retrofitköltség;
- a 4 575 790 lakás nem megfigyelt tanúsítványállomány, hanem a KSH által modellezett eloszlás publikált binösszege;
- a 4 008 541 lakásos épülettípus-proxy `ASS`, és nem kapcsolható automatikusan a 16 energetikai cellához.
