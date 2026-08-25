# B09-P1 – bounded physical supply and adequacy ledger

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

This slice does not dispatch B07 batteries, B08 flexibility, system storage or
generation; it makes no tariff, market, reserve, curtailment, headroom,
reinforcement, CAPEX, national-scaling or monetizable-system-value claim.
`BOUNDED_SCOPE_TOTAL` is a B09-derived bounded sum, never a national result.
B08 `scope_total_rows` are summary inputs and are rejected by B09.
