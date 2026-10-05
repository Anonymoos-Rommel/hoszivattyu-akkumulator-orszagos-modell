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

## V1 tested-reference evidence and coordinate

[SAX2026 source reference](../../docs/checkpoints/V1_013_SAX_SOURCE_AND_COORDINATE.md) adds explicit, bounded converter-point consumers and a [proposed discharge-equivalent coordinate contract](../../docs/methodology/b07_discharge_equivalent_reference_contract.md). It does not fill legacy one-way efficiency fields or alter the existing engine. Source-tested DC capacity/cycle efficiency and separate output-axis converter curves permit a conditional reference route; idle, aging, national applicability and legal gates remain distinct. No new state runtime is included in this checkpoint.


V1-038 adopts the separately named [discharge-equivalent reference](discharge_equivalent_reference.py) with explicit initial/terminal inventory, converter boundaries and cycle-eligibility checks. Its constant tested-product applicability and separately supplied idle-exposure aggregate use E2/PROVISIONAL_BASE; calculated balances are DER. [Validation debt](../../registry/b07_reference_validation_debt.json) preserves the E1 upgrade path. Exact component measurements are not required merely to continue the E2 aggregate model. The existing engine remains unchanged; the idle AC proxy does not invent a DC state transition, a national product choice or a complete annual-system efficiency.


## Source temperature and test conditions (V1-052)

The SAX source controls and genuine source-labelled run/aggregate-idle results now
include `source_conditions`. The 5–35 °C manufacturer operating specification is
separate from the unknown measured laboratory ambient. The published common capacity
protocol retains its 100/50/25% nominal-power levels and six retained cycles; its
Fronius D1 example does not become SAX test wattages. The additional low-load method
also retains its own scope. All existing numerical controls, curves and calculations
are unchanged. Synthetic references receive no source-condition authority.

See the [condition handoff checkpoint](../../docs/checkpoints/V1_052_B07_SOURCE_CONDITIONS.md)
and the [reference contract](../../docs/methodology/b07_discharge_equivalent_reference_contract.md).
The exact report, official data asset and datasheet were recovered against their
existing hashes; originals remain private. Q-B07-003 E2 applicability debt, D02
lifecycle and D03 operating/legal availability remain open. This prepares the original
D01 handoff for whole-slice acceptance review; a real reviewed condition commit must
exist before its acceptance metadata can reference it.

## Supplied shared-use schedules (V1-066)

[`shared_use_schedule_contract.evaluate_shared_use`](shared_use_schedule_contract.py)
audits household and state/aggregator use of one physical battery across two
explicit generation-free schedules. It executes each native B07 engine once per
leg and interval, then reconciles supplied actor allocations and independent
energy, power, duration, budget and service-window rights. Shared-capacity access
and a protected inventory pool are separate modes; neither creates charged energy.

Activation under an existing reservation and agreement-versus-household-only
comparisons have distinct baseline bindings. Raw signed connection response,
physical clipping, actor shortages, recharge and terminal inventory stay visible.
Reference idle keeps the DC path and total-connection response unknown while
preserving qualified active-converter component arithmetic and a separately
supplied E2 aggregate AC debit. Contract availability respects the unsplit retained
inventory floor; missing actor rows cannot erase established local violations.
Known-use lower bounds retain whole-window energy/duration and non-replenishing
budget contradictions across earlier allocation gaps while exact ledgers remain
Q. Possible recharge never becomes a fixed initial-budget cap.
Unqualified household correspondence retains upstream protection failures only
as diagnostics for their original subjects. No source, rights split,
dispatch priority, monetary value or permission is chosen by this consumer.

See the [versioned input/status registry](../../registry/b07_shared_use_schedule_contract.json)
and [checkpoint with usage and acceptance coverage](../../docs/checkpoints/V1_066_B07_SHARED_USE_SCHEDULE.md).
Actual site permission, commercial delivery, household economics and national or
network consequences keep their separate gates. Existing B07 APIs, numerical
behavior and readiness declarations are unchanged.
