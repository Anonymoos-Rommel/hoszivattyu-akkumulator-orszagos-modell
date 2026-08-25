# B07 – Háztartási akkumulátor és VPP

## P1 scope

B07-P1 kizárólag a háztartási akkumulátor fizikai állapotátmenetét és a
fizikai rugalmassági burkot adja. A motor nem tartalmaz tarifát, H-tarifás
jogi döntést, VPP-piaci ajánlatot, bevételt, CAPEX-et vagy gazdasági dispatch-et.

## Canonical boundary

The command boundary is AC/grid-side power at the battery interface:

* charging: `stored_energy_added = grid_charge_energy * charge_efficiency`;
* discharging: `grid_energy_delivered = energy_removed_from_storage * discharge_efficiency`.

Each one-way efficiency is applied once. `nominal_capacity_kwh` and
`usable_capacity_kwh` remain separate; SOC is bounded by explicit fractional
limits. Power limits are independent from energy capacity, and the timestep is
explicit in hours.

The engine clips requests only against physical limits and reports curtailed
charge or unserved discharge. Simultaneous opposing commands fail closed.

## Interfaces

`compute_household_balance` accepts base household load, B05 electrical heat-
pump load, other load, onsite generation and battery flows. It returns import,
physical export and any export curtailment. Export permission is a separate
`Q`/`POL`/`SCN` status and is never converted into a tariff result.

`make_b08_handoff` exposes the minimal physical fields for B08:
`net_grid_import_kw`, `net_grid_export_kw`, `battery_charge_kw`,
`battery_discharge_kw`, `physical_up_flex_kw`, `physical_down_flex_kw` and
`soc_fraction`.

## EU-first product evidence

The bounded evidence pack contains German-manufactured or Germany-made
manufacturer claims for VARTA pulse neo and sonnenBatterie 10 performance.
European brand, EU sales or an EU office is not treated as proof of cell origin
or supply-chain independence; those unresolved boundaries remain `Q`. No raw
manual or copyrighted table is stored in the repository.

## Product-specific efficiency boundary (B07-P2)

The product registry keeps direction-specific fields separate from the legacy
single efficiency field:

* VARTA pulse neo 6: the `97.8%` observation is battery-only (`BATTERY_ONLY`),
  not an AC/grid charge or discharge value. The HTW report also distinguishes
  AC-system performance from AC2BAT and BAT2AC measurement curves. Charge,
  discharge and round-trip product values therefore remain `Q`.
* sonnenBatterie 10 performance: sonnen's `75–80%` figure is a practical
  whole-system example, not an exact product/direction value. Charge,
  discharge, round-trip and the precise AC/grid boundary remain `Q`.

No square-root split, direction symmetry, hidden inverter multiplication or
round-trip substitution is allowed. Runtime continues to use explicit SCN
one-way inputs only until product-specific AC/grid evidence is available.

## Readiness boundaries

P1 can close the physical SOC engine, power/energy limits, household balance
and B08 physical handoff for explicit SCN/product fixtures. Runtime
degradation, H-tariff legality, VPP eligibility and market availability remain
unresolved.

Decision snapshot:

* `BATTERY_PHYSICAL_CONTRACT_READY = YES`
* `SOC_ENGINE_READY = YES`
* `PRODUCT_EVIDENCE_READY = YES` for the bounded EU-first evidence pack; product-specific one-way efficiency and cell origin remain Q
* `DEGRADATION_RUNTIME_MODEL_READY = NO`
* `PHYSICAL_FLEXIBILITY_READY = YES`
* `H_TARIFF_BATTERY_INTERFACE_READY = NO`
* `VPP_MARKET_INTERFACE_READY = NO`
* `B08_PHYSICAL_HANDOFF_READY = YES`
* `B07_READY_FOR_NEXT_SLICE = YES`

The next highest-value blocker is a combined B04/B07 evidence slice: prove the
H-tariff meter/battery/export boundary and obtain product-specific AC/DC
one-way efficiency plus cell/supply-chain origin evidence without importing a
foreign-dependence assumption.
