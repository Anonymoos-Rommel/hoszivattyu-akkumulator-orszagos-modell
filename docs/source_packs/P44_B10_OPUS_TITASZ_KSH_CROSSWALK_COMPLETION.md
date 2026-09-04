# B10-P44 — OPUS TITÁSZ / KSH service-area crosswalk completion

## Purpose

P44 is an evidence/data completion slice only. It completes the current OPUS TITÁSZ M1 settlement-list materialization without changing any B10 node, headroom, reinforcement, cost, timing, or CAPEX gate.

The new boundary is:

`COMPLETE OPUS OPERATOR M1 != COMPLETE NATIONAL CROSSWALK`

## Authorities

### OPUS TITÁSZ current M1

Source ID: `SRC-B10-OPUS-TITASZ-M1-2026`

The current 2026 OPUS TITÁSZ business-rule attachment publishes `AZ OPUS TITÁSZ ZRT. TERÜLETI ILLETÉKESSÉGE` as a serialised settlement list. The list terminates at serial **395, Zsurk**.

P20 and P40–P43 already materialized serials 1–170. P44 materializes the complete remaining interval, serials **171–395**, beginning at serial **171, Lónya** and ending at serial **395, Zsurk**.

### KSH settlement identity

Source ID: `SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`

The official KSH 2019 gazetteer publishes the five-digit `településazonosító törzsszám`. Every one of the 225 P44 settlement names has a direct exact-name KSH identity in that authority.

No fuzzy matching, accent normalization, approximate matching, or identity override is introduced by P44.

## Exact completion result

P44 adds exactly **225 whole-settlement memberships**. Together with the 170 historical OPUS rows, the current OPUS TITÁSZ M1 settlement population is therefore exactly **395 materialized rows**.

For append-only auditability, P44 does not rewrite the historical evolving tranche. The complete OPUS operator materialization is the explicit union of the **historical tranche + P44 completion tranche**:

- `registry/dso_service_area_membership_crosswalk_tranche.csv` — historical P20/P40/P41/P42/P43 OPUS rows 1–170 plus the other bounded operator tranches;
- `registry/dso_service_area_membership_crosswalk_opus_p44.csv` — exact P44 OPUS rows 171–395 only.

All 225 new records are independently frozen in `tests/test_b10_p44_opus_titasz_ksh_crosswalk_completion.py` as exact KSH-code/name pairs. The historical and completion registry surfaces together are the materialized operator data surface; this source pack records the evidence contract and completion boundary rather than republishing the operator or KSH source documents.

Every new P44 row is:

- `coverage_scope = WHOLE_SETTLEMENT`
- `usage_location_requirement = NONE`
- `evidence_status = OBS`
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`
- bound to both the current OPUS M1 authority and the official KSH five-digit settlement identifier authority.

The OPUS source-registry row therefore moves from historical partial-tranche state to `COMPLETE_OPERATOR_M1_MATERIALIZED`.

## Fail-closed semantic boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`COMPLETE OPUS OPERATOR M1 != COMPLETE NATIONAL CROSSWALK`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

Complete materialization of one operator's current M1 settlement list does not prove that the other five DSO service-area populations are complete, that partial-settlement boundaries are resolved, or that any household/programme entity is mapped to an exact electrical node.

## What P44 does not prove

P44 does **not** claim:

- complete national KSH-to-DSO membership coverage;
- resolution of partial-settlement or usage-location membership;
- exact programme entity-to-node mapping;
- exact DSO node identity or complete topology;
- headroom sufficiency;
- limiting-node status;
- reinforcement need or reinforcement cost;
- total reinforcement project cost;
- customer connection charge;
- programme-incremental CAPEX or timed programme CAPEX.

Service-area membership remains strictly upstream of node, headroom, network-study, reinforcement and CAPEX authority.

## Canonical and closure state

`registry/dso_service_area_membership_crosswalk.csv` remains header-only.

The following national blockers remain active:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

P44 does not change module status. B10 remains `IN_PROGRESS` and readiness remains **15%**.

## Historical lineage

- P20: OPUS M1 serials 1–10
- P40: serials 11–50
- P41: serials 51–90
- P42: serials 91–130
- P43: serials 131–170
- P44: serials 171–395

P44 closes only the current OPUS TITÁSZ operator-level M1 settlement-list materialization. National service-area completion remains fail-closed.
