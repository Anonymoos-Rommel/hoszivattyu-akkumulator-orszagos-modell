# V1 checkpoint012: three historical TABULA annual heat references

Purpose: reproduce source-filled building physics before national service allocation. Nine source variants belong to three examples and their two envelope packages. The result is annual useful space heat at the source-conditioned floor-area boundary, excluding DHW, generator/distribution losses, electricity and peak load. It is not observed household consumption or a 2022 Hungarian population estimate.

The exact July2016 workbook is read with cached values and formula strings; no Excel formulas/macros are executed. The source row entry/change dates remain separate from workbook issue/retrieval dates. Source formulas remain provenance only. The independent Python seasonal calculation checks all nine source outputs. Native geometry checks and source remarks remain visible; their meanings must be verified before admission.

Native service uses the workbook's nonuniform/intermittent heating adjustment. Uniform-heating scenarios explicitly set that factor to1 and recompute gain utilization. A changed indoor temperature is allowed only as a separately labelled uniform-service scenario. It does not apply a survey mean to every dwelling or estimate a nonlinear population expectation. Climate, area, geometry and other service settings remain the same within each envelope comparison.

Two native unit annotations are normalized transparently:
- Sum_DeltaT_for_HeatingDays is K·day, despite the workbook label kKh/a. The seasonal W/K × K·day ×24h/day ÷1000 conversion is0.024.
- I_Sol_* is seasonal irradiation per area, kWh/m² during the declared heating period, despite the workbook label kWh/a. Multiplication by window area and optical factors yields kWh; divide by conditioned floor area for kWh/m².

Native2016 low-transmission heating-factor extrapolation is reproduced exactly, including factors over1; it is not silently clipped to match an older2013 printed method. Uniform-service values are explicit SCN, not corrections of the published native values. The case inputs cannot be used to infer a design peak from annual energy or seasonal ground reduction factors.

Attribution: IEE Projects TABULA + EPISCOPE (www.episcope.eu). Reuse terms: https://episcope.eu/communication/download/ . The numerical subset and source formulas retain attribution; no source workbook is executed. Exact source bytes remain available locally with a hash; repository snapshot status must be explicit.

A third native annotation is harmonized: g_gl_n_Measure_Window_1/2 are dimensionless solar-energy transmittances, despite the native m²K/W header. This follows their optical multiplication in the source equation.

The source geometry compatibility check is preserved as a warning. The total-envelope ratios pass its [0.8,1.25] check. All three examples fail its simple floor-area estimator comparison [0.9,1.3], and MFH also fails its window-plus-door ratio [0.67,1.5]. These are exact manually supplied geometry versus simplified estimator checks, not a proof that the geometry is wrong. Historical reference reproduction is possible with the warning; applicability to a real building or current type-average still needs separate justification.

This seasonal reference does not populate the existing B06 P63 monthly-plus-design-peak contract. Any monthly/hourly handoff needs source-backed time distribution and design conditions, and no source annual value is silently converted to a peak or monthly series.

## Verification and downstream status

The extractor reproduces all nine rows byte-for-byte from the pinned source workbook, with native worksheet/column/row, units, dates, cached values and 351 formula cells. Independent read-only review compared all2979 cells of the nine full original rows with the workbook and reproduced all50 Hungarian annual results (maximum residual5.68e−14kWh/m²). That review also confirmed the source geometry check and the three unit annotations. It does not establish empirical validation or current representativeness.

Six focused consumer tests cover the nine annual regressions, source hashes, geometry-warning visibility, uniform-service recalculation, temperature/scope rejection, retained source factors above1 and the gain/loss-ratio1 analytical limit and neighbourhood. Full-suite verification is recorded separately. The module is restricted to these nine source Refurbishment variants; the broader workbook Variation branch is not implemented.

Source-native results are DER. Uniform-service results are SCN. Neither closes a whole research slice, changes a readiness score, nor claims that missing monthly/design inputs equal zero. For the deep-renovated multifamily/block examples the source-native adjustment exceeds1, so the explicit uniform case is not universally an upper heat-demand bound. No further general TABULA literature search is required for this narrow historical reference; further evidence is sought only for a material downstream handoff.
