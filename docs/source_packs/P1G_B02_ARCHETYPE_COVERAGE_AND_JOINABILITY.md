# P1-G forráscsomag: B02 archetípus-cellalefedettség és összekapcsolhatóság

Állapot: **WBL011 full stock joint materialized; teljes B02 országos műszaki eloszlás még nincs becsülve**

Current-state frissítés: **2026-09-20 / project-wide population inference policy**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

## Döntési eredmény

A current B02 adatcsomag több, eltérő authority-grainen áll:

1. a KSH energetikai publikáció 16 épülettípus × építési időszak cellát és 944 primerenergia-bint ad `MODELLED` státuszban;
2. a 2015-ös lakásfelmérésből 2022-re vetített building-type kapcsolat 8 `ASS` proxycella;
3. a pinned `WBL011/V67` direct full-stock joint P15-ben **116 452** `OBS` sorral és **4 008 541** lakással repositoryban materializált;
4. a WBL017 hőszivattyú-baseline továbbra is külön grain és nem teljes occupied-population joint.

Hőleadó- és tervezési hőmérsékletre továbbra sincs teljes közös országos mikroadat. Ezért nem áll rendelkezésre source-native teljes joint a terület × épülettípus × építési kor × falazat × alapterület × komfort × fűtés × tüzelőanyag × primerenergia × hőleadó × hőmérséklet grainen. A 2026-09-20-i project-wide population inference policy szerint azonban **ennek hiánya önmagában nem blocker**: országos eloszlás reprezentatív mintából vagy validált, kalibrált többforrású inferenciából is becsülhető, explicit bizonytalansággal.

## Energetikai cellalefedettség

A 16 KSH-modellezett building-type × construction-period cella publikált energiaigény-binjeinek összege 4 575 790 lakás. A 944 binből 864 pozitív és 80 nulla. Ez MODELLED source surface; nem WBL assignment authority.

## Összekapcsolhatósági mátrix

| Részgrain | Státusz | Megengedett | Tiltott új authority nélkül |
| --- | --- | --- | --- |
| WBL011 direct full stock joint | `OBS`, `MATERIALIZED` | geography, construction period, wall, area, comfort, heating mode, fuel ugyanazon source-native sorban | building type, primary energy, heat emitter, design temperature |
| WBL011 envelope / heating-fuel margók | `OBS`, `MATERIALIZED` | önálló részgrain elemzés | egymás synthetic cross-joinja; combined elemzéshez a direct full joint kell |
| WBL017 heat-pump baseline | `OBS`, részgrain | combined heating/fuel × HOSZIV | technical eligibility, emitter, temperature |
| KSH energetikai eloszlás | `MODELLED`, `MATERIALIZED` | building type × period × primary energy | WBL subcell assignment authority |
| Building-type proxy | `ASS`, `MATERIALIZED` | settlement type × building type total | county/period/wall/area/comfort/heating/fuel subcell promotion |
| OÉNY emitter/temperature | `Q`, request sent / awaiting response | rétegzett minta validálásra és országos inferenciára használható, ha reprezentativitás és bizonytalanság igazolt | heating/fuel alapú vak imputáció |
| Teljes B02 archetype | `Q` | új joint authority **vagy** admitted representative/calibrated population inference után | külön margók dokumentálatlan keresztbeszorzása |

A külön margók keresztbeszorzása tilos. A P15 WBL011 full joint ezt a WBL011-en belüli combined kapcsolatot source-native módon oldja meg, nem independence assumptionnel.

## Reprodukció és lineage

```powershell
python tools/extract_b02_ksh_wbl_joint_cells.py --output-dir data/processed/b02 --retrieved-at 2026-09-05
python tools/build_b02_archetype_coverage.py --data-dir data/processed/b02 --retrieved-at 2026-09-05
```

A `b02_archetype_coverage_manifest.json` a repo-bemenetek és derived outputok hashét rögzíti. A teljes B02 országos technikai becslés továbbra is Q, de **nem azért, mert nincs minden lakásról teljes joint rekord**; azért, mert a még hiányzó változókra a védhető populációs inferencia nincs teljesen materializálva.

## Következő B02 kapuk

1. current WBL-compatible building-type authority vagy admitted calibrated linkage;
2. primary-energy-to-WBL link authority vagy admitted calibrated linkage;
3. heat-emitter és design-temperature országos inferencia reprezentatív vagy kalibrált mintából, explicit uncertaintyvel;
4. OÉNY válasz beérkezése esetén annak reprezentativitási/missingness auditja; az OÉNY-út hiánya nem zárja ki más reprezentatív műszaki minta használatát.

## Nem következik ebből

- nincs új technikailag alkalmas lakásszám;
- nincs országos heat-emitter vagy design-temperature distribution;
- nincs primary-energy OBS promotion;
- a 4 008 541 direct WBL011 stock universe nem azonos technical/final eligible stockkal.
