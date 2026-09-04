# B10-P47 — MVM Émász / KSH whole-settlement completion

Status date: 2026-09-04

Canonical base: `b09c7773fba94a7a3afe34d8df88fb6b45837b2b`

## Purpose

P47 is a **completion-first evidence/data slice**, not a new semantic gate and not another arbitrary 40-row tranche.

It accounts for the complete current MVM Émász M1 source list, materializes every whole-settlement identity that can presently be admitted under the existing exact-identity rules, and leaves the remaining spelling and named-subsettlement cases explicitly fail-closed.

## Core boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != NAMED SUBSETTLEMENT OR SETTLEMENT PART`

`IDENTITY-SPECIFIC SOURCE-FORMAT SPLIT != GENERAL TOKEN SPLITTER`

`SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE`

`COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

These boundaries are fail-closed.

## Authority chain

### Current MVM Émász territorial authority

`SRC-B10-MVM-EMASZ-M1-2026`

Official current M1 attachment exposed from the 2026-05-26 business-rule package:

`https://mvmemaszhalozat.hu/-/media/emaszhalozat/emasz-halozat-uzletszabalyzat-szabalyzatok/uzletszabalyzat-20260526/msz_uzletszabalyzat_melleklet_2025_i_md_2025_1022.ashx?hash=EB463FF2F46DD05995991DD2B7C06AEA4AAC0195&la=hu-hu`

The M1 section is titled `Az MVM Émász Áramhálózati Kft. területi illetékessége`.

### KSH identity authority

Primary current identity authority:

`SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`

Reproducible locator:

`SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

Direct immutable KSH-ID authority used for the tightly scoped exceptions:

`SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`

The derived locator is only a locator. It does not replace KSH authority and does not upgrade P47 rows to OBS. P47 rows remain `DER`.

## Complete source accounting

The current M1 text yields **749 source tokens** under the bounded extraction used for P47.

- **99** tokens carry a parenthesized named-subsettlement / settlement-part / special-grain form and are not promoted to KSH whole-settlement membership.
- **650** source tokens are non-parenthesized candidates.
- two of those non-parenthesized source tokens contain an evident missing delimiter and each represent two separately evidenced KSH whole settlements:
  - `Márkháza Mályi` → `Márkháza` + `Mályi`;
  - `Szentistván Szentistvánbaksa` → `Szentistván` + `Szentistvánbaksa`.
- therefore the non-parenthesized layer corresponds to **652 potential whole-settlement identities** after those two tightly scoped source-format splits.
- two spelling edges remain deliberately unresolved:
  - current MVM `Fóny` versus KSH `Fony` (`17932`);
  - current MVM `Hídvégardó` versus KSH `Hidvégardó` (`25672`).

P47 does **not** authorize those two equivalences and does not create a general accent or fuzzy-name rule.

## P47 materialization

Historical MVM Émász state is preserved unchanged:

- P21: **5 OBS** rows;
- P36: **40 DER** rows;
- historical total: **45**.

P47 adds **605 DER whole-settlement identities**:

- **599** exact current-M1 / current-KSH derived-locator joins;
- `Miskolc` (`30456`) from direct official KSH 2019 identity because the derived locator exposes repeated base rows carrying the same code; repeated identical code does not create competing identity;
- `Mátraterenye` (`33525`) from direct official KSH 2019 identity because locator omission is not treated as absence or zero;
- four identities from exactly two identity-specific current-M1 source-format splits:
  - `Márkháza` (`14641`);
  - `Mályi` (`27395`);
  - `Szentistván` (`22169`);
  - `Szentistvánbaksa` (`08484`).

Therefore:

**45 historical + 605 P47 = 650 materialized MVM Émász whole-settlement identities.**

This is **two identities short of the 652 potential whole-settlement identity layer** solely because the two spelling-equivalence edges remain unauthorized.

## Normalized storage

P47 uses a compact normalized representation because 599 of the 605 new rows share identical operator, service-area, evidence-status and source-lineage metadata.

- `registry/dso_service_area_membership_emasz_p47_pairs.csv` stores the exact 605 KSH code/name pairs;
- `registry/dso_service_area_membership_emasz_p47_manifest.csv` stores the invariant MVM Émász whole-settlement DER semantics and normal source chain once;
- `registry/dso_service_area_membership_emasz_p47_exceptions.csv` stores the six rows whose KSH-identity path differs from the normal derived-locator path.

This normalization is storage-only:

`NORMALIZED STORAGE != WEAKER ROW-LEVEL EVIDENCE`

The test contract reconstructs and validates the effective row semantics for every pair.

## Fail-closed unresolved population

P47 intentionally leaves unresolved:

1. `Fóny` → `Fony` (`17932`) spelling-equivalence decision;
2. `Hídvégardó` → `Hidvégardó` (`25672`) spelling-equivalence decision;
3. all **99** parenthesized named-subsettlement / special-grain M1 tokens at whole-settlement grain.

No missing row is interpreted as zero, non-membership, or permission to infer a nearest/parent settlement.

## Non-claims

P47 does not prove:

- complete MVM Émász operator membership crosswalk;
- usage-location membership for named settlement parts;
- a complete national KSH-to-DSO crosswalk;
- exact DSO node identity;
- complete node inventory or topology;
- headroom sufficiency;
- limiting-node status;
- reinforcement requirement or cost;
- programme-incremental CAPEX.

The canonical national crosswalk remains header-only. The blockers remain active, including `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK` and `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
