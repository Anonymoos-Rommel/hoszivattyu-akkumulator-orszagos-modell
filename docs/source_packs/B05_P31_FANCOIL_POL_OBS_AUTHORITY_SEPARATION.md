# B05-P31 — FAN-COIL POL / OBS AUTHORITY SEPARATION

Date: 2026-09-25  
Canonical base: `b7542153b47ff5d65b366330cf0552994aec3993`

## Purpose

P25 and P27 correctly kept the fan-coil emitter response-time conflict
fail-closed:

```
HEM-TP-12 v3 document interpretation: 1370 s
current official HEM reference code:    360 s
```

P31 does not decide which source is "right".

Instead it removes a category error:

```
UPSTREAM HEM POLICY DISAGREEMENT
!=
PHYSICAL FAN-COIL OBSERVATION
```

## Fresh upstream audit

The official HEM technical-documentation index was current on 2026-09-25.

HEM-TP-12:
- document reference: HEM-TP-12;
- version: v3.0;
- issue date: January 2026;
- HEM version: 1.0.

Section 4.3.4 states that the emitter/distribution response time
`tau_out,em,type` depends on the emitter category and references
EN15316-4-2:2017 Table 13.  It then states that the current methodology uses
the **Light embedded systems** value for **all heat pumps with wet
distribution**.

P31 preserves that as a source-specific document-policy branch:

```
HEM_TP12_V3_DOCUMENT_POLICY = 1370 s / POL
```

The current official reference repository main is still:

`5a3ac9728df712332a5625571c43d3bc10bd2bf3`

at the P31 audit.

In `src/core/heating_systems/heat_pump.rs`, the implementation explicitly
defines:

```
TIME_CONSTANT_SPACE_UFH       = 1370 s
TIME_CONSTANT_SPACE_FAN_COILS =  360 s
TIME_CONSTANT_SPACE_WARM_AIR  =  120 s
```

and selects `TIME_CONSTANT_SPACE_FAN_COILS` for
`HeatPumpEmitterType::FanCoils`.

P31 preserves that as a separate source-specific code-reproduction branch:

```
HEM_REFERENCE_CODE_5A3AC972 = 360 s / POL
```

## What P31 resolves

The old residual:

```
HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED
```

is changed to:

```
RESOLVED_BY_AUTHORITY_SEPARATION_NO_SILENT_SELECTION
```

This does **not** mean the sources now agree.

It means the architecture no longer requires them to agree before work can
continue.

The divergence remains a current factual source condition and is stored as:

`CONFIRMED_CURRENT_DIVERGENCE`.

## Policy behavior

P31 creates two explicit HEM policy-reproduction authorities:

1. `HEM_TP12_V3_DOCUMENT_POLICY` -> 1370 s / POL
2. `HEM_REFERENCE_CODE_5A3AC972` -> 360 s / POL

If neither authority is explicitly selected, fan-coil policy evaluation
fails closed.

The P25 legacy generic resolver is deliberately unchanged and remains Q for
fan coils.

Therefore P31 cannot silently convert either source into the project's
generic default.

## OBS behavior

A separate OBS branch admits a fan-coil response time only when the caller
supplies:

- a positive response-time value; and
- an exact source identifier for the emitter/manufacturer/laboratory record.

The OBS branch cannot be combined with a HEM policy authority in the same
resolution call.

Thus:

```
1370 s HEM document policy != OBS
360 s HEM code policy        != OBS
```

and:

```
explicit emitter/lab transient record -> possible OBS
```

## Runtime consequence

The P24 on/off inertia equation can now be exercised for fan coils in three
strictly separated situations:

- explicit HEM document-policy reproduction;
- explicit current-reference-code reproduction;
- explicit source-bound physical emitter response evidence.

For a fully OBS-oriented runtime, product-specific `tau_eq` remains
independently required.  P31 does not weaken P28.

## Q-B05-004 transition

Historical coordinate residuals remain:

- `MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`
- `DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`

OBS transient residuals become:

- `FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED`
- `PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED`

The HEM doc/code divergence is no longer itself an OBS blocker.

## Readiness

- PART_LOAD_MODULATION: 45% -> 45%
- B05 overall: 64% -> 64%

No readiness uplift is minted because P31 separates authority classes but
does not add a new physical emitter measurement.

## Sources

- HEM-TP-12 v3.0:
  https://assets.publishing.service.gov.uk/media/69a6cbe7723a61518b9f1395/hem-tp-12-heat-pump-methodology.pdf
- Current official HEM reference implementation:
  https://github.com/communitiesuk/epb-home-energy-model/blob/5a3ac9728df712332a5625571c43d3bc10bd2bf3/src/core/heating_systems/heat_pump.rs
