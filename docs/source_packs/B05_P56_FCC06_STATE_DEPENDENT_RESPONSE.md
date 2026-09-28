# B05-P56 — Trane FCC06 state-dependent physical response admission

**Date:** 2026-09-28  
**Canonical parent main:** `11390535b421592d21f9c89052f6eddb3a65b3e3`

## Purpose

P43-P44 narrowed the fan-coil branch of Q-B05-004 to:

`EXACT_FCU_HEATING_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`.

P56 identifies a materially stronger public record: Martinčević, Vašak and Lešić,
*Identification of a control-oriented energy model for a system of fan coil
units*, Control Engineering Practice 91 (2019) 104100,
DOI `10.1016/j.conengprac.2019.07.018`.

A public author manuscript is hosted by the University of Zagreb FER/LARES.

The record is exact at product grain for **Trane FCC06** and contains heating
experiments, explicit fan-speed steps, minute-scale measurements, a
first-principles switched-linear thermal model, identified state-dependent heat
transfer parameters, and open-loop validation.

P56 does **not** convert this into a universal scalar emitter response time.

Core boundaries:

```
EXACT FCC06 HEATING DYNAMIC RECORD
!=
UNIVERSAL FAN-COIL RESPONSE CONSTANT

8 MIN EXPERIMENT ENGAGEMENT
!=
TAU_OUT = 480 S

FCC06 WATER-STATE TIME CONSTANT
!=
HEM / EN15316 EMITTER TAU_OUT

STATE-DEPENDENT PHYSICAL RESPONSE
!=
ONE SCALAR WITHOUT MAPPING AUTHORITY
```

## 1. Exact test object

The test-site is the University of Zagreb FER living lab.

The source identifies the FCU manufacturer and product types directly:

- Trane FCC06;
- Trane FCC04.

The south-side 9th-floor test system contains 17 FCUs:

- 12 FCC06;
- 5 FCC04.

The thermodynamic identification used by P56 targets FCC06.

The data-acquisition system operates on a one-minute timescale.

## 2. Heating transient protocol

For experimental validation the source shuts down the other units and runs one
selected FCU with valves fully open.

The sequence changes fan speed from OFF to the available non-zero states.

Each fan-speed engagement lasts **8 minutes**. The source states this duration
was sufficient to cover both transient and steady-state behaviour.

P56 admits that as an experimental-window fact only:

`EXPERIMENT_WINDOW = 480 S`.

It explicitly forbids:

`RESPONSE_TIME = 480 S`.

The experiment duration is not a source-reported 63.2% time constant, HEM
`tau_out`, or any other scalar response definition.

## 3. Physical response model

The source derives the FCU water-side dynamic equation:

`m_w c_w dT_w,out/dt = q_w c_w (T_w,in - T_w,out) - U_o (T_w - T_a,in)`

with mean in-coil water temperature approximated by:

`T_w = 0.5 (T_w,in + T_w,out)`.

The air-side time ratio `m_a/q_a` is described as typically below one second
and negligible relative to the water time constant. The air-side process is
therefore treated as stationary and the thermal power affecting the zone equals
the transmitted thermal power under the model assumptions.

For fixed water flow the water state is first order.

The identified FCC06 heat-transfer surface is fan-speed and water-flow
dependent:

`U_o(x,q_w) = epsilon_x * a_x / (1 + b_x q_w^(-beta))`.

Heating-season `epsilon_x = 1`.

Identified parameters:

| fan state | a_x | b_x |
|---|---:|---:|
| OFF | 5.30 | 0 |
| L | 96.45 | 1.73e-3 |
| M | 152.90 | 3.58e-3 |
| H | 201.80 | 5.40e-3 |

Common `beta = 1.86`.

Therefore the source itself demonstrates that physical FCU response is
operating-state dependent.

## 4. Experimental depth

The FCC06 thermodynamic model is identified from **32 test-sequence runs** on
FCC06 units in different zones across:

- heating season 2015/2016;
- heating season 2016/2017;
- cooling season 2017.

For heating the seasonal correction coefficient is one for all fan speeds.

The source validates the model in open loop against minute-sampled return-water
measurements. Reported NRMSE is below **6%** for every validation data set,
including predictions at least one hour long.

This is substantially stronger than the P43/P44 room-temperature-only
fan-coil evidence.

## 5. What can be derived

The published first-order water-state equation gives the state coefficient:

`lambda = q_w/m_w + U_o/(2 m_w c_w)`.

Therefore a bounded physical water-state time constant is mathematically:

`tau_water = 1/lambda = m_w / (q_w + U_o/(2 c_w))`.

P56 implements this equation.

But the source states that `m_w`, the water mass inside the FCU, is available
from the manufacturer's catalogue. The exact numeric FCC06 `m_w` is **not
reported in the peer-reviewed article layer inspected by P56**.

The cited catalogue is:

Trane, *UniTrane fan coil units*, `UNT-PRC006-E4`, 2010.

A public catalogue mirror confirms the exact document identity and FCC size
family, but P56 did not recover an authoritative exact FCC06 in-coil water-mass
value from the inspected public text surface.

Therefore numeric `tau_water` remains fail-closed until exact `m_w` is
bound.

## 6. Why this does not populate HEM tau_out

The existing P24/P25 method uses one scalar:

`tau_out = emitter/distribution response-time characteristic`.

The FCC06 source instead supplies a physical state-dependent model whose
timescale changes with at least:

- water mass;
- water mass flow;
- fan state through `U_o(x,q_w)`;
- water heat capacity.

P56 therefore refuses:

`tau_water -> HEM tau_out`

without an explicit semantic mapping authority.

Even after exact FCC06 water mass is recovered, P56 would permit calculation
of a **state-dependent FCC06 water-state time constant**, not automatic
replacement of the HEM/EN15316 emitter-class scalar.

A successor may either:

1. establish an explicit mapping from this physical state response to the HEM
   `tau_out` semantics; or
2. establish a direct state-dependent physical fan-coil runtime path that
   bypasses the scalar HEM approximation for this product class.

## 7. Q-B05-004 transition

The old generic fan-coil acquisition residual:

`EXACT_FCU_HEATING_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`

is narrowed to an exact product result:

`RESOLVED_TO_EXACT_FCC06_STATE_DEPENDENT_HEATING_DYNAMIC_RECORD`.

Remaining FCU residuals become:

1. `EXACT_FCC06_WATER_MASS_OR_SOURCE_REPORTED_SCALAR_RESPONSE_TIME_REQUIRED`;
2. `STATE_DEPENDENT_FCU_RESPONSE_TO_HEM_TAU_OUT_MAPPING_OR_DIRECT_RUNTIME_PATH_REQUIRED`.

Independent Q-B05-004 residuals remain:

- `EXACT_SOURCE_NATIVE_A_MINUS15_W50_2D_OPERATING_OR_PERFORMANCE_RECORD_REQUIRED`;
- `EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED`;
- `EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`.

Q-B05-004 therefore remains OPEN.

## 8. Readiness

P56 performs **NO_MECHANICAL_READINESS_UPLIFT**.

- PART_LOAD_MODULATION remains **45%**
- B05 remains **64%**

Reason: P56 replaces an ambiguous evidence-search blocker with a real exact
product dynamic surface, but the canonical scalar hourly path is still not
numerically executable from OBS-grade fan-coil response authority.

A later successor-aware recalibration may score accumulated evidence
separately.

## Sources

- Martinčević, A.; Vašak, M.; Lešić, V. (2019), *Identification of a
  control-oriented energy model for a system of fan coil units*, Control
  Engineering Practice 91, 104100.
  DOI: https://doi.org/10.1016/j.conengprac.2019.07.018
- Public author manuscript:
  https://www.lares.fer.hr/_news/86201/CONPRA_4100.pdf
- Manufacturer catalogue cited by the paper:
  Trane, *UniTrane fan coil units*, UNT-PRC006-E4, 2010.
  Public mirror used only to confirm document identity:
  https://www.yumpu.com/en/document/view/8519587/unitranetm-fan-coil-units

No copyrighted source PDF is committed to the repository.
