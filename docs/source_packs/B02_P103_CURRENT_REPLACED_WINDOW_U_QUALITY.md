# B02-P103 — CURRENT REPLACED-WINDOW U-QUALITY EVIDENCE

## Goal

Continue from the P102 primary residual:

`CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED`

and determine whether public Hungarian evidence can identify the U-quality of the
2022 `WINDOW_REPLACED` stock branch.

## 1. First repair: the prospective programme target was stale

P100 inherited the P80 historical reference-retrofit timber/PVC window value:

**1.15 W/m2K**.

That value remains valid as historical P80 calibration.

However the prospective programme is current. The already-admitted current
9/2023. (V. 25.) ÉKM authority used by P92 gives, for >0.5 m2 wood/PVC facade
glazed openings:

**1.10 W/m2K**.

P103 therefore repairs only the current prospective programme target:

`WINDOW: 1.15 -> 1.10 W/m2K`.

The historical P80 evidence is not rewritten into a false current source.

## 2. Current and historical regulatory epochs

P103 materializes three requirement contexts.

### Historical generic tier

- wood/PVC: **1.60 W/m2K**;
- metal frame: **2.00 W/m2K**.

### Historical stricter energy-saving renovation tier

For affected structures in qualifying energy-saving renovation after
2017-12-31:

- wood/PVC: **1.15 W/m2K**;
- metal frame: **1.40 W/m2K**.

### Current 9/2023 ÉKM tier

- wood/PVC >0.5 m2 facade glazed opening: **1.10 W/m2K**;
- metal frame: **1.40 W/m2K**.

This surface is useful for validation and chronology.

It does not prove installed performance:

`LEGAL U REQUIREMENT != VERIFIED REALIZED U`.

Even a current wood/PVC replacement whose legal requirement equals 1.10 stays
unresolved unless realized/project Uw evidence is admitted for the claim.

## 3. KSH public replacement-recency schema

The public KSH 2020 household energy questionnaire contains exactly the type of
chronology variable needed for a future regulatory-epoch crosswalk.

It distinguishes window replacement as:

- partial;
- all;
- none;
- unknown.

It also records the most recent replacement as:

- last year;
- 2-10 years;
- more than 10 years;
- unknown.

But P103 did not find a public national response distribution for this recency
variable, and the public instrument does not supply frame material or realized
Uw.

The interviewer guidance also prevents promotion of the "all" label into exact
technical proof for every opening.

Therefore:

`KSH REPLACEMENT RECENCY != FRAME MATERIAL != REALIZED Uw`.

## 4. BME 2026 current Hungarian EPC calibration

The already-admitted BME RBSM 2026 source provides a valuable independent
current/Hungarian calibration for the examined Type-5 family-house archetype.

For the EPC-derived full-window U surface:

- source values are filtered to **1.10-4.00 W/m2K**;
- fitted distribution: **Normal**;
- mean: **2.518 W/m2K**;
- sigma: **0.670 W/m2K**.

This is strong evidence that a real current Hungarian EPC window-U surface can
be represented quantitatively.

But the cohort is:

`TYPE-5 FULL WINDOW EPC SET`

not:

`TYPE-5 REPLACED WINDOW SUBSET`.

And Type-5 is not the entire Hungarian stock.

Therefore P103 deliberately forbids conversion of this distribution into a
national replaced-window reference-compliance percentage.

## 5. Fail-closed runtime gate

P103 makes replaced-window classification executable.

If explicit realized `Uw` exists:

- `Uw <= 1.10 -> REFERENCE_WINDOW_SATISFIED_VERIFIED_U`;
- `Uw > 1.10 -> REFERENCE_WINDOW_DEFICIT_VERIFIED_U`.

If realized `Uw` is absent:

- replacement status alone -> unresolved;
- replacement status + age -> unresolved;
- replacement status + legal epoch -> unresolved;
- current legal wood/PVC requirement equal to 1.10 -> still unresolved;
- metal-frame current legal limit 1.40 -> unresolved.

The legal surface can validate plausibility; it cannot replace realized
performance evidence.

## 6. National result

P103 found no defensible public evidence that identifies a national
replaced-window realized-Uw distribution or a bounded national compliance share.

Therefore **no new national percentage is invented**.

The validated P102 programme-action bounds remain:

- conservative synthetic type-mean calibrated retrofit floor:
  **82.7861029945%**;
- HP_ONLY candidate lower edge:
  **0%**;
- HP_ONLY candidate upper edge:
  **17.2138970055%**.

This unchanged numerical result is itself important: P103 separates a genuine
evidence gap from a modelling opportunity.

## 7. New exact residual

The former broad blocker:

`CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED`

is narrowed to:

`CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED`.

If a regulatory-proxy route is attempted instead of direct Uw evidence, it
also requires:

`PUBLIC_REPLACEMENT_RECENCY_X_FRAME_MATERIAL_CROSSWALK_REQUIRED_IF_REGULATORY_PROXY_USED`.

The independent wall residual remains:

`MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED`.

## 8. What would close the window blocker?

Any of the following can qualify, if provenance and population semantics are
adequate:

1. a representative current Hungarian replaced-window Uw distribution;
2. an EPC/OÉNY extract identifying replaced-window performance with sufficient
   cohort semantics;
3. a public programme completion dataset with replacement date, frame class and
   verified Uw;
4. a defensible bounded crosswalk from replacement epoch x frame material x
   verified requirement/commissioning evidence.

A product catalogue or current legal limit alone is insufficient.

## 9. Readiness

P103 improves evidence governance and corrects the prospective target, but does
not add a defensible national numeric current-window share.

Therefore:

- **B02 remains 55%**;
- **PEAK_LOAD_EFFECT remains 50%**;
- **Q-B02-004 remains OPEN_NARROWED**.

## 10. Canonical boundaries

`LEGAL U REQUIREMENT != VERIFIED REALIZED U`

`WINDOW REPLACED STATUS != REALIZED U`

`KSH REPLACEMENT RECENCY != FRAME MATERIAL`

`BME TYPE5 FULL WINDOW U DISTRIBUTION != REPLACED WINDOW U DISTRIBUTION`

`TYPE5 EPC CALIBRATION != NATIONAL WINDOW POPULATION DISTRIBUTION`

`REGULATORY LIMIT MATCH != REALIZED COMPLIANCE`
