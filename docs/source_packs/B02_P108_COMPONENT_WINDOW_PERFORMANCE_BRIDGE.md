# B02-P108 — COMPONENT-SPECIFIC WINDOW REPLACEMENT PERFORMANCE BRIDGE

## Goal

P107 resolved the HUN Invert numeric extract but showed that whole-building
renovation generation cannot stand in for component-specific window
replacement.

The exact blocker was:

`COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED`.

P108 resolves that blocker at **record/project level**.

## 1. Hungarian programme chain

The current MFB KEHOP Plusz Otthonfelújítási Program permits window
replacement / energy-saving modernization as a supported envelope action.

B06-P64 already admitted the current programme completion chain:

`realized scope + final invoice + performance confirmation + final HET + final energy calculation`

with the same record, intervention, project and site identity.

Therefore a completed project whose realized scope explicitly contains window
replacement has an authoritative action/delivery identity.

## 2. Two admissible performance paths

### A. Final detailed energy calculation

If the post-completion energy calculation contains explicit window U values and
those values are explicitly linked to the realized replaced-window scope, the
same completed-project record contains:

`WINDOW REPLACED + POST-STATE WINDOW U`.

A final HET by itself is not sufficient. The component value must be explicit
and scope-linked.

### B. Installed product performance declaration

The public KTI Construction Product Registry contains approved construction
products and performance declarations. The OFP key-product database remains
part of the KEHOP programme infrastructure.

A catalogue product is **not** automatically an installed product.

This path is admitted only when:

- the exact installed product reference is present;
- its U value is explicit;
- the product reference is linked to the final invoice / performance
  confirmation;
- the same realized scope contains the window replacement.

Then:

`WINDOW REPLACED + INSTALLED PRODUCT DoP U`

is a valid component-specific record.

## 3. Whole-dwelling boundary

Even when all replaced openings are compliant:

`REPLACED OPENING COMPLIANCE != WHOLE DWELLING WINDOW COMPLIANCE`.

Whole-dwelling promotion still requires either:

- explicit full-dwelling window coverage; or
- independently verified compliant state of all remaining windows.

## 4. EKR overlap boundary

A KEHOP-financed window project is not automatically a non-EKR project.

Therefore:

`KEHOP COMPLETED PROJECT != NON-EKR PROJECT`.

Before using a KEHOP cohort as the non-EKR branch, HEM/EKR attribution or a
defensible overlap bound is required.

## 5. Blocker result

Resolved:

`COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED`

as:

`QUALIFIED_RECORD_LEVEL_KEHOP_WINDOW_COMPLETION_PERFORMANCE_BRIDGE`.

The new exact population blocker is:

`KEHOP_COMPLETED_WINDOW_PROJECT_TECHNICAL_COHORT_REQUIRED`.

This is a much narrower acquisition problem: enumerate completed projects with
realized window scope and one of the two admitted post-state performance paths.

## 6. Numeric effect

No public completed-project technical cohort has yet been identified.

Therefore the current national calibrated programme-action bounds remain:

- retrofit floor: **82.7861029945%**
- HP_ONLY lower: **0%**
- HP_ONLY upper: **17.2138970055%**

B02 remains 55%; PEAK_LOAD_EFFECT remains 50%.

## Canonical boundaries

`PROGRAMME WINDOW ELIGIBILITY != REALIZED WINDOW REPLACEMENT`

`FINAL HET ONLY != REALIZED WINDOW SCOPE`

`PRODUCT CATALOGUE ENTRY != INSTALLED PRODUCT`

`SAME PROJECT DOCUMENT SET != AUTOMATIC COMPONENT LINK`

`REPLACED OPENING COMPLIANCE != WHOLE DWELLING WINDOW COMPLIANCE`

`KEHOP COMPLETED PROJECT != NON-EKR PROJECT`

`RECORD-LEVEL BRIDGE != NATIONAL POPULATION SURFACE`
