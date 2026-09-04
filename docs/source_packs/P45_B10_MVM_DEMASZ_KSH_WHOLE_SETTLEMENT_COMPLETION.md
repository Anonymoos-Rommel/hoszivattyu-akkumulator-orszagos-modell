# B10-P45 — MVM Démász / KSH whole-settlement completion

## Purpose

P45 is an evidence/data completion slice only. It completes every currently published **whole-settlement** MVM Démász service-area membership that can be joined to a current five-digit KSH settlement identifier, while preserving the separate usage-location gate for settlements that the operator publishes only as partly inside its service area.

The completion boundary is:

`COMPLETE WHOLE-SETTLEMENT M1 MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

and:

`20 PARTIAL SETTLEMENTS ACCOUNTED != EXACT USAGE-LOCATION RESOLUTION`

## Authorities

### MVM Démász current service-area publication

Source ID: `SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026`

The current operator publication separates:

- **256 settlements wholly inside** the MVM Démász service area; and
- **20 settlements partly inside** the MVM Démász service area.

P20 materialized 10 direct OBS whole-settlement memberships. P35 added 30 DER whole-settlement memberships. P45 adds the remaining **216** whole-settlement memberships, producing an exact **256/256 current whole-settlement population** across the immutable historical tranche plus the dedicated P45 completion tranche.

The source contains **276 settlement labels in total** at these two grains: 256 whole-settlement labels plus 20 partial-settlement labels. That denominator does not mean 276 whole-settlement memberships.

### KSH settlement identity

Source IDs:

- `SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`
- `SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

Every one of the 216 P45 whole-settlement names is joined by exact settlement-name identity to a five-digit KSH settlement identifier through the established reproducible locator. No fuzzy matching, accent normalization, approximate matching, or identity-specific spelling override is introduced by P45.

The P45 rows remain `DER`, not `OBS`, because the primary KSH XLSX row itself is not directly materialized in the repository:

`KSH PRIMARY SOURCE LOCATOR + REPRODUCIBLE DERIVED ROW LOCATOR != DIRECT PRIMARY ROW OBSERVATION`

## Exact completion result

P45 adds exactly **216 whole-settlement memberships**.

Together with the historical 40 MVM Démász rows:

`40 historical + 216 P45 = 256 current whole-settlement memberships`

Every P45 row is:

- `operator_id = MVM_DEMASZ`
- `service_area_id = MVM_DEMASZ:SERVICE_AREA`
- `coverage_scope = WHOLE_SETTLEMENT`
- `usage_location_requirement = NONE`
- `evidence_status = DER`
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`

The existing historical tranche is not rewritten. P45 uses a dedicated append-only completion surface.

## The 20 partial settlements

The current operator publication separately identifies these 20 settlements as only partly inside the service area:

- `Baja`
- `Csongrád`
- `Csabacsűd`
- `Dabas`
- `Dévaványa`
- `Érsekcsanád`
- `Gyomaendrőd`
- `Kunszentmárton`
- `Mohács`
- `Péteri`
- `Solt`
- `Szeghalom`
- `Szentes`
- `Tápiószőlős`
- `Tass`
- `Tiszakécske`
- `Tiszasas`
- `Tiszaug`
- `Újhartyán`
- `Zsadány`

These names are **not** promoted to whole-settlement membership rows. Their exact usage-location membership remains unresolved and must continue to fail closed under:

`Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED`

and the integration blocker:

`PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

P45 therefore does **not** claim a complete MVM Démász operator membership crosswalk. The existing source-registry extraction status remains `PARTIAL_TRANCHE_MATERIALIZED`: the whole-settlement population is complete, but the partial-settlement usage-location population is not.

## Fail-closed semantic boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP`

`COMPLETE WHOLE-SETTLEMENT M1 MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

`20 PARTIAL SETTLEMENTS ACCOUNTED != EXACT USAGE-LOCATION RESOLUTION`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

## What P45 does not prove

P45 does **not** claim:

- complete MVM Démász usage-location resolution for the 20 partial settlements;
- complete MVM Démász operator membership crosswalk;
- complete national KSH-to-DSO membership coverage;
- exact programme entity-to-node mapping;
- exact DSO node identity or complete topology;
- headroom sufficiency;
- limiting-node status;
- reinforcement need or reinforcement cost;
- total reinforcement project cost;
- customer connection charge;
- programme-incremental CAPEX or timed programme CAPEX.

## Canonical and closure state

`registry/dso_service_area_membership_crosswalk.csv` remains header-only.

The following national blockers remain active:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

B10 remains `IN_PROGRESS` and readiness remains **15%**.

## Historical lineage

- P20: 10 direct OBS MVM Démász whole-settlement memberships.
- P35: 30 additional DER whole-settlement memberships.
- P45: remaining 216 DER whole-settlement memberships.

P45 closes the **current MVM Démász whole-settlement population only**. The 20 partial-settlement usage-location cases remain explicit open evidence obligations.
