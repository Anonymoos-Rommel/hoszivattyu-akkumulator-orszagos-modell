# B08-P2 – Hungarian observed load evidence audit

Audit date: **2026-09-01**
Repository base: `a81b6dcd7122b2bd5b671eddd0f044c2d74dc199`

## Evidence verdict

| Candidate | Verdict | Supported grain | Why |
|---|---|---|---|
| ENTSO-E Transparency Platform Actual Total Load [6.1.A] | **Selected metadata contract** | Hungarian control area / bidding zone `10YHU-MAVIR----U` | A65/A16/A04 is explicitly realised actual total load; official API and MTU semantics are documented. Numeric raw data remain external because the inspected current free-reuse authority does not establish A65 reuse. |
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

No raw ENTSO-E response is committed. The inspected official authority is the
**ENTSO-E List of Data Available for Free Re-use, last modified 2023-10-18**:
`https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fterms+and+conditions%2F231018_List_of_Data_available_for_reuse.pdf`.
It expressly lists day/week/month/year-ahead total-load forecasts and other
specified items under CC BY 4.0, but does not list Actual Total Load/A65. The
result is **not** an inference that omission is a legal prohibition; A65 free
reuse is simply not established by this inspected list. The associated 2023
Terms URL is recorded in `registry/sources.csv`.

Each future acquisition must record the exact non-secret request URL/query,
timezone-aware retrieval timestamp, source revision or
`NOT_PROVIDED_BY_SOURCE`, source identifiers, response SHA-256 of the exact
UTF-8 payload bytes, and one of the finite reuse decisions
`REUSE_CLEARED`, `EXTERNAL_ONLY_REUSE_UNRESOLVED`, `REUSE_RESTRICTED`, or
`REUSE_UNKNOWN`. Only `REUSE_CLEARED` can permit `OBS`; repository/raw storage
policy alone cannot clear reuse. Until that record exists, the numeric series
remains external and its repository evidence status remains Q.

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
