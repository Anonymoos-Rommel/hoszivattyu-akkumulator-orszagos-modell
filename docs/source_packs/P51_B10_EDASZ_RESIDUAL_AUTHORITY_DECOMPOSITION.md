# B10-P51 — ÉDÁSZ RESIDUAL AUTHORITY DECOMPOSITION

Status date: 2026-09-05

Canonical base: `726661568989eec5825e554bb5f8033852448f2f`

## Purpose

P51 closes the accounting ambiguity around the **59 unresolved unique ÉDÁSZ source tokens** left by P49 and preserved by P50.

It is a fail-closed classification slice, not a normalization or promotion slice.

P51 asks one narrow question:

> After the 30 P50 spelling-equivalence diagnostics and the six P49 cross-DSO whole-settlement conflicts are separated, what exact residual source-form/grain population remains?

The answer is **23 unique source forms / 24 source occurrences**.

P51 adds **zero** service-area membership rows.

## Authority surface

Current DSO authority remains:

- `SRC-B10-EON-EDASZ-M1-CANDIDATE-2025`
- official E.ON Észak-dunántúli M1 attachment, revision `20241209`
- URL: `https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EED/2025/EED_elo_usz_melleklet_20241209%20%28v1%29.pdf`

Upstream frozen audit/accounting surfaces:

- P49 whole-settlement completion and its six `CROSS_DSO_WHOLE_CONFLICT_EXCLUDED` rows;
- P50 exact 30-row spelling-equivalence authority audit.

P51 introduces no new external identity authority.

## Exact unresolved partition

The P49/P50 unresolved population is now decomposed exactly:

`30 P50 spelling diagnostics + 6 P49 cross-DSO conflicts + 23 P51 residual source forms = 59 unresolved unique tokens`

Occurrence accounting is also exact:

`30 + 6 + 24 = 60 unresolved source occurrences`

The unique/occurrence difference is entirely the source-native duplicate `Séska`, which occurs twice.

The partition is frozen in:

- `registry/dso_service_area_membership_edasz_p51_residual_authority_audit.csv`
- `registry/dso_service_area_membership_edasz_p51_authority_manifest.csv`

Exact P51 residual audit-set SHA-256 over sorted
`source_token|source_occurrence_count|residual_class|admission_status` rows:

`042df54daae95c99a52c734aa397f7d9201616f9f61a138c5cf30d594346a70f`

## Nine P49 special / mixed-grain forms

P49 already identified the following source forms as examples of the special/mixed administrative-grain population. P51 freezes the exact nine-member subset within the final residual set:

- `Ács-Jegespuszta`
- `Gánt Vérteskozma`
- `Isztimér-Királysz.`
- `Kerkateskánd-hegy`
- `Lesencei-Uzsabánya`
- `Lovászi Luku-hegy`
- `Rábapaty-Felsőpaty`
- `Szőce-Rimány`
- `Szt.Királyszabadja`

Their P51 class is `SPECIAL_OR_MIXED_GRAIN`.

That label is an inherited fail-closed routing classification. It is **not** a claim that every compound component is a KSH settlement part, nor does it identify the parent settlement, coverage share, or programme usage-location mapping.

`SPECIAL OR MIXED SOURCE LABEL != WHOLE-SETTLEMENT MEMBERSHIP`

Promotion requires identity/grain authority or usage-location resolution specific to the source form.

## Fourteen standalone non-exact source forms

The remaining 14 residual forms are standalone current-M1 labels that were not admitted by the P49 exact KSH identity path and are outside the P50 30-edge spelling-equivalence set:

- `Dunakilti`
- `Ferőhomok`
- `Fertőújlak`
- `Iklóbördöce`
- `Jóbháza`
- `Kajérpéc`
- `Kecséd`
- `Nádasladány`
- `Nagyszentjánosk`
- `Séska`
- `Srród`
- `Zalagyömrő`
- `Zichiújfalu`
- `Zsédely`

Their P51 class is `STANDALONE_NONEXACT_IDENTITY`.

This classification deliberately does **not** diagnose the reason for non-equivalence. P51 does not call any row a typo, historical name, OCR artifact, renamed settlement, settlement part, or fuzzy KSH match.

`NONEXACT STANDALONE SOURCE FORM != AUTHORIZED CANONICAL IDENTITY`

Any future promotion requires identity-specific authority independently binding the ÉDÁSZ source form to a canonical whole-settlement identity.

## Duplicate handling

`Séska` is present twice in the current M1 source.

P51 records:

- one unique residual identity token;
- `source_occurrence_count = 2`;
- no second identity;
- no inferred canonical target.

`DUPLICATE SOURCE OCCURRENCE != SECOND LOCALITY IDENTITY`

## Boundaries preserved

P51 does not alter any P49 or P50 admission decision.

It does not:

- strip suffixes;
- split compound labels into multiple memberships;
- expand abbreviations;
- perform fuzzy, accent, edit-distance, or phonetic matching;
- infer old-to-current settlement-name continuity;
- override any P49 cross-DSO conflict;
- infer whole-settlement coverage from administrative-unit presence;
- infer programme usage-location mapping.

The governing boundary is:

`SOURCE FORM PRESENCE != WHOLE-SETTLEMENT IDENTITY AUTHORITY`

## State impact

P51 adds **zero** service-area membership rows.

ÉDÁSZ remains:

`45 historical + 769 P49 = 814 materialized current provable whole-settlement identities`

The unresolved population remains:

- **59 unique source tokens**;
- **60 source occurrences**;
- partitioned exactly as `30 + 6 + 23` unique and `30 + 6 + 24` occurrences.

The operator extraction state remains `PARTIAL_TRANCHE_MATERIALIZED`.

The national canonical crosswalk remains header-only.

The standing blockers remain in force, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

P51 does not prove node identity, headroom, limiting-node status, reinforcement requirement, reinforcement cost, programme-incremental CAPEX, or timing.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
