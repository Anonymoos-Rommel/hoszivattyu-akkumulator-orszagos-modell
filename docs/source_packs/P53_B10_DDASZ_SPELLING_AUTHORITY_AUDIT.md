# B10-P53 — E.ON DDÁSZ spelling-equivalence authority audit

Status date: 2026-09-05

Canonical base: `f98fc6fd41f871c124d3d42c71e784c51cdbb6de`

## Purpose

P53 is a fail-closed authority-audit slice over the exact fourteen spelling-equivalence diagnostics left unresolved by P48 for E.ON Dél-dunántúli Áramhálózati Zrt.

It does not create a generalized normalization rule and it does not add service-area membership rows.

## Current authority boundary

P48 remains the current DDÁSZ territorial authority path through:

- `SRC-B10-EON-DDASZ-M1-CANDIDATE-2025`;
- the current approved-package M1 attachment, revision `20241209`;
- the P22 approved-package / MEKH revision-lineage conclusion.

P53 does not replace or weaken that currentness edge.

## Historical comparison source

P53 compares the fourteen P48 diagnostics against an official E.ON-hosted 2022 E.ON Áramszolgáltató Kft. universal-service rules attachment:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/eas/2022/EON_Aramszolg_egyetemes_USZ_fugg_mell_korrekturazott_tervezet.pdf`

Its 5th appendix is titled:

`Az E.ON Áramszolgáltató Kft. működési területe`

and its table columns are:

`Település | Hálózati engedélyes | Megye`

This makes the source useful as historical E.ON network-licensee corroboration. It is not the current DDÁSZ M1 authority, it is not a KSH identifier source, and it does not explicitly bind a current DDÁSZ M1 source form to a five-digit KSH settlement code.

Therefore:

`HISTORICAL E.ON NETWORK-LICENSEE TABLE != CURRENT DDÁSZ M1 AUTHORITY`

`HISTORICAL CANONICAL-FORM DSO CORROBORATION != CURRENT M1 SOURCE-FORM EQUIVALENCE`

## Exact fourteen-edge result

The historical E.ON table yields two disjoint classes.

### Four canonical-form DSO corroborations

For exactly four P48 diagnostics the historical E.ON table uses the current KSH spelling while identifying E.ON Dél-dunántúli Áramhálózati Zrt. as the network licensee:

| Current DDÁSZ M1 source form | Diagnostic current KSH identity | KSH code | Historical E.ON form |
| --- | --- | ---: | --- |
| `Kálóz` | `Káloz` | `16683` | `Káloz` |
| `Kazsók` | `Kazsok` | `26888` | `Kazsok` |
| `Köröshegy` | `Kőröshegy` | `15510` | `Kőröshegy` |
| `Kövágótöttös` | `Kővágótöttös` | `06992` | `Kővágótöttös` |

These rows are useful corroboration, but they still do not contain an explicit identity edge from the current M1 source form to the KSH code. P53 therefore does not infer that edge from spelling similarity alone.

### Ten historical repetitions of the current source variant

For the remaining ten diagnostics the historical E.ON table repeats the same non-KSH source form seen in the current DDÁSZ M1:

- `Balatonöszöd`;
- `Baranyahidvég`;
- `Csikóstöttös`;
- `Cun`;
- `Füzvölgy`;
- `Kallosd`;
- `Öcsény`;
- `Szabadhidvég`;
- `Turony`;
- `Vókány`.

For these rows the P50/P52 boundary applies directly:

`HISTORICAL REPETITION OF THE SAME SOURCE VARIANT != INDEPENDENT IDENTITY-EQUIVALENCE AUTHORITY`

## Admission decision

P53 adds **zero** service-area membership rows.

No audited edge is promoted because neither class supplies a claim-specific current identity binding from the current DDÁSZ M1 source form to the five-digit KSH settlement identity.

P53 does not authorize:

- fuzzy or edit-distance matching;
- accent folding;
- typo correction;
- generalized orthographic normalization;
- historical-to-current canonicalization;
- inference from same operator and similar spelling;
- replacement of the current DDÁSZ M1 authority by a historical supplier document.

The exact audit-set SHA-256 is:

`e3a7e8e3b25964b3964eaaac027edc9fb52c4420f06391aed016fcc34639a2ce`

## Population consequence

P48 remains unchanged:

- 43 historical DDÁSZ whole-settlement identities;
- 777 P48 DER whole-settlement identities;
- **820 materialized current provable whole-settlement identities**;
- **296** current M1 source tokens remain fail-closed at the P48 completion boundary.

The fourteen spelling diagnostics remain unresolved; P53 merely sharpens their authority classification into `4 + 10` without promotion.

The national canonical crosswalk remains header-only.

## Non-claims and B10 state

P53 does not prove complete DDÁSZ membership, partial-settlement usage-location membership, exact DSO nodes, complete topology, limiting nodes, headroom sufficiency, reinforcement need, reinforcement cost, programme-incremental CAPEX, or timed programme CAPEX.

The standing blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`.

B10 remains `IN_PROGRESS` and readiness remains **15%**.
