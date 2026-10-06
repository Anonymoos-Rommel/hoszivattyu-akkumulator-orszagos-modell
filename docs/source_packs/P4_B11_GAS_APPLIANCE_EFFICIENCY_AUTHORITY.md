# B11-P4 — Gas-appliance efficiency authority and energy-basis gate

Canonical base: `52e38ed7696f24e7359d3fb658b8a9df15d8dbb7`

## Core boundaries

`EU ETA_S / LABEL != IN-USE SEASONAL FUEL-CONVERSION EFFICIENCY`

`GCV-BASED EFFICIENCY != LHV-BASED EFFICIENCY`

`ECODESIGN MINIMUM != HUNGARIAN STOCK AVERAGE`

B11-P3 converts useful heat to gas input energy and then to gas volume. P4 hardens the efficiency term used in that conversion.

## EU product/regulatory evidence

Commission Regulation (EU) No 813/2013 defines boiler useful efficiency as useful heat output divided by total energy input, with fuel energy expressed on a GCV basis. It also defines seasonal space-heating efficiency (`eta_s`) as a broader product metric with corrections for controls, auxiliary electricity, standby heat loss and ignition-burner consumption.

Commission Delegated Regulation (EU) No 811/2013 defines the seasonal space-heating efficiency classes used by the product label.

These are authoritative product/regulatory definitions. They do **not** establish the distribution of in-use seasonal gas-appliance efficiency in Hungarian homes and do not, by themselves, authorize programme gas-volume calculations.

The European Commission space-heater policy page provides EU-wide context and EPREL access. Its EU-average in-use/sold boiler efficiency figures are not Hungarian stock calibration and are not imported into the B11 runtime.

## Energy-basis gate

P3 uses gas lower heating value (`LHV`) for the physical m3 conversion. An efficiency stated on gross calorific value (`GCV`) basis cannot be inserted directly.

For the same gas quantity:

`eta_LHV = eta_GCV * GCV / LHV`

Conversion is allowed only when both GCV and LHV are explicit, positive and applicable to the same gas-quality context. No generic national ratio is embedded.

Because `GCV > LHV`, an LHV-basis efficiency for a condensing appliance may exceed 1.0. Therefore P3 no longer applies a basis-blind `<= 1.0` cap. Instead it requires the explicit `fraction_lhv` unit and relies on P4 to authorize/normalize the efficiency evidence.

## Metric authority

P4 separates three concepts:

1. `EU_SEASONAL_SPACE_HEATING_ETA_S` — product/regulatory seasonal metric; not direct fuel-volume authority.
2. `EU_USEFUL_EFFICIENCY` — product operating-point efficiency on the regulation's energy basis; not an observed in-use household seasonal value.
3. `SEASONAL_FUEL_CONVERSION_EFFICIENCY` — the metric required by P3 for annual gas-volume derivation. It must be household/archetype/calibration-specific evidence and must carry an explicit GCV or LHV basis.

## Hungarian stock blocker

No authoritative current Hungarian household/archetype distribution of in-use seasonal gas-appliance fuel-conversion efficiency has been established in this slice. Therefore:

- no 0.8/0.9/etc. national default is introduced;
- no boiler-age class is mapped silently to an efficiency;
- no Ecodesign minimum is treated as existing-stock performance;
- no EU average is treated as Hungarian performance;
- no product label/class is treated as programme calibration.

A later numeric calibration requires evidence that is representative of the Hungarian in-use stock or an explicit household/building system record.

## Runtime consequence

`modules/B11/gas_efficiency_authority.py` rejects regulatory/product metrics when asked to authorize P3 fuel volume. GCV-basis seasonal fuel-conversion evidence additionally requires an explicit GCV/LHV gas-quality pair before an LHV-basis value can be returned.

The P3 bridge now accepts only:

- `fraction_lhv` for seasonal fuel-conversion efficiency;
- `MJ/m3_LHV` for gas lower heating value.

This is an interface hardening, not a new programme bcm result.

## Sources

- EUR-Lex: Commission Regulation (EU) No 813/2013.
- EUR-Lex: Commission Delegated Regulation (EU) No 811/2013.
- European Commission: Space Heaters product-policy page / EPREL context.

Retrieved: 2026-09-03.

## Qualified historical seasonal references

The source-specific `registry/b11_seasonal_boiler_reference_manifest.json`
reuses `registry/b11_gas_efficiency_sources.csv` and the global source registry.
It adds no runtime reader or general evidence schema. Its native records, source
hashes, family/geography/service boundaries and explicit non-admission states
are checked by `tools/validate_registry.py` and
`tests/test_b11_seasonal_boiler_references.py`, following the V1-067 pattern.
Only necessary attributed factual references and original qualification metadata
are retained. Original PDFs/HTML and full extracted text remain external-only;
no original-document redistribution licence or blanket relicensing is inferred.

### BOILeff: selected historical gas installations

`SRC-B11-BOILEFF-FINAL-2009`, Table 2 (printed p12 / PDF p22), reports six HU
`OBS` GCV efficiencies: HU 1 93.4%, HU 2 90.1%, HU 3 88.9%, HU 5 83.8%,
HU 6 80.7%, HU 7 80.0%. These are source-labelled measured field results,
not claims to recovered raw uninterrupted meter series. Eight AT rows remain
separate same-family aggregation context. The detailed `OBS` 14 gas systems
are selected from `OBS` 29 metered systems; the latter include `OBS` 23 gas,
3 oil and 3 biomass systems. The country-by-fuel cross-tab is unavailable.
Installation-quality selection gives no probability-sample or national weights.

Study-level timing is heating season 2008/2009; completed case dates and valid
coverage are unknown. The blank agreement's planned December 2009 endpoint and
meter description do not prove installed/calibrated meters or completed readings.
Actual heating/DHW/storage/distribution and auxiliary boundaries remain incomplete.
The report says `OBS` two cases lacked separate DHW metering without identifying
them. Same-family EEDAL preliminary Austrian methods/results do not fill HU gaps.
The JRC date is repository availability, not an exact print-publication date.

The publisher's `DER` aggregates are HU 86.00%, AT 89.63%, combined 87.9%.
Separate audit `DER` unweighted means of rounded rows are 86.15%, 88.6375% and
87.5714…%. Their disagreement and the apparent AT 7/AT 11 Figure 8 order reversal
remain visible. No weights are invented, source values repaired or default chosen.
Source predictions/guarantee bands are not calibration uncertainty; the climate-
corrected savings comparison does not establish an old-boiler conversion baseline.

### UK EST: processed annual records with different service boundaries

`SRC-B11-EST-FIELD-2009`, Tables 9–11 and Appendix D, supplies `OBS` 43 accepted
annual datasets: 31 combi, 10 regular, 2 CPSU. Individual accepted field ratios
are `DER`, reflecting source processing and possible substitution. The source's
`DER` mean/SD are 82.5%/4.0 percentage points for combi and 85.3%/2.5 points for
regular. CPSU field values are 76.5% and 64.1%; no pooled CPSU statistic is adopted.
Between-site SD is neither metrological uncertainty nor a confidence interval.
Rounded-row means/SD audits do not replace the source's published precision.

Combi meters measure separate boiler SH and DHW output. Regular measures total
boiler heat before primary-pipe/cylinder losses; cylinder draw-off is not its
heat-efficiency numerator. CPSU includes an integral primary store. These are
not interchangeable terminal room/tap service quantities. Regular denotes layout,
not an old non-condensing baseline. SEDBUK product-rating values are outside the
handoff; the source's B-rated regular exception and the author's omitted CPSU
product descriptors remain qualification notes, never substitutes for field values.

The rows join one-to-one to reported substitution counts: `OBS` 449 unchanged
months, 67 substitution months and 225 substituted days. Source-convention
`DER` denominator 43 × 365 = 15,695 days gives 1.4336…%; the source prints
`DER` 1.4% in Table 8, 1.43% in the appendix and contradictory 2.3% in nearby prose.
No prose repair or common-calendar-year claim is made. Class-level count sums
and rounded-row statistics are explicitly audit `DER`. Case 327BSW retains
`OBS` 54 substituted days; case 328CHI retains its breakdown-affected result.

Self-selection, access/space constraints, young boilers, geography and attrition
remain explicit. Actual service and weather vary; no degree-day adjustment was
applied. Short-DHW-draw meter bias, separate electricity, missing propagated
uncertainty and unverified per-case gas subtype remain limits. Summer-DHW-only,
illustrative cylinder-loss and proposed SAP adjustments are not applied to the
annual rows. Neither heat-balance QA thresholds nor product labels provide a
complete uncertainty budget.

`SRC-B11-EST-TPI-2010` is the same cohort family: `OBS` 37 accepted extension
sets and `OBS` 82 combined annual sets do not mean independent homes. Its prose
`OBS` 46 original sets differs from the repeated table's `OBS` 43; arithmetic is
not silently repaired to reconcile the combined count. No additive merge,
independent replication or transferable TPI saving is inferred.

### Existing authority remains unchanged

The source GCV/HCV label is known. Applicable calorific temperature/context,
compatible GCV/LHV pair and volume reference state remain `Q`. The unchanged
`authorize_fuel_volume_efficiency` gate rejects these references with absent
calorific metadata, even when source-native `OBS`/`DER` values are supplied.
No fake `CalorificBasis`, generic conversion ratio, runtime fuel volume,
Hungarian default, source-low/high engine, national weighting, TABULA replacement
or gas-quality-control substitution is created. B11-D01 remains `INTEGRATING`;
its canonical TABULA references, task acceptance and module readiness are unchanged.

The manifest and research log name the remaining qualification debt. Better case
measurement documentation or a separately justified applicable/representative
inference can support later work. Historical reference retention does not require
universal private household bills, measured ageing, a full calendar year or an
exhaustive census. This handoff does not decide later source/default admission.
