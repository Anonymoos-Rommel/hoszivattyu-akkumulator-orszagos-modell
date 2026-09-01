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
`REUSE_CLEARED` gates pass. Direct object construction cannot mint OBS. ENTSO-E
also states that published actual-generation values may contain provider
estimates when measurements are unavailable, so the runtime preserves that
source-semantic caveat instead of claiming meter-only evidence.

The existing B09 adequacy engine consumes kW. Therefore the source-native MW
record enters B09 only through explicit dimensional conversion:

`delivered_generation_kw = source_power_mw * 1000`

That handoff is `DER` when the source-native row is OBS; Q remains Q. It also
requires an explicit expected production-type acquisition manifest and a
complete component/timestamp panel. Missing production types or timestamps are
never interpreted as zero.

No ENTSO-E numeric raw payload is committed. The inspected reuse authority does
not establish A75 raw-response redistribution clearance, so acquisition-specific
reuse remains Q. The evidence contract does not create county or DSO generation,
regional allocation, national scaling, storage/dispatch authority or B10 network
headroom/reinforcement authority. Q-B09-001 therefore remains OPEN but is
partially bounded; Q-B09-002 is unchanged.

This module does not dispatch B07 batteries, B08 flexibility, system storage or
generation; it makes no tariff, market, reserve, curtailment, headroom,
reinforcement, CAPEX, national-scaling or monetizable-system-value claim.
`BOUNDED_SCOPE_TOTAL` is a B09-derived bounded sum, never a national result.
B08 `scope_total_rows` are summary inputs and are rejected by B09.
