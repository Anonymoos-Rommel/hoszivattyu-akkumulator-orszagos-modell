# B07/B12: körülhatárolt tárolási SCN-kontraktus

Dokumentációs állapot: 2026-10-28. A leírás a 2026-10-26–27-i helyi
referenciaesetek szakmai feltételeit és értelmezési határait rögzíti.
Nem végrehajtható bemenet, új modellfeltétel, teljes modul-/E2-lezárás vagy
publikálási engedély. A közölt eredmények helyi referenciaeredmények;
a dokumentum közzététele önmagában nem igazol független reprodukciót.

## Vizsgálati cél és rendszerhatár

A vizsgálati cél a hálózat terhelésének kiegyenlítése. Egy háztartás eredménye
nem országos átlag. A 18–22 közötti kisütés a ház saját fogyasztását fedezi;
nem szolgáltatói vagy hálózati lehívás. EV-töltés és export nincs ebben az esetben.
A koordinált, eltolva indított töltés külön forgatókönyv. A tényleges távoli
vezérelhetőség, szolgáltatási jogosultság és működő hálózati integráció nincs
igazolva. A védett energiamennyiség, kW-teljesítmény, időtartam és lehívott
energia külön mennyiség; rendelkezésre tartásból nem következik kisütés.

A tágabb rendszertervezési kérdés a termelés, fogyasztás, tárolás és hálózat
együttes mérlege: a jelenlegi villamos igény, a gázos fűtés hőszivattyús
kiváltásának többlete és egy később külön definiált EV-igény ellátása termelés,
tárolás, import, szabályozható tartalék és hálózatfejlesztés mellett.
EV-terhelés a jelen referencia számaiban nincs.

- Nappali napenergia-többlet és éjszakai olcsó energia vizsgálati hipotézis,
  nem minden napra garantált többlet vagy ingyenes energia.
- Az atomenergia külön kategória a megújulóktól. Alacsony határköltségből
  nem következik alacsony nagykereskedelmi vagy háztartási ár.
- A PV/helyszíni/hálózati felújítás célja a biztonságosan hasznosítható termelés.
  Feszültségminőségi korlátozás és veszteség külön kérdés; invertervédelem
  kikapcsolása vagy megkerülése nem része a forgatókönyvnek. A megtermelhető
  és a hálózatra ténylegesen átadott energia eltérhet.
- Éves MWh-egyezés nem igazol órás MW-egyensúlyt, többnapos/évszakos ellátást
  vagy helyi vezetékalkalmasságot. Tárolóveszteség, készlet, töltési/kisütési
  teljesítmény, import és szabályozható háttér külön mérlegelem.
- A 07–10 és 18–21 közötti ablakok vizsgálati felvetések, nem megfigyelt
  kritikus időszakok és nem helyettesítik a 18–22-es háztartási esetet.

A teljes fogyasztás maximuma, a nap-/széltermelés levonása utáni maradó igény
maximuma és az ármaximum külön kérdés, eltérő időponttal. A besorolás
Europe/Budapest idő, DST, évszak/hónap és hétköznap/hétvége szerint értendő.
Teljes év és részleges aktuális év lefedése nem tekinthető azonosnak.

## Kapcsolat a meglévő modulkontraktusokkal

Az alábbi megfeleltetés a [meglévő kutatási tervhez](../../registry/v1_research_plan.json)
kapcsolódik; nem új motor, modul vagy készültségi állítás.

| Kérdés | Meglévő munkaszelet és határ |
| --- | --- |
| Résztvevők, állapotok, későbbi EV-penetráció | B01-D01/P01, B08-D02: explicit populáció, súly és ellenforgatókönyv; a referencia nem országos átlag. |
| Fűtéskiváltás villamos többlete | B05-D01/D03, B06-D01/D03, B11-D01/D03: azonos hőszolgáltatás, gázelkerülés és villamos többlet; HMV/segédenergia külön ismeretlen. |
| Terhelés és egyidejű összegzés | [B08](../../modules/B08/README.md): időben összeillő AC-határ; összegzésből nem következik vezérlés vagy népességsúly. |
| Termelés és import | [B09](../../modules/B09/README.md): termelési panel és maradó mérleg, nem automatikus tároló-diszpécser. Nettó/bruttó/HMKE határok különbözhetnek; teljes termelés utáni residual nem csak nap/szél utáni igény. |
| Koordinált tárolás | B07-D01/D03: meglévő fizika és explicit ütemezés; készlet, MW és szolgáltatási jog külön. |
| Helyi hálózat és PV-csatlakozás | [B10](../../modules/B10/README.md): célhely/topológia, beavatkozás és időzítés; országos energiaegyenleg nem igazol helyi headroomot vagy csatlakozási engedélyt. |
| Piaci érték és háztartási költség | B04-D01/D02/L01, B12-D01/D03: nagykereskedelmi EUR/MWh külön a bruttó háztartási HUF-tarifától és teljes életciklus-költségtől. |
| Finanszírozás és kivitelezés | B13/B14/B18: rendszerirányítási cél nem igazol támogatási jogosultságot, keretet vagy kivitelezési kapacitást. B15 kapui változatlanok. |

## Adat- és időbeli lefedettség

A leírt referencia adatideje **2025**, nem 2026-os megfigyelés. A beszerzés
vagy source_id 2026-os dátuma nem változtatja meg az adatévet.

- A [B04 ármanifest](../../registry/b04_wholesale_reference_manifest.json)
  teljes UTC-2025 referenciaárat és 11 eredeti SMARD-forrás kötését rögzíti.
  A natív negyedórás/órás átlag konvenció a forrásértelmezés része.
- A [B08/B09 történeti manifest](../../registry/b08_b09_historical_balance_manifest.json)
  és [B09 termelési manifest](../../registry/b09_gui_reference_manifest.json)
  E2, 2025-ös magyar control-area referencia: PT15M, 35 040 időpont,
  14 aktív termelési kategória. A numerikus források külső megőrzésűek;
  pusztán e dokumentum olvasásából nem következik elérhetőségük vagy betöltésük.
- A történeti adatút terhelési panelje 7 214 812 bájt, termelési panelje
  156 451 085 bájt, recovery-lineage állománya 2 106 638 bájt; az eredeti
  forráskötések és tárolási/újrahasználati korlátok érvényesek.
- A teljes UTC-év nem teljes Budapest polgári év és nem teljes összefüggő
  meteorológiai tél.

Kritikusidő-összevetésnél az ár, terhelés és termelés azonos időbeli és
forráshatára szükséges. Órás aggregálásban az intervallumenergia megmaradása
feltétel; lyukpótlás vagy hallgatólagos időeltolás nincs e kontraktusban.
Ár és termelés együttjárása önmagában nem oksági bizonyíték.
Aktuális, 2026-os összevetés külön, közösen teljes megfigyelési ablakot igényel;
a legutolsó közös lezárt nap nem feltételezett bemenet.

Az alábbiak a 2026-10-26-i dokumentált forráselérési megállapítások,
nem friss hozzáférési vagy numerikus lefedettségi igazolások:

- [MAVIR RTDW](https://rtdwweb.mavir.hu/rtdwweb/webuser/GenerateChartsServlet?hunLang=hu-hu&tabId=tab7679):
  dátum/felbontás/export és termelési kategóriák felülete elérhető volt;
  a legutolsó numerikus adatnap nem volt igazolt. HMKE/SCTE és nettó/bruttó
  sorok nem felcserélhetők.
- [ENTSO-E Transparency](https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=):
  a statikus olvasás JavaScript-hibája miatt aktuális numerikus lefedés nem
  volt állítható. Az A65 actual-load és A75 actual-generation szerződés külön marad.
- [ENTSO-E Power Statistics](https://www.entsoe.eu/data/power-stats/):
  a 2026-os órás terhelési/statisztikai letöltések Q1/Q2 jelölése részéves
  keresztellenőrzési lehetőség volt; nem októberi/YTD vagy teljes téli bizonyíték.
- [SMARD letöltő](https://www.smard.de/en/downloadcenter/download-market-data/):
  az interaktív felület elérhetősége nem igazolta új 2026-os fájl lefedését;
  a magyar árzóna, forrásrevízió és felbontás külön azonosítandó.

## SCN fizikai és elszámolási feltételek

| Tétel | Értelmezés és minősítés |
| --- | --- |
| Háztartás | Magyar, 56 m²-es, WM50/W55 csak térfűtéses referencia; közös alapfogyasztás egyszer; nincs PV vagy EV. Nem országosan reprezentatív. |
| Tároló | **SCN: 10 kWh kisütött-DC-egyenértékű használható kapacitás**. Nem névleges marketingkapacitás vagy igazolt 10 kWh-s SAX készülék. |
| Tartalék és indulás | **SCN: 20% = 2 kWh védett hálózati készlet**; mindkét összehasonlítási ág 2 kWh-ról indul. A háztartás ezt nem merítheti le. Végleges programarány nincs kiválasztva. |
| Háztartási kisütés | Budapest szerint **18:00–22:00**, legfeljebb **1,5 kW AC** és a tényleges órás háztartási terhelés. A külön prioritási esetben a kisütési árküszöb elhagyott. Nem garantált napi 6 kWh. |
| Töltés | Budapest szerint **00–06 és 10–16**, ha az aktuális megőrzött ár az előző 24 lezárt fizikai óra mediánja alatt van. Nincs hallgatólagos 22–24-es töltés. |
| Idő és információ | Eredeti UTC-2025, 8760 óra, Europe/Budapest/DST. Első 24 fizikai óra tartásos bemelegítés; nincs kitalált előző ár vagy készlet. Nem 2028-ra átnevezett profil. |
| Átvett paraméterek | **SCN/ASS:** a 7,572 kWh-s referencia konvertergörbéi, teljesítménytartományai, 0,958183 DC-ciklushatásfoka és 4,07 W AC készenléti közelítése változatlanul átvett. Nincs arányos skálázás; nem 10 kWh-s termékmegfigyelés. |
| Önkisülés | Explicit idealizálás: nulla cellaoldali önkisülés. Szigorú alapműködésben az ismeretlen idle Q. Aktív veszteség megmarad; 4,07 W csak tényleges idle időben külön AC-elszámolás. |
| Mérleg és pénz | Nincs egyidejű töltés/kisütés vagy export. Zárókészlet látható; nincs ingyenes visszaállítás vagy választott készletértékelés. Befagyasztott 2026-os A1 HUF-díj és 2025-ös nagykereskedelmi EUR-értékelés külön; nincs árjóslat, tényleges számla vagy ROI. |

A **7,572 kWh** a forráshoz kötött SAX Power Home Plus / V23.50 referencia
kisütött-DC-egyenértékű kapacitása. Forrásadatai, azonosítója, guardjai és
korábbi futásai nem változnak 10 kWh-ra. A külön kapacitásérzékenység
azonosítója `SCN_CAPACITY_10KWH_SAX_CURVES_UNSCALED_20261026`;
a prioritási vezérlés külön `EVENING_PRIORITY` eset.

Kapcsolódó kontraktusok: [forrás-/alkalmazhatósági adósság](../../registry/b07_reference_validation_debt.json),
[eredeti és SCN-konstruktor](../../modules/B07/discharge_equivalent_reference.py),
[háztartási vezérlések](../../modules/B12/battery_reservation_reference.py),
[ütemezési szerződés](V1_066_B07_SHARED_USE_SCHEDULE.md).

A 100 m² feletti házakra felvetett **12–15 kWh** vizsgálati hipotézis,
nem piaci adat, méretezési szabály vagy jelen számítási eset. A referencia
nem igazolja, hogy 10 kWh alatt nem érdemes telepíteni.

## Korábbi helyi referenciaeredmények

Az alábbi SHA256 értékek külső megőrzésű helyi műszaki eredményeket azonosítanak.
E fájlok nem e dokumentummal csomagolt adatok; nyilvános hozzáférésük nincs
igazolva. A hash önmagában nem biztosít hozzáférést vagy reprodukciót.

| Eredmény | SHA256 |
| --- | --- |
| Árküszöbös 10 kWh ellenág éves eredménye | `a7e5b246129f35c6bdb7e78aa3803d2af2f674c872047bf82ed018ccc0c6dfc9` |
| Esti prioritás éves eredménye | `e5d27bd7f909f1c13d981a63c3fd54be0107032dae2811b857ce9b680034b1d6` |
| A két eset közvetlen összehasonlítása | `02289c6c38a6a26387e9673360d6458af115522909f23a8b07de2c3e2c5852e5` |

A korábbi helyi részfeladat dokumentált ellenőrzése: 198 sikeres B07-teszt,
ebből 42 célzott eset független ismétléssel; registry VALID. Ezek történeti
részfeladat-bizonyítékok, nem a jelen dokumentációs változat új tesztjei,
teljes projektregresszió vagy projektlezárás.

A prioritási eset az árküszöböshöz képest 54,17 kWh további esti igényt fedezett,
59,05 kWh többlettöltéssel és 4,50 kWh többlet éves vételezéssel. Bemelegítés
után az esti órás importmaximum 1,246 kW-ról numerikusan nullára csökkent;
a teljes éves esti maximum az első napi bemelegítés miatt 1,387 kW maradt.
A töltés közbeni **4,861 kW egy háztartás órás átlagos maximuma**;
nem országos hálózati probléma bizonyítéka. Az aggregált következmény külön kérdés.

## Két háztartás koordinált töltési SCN-je

A körülhatárolt összehasonlítás két azonos SCN-referenciaháztartás önálló
töltése és az ár szerint tölthető fizikai órákon felváltva legfeljebb egy
töltő esete. HH1 indul, majd HH2 kaphat lehetőséget; tele vagy fizikailag
nem tölthető háztartás kimarad. A sor csak ténylegesen befogadott töltés után
vált; töltés nélkül nem lép tovább. Egy órán belül nincs rejtett részidős
újraosztás. A készülék töltési görbéje és korlátja változatlan. Mindkettő
2 kWh-ról indul; az esti elsőbbség és olcsó töltési feltétel megmarad.

A körülbelül 3,436 kW összes akkumulátortöltési plafon az ütemezési
feltevés következménye, nem megfigyelt feederadat; a két háztartás egyéb
terhelése ezen felül számít. Ez két explicit háztartás, nem népességbecslés,
éles vezérlési szolgáltatás vagy finanszírozási konstrukció.

A meglévő B07 fizika és Request/Interval audit adja az értékelés határát.
Kimenetei: egyidejű összterhelési csúcs, visszatöltési késés, esti ki nem
szolgált igény, tartalékmegőrzés és zárókészletek. Kisebb töltési csúcs
nem helyettesíti az esti ellátás és zárókészlet külön összehasonlítását.

Nyitott bemenetek: tényleges operátori aktiválás és szolgáltatási kW/időtartam,
végleges rendelkezésre tartási arány, finanszírozás, jogi és műszaki
távirányítási jogosultság, csatlakozási/vezetékterhelhetőség, országos súlyok
és teljes életciklus-költség/megtérülés. Az ismeretlen érték nem nulla.

## Forrás- és újrahasználati határ

A fizikai és tarifaforrások az idézett repository-manifestekben azonosított
források; e dokumentációs változat nem fogad be új forrást vagy adatot.
SMARD numerikus piaci adatoknál a [B04 manifest](../../registry/b04_wholesale_reference_manifest.json)
szerinti forrásazonosító, eredeti URL, hash és újrahasználati státusz érvényes;
attribúció **Bundesnetzagentur | SMARD.de**, licenc
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), a
[SMARD adatfelhasználási feltételeinek](https://www.smard.de/en/datennutzung)
megfelelő numerikus piaciadat-körben. Ez nem más szolgáltató adatainak vagy
dokumentumok/PDF-ek bájtjainak általános újraközlési joga. A licenc és a
konkrét adatcsomag tulajdonosi publikálási engedélye külön feltétel;
e dokumentum egyik helyett sem ad engedélyt.
