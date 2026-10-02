# B05 – Hőszivattyú fizikai és teljesítménymodell

## Current cycling qualification — 2026-10-02

P20/P22 WM50 and P23/P42 Dimplex exact fixed-W35 Cdh/MIN joining are Q.
Manufacturer fixed-coordinate minimum facts and separately scoped certified
Cdh remain valid. The common gate requires source-bound test-water and MIN
transfer authority; caller booleans cannot close it. Conditional P18 algebra
is executable under an explicit conditional status. Historical exact-join
claims below are superseded for physical admission. The original P59 eight-point
execution criterion remains unchanged but unresolved: current component total
is Q/null, with 67 supported points and 8 unresolved weight. Historical 75 is
preserved; B05 module 64 is unchanged. See the V1-035 checkpoint note.

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

- A V1 motor determinisztikus, bounded bilineáris interpolációt használ a teljesítménytérkép teljes téglalap-rácsán. A belső pontokban a hőteljesítményt és a teljes egység villamos inputját interpolálja, majd COP = Q/P; a COP nem harmadik független interpolált felület. Ugyanez érvényes a megengedett hideg oldali egydimenziós interpolációra. Az exact source-native pontok és kerekítési toleranciájuk változatlanok.
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

`PERFORMANCE_MAP=PARTIAL (80%)`; `THERMAL_DEMAND_INTERFACE=PARTIAL`; `WEATHER_INPUT=PARTIAL (75%)`; `WEATHER_SOURCE=VALIDATED`; `HOURLY_WEATHER_INPUT=PARTIAL (85%)`; `REFERENCE_WEATHER=PARTIAL (60%)`; `COLD_1_IN_10=PARTIAL (80%)`; `EXTREME_COLD_EVENT=VALIDATED (90%)`; `SPATIAL_COVERAGE=PARTIAL (60%)`; `WEATHER_PERFORMANCE_DOMAIN_COVERAGE=PARTIAL (60%)`; `DEFROST=PARTIAL (20%)`; `PART_LOAD_MODULATION=PARTIAL (45%)`; `OPERATING_ENVELOPE=PARTIAL (55%)`; `PRODUCT_DIVERSITY=PARTIAL (45%)`; `DHW_MODE=PARTIAL`; `PRODUCT_SCALING=Q`. A B05 státusza ezért `IN_PROGRESS`, nem `VALIDATED`. A jelenlegi B02/B03/B04 dependency edge megmarad orchestration-gate-ként, de a fizikai runtime nem használ tarifát vagy pénzértéket.

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

B05-P31 separates the current HEM fan-coil document/code divergence from OBS-grade emitter physics. Fresh upstream readback on 2026-09-25 confirms HEM-TP-12 v3 still assigns the Light-embedded method value to all wet-distribution heat pumps, while the current official reference implementation main remains commit `5a3ac9728df712332a5625571c43d3bc10bd2bf3` and explicitly maps `FanCoils` to 360 s versus `RadiatorsUfh` to 1370 s. P31 does not choose a winner. It exposes two explicit POL branches: `HEM_TP12_V3_DOCUMENT_POLICY = 1370 s` and `HEM_REFERENCE_CODE_5A3AC972 = 360 s`. The legacy P25 generic fan-coil resolver remains fail-closed. A separate explicit OBS path can use an emitter/manufacturer/lab response-time record without waiting for upstream HEM reconciliation. Therefore `HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED` is resolved as a governance blocker by authority separation, while `FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED` remains open. Product-specific `tau_eq` remains separately open through the P28 product/lab route. PART_LOAD_MODULATION remains 45% and B05 remains 64%.

B05-P32 closes the two P29 residual families in bounded exact Dimplex scope. WPM Touch provides a source-defined stateful DHW request rule using setpoint, hysteresis and current controller-calculated HP maximum temperature; LA 2030CP now has an exact manufacturer W65 table containing min/max Qh, Pel and COP at nine outdoor temperatures. The two evidence layers are joined without graph digitization or interpolation. A unique W65 performance point is executable only when the runtime inverter level is explicitly MIN or MAX and the outdoor temperature matches an exact source-table coordinate. Generic controller state and generic DHW high-temperature performance remain Q outside this product/controller grid. Q-B05-005 remains OPEN_NARROWED_TO_RUNTIME_LEVEL_AND_CROSS_PRODUCT_COVERAGE. DHW_MODE rises from 45% to 60%; B05 remains 64%.

B05-P33 narrows the remaining defrost blocker with exact NIBE S2125 product-family controller and telemetry evidence. The S2125 controller creates a defrost requirement when BT16 is below the configured defrost-start threshold while the compressor runs; the controller exposes time until active defrost, and defrost begins when that value reaches zero. Passive defrost is separately gated by fulfilled compressor demand, an existing defrost requirement and BT28 above the configured passive-defrost cut-out. Active defrost is compressor-on/fan-off; passive defrost is compressor-off/fan-on. Current NIBE Modbus documentation directly exposes BT28, BT16, current compressor frequency and Defrost state 0=off/1=active/2=passive. P33 therefore makes exact defrost state observable/classifiable for this product family, but does not infer BT16 from Hungarian ambient temperature/humidity and does not manufacture event heat or electrical kWh. Q-B05-003 remains OPEN_NARROWED_TO_EVENT_ENERGY_AND_WEATHER_TO_EVAPORATOR_STATE. DEFROST rises from 5% to 20%; B05 remains 64%.

B05-P34 audits the remaining NIBE event-energy path without manufacturing a numeric penalty. Current official NIBE S-Series Modbus authority co-exposes direct S2125 Defrost state with common electrical and thermal measurement channels (including instantaneous used power and cumulative kWh/flow-energy registers), proving that a same-system measurement path is technically available. Public HeatpumpMonitor system 252 and its OpenEnergyMonitor owner discussion bind a real 7.6 kW S2125 R290 Silkeborg installation to public heat/electric monitoring and defrost observations; HeatpumpMonitor also publishes a timestamped timeseries API contract. P34 nevertheless keeps event energy Q because no raw series has been admitted that co-times direct Defrost=1/2 state with exact electrical and thermal meter values on a common event boundary. An executable admission gate now requires same system identity, direct state, contiguous interval-mean measurements, explicit meter boundaries and thermal sign convention before event kWh may be derived. DEFROST remains 20%; B05 remains 64%.

B05-P35 separates HeatpumpMonitor's public heat-loss proxy from direct NIBE event identity and narrows the remaining Silkeborg acquisition artifact. Exact HeatpumpMonitor code at commit a68fdc026bdfc74afe557d952f0d4d96ce76eba5 accumulates negative `heatpump_heat` not classified as cooling into `total_defrost_and_loss_kwh`; this is therefore a negative-heat proxy, not direct controller state. The same backend exposes only configured MyHeatpump app feed keys through the public timeseries API. Separately, the exact system owner documents S2125/S320 internal-sensor ingestion through Modbus/TCP into EmonCMS and later direct `defrosting mode` / `last defrost` logging in Home Assistant. The public `jkjaer/emonhub` fork does not expose the owner's site register configuration, and an isolated hosted API probe was blocked by HTTP 403 before system-252 metadata retrieval. P35 therefore narrows the numeric blocker to an owner raw direct-state export plus a co-timed electric/thermal export; proxy heat loss, screenshots and remote-access failures cannot mint event identity or kWh. DEFROST remains 20%; B05 remains 64%.


B05-P36 resolves the exact Silkeborg co-timed electric/thermal acquisition residual and qualifies a bounded cumulative-energy route through the owner's publicly linked EmonCMS app without storing the public read credential. The exact app exposes heatpump_elec 501345 and heatpump_heat 501342 as 10 s W feeds; the audited day yields 8297 common non-null timestamps and 596 negative-heat points. Direct W integration remains forbidden because PHPFina is Fixed Interval No Averaging. Separately, pinned MyHeatpump code defines heatpump_elec_kwh / heatpump_heat_kwh as cumulative energy and computes window energy as end minus start. An exact four-feed field probe then yields 68 common timestamps, 42/42 negative thermal points with negative thermal-kWh delta and zero reset-like >1 kWh steps across 67 deltas. Thus both SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED and the qualified cumulative-delta route are resolved; raw direct NIBE Defrost state/event boundary is the remaining exact-system event-energy blocker. No numeric event kWh is minted. DEFROST remains 20%; B05 remains 64%.


B05-P37 audits the remaining direct-state acquisition boundary instead of treating negative heat or a generic operating mode as event identity. The exact Silkeborg public EmonCMS read route reports 13 feeds; a targeted direct-state candidate scan returns only S2125 Operation Mode 501344. Co-timed readback shows 10/20/30 values across 8297 thermal timestamps, and NIBE prioritisation semantics plus persistence through negative-heat runs exclude that feed as Defrost 0/1/2. The public EmonCMS input list contains exactly seven names — OutdoorTemp, FlowRate, TargetSupplyTemp, OperationMode, ReturnTemp, SupplyTemp and CurPwr — with no direct Defrost input. This bounded public result is not promoted to private Home Assistant absence. Independent real S2125 implementations prove that direct 1805/HA state can be historized into InfluxDB, so the remaining blocker is narrowed to an exact Silkeborg private HA history export or a prospective exact-system 1805 logger export containing one complete OFF→ACTIVE/PASSIVE→OFF event. No numeric event kWh is minted. DEFROST remains 20%; B05 remains 64%.


B05-P38 performs the final bounded public acquisition attack for one complete S2125 direct defrost event package. A hosted HeatpumpMonitor API scan reads 809 current public systems and identifies four S2125 systems: 252 Silkeborg, 448 Bristol, 660 Farnham and 729 Molesey. Every system exposes electric/thermal energy surfaces, but every /timeseries/available result has zero direct-state candidates. Additional metadata and heatpump-page route probes for 448/660/729 find only internal HeatpumpMonitor routes and zero linked public EmonCMS app routes; 252's separate owner EmonCMS surface was already audited in P36/P37. Independent S2125 Home Assistant/InfluxDB field evidence still proves direct-state history exists and can be co-displayed with compressor frequency, BF1 flow, EB101 power and temperatures, so the fleet result is explicitly bounded and never treated as global absence. The event residual is consolidated to S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED; Silkeborg private HA history plus P36 energy remains one valid route, or another exact S2125 may supply state+electric+thermal on one timebase. No numeric event kWh is minted. DEFROST remains 20%; B05 remains 64%. Next independent priority: WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED.


B05-P39 narrows the weather-to-evaporator blocker to a concrete observed telemetry object instead of inventing an ambient-weather formula. Official S2125 control semantics require BT16 plus compressor/controller state and directly expose BT28, BT16, current compressor frequency and Defrost 0/1/2. A hosted probe of two publicly linked MyHeatpump EmonCMS systems finds only metoffice outside_temperature among targeted weather/evaporator/controller candidates: app 1 has 14 feeds/123 inputs, app 2 has 9 feeds/55 inputs, and neither exposes a BT16/evaporator/direct-state input candidate. Independent exact S2125 field evidence proves HA/Influx direct-state historization, BT16 HA monitoring and USB diagnostic logging routes exist. An exact S2125+SMO20 myUplink issue exposes 579 entities but its diagnostics attachment is currently unavailable, so no raw channel content is inferred. WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED is narrowed to S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED. Direct Modbus, actual USB raw logs and raw HA/Influx history are admissible acquisition classes only with exact system identity and explicit cadence, scaling and aggregation semantics. No numeric weather-to-BT16 mapping or frequency curve is minted. DEFROST remains 20%; B05 remains 64%.


B05-P40 acquires the first public machine-readable exact S2125 same-response OBS snapshot containing every P39 target signal. A pinned SvenPausH/NibeAPI field export from an owner-identified S2125-12 + VVMS320 system contains source-native raw/scaled BT28 (1621: 8.3 C), BT16 (1622: 4.9 C), current compressor frequency (1803: 20 Hz) and direct Defrost (1805: 0) in the same exported API response at source-native timestamp 2026-05-13 20:36:13; the source does not state timezone. The raw third-party JSON is not copied into the public repository. The pinned NibeAPI implementation refreshes the REST API at a 10 s default interval and can write scaled timestamped input-register values to InfluxDB, but the owner's historical Influx rows are not public. Therefore S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED is only PARTIAL_RESOLVED_TO_SINGLE_SNAPSHOT and the exact residual becomes S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED. One non-defrost snapshot cannot create a weather-to-BT16 model or defrost-frequency curve. DEFROST remains 20%; B05 remains 64%.

B05-P42 freezes the independent S2125 defrost acquisition path and returns to Q-B05-004. A current Dimplex System C Version 03/2026 detailed table set publishes a complete LA2030CP minimum Qh/Pel/COP surface over ten outdoor nodes (-22,-15,-10,-7,2,7,12,20,30,40 C) and W35/W45/W55. This is 30 exact source-native points and 18 complete bounded cells. The previously blocked A-10 row is explicit at W35/W45/W55, so the A-10 interpolation barrier is retired. Because the current detailed revision differs from the older P23 summary at some coordinates, P42 supersedes the P23 Dimplex surface for current model use and forbids cross-version mixing. The canonical P9 stress interval is continuously covered at W35/W45/W55. A fresh Mitsubishi current-databook recheck does not close A-15/W50: Vol.6.0 still leaves that coordinate blank across Max/Nominal/Mid/Min, while no exact tabular operating threshold resolves physical applicability. The cell remains fail-closed Q. PART_LOAD_MODULATION remains 45% and B05 remains 64%.

B05-P43 attacks the remaining Q-B05-004 OBS transient-fidelity residuals without manufacturing either response constant. A real fan-coil laboratory study is admitted only as system-level dynamic evidence because it measures room operative temperature for a room+FCU cooling setup; room response, cooling-only response and HEM policy constants cannot populate the physical fan-coil emitter-response variable. Peer-reviewed AWHP on/off literature confirms that measured heat-pump transient time constants vary materially across units/control hardware and explicitly requires detailed seconds-scale testing for a given unit; published generic values therefore cannot populate product tau_eq. Current HP KEYMARK records bind the two canonical targets to named laboratories: LA 2030CP / registration 40060852 -> VDE Prüf- und Zertifizierungsinstitut GmbH, and PUZ-WM50VHA(-BS) within registration 037-0032-20 rev.2 -> SZU Brno. Public KEYMARK certification surfaces identify the lab but do not expose product tau_eq or raw transient traces. P43 adds executable fail-closed admission gates and narrows acquisition to an emitter-output heating step-response record plus an exact-product seconds-scale manufacturer/named-lab transient record. PART_LOAD_MODULATION remains 45% and B05 remains 64%.

B05-P44 performs a second public-web attack on the two remaining OBS transient-fidelity paths and deliberately tightens P43 where the evidence is weaker than the acquisition hypothesis. The exact Dimplex LA2030CP VDE/KEYMARK certificate 40060852 identifies test Report `328782-TL2-1` and Appendix 601 dated 2025-08-29. Current Heat Pump KEYMARK Annex A independently requires recognised-laboratory admission/surveillance testing at certification-body-selected EN14825 part-load conditions, and current UK PCDB listing requirements require complete EN14825 reports. However, the public PCDB EN14825 declaration surface exposes part-load capacity/COP/Cdh but no `tau_eq` or seconds-scale trace. P44 therefore freezes `COMPLETE_EN14825_REPORT_EXISTS != PRODUCT_TAU_EQ_OR_RAW_TRANSIENT_TRACE_PROVEN`. A new Bosch route strengthens the Dimplex search path without permitting cross-product transfer: Bosch CS5001AW22 VDE certificate 40061610 names Glen Dimplex Deutschland GmbH as the production site, and Bosch's 2026 ErP declaration explicitly cites Dimplex report number `328782-TL2-1`; nevertheless Bosch/Dimplex platform evidence is not promoted to exact product identity. U-CERT reproduces EN15316-4-2 heat-pump inertia default `TAU_EQ=30 s`, while the UK SAP/HEM branch uses 140 s; this confirms that a policy/default value is authority-specific, not product physics. Additional 2026 heating-mode FCU experiments remain room/system-response evidence rather than direct emitter heat-output step response. P44 also recovers two closer terminal-level experimental routes: a 2021 fan-coil start-up-to-stabilization energy-flow study and a 2023 experiment-validated 2R1C heating-terminal model whose parameter acquisition uses water flow and dynamic water/terminal-surface/room temperatures with heat-flux validation. These prove that emitter-level dynamic measurement is experimentally established, but the inspected public layers still do not expose one exact FCU specimen plus an explicit emitter heat-output response constant at the project's admission grain. Q-B05-004 remains OPEN; PART_LOAD_MODULATION remains 45% and B05 remains 64%.

B05-P45 attacks the exact Dimplex VDE report object before any external request. Report `328782-TL2-1` is independently bound by the LA2030CP VDE/KEYMARK certificate and the Bosch CS5001AW22 ErP declaration, but an exact-ID/format-variant sweep across indexed public web surfaces and targeted VDE/Dimplex/Bosch domains does not recover the underlying report, Appendix 601 content or a source-native transient excerpt. This is deliberately recorded as public recoverability evidence only: `PUBLIC_INDEX_SEARCH_MISS != REPORT_NONEXISTENCE != INTERNAL_CONTENT_ABSENCE`. The official VDE catalogue describes certificate/product/technical-data outputs; the HP KEYMARK five-page LA2030CP public export exposes EN14511 pass/fail items and EN14825 Prated/SCOP/Tbiv/TOL/Pdh/COP/Cdh plus auxiliary powers, but no `tau_eq`, transient, time-constant or seconds-scale trace field. The Dimplex residual therefore narrows to `EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED`. No physical parameter is minted; PART_LOAD_MODULATION remains 45% and B05 remains 64%.

B05-P46 re-attacks the sole remaining Mitsubishi cold/high-supply coordinate without relaxing P26's no-digitization boundary. PUZ-WM50VHA(-BS) A-15/W50 is blank across all published performance levels in Vol.5.3, Vol.5.9 and current Vol.6.0, while A-15/W35/W40/W45 and A-10/W50/W55 remain source-native populated neighbours. Two independent official Mitsubishi publication surfaces reinforce the same publication boundary: Mitsubishi Sweden gives A-15/W35=3.9 kW and A-15/W45=3.9 kW, and Mitsubishi France's 2026 catalogue gives A-15/W35/W45 maximum output 3.90/3.90 kW, with neither surface publishing W50 at A-15. P46 freezes that persistent omission as source-availability evidence only. A general maximum outlet temperature plus a separate ambient operating range may not be composed into a synthetic two-dimensional coordinate. The residual therefore narrows to `EXACT_SOURCE_NATIVE_A_MINUS15_W50_2D_OPERATING_OR_PERFORMANCE_RECORD_REQUIRED`; graph digitization, interpolation and blank=unsupported remain forbidden. PART_LOAD_MODULATION remains 45% and B05 remains 64%.

B05-P47 corrects the Mitsubishi transient-report acquisition grain before any external request. The original SZU certificate 037-0032-20 and current rev.2 certificate bind PUZ-WM50VHA(-BS) product scope and SZU/KEYMARK authority but expose neither tested-sample identity nor underlying report/protocol ID. The current public KEYMARK database adds detailed EN14511/EN14825 values and pass/fail operating tests but still no raw transient trace. More importantly, the exact PUZ-WM50VHA(-BS) outdoor unit appears under multiple registrations (037-0030-20 rev.2 and 037-0032-20 rev.2), while official KEYMARK sampling rules establish that certification scope may exceed directly tested subtype scope: Annex A Rev.3 already required only one tested subtype for up to five certified non-air/air subtypes, and current Scheme Rev.15 explicitly states that one air/water test can certify five subtypes and that the test report is communicated to the certification body. P47 therefore freezes `REGISTRATION_ID != UNIQUE_TESTED_SPECIMEN != TEST_REPORT_ID`. Exact public report/protocol searches did not recover the underlying SZU report, but non-recovery is not nonexistence. A historical MCS product-directory capture additionally resolves 037-0032-20-01/02 as PUZ-WM50VHA / PUZ-WM50VHA-BS model-level certification identifiers, so those suffixes are explicitly forbidden as guessed SZU report IDs. The Mitsubishi transient residual narrows to `EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`. No product tau is minted; PART_LOAD_MODULATION remains 45% and B05 remains 64%.

B05-P48 converts the P47 Mitsubishi/SZU lineage blocker into an exact human-gated acquisition package without sending any request. Current KEYMARK sampling semantics require certification-body sample selection from serial-traceable units and transmission of the test report to the certification body; the public KEYMARK document index exposes Annex L as the sampling-template artifact class, but no filled Mitsubishi sampling record was recovered. P48 therefore defines the source-native fields required from a response: tested subtype/model, direct-test/specimen binding, exact report/protocol ID and date, testing laboratory, test conditions, and whether the record contains direct `tau_eq` or a seconds-scale trace sufficient for explicit derivation. Official routes are pinned to SZU product-certification/COSM and Mitsubishi Ecodan technical support. The canonical dispatch state is `ACQUISITION_PACKAGE_READY_UNSENT`; no external send is authorized. Contact readiness is not physical readiness: the residual remains `EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`, PART_LOAD_MODULATION remains 45%, and B05 remains 64%.

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
- `docs/source_packs/B05_P31_FANCOIL_POL_OBS_AUTHORITY_SEPARATION.md`
- `registry/b05_p31_fancoil_authority_separation.csv`
- `modules/B05/fan_coil_authority_separation.py`
- `docs/source_packs/B05_P32_DHW_STATEFUL_W65_RUNTIME.md`
- `registry/b05_p32_dhw_stateful_w65_runtime.csv`
- `data/processed/b05_p32_dimplex_w65_performance.csv`
- `modules/B05/dhw_stateful_high_temp.py`
- `docs/source_packs/B05_P33_NIBE_DEFROST_STATE_TELEMETRY.md`
- `registry/b05_p33_nibe_defrost_runtime.csv`
- `data/processed/b05_p33_nibe_s2125_modbus_channels.csv`
- `modules/B05/defrost_runtime_state.py`
- `docs/source_packs/B05_P34_NIBE_DEFROST_EVENT_ENERGY_ADMISSION.md`
- `registry/b05_p34_nibe_defrost_event_energy_admission.csv`
- `data/processed/b05_p34_public_nibe_defrost_evidence_inventory.csv`
- `modules/B05/defrost_event_energy_admission.py`
- `docs/source_packs/B05_P35_NIBE_DEFROST_DIRECT_STATE_EXPORT_BOUNDARY.md`
- `registry/b05_p35_nibe_defrost_direct_state_export_boundary.csv`
- `data/processed/b05_p35_silkeborg_defrost_source_inventory.csv`
- `modules/B05/defrost_identity_source_contract.py`
- `docs/source_packs/B05_P36_SILKEBORG_COTIMED_METER_EXPORT.md`
- `registry/b05_p36_silkeborg_cotimed_meter_export.csv`
- `data/processed/b05_p36_silkeborg_public_meter_export_inventory.csv`
- `modules/B05/defrost_meter_export_contract.py`
- `docs/source_packs/B05_P37_S2125_DIRECT_STATE_PUBLIC_ACQUISITION.md`
- `registry/b05_p37_s2125_direct_state_public_acquisition.csv`
- `data/processed/b05_p37_s2125_public_state_surface_inventory.csv`
- `modules/B05/direct_defrost_state_acquisition.py`
- `docs/source_packs/B05_P38_PUBLIC_S2125_DIRECT_EVENT_ACQUISITION.md`
- `registry/b05_p38_public_s2125_direct_event_acquisition.csv`
- `data/processed/b05_p38_public_s2125_fleet_inventory.csv`
- `modules/B05/public_s2125_direct_event_acquisition.py`
- `docs/source_packs/B05_P39_BT16_OBSERVED_TIMESERIES_ACQUISITION.md`
- `registry/b05_p39_bt16_observed_timeseries_acquisition.csv`
- `data/processed/b05_p39_bt16_acquisition_route_inventory.csv`
- `modules/B05/bt16_observed_timeseries_contract.py`
- `docs/source_packs/B05_P40_S2125_FOUR_SIGNAL_OBS_SNAPSHOT.md`
- `registry/b05_p40_s2125_four_signal_obs_snapshot.csv`
- `data/processed/b05_p40_s2125_four_signal_obs_snapshot.csv`
- `modules/B05/s2125_four_signal_snapshot_contract.py`
- `docs/source_packs/B05_P43_TRANSIENT_FIDELITY_ADMISSION.md`
- `registry/b05_p43_transient_fidelity_admission.csv`
- `data/processed/b05_p43_transient_evidence_inventory.csv`
- `modules/B05/transient_fidelity_admission.py`
- `docs/source_packs/B05_P44_TRANSIENT_REPORT_LINEAGE.md`
- `registry/b05_p44_transient_report_lineage.csv`
- `data/processed/b05_p44_transient_report_inventory.csv`
- `modules/B05/transient_report_lineage.py`
- `docs/source_packs/B05_P45_DIMPLEX_VDE_REPORT_RECOVERABILITY.md`
- `registry/b05_p45_dimplex_vde_report_recoverability.csv`
- `data/processed/b05_p45_dimplex_vde_report_recoverability.csv`
- `modules/B05/transient_report_recoverability.py`
- `docs/source_packs/B05_P46_MITSUBISHI_A15_W50_DOMAIN_BOUNDARY.md`
- `registry/b05_p46_mitsubishi_a15_w50_domain_boundary.csv`
- `data/processed/b05_p46_mitsubishi_a15_w50_evidence.csv`
- `modules/B05/mitsubishi_a15_w50_domain_gate.py`
- `docs/source_packs/B05_P47_MITSUBISHI_SZU_SAMPLING_REPORT_BOUNDARY.md`
- `registry/b05_p47_mitsubishi_szu_sampling_report_boundary.csv`
- `data/processed/b05_p47_mitsubishi_szu_sampling_inventory.csv`
- `modules/B05/mitsubishi_szu_sampling_report_boundary.py`
- `docs/source_packs/B05_P48_MITSUBISHI_SZU_ACQUISITION_PACKAGE.md`
- `registry/b05_p48_mitsubishi_szu_acquisition_package.csv`
- `data/processed/b05_p48_mitsubishi_szu_acquisition_targets.csv`
- `modules/B05/mitsubishi_szu_acquisition_package.py`
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


B05-P52 separates the exact S2125 passive-defrost branch from active reverse-cycle defrost using the pinned P49 owner raw package. All 102 direct Defrost=2 samples across 22 runs are compressor-off and requested-compressor-off with source-native qheat406=0 while the outdoor fan remains positive. Median passive duration is 180.5 s. The unchanged P49 Victron integration reproduces the active P49 result before deriving passive measured-covered state-window electricity (median 0.004854669 kWh), but short passive windows have materially lower boundary coverage (median 94.9480%). A strict compressor-off matched-control attack supports only 5/9 HEAT events and 0/11 DHW events, so P52 does not mint a branch-wide causal passive increment and does not transfer the P50 signed-thermal factor into compressor-off operation. PASSIVE_DEFROST_BRANCH_REQUIRED -> PARTIAL_RESOLVED_TO_DIRECT_PASSIVE_STATE_AND_MEASURED_WINDOW_ELECTRICITY. DEFROST remains 20%; B05 remains 64%.


B05-P53 resolves the exact-system S2125 pre-DHW active-defrost branch without pooling it with HEAT. P50 matched-DHW n=46 / median direct electrical delta -0.018409 kWh is exactly reproduced; P53 primary strict n=35 gives median -0.019820 kWh with bootstrap median 95% CI -0.058569..-0.005337. QN10 routing shows that pre-DHW state usually does not remain the DHW hydraulic path during active defrost (32/35 strict events diverted). Source-native compressor-only DHW energy register 1583 is monotonic and gives strict matched active-window shortfall median 0.20 kWh; 26/35 strict events show sustained counter catch-up before censoring, median 14.5 min. P50's HEAT signed-thermal factor is not transferred to DHW and no universal/full-cycle DHW constant is admitted. DHW_DEFROST_BRANCH_REQUIRED -> RESOLVED_FOR_EXACT_SYSTEM_ACTIVE_DHW_ORIGIN_AND_SOURCE_NATIVE_COUNTER_BRANCH. DEFROST remains 20%; B05 remains 64%.


B05-P54 performs the deferred successor-aware DEFROST readiness recalibration over the P49-P53 evidence stack. The new explicit 11-gate scorecard totals 100 possible points and awards 65: direct state semantics, exact same-system raw event boundary, electrical coverage and strict active-HEAT matched effect are resolved; signed thermal, recovery/full-cycle, passive, DHW and state-conditioned predictive gates remain partial; cross-product replication and Hungarian weather/event-frequency transfer remain open. DEFROST therefore moves **20 -> 65** and remains PARTIAL. A hard ceiling of 65 applies until independent replication. Q-B05-003 residuals are unchanged. B05 overall remains **64%** because no canonical component-to-module aggregation authority exists; P54 does not invent one.


B05-P56 resolves the generic fan-coil heating dynamic-record search target to an exact **Trane FCC06** physical record. The peer-reviewed 2019 living-lab study provides explicit fan-speed step tests, minute-scale water-side measurements, 32 thermodynamic identification runs, a state-dependent switched-linear `Uo(x,qw)` heating surface and <6% open-loop validation error. P56 preserves the physical semantics: the 8 min test engagement is not a 480 s response constant, and a state-dependent FCC06 water-state time constant is not silently mapped to the HEM/EN15316 scalar `tau_out`. Numeric state-time derivation remains fail-closed until exact FCC06 in-coil water mass is bound. Q-B05-004 remains OPEN; PART_LOAD_MODULATION remains **45%** and B05 remains **64%**.

P56 canonical artifacts:

- `docs/source_packs/B05_P56_FCC06_STATE_DEPENDENT_RESPONSE.md`
- `registry/b05_p56_fcc06_state_dependent_response.csv`
- `data/processed/b05_p56_fcc06_dynamic_evidence.csv`
- `modules/B05/fcu_state_dependent_response.py`


B05-P57 resolves the FCC06 `state-response -> HEM tau_out mapping OR direct runtime` fork by choosing the second route: an exact constant-input analytical step of the peer-reviewed FCC06 water-side ODE. The bounded direct path consumes fan state, water mass flow, explicit study-compatible water mass, medium heat capacity, inlet/zone/outlet temperatures and timestep; it does not require or assert one HEM/EN15316 scalar `tau_out`. Catalogue lineage is tightened separately: the paper-cited Trane `UNT-PRC006-E4` (2010) document identity is publicly recoverable, while a separate Trane UniTrane product-guide revision exposes **1.7 L** for size-06 2-pipe/3-row water content and **0.29 L** for the non-applicable 4-pipe/1-row heating coil. P57 keeps 1.7 L as cross-revision corroboration only and forbids `1.7 L = 1.7 kg` without exact cited-edition binding plus explicit medium density. Q-B05-004 remains OPEN; PART_LOAD_MODULATION remains **45%** and B05 remains **64%**.

P57 canonical artifacts:

- `docs/source_packs/B05_P57_FCC06_WATER_CONTENT_LINEAGE.md`
- `registry/b05_p57_fcc06_water_content_lineage.csv`
- `data/processed/b05_p57_fcc06_water_content_evidence.csv`
- `modules/B05/fcc06_direct_runtime.py`


B05-P58 narrows the remaining FCC06 water-mass blocker. Two Trane manufacturer catalogue revisions — **PROD-PRC011-E4 (2004)** and **PROD-PRC014-E4 (2006)** — independently publish **1.7 L** for the FCC06 size-06 / 2-pipe / 3-row water-content branch. The exact experiment-cited **UNT-PRC006-E4 (2010)** document and page-16 General Data location are known, but its numeric cell remains unrecovered, so the repeated 1.7 L value is admitted only for explicit ASS sensitivity and never relabeled exact study OBS. From the published FCC06 ODE, P58 makes two structural facts executable: steady-state outlet temperature/power are independent of `m_w`, while the first-order state time constant scales linearly with `m_w`. The exact-mass residual is therefore narrowed to **OBS transient validation** rather than generic FCC06 runtime. PART_LOAD_MODULATION remains **45%** and B05 remains **64%**.

P58 canonical artifacts:

- `docs/source_packs/B05_P58_FCC06_MASS_SENSITIVITY.md`
- `registry/b05_p58_fcc06_mass_sensitivity.csv`
- `data/processed/b05_p58_fcc06_water_content_stability.csv`
- `modules/B05/fcc06_mass_sensitivity.py`


B05-P59 performs the deferred successor-aware **PART_LOAD_MODULATION** readiness recalibration across the accumulated P15-P58 evidence stack. An explicit 12-gate / 100-point scorecard awards **75 points**. Source-native minimum-modulation surfaces, same-point minimum capacity/COP pairing, bounded multi-manufacturer product evidence, certified Cdh, EN14825 standard-bin cycling, hourly-method separation and explicit bounded default runtime policy are resolved. Cold/high-supply coordinate coverage, one-system field cycling validation and exact FCC06 transient physics remain partial. Product-specific Dimplex/Mitsubishi heat-pump transient authority and exact FCC06 OBS transient mass binding remain open zero-credit gates. Therefore **PART_LOAD_MODULATION moves 45 -> 75** and remains PARTIAL. Q-B05-004 remains OPEN / E2 / VALIDATION_BLOCKER / MODEL_CONTINUE. B05 overall remains **64%** because no canonical component-to-module aggregation authority exists.

P59 canonical artifacts:

- `docs/source_packs/B05_P59_PART_LOAD_READINESS_RECALIBRATION.md`
- `registry/b05_p59_part_load_readiness_scorecard.csv`
- `modules/B05/part_load_readiness_recalibration.py`

## V1 weather interval support

[Reused source-window adapter](../../docs/checkpoints/V1_007_B05_WEATHER_TIME_SUPPORT.md) retains HungaroMet observation endpoints and exposes the preceding temperature-average interval. Concurrent energy/price joins must use interval_start_utc; endpoint humidity is not an hourly mean.

## V1 explicit manufacturer reference

[WM50 source-condition reference](../../docs/checkpoints/V1_011_WM50_SOURCE_REFERENCE.md) preserves four separate frequency modes, 208 capacity/COP pairs, 44 source blanks and exact defrost annotations. `manufacturer_wm50_reference.py` uses existing bounded Q/input interpolation; an explicit fixed-supply column is available without filling source gaps. It does not change the default dispatch surface or establish annual/national efficiency.
