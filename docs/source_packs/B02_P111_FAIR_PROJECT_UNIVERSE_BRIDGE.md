# B02-P111 — FAIR PROJECT-UNIVERSE EXPORT BRIDGE

## Goal

P110 identified the exact KEHOP implementation / FAIR administrative locus and
defined the minimum admissible 1103 aggregate and preferred record extract.

P111 asks a narrower acquisition question:

Can the KEHOP 4.1.7/4.1.8 project universe itself be obtained from FAIR in
machine-readable form, so the only remaining acquisition is the project-level
completion-indicator/1103 join?

The answer is yes for the project universe and not yet for the 1103 completion
field.

## 1. Official FAIR supported-project export

The official FAIR/EUPR help for Támogatott projekt kereső states that:

- supported-project data come from programme information systems, including
  EUPR;
- the data are refreshed daily;
- search results can be exported as CSV for authenticated SSO users;
- the general export can be subject to a 300-row cap, except Szechenyi Terv
  Plusz, where the documentation states no result-row limit.

This is a concrete machine-readable acquisition route rather than a generic
assumption that FAIR may contain the projects.

Canonical result:

KEHOP 4.1.7/4.1.8 -> FAIR supported-project search -> SSO CSV export

For the project-universe layer this is qualified.

## 2. What the documented export does and does not expose

The official help documents project/search fields such as:

- call identifier/name;
- project title;
- beneficiary;
- awarded support;
- decision date;
- programme / operational programme;
- region and location;
- project identifiers and financial/project metadata;
- intervention-category metadata.

The documented field list does not establish exposure of the professional
physical-completion field:

Energiahatékonysági intézkedés kategória

nor an exact:

MEKH 1103

filter/export.

Therefore:

FAIR PROJECT CSV != COMPLETION INDICATOR EXPORT

and:

PROJECT METADATA != MEASURE CATEGORY 1103.

P111 does not invent the missing field.

## 3. Internal FAIR indicator locus remains real

The current FAIR legal architecture independently supports why the missing
field can exist outside the documented search export.

The FAIR Központi Rendszer is defined as the system serving the registration of
programme resources, indicators and their fulfilment.

Combined with P109 and P110:

- P109 proves the KEHOP completion indicator carries MEKH measure categories;
- P110 proves the KEHOP implementation / FAIR administrative ownership;
- P111 proves a machine-readable project-universe export route.

The unresolved acquisition is now one exact bridge:

FAIR project_id -> physical-completion measure category -> 1103

or an equivalent complete source-generated 1103 aggregate.

## 4. Programme-scale control

MFB stated on 2026-04-29 that the combined KEHOP Plusz 4.1.7/4.1.8 programmes
had about HUF 73 billion in programme resources tied up and were expected to
support nearly 10,000 homes.

This is useful only as an approximate programme-scale plausibility control.

It is not:

- a physically completed-project count;
- an exact 4.1.7/4.1.8 project-universe count;
- an 1103 count;
- a window-replacement share;
- a technical-performance cohort.

Canonical boundary:

NEARLY 10,000 EXPECTED HOMES != COMPLETED PROJECT COUNT.

## 5. Blocker repair

P110 primary residual:

FAIR_IH_KEHOP_1103_COMPLETION_EXPORT_OR_AGGREGATE_REQUIRED

is superseded because the generic machine-readable project-universe route is
now qualified.

New exact primary residual:

FAIR_IH_KEHOP_1103_COMPLETION_INDICATOR_JOIN_OR_SOURCE_AGGREGATE_REQUIRED

Preferred technical route remains:

FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED

Downstream independent residuals remain:

- KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED
- KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED

## 6. Numeric effect

No project-level completed 1103 classification or complete source-generated
1103 aggregate is admitted in P111.

Therefore:

- calibrated retrofit floor remains 82.7861029945%
- HP_ONLY lower remains 0%
- HP_ONLY upper remains 17.2138970055%
- B02 remains 55%
- PEAK_LOAD_EFFECT remains 50%

## Sources

### SRC-B02-FAIR-SUPPORTED-PROJECT-SEARCH-HELP-2026

Official EUPR/EPTK / FAIR help:
https://help.fair.gov.hu/node/2060

Role:
machine-readable supported-project universe route; daily refresh; authenticated
CSV export; Szechenyi Terv Plusz no result-row limit.

### SRC-B02-HU-60-2014-FAIR-REGULATION

Official Nemzeti Jogszabálytár:
https://njt.jog.gov.hu/jogszabaly/2014-60-20-22

Role:
FAIR system semantics; FAIR KR indicator and fulfilment registry authority.

### SRC-B02-MFB-OFP-PROGRAMME-SCALE-2026

Official MFB release, 2026-04-29:
https://www.mfb.hu/kiemelkedo-igenylesi-szamokkal-zarul-az-energiahatekonysagi-otthonfelujitasi-program-s2879

Role:
approximate combined 4.1.7/4.1.8 programme-scale control only.

## Canonical boundaries

FAIR PROJECT CSV != COMPLETION INDICATOR EXPORT

PROJECT METADATA != MEASURE CATEGORY 1103

LOGIN-GATED SEARCH EXPORT != INTERNAL INDICATOR EXPORT

NEARLY 10,000 EXPECTED HOMES != COMPLETED PROJECT COUNT

PROJECT UNIVERSE ROUTE != TECHNICAL U DISTRIBUTION
