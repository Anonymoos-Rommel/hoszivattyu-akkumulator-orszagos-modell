# B09 – bounded physical supply and adequacy ledger

B09-P1 consumes canonical B08 AC/grid-side net load and an explicit delivered
generation panel. The only physical identity is:

`residual_demand_kw = b08_net_grid_load_kw - delivered_generation_kw`

`unserved_or_residual_load_kw = max(residual_demand_kw, 0)` and
`surplus_supply_kw = max(-residual_demand_kw, 0)`. Energy is derived only as
`kW * timestep_hours`.

The output is bounded and truth-aware. REAL arithmetic is DER, SCN remains SCN,
and Q propagates fail-closed. Every declared `(component, region, timestamp)`
generation cell is explicit; zero generation is a real zero record and missing
generation is an error. Time is timezone-aware UTC and the generation boundary
is `GENERATION_AC`.

## B09-P2 observed-generation evidence contract

`observed_generation_contract.py` adds a source-native ENTSO-E intake contract
for **Actual Generation per Production Type / Aggregated Generation per Type
[16.1.B&C]** at the Hungarian ENTSO-E control-area / bidding-zone grain.

The selected source contract is A75/A16 with A08 resource-type aggregation,
Hungarian EIC `10YHU-MAVIR----U`, source-native Bxx production types, explicit
PT15M/PT30M/PT60M intervals and MW quantities. ENTSO-E permits A01 production
and A93/A94 wind/solar business types for this article. Production and
consumption directions remain distinct: consumption series are excluded and are
never negated into generation.

A source-native value can become `OBS` only after exact source identity, request
query, period, payload SHA-256, acquisition timestamp and explicit
`REUSE_CLEARED` gates pass. Direct object construction cannot mint OBS. The
directly verified Detailed Data Descriptions v3r4 state that actual aggregated
net generation is computed from available instantaneous values and that
unknown output, including small-scale generation without real-time measurement
devices, may be estimated. The runtime therefore preserves the explicit
source-semantic caveat `ENTSOE_PUBLISHED_ACTUAL_MAY_INCLUDE_PROVIDER_ESTIMATES`
instead of claiming meter-only evidence. ENTSO-E's current MoP page identifies
v3.5 as the latest revision context, but this slice does not relabel the
directly verified v3r4 16.1.B&C DDD text as v3.5.

The official machine/API and product references are registered in
`registry/sources.csv`: the Generation and Load Process Implementation Guide
version 0.3 draft, the current v3.5 MoP package, and the platform's Actual
Generation per Production Type view. A separate stable FAQ authority was not
established; the estimate caveat is sourced from the DDD itself.

The existing B09 adequacy engine consumes kW. Therefore the source-native MW
record enters B09 only through explicit dimensional conversion:

`delivered_generation_kw = source_power_mw * 1000`

That handoff is `DER` when the source-native row is OBS; Q remains Q. It also
requires an explicit expected production-type acquisition manifest and a
complete component/timestamp panel. Missing production types or timestamps are
never interpreted as zero.

No ENTSO-E numeric raw payload is committed. The official free-reuse list last
modified **2023-10-18** does not list Actual Generation per Production Type/A75.
This omission is not treated as a prohibition; A75 raw-response redistribution
clearance is simply not established, so acquisition-specific reuse remains Q.
The evidence contract does not create county or DSO generation,
regional allocation, national scaling, storage/dispatch authority or B10 network
headroom/reinforcement authority. Q-B09-001 therefore remains OPEN but is
partially bounded; Q-B09-002 is unchanged.

This module does not dispatch B07 batteries, B08 flexibility, system storage or
generation; it makes no tariff, market, reserve, curtailment, headroom,
reinforcement, CAPEX, national-scaling or monetizable-system-value claim.
`BOUNDED_SCOPE_TOTAL` is a B09-derived bounded sum, never a national result.
B08 `scope_total_rows` are summary inputs and are rejected by B09.

## Qualified P5/P6/P7 GUI generation reference

`gui_generation_reference.py` verifies and streams the six exact existing
source workbooks into the P7 signed-net recovery consumer. It preserves every
numeric A75 cell and recovers only the 4,820 approved missing keys. The source
capacity manifest controls active versus structural n/e types. MAVIR interval
ends, explicit UTC offsets, full-row overlap agreement and source-cell lineage
remain explicit.

The 490,560 records cover the complete native 2025 UTC year. They retain Q-derived
rows within the existing qualified E2/external-only wrapper; the XML/OBS reuse
gate is unchanged. The prior hour needed for the Budapest civil year is absent,
so no complete local-year or winter result is asserted. The full panel and
lineage are materialized only under ignored `data/interim`. See
[checkpoint 017](../../docs/checkpoints/V1_017_B09_GUI_GENERATION_REFERENCE.md).

## V1-020 — Future source references

`future_supply_reference.py` is a separate research/reference-only intake for
exact external ERAA2025 files. It preserves 88 National Trends capacity rows
and 49 amended Cost Based EVA change rows, with explicit source, revision,
scenario, model-stage, year, date-basis and resource-role selection. Future
values remain SCN, not observed or financed capacity. Sparse absence is not zero.

The source-specific model-use qualification remains REVIEW_REQUIRED; no central
future is selected and no existing engine imports this adapter. Reference
materialization does not authorize future hourly generation, storage dispatch,
guaranteed imports, adequacy/LOLE, revenues or national programme effects.
Original sources and normalized rows remain external-only, with ignored-output
guards in the local materializer.

See [checkpoint 020](../../docs/checkpoints/V1_020_B09_FUTURE_SUPPLY_REFERENCE.md)
and the [source manifest](../../registry/b09_future_supply_reference_manifest.json).
B09-D02 stays INTEGRATING; the earlier accepted native 2025 UTC observed-source
handoff and Q-B09-001 qualification are not broadened to these new files.
