# B08/B09-P4 — ENTSO-E numeric acquisition access gate

**Date:** 2026-09-27  
**Canonical base:** `d1e2e887629e6174107aed24ca0120a8ea9c2994`

## Purpose

This slice attacks the current E3 model blockers:

- `Q-B08-001` — no canonical Hungarian observed load panel;
- `Q-B09-001` — no canonical Hungarian observed generation panel.

It does not create a synthetic substitute and it does not change either blocker to E2.

## Result

The data products exist and the repository already has canonical parsers for both source-native XML products.

The remaining blocker is now narrowed to:

`ENTSOE_REGISTERED_EXPORT_OR_API_TOKEN_REQUIRED`

This is an **access/acquisition blocker**, not a data-existence or parser-design blocker.

## 1. B08 target

Dataset: **Actual Total Load [6.1.A]**

Canonical API semantics already frozen by B08-P2:

- `documentType=A65`
- `processType=A16`
- `businessType=A04`
- `outBiddingZone_Domain=10YHU-MAVIR----U`

Existing parser:

`modules/B08/observed_load_contract.py`

No new parser is required.

## 2. B09 target

Dataset: **Actual Generation per Production Type [16.1.B&C]**

Canonical API semantics already frozen by B09-P2:

- `documentType=A75`
- `processType=A16`
- `in_Domain=10YHU-MAVIR----U`
- source-native `A08` resource-type aggregation;
- source-native `Bxx` production-type codes;
- source-native MW.

Existing parser:

`modules/B09/observed_generation_contract.py`

No new parser is required.

## 3. Fresh current access audit

Fresh official platform verification on 2026-09-27 establishes:

1. The Transparency Platform remains publicly viewable and identifies itself as providing free continuous access to electricity-market data.
2. The platform states that **registered users can download data tables and graphs**.
3. The Actual Generation per Production Type data view explicitly shows **"Please log in to export data"**.
4. Current official API-token management guidance states that a user who does not yet have the Web API Security Token field must:
   - register on the Transparency Platform;
   - request RESTful API access from ENTSO-E;
   - after enablement, generate/use the security token.

Therefore:

`PUBLIC_DATA_VIEW != BULK_EXPORT_ACCESS`

and:

`REGISTERED_PLATFORM_ACCOUNT != WEB_API_ACCESS_ENABLED`

and:

`WEB_API_TOKEN_REQUIRED != TOKEN_MAY_BE_COMMITTED`

## 4. Secret boundary

A future token must be supplied only through an external/local secret mechanism such as:

`ENTSOE_SECURITY_TOKEN`

The token must never be placed in:

- canonical request URLs stored in provenance;
- source registries;
- commits;
- CI logs;
- public issue/PR text;
- raw evidence manifests.

The existing B08/B09 parsers deliberately validate **non-secret canonical request URLs**.

## 5. Canonical acquisition period

The first real baseline should use the latest completed common calendar year:

**2025-01-01 00:00 Europe/Budapest -> 2026-01-01 00:00 Europe/Budapest**

UTC request coverage:

**2024-12-31T23:00Z -> 2025-12-31T23:00Z**

This aligns the real panel to the existing B08 seasonal/calendar reporting contract rather than silently treating UTC midnight as the Hungarian civil-year boundary.

## 6. API request templates

B08 non-secret canonical request:

`https://web-api.tp.entsoe.eu/api?documentType=A65&processType=A16&businessType=A04&outBiddingZone_Domain=10YHU-MAVIR----U&periodStart=202412312300&periodEnd=202512312300`

B09 non-secret canonical request:

`https://web-api.tp.entsoe.eu/api?documentType=A75&processType=A16&in_Domain=10YHU-MAVIR----U&periodStart=202412312300&periodEnd=202512312300`

The security token is supplied separately and is not part of the canonical provenance URL.

The official API implementation guide states that public HTTPS Web API queries can generally cover up to one year, subject to article-specific implementation constraints.

## 7. Raw-data and reuse boundary

Raw A65/A75 payloads remain:

`EXTERNAL_ONLY`

unless explicit reuse clearance is established.

The current project evidence already records that the inspected 2023 free-reuse list does not establish A65/A75 free-reuse clearance. This omission is not interpreted as a prohibition.

Acquisition must preserve:

- exact payload bytes;
- SHA-256;
- retrieval time;
- source revision or `NOT_PROVIDED_BY_SOURCE`;
- exact non-secret request URL;
- model-use/reuse decision.

## 8. Admission after access

### B08

On acquisition:

1. hash exact UTF-8 XML payload;
2. construct canonical provenance;
3. run `parse_entsoe_actual_total_load`;
4. verify no duplicate source-series timestamps;
5. retain source-native MTU;
6. materialize the national/control-area baseline.

### B09

On acquisition:

1. hash exact UTF-8 XML payload;
2. construct canonical provenance;
3. run `parse_entsoe_actual_generation_per_type`;
4. enumerate source-native Bxx types actually present;
5. establish the expected-production-type manifest separately;
6. never interpret an absent production type as zero;
7. materialize the national/control-area generation panel.

## 9. Blocker state

### Q-B08-001

Remains:

- evidence tier: **E3**
- blocker class: **MODEL_BLOCKER**
- model blocker: **yes**

Exact residual:

`ENTSOE_REGISTERED_EXPORT_OR_API_TOKEN_REQUIRED -> REAL_A65_PAYLOAD_REQUIRED -> MODEL_USE_REUSE_DECISION_REQUIRED`

### Q-B09-001

Remains:

- evidence tier: **E3**
- blocker class: **MODEL_BLOCKER**
- model blocker: **yes**

Exact residual:

`ENTSOE_REGISTERED_EXPORT_OR_API_TOKEN_REQUIRED -> REAL_A75_PAYLOAD_REQUIRED -> EXPECTED_PRODUCTION_TYPE_MANIFEST_REQUIRED -> MODEL_USE_REUSE_DECISION_REQUIRED`

## 10. Readiness

No numeric panel has been acquired.

No readiness percentage is increased.

## Official references

- ENTSO-E Transparency Platform:
  https://transparency.entsoe.eu/
- ENTSO-E API token management:
  https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2FAPI-Token-Management.pdf
- ENTSO-E REST API implementation guide:
  https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/RestfulAPI_IG.pdf
- Actual Generation per Production Type:
  https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=
