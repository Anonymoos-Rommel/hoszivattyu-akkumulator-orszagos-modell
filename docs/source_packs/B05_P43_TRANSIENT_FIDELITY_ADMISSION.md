# B05-P43 - transient-fidelity evidence admission

Date: 2026-09-26
Canonical base: `b68213f6d330e1c27a9314c7ba5cc8a2ddffd518`

## Purpose

P43 attacks the two OBS transient-fidelity residuals left by P31/P42:

1. `FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED`;
2. `PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED`.

P43 does not assign a new response-time value. It converts the remaining
research problem into two executable fail-closed measurement contracts and
identifies exact named acquisition targets.

Core boundaries:

```
ROOM + FCU SYSTEM RESPONSE != EMITTER-ONLY RESPONSE
COOLING RESPONSE != HEATING RESPONSE
GENERIC LITERATURE TIME CONSTANT != CANONICAL PRODUCT tau_eq
NAMED TEST LAB != TRANSIENT TEST RESULT
KEYMARK Cdh != tau_eq
```

## 1. Fan-coil physical evidence review

Arghand et al., *Dynamic Thermal Performance and Controllability of Fan Coil
Systems*, experimentally studied a fan-coil system in a mock-up office room.
The study applied step changes in supply-water temperature, fan speed and room
heat load and found first-order dynamic behaviour.

The critical measurement boundary is explicit: dynamic response was evaluated
using room operative temperature, and the tested installation was operated as a
cooling system with chilled water.

This is genuine experimental evidence that fan-coil systems possess measurable
dynamic response. It is not the physical quantity required to populate the
project's fan-coil emitter response-time input for heating.

Therefore:

`SYSTEM_LEVEL_DYNAMIC_OBS_NOT_EMITTER_RESPONSE_OBS`.

Residual:

`OPEN_NARROWED_TO_EMITTER_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`.

A future fan-coil record may populate the OBS branch only with exact source-
bound emitter/test-specimen identity, heating mode, a defined physical input
step, direct emitter output response or source-native air/water-side
measurements sufficient to derive it, explicit timebase, and a positive
response time reported or validly derived. Room operative temperature alone
fails the gate; cooling is not silently transferred to heating.

## 2. Heat-pump tau_eq evidence review

Xu et al. (2021) report materially different time constants across prior AWHP
studies: 24 s for one tested unit, 25-35 s for EEV cases, 100-120 s for TEV
cases and 10-20 s in another study. The paper explicitly states that an
accurate value for a given unit requires a detailed test with seconds-scale
sampling.

P43 uses this only as a method boundary:

`TAU_EQ_IS_UNIT_SPECIFIC_AND_REQUIRES_TRANSIENT_TEST_EVIDENCE`.

None of these literature values is transferred to Mitsubishi PUZ-WM50VHA or
Dimplex LA 2030CP.

Residual:

`OPEN_NARROWED_TO_EXACT_PRODUCT_SECONDS_SCALE_TRANSIENT_RECORD_FROM_MANUFACTURER_OR_NAMED_TEST_LAB`.

A future product record may populate `VAR-B05-ONOFF-TRANSIENT-TAU-EQ` only
when exact product and source identities are explicit and either the
manufacturer/named laboratory directly reports tau_eq from a relevant heating
on/off transient test, or a record exposes a seconds-scale heating
start/restart transient with thermal-output and electrical-input response,
steady-state reference and explicit derivation method.

Generic literature ranges, controller anti-cycling timers, Cdh and HEM 140 s
remain forbidden substitutes.

## 3. Named canonical laboratory targets

Current HP KEYMARK binds **Dimplex LA 2030CP** registration `40060852` to
**VDE Prüf- und Zertifizierungsinstitut GmbH, DE** and includes EN 14825:2022
in the testing basis.

Current HP KEYMARK covering **Mitsubishi PUZ-WM50VHA(-BS)** binds registration
`037-0032-20 / rev. 2` to **SZU Brno, CZ**.

These are now named acquisition targets. Their public certification surfaces
identify the laboratory but do not expose an admitted tau_eq or raw
seconds-scale transient record.

## 4. Q-B05-004 transition

P42 state remains an OPEN umbrella. P43 residuals:

1. `MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`;
2. `EMITTER_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`;
3. `EXACT_PRODUCT_SECONDS_SCALE_TRANSIENT_RECORD_FROM_MANUFACTURER_OR_NAMED_TEST_LAB`.

No readiness is minted from better targeting.

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

## Sources

- Fan-coil experiment: https://research.chalmers.se/en/publication/507939
- AWHP on/off transient study: https://www.sciencedirect.com/science/article/pii/S1359431121007535
- Dimplex LA 2030CP HP KEYMARK: https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=6778
- Mitsubishi WM50 HP KEYMARK: https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=4300
