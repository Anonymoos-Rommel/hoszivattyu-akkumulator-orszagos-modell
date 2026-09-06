# B02-P35 — EKR/HEM gas-convector administrative route qualification

**State:** `ADMINISTRATIVE DEVICE-SPECIFIC ROUTE QUALIFIED / PUBLIC STOCK SURFACE NOT PROVEN / ZERO VALIDATION CLOSURES`

**Base:** `2438ee54460467cb3fdf49991184fb35dac84568`

**Audit date:** 2026-09-06

## 1. Purpose

P34 exhausted the KSH STADAT route as gas-convector validation because source-native `individual room heating + gas` is not device-specific `GAS_CONVECTOR` evidence.

P35 therefore tests the next evidence route: whether the Hungarian Energy Efficiency Obligation Scheme (`EKR`) and the registry of certified energy savings (`HEM`) contain a current administrative path that identifies a pre-investment gas convector explicitly enough to support independent emitter validation.

The result is split:

`ADMINISTRATIVE GAS-CONVECTOR EVIDENCE EXISTS != PUBLIC GAS-CONVECTOR STOCK SURFACE EXISTS`

The current EKR catalogue creates an explicit, document-backed administrative route for a pre-investment `gázkonvektor` in heat-pump replacement cases. However, the legally defined public HEM-registry content recovered in P35 does not expose the pre-investment device type as a public registry field. No public emitter-specific numerator/denominator has therefore been recovered.

P35 closes zero P30 blockers.

## 2. Evidence-storage rule

Joseph's standing evidence rule remains binding:

`EXACT REFERENCE REQUIRED / REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY`

P35 stores only authority, public URL, exact legal/document locator, source-native semantics and bounded admission metadata.

No Magyar Közlöny PDF, HEM handbook PDF, registry export, screenshot, spreadsheet or other external source binary is copied into this repository.

## 3. Current EKR catalogue: pre-investment gas convector is explicit

### Source

- source ID: `SRC-B02-EKR-41-2025-EM-HEATPUMP-GASCONVECTOR`
- authority: Magyar Közlöny / Energiaügyi Minisztérium
- URL: `https://magyarkozlony.hu/dokumentumok/5858f900426cb56e532a468a989dbb1417d9aef0/letoltes`
- document: Magyar Közlöny 2025. évi 160. szám; `41/2025. (XII. 30.) EM rendelet`; 1. melléklet replacing the 1. melléklet of `18/2025. (VII. 31.) EM rendelet`
- exact locator A: printed page `11508` / PDF zero-based page `61`; II. rész -> `2. Épülettechnikai rendszerek korszerűsítése` -> `2.1. Gázkazán cseréje hőszivattyúra` -> `2.1.1.1. Alkalmazás feltételei`, point `b)`
- exact locator B: printed page `11509` / PDF zero-based page `62`; `2.1.3.1. Rögzítendő bemeneti műszaki paraméterek`
- exact locator C: printed pages `11509-11510` / PDF zero-based pages `62-63`; `2.1.3.2. Alátámasztó dokumentumok`, rows 3-5

### Source-native facts

The current catalogue explicitly allows the replaced device to be:

- traditional gas boiler;
- condensing gas boiler;
- **gas convector**.

The input-parameter table explicitly labels the pre-investment side:

`Beruházás előtti gázkazán, gázkonvektor`

and requires, among other fields:

- manufacturer;
- type;
- installation date in early-replacement cases;
- the replaced gas boiler/gas convector performance factor where applicable.

The supporting-document table separately requires evidence for the old gas boiler/gas convector's:

- commissioning date;
- nominal heating capacity;
- type used to determine `Ck`.

Accepted source-native document classes include technical datasheet, commissioning report, nameplate, accounting document for installation, and — for type determination — a pre-modernisation valid energy performance certificate.

Therefore this is materially stronger than a survey label: an EKR heat-pump replacement HEM may be backed by household/building-specific administrative evidence that the pre-investment device was a `gázkonvektor`.

Canonical consequence:

`EKR CATALOGUE DEVICE-SPECIFIC BASELINE = QUALIFIED`

but:

`QUALIFIED ADMINISTRATIVE BASELINE != PUBLIC STOCK PREVALENCE`

## 4. HEM intake workflow carries detailed measure data

### Source

- source ID: `SRC-B02-MEKH-HEM-MODULE-HANDBOOK`
- authority: Magyar Energetikai és Közmű-szabályozási Hivatal
- URL: `https://ekr.mekh.hu/docs/HEM_Modul_kezikonyv.pdf`
- exact locator: section `5.1. HEM Bejegyzés`, printed pages 9-10 / PDF zero-based pages 8-9; especially the paragraphs describing the `HEM_AuditorBejegyzo` form, catalogue-vs-individual-audit selection, the `Intézkedés` sheet and technical-parameter entry

### Source-native facts

The handbook states that:

1. HEM registration is performed by an authorised energy auditing organisation;
2. catalogue-based HEMs are entered as catalogue measures;
3. the `Intézkedés` sheet contains the measure name and type;
4. the subsequent part of the sheet requires technical parameters associated with the measure;
5. those technical-data requirements are aligned with `17/2020. (XII. 21.) MEKH rendelet`;
6. HEM registration can also be submitted through an Excel template for large projects.

This proves that the administrative system is structurally capable of carrying device-specific measure inputs required by the current catalogue.

It does **not** prove that these detailed inputs are exposed in the public registry view or in a public bulk export.

## 5. HEM registry content versus HEM submission content

### Source

- source ID: `SRC-B02-MEKH-17-2020-HEM-DATA-CONTENT`
- authority: Nemzeti Jogszabálytár / MEKH
- URL: `https://njt.jog.gov.hu/jogszabaly/2020-17-20-5Z`
- exact locator A: `1/A. A hitelesített energiamegtakarítások nyilvántartásának adattartalma` -> `2/A. §`
- exact locator B: `2. Az elért energiamegtakarítás bejelentése` -> `3. § (1) a)-n)`
- exact locator C: `3. Az energiamegtakarítás megállapítása céljából készített energetikai audit kiegészítő kötelező tartalmi elemei` -> `4. § a)-h)`
- consolidated text date displayed by NJT: `2026.04.01.`

### Registry fields under 2/A. §

The HEM registry content recovered in `2/A. §` consists of:

- HEM certification identifier;
- energy-saving quantity;
- beneficiary data;
- implementation/use/commissioning date;
- savings lifetime.

No pre-investment heat-emitter/device field is listed in `2/A. §`.

### Additional submitted data under 3. §

The HEM submission includes materially richer data, including:

- measure/renovation name and type;
- start date;
- location and final-user identifiers;
- catalogue or individual-audit provenance;
- expected lifetime and degradation;
- early-replacement data;
- short technical description;
- total eligible energy saving.

For individual audits, `4. §` additionally requires the pre-intervention technical state, and for equipment purchase/replacement the equipment name, type and performance characteristics.

Therefore:

`HEM SUBMISSION DATA > HEM PUBLIC-REGISTRY STATUTORY FIELD SET`

P35 found no authoritative public source proving that the detailed pre-investment `gázkonvektor` parameter is published as a public HEM-registry field or public bulk-download column.

## 6. Public-access boundary

### Source

- source ID: `SRC-B02-EHAT-15A-PUBLIC-HEM-REGISTRY`
- authority: Nemzeti Jogszabálytár
- URL: `https://njt.jog.gov.hu/jogszabaly/2015-57-00-00`
- exact locator: `2015. évi LVII. törvény`, `15/A. § (4a)-(4g)`, especially `(4a)`, `(4e)` and `(4g)`

### Source-native facts

The Act requires the authority to maintain the HEM registry online and to make the data of energy savings in the registry that are eligible for a given year available on the energy-efficiency information website by the following 31 March. It also states that the energy-saving datum in the HEM registry is authoritative public-register data.

This creates a public-access obligation for **registry data**.

But the current statutory HEM registry field set in `17/2020. (XII. 21.) MEKH rendelet 2/A. §` does not include the pre-investment gas-convector field.

Consequently P35 must fail closed:

`PUBLIC HEM REGISTRY != PROVEN PUBLIC PRE-INVESTMENT GAS-CONVECTOR DATASET`

## 7. Admission consequence

P35 upgrades the EKR/HEM route from an untested idea to:

`QUALIFIED ADMINISTRATIVE DEVICE-SPECIFIC ROUTE / PUBLIC VALIDATION SURFACE NOT YET AVAILABLE`

This means:

- an EKR/HEM record under the current heat-pump catalogue can carry evidence that the pre-investment device was a gas convector;
- the administrative evidence can be stronger than survey inference because it is measure-specific and document-backed;
- the public HEM registry content recovered here does not expose that device field;
- no public gas-convector HEM count, denominator, regional distribution or WBL-compatible validation metric has been recovered.

Therefore:

- `validation_metrics = no` remains unchanged;
- `independence_assumption_controlled = no` remains unchanged;
- `approval_status = NOT_APPROVED` remains unchanged;
- P30 remains `ASS / Q`;
- `NO_VALIDATION_METRICS` remains open;
- B02 readiness remains `55%`.

## 8. What P35 proves

P35 proves:

1. the current EKR catalogue explicitly recognises `gázkonvektor` as a pre-investment device in heat-pump replacement measure 2.1;
2. the catalogue requires multiple device-specific pre-investment parameters and supporting documents;
3. HEM intake supports catalogue measure selection and detailed technical parameters;
4. the legally defined HEM registry field set is materially narrower than the submitted HEM data;
5. the public-register obligation does not by itself prove publication of the detailed pre-investment gas-convector field;
6. EKR/HEM is therefore a credible administrative evidence source, but not yet a public stock-validation surface.

## 9. Highest-value next action

The shortest path to making this route validation-capable is to recover an **authoritative aggregated extract or official confirmation** that distinguishes HEM heat-pump measure `2104` by pre-investment device (`gázkazán` vs `gázkonvektor`).

Minimum useful aggregate fields:

- HEM / measure year;
- measure code `2104`;
- pre-investment device category;
- count of affected dwellings/buildings or individual actions;
- optional county/region;
- optional building type;
- explicit denominator or full measure-2104 count.

Acceptable authority paths:

1. existing MEKH public data/export/API if one exposes the pre-investment device field;
2. an official MEKH response providing an aggregated table or field mapping;
3. an official MEKH/EM publication that reports measure-2104 gas-convector counts;
4. a lawfully obtainable HEM aggregate with authoritative metadata.

Until one of these exists:

`ADMIN ROUTE = QUALIFIED`

`PUBLIC VALIDATION METRIC = NOT AVAILABLE`

No source binary is to be committed in future slices unless Joseph explicitly changes the repository policy.
