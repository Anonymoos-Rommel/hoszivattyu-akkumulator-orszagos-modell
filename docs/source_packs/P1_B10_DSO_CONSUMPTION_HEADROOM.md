# B10-P1 — DSO consumption-side headroom evidence pack

Retrieval/audit date: 2026-09-01
Repository base: `f199678578493732d969cfe5074d41a32a0c172b`

## Decision

The first B10 physical-network slice is bounded to **MVM Démász Áramhálózati Kft.** official
consumption-purpose substation free-capacity publications. This is sufficient to
create a fail-closed source contract without claiming national DSO coverage.

The selected source pair is:

1. MVM DEMASZ — consumption-purpose free capacities:
   `https://mvmhalozat.hu/attachments/41914`
2. MVM DEMASZ — method/interpretation for the published free capacities:
   `https://mvmhalozat.hu/attachments/41913`

The publication exposes, by station / source-native station code / voltage level,
current and five-year planning-horizon fields including N-1 transformer capacity,
winter-evening consumption peak and theoretical consumption-side free capacity.

The publication header identifies the station-code field as a four-letter `AÁ`
identifier, and the source rows use four-letter codes such as `BAJA`, `BAJD` and
`BCSA`. The runtime therefore validates exactly four Unicode letters and preserves
the source-native code without case normalization; it does not assert a broader
alphanumeric taxonomy.

The official MVM company information page
(`https://www.mvmhalozat.hu/aram/oldalak/430`) identifies the publisher as
exactly `MVM Démász Áramhálózati Kft.`. The MVM site impressum
(`https://mvmhalozat.hu/aram/oldalak/2785`) states that the site's content is
copyrighted and republication requires prior written permission. This was not
treated as redistribution clearance for the numeric PDF, so raw PDFs remain
external.

## Source semantics

The official methodology describes consumption-side current free capacity as a
network calculation based on N-1 transformer capacity and measured maximum
winter-evening load. The five-year value uses the approved network-development
planning horizon and forecast/load-development assumptions.

These values are **indicative network capacity information**, not an individual
connection decision. The actual connection conditions for a concrete connection
request remain subject to the distribution-system operator's individual technical
assessment / MGT process.

Therefore the canonical semantic marker is:

`PUBLISHED_INDICATIVE_DSO_ESTIMATE_NOT_CONNECTION_AUTHORITY`

and every runtime row preserves:

`connection_authority = MGT_REQUIRED`.

## Evidence/truth decision

B10-P1 deliberately does not parse or redistribute the official PDF directly.
The runtime parser accepts a normalized external TSV acquisition artifact with an
exact schema and checksum. Because this TSV is a transformation/transcription of
the official publication, the normalized row is **never OBS**.

A row can become `DER` only when all of the following are present:

- canonical MVM DEMASZ data source identity;
- canonical methodology source identity;
- timezone-aware acquisition timestamp;
- explicit reuse decision `REUSE_CLEARED`;
- source-PDF SHA-256;
- exact normalized-text SHA-256;
- explicit `VERIFIED_AGAINST_SOURCE` extraction verification;
- complete required station numeric fields.

Otherwise the row remains `Q`. Missing is not zero.

No raw PDF, raw restricted payload or manually copied national numeric dataset is
committed by this slice.

## Canonical grain

The supported grain is only:

`DSO_SUBSTATION = MVM_DEMASZ:<station_code>:<voltage_kV>KV`

with separate:

- `CURRENT`
- `FIVE_YEAR`

records.

No county, settlement, ENTSO-E control-area or household allocation is inferred.
Substation free capacities are not declared additive. B10-P1 explicitly carries
`aggregation_authority = NONE_NON_ADDITIVE`.

## B08/B09 handoff boundary

B08-P2 and B09-P2 currently provide partial evidence at Hungarian ENTSO-E
control-area / bidding-zone grain. That grain does **not** match B10-P1's
DSO-substation grain.

Consequently B10-P1 may assess incremental demand only when an upstream contract
already supplies exactly the same `DSO_SUBSTATION` region key. It cannot create
the missing spatial crosswalk.

This preserves Q-B01-002 and prevents:

- control-area-to-substation disaggregation;
- county-to-DSO proxy allocation;
- household-count scaling;
- population/consumption-share scaling;
- false regional headroom claims.

## Baseline/incremental infrastructure boundary

The v1.2 methodology requires separate baseline and program-incremental
infrastructure accounting. B10-P1 does not yet populate either
`baseline_infrastructure.csv` or `incremental_capex_attribution.csv` because the
selected source pair is headroom evidence, not project-cost or contractual-status
evidence.

Q-B10-001 and Q-B10-002 therefore remain OPEN.

## Additional source discovery, not yet canonical runtime authority

The 2026-09-01 audit also identified an OPUS TITASZ public free-capacity
publication with current and five-year consumption-side information. It is useful
for later national DSO coverage, but it is intentionally not folded into P1's
runtime parser before a separate source-schema adapter and provenance contract are
reviewed.

## P1 exclusions

No claim is made for:

- national DSO coverage;
- national or DSO-total headroom;
- county/DSO crosswalk;
- medium/low-voltage feeder constraints;
- power-flow or voltage-quality feasibility;
- reinforcement cost;
- baseline-project commitment status;
- incremental program CAPEX;
- connection approval;
- B10 completion.
