# B02-P34 — KSH STADAT heating derivation recovery

**State:** `DERIVATION ROUTE RECOVERED / GAS-CONVECTOR INTERPRETATION FALSIFIED / ZERO VALIDATION CLOSURES`

**Base:** `3a51410da101b6712e8938612351819d574940d1`

**Audit date:** 2026-09-06

## 1. Purpose

P33 identified KSH STADAT table 14.8.2.2 as a potentially independent spatial validation surface because it publishes the row `Egyedi helyiségfűtés gázzal`, including `11.7%` nationally in the `2020` block.

P33 deliberately left the questionnaire-to-publication derivation unproven and proposed recovering the exact KSH mapping before treating the row as gas-convector evidence.

P34 performs that recovery attempt using the exact KSH questionnaire vintages and KSH methodological metadata.

The result is a **negative but decisive semantic finding**:

`STADAT EGYEDI HELYISÉGFŰTÉS GÁZZAL != SOURCE-NATIVE GAS-CONVECTOR CATEGORY`

The archived STADAT row cannot serve as gas-convector validation evidence because the questionnaire vintage corresponding to the STADAT `2020` reference year does not contain a gas-convector subtype variable at all.

P34 closes zero P30 blockers.

## 2. Evidence-storage rule

Joseph's standing evidence rule remains binding:

`EXACT REFERENCE REQUIRED / REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY`

P34 stores only source IDs, public URLs, exact page/field locators, source-native semantics and admission metadata.

No KSH PDF, CSV, XLSX, screenshot or other source binary is copied into the repository.

## 3. First correction: STADAT `2020` must be aligned to the 2021 HKÉF questionnaire

The old KSH STADAT methodology explicitly states that the published year labels use the **reference year rather than the survey year** for this HKÉF publication family.

Therefore the STADAT `2020` block must be checked against the HKÉF instrument with:

- survey year: `2021`;
- reference year: `2020`.

Exact KSH questionnaire:

- source ID: `SRC-B02-KSH-HKEF-QUESTIONNAIRE-2021`
- URL: `https://www.ksh.hu/docs/hun/info/02osap/onk/2154/k212154.pdf`
- cover: `Felvétel éve: 2021`, `Referencia év: 2020`;
- housing section: printed page 9 / PDF index 8 for `FUTMOD` and the beginning of `ENERG1/ENERG2`;
- printed page 10 / PDF index 9 for the energy-carrier response values.

This supersedes the tempting but incorrect use of the 2022 questionnaire for the STADAT `2020` row.

`STADAT REFERENCE YEAR 2020 != HKÉF SURVEY YEAR 2022`

## 4. Source-native 2021 heating variables

The 2021 questionnaire defines:

### `FUTMOD`

`Milyen módon fűtik a lakást?`

- `1` = távfűtéssel;
- `2` = egy épület több lakását fűtő kazánnal;
- `3` = egy lakást fűtő készülékkel;
- `4` = **egyedi helyiségfűtéssel**;
- `5` = mobil fűtéssel;
- `0` = nincs fűtés.

### `ENERG1` / `ENERG2`

`Mivel fűtenek?`

The questionnaire allows two energy carriers and explicitly instructs the respondent that the first value must be the one used **primarily**.

Response codes include:

- `1` = **Gázzal**;
- `2` = Villannyal;
- `3` = Folyékony vagy szilárd tüzelőanyaggal;
- `4` = Alternatív erőforrással.

Therefore the 2021 instrument can encode the source-native semantic combination:

`FUTMOD=4 + ENERG1=1`

meaning:

`PRIMARY HEATING MODE = INDIVIDUAL ROOM HEATING` and `PRIMARY HEATING ENERGY = GAS`.

That is fully consistent with the STADAT label `Egyedi helyiségfűtés gázzal`.

However the questionnaire contains **no variable that distinguishes gas convector from another fixed room-heating appliance using gas**.

Therefore even an exact publication program mapping to `FUTMOD=4 + ENERG1=1` would prove only:

`INDIVIDUAL ROOM HEATING + PRIMARY GAS`

not:

`GAS_CONVECTOR`.

## 5. Exact STADAT surface

KSH STADAT table:

- source ID: `SRC-B02-KSH-STADAT-JOV0048-2020`
- URL: `https://www.ksh.hu/stadat_files/jov/hu/jov0048.html`
- table: `14.8.2.2. A háztartások és lakások megoszlása, a lakások mennyiségi és minőségi mutatói régió és településtípus szerint`
- exact locator: `2020` block -> `A lakások megoszlása a fűtés módja szerint, %` -> row `Egyedi helyiségfűtés gázzal`;
- national `Ország összesen` value: `11.7%`.

The row is a valuable independent **heating-mode × primary-fuel** control.

It is not an emitter/device-specific control.

Canonical boundary:

`ROOM-HEATING MODE + GAS != GAS-CONVECTOR DEVICE`

## 6. Why P33's proposed `FUTMOD=4 AND EGYEDI=1` bridge is falsified

The explicit gas-convector subtype exists in the **2022** HKÉF instrument:

- source ID: `SRC-B02-KSH-HKEF-QUESTIONNAIRE-2022`;
- URL: `https://www.ksh.hu/docs/hun/info/02osap/onk/2154/k222154.pdf`;
- survey year: `2022`;
- reference year: `2021`;
- `FUTMOD=4` triggers `EGYEDI`;
- `EGYEDI=1` = `Gázkonvektorral`.

This is a stronger emitter taxonomy than the 2021 instrument.

But the archived STADAT table ends with reference year `2020` and therefore does not overlap the 2022 questionnaire's explicit `EGYEDI` subtype variable.

Consequently the proposed bridge:

`STADAT 2020 row -> FUTMOD=4 AND EGYEDI=1`

is not merely unproven; it is **temporally and instrument-semantically invalid**.

P33 remains a historical candidate snapshot. P34 supersedes only that derivation hypothesis.

## 7. KSH methodological provenance

KSH methodological documentation for `Fogyasztás színvonala, szerkezete` identifies HKÉF / OSAP 2154 as the relevant direct household survey source and lists STADAT among the electronic publication forms.

This establishes the correct source family and publication lineage at the statistical-domain level.

It does **not** publish the exact internal table-generation expression for the row.

KSH's methodological FAQ explicitly states that if the published methodological documentation does not provide enough information about an individual datum or its calculation, users should contact KSH for further information.

Therefore the remaining narrow provenance question is:

`EXACT TABLE-GENERATION EXPRESSION FOR STADAT ROW = NOT PUBLICLY RECOVERED`

But this missing expression can no longer change the emitter conclusion: the 2021 source instrument itself has no gas-convector subtype variable.

## 8. Admission consequence

P34 changes the interpretation of the STADAT candidate from:

`POTENTIAL GAS-CONVECTOR VALIDATION IF DERIVATION IS PROVEN`

to:

`QUALIFIED INDEPENDENT HEATING-MODE/FUEL CONTROL / EXCLUDED AS GAS-CONVECTOR VALIDATION`.

Therefore:

- `validation_metrics = no` remains unchanged;
- `independence_assumption_controlled = no` remains unchanged;
- `approval_status = NOT_APPROVED` remains unchanged;
- P30 remains `ASS / Q`;
- `NO_VALIDATION_METRICS` remains open;
- B02 readiness remains `55%`.

This is a useful negative closure of a research route, not a model-admission closure.

## 9. What P34 proves

P34 proves:

1. the STADAT `2020` block aligns to the HKÉF 2021 instrument / reference year 2020;
2. that instrument distinguishes heating mode (`FUTMOD`) and primary/secondary energy (`ENERG1`, `ENERG2`);
3. it does **not** contain a gas-convector subtype variable;
4. the explicit `EGYEDI=1 = Gázkonvektorral` taxonomy appears in the 2022 questionnaire / reference year 2021;
5. the archived STADAT series does not provide an overlapping explicit gas-convector publication surface;
6. therefore STADAT `Egyedi helyiségfűtés gázzal` cannot be promoted to gas-convector prevalence.

## 10. Next evidence order

The KSH STADAT derivation route is now exhausted for P30 emitter validation.

The next highest-value public routes are therefore genuinely emitter-specific current evidence sources, especially:

1. EKR/HEM public or documented administrative surfaces that distinguish pre-investment `gázkonvektor`;
2. MVM KonvekPRO public/administrative current gas-convector cohort evidence;
3. additional independent current administrative inventories;
4. the detailed REKK/TÁRKI microdata route if lawfully obtainable.

Historical NÉeS/ÉMI remains useful only as an independent structural holdout.

No source binary is to be committed in any of these routes unless Joseph explicitly changes the repository policy.
