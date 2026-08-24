# B07-P1 data contract

## Product evidence

`data/processed/battery_product_evidence.csv` stores source-native product
facts. Capacity, power and efficiency boundaries are explicit. A usable
capacity derived from a manufacturer DoD statement is `DER`, not `OBS`.
Missing AC/DC or efficiency boundary remains `Q`; chemistry does not create
efficiency, degradation or power assumptions.

## Physical transition

`BatterySpec` requires positive nominal/usable capacities, explicit SOC bounds,
non-negative AC power limits, one-way efficiencies in `(0, 1]`, and a positive
hour timestep. The state is `soc_kwh` on the usable-capacity boundary.

The command results preserve both grid-side and stored-energy quantities:

* charge grid energy → stored energy after one charge efficiency;
* stored energy removed → grid-delivered discharge energy after one discharge efficiency;
* clipped charge and unserved discharge are explicit outputs.

Standing loss is not invented. Temperature restrictions are represented only
when source-native limits exist; outside the envelope the engine fails closed.

## Policy and market separation

The following remain policy questions and never change physical dispatch:

`H_TARIFF_BATTERY_CHARGE_ALLOWED = Q`

`H_TARIFF_BATTERY_DISCHARGE_ALLOWED = Q`

`H_TARIFF_EXPORT_ALLOWED = Q`

Physical flexibility means what the battery could move from its current SOC and
power limits. It is not legal eligibility or a VPP market commitment.

