# B02-P110 — KEHOP 1103 FAIR/IH EXTRACT ACCESS SURFACE

## Goal

P109 proved that the completed KEHOP window cohort is source-native:

`physical completion + MEKH measure category 1103`.

The remaining blocker was:

`MFB_KEHOP_COMPLETION_INDICATOR_1103_EXTRACT_REQUIRED`.

P110 identifies the exact administrative data locus and the minimum admissible
data products.

## 1. Administrative locus

Current KEHOP Plusz governance assigns the responsible implementation
administration duties to:

- monitor project implementation by physical indicators;
- aggregate and analyse acquired implementation data;
- provide programme-progress data;
- participate in the KEHOP Plusz FAIR system's development and information
  content.

Combined with P109, this establishes:

`KEHOP COMPLETION INDICATOR 1103 -> IH / FAIR ADMINISTRATIVE SURFACE`.

This is an access-location result, not public availability.

## 2. Public-surface audit

The public MFB programme page is status/scope authority.

The public project-search concept can expose project metadata, but P110 did not
identify a current public surface proving:

- project-level completion-indicator field exposure;
- MEKH measure-category filtering;
- exact 1103 filtering;
- complete 4.1.7/4.1.8 completed-project enumeration;
- technical-document join keys;
- HEM attribution.

Therefore:

`PUBLIC PROJECT SEARCH != COMPLETION INDICATOR EXPORT`.

Programme-level RCO18/RCR26/RCR29 reporting is also insufficient:

`PROGRAMME INDICATORS != COMPONENT ACTION COHORT`.

## 3. Two admissible extract products

### A. Minimum aggregate route

A FAIR/IH source-generated aggregate may be admitted when it declares:

- programme scope: 4.1.7 and/or 4.1.8;
- reference cutoff date;
- total physically completed projects in the declared scope;
- exact count carrying measure category 1103;
- complete enumeration for the declared scope;
- source-scope description.

This can support:

- completed 1103 project count;
- 1103 share within that exact completed KEHOP scope.

It cannot support:

- window U distribution;
- whole-dwelling compliance;
- EKR/non-EKR split.

### B. Preferred record-extract route

The preferred extract retains:

- programme code;
- stable project ID;
- physical-completion date;
- measure-category codes including 1103;
- final-HET reference;
- final energy-calculation or installed-product join key;
- explicit HEM agreement / HEM ID where present;
- source cutoff and complete-enumeration metadata.

This can proceed into the P108 technical-performance join and P109 EKR overlap
classification.

## 4. Blocker repair

Superseded:

`MFB_KEHOP_COMPLETION_INDICATOR_1103_EXTRACT_REQUIRED`.

New exact primary residual:

`FAIR_IH_KEHOP_1103_COMPLETION_EXPORT_OR_AGGREGATE_REQUIRED`.

Preferred technical route:

`FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED`.

Downstream independent residuals remain:

- `KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED`
- `KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED`.

## 5. Numeric effect

No FAIR/IH 1103 completion extract or source-generated aggregate is currently
admitted.

Therefore:

- calibrated retrofit floor remains **82.7861029945%**
- HP_ONLY lower remains **0%**
- HP_ONLY upper remains **17.2138970055%**
- B02 remains **55%**
- PEAK_LOAD_EFFECT remains **50%**

## Canonical boundaries

`PUBLIC PROJECT SEARCH != COMPLETION INDICATOR EXPORT`

`PROGRAMME INDICATORS != COMPONENT ACTION COHORT`

`ADMIN DATA EXISTS != PUBLIC DATA AVAILABLE`

`1103 AGGREGATE != TECHNICAL U DISTRIBUTION`

`1103 COUNT != NON-EKR 1103 COUNT`
