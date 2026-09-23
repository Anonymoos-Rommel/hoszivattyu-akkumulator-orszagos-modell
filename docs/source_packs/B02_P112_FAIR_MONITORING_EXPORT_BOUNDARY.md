# B02-P112 — FAIR PROJECT-LEVEL MONITORING EXPORT BOUNDARY

## Goal

P111 proved a machine-readable FAIR supported-project universe for the KEHOP
Plusz 4.1.7/4.1.8 programme family.

The remaining question was whether the project-level physical-completion
professional metric can be source-exported at all, or whether even the
single-project data path was unknown.

P112 proves the generic project/report export mechanism and narrows the
remaining acquisition to exact KEHOP field readback plus cross-project
completeness.

## 1. FAIR project/report monitoring export

The official FAIR/EUPR help for Monitoring mutatók rögzítése Szakmai- és Záró
Beszámolóknál states that the function is part of both professional and closing
reports.

The list can be exported as CSV or Excel.

The documented list/export surface contains:

- Monitoring mutató megnevezése;
- mutató típusa;
- bázis/cél values;
- Tény dátuma;
- Tény változás;
- Tény összváltozás;
- Tény kumulált;
- the report sequence associated with the fact value;
- the report type, including Záró szakmai beszámoló.

The records are access-controlled: authorised users can edit or view depending
on their rights.

This proves a source-native project/report fact export route.

## 2. KEHOP exact professional metric schema

P109 already established from the 4.1.7 and 4.1.8 call documents that projects
must provide data at physical completion for:

Energiahatékonysági intézkedés kategória

as a project-level professional metric using the MEKH category list based on
the energy certificate.

The current MEKH taxonomy binds:

1103 = Épületszerkezetek - Felújítás - Nyílászáró cseréje

Therefore the source-native schema for a 1103 completion fact is exact.

## 3. What P112 does not overclaim

The public FAIR help is generic system documentation.

P112 has not directly observed a live 4.1.7 or 4.1.8 monitoring export showing
the exact Energiahatékonysági intézkedés kategória field.

Therefore:

GENERIC MONITORING EXPORT CAPABILITY != OBSERVED KEHOP 1103 EXPORT

The live parameterization/readback residual remains:

KEHOP_417_418_1103_MONITORING_PARAMETERIZATION_READBACK_REQUIRED

This is now a field-binding verification problem, not a question about whether
FAIR can export project monitoring facts.

## 4. Project-level export is not the national cohort

Even if a single authorised project exports an exact 1103 fact, that alone is
not the complete 4.1.7/4.1.8 cohort.

P111 already gives the machine-readable project universe.

P112 therefore narrows the primary acquisition to:

FAIR_IH_CROSS_PROJECT_KEHOP_1103_MONITORING_EXPORT_OR_SOURCE_AGGREGATE_REQUIRED

An admissible closure is either:

1. an institutional cross-project monitoring/report export joined to the P111
   project universe; or
2. a complete source-generated 1103 aggregate for the declared programme and
   cutoff scope.

Convenience samples or individually accessible projects are rejected as a
national cohort denominator.

## 5. Preferred record route remains

For downstream P108 technical-performance joining, the preferred product
remains:

FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED

with:

- programme code;
- stable project ID;
- physical-completion date;
- exact 1103 category;
- final HET / final calculation or installed-product join key;
- HEM ID or HEM-generation agreement reference when present.

## 6. Numeric effect

No complete cross-project 1103 cohort is admitted in P112.

Therefore:

- calibrated retrofit floor remains 82.7861029945%
- HP_ONLY lower remains 0%
- HP_ONLY upper remains 17.2138970055%
- B02 remains 55%
- PEAK_LOAD_EFFECT remains 50%

## Sources

### SRC-B02-FAIR-MONITORING-REPORT-EXPORT-HELP-2026

Official FAIR/EUPR help:
https://help.fair.gov.hu/node/197

Role:
project/report monitoring export mechanics, fact fields, report binding and
access-control boundary.

### SRC-B06-HU-KEHOP-417-COMPLETION-2025

KEHOP Plusz-4.1.7-24 call authority already admitted by P109.

Role:
project-level physical-completion professional metric schema.

### SRC-B02-HU-KEHOP-418-COMPLETION-INDICATORS-2025

KEHOP Plusz-4.1.8-24 counterpart already admitted by P109.

Role:
same project-level professional metric schema for Budapest.

## Canonical boundaries

PROJECT-LEVEL MONITORING EXPORT != CROSS-PROJECT COMPLETE COHORT

GENERIC MONITORING EXPORT CAPABILITY != OBSERVED KEHOP 1103 EXPORT

PROFESSIONAL METRIC SCHEMA != PUBLIC FIELD AVAILABILITY

FACT VALUE EXPORT != TECHNICAL U DISTRIBUTION

1103 COMPLETION FACT != EKR/HEM CLASSIFICATION
