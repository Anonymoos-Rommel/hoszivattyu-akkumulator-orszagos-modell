# B05-P29 — CONTROLLER-BOUND DHW DISPATCH

Date: 2026-09-25  
Canonical base: `35a7af6982611502052e465c4b5b8aeafca158e5`

## Purpose

P29 addresses Q-B05-005 without turning controller documentation into a
generic heat-pump rule.

Core boundary:

```
CONTROLLER DISPATCH EVIDENCE
!=
HIGH-TEMPERATURE CAPACITY / INPUT / COP EVIDENCE
```

and:

```
EXACT PRODUCT/CONTROLLER POLICY
!=
CROSS-PRODUCT DEFAULT
```

## Mitsubishi PUZ-WM50VHA(-BS) + FTC6

Exact system binding is supported by the BRE-verified Mitsubishi declaration
for EHPT20X-MHEDW FTC6 packaged cylinder with PUZ-WM50VHA(-BS).

The FTC6 manufacturer manual exposes:
- DHW maximum temperature 40-60 C;
- maximum DHW operation time 30-120 min;
- a 30-120 min DHW-mode restriction after maximum DHW operation time, during
  which space heating has priority and further stored-water heating is
  temporarily prevented;
- simultaneous DHW/heating as an explicit On/Off commissioning setting,
  default Off.

P29 therefore does not assume a universal Mitsubishi ordering.  If the actual
simultaneous-operation setting or post-DHW restriction state is unknown, the
runtime remains Q.  If simultaneous mode is enabled, the controller mode is
known but the heat split is not, so energy allocation remains Q.

Sources:
- SRC-B05-MITSUBISHI-WM50-FTC6-DHW-CONTROL-2026
- SRC-B05-MITSUBISHI-WM50-FTC6-BINDING-2026

## Dimplex LA 2030CP + WPM Touch

The manufacturer Quick Installation Guide explicitly identifies
`LA 2030CP + WPM Touch`.

The WPM Touch operating instructions state that when a DHW request is made
during heating operation, the heat circulating pump is deactivated and the DHW
circulating pump is activated while the heat pump is running.  This is admitted
as bounded controller/hydraulic dispatch evidence for the exact controller
binding.

The LA 2030CP installation instructions publish a heating-water flow limit up
to 70 C.  P29 uses that only as operating-envelope evidence:

```
HIGH-TEMPERATURE CAPABILITY != HIGH-TEMPERATURE COP
```

No capacity, electrical input or COP is created from the temperature limit.

Sources:
- SRC-B05-DIMPLEX-LA2030CP-WPMTOUCH-BINDING-2026
- SRC-B05-DIMPLEX-WPMTOUCH-DHW-CONTROL-2026
- SRC-B05-DIMPLEX-LA2030CP-HIGH-TEMP-2026

## Runtime consequence

The existing generic B05 engine stays fail-closed when simultaneous space and
DHW loads have different required supply temperatures and no explicit
controller state is available.  P29 adds a separate controller-bound contract;
it does not weaken `Q_DHW_PRIORITY`.

A future executable energy allocation must have both:
1. stateful controller/request information for the selected exact system; and
2. admissible product performance at the actually dispatched DHW operating
   temperature.

## Q-B05-005 transition

```
OPEN
->
OPEN_NARROWED_TO_STATEFUL_CONTROLLER_RUNTIME_AND_DHW_HIGH_TEMP_PERFORMANCE
```

Residuals:
- `STATEFUL_DHW_CONTROLLER_RUNTIME_REQUIRED`
- `DHW_HIGH_TEMP_PRODUCT_PERFORMANCE_REQUIRED`

## Readiness

- DHW_MODE: 30% -> 45%
- B05 overall: 64% -> 64%

The uplift reflects real controller evidence on two exact systems, not a claim
of complete hourly DHW energy modelling.
