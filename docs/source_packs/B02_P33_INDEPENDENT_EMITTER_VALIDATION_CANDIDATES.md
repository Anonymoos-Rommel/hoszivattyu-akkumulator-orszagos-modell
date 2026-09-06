# B02-P33 — independent emitter-validation candidate qualification

**State:** `CANDIDATES QUALIFIED / ZERO VALIDATION-BLOCKER CLOSURES`

**Base:** `05937fd5929d266fbdb413c18422364fe502b5d4`

**Audit date:** 2026-09-06

## 1. Purpose

P32 repaired the technical-applicability contract. P33 resumes the evidence-first work order from P31 and qualifies the strongest newly identified public emitter-validation candidates without converting semantic proximity into evidence.

P33 closes **zero** P30 admission blockers.

The P30 calibrated gas-convector linkage remains:

- `approval_status = NOT_APPROVED`;
- `validation_metrics = no`;
- `independence_assumption_controlled = no`;
- `output_evidence_status = ASS`;
- `current_status = Q`.

The exact blockers remain:

- `NO_JOSEPH_APPROVAL`;
- `NO_VALIDATION_METRICS`;
- `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

Canonical boundary:

`VALIDATION CANDIDATE != VALIDATION METRIC`

`SOURCE-NATIVE LABEL SIMILARITY != PROVEN PUBLICATION DERIVATION`

`HISTORICAL FIELD SURVEY != CURRENT STOCK AUTHORITY`

## 2. Repository storage policy

Joseph's evidence-handling rule for this slice is explicit:

`EXACT REFERENCE REQUIRED / SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY`

P33 therefore stores only:

- stable external source URL;
- issuing authority;
- exact table/page/field locator;
- source-native claim text or bounded paraphrase;
- evidence-role and admissibility metadata.

No KSH questionnaire PDF, NÉeS PDF, STADAT export, screenshot or other source binary is copied into the repository.

Machine-readable policy and locators are in:

`registry/b02_p33_independent_emitter_validation_candidates.csv`

## 3. KSH HKÉF questionnaire — explicit gas-convector taxonomy

### Exact source

- source ID: `SRC-B02-KSH-HKEF-QUESTIONNAIRE-2022`
- authority: Központi Statisztikai Hivatal (KSH)
- external URL: https://www.ksh.hu/docs/hun/info/02osap/onk/2154/k222154.pdf
- document title: `KÉRDŐÍV a 2022. évi Háztartási Költségvetési és Életkörülmény Adatfelvételhez`
- survey year: `2022`
- document-stated reference year: `2021`
- exact locator: **printed page 6 / PDF page index 5**, section `II. Lakásjellemzők`, fields `FUTMOD` and `EGYEDI`.

### Exact source-native semantics

The questionnaire defines:

- `FUTMOD = 4`: `Egyedi fix helyiségfűtéssel (pl. konvektor, kályha, kandalló)`;
- `EGYEDI` is asked when `FUTMOD=4`;
- `EGYEDI = 1`: `Gázkonvektorral`.

Therefore:

`KSH HKÉF SOURCE TAXONOMY CAN IDENTIFY GAS_CONVECTOR EXPLICITLY = PROVEN`

This is stronger than inferring an emitter from a generic heating-mode or fuel label.

But the questionnaire is a schema/instrument. By itself it supplies no published national gas-convector percentage and no WBL assignment.

`QUESTIONNAIRE CATEGORY != PUBLISHED AGGREGATE`

`QUESTIONNAIRE CATEGORY != CURRENT STOCK ASSIGNMENT`

## 4. KSH STADAT 14.8.2.2 — independent numeric heating-mode surface, derivation still unproven

### Exact source

- source ID: `SRC-B02-KSH-STADAT-JOV0048-2020`
- authority: Központi Statisztikai Hivatal (KSH)
- external URL: https://www.ksh.hu/stadat_files/jov/hu/jov0048.html
- table: `14.8.2.2. A háztartások és lakások megoszlása, a lakások mennyiségi és minőségi mutatói régió és településtípus szerint`
- status shown by KSH: `Archív tábla, nem frissül tovább.`
- page metadata: `Utolsó frissítés: 2022. november 4.`
- exact locator: year block `2020` -> section `A lakások megoszlása a fűtés módja szerint, %` -> row `Egyedi helyiségfűtés gázzal`.
- source-native national value in the first `Ország összesen` column: `11.7%`.

The same row also publishes region- and settlement-type values, so it is potentially useful as an independent spatial control.

### Required semantic restraint

P33 did **not** find an official KSH derivation statement proving that the STADAT row is exactly calculated as:

`FUTMOD = 4 AND EGYEDI = 1`

from the questionnaire above.

The semantic correspondence is plausible, but plausibility is not enough for an exact evidence chain.

Therefore P33 records:

`STADAT "Egyedi helyiségfűtés gázzal" -> GAS_CONVECTOR = DERIVATION_UNPROVEN`

and:

`validation_admissible = NO`

for P30 gas-convector validation at this stage.

The `11.7%` figure must remain labelled exactly as KSH publishes it. It must **not** be renamed to `gas-convector share` until the publication derivation is recovered from KSH metadata, methodological documentation, a data-dictionary/codebook, or an authoritative KSH response.

## 5. NÉeS / ÉMI — independent 20,842-building field survey

### Exact source

- source ID: `SRC-B02-NEES-EMI-20842-FIELD-SURVEY-2015`
- authority: Hungarian Government / National Building Energy Strategy; underlying field survey by ÉMI
- strategy PDF external URL: https://2015-2019.kormany.hu/download/d/85/40000/Nemzeti%2520E%25CC%2581pu%25CC%2588letenergetikai%2520Strate%25CC%2581gia%2520150225.pdf
- legal adoption authority: `1073/2015. (II. 25.) Korm. határozat a Nemzeti Épületenergetikai Stratégiáról`
- legal authority URL: https://njt.jog.gov.hu/jogszabaly/2015-1073-30-22
- strategy exact locator: **printed pages 31–32 / PDF page indices 30–31**, section `3.2.2`, immediately after Table 9; the gas-convector bullet is on **printed page 32**.

### Exact source-native evidence boundary

The strategy explicitly distinguishes this as `Az ÉMI egy másik felmérést is elvégzett` and reports:

- `20842` buildings surveyed;
- distribution across Hungarian regions and across Budapest, larger and smaller towns, and villages;
- on-site inspection (`helyszíni szemle`);
- questionnaire completion by ÉMI experts.

On printed page 32 the strategy reports gas-convector occurrence by building type:

- first four family-house types: `11–20%`;
- older post-1945 conventional apartment buildings: `46%`;
- other industrialized-technology buildings: `43%`;
- pre-1945 small and large apartment buildings: `26%`.

This is a materially different evidence collection from the REKK/TÁRKI 2022 survey margin consumed by P30 and is also described separately from the preceding Csoknyai typology survey in the strategy text.

Therefore it is admitted as:

`INDEPENDENT HISTORICAL STRUCTURAL HOLDOUT CANDIDATE`

not as current-stock authority.

The strategy does not establish that these historical proportions describe the 2021/2022 occupied stock without change.

Therefore:

`HISTORICAL 20,842-BUILDING FIELD SURVEY != CURRENT 2022 EMITTER DISTRIBUTION`

`INDEPENDENT HISTORICAL STRUCTURE != CURRENT VALIDATION METRIC`

It may be used to falsify grossly incompatible structural assumptions or to compare qualitative/type ordering, but it cannot by itself close P30's current `NO_VALIDATION_METRICS` blocker.

## 6. What P33 newly proves

P33 proves three bounded facts:

1. KSH HKÉF has an explicit source-native gas-convector response category (`FUTMOD=4`, `EGYEDI=1`).
2. KSH STADAT publishes an independent national/spatial `Egyedi helyiségfűtés gázzal` surface, including `11.7%` nationally for 2020, but the exact questionnaire-to-publication derivation has not yet been proven.
3. NÉeS publishes a separate ÉMI 20,842-building on-site survey with explicit building-type gas-convector proportions, but this is historical structural evidence rather than current-stock authority.

These facts materially improve the validation search space without changing admission state.

## 7. What P33 explicitly does not prove

P33 does not prove:

- that the 2020 STADAT gas-room-heating row equals gas-convector prevalence;
- that a 2020 share is a 2022 share;
- that NÉeS historical building-type shares remain current;
- a current gas-convector cross-tab at WBL cell grain;
- any current radiator/surface-heating distribution;
- any hydronic design-temperature distribution;
- independence-control closure for P30;
- Joseph approval.

No emitter assignment CSV is materialized.

No `OBS`/`DER` current-stock emitter surface is created.

B02 readiness remains `55%`.

## 8. Correct next step

The highest-value next action remains to recover the exact KSH derivation for STADAT `Egyedi helyiségfűtés gázzal`.

Admissible closure evidence would include one of:

- an official KSH table-definition / variable mapping;
- a source-native codebook or publication program mapping the row to `FUTMOD` / `EGYEDI`;
- an authoritative KSH methodological statement or response;
- a public KSH export whose metadata explicitly binds the published category to the questionnaire response code.

If that mapping is proven, the 2020 national/spatial surface becomes a candidate for a genuinely independent emitter validation metric. Until then, fail closed.
