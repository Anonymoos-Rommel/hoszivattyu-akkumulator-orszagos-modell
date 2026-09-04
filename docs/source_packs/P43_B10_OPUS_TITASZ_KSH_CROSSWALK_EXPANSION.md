# B10-P43 — OPUS TITÁSZ / KSH service-area crosswalk expansion IV

## Purpose

P43 is an evidence/data slice only. It extends the bounded OPUS TITÁSZ service-area membership materialization from the current official M1 territorial-jurisdiction attachment without changing any B10 semantic gate.

The core boundary remains:

`BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK`

## Authorities

### OPUS TITÁSZ current M1

Source ID: `SRC-B10-OPUS-TITASZ-M1-2026`

The current 2026 OPUS TITÁSZ business-rule attachment publishes `AZ OPUS TITÁSZ ZRT. TERÜLETI ILLETÉKESSÉGE` as a serialised settlement list. P43 materializes exactly serials **131–170**.

### KSH settlement identity

Source ID: `SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`

The official KSH 2019 gazetteer publishes the five-digit `településazonosító törzsszám`. P43 joins the exact OPUS M1 settlement names to their direct official KSH identifiers.

No fuzzy matching, accent normalization, approximate matching, or identity override is introduced in P43.

## Exact P43 materialization

| M1 serial | KSH code | Settlement |
|---:|:---:|---|
| 131 | 19992 | Kemecse |
| 132 | 17145 | Kenderes |
| 133 | 07418 | Kengyel |
| 134 | 12618 | Kertészsziget |
| 135 | 28431 | Kék |
| 136 | 14359 | Kékcse |
| 137 | 32869 | Kérsemjén |
| 138 | 19813 | Kétpó |
| 139 | 19424 | Kisar |
| 140 | 08509 | Kishódos |
| 141 | 28477 | Kisléta |
| 142 | 15477 | Kismarja |
| 143 | 16036 | Kisnamény |
| 144 | 29300 | Kispalád |
| 145 | 09751 | Kisszekeres |
| 146 | 25919 | Kisújszállás |
| 147 | 12672 | Kisvarsány |
| 148 | 09265 | Kisvárda |
| 149 | 07445 | Kocsord |
| 150 | 17455 | Kokad |
| 151 | 02167 | Komádi |
| 152 | 22336 | Komlódtótfalu |
| 153 | 27146 | Komoró |
| 154 | 25964 | Konyár |
| 155 | 23728 | Kótaj |
| 156 | 16665 | Kölcse |
| 157 | 23612 | Kömörő |
| 158 | 10764 | Körösnagyharsány |
| 159 | 31130 | Körösszakál |
| 160 | 08943 | Körösszegapáti |
| 161 | 32975 | Kőröstetétlen |
| 162 | 30164 | Körösújfalu |
| 163 | 11235 | Kőtelek |
| 164 | 05254 | Kuncsorba |
| 165 | 22567 | Kunhegyes |
| 166 | 23171 | Kunmadaras |
| 167 | 32504 | Kunszentmárton |
| 168 | 21290 | Laskod |
| 169 | 30979 | Levelek |
| 170 | 05768 | Létavértes |

P43 therefore adds exactly **40 whole-settlement memberships** and expands the bounded OPUS TITÁSZ materialization from 130 to **170 materialized rows**.

The P43 boundary ends at M1 serial **170, Létavértes**. M1 serial **171, Lónya** is deliberately not materialized by P43.

## Truth status

Every new P43 row is:

- `coverage_scope = WHOLE_SETTLEMENT`
- `usage_location_requirement = NONE`
- `evidence_status = OBS`
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`
- bound to both the current OPUS M1 authority and the official KSH five-digit settlement identifier authority.

This is direct observed source binding at the service-area membership grain only.

## Fail-closed semantic boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

P43 records only bounded public facts needed for the model contract. It does not republish the source document or claim a reconstructed complete source database.

## What P43 does not prove

P43 does **not** claim:

- complete OPUS TITÁSZ settlement inventory materialization;
- complete national KSH-to-DSO membership coverage;
- resolution of partial-settlement or usage-location membership;
- exact programme entity-to-node mapping;
- exact DSO node identity or topology;
- headroom sufficiency;
- limiting-node status;
- reinforcement need or reinforcement cost;
- programme-incremental CAPEX.

Service-area membership remains strictly upstream of node, headroom, network-study, reinforcement and CAPEX authority.

## Canonical and closure state

`registry/dso_service_area_membership_crosswalk.csv` remains header-only.

The following blockers remain active:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

P43 does not change module status. B10 remains `IN_PROGRESS` and readiness remains **15%**.

## Historical lineage

- P20: OPUS M1 serials 1–10
- P40: serials 11–50
- P41: serials 51–90
- P42: serials 91–130
- P43: serials 131–170

The resulting 170-row OPUS tranche is still a bounded partial materialization, not a complete operator crosswalk.
