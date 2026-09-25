# B05-P28 - product-specific tau_eq evidence path

## Purpose

P27 separated the Q-B05-004 umbrella into:

- bounded product-level evidence;
- coordinate coverage;
- OBS-grade hourly transient fidelity.

P28 investigates one exact OBS-runtime residual:

`PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME`.

Core rule:

`METHOD PARAMETER ROLE != DEFAULT VALUE != PRODUCT OBSERVATION`.

## 1. What HEM establishes

Current HEM-TP-12 defines the below-minimum on/off inertia term using:

- minimum continuous compressor power;
- load ratio;
- `tau_eq`;
- emitter/distribution response time.

HEM explicitly describes `tau_eq` as a characteristic parameter of the heat pump due to the on/off transient.

Therefore `tau_eq` is not semantically interchangeable with:

- Cdh;
- minimum modulation;
- controller anti-cycling time;
- emitter response time.

## 2. Default-policy boundary

P25 already admitted:

`HEM_DEFAULT_SCENARIO -> tau_eq = 140 s`

as POL/default authority.

P28 does not change that.

The 140 s value is still forbidden as a product observation unless a product-specific source independently proves the same value.

## 3. Exact public PCDB audit

P28 checked exact public product records for the two canonical bounded surfaces.

### Mitsubishi PUZ-WM50VHA

The UK PCDB public product record exists for Mitsubishi Electric Ecodan 5.0 kW / PUZ-WM50VHA.

The public-facing detail exposes product identity and assessment fields, but no product `tau_eq` / on-off transient time-constant field.

### Dimplex LA 2030CP

The UK PCDB public search/detail record exists for Dimplex LA 2030CP, including the 35 C record.

The public-facing record does not expose a product `tau_eq` / on-off transient time-constant field.

Important boundary:

`PUBLIC FIELD NOT EXPOSED != INTERNAL/SUBMITTED FIELD DOES NOT EXIST`.

P28 therefore does not claim that BRE, the manufacturer or a test laboratory lacks the parameter.

## 4. Certified part-load data are not tau_eq

The canonical HP KEYMARK evidence already contains product-specific EN14825 Cdh values for Mitsubishi and Dimplex.

Those values remain useful for the standard-bin validation track.

They are not silently converted into `tau_eq` for the hourly HEM/EN15316-style transient path.

No inverse derivation is admitted without an explicit validated method and the underlying transient test record.

## 5. Residual narrowing

Previous residual:

`PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME`

becomes:

`OPEN_NARROWED_TO_PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED`.

Admissible future evidence includes an explicit product/manufacturer/test-lab record that identifies the model and reports or validly derives `tau_eq` from the relevant transient/part-load test.

Forbidden closure routes:

- HEM 140 s default -> product OBS;
- Cdh -> tau_eq without explicit authority;
- controller anti-cycling timer -> tau_eq;
- cross-product tau_eq transfer;
- literature range midpoint -> product value.

## 6. Readiness

No readiness uplift.

- `PART_LOAD_MODULATION = 45%`;
- B05 = **64%**.

P28 improves the evidence acquisition contract; it does not create a physical measurement.

## Sources

Current HEM-TP-12:
https://assets.publishing.service.gov.uk/media/69a6cbe7723a61518b9f1395/hem-tp-12-heat-pump-methodology.pdf

Mitsubishi PUZ-WM50VHA UK PCDB public record:
https://www.ncm-pcdb.org.uk/sap/pcdbdetails.jsp?id=104570&mid=020047&pid=31&type=362

Dimplex LA 2030CP UK PCDB public record:
https://www.ncm-pcdb.org.uk/sap/pcdbdetails.jsp?id=111303&mid=020165&pid=31&type=362
