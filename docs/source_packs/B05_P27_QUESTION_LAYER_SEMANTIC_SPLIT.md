# B05-P27 - Q-B05-004 semantic subclaim split

## Purpose

P24-P26 accumulated four different residual types under the single Q-B05-004 umbrella.

The original question is:

**which products have proven minimum modulation, cycling and part-load degradation evidence?**

The historical lineage also intentionally keeps Q-B05-004 OPEN while broader product/runtime coverage is incomplete.

P27 therefore does not rename the question, does not add new top-level question IDs and does not rewrite historical source packs.

Instead it makes the internal state explicit:

`PRODUCT-LEVEL EVIDENCE != COORDINATE COVERAGE != OBS-GRADE HOURLY TRANSIENT FIDELITY`.

Q-B05-004 remains OPEN as the umbrella.

## 1. PRODUCT_LEVEL_EVIDENCE

This subclaim is:

`RESOLVED_BOUNDED_PRODUCT_EVIDENCE`.

### Mitsubishi PUZ-WM50VHA(-BS)

Canonical evidence already contains:

- 40 exact manufacturer minimum-capacity + minimum-point COP observations;
- 27 complete bounded interpolation cells;
- exact same-product Cdh bins;
- exact cycling-ready points where minimum floor, COP and Cdh co-locate.

### Dimplex LA 2030CP

Canonical evidence already contains:

- 15 exact manufacturer minimum-output points across W35/W45/W55;
- six bounded piecewise cells;
- exact non-default HP KEYMARK Cdh bins;
- three exact W35 cycling-ready bins.

This proves bounded product-level evidence.

It does not prove exhaustive market coverage.

## 2. COORDINATE_COVERAGE

This subclaim remains OPEN.

Residuals:

- `MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`;
- `DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`.

These are exact coordinate/surface gaps.

They do not erase the bounded product-level evidence already established.

No graph digitization, source-gap interpolation, zero-fill or cross-product transfer is introduced.

## 3. OBS_HOURLY_TRANSIENT_FIDELITY

This subclaim remains OPEN.

P25 already made the explicit HEM default-policy path executable for supported emitter classes.

That does not make HEM defaults product observations.

Residuals:

- `HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED`;
- `PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME`.

## 4. Fresh upstream fan-coil audit

The current official HEM-TP-12 v3.0, issue date January 2026, still states that the current methodology uses the **Light embedded** value for **all heat pumps with wet distribution**.

The current UK government reference-code commit remains:

`5a3ac9728df712332a5625571c43d3bc10bd2bf3`.

The code still defines:

- `RadiatorsUfh = 1370 s`;
- `FanCoils = 360 s`;
- `WarmAir = 120 s`.

Therefore the fan-coil documentation/code divergence is current and remains Q.

P27 does not choose one side.

## 5. Readiness

No readiness uplift is created by semantic repair.

- `PART_LOAD_MODULATION = 45%`;
- B05 = **64%**.

## Sources

Current official HEM technical-documentation index:
https://www.gov.uk/government/publications/home-energy-model-technical-documentation

HEM-TP-12 v3.0:
https://assets.publishing.service.gov.uk/media/69a6cbe7723a61518b9f1395/hem-tp-12-heat-pump-methodology.pdf

Current reference implementation:
https://github.com/communitiesuk/epb-home-energy-model/blob/5a3ac9728df712332a5625571c43d3bc10bd2bf3/src/core/heating_systems/heat_pump.rs
