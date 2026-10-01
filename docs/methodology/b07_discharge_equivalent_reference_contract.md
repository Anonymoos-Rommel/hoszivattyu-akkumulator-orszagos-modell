# PROPOSED B07 discharge-equivalent tested-reference coordinate contract

Status: PROPOSED, branch-local reviewed method for a separately named conditional reference model. No canonical adoption or owner adoption is asserted. This document does not implement runtime or change the existing BatterySpec/one-way contract. Any required canonical adoption remains an explicit decision before normative replacement.

## Purpose and scope

A reproducible tested-product reference can use measured battery-only DC cycle efficiency, discharged-DC usable capacity and separately published converter curves without pretending to observe chemical one-way efficiencies. The reference is conditional on the source's tested product/firmware and a constant-cycle-efficiency approximation. It is not a representative Hungarian fleet, procurement recommendation, BMS SOC emulator, legal connection permission or aging model.

## State and balances

Let x [kWh_DC_discharge_equivalent] be remaining usable output-equivalent DC inventory, C [same unit] measured discharged-DC usable capacity, eta a battery-only DC cycle efficiency, c the admitted DC charge energy and d delivered DC discharge energy.

x_next = x + eta*c - d, 0 <= x <= C.

The finite-horizon identity is sum(d)=eta*sum(c)+x_initial-x_terminal. Initial energy is declared, and terminal inventory is reported; cyclic comparisons require equal initial/terminal inventory. Charging-side loss assignment is bookkeeping and does not locate physical chemical heat release. x/C is a reference inventory fraction, not demonstrated chemical or BMS SOC.

For any latent constant one-way split a*b=eta, coordinate x=b*z and capacity C_z=C/b produce the same balances with transformed initial/terminal states and reserves. This proves non-identifiability is not a barrier to this reduced reference. No square-root or other split is stored as observed product data.

## Converter boundaries

External commands and results retain AC boundaries, while every DC flow and inventory change is explicit. The source curves use path OUTPUT power:
- Charge curve eta_AC2BAT(q_DC): AC input is q_DC/eta_AC2BAT(q_DC)
- Discharge curve eta_BAT2AC(p_AC): DC withdrawal is p_AC/eta_BAT2AC(p_AC)

Charge commands solve the inverse mapping only inside a verified monotone segment. Capacity permits c <= (C-x)/eta; discharge permits d <= x. All hardware limits apply at their stated boundary. The actual clipped operating point must be solved before energy is admitted; never over-admit then clamp the state.

If the resulting constant operating power is below published support, conservatively decline it and report unused input/unserved demand. Do not silently substitute a duty cycle or average unsupported points. A duty-cycle extension would need its own substep and idle contract. Do not apply manufacturer DoD again to measured usable C; any additional reserve is an explicit separate policy.

## Source identity and low power

Use source edition/product/firmware together. HTW2026A1 identifies SAX Power Home Plus, firmwareV23.50; HTW2023A1 identified VARTA and is not the same product. Published vector-curve points are fitted curves, not hundreds of independent lab observations. Dedicated low-load and standard-power fits are distinct fits from the same research family; their overlap disagreement remains visible. No automatic averaging. Interpolation bridge or selection policy must be explicit before integration.

## Idle and unmodelled losses

HTW2026pp26-27 defines a combined empty-state total. Figure24 specifically resolves SAX A1's reported4.07W to AC-system plus AC-sensor draw at the tested empty state; this is not an all-state idle load. Cell-powered BMS draw cannot be determined under the guideline and is excluded from SPI. Idle AC draw, DC inventory drain and their state applicability require separate evidence or a clearly scoped provisional assumption; omission is not observed zero. Never charge active converter losses again as idle overhead.

Constant eta and C outside the lab conditions remain applicability debt: the report states their dependence on charging/discharging power. A closed-cycle reference can be tested without claiming annual degradation or sustained grid flexibility. A later annual runner must expose idle, aging, initial/terminal and unsupported-power energy rather than hide them.

## Minimal validation

1. Full/partial and finite-horizon DC identities, e.g. C9kWh and eta0.9 require10kWh input to fill and allow9kWh output
2. Coordinate equivalence including capacity, initial/terminal inventory, clipping and reserves
3. Empty/full/near-boundary clipping with unsupported low power declined
4. Correct converter output-axis inverse, post-clipping efficiency and independent AC/DC ledger
5. Constant-power timestep consistency and explicit idle/initial/terminal treatment
6. Year/product/firmware provenance and unchanged legacy gates; no derived coefficient becomes OBS

## Adoption boundary

Existing Q-B07-003 is E2, VALIDATION_BLOCKER, model_blocker=no. Adoption is a methodological contract decision within the approved feasibility work; it does not close that validation debt or change owner claims. Altering final scope, evidence quality, costs, legal permission or procurement intent still requires the applicable owner decision. The new reference must have its own API and cannot be encoded by setting legacy charge_efficiency=eta and discharge_efficiency=1.

## Supporting standby and curve evidence

Figure24 on PDFpage26 does resolve SAX A1's tested EMPTY-state path: cumulative total and AC-system-plus-sensor vector bars have exactly the same height. The total digitizes to4.0694977W, consistent with the app's4.07W; the AC sensor component is about0.8595W. Thus the tested empty-state reported total is AC-side. This does not resolve nonempty idle-state draw or cell/BMS consumption excluded from the test. Evidence is in registry/b07_sax_reference_manifest.json, standby_component_evidence; no original figure is proposed for repository publication.

The separate discharge curve fits differ in their overlap. At160/200/300/400/450W, the standard fit is about0.691/0.557/0.364/0.262/0.228 percentage points more efficient than the dedicated low-load fit. This is fit/method uncertainty within one source family, not independent evidence to average. A first point-reference consumer should require an explicit curve selection and stay within that curve's domain. A later dispatch integration must adopt and test its selection/join rule explicitly.

## API necessity and existing-code reuse

The existing BatterySpec, BatteryState, BatteryStepResult and B08 handoff encode stored-energy SOC and scalar one-way transitions. Their state/clipping fields cannot represent this coordinate without misleading semantics. A new reference state must name discharge-equivalent DC inventory and explicit converter flows. The existing AC household balance function compute_household_balance is reusable unchanged for actual admitted AC charge and delivered AC discharge. Existing scalar-efficiency clipping is not reused because converter efficiency varies with actual path output and curve support. A reference flexibility result, if implemented, must call the same new feasibility solver rather than the legacy scalar formula. This does not create a second tariff, export-permission or household accounting policy.
