# V1 checkpoint 001: B05 interpolated power consistency

Scope: partial progress within B05-D02, not slice or module completion.

## Reused authority and defect

- `SRC-B05-JRC-COP-2023` defines COP as useful heat output / electrical input.
- `SRC-B05-STIEBEL-HPA-O-CS-PLUS-2022` supplies the existing exact manufacturer points in `data/processed/heat_pump_performance_points.csv`.
- No source document, source value, source status or numerical evidence tier is changed.

The prior engine independently interpolated Q, P and COP. A nonlinear ratio does not commute with interpolation: at HPA-O 4 A−2/W40 it returned Q=3.365 kW, P=1.2066666666666668 kW and COP=2.938888888888889. Its hourly consumer used Q/COP=1.1449905482041587 kW at full output, rather than the map's P, a 5.1113% component discrepancy relative to that P. This is not a national error estimate.

## Correction and limitations

For bounded DER interior and allowed cold-axis points, interpolate Q and total-unit P using the existing weights and calculate COP=Q/P. At the example point COP is 2.7886740331491713 and full-output hourly electricity is 1.2066666666666668 kWh for a one-hour step. Nonpositive interpolated Q/P is fail-closed. No missing source corners are filled and no extrapolation is added.

Choosing Q/P as the dependent interpolated quantity makes the existing power map and consumer internally consistent. It does not empirically validate the bilinear surface, provide a national equipment mix or prove cycling/defrost performance. Exact source-native triples remain unchanged, including their existing stated rounding tolerance; exact-node published COP can therefore still differ slightly from Q/P within that tolerance. This patch does not relabel those published observations.

The minimum-point surface is a different two-observable contract (capacity and COP, with input derived); it does not carry a third independently interpolated input and is unchanged.

## Verification and remaining work

Focused tests cover a varying-power synthetic grid, both existing Stiebel products, interior and cold-axis coordinates, 15/60-minute steps, part/full/overcapacity demand, exact-source preservation, outside-domain rejection, and zero-interpolated-power fail-closed behavior. Existing B05 source/runtime tests remain required. The patch received a separate narrow implementation review; it is not an independent scientific validation of the whole model.

B05-D02 remains INTEGRATING. Next: source-grain cohort/application coverage and actual B02/B06 thermal-demand handoff; B05-D01/D03 remain separate incomplete requirements. No readiness increase, national calculation or evidence-debt closure is claimed.
