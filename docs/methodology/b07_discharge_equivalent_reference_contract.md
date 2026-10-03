# B07 discharge-equivalent conditional-reference coordinate contract

Status: OWNER-ADOPTED CONDITIONAL REFERENCE METHOD, 2026-10-02. Adoption permits the separately named reference and its reviewed feature-branch implementation. It does not replace the existing BatterySpec/one-way engine, select national operating policy, or authorize a main merge. The coordinate and balances are DER; test-to-target constant-parameter applicability and the declared aggregate standby proxy remain E2/PROVISIONAL_BASE under Q-B07-003.

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

Existing Q-B07-003 is E2, VALIDATION_BLOCKER, model_blocker=no. The owner adopted this bounded method after review and clarified that E2 continuation must not wait for every component-level E1 measurement. That adoption does not close validation debt or promote source applicability to E1. Altering final scope, evidence quality, costs, legal permission or procurement intent still requires the applicable owner decision. The new reference must have its own API and cannot be encoded by setting legacy charge_efficiency=eta and discharge_efficiency=1.

## Supporting standby and curve evidence

Figure24 on PDFpage26 does resolve SAX A1's tested EMPTY-state path: cumulative total and AC-system-plus-sensor vector bars have exactly the same height. The total digitizes to4.0694977W, consistent with the app's4.07W; the AC sensor component is about0.8595W. Thus the tested empty-state reported total is AC-side. This does not resolve nonempty idle-state draw or cell/BMS consumption excluded from the test. Evidence is in registry/b07_sax_reference_manifest.json, standby_component_evidence; no original figure is proposed for repository publication.

The separate discharge curve fits differ in their overlap. At160/200/300/400/450W, the standard fit is about0.691/0.557/0.364/0.262/0.228 percentage points more efficient than the dedicated low-load fit. This is fit/method uncertainty within one source family, not independent evidence to average. A first point-reference consumer should require an explicit curve selection and stay within that curve's domain. A later dispatch integration must adopt and test its selection/join rule explicitly.

## API necessity and existing-code reuse

The existing BatterySpec, BatteryState, BatteryStepResult and B08 handoff encode stored-energy SOC and scalar one-way transitions. Their state/clipping fields cannot represent this coordinate without misleading semantics. A new reference state must name discharge-equivalent DC inventory and explicit converter flows. The existing AC household balance function compute_household_balance is reusable unchanged for actual admitted AC charge and delivered AC discharge. Existing scalar-efficiency clipping is not reused because converter efficiency varies with actual path output and curve support. A reference flexibility result, if implemented, must call the same new feasibility solver rather than the legacy scalar formula. This does not create a second tariff, export-permission or household accounting policy.


## E2 aggregate continuation and later E1 closure

The reference implementation is `modules/B07/discharge_equivalent_reference.py`.
Its constant tested-product C and DC-cycle eta have scoped E2 applicability;
its calculated balances are DER with explicit scenario commands. A caller-created
mathematical Reference remains SCN/E3 rather than acquiring source status from
the method's adoption. Source-labelled references must match the pinned facts.

`provisional_standby_ac_energy(idle_hours=...)` applies one4.07W aggregate
AC-accounting proxy to explicitly supplied idle exposure. HTW's exact-system
empty-state observation and the manufacturer's approximately4W system statement
support this E2 base. It may supply a provisional finite/annual aggregate energy
component; exact BMS subcomponents are not a prerequisite. State/revision and
cell-powered loss inclusion remain explicit validation debt. The value is not
an all-state observation or an upper bound, and no idle duration is selected.
Active cycle losses already include their tested BMS contribution; the idle
proxy is not added to active converter/cycle paths a second time.

The aggregate debit does not establish physical DC inventory drain. The current
state-path consumer retains Q across idle intervals until that physical
allocation is supplied under an appropriate contract. This is a scope limitation
of that consumer, not an E3 reclassification of Q-B07-003 or a prohibition on
provisional aggregate model continuation. Neither SPI nor a product of path
means is a substitute for a boundary-consistent energy round-trip base.

`registry/b07_reference_validation_debt.json` records the exact approximations,
support, applicability and E1 upgrade evidence. Sufficient boundary-complete
aggregate measurements or validated calibration can close that debt; a separate
laboratory value for every internal component is not mandatory. Materiality is
assessed for the actual decision/profile when relevant, not imposed as another
universal E2 gate. The known4.07W component corresponds to5.0875–14.245kWh over
the report's generic1,250–3,500empty hours, or35.6532kWh over8,760explicit hours.
Those are conditional exposure calculations, not Hungarian operating assumptions
or bounds on unmeasured losses. No claim of negligible total error is made.


## Qualified temperature and test-condition handoff (V1-052)

The curated SAX controls now carry `source_conditions`, and genuine source-labelled
`run()` and provisional aggregate-idle results expose that same hash-bound metadata.
Synthetic mathematical references return no source-condition authority. No numerical
source value, fitted vertex, clipping formula, cycle calculation or idle base changes.

HTW/aquu report version 1.0, declared March 2026, Table 1 on printed/PDF page 13
reports a manufacturer-specified 5–35 °C permissible range for the SAX battery and
inverter. The exact undated manufacturer datasheet corroborates that specification;
it is the same manufacturer lineage, not an independent temperature experiment.
The range is neither measured test ambient nor a validated capacity/efficiency envelope.
Actual SAX laboratory ambient and individual test date remain null/Q. Page 17 notes
ambient influence without supplying a numeric SAX test temperature. No midpoint,
generic guideline temperature, site default, thermal correction or derating law is selected.

The report's common capacity procedure (pages 9 and 15) uses 100%, 50% and 25% of
nominal charging/discharging power, three cycles at each level, discards the first
conditioning cycle, and averages discharged DC energy over the six retained cycles.
Its numerical power illustration is Fronius D1, not SAX A1. Exact SAX cycle wattages
and raw traces remain unknown; no multiplication of catalog ratings supplies them.
Battery efficiency retains the reported eta_BAT summary without inventing a pooling
formula. The additional low-load procedure on pages 21–22 is separate, with at least
eight measured supports up to 10% nominal discharge power. The SAX measurement count
is not established, and fitted-vector vertex counts are not measurement counts.

These conditions complete the missing D01 source-to-consumer metadata at the existing
bounded E2 level. Test-to-target applicability remains Q-B07-003 debt. They do not
admit site operation, whole-year physical inventory, a national product mix, lifecycle
returns, legal access, or a new B08 reference-dispatch path. Unsupported temperature
fields are rejected by the existing explicit command schema. D01 acceptance requires
review of this exact condition handoff and a truthful reviewed-commit binding; it does
not require a new measurement campaign merely to use the adopted E2 reference.
