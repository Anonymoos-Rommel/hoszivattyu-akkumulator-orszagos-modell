# B02-P36 — HEM 2104 public aggregate and semantic-drift audit

**State:** `PUBLIC AGGREGATE RECOVERED / DEVICE SPLIT NOT PUBLIC / 2104 SEMANTIC DRIFT PINNED / ZERO VALIDATION CLOSURES`

**Base:** `89ca5615555280fe93ac7f395b7182d8fd8f5c16`

**Audit date:** 2026-09-06

## 1. Purpose

P35 proved that the current EKR catalogue can carry document-backed pre-investment `gázkonvektor` evidence in heat-pump measure 2104, while the public HEM registry field set did not prove a device-specific public surface.

P36 tests the next narrow question:

`CAN THE PUBLIC HEM SURFACE OR AN AUTHORITATIVE PUBLIC AGGREGATE DISTINGUISH 2104 GAS-BOILER VS GAS-CONVECTOR BASELINES?`

The answer remains **no**.

P36 also identifies a critical temporal semantic boundary:

`SAME MEASURE CODE 2104 != SAME PRE-INVESTMENT DEVICE ELIGIBILITY OVER TIME`

## 2. Evidence-storage rule

Joseph's standing evidence rule remains binding:

`EXACT REFERENCE REQUIRED / REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY`

P36 stores only authority, external URL, exact page/section/field locator, source-native facts and bounded admission metadata.

No MEKH PDF, Magyar Közlöny PDF, NJT PDF, HUPX/CEEGEX report PDF, registry export, screenshot, spreadsheet or other source binary is copied into the repository.

## 3. Current public HEM surface is explicitly bounded

Source:

- source ID: `SRC-B02-MEKH-HEM-MODULE-HANDBOOK-PUBLIC-FIELDS`
- authority: MEKH
- URL: `https://ekr.mekh.hu/docs/HEM_Modul_kezikonyv.pdf`
- exact locator: section `8. Publikusan elérhető adatok`, printed page 18 / PDF zero-based page 17.

The handbook states that, without registration/login and with the HEM identifier known, the public surface exposes:

- HEM identifier;
- energy saving amount (GJ);
- current beneficiary name;
- beneficiary tax/core number;
- beneficiary address;
- implementation date;
- saving type;
- lifetime.

It further states that the additional public summary data are only:

- number of implemented/registered HEMs;
- total amount of certified energy savings.

The public-field list does **not** expose:

- `Intézkedés megnevezése`;
- `Intézkedés típusa` / measure code 2104;
- pre-investment device (`gázkazán` vs `gázkonvektor`);
- pre-investment device manufacturer/type/power;
- building function as a public search dimension.

Canonical boundary:

`PUBLIC HEM IDENTIFIER RECORD != PUBLIC MEASURE-SPECIFIC TECHNICAL RECORD`

## 4. Internal HEM intake is richer than the public surface

Same MEKH handbook:

- exact locator: section `5.1. HEM Bejegyzés`, printed page 10 / PDF zero-based page 9, paragraph beginning `Az Előlap kitöltését követően...`.

The authenticated intake workflow contains:

- `Intézkedés megnevezése`;
- `Intézkedés típusa`;
- measure-specific technical parameters tied to the applicable EKR catalogue.

Therefore:

`INTERNAL HEM MEASURE DATA > PUBLIC HEM FIELD SET`

This confirms that an official MEKH-side aggregation by measure/device is technically plausible from administrative data, but it is not automatically reproduced by the public registry.

## 5. Current public landing-page aggregate

Source:

- source ID: `SRC-B02-MEKH-EKR-PUBLIC-LANDING-2026-09-06`
- authority: MEKH
- URL: `https://ekr.mekh.hu/`
- exact locator: public landing page -> `Hitelesített energiamegtakarítások száma` and `Hitelesített energiamegtakarítás mennyisége` counters;
- observed: 2026-09-06.

Observed public totals:

- HEM count: `13,524`;
- certified energy-saving quantity: `24,901,609.7 GJ`.

These values prove an active current aggregate surface, but they provide no 2104/device denominator or split.

`TOTAL HEM COUNT != 2104 COUNT != GAS-CONVECTOR COUNT`

## 6. Historical measure-level 2104 aggregate exists

Source report:

- source ID: `SRC-B02-EKR-MARKETMON-2022-Q3-2104`
- authority: HUPX/CEEGEX, report prepared on MEKH commission;
- provenance page: `https://hupx.hu/hu/2022/11/29/elso-ekr-piacmonitoring-riport`;
- report URL: `https://hupx.hu/uploads/EKR/EKR_HEM_2022%20Q3_report.pdf`;
- exact locator: `EKR Hitelesített energiamegtakarítások piacmonitoring jelentés – 2022 Q3`, PDF zero-based page 14, figure/table `A TOP 5 kategóriákra vetített projektek átlagos megtakarításai`.

The report uses 541 registered projects and shows for:

`2104 - Épületgépészet - Fűtési rendszer - Hőszivattyú beépítése`

- certified saving: `30,446 GJ`;
- project count: `2`;
- project average: `15,223 GJ`.

The following page also identifies one 2104 project with `30,372 GJ` in the early-replacement analysis.

This proves that authoritative/commissioned analysis can aggregate the registry by measure code.

It does **not** prove a gas-convector cohort.

## 7. Why the 2022 2104 aggregate is not gas-convector evidence

Historical catalogue source:

- source ID: `SRC-B02-EKR-17-2020-2104-GASBOILER-ONLY`
- authority: Nemzeti Jogszabálytár / MEKH
- URL: `https://njt.jog.gov.hu/document/df/df0dEJR_8467467-5X05890.pdf`
- exact locator: section `2.1. Gázkazán cseréje hőszivattyúra`; `2.1.1.1. Alkalmazás feltételei`; PDF zero-based page 56; line/item `b)`; `2.1.2` measure type 2104; PDF zero-based pages 56-57 technical-parameter table.

That catalogue states the replaced equipment is:

`hagyományos vagy kondenzációs gázkazán`

and its pre-investment technical-parameter table is explicitly `gázkazán`.

No gas-convector eligibility is present in this historical 2104 definition.

Therefore the 2022 measure-level aggregate cannot be reinterpreted as a mixed boiler/convector cohort.

Canonical:

`2022 2104 AGGREGATE = HISTORICAL GAS-BOILER-SCOPE AGGREGATE`

not:

`2022 2104 AGGREGATE = GAS-CONVECTOR VALIDATION SURFACE`

## 8. Current 2104 scope now includes gas convectors

Current catalogue source:

- source ID: `SRC-B02-EKR-41-2025-EM-2104-GASCONVECTOR`
- authority: Magyar Közlöny / Energiaügyi Minisztérium
- URL: `https://magyarkozlony.hu/dokumentumok/5858f900426cb56e532a468a989dbb1417d9aef0/letoltes`
- legal locator: `41/2025. (XII. 30.) EM rendelet`, which replaces the 1st annex of `18/2025. (VII. 31.) EM rendelet`;
- catalogue locator: Magyar Közlöny 2025. évi 160. szám, printed page 11508 / PDF zero-based page 61, section `2.1.1.1. Alkalmazás feltételei`, item `b)`;
- technical locator: printed page 11509 / PDF zero-based page 62, `2.1.3.1. Rögzítendő bemeneti műszaki paraméterek`.

The current scope explicitly allows:

`hagyományos vagy kondenzációs gázkazán, gázkonvektor`

under the same measure code:

`2104 - Épületgépészet - Fűtési rendszer - Hőszivattyú beépítése`.

Thus measure code 2104 has a proven temporal scope discontinuity between the historical catalogue snapshot and the current catalogue.

P36 does not claim the exact first effective day on which gas-convector eligibility entered 2104; it only pins the proven historical/current semantic difference needed for fail-closed evidence use.

## 9. Admission consequence

P36 recovers a **historical measure-level aggregate** and a **current public total aggregate**, but neither provides a current device-specific gas-convector validation metric.

Therefore:

- `validation_metrics = no` remains unchanged;
- `independence_assumption_controlled = no` remains unchanged;
- `approval_status = NOT_APPROVED` remains unchanged;
- P30 remains `ASS / Q`;
- `NO_VALIDATION_METRICS` remains open;
- B02 readiness remains `55%`.

The following are prohibited:

`CURRENT PUBLIC HEM TOTAL -> GAS-CONVECTOR SHARE`

`HISTORICAL 2104 PROJECT COUNT -> CURRENT GAS-CONVECTOR SHARE`

`2104 CODE MATCH ACROSS YEARS -> SAME DEVICE POPULATION`

## 10. Next evidence order

The strongest next action is no longer blind public-web searching for a field the MEKH handbook explicitly excludes from the public field set.

The next evidence target is an **authoritative MEKH/EM aggregate or official response** computed from internal HEM measure/technical fields, requesting at minimum:

1. HEMs under measure code `2104` for the period in which gas-convector eligibility is in force;
2. pre-investment device split: `gázkazán` vs `gázkonvektor`;
3. project/HEM count and certified GJ by device;
4. implementation year;
5. residential vs public-building flag if available;
6. geography at the finest releasable non-personal-data level;
7. denominator/coverage definition and disclosure rules.

Until such a source is obtained:

`PUBLIC DEVICE-SPECIFIC 2104 VALIDATION METRIC = NOT AVAILABLE`

No source binary is to be committed unless Joseph explicitly changes the repository policy.
