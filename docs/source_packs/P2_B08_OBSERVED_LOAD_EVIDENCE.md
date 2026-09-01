# B08-P2 – Hungarian observed load evidence audit

Audit date: **2026-09-01**
Repository base: `a81b6dcd7122b2bd5b671eddd0f044c2d74dc199`

## Evidence verdict

| Candidate | Verdict | Supported grain | Why |
|---|---|---|---|
| ENTSO-E Transparency Platform Actual Total Load [6.1.A] | **Selected metadata contract** | Hungarian control area / bidding zone `10YHU-MAVIR----U` | A65/A16/A04 is explicitly realised actual total load; official API and MTU semantics are documented. Numeric raw data remain external because primary-owner reuse must be checked. |
| MAVIR RTDW public publication | **Rejected for canonical numeric intake in this slice** | Not established by the inspected interface | Public UI has date, resolution, format and export controls, but no stable machine-readable schema, documented API path, or clear numeric-data reuse terms were established. |
| ENTSO-E Power Statistics monthly/hourly load | **Context only** | Country aggregate | Official downloadable historical/hourly statistics are country aggregated and useful as a cross-check, but the page does not establish the same source-native MTU/API provenance needed for the selected real intake. |

## Selected source contract

Publisher: **ENTSO-E**, with source-native data submitted by the TSO.
Product: **Actual Total Load [6.1.A]**.
API: `https://web-api.tp.entsoe.eu/api` with:

```text
documentType=A65
processType=A16
businessType=A04
outBiddingZone_Domain=10YHU-MAVIR----U
periodStart=<yyyyMMddHHmm UTC>
periodEnd=<yyyyMMddHHmm UTC>
```

The endpoint requires a registered Transparency Platform user and token. The
response is an ENTSO-E GL market document. The official data description says
that actual total load is published per bidding zone and market time unit,
uses the average of real-time load values, includes losses, and follows the
published net-generation/exchange/storage definition. It also says that an
unknown net-generation output may be estimated; B08 therefore consumes only
the published source-native A65 series and does not reconstruct its components.

The official implementation material supports `PT15M`, `PT30M`, and `PT60M`.
Records are interval-start records with an explicit interval end derived from
the accepted resolution. Source offsets are retained in provenance and the
canonical internal timestamp is UTC. Duplicate canonical `(series_id,
timestamp_utc)` keys fail closed. No implicit one-hour assumption exists.

## Truth and spatial rules

- `OBS`: only a source-native realised A65/A16/A04 quantity with the required
  provenance.
- `DER`: only explicit arithmetic such as `observed_load_mw * timestep_hours`
  producing MWh.
- `Q`: missing quantity, unresolved reuse permission, missing checksum, or any
  unsupported mapping. Missing is not zero.
- `SCN`: repository-created mechanics fixtures remain SCN and cannot be
  promoted by the parser.
- The only supported real spatial identity in this slice is
  `HUNGARY_CONTROL_AREA` / `ENTSOE_CONTROL_AREA`.
- A national/control-area series cannot validate regional B08 output. No DSO
  or county series is inferred, and no county↔DSO crosswalk is assumed.

## Licence and provenance decision

No raw ENTSO-E response is committed. The Transparency Platform terms require
source attribution and place responsibility on the data user to check the
current free-reuse list and, where necessary, obtain primary-owner agreement.
The inspected list does not establish free reuse for Actual Total Load. Each
future acquisition must record the exact request URL, retrieval timestamp,
source revision, response SHA-256, source identifiers, and the then-current
reuse decision. Until that record exists, the numeric series remains external
and its repository evidence status remains Q.

## Boundary decisions

Q-B08-001 remains **OPEN, partially bounded**: source product, API fields,
source semantics, control-area grain, interval options, UTC rule and external
raw-data policy are now canonical; real snapshot checksum/reuse clearance and
regional evidence remain open. Q-B01-002 remains open. Q-B08-002 remains
**OPEN/Q**: no season, winter window, peak calendar or 1-in-N policy was
justified by this source audit.

No change is made to B09 generation/dispatch/storage authority or B10
headroom/reinforcement/CAPEX authority. Overall B08 readiness remains 45%:
this slice adds partial readiness rows for observed evidence, time contract and
spatial grain, but does not claim a real regional runtime or national scaling.
