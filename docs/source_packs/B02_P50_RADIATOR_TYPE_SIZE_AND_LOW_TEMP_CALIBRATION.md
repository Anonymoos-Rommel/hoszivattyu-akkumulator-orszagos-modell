# B02-P50 — radiator type/size and low-temperature calibration

**State:** `BOUNDED TYPE-SIZE EVIDENCE MATERIALIZED / LOW-TEMPERATURE ENGINEERING CHAIN MATERIALIZED / NATIONAL P42 STILL Q`

**Canonical base:** `a97aad2699ad0224a5ed8bb5b2606b862a68c798`

**Implementation date:** 2026-09-07

## 1. Purpose

P50 moves from the P44-P49 quantity branch into the next programme-critical question:

`HOW MANY RADIATORS -> WHAT TYPE/SIZE -> OUTPUT AT TARGET WATER TEMPERATURE -> KEEP / UPSIZE / CHANGE -> B06`

The slice materializes exact bounded residential type/size evidence and one source-native low-temperature engineering chain. It does not infer a national radiator type distribution from a handful of households, one panel circuit, product-market shares, or historical production.

Hard boundaries:

`BOUNDED TYPE-SIZE OBSERVATION != NATIONAL TYPE-SIZE DISTRIBUTION`

`PUBLIC SELF-REPORT != REPRESENTATIVE STOCK`

`SOURCE-REPORTED DIMENSION != CATALOGUE NOMINAL SIZE`

`PARTIAL ROOM CIRCUIT != WHOLE-DWELLING EMITTER INVENTORY`

`TARGET-TEMPERATURE OUTPUT + ROOM HEAT LOSS != AUTOMATIC KEEP/CHANGE WITHOUT SOURCE/ENGINEERING RULE`

`HISTORICAL HEATING SURFACE M2 != PHYSICAL RADIATOR UNIT COUNT`

`ZFR REQUIRED TABLE != PUBLICLY RECOVERED BENEFICIARY TABLE`

`DUPLICATED PROPERTY/REQUEST COPY != INDEPENDENT OBSERVATION`

All five P42 national claims remain `Q` and `programme_use_allowed=NO`.

## 2. Materialized residential type/size evidence

### 2.1 Pécs panel: existing RADAL variants plus 55 C performance

Primary source:

`https://ojs.emt.ro/EPKO/article/download/2032/2100/3148`

Title:

`Iparosított technológiával létesített lakóépületek szerkezeti korszerűsítését követő minimális fűtéstechnikai beavatkozásai`

The 2025 PTE engineering paper documents an uninsulated Pécs panel building with studio dwellings, a TR one-pipe heating system, RADAL 600 radiators and pipe emitters in kitchens/bathrooms.

Exact source locators:

- PDF page 2/6, section 2.1 and table 1: the studied riser serves the rooms of dwellings on five floors and the existing radiator variants are `RADAL 600-11`, `RADAL 600-9`, `RADAL 600-10`, `RADAL 600-11`, `RADAL 600-22` from floors V to I;
- PDF page 3/6, table 2 in PDF text indexing / printed table immediately following section 2.2: full structural retrofit at `te=55 C` gives the following **radiator + pipe** outputs and post-envelope room heat losses:

| Floor | Existing radiator | Output at te=55 C | Post-envelope room heat loss | Diagnostic margin |
|---|---|---:|---:|---:|
| V | RADAL 600-11 | 873 W | 750 W | +123 W |
| IV | RADAL 600-9 | 627 W | 662 W | -35 W |
| III | RADAL 600-10 | 635 W | 662 W | -27 W |
| II | RADAL 600-11 | 636 W | 662 W | -26 W |
| I | RADAL 600-22 | 864 W | 782 W | +82 W |

The paper's source-native conclusion is more important than a simplistic sign test: after full envelope retrofit, central supply-temperature reduction from 90 C to 55 C can closely align output to the reduced heat need **without in-dwelling capacity-matching work in the studied circuit**, provided the original design flow rates can be maintained and the hydraulic system is suitable.

Therefore P50 stores the arithmetic margin as a diagnostic only. It does **not** translate `margin < 0` into an automatic `CHANGE` decision.

The same paper separately states that under partial envelope retrofit the lower-floor room can constrain the achievable supply temperature and one solution is to replace the lower-floor radiator with a higher-output radiator. This directly supports the programme chain:

`POST-ENVELOPE ROOM HEAT LOSS + EXISTING EMITTER OUTPUT AT TARGET WATER TEMP + HYDRAULICS -> KEEP / UPSIZE / CHANGE`

Important scope boundary: the five materialized radiators are the room radiators on one studied vertical circuit. Kitchen and bathroom pipe emitters exist outside that circuit. P50 therefore refuses a whole-dwelling radiator ratio from this source.

### 2.2 Kerepes: complete source-reported 22K size mix in one 85 m2 house

Public source:

`https://qjob.hu/bekescsaba/munka/kazangepesz-allas`

The syndicated Qjob service request states that the property is an `85 m2` family house in Kerepes with `5 db radiátor`, all `22k`, `60 cm` high, connected with copper pipe. The source then gives the full stated length set:

- `2 db 156 cm`;
- `1 db 73 cm`;
- `1 db 60 cm`;
- `1 db 40 cm`.

P50 preserves these as source-reported dimensions and converts centimetres to millimetres only:

- H600 x L1560: 2 units;
- H600 x L730: 1 unit;
- H600 x L600: 1 unit;
- H600 x L400: 1 unit.

Bounded cohort diagnostics:

- total = `5` radiators;
- `5.0 radiators/dwelling` for this one household only;
- `5 / 85 * 100 = 5.882353 radiators/100m2` for this one household only;
- source-native type share = `22K: 100%`;
- source-reported length shares = `1560 mm: 40%`, each other length `20%`.

The reported `156 cm` and `73 cm` values are deliberately **not** normalized to likely commercial catalogue lengths such as 1600/700/720 mm. A measured/stated dimension is not silently rewritten into a product SKU.

The same request appears on multiple Qjob city/category feeds. These are syndicated copies of one request and therefore one observation identity, not multiple independent households.

### 2.3 Erdőkertes: 10 installed 22K radiators in one 175 m2 house

Public property source:

`https://ingatlan.jofogas.hu/pest/175_nm_es_haz_elado_Erdokertes_151880838.htm`

Exact listing facts:

- house size: `175 m2`;
- Immergas 24 kW condensing gas boiler;
- bathroom floor heating;
- `10 db 22K típ radiátor került felszerelésre az ingatlanban`.

P50 admits:

`1 dwelling -> 10 installed 22K radiators`

and leaves size fields blank because the listing does not publish radiator dimensions.

The same property is copied in other listings under reference `HZ036690`; copies are not independent stock observations.

## 3. Official ZFR all-radiator type/size table contract

Official source:

`https://tav2019.nffku.hu/data/webfiles/ZFR-TAV-2019_PU_190617.pdf`

The ZFR-TÁV/2019 programme guide requires the technical description, for radiator replacement, to contain a summary table covering **every radiator**, with:

- original radiator dimensions;
- new radiator dimensions;
- performance change;
- water-temperature change.

The same technical description also requires the building dwelling count, design secondary temperatures, flow rates, hydraulic resistance/topology, typical emitter types/connections and hydraulic balancing concept.

This is important because it proves that project-level records capable of answering the type/size/replacement question were contractually generated.

But:

`MANDATORY BENEFICIARY TABLE SCHEMA != PUBLICLY RECOVERED NUMERIC TABLE`

P50 does not invent any beneficiary type-size distribution from the existence of the form. The next high-value recovery route is to locate already-public beneficiary technical descriptions or attachments keyed by ZFR project identity.

## 4. Non-residential technical cross-check — not residential stock

A Jászapáti public project plan publishes exact pre-development radiator rows for a municipal office/workshop, including source-native RADAL type/size/output/count entries such as:

- `RADAL 600 10 tagos` / size token `860` / `1.779 kW` / 4 units;
- `RADAL 600 15 tagos` / `1310` / `2.669 kW` / 4;
- `RADAL 600 22 tagos` / `1835` / `3.914 kW` / 2.

A Jászivány municipal project similarly publishes Dunaferr DK 600 and RADAL 600 variants with type, size token, nominal performance and count.

These sources demonstrate that source-native variant-to-dimension tables can be recovered, and they can be useful engineering controls for legacy radiator nomenclature. They are **not residential observations** and therefore P50 does not use them to weight residential stock composition.

Hard boundary:

`NON-RESIDENTIAL TYPE-SIZE MAPPING != RESIDENTIAL STOCK DISTRIBUTION`

## 5. Historical RADAL magnitude control

GREEN BRANDS Hungary 2019/2020, using brand-supplied Lehel material, states that RADAL radiators developed with the expansion of prefabricated housing in the 1970s and that `30 million square metres of heating surface` from these radiators were installed **in Hungary alone**, with additional exports.

Source:

`https://green-brands.hu/2020/wp-content/uploads/2020/12/GBHU_2020_publication-final.pdf`

Exact locator: PDF page 15/19 in the web renderer, LEHEL Radiátor brand history section.

This is a useful historical magnitude/material control. It is not a current unit count:

`30,000,000 m2 HEATING SURFACE != 30,000,000 RADIATOR UNITS`

`HISTORICAL INSTALLED RADAL SURFACE != CURRENT RADAL STOCK AFTER DECADES OF REPLACEMENT`

No unit conversion is made.

## 6. Executable P50 contract

`modules/B02/radiator_type_size_calibration.py` provides:

- `RadiatorTypeSizeCandidate`;
- `assess_radiator_type_size()`;
- `summarize_bounded_cohort()`.

The gate requires exact source identity/locator, positive physical counts, valid source role, source-bounded cohort binding and reproducibility. Current whole-dwelling rows additionally require current residential scope, an explicit whole-dwelling inventory flag and a dwelling denominator.

The cohort summarizer:

1. accepts exactly one `cohort_id`;
2. rejects mixed roles;
3. rejects duplicate anchor rows;
4. rejects any unqualified row;
5. computes total units, source-native type shares and source-native variant shares only inside that bounded cohort;
6. computes dwelling/area intensity only for complete current whole-dwelling cohorts;
7. never returns national P42 authority.

Thus:

`BOUNDED COHORT SHARE != NATIONAL WEIGHT`

`CROSS-COHORT POOLING WITHOUT EXPLICIT POPULATION WEIGHTS/DISJOINTNESS = FORBIDDEN`

## 7. What P50 resolves and what it does not

P50 materially advances the original programme intent:

- exact current source-reported 22K size mix exists for one detached house;
- exact current 22K unit count exists for another detached house;
- exact legacy RADAL variants exist on a residential panel circuit;
- the same existing variants have explicit 55 C output-vs-post-envelope-heat-loss rows;
- the engineering paper demonstrates the decisive role of hydraulic suitability and the possibility of either retaining existing emitters or replacing the constrained lower-floor radiator with a higher-output unit;
- the official ZFR programme proves that all-radiator original/new dimension/performance/temperature tables were required at project level.

Still unresolved nationally:

- number of radiator-heated dwellings;
- total installed radiator units;
- representative national material/type/size distribution;
- stock-level post-envelope KEEP/UPSIZE/CHANGE shares;
- national replacement quantity and output bands.

Therefore all five P42 rows remain `Q / programme_use_allowed=NO`.

No source binary is committed. No external request, email or purchase is performed in P50.
