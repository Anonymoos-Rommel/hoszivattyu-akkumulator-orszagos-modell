# B08 – bounded electrical system-load aggregation

B08 aggregates explicit AC/grid-side household boundary records. Its canonical
identity is `net_grid_load_kw = gross_grid_import_kw - gross_grid_export_kw`,
with energy derived as power times the explicit timestep. Import/export and
physical up/down flexibility remain separate; flexibility is not dispatch.

The B05 heat-pump load is already included in the B07 household balance and is
handed to B08 once through `B08PhysicalHandoff`. B01 state is carried only as
trace metadata. B02 eligibility/readiness, legal export, tariffs, B09 dispatch,
B10 headroom/reinforcement, seasonal peaks, population scaling, and national
claims remain outside this bounded contract and are Q/partial.

The supplied fixture is SCN-only, dataset-licensed, two-region and explicit.
`BOUNDED_SCOPE_TOTAL` means the sum of the explicit bounded records, not a
national estimate. Every source entity must be present at every run timestamp;
missing values, duplicate keys, alternate boundaries, mixed region schemes,
mixed truth contexts, negative physical inputs, naive timestamps, and
inconsistent timesteps fail closed. Timestamps are timezone-aware and
canonicalized to UTC; each timestamp denotes the start of an explicit interval
whose duration is `timestep_hours`.

## B08-P2 observed-load evidence contract

The selected source candidate is ENTSO-E Transparency Platform **Actual Total
Load [6.1.A]**, queried as `documentType=A65`, `processType=A16`,
`businessType=A04`, and `outBiddingZone_Domain=10YHU-MAVIR----U`. The source
definition is the source-native actual total load per market time unit. It is
not a household meter panel and it is not a county or DSO series.

The machine-readable acquisition path is the registered-user REST API at
`https://web-api.tp.entsoe.eu/api`. The contract preserves the source-native
`PT15M`, `PT30M`, or `PT60M` resolution, requires timezone-aware period
timestamps, records interval start and end, and normalizes timestamps to UTC
without resampling. Fall-back duplicate local wall-clock labels are retained
as distinct offset-bearing instants; spring-forward gaps are not filled.

The parser in `observed_load_contract.py` is metadata-only in this repository:
no ENTSO-E raw response is committed. A source-native numeric value may be
`OBS` only when all runtime gates pass: realised A65/A16/A04, Hungarian EIC,
explicit numeric quantity, supported resolution, timezone-aware source and
acquisition timestamps, complete source provenance, exact UTF-8 payload
SHA-256 match, and the explicit finite reuse decision `REUSE_CLEARED`.
`EXTERNAL_ONLY_REUSE_UNRESOLVED`, `REUSE_RESTRICTED`, `REUSE_UNKNOWN`, a
missing checksum, or repository storage permission alone keep the value `Q`.
`MW` remains power; `MWh` is a separate `DER` value computed only as `MW *
explicit timestep_hours`. Missing quantity is `Q`, never zero. The source's
control-area grain is retained as `HUNGARY_CONTROL_AREA` with
`ENTSOE_CONTROL_AREA`; no county/DSO relabelling or proxy split is permitted.
The parser hashes the exact acquired UTF-8 payload text; it never hashes a
reserialized or normalized XML document. Source revision is recorded when
provided, otherwise the explicit marker `NOT_PROVIDED_BY_SOURCE` is required.

MAVIR's public RTDW page exposes interactive date, resolution, format and
export controls, but this audit did not establish a stable machine schema or
clear numeric-data reuse terms. It remains a source lead, not a canonical
numeric input for B08-P2.

The official ENTSO-E free-reuse list last modified **2023-10-18** is recorded
as `SRC-B08-ENTSOE-REUSE-LIST-2023`. It lists free-reuse forecast load items
and other specified data under CC BY 4.0, but it does not list Actual Total
Load/A65. This omission is not treated as a prohibition; it means that free
reuse for an acquired A65 response is not established by the inspected list.
The 2023 ENTSO-E Transparency Terms remain the governing provenance/reuse
context. Consequently, raw responses stay external and the runtime reuse
decision remains unresolved until acquisition-specific clearance is evidenced.

## Qualified P5 GUI load reference

`gui_load_reference.py` implements the later P5 source-specific E2 model-use
admission for the two exact registered 2025/2024 GUI exports. It verifies the
original bytes/hash and source headers, reads actual sheet rows despite stale
XLSX dimensions, and builds the exact 2025 Europe/Budapest civil-year panel.
The output remains DER with explicit E2/external-only provenance. It does not
relax the older XML parser's OBS/reuse gate above.

`tools/materialize_b08_gui_load_reference.py` writes the normalized numeric
panel and its annual/winter receipt only into ignored `data/interim`. Raw XLSX
and complete source series are not published. The historical control-area
baseline is not a programme result or a regional mapping. See
[checkpoint 016](../../docs/checkpoints/V1_016_B08_QUALIFIED_LOAD_REFERENCE.md).

## Dated regional-key handoff

The source-bound DSO key catalogue in
`registry/b08_dated_regional_key_handoff.json` reuses the existing B10 P63
callable and P64 residual accounting. It supplies 3,052 whole-settlement
mappings and one exact partial usage-location mapping from the named
published snapshot, with source lineage and exclusions retained.

The offered scheme is `DSO_SERVICE_AREA`, not a regional split of the
control-area load. The generic `GridBoundaryRecord` region strings do not
validate this mapping. Exact upstream keys and a matching source snapshot
are required; absent or ambiguous keys remain Q/refused and do not acquire
zero load, default membership or a proved residual identity. Tass code 20525
alone cannot establish its named subset. See
[checkpoint 060](../../docs/checkpoints/V1_060_REGIONAL_KEYS_AND_OWNER_POLICY.md)
for the original-task acceptance scope and dated-source limits.
