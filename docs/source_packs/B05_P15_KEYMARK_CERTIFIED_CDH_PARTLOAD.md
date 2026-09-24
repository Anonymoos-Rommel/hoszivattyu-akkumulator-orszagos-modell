# B05-P15 - HP KEYMARK certified non-default Cdh and part-load evidence

## Purpose

B05-P15 narrows Q-B05-004 by separating three layers:

1. certified EN 14825 part-load fields published for an identified product;
2. the EN 14825 degradation-coefficient default rule;
3. B05 hourly cycling-runtime application.

Core boundaries:

`CERTIFIED NON-DEFAULT CDH != REGULATORY DEFAULT 0.9`

`CERTIFIED CDH FIELD != INDEPENDENT RAW LAB MEASUREMENT AT EACH TJ`

`PRODUCT-SPECIFIC EN14825 CDH != UNIVERSAL CYCLING PENALTY`

`PART-LOAD COP TABLE != B05 HOURLY CYCLING FORMULA`

`CDH = 0.9 != PROOF THAT 0.9 WAS MEASURED`

P15 does not modify the B05 engine energy formula.

## 1. Standard semantic authority

EN 14825 defines the degradation coefficient Cd as a measure of efficiency
loss due to cycling.

For air-to-water, water/brine-to-water and DX-to-water units, if Cd is **not
determined by measurement**, the default degradation coefficient is 0.9.

Therefore a certified EN 14825 Cdh value that differs from 0.9 cannot be the
standard no-measurement fallback.

P15 calls such a value:

`CERTIFIED_NONDEFAULT_MEASUREMENT_DETERMINED_CDH`.

This classification is intentionally narrower than calling every published
Tj-specific value an independent raw laboratory measurement. The KEYMARK
publication is the certified product field; its internal EN 14825 derivation
may include standard-method transformations.

Conversely, a published value exactly equal to 0.9 remains semantically
ambiguous without additional test metadata:

`0.9 -> DEFAULT_OR_MEASURED_EQUAL_TO_DEFAULT_UNRESOLVED`.

## 2. Current certified product

Current Heat Pump KEYMARK subtype:

- certificate holder: Vaillant GmbH;
- registration: 011-1W0760;
- subtype: aroTHERM plus / aroTHERM exclusive ES (M casing);
- certification body: DIN CERTCO;
- testing basis: HP KEYMARK certification scheme rules rev. 15;
- testing laboratory: TÜV Rheinland Energy GmbH, DE.

P15 materializes the current model:

`VWL 85/6 A 230V S3`

for EN 14825 average climate.

## 3. Certified average-climate part-load fields

### Low-temperature application

| Tj | Pdh kW | COP Tj | Cdh Tj |
|---:|---:|---:|---:|
| -7 C | 6.38 | 2.93 | 0.990 |
| +2 C | 3.83 | 4.73 | 0.970 |
| +7 C | 3.21 | 6.33 | 0.950 |
| +12 C | 3.72 | 7.79 | 0.940 |

### Medium-temperature application

| Tj | Pdh kW | COP Tj | Cdh Tj |
|---:|---:|---:|---:|
| -7 C | 5.66 | 2.17 | 0.990 |
| +2 C | 3.49 | 3.32 | 0.970 |
| +7 C | 3.06 | 4.67 | 0.960 |
| +12 C | 3.62 | 6.23 | 0.950 |

All eight Cdh values differ from the EN 14825 no-measurement fallback 0.9.

Therefore P15 qualifies an identified current air-to-water product with
certified non-default Cdh plus certified Pdh/COP part-load fields.

## 4. What is resolved

P6 stated that no product-specific measured Cdh/cycling COP was in the evidence
pack.

P15 supersedes only that narrow statement:

- product-specific certified Cdh exists for an identified current product;
- certified EN 14825 Pdh/COP part-load fields exist at the same Tj anchors;
- the Cdh values are non-default under the EN 14825 fallback rule.

The residual:

`PRODUCT_SPECIFIC_CDH_EVIDENCE_REQUIRED`

is therefore resolved for the admitted Vaillant product.

## 5. What remains open

P15 does **not** directly apply Cdh to every B05 hour.

Remaining work includes:

- exact EN 14825-to-B05 runtime application contract;
- capacity-ratio / cycling-state mapping;
- interaction with source-native minimum modulation;
- interpolation between certified Tj anchors;
- treatment outside the certified part-load domain;
- cross-manufacturer validation;
- decision whether the B05 hourly runtime should use EN 14825 standard-method
  degradation directly or only as a sensitivity/control layer.

Therefore Q-B05-004 becomes:

`OPEN_NARROWED_TO_RUNTIME_APPLICATION_AND_MODULATION_COVERAGE`.

## 6. Minimum modulation boundary

P15 does not manufacture a minimum modulation value from Pdh or Cdh.

The existing Vaillant/Stiebel source-native minimum-modulation evidence remains
separate.

`Pdh != MINIMUM_STABLE_MODULATION`.

## 7. Readiness

B05 remains **64%**.

PART_LOAD_MODULATION remains **PARTIAL / 45%** pending the runtime-application
contract and broader modulation coverage.

No readiness percentage uplift is minted.

## Sources

### SRC-B05-EN14825-CDH-2022

SIST EN 14825:2022 public catalogue/preview.

https://standards.iteh.ai/catalog/standards/sist/0d3be441-d22e-447c-8204-e2b4b9c731f4/sist-en-14825-2022

Role:
- degradation coefficient definition;
- explicit 0.9 default only if Cd is not determined by measurement for
  air-to-water class.

### SRC-B05-HPKEYMARK-VAILLANT-PLUS-M-2026

Heat Pump KEYMARK current certificate-holder surface.

https://www.heatpumpkeymark.com/de/nc/ps-keymark/certificate-holders/?cHash=49e546a4d0f777aac5ca2a80652e03a6&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=7607

Role:
- current certified subtype identity;
- DIN CERTCO / TÜV Rheinland test context;
- EN 14825 product-specific Pdh/COP/Cdh fields.
