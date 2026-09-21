# B02-P75 — KEHOP structural-scope crosswalk on the exact P21/WBL grain

**State:** `KEHOP SCOPE CROSSWALK PARTIALLY RESOLVED WITH NUMERIC STRUCTURAL BOUNDS`

**Canonical base:** `e460bd2106e58006d7ea2540cf658f88e5a4dff2`

**Implementation date:** 2026-09-21

## 1. Purpose

P74 bound the official **3,556,000 HUF/set** complete emitter + secondary-circuit
maximum cost to the KEHOP source scope, but correctly refused to multiply that
price across all national nonreuse dwellings.

P75 quantifies the overlap between that programme's structural property scope
and the canonical B02 population model.

It does not manufacture a legal programme-eligibility count.

## 2. Current official MFB scope

The official MFB national programme overview dated 2026-01-21 states that:

- KEHOP Plusz-4.1.7-24 covers properties outside Budapest;
- KEHOP Plusz-4.1.8-24 covers Budapest;
- the programme concerns occupied one- and multi-dwelling family houses built
  and permitted before 2007.

The two programme variants therefore remove a national **geographic** gap for
this structural scope.

Current application availability is a separate question; both programme
routes were later suspended due to committed/exhausted funds. P75 uses the
published property-scope definition, not live funding availability.

## 3. Model crosswalk and evidence class

P75 joins on exact `cell_id`:

1. P21 calibrated FAMILY_HOUSE probabilities;
2. P22 source-derived heating topology;
3. P72 non-district physical-screening scope;
4. P73 latent central reuse/nonreuse contract.

The complete WBL/P21 calculation runs across **116,452** committed full-joint
rows.

P21 building type remains `ASS`.

Therefore:

`P21 FAMILY_HOUSE != LEGAL PROPERTY-REGISTER FAMILY-HOUSE CLASSIFICATION`.

The output is a modelled structural crosswalk, not a legal eligibility list.\n\n`STRUCTURAL_SCOPE_COMPATIBILITY != LEGAL_PROGRAMME_ELIGIBILITY`.

## 4. 2007 cutoff without invented precision

The WBL construction-period bands are:

- Y_LT1919;
- Y1919-1945;
- Y1946-1960;
- Y1961-1980;
- Y1981-2000;
- Y2001-2010;
- Y_GE2011.

The MFB cutoff is before 2007.

Therefore:

- all bands through **Y1981-2000** are definitely before 2007;
- **Y2001-2010** straddles the cutoff;
- **Y_GE2011** is after the cutoff.

P75 does not assume uniform construction years inside Y2001-2010.

Canonical boundary:

`Y2001-2010 != PROVEN PRE-2007`.

The straddling band's eligible fraction remains latent in `[0,1]`. This is
sufficient to produce valid bounds.

## 5. Exact CI-materialized P21 scenario results

The first P75 CI run on the complete committed dataset emitted:

### P21 CENTRAL scenario

- definite-pre2007 FAMILY_HOUSE × non-district:
  **1,915,040.991137**
- possible-pre2007 FAMILY_HOUSE × non-district:
  **2,108,846.960998**
- definite-pre2007 FAMILY_HOUSE × NHEAT:
  **790,210.708248**
- possible-pre2007 FAMILY_HOUSE × NHEAT:
  **810,370.805678**

### P21 FLAT structural-sensitivity scenario

- definite-pre2007 FAMILY_HOUSE × non-district:
  **1,902,145.425797**
- possible-pre2007 FAMILY_HOUSE × non-district:
  **2,098,377.659468**
- definite-pre2007 FAMILY_HOUSE × NHEAT:
  **784,618.148163**
- possible-pre2007 FAMILY_HOUSE × NHEAT:
  **804,921.877002**

The P21 scenarios are not mixed cell-by-cell. P75 takes coherent whole-scenario
endpoints.

## 6. Structural KEHOP candidate envelope

Combining:

- the lower P21 scenario for construction bands wholly before 2007; and
- the upper P21 scenario with the entire 2001-2010 cutoff-straddling band
  admitted only as a possibility;

gives:

`KEHOP_STRUCTURAL_CANDIDATE = [1,902,145.425797 ; 2,108,846.960998]`

expected dwelling-equivalents.

Relative to the exact B02 non-district physical screen of 3,389,817 dwellings:

`[56.113514% ; 62.211233%]`.

This is not a programme participation forecast.

## 7. Crosswalk to the P73 nonreuse set

P70/P72 already prove every NHEAT dwelling requires
`NEW_OR_REPLACE_DISTRIBUTION_REQUIRED` on the canonical central-hydronic
air-to-water route.

Therefore the minimum structurally compatible overlap is the minimum P21
scenario for:

`definite-pre2007 FAMILY_HOUSE × NHEAT`.

That value is:

**784,618.148163 expected dwelling-equivalents**

or:

**23.146328% of the physical-screening scope**.

For the upper endpoint:

- the entire 2001-2010 band may contain pre-2007 properties; and
- the full structurally compatible CENTRAL_HEATING population may occupy the
  nonreuse side of the P73 latent split.

Therefore:

`KEHOP_STRUCTURAL_SCOPE ∩ NONREUSE`

is bounded by:

`[784,618.148163 ; 2,108,846.960998]`

expected dwelling-equivalents,

or:

`[23.146328% ; 62.211233%]`

of the physical-screening scope.

## 8. What this resolves

P74 residual:

`NONREUSE_KEHOP_SCOPE_CROSSWALK_REQUIRED`.

P75 status:

`PARTIAL_RESOLVED_STRUCTURAL_BOUNDS`.

The broad search problem is gone. We now know quantitatively how large the
source-compatible structural overlap can be under the canonical P21/P22/P73
model.

## 9. What remains

P75 does not prove all programme/legal eligibility conditions.

Residual:

- `KEHOP_LEGAL_ELIGIBILITY_CONDITIONS`;
- `NONREUSE_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_BOUND_REQUIRED`.

The latter matters because the official KEHOP package ceiling cannot be
silently extended to nonreuse dwellings outside the source's family-house /
pre-2007 structural scope.

The Y2001-2010 sub-band can be researched later to tighten the interval, but it
is **not required for a valid bound**.

## 10. Non-claims

P75 does not claim:

- 1.90-2.11 million legally eligible KEHOP properties;
- 784,618 legally eligible programme participants;
- P21 FAMILY_HOUSE is an OBS legal property classification;
- all CENTRAL_HEATING candidates are nonreuse;
- a uniform pre/post-2007 split inside Y2001-2010;
- the KEHOP 3,556,000 HUF ceiling applies outside the source programme scope;
- Q-B02-004 is resolved.

B02 readiness remains **55%**.
