# P1-C forráscsomag: B02 energetikai modellkapcsolat és lefedettség

Állapot: **épülettípus- és energiaigény-kivonat reprodukálható; műszaki alkalmasság nincs kiszámítva**

Lekérdezés napja: **2026-08-12**

## Forráseredmény

A KSH 2025. november 14-én közzétett kísérleti statisztikája a 2022-es népszámlálási lakásállományt 2020–2023 között kiadott energetikai tanúsítványokkal kapcsolta össze. A módszertan szerint 4 580 538 lakásból 279 020-hoz kapcsolódott tanúsítvány, ami publikáltan 6,1%.

A végleges energiaigény-becslés random forest módszerrel készült, külön családi házakra és társasházi/többlakásos épületekre. Emiatt a primerenergia-igény nem megfigyelt népszámlálási mező, hanem `MODELLED` kimenet.

## Reprodukálható kivonat

A KSH nem külön XLSX- vagy CSV-fájlként, hanem a nyilvános HTML tábláiban és grafikonkonfigurációiban közli a részletes eredményeket. A [`tools/extract_b02_ksh_energy.mjs`](../../tools/extract_b02_ksh_energy.mjs) korlátozott, adatjellegű parserrel kinyeri:

- az országos TNM/ÉKM energiaosztály-megoszlást;
- a családi ház és többlakásos épület építési időszak szerinti átlagos ÉKM energiaigényét;
- mindkét épülettípus 10–590 kWh/m²/év publikált eloszlását;
- a módszertani lakásuniverzumot és tanúsítvány-kapcsolást.

A kivonó minden forrás-HTML SHA-256 lenyomatát rögzíti, és eltérő ábraalak vagy kontrollérték esetén leáll.

## Lefedettségi kontroll

| Rekord | Lakásszám | Státusz |
| --- | ---: | --- |
| Módszertani teljes lakásuniverzum | 4 580 538 | OBS |
| Kapcsolt energiatanúsítvány | 279 020 | OBS |
| Családi ház a publikált energiaigény-binekben | 2 881 310 | MODELLED |
| Többlakásos épület a publikált energiaigény-binekben | 1 694 480 | MODELLED |
| Publikált binek együtt | 4 575 790 | DER |
| Maradék | 4 748 | DER |
| Publikált-bin lefedettség | 99,896344% | DER |

A 99,896%-os arány csak azt mutatja, hogy a publikált ábrabinek összege mennyire egyezik a módszertani lakásuniverzummal. Nem helyettesíti a 6,1%-os tényleges tanúsítvány-kapcsolási arányt, és nem bizonyít egyedi lakásszintű pontosságot.

## Archetípus-benchmarkok

A KSH modell alapján például az 1961–1980 között épült családi házak átlagos energiaigénye 375 kWh/m²/év, az azonos korú többlakásos épületek lakásaié 187 kWh/m²/év. Ezek alkalmasak B05/B06 benchmarknak és bizonytalansági sávok kialakítására, de nem használhatók önmagukban hőszivattyús alkalmassági döntésre.

## Lezárt és nyitott határok

Lezárt:

- `FAMILY_HOUSE` és `MULTI_DWELLING` épülettípus;
- a publikált ÉKM energiaigény-átlagok és eloszlások gépi lineage-e;
- `OBS`, `MODELLED` és `DER` státuszok szétválasztása;
- a publikált eloszlás országos visszaegyeztetése.

Nyitott:

- a WBL011/WBL017 népszámlálási cellák közvetlen épülettípus-kapcsolata;
- a hőleadó rendszer és tervezési előremenő hőmérséklet;
- a 4 748 lakásos maradék oka;
- archetípusonkénti modellhiba és bizonytalansági intervallum;
- műszaki kizárási és minimális retrofit-szabály.
