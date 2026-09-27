# Evidence tiers, canonical base values and validation debt

**Status:** CANONICAL  
**Effective:** 2026-09-27  
**Scope:** B01-B20 blockers, missing-source decisions, canonical model inputs and final decision-grade validation

## 1. Purpose

The project separates **model continuation** from **final evidence closure**.

A missing exact primary document, laboratory report, private dataset or record-level source must not automatically stop the national model when the best available evidence is already strong enough to support one defensible canonical base value. At the same time, a provisional value must never be promoted to verified fact.

Canonical rules:

`MISSING EXACT PRIMARY EVIDENCE != AUTOMATIC MODEL BLOCKER`

`NO DEFENSIBLE CANONICAL BASE == MODEL BLOCKER`

`PROVISIONAL BASE != VERIFIED FACT`

`MODEL CONTINUATION != FINAL VALIDATION`

## 2. Three evidence tiers

### E1 — VERIFIED / AUTHORITATIVE

The claim or model input is supported at the required grain, boundary, unit and reference period by authoritative or otherwise decision-grade evidence.

Typical examples:
- source-native official numeric data;
- exact manufacturer/laboratory record;
- exact legal/tariff authority;
- reproducible derived value from E1 inputs;
- an admitted representative/calibrated estimator whose evidence contract is complete for the claim.

E1 may be used in the canonical model and may support final decision-grade publication within its declared scope.

### E2 — PROVISIONAL_BASE / VALIDATION_DEBT

The exact underlying primary evidence is unavailable, non-public, not yet released or incomplete, but the available evidence is sufficiently strong to select **one** defensible canonical base.

E2 admission requires all of the following:

1. the physical/economic quantity is clearly defined;
2. unit, grain, product/system boundary and reference period are explicit;
3. at least one high-authority direct support or a convergent set of qualified independent supports exists;
4. applicability to the target product/population/system is documented;
5. no stronger contradictory evidence is known;
6. any derivation is reproducible and explicit;
7. the exact missing evidence is registered as validation debt;
8. the value is labelled E2/PROVISIONAL_BASE and is never promoted to OBS merely because it is used by the model.

E2 **authorizes model continuation** for the declared scope. It does not close the validation debt.

For final decision-grade closure, each material E2 item must be upgraded to E1 or remain explicitly disclosed as unresolved validation debt; it may not silently become verified.

### E3 — ASSUMPTION_ONLY / INSUFFICIENT_EVIDENCE

The available evidence does not support a defensible canonical base at the required boundary.

E3 may be used only as:
- an explicit `ASS`, `SCN` or `POL` value where that use is legitimate; or
- an optional exploratory calculation that is not presented as the canonical central model.

If the quantity is required by the central model and no E1/E2 base exists, E3 is a **MODEL_BLOCKER**.

Legal permission, tariff eligibility, permit status and other discrete authority questions are never upgraded to E2 by statistical or engineering inference. They remain fail-closed until the relevant authority is established.

## 3. One canonical base per model variable

For evidence-gap handling, the central model uses exactly one canonical base value or one canonical source-native artifact per variable/input.

Canonical rule:

`ONE CANONICAL VALUE PER MODEL VARIABLE`

For a scalar:

`X = X_base`

not:

`X_low / X_base / X_high`

merely because the exact primary source is unavailable.

The project must not create an automatic Cartesian product of independent low/base/high substitutions for missing evidence.

Canonical rule:

`NO AUTOMATIC LOW/BASE/HIGH CARTESIAN PRODUCT FOR SOURCE GAPS`

An E2 base is selected by triangulation and applicability, not by midpoint convenience.

## 4. Statistical uncertainty is not source-gap substitution

This policy does **not** erase real statistical uncertainty, population heterogeneity, measurement error or a source-native distribution.

A representative survey, calibrated population estimator or physical distribution may still report:
- confidence/credible intervals;
- estimator error;
- source-native quantiles;
- structural diagnostics.

Those outputs describe uncertainty in the evidence or target population. They are not permission to create separate independent low/base/high model inputs for every missing source.

The canonical central run consumes one selected base definition for each input. Uncertainty may be reported alongside the central result or evaluated in a separately declared study, but source gaps must not be converted automatically into a combinatorial worst-case space.

## 5. Blocker classes

Every current `OPEN` blocker must be assigned an evidence tier and a blocker class in `registry/project_blocker_evidence_audit.csv`.

Allowed blocker classes:

- `MODEL_BLOCKER` — central canonical computation cannot proceed for the affected output;
- `VALIDATION_BLOCKER` — E2 base allows computation, but final decision-grade validation remains open;
- `LEGAL_AUTHORITY_BLOCKER` — exact legal/regulatory/permission authority is required; fail closed;
- `POLICY_DECISION` — normative owner/policy choice; evidence informs but cannot determine it;
- `EXECUTION_DEPENDENCY` — no new source-gap blocker at this question; dependent computation still must be run;
- `OPTIONAL_EXTENSION` — not required by the core model unless the optional feature/claim is activated;
- `CONTRACT_BOUNDARY` — a deliberate prohibition or scope boundary, not a missing datum to be guessed.

## 6. Model blocker vs finalization blocker

The audit separately records:
- whether an item blocks the **central model** now; and
- whether it blocks **final decision-grade validation**.

This prevents the previous false equivalence:

`FINAL EVIDENCE NOT CLOSED == MODEL MUST STOP`

An E2 VALIDATION_BLOCKER normally has:

`model_blocker = no`

and:

`finalization_blocker = yes`

for material claims.

## 7. Record-level and legal boundaries remain fail-closed

E2 is not a shortcut around discrete record/project authority.

Examples:
- a national network cohort cannot certify a specific substation headroom;
- a population emitter estimate cannot pass a specific dwelling;
- a manufacturer-family base cannot prove an exact tested specimen;
- a legal interpretation cannot authorize H-tariff battery charging.

Exact record/project/legal claims still require claim-specific E1 authority.

## 8. Validation debt

Each E2 row must state:
- the missing exact evidence;
- who/what can supply it where known;
- what claim it would upgrade;
- whether the debt is material to finalization.

External acquisition can continue in parallel with modelling. If a later authoritative source changes an E2 base, the canonical value is replaced and affected outputs are rerun. History and provenance are preserved.

## 9. Transition rules

`E3 -> E2` only after the E2 admission gate is satisfied.

`E2 -> E1` only after authoritative/decision-grade validation closes the registered debt.

`E1 -> E2/E3` is required if a source becomes inapplicable, superseded, semantically mismatched or contradicted.

No evidence tier is permanent merely because it was previously accepted.

## 10. Current audit

The canonical current mapping is:

`registry/project_blocker_evidence_audit.csv`

Historical blocker audits remain historical evidence of the earlier decision state and are not rewritten.
