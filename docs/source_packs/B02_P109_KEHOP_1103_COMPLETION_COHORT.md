# B02-P109 — KEHOP 1103 COMPLETION-INDICATOR COHORT SCHEMA

## Goal

P108 resolved the record-level component bridge and left:

`KEHOP_COMPLETED_WINDOW_PROJECT_TECHNICAL_COHORT_REQUIRED`.

P109 determines whether completed KEHOP projects already carry a structured
administrative cohort key for window replacement.

## 1. Physical-completion reporting already carries action category

The current KEHOP Plusz 4.1.7-24 call requires project-level data at physical
completion for:

`Energiahatékonysági intézkedés kategória`

using the MEKH category list, based on the energy certificate.

The 4.1.8-24 Budapest call uses the same indicator structure.

The two programmes cover the KEHOP family geographically:

- 4.1.7: outside Budapest;
- 4.1.8: Budapest.

Thus a nationwide **KEHOP programme-family** completed-project action cohort can
be defined without inventing an action label.

## 2. Exact window code

The current 18/2025 EM taxonomy identifies:

`1103 - Épületszerkezetek - Felújítás - Nyílászáró cseréje`.

Therefore a completed KEHOP project whose physical-completion indicator includes
1103 is an administratively identified window-replacement project.

This is stronger than inferring window action from generic RCO18 or energy
savings.

## 3. Exact cohort schema

A future extract is admissible only if it carries:

1. programme code;
2. stable project ID;
3. physical-completion date;
4. MEKH measure category;
5. declared extract scope and cutoff date;
6. complete enumeration for that declared scope.

The cohort selector is exact:

`MEASURE_CATEGORY == 1103`.

Duplicate project IDs are rejected.

A convenience sample is not accepted as a cohort denominator.

## 4. Technical-performance join

The completion indicator identifies **what action family was completed**.

It does not by itself supply the post-state component U distribution.

P108 still governs the performance join:

- same-project final HET + final detailed energy calculation with
  scope-linked window U; or
- exact installed-product DoP linked through final invoice and realized scope.

Therefore:

`COMPLETION INDICATOR 1103 != TECHNICAL U DISTRIBUTION`.

The post-extract residual is:

`KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED`.

## 5. HEM/EKR overlap is separate

The KEHOP call permits advisory compensation through HEM only when a written
HEM-generation agreement is made.

That route is optional.

Therefore:

`MEKH CATEGORY 1103 != REGISTERED HEM 1103`.

For EKR overlap classification P109 requires either:

- an explicit project-level HEM ID; or
- a HEM-generation-agreement reference, pending final HEM binding.

Without that:

`EKR_HEM_OVERLAP_UNCLASSIFIED`.

This prevents double counting between the KEHOP cohort and the separate EKR
1103 cohort.

## 6. Public-access audit

The public programme pages and call documents establish the schema and current
programme status.

P109 did **not** identify a public completed-project export exposing:

- stable project IDs;
- completion dates;
- project-level MEKH action categories;
- final HET/calculation references;
- project-level HEM attribution.

Programme-level RCO18/RCR26 indicators do not substitute for this extract.

## 7. Blocker repair

Superseded:

`KEHOP_COMPLETED_WINDOW_PROJECT_TECHNICAL_COHORT_REQUIRED`.

Exact residuals:

1. `MFB_KEHOP_COMPLETION_INDICATOR_1103_EXTRACT_REQUIRED`
2. `KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED`
3. `KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED`

The unknown is no longer the cohort definition. The cohort definition is now
source-native and executable.

The remaining unknown is access/materialization.

## 8. National numeric effect

No completed-project 1103 extract is admitted yet.

Therefore:

- calibrated retrofit floor remains **82.7861029945%**
- HP_ONLY lower remains **0%**
- HP_ONLY upper remains **17.2138970055%**
- B02 remains **55%**
- PEAK_LOAD_EFFECT remains **50%**

## Canonical boundaries

`COMPLETION INDICATOR 1103 != TECHNICAL U DISTRIBUTION`

`RCO18 HOUSEHOLD COUNT != WINDOW 1103 COHORT`

`MEKH CATEGORY 1103 != REGISTERED HEM 1103`

`PUBLIC PROGRAMME STATUS != COMPLETED PROJECT ENUMERATION`

`ADMINISTRATIVELY ENUMERABLE != PUBLICLY AVAILABLE`

`CONVENIENCE SAMPLE != COMPLETE DECLARED-SCOPE COHORT`
