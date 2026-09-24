# B05-P16 - cross-manufacturer part-load validation and runtime state gate

## Purpose

B05-P16 continues Q-B05-004 from the P15 boundary without promoting certified
part-load fields into an unsupported hourly energy formula.

It closes two narrower method/evidence steps:

1. a second manufacturer is required to show that non-default certified EN14825
   Cdh plus Pdh/COP fields are not unique to the admitted Vaillant record;
2. the B05 runtime must decide continuous versus cycling operation from an
   explicit minimum continuous modulation input **before** degradation evidence
   can be considered.

Core boundaries:

`CERTIFIED CDH != DIRECT HOURLY MULTIPLIER`

`PDH != MINIMUM STABLE MODULATION`

`CYCLING STATE != NUMERIC CYCLING ENERGY CORRECTION`

`UK HEM METHOD CONTROL != HUNGARIAN REGULATORY AUTHORITY`

`CROSS-MANUFACTURER FIELD VALIDATION != PERFORMANCE EQUIVALENCE`

P16 does not modify the B05 engine energy formula.

## 1. Second-manufacturer certified evidence

Current Heat Pump KEYMARK subtype:

- certificate holder: Bosch Thermotechnik GmbH;
- registration: 011-1W0581;
- subtype: Bosch CS5800i/6800iAW 4/5/7 OR;
- certification body: DIN CERTCO;
- test laboratory: Fraunhofer ISE, DE;
- refrigerant: R290.

P16 materializes the identified model:

`CS5800iAW 4 ORE-S (60°C)`

for the certified warmer-climate part-load rows exposed by the current KEYMARK
record.

### Low-temperature application

| Tj | Pdh kW | COP Tj | Cdh Tj |
|---:|---:|---:|---:|
| +2 C | 4.31 | 3.21 | 0.990 |
| +7 C | 2.64 | 4.95 | 0.970 |
| +12 C | 1.82 | 6.72 | 0.950 |

### Medium-temperature application

| Tj | Pdh kW | COP Tj | Cdh Tj |
|---:|---:|---:|---:|
| +2 C | 3.92 | 2.12 | 0.990 |
| +7 C | 2.41 | 3.09 | 0.980 |
| +12 C | 1.79 | 5.01 | 0.960 |

All six Cdh values are non-default relative to the EN14825 air-to-water
no-measurement fallback established in P15.

This resolves:

`CROSS_MANUFACTURER_PART_LOAD_VALIDATION_REQUIRED`

as:

`RESOLVED_FOR_TWO_CERTIFIED_MANUFACTURERS`

for evidence-field availability only. Vaillant and Bosch values are not pooled,
averaged, transferred between products, or treated as a market sample.

## 2. Current HEM method control

The UK Home Energy Model HEM-TP-12 current technical methodology states that a
variable-capacity heat pump enters on/off operation when the load ratio is below
the lowest possible continuous load ratio. It also treats minimum modulation as
a separate input to the calculation, including a required 35 C input for wet
distribution and an optional 55 C input when corresponding EN14825 test data is
provided.

HEM then calculates on/off driving energy through a separate on/off/inertia
method. This is important to B05 because it supports the **ordering** of the
runtime state decision while rejecting a shortcut such as:

`hourly COP x Cdh`

HEM is used here only as a high-quality external method control. It is not
Hungarian regulatory authority and does not supply product-specific modulation
floors for the B05 admitted products.

## 3. Executable fail-closed state contract

P16 adds `part_load_runtime_contract.py`.

For a positive hourly requirement inside available capacity:

1. no explicit minimum continuous capacity ->
   `Q / MODULATION_FLOOR_REQUIRED`;
2. requirement >= minimum continuous capacity ->
   `CONTINUOUS_MODULATION`;
3. requirement < minimum continuous capacity ->
   `BELOW_MINIMUM_MODULATION / CYCLING_REQUIRED`.

The contract exposes both:

- load ratio = required / available capacity;
- minimum continuous load ratio = minimum continuous / available capacity.

Product-specific Cdh evidence becomes *eligible for consideration* only in the
cycling state. The contract always returns:

`direct_numeric_cdh_application_allowed = False`.

Therefore the old residual:

`CDH_TO_B05_RUNTIME_APPLICATION_CONTRACT_REQUIRED`

is narrowed to:

`CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED`.

## 4. What remains open

Two residuals remain for Q-B05-004:

- `MULTI_PRODUCT_MIN_MODULATION_COVERAGE_REQUIRED`;
- `CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED`.

The first requires same-product/source-native modulation-floor coverage that can
be safely joined to the product runtime record. Pdh is not used as a proxy.

The second requires an approved numeric cycling-energy method and all parameters
needed by that method. P16 does not import the UK HEM numeric equations into the
Hungarian runtime merely because their state semantics are useful.

Canonical Q-B05-004 state:

`OPEN_NARROWED_TO_MIN_MOD_COVERAGE_AND_NUMERIC_CYCLING_METHOD`.

## 5. Readiness

B05 remains **64%**.

PART_LOAD_MODULATION remains **PARTIAL / 45%**.

No percentage uplift is minted because the engine still has no admitted numeric
cycling-energy correction and same-product modulation-floor coverage remains
incomplete.

## Sources

### SRC-B05-HPKEYMARK-BOSCH-CS5800I-2026

Heat Pump KEYMARK current Bosch subtype surface.

https://www.heatpumpkeymark.com/de/?cHash=53c245b5daddd9d259070acb2f8a5b5a&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=5929&type=109126

Role:
- current certified subtype identity;
- DIN CERTCO / Fraunhofer ISE test context;
- product-specific certified EN14825 Pdh/COP/Cdh fields.

### SRC-B05-UK-HEM-TP12-2026

UK Department for Energy Security and Net Zero, Home Energy Model HEM-TP-12.

https://assets.publishing.service.gov.uk/media/69a6cbe7723a61518b9f1395/hem-tp-12-heat-pump-methodology.pdf

Role:
- variable-capacity continuous/on-off state boundary;
- minimum modulation as a separate input;
- evidence that on/off electricity is treated by a separate runtime method
  rather than by a universal direct Cdh multiplier.

P16 does not treat HEM as Hungarian regulatory authority.
