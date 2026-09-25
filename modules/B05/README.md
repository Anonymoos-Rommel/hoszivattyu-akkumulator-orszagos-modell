# B05 – Hőszivattyú fizikai és teljesítménymodell

## Cél

A B05 egy explicit hőigény- és időjárás-profilra alkalmazott, operating-point teljesítménytérképes hőszivattyú-fizikai motor. Nem egyetlen éves SCOP/COP értékkel helyettesíti az üzemi viselkedést.

## Bemeneti szerződés

- órás `timestamp` és `outdoor_temperature_C` időjárási input;
- `space_heating_required_kW` és külön `dhw_required_kW` hőigény;
- `required_supply_temperature_C` és külön HMV előremenő hőmérséklet;
- berendezés-azonosító, technológia és source-native/certified operating-point teljesítménytérkép; a kanonikus exact point-set Vaillant aroTHERM és STIEBEL ELTRON HPA-O pontokat tartalmaz. B05-P10 külön NIBE S2125 source-native continuous W35/W45/W55 **capacity-domain** evidence-et ad a P9 hidegstressz-tartományára. B05-P11 két Tekno Point ATHENA R32 mérethez exact `A-15/A-7 × W35/W55` capacity + published power-input + COP sarkokat ad; ezekből az engine W45-öt és a P9 stressz-intervallum belső pontjait bounded DER interpolációval számolja. B05-P12 két EC POWER PMH mérethez ugyanezen sarokkoordinátákon source-native capacity + COP adatot ad; ezeket külön OBS source-layer őrzi, majd az electrical input a már meglévő two-of-three szabály szerint DER-ként materializálódik a canonical complete point-setbe;
- explicit backup-konfiguráció, ha van;
- opcionális páratartalom csak bizonyított defrost-modellhez.

## Kimeneti szerződés

- operating-point COP, hőteljesítmény, teljes egység villamos teljesítménye;
- elérhető kapacitás, igényelt kapacitás, részterhelési arány és kapacitáshiány;
- órás hőleadás, hőszivattyú-villamos energia, backup-villamos energia és összes villamos energia;
- szezonális hő, villamos energia, `seasonal_cop_simulated`, `spf_simulated` és fizikai csúcsteljesítmény;
- HMV és térfűtés külön inputmezőként, valamint explicit Q státusz, ha a módválasztás vagy a teljesítménytérkép nem bizonyított.

## Fizikai határ

B05 nem fogyaszt és nem számol Ft/kWh, Ft/MJ, gázárat, tarifát, számlát, megtérülést, finanszírozást, támogatást, fiskális vagy importértéket, akkumulátor/VPP dispatch-et. A B04 registry csak downstream komponens; nem módosíthatja a COP-ot vagy az energiaigényt.

## Módszer és fail-closed szabályok

- A V1 motor determinisztikus, bounded bilineáris interpolációt használ a teljesítménytérkép teljes téglalap-rácsán.
- Ismert pontot változtatás nélkül reprodukál; hiányzó sarokpont vagy tartományon kívüli hőmérséklet `Q / OUT_OF_PERFORMANCE_DOMAIN` vagy `Q / MISSING_GRID_POINT`.
- A kapacitás, teljes egység-input és COP közül kettőből a harmadik `DER`; három forrásérték inkonzisztenciája validációs hiba. A gyártói, két tizedesre kerekített táblákhoz legfeljebb 0,05 COP-eltérés tolerált; nagyobb eltérés Q/validációs hiba.
- Modulation-floor hiányában nincs kitalált degradációs együttható. B05-P15 current HP KEYMARK EN14825 Vaillant part-load Pdh/COP/Cdh mezőket materializál. B05-P16 ezt egy második, Bosch HP KEYMARK gyártói rekorddal cross-manufacturer szinten validálja, és külön fail-closed runtime-state contractot ad: explicit minimum continuous capacity nélkül a cycling-state alkalmazhatósága Q; a floor alatt `CYCLING_REQUIRED`, fölötte `CONTINUOUS_MODULATION`. A current UK HEM-TP-12 ezt a sorrendet módszertani kontrollként támogatja, de nem magyar szabályozási authority és nem termékadat. A certified Cdh csak cycling-state után válhat megfontolható evidence-é; közvetlen órás multiplier vagy `COP × Cdh` korrekció továbbra is tiltott bizonyított numerikus runtime-módszer nélkül. B05-P17 ehhez két exact same-product minimum-modulation anchor-t ad (Vaillant A7/W35, Bosch A2/W35); az anchor lookup exact-coordinate-only, ezért a hiányzó operating coordinate továbbra is Q. B05-P18 a to-water EN14825 cycling képletet külön executable standard-method contractként kvalifikálja: `COPbin = COPd × CR / (Cdh × CR + (1 − Cdh))`. Ez nem engedi meg a névleges vagy más kapacitásponton mért COP csendes használatát: a `COPd`-nek ugyanahhoz a cycling kapacitáshoz kell tartoznia, amely a `CR` nevezője. B05-P19 tovább szigorítja ezt: ugyanazon operating conditionben együtt közölt min/max capacity/input/COP tartományok sem tekinthetők automatikusan point-paired adatoknak; range-endpoint division és COP-endpoint hozzárendelés explicit source semantics nélkül tiltott. B05-P20 az első source-native point-paired closure-t adja: Mitsubishi PUZ-WM50VHA A7/W35 Min/Nom/Max capacity, input és COP tripletjei pozicionálisan párosítottak; a minimum pont 1.80 kW / 0.33 kW / COP 5.46. A current HP KEYMARK outdoor-only PUZ-WM50VHA(-BS) +7 low-temperature Cdh=0.950 értékével ez az exact pont már a P18 cycling képlettel numerikusan értékelhető. B05-P21 ugyanazon PUZ-WM50VHA modellhez négy source-native minimum-output sarkot materializál (A2/A7 x W35/W45), és a már kanonikus complete-rectangle szabályt alkalmazza a modulation floor-ra is: exact corner = OBS, rectangle-interior = bounded bilinear DER, rectangle-outside/missing corner = Q. Az engine min_modulation interpolációja ezzel együtt javul: többé nem a négy sarok egyszerű átlaga, hanem ugyanaz a koordinátafüggő lineáris/bilineáris súlyozás fut. B05-P22 az official Mitsubishi Data Book Min táblájával ezt 40 exact minimum-capacity/COP pontra és 27 complete bounded cellára bővíti. A core surface A-10..A20 x W35..W55; hidegebben lépcsősen szűkül A-15..A-10 x W35..W45, illetve A-20..A-15 x W35..W40 tartományra. Blank source cell továbbra sem interpolálható. Ugyanazon modell official ERP dokumentuma négy exact W35 low-temperature Cdh bin-t ad (-7/+2/+7/+12 C); ezek között nincs automatikus órás Cdh-interpoláció. B05-P23 egy második gyártói modulation-floor surface-et kvalifikál Dimplex LA 2030CP-vel: 15 exact minimum-output pont W35/W45/W55 mellett. A forrás A-10 minimum sora hiányos, ezért a surface explicit A-10 interpolation barrierrel működik; -15 és -7 között nincs csendes híd. A current HP KEYMARK ugyanahhoz az exact modellhez non-default Cdh bin-eket ad, és A-7/A2/A7 W35 pontokon a gyártói minimum-COP mezőkkel három exact második-gyártós cycling-ready bin áll össze. B05-P24 lezárja a Cdh órás hőmérsékletre vetítésének szemantikai kérdését: ezt a projekt nem lineáris/nearest-bin interpolációval oldja meg. A Cdh/COPbin út exact EN14825/DEAP standard-bin validáció marad; a generic órás fizikai runtime a current HEM-TP-12 v3.0 EN15316-derived on/off transient útját követi, ahol a below-minimum állapotban a többlet compressor power a minimum continuous compressor power, LR, heat-pump transient parameter és emitter response time függvénye. Cdh nem bemenete ennek az órás képletnek. B05-P25 ehhez explicit parameter-policy réteget ad. A HEM-default scenario tau_eq=140 s csak POL/default minőségű és csak explicit policy-választással használható. A current HEM dokumentum és reference code egyező emitter classoknál a response time materializálható: radiator/UFH wet=1370 s, warm air=120 s, DHW/storage=1560 s. Fan coil esetén a current HEM v3 dokumentum (all wet -> Light embedded) és a current Rust reference code (FanCoils -> 360 s) eltér; ez Q marad. A generic product-specific tau_eq változó szintén Q marad. B05-P26 visszatér a közvetlen termékfizikához: a PUZ-WM50VHA gyártói maximum outlet-water operating-envelope görbéjével újraminősíti a P22 hideg/high-supply blank Min cellákat. A-20/W45, W50, W55 és A-15/W55 az operating envelope-on kívül van, ezért ezek nem hiányzó modulation-floor adatok. A-15/W50 továbbra is Q, mert a projekt nem digitizál és nem interpolál köztes görbeértéket csak a blocker lezárásáért. A P9 W55 hidegebb, A-10 alatti szegmense ennél a terméknél product-applicability kizárás, nem missing-data Q.
- Defrost büntetés nincs beégetve. B05-P14 szerint az explicit EN 14511-tagged performance pointoknál a rating interval alatt fellépő defrost hőhatása a heating-capacity, villamos igénye pedig az effective-power-input accounting része; ezért ezekre külön univerzális defrost penalty nem tehető rá. Ez nem állítja, hogy minden rating point alatt ténylegesen történt defrost.
- P6 audit runtime következtetése megmarad: `defrost_runtime_penalty`, `defrost_model_status`, `cdh_measured` és `cycling_penalty_runtime` Q. P14 kizárólag a `defrost_accounting_boundary`-t oldja fel explicit EN 14511-tagged pontokra. Az EU 813/2013 szerinti `cdh_regulatory_default=0,9` továbbra is csak POL compliance-method érték, nem runtime-korrekció.
- Backup csak explicit engedélyezéssel, típussal, kapacitással és hatásfokkal működik, és külön fogyasztásként jelenik meg.
- HMV eltérő hőmérsékleten egyidejű térfűtéssel csak explicit priority-konfigurációval fut; egyébként Q.

## SCOP / SPF szemantika

`scop_en14825_declared` (forrásban deklarált szezonális érték), `scop_en14825_calculated` (szabványos számítás, jelenleg nincs implementálva) és `seasonal_cop_simulated`/`spf_simulated` (saját órás szimuláció) külön fogalom. A jelenlegi szimulált COP a hőszivattyú által leadott hő és a hőszivattyú teljes egység-villamos energiájának aránya; az SPF a backup-ágat is tartalmazza.

## Időjárás és forgatókönyvek

Az engine csak explicit órás időjárási inputot fogad. A HungaroMet ODP historikus automata-állomás adataiban a `Time` UTC, a `-999` hiányjel, a `ta` az elmúlt óra átlaghőmérséklete, a `t` pillanatnyi hőmérséklet, a `tn`/`tx` az óra minimuma/maximuma, az `u` pedig pillanatnyi relatív nedvesség. A canonical B05 `outdoor_temperature_C` kifejezetten `ta`-ból képzett `DER` leképezés; a source-native mezők `OBS` és a `t` nem cserélődik fel csendben.

A P3 materializáció öt állomás station-specific, legutóbbi közös teljes megfigyelt év (2025) profilját és a teljes elérhető archívumból kiválasztott, 72 órás megfigyelt hidegperiódust tartalmazza. A 2025-ös profil nem nevezhető 1991–2020 normálnak; a klimatológiai normál és a homogenizált adatsor külön evidence layer. Nincs imputáció, helyi időre/DST-re konverzió vagy országos súlyozás. P8/P9 104 teljes Dec-Feb blokk alapján project-derived empirical historical 10-year coldest-72h-mean stress envelope-et materializál `−13.331944…−9.644444 °C` tartományban; ez nem official HungaroMet 1-in-10 és nem jövőbeli gyakorisági állítás. P10 az official NIBE S2125 continuous capacity curves alapján bizonyítja, hogy W35/W45/W55 capacity-domain szinten ez a teljes mean-stress intervallum lefedett egy további gyártónál is. A P10 görbékből exact kW érték nem kerül digitizálásra. P11 viszont külön source-native teljesítménytáblából két ATHENA R32 mérethez complete `-15..-7 C × W35..W55` rectangular performance surface-et materializál; a teljes P9 mean-stress intervallumon W35/W45/W55 így extrapoláció nélkül értékelhető. Exact Tekno Point sarkok complete OBS triple-ek; az EC POWER exact capacity/COP forrásértékek OBS-k, a belőlük képzett electrical input DER. P11+P12 így két külön gyártónál ad teljes B05-admissible `-15..-7 C × W35..W55` fizikai felületet; a P9 stressz W35/W45/W55 tartománya cross-manufacturer lefedett. B05-P13 egy WAMAK AWK 35 EVI `-22..-10 C × W35..W55` felületet ad, így a canonical observed `-21.9 C` órás minimum is W35/W45/W55 mellett extrapoláció nélkül értékelhető. Az A-22/W55 forrás input-konfliktusa explicit Q/DER határral kezelt. Az engine a complete performance-map határon kívül továbbra is fail-closed módon működik.

## Readiness és Q-k

`PERFORMANCE_MAP=PARTIAL (80%)`; `THERMAL_DEMAND_INTERFACE=PARTIAL`; `WEATHER_INPUT=PARTIAL (75%)`; `WEATHER_SOURCE=VALIDATED`; `HOURLY_WEATHER_INPUT=PARTIAL (85%)`; `REFERENCE_WEATHER=PARTIAL (60%)`; `COLD_1_IN_10=PARTIAL (80%)`; `EXTREME_COLD_EVENT=VALIDATED (90%)`; `SPATIAL_COVERAGE=PARTIAL (60%)`; `WEATHER_PERFORMANCE_DOMAIN_COVERAGE=PARTIAL (60%)`; `DEFROST=Q`; `PART_LOAD_MODULATION=PARTIAL (45%)`; `OPERATING_ENVELOPE=PARTIAL (55%)`; `PRODUCT_DIVERSITY=PARTIAL (45%)`; `DHW_MODE=PARTIAL`; `PRODUCT_SCALING=Q`. A B05 státusza ezért `IN_PROGRESS`, nem `VALIDATED`. A jelenlegi B02/B03/B04 dependency edge megmarad orchestration-gate-ként, de a fizikai runtime nem használ tarifát vagy pénzértéket.

B05-P16 után a `PART_LOAD_MODULATION` továbbra is 45%: a cross-manufacturer Cdh/part-load mezők és a cycling-state sorrend már bizonyítottabb, de a same-product minimum-modulation coverage és a numerikus cycling-energy módszer még nyitott.

B05-P17 két exact same-product anchorral lezárja a többtermékes minimum-modulation evidence hiányát bounded anchor szinten. Az anchorok között vagy rajtuk kívül minimum modulation nem interpolálható/extrapolálható; a következő residual a modulation-floor surface/interpolation contract és a numerikus cycling-energy method.

B05-P18 lezárja a numerikus módszer-authority részt az EN14825-based to-water cycling képlettel, de a canonical runtime még nem kap cycling-korrekciót. A két P17 anchor esetén a certified Pdh/COP kapacitáspont nem egyezik pontosan a minimum modulation kapacitással, ezért `MINIMUM_CAPACITY_COP_INPUT_REQUIRED` marad Q. A másik residual továbbra is a modulation-floor surface/interpolation contract.

B05-P19 egy harmadik, current certified exact producton (Amitime PAVH-06V1FXC) bizonyítja, hogy minimum/maximum A7/W35 capacity, electrical-input és COP range-ek együtt publikálhatók. A forrás azonban nem párosítja explicit módon a range-endpointokat, ezért ebből minimum-capacity COP nem származtatható. Az exact HP KEYMARK Cdh=0.900 mezők a P15 szabály szerint default-vs-measured ambiguousak. A residual ezért `POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED`-ra szűkül; readiness nem nő.

B05-P20 a Mitsubishi PUZ-WM50VHA A7/W35 gyártói Min/Nom/Max táblájával és a current HP KEYMARK PUZ-WM50VHA(-BS) non-default Cdh mezőjével lezárja a `POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED` és a co-location gate blokkerét egy exact current product pointon. Q-B05-004 így `OPEN_NARROWED_TO_MODULATION_FLOOR_SURFACE_ONLY`; az egyetlen residual a `MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`. Readiness nem nő, mert egy pont nem felület.

B05-P21 a korábbi surface/interpolation residualt bounded scope-ban lezárja: PUZ-WM50VHA A2..A7 x W35..W45 complete minimum-output rectangle. Q-B05-004 továbbra is OPEN, de `OPEN_NARROWED_TO_OUTSIDE_BOUNDED_MODULATION_FLOOR_COVERAGE`; a maradék coverage gap a rectangle-en kívüli hőmérséklet/előremenő tartomány. `PART_LOAD_MODULATION` ezért továbbra is 45%.

B05-P22 a P21 narrow rectangle-et current evidence-surface szinten supersede-eli a 40 pontos official Data Book Min grid-del. A teljes P9 mean-stress envelope W35 és W45 esetén floor-covered; W55 esetén a -10 C alatti stressz-rész továbbra is Q. Q-B05-004 új állapota `OPEN_NARROWED_TO_COLD_HIGH_SUPPLY_CDH_MAPPING_AND_SECOND_SURFACE`. Residualok: `MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`, `CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED`, `SECOND_MANUFACTURER_MODULATION_FLOOR_SURFACE_REQUIRED`. Readiness marad 45%.

B05-P23 a `SECOND_MANUFACTURER_MODULATION_FLOOR_SURFACE_REQUIRED` residualt `RESOLVED_FOR_DIMPLEX_LA2030CP_PIECEWISE_SURFACE` állapotban lezárja. A Dimplex A-10 minimum source-gap külön barrierként megmarad, ezért Q-B05-004 most `OPEN_NARROWED_TO_DOMAIN_GAPS_AND_CDH_MAPPING`. Residualok: `MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`, `DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`, `CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED`. Readiness marad 45%.

B05-P24 a `CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED` residualt `RESOLVED_BY_METHOD_SEPARATION_NO_CDH_INTERPOLATION` állapotban lezárja. A standard-bin Cdh evidence megmarad audit/validation célra, de az órás fizikai runtime nem interpolál Cdh-t. Q-B05-004 új állapot: `OPEN_NARROWED_TO_DOMAIN_GAPS_AND_HOURLY_ONOFF_PARAMETERS`. Új residual: `HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED`, a két termék-domain gap mellett. Readiness marad 45%.

B05-P25 a `HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED` residualt `RESOLVED_FOR_EXPLICIT_HEM_DEFAULT_POLICY_WITH_BOUNDED_EMITTER_CLASSES` állapotban lezárja default-scenario scope-ban. Q-B05-004 új állapot: `OPEN_NARROWED_TO_DOMAIN_GAPS_FANCOIL_AND_PRODUCT_TAU_EQ`. Nyitva marad a két termék-domain gap, a `HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED` és a `PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME`. Readiness marad 45%.

B05-P26 a Mitsubishi cold/high-supply gapet öt blank celláról egyetlen exact kérdésre szűkíti. `MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED -> PARTIAL_RESOLVED_NARROWED_TO_A_MINUS15_W50`; új residual: `MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`. Q-B05-004: `OPEN_NARROWED_TO_SINGLE_MITSUBISHI_CELL_PLUS_DIMPLEX_FANCOIL_TAU_EQ`. Readiness marad 45%.

B05-P27 repairs the internal semantics of Q-B05-004 without changing its top-level OPEN lineage. The umbrella question is split into explicit P27 subclaims: `PRODUCT_LEVEL_EVIDENCE = RESOLVED_BOUNDED_PRODUCT_EVIDENCE` for the currently proven Mitsubishi/Dimplex surfaces; `COORDINATE_COVERAGE = OPEN` for the remaining exact product-grid gaps; and `OBS_HOURLY_TRANSIENT_FIDELITY = OPEN` for the fan-coil documentation/code divergence plus product-specific `tau_eq`. `PART_LOAD_MODULATION` remains 45% and B05 remains 64%.

B05-P28 audits the product-specific `tau_eq` evidence path. Current HEM requires `tau_eq` as a heat-pump on/off transient characteristic, but the checked exact public PCDB records for PUZ-WM50VHA and LA 2030CP do not expose a product `tau_eq` value. This does not prove internal PCDB/manufacturer data absence. `PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME` therefore remains open but is narrowed to `PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED`. Cdh, minimum modulation, controller anti-cycling time and the 140 s HEM default are explicitly forbidden as product-OBS substitutes. `PART_LOAD_MODULATION` remains 45% and B05 remains 64%.

B05-P29 qualifies bounded product/controller DHW dispatch semantics without promoting controller behavior into high-temperature performance evidence. Mitsubishi PUZ-WM50VHA(-BS) + EHPT20X-MHEDW/FTC6 exposes configurable simultaneous DHW/heating operation and a source-defined post-DHW heating-priority restriction after the maximum DHW operation time. Dimplex LA 2030CP + WPM Touch explicitly switches circulation from space heating to DHW when a DHW request occurs during heating. The generic engine remains fail-closed without explicit controller identity/state, and high-temperature operating-envelope capability is not reused as capacity/COP. Q-B05-005 remains OPEN_NARROWED_TO_STATEFUL_CONTROLLER_RUNTIME_AND_DHW_HIGH_TEMP_PERFORMANCE. DHW_MODE rises to 45%; B05 remains 64%.

B05-P30 resolves Q-B05-006 as a hydraulic-axis admissibility contract. The current canonical performance snapshot contains 53 OBS/DER product points across 11 equipment IDs and no source-native return-temperature or delta-T performance coordinates. Current Dimplex evidence demonstrates why the distinction matters: A7/W35...30 is a fixed EN14511 test condition, return temperature is instrumented, and heating curves are published by outlet-water temperature at fixed water flow. Fixed test condition / sensor / operating limit therefore does not prove performance sensitivity. A return or delta-T axis may be admitted only when exact same-product, same-unit-boundary capacity/input/COP evidence explicitly varies that coordinate at otherwise matched outdoor and supply conditions. With supply retained, return and delta-T are algebraically linked and cannot both be independent axes. Q-B05-006 is RESOLVED_CONTRACT; PERFORMANCE_MAP remains 80% and B05 remains 64%.

## Kanonikus artefaktumok

- `docs/source_packs/B05_HEAT_PUMP_PHYSICAL_MODEL.md`
- `docs/source_packs/B05_P10_NIBE_COLD_HIGH_SUPPLY_CAPACITY_DOMAIN.md`
- `registry/b05_p10_nibe_cold_high_supply_capacity_domain.csv`
- `docs/source_packs/B05_P11_TEKNOPOINT_COLD_HIGH_SUPPLY_RECTANGLE.md`
- `registry/b05_p11_teknopoint_cold_high_supply_rectangle.csv`
- `docs/source_packs/B05_P12_ECPOWER_CROSS_MANUFACTURER_COLD_SURFACE.md`
- `registry/b05_p12_ecpower_cross_manufacturer_cold_surface.csv`
- `data/processed/b05_p12_ecpower_source_capacity_cop_observations.csv`
- `data/processed/b05_p12_cross_manufacturer_cold_high_supply_surface.csv`
- `modules/B05/cold_high_supply_cohort.py`
- `docs/source_packs/B05_P13_WAMAK_EXTREME_COLD_CLOSURE.md`
- `registry/b05_p13_wamak_extreme_cold_closure.csv`
- `data/processed/b05_p13_wamak_source_observations.csv`
- `data/processed/b05_p13_observed_extreme_performance_coverage.csv`
- `docs/source_packs/B05_P14_EN14511_DEFROST_ACCOUNTING_BOUNDARY.md`
- `registry/b05_p14_en14511_defrost_accounting_boundary.csv`
- `data/processed/b05_p14_defrost_point_applicability.csv`
- `modules/B05/defrost_accounting_contract.py`
- `docs/source_packs/B05_P15_KEYMARK_CERTIFIED_CDH_PARTLOAD.md`
- `registry/b05_p15_keymark_certified_cdh_partload.csv`
- `data/processed/b05_p15_vaillant_keymark_partload.csv`
- `modules/B05/part_load_degradation_contract.py`
- `docs/source_packs/B05_P16_CROSS_MANUFACTURER_RUNTIME_GATE.md`
- `registry/b05_p16_runtime_partload_contract.csv`
- `data/processed/b05_p16_bosch_keymark_partload.csv`
- `modules/B05/part_load_runtime_contract.py`
- `docs/source_packs/B05_P17_SAME_PRODUCT_MODULATION_ANCHORS.md`
- `registry/b05_p17_same_product_modulation_anchors.csv`
- `data/processed/b05_p17_same_product_modulation_anchors.csv`
- `modules/B05/modulation_anchor_contract.py`
- `docs/source_packs/B05_P18_EN14825_CYCLING_NUMERIC_METHOD.md`
- `registry/b05_p18_cycling_numeric_method.csv`
- `data/processed/b05_p18_cycling_input_gap.csv`
- `modules/B05/cycling_degradation_method.py`
- `docs/source_packs/B05_P19_CYCLING_INPUT_COLOCATION_GATE.md`
- `registry/b05_p19_cycling_input_colocation_gate.csv`
- `data/processed/b05_p19_cycling_input_coverage.csv`
- `modules/B05/cycling_input_colocation.py`
- `docs/source_packs/B05_P20_QUALIFIED_CYCLING_READY_POINT.md`
- `registry/b05_p20_qualified_cycling_ready_point.csv`
- `data/processed/b05_p20_qualified_cycling_ready_point.csv`
- `modules/B05/qualified_cycling_point.py`
- `docs/source_packs/B05_P21_BOUNDED_MODULATION_FLOOR_SURFACE.md`
- `registry/b05_p21_modulation_floor_surface.csv`
- `data/processed/b05_p21_mitsubishi_modulation_floor_surface.csv`
- `modules/B05/modulation_floor_surface.py`
- `docs/source_packs/B05_P22_MITSUBISHI_EXTENDED_MINIMUM_POINT_GRID.md`
- `registry/b05_p22_mitsubishi_extended_minimum_grid.csv`
- `data/processed/b05_p22_mitsubishi_minimum_point_grid.csv`
- `data/processed/b05_p22_mitsubishi_w35_cycling_bins.csv`
- `modules/B05/minimum_point_surface.py`
- `docs/source_packs/B05_P23_DIMPLEX_SECOND_MODULATION_FLOOR_SURFACE.md`
- `registry/b05_p23_dimplex_second_floor_surface.csv`
- `data/processed/b05_p23_dimplex_modulation_floor_surface.csv`
- `data/processed/b05_p23_dimplex_w35_cycling_bins.csv`
- `modules/B05/barrier_aware_modulation_floor_surface.py`
- `docs/source_packs/B05_P24_HOURLY_CYCLING_METHOD_SEPARATION.md`
- `registry/b05_p24_hourly_cycling_method_separation.csv`
- `modules/B05/hourly_cycling_method.py`
- `docs/source_packs/B05_P25_HEM_TRANSIENT_DEFAULT_AUTHORITY.md`
- `registry/b05_p25_hem_transient_default_authority.csv`
- `modules/B05/hourly_onoff_parameter_policy.py`
- `docs/source_packs/B05_P26_MITSUBISHI_COLD_HIGH_SUPPLY_CLASSIFICATION.md`
- `registry/b05_p26_mitsubishi_cold_high_supply_classification.csv`
- `data/processed/b05_p26_mitsubishi_cold_high_supply_classification.csv`
- `docs/source_packs/B05_P27_QUESTION_LAYER_SEMANTIC_SPLIT.md`
- `registry/b05_p27_question_layer_semantic_split.csv`
- `docs/source_packs/B05_P28_PRODUCT_TAU_EQ_EVIDENCE_PATH.md`
- `registry/b05_p28_product_tau_eq_evidence_path.csv`
- `docs/source_packs/B05_P29_DHW_CONTROLLER_DISPATCH.md`
- `registry/b05_p29_dhw_controller_dispatch.csv`
- `modules/B05/dhw_dispatch_contract.py`
- `docs/source_packs/B05_P30_HYDRAULIC_AXIS_ADMISSIBILITY.md`
- `registry/b05_p30_hydraulic_axis_admissibility.csv`
- `data/processed/b05_p30_hydraulic_axis_snapshot.csv`
- `modules/B05/hydraulic_axis_admissibility.py`
- `modules/B05/engine.py`
- `registry/heat_pump_sources.csv`
- `registry/heat_pump_variables.csv`
- `registry/heat_pump_formulas.csv`
- `registry/heat_pump_scenarios.csv`
- `registry/heat_pump_readiness.csv`
- `data/processed/heat_pump_performance_points.csv`
- `data/processed/heat_pump_performance_coverage.csv`
- `data/processed/heat_pump_weather_scenarios.csv`
- `data/processed/heat_pump_weather_hourly.csv`
- `data/processed/heat_pump_weather_profiles.csv`
- `data/processed/heat_pump_weather_coverage.csv`
- `data/processed/heat_pump_weather_supply_coverage.csv`
- `modules/B05/weather.py`
- `tools/materialize_b05_weather.py` (raw ZIP input outside Git; bounded derived output only)
