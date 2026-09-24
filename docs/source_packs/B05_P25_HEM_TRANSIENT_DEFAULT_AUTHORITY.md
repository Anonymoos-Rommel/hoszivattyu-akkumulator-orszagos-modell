# B05-P25 - HEM transient default authority and bounded emitter mapping

## Purpose

P24 left:

`HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED`.

P25 makes the P24 hourly on/off formula executable under an explicit standard
default policy, while preserving the distinction between:

- method/default values;
- current implementation behavior;
- product-specific physical observations.

Core rule:

`DEFAULT METHOD PARAMETER != PRODUCT OBSERVATION`.

## 1. Current HEM technical document

HEM-TP-12 v3.0 uses the EN15316-4-2:2017 equation-28-style inertia term below
the minimum continuous load ratio.

For the emitter time characteristic it states that current methodology uses:

- **Light embedded systems** for heat pumps with wet distribution;
- **Very low** for warm-air heat pumps;
- **Domestic hot water & storage** for water heating.

It points to EN15316-4-2:2017 Table 13 for the default time characteristics.

## 2. Current UK government reference implementation

Pinned reference-code commit:

`5a3ac9728df712332a5625571c43d3bc10bd2bf3`.

The current Rust heat-pump implementation states that the following constants
come from BS EN15316-4-2:2017 Table 13:

| reference-code class | seconds |
|---|---:|
| RadiatorsUfh | 1370 |
| FanCoils | 360 |
| WarmAir | 120 |
| water / DHW | 1560 |

The runtime chooses:

- `RadiatorsUfh -> 1370`;
- `FanCoils -> 360`;
- `WarmAir -> 120`;
- water-heating service -> `1560`.

The on/off heat-pump inertia parameter itself is not hard-coded by the engine.
The core input schema requires a positive:

`time_constant_onoff_operation`.

Current reference examples and tests repeatedly supply:

`140 s`.

## 3. Historical official UK default authority

The official BRE/UK NCM supporting method CALCM:01 issue 1.2 explicitly states:

- `tau_eq` default = **140 s**;
- heavy embedded emitter = 1920 s;
- light embedded = 1370 s;
- low = 360 s;
- very low = 120 s;
- DHW/storage = 1560 s.

P25 uses this historical document only to establish the provenance of the
**default scenario** value.

It is not treated as:

- a 2026 Hungarian regulatory default;
- a product measurement;
- proof that every heat pump has a 140 s physical transient constant.

## 4. Bounded current agreement

Current HEM v3 text and current reference code agree sufficiently for:

### Radiator / UFH wet distribution

P25 maps this bounded project class to:

`tau_out = 1370 s`.

This follows current HEM's Light-embedded wet-distribution method and the
current code's `RadiatorsUfh` constant.

### Warm air

`tau_out = 120 s`.

### DHW / storage

`tau_out = 1560 s`.

## 5. Fan-coil divergence

This is intentionally not hidden.

Current HEM v3 says the present methodology uses the **Light embedded** value
for **all heat pumps with wet distribution**.

That implies:

`1370 s`.

Current Rust reference code detects fan-coil emitters and uses:

`360 s`.

Therefore P25 returns:

`Q / HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED`.

No silent preference is given to documentation or code.

## 6. Explicit HEM-default tau_eq policy

The generic variable:

`VAR-B05-ONOFF-TRANSIENT-TAU-EQ`

remains Q for product-specific physical runtime.

A new separate policy variable is introduced:

`VAR-B05-HEM-DEFAULT-TAU-EQ = 140 s` — **POL**.

The 140 s value is only admitted if the caller explicitly selects:

`HEM_DEFAULT_SCENARIO`.

With no product-specific value and no explicit default policy, the runtime
fails closed.

If a qualified product-specific `tau_eq` is supplied, it takes precedence
and is not replaced by 140 s.

## 7. Executable example

For an explicit radiator/UFH HEM-default scenario:

- minimum continuous compressor power = 0.50 kW;
- load ratio = 0.20;
- minimum continuous load ratio = 0.40;
- `tau_eq = 140 s`;
- emitter time = 1370 s.

P24 equation:

`P_onoff = 0.50 * 140 * 0.20 * 0.80 / 1370`

gives approximately:

`0.00817518 kW`.

This is a **POL/default-scenario DER result**, not a product observation.

## 8. Residual transition

`HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED`
->
`RESOLVED_FOR_EXPLICIT_HEM_DEFAULT_POLICY_WITH_BOUNDED_EMITTER_CLASSES`.

Q-B05-004 becomes:

`OPEN_NARROWED_TO_DOMAIN_GAPS_FANCOIL_AND_PRODUCT_TAU_EQ`.

Remaining residuals:

1. `MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`;
2. `DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`;
3. `HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED`;
4. `PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME`.

## 9. Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

No readiness uplift is minted because P25 establishes a controlled default
scenario, not new product-specific transient measurements.

## Sources

Current HEM-TP-12 v3.0:
https://assets.publishing.service.gov.uk/media/69a6cbe7723a61518b9f1395/hem-tp-12-heat-pump-methodology.pdf

Current UK government Rust reference implementation:
https://github.com/communitiesuk/epb-home-energy-model/blob/5a3ac9728df712332a5625571c43d3bc10bd2bf3/src/core/heating_systems/heat_pump.rs

Current core input schema:
https://github.com/communitiesuk/epb-home-energy-model/blob/5a3ac9728df712332a5625571c43d3bc10bd2bf3/schemas/core-input.schema.json

Historical official UK NCM CALCM:01 issue 1.2:
https://www.ncm-pcdb.org.uk/sap/filelibrary/pdf/Calculation_Methodology/SAP_2012/CALCM-01---SAP-REVISED-HEAT-PUMP-PERFORMANCE-METHOD---V1.2.pdf
