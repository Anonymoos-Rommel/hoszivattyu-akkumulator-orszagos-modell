# Paired-power component on the existing thermal trajectory

`modules/B05/hourly_power_component_reference.py` adds one explicit technical
SCN to the [72-hour thermal reference](V1_033_HOURLY_THERMAL_SERVICE_REFERENCE.md).
It reads that exact admitted case itself, preserving its temperature trajectory,
source hashes, physical UTC hours, thermal requirements and capacity shortfalls.
No alternative household, controller, supply temperature or source labels can be
supplied to this entry point. External radiation remains caller-owned and passes
the existing byte, unit and interval checks; absent radiation gives Q.

At the fixed W55 coordinate, the consumer obtains each separate manufacturer's
MIN, MID, NOMINAL and MAX Q/P pair through the existing bounded source adapter.
It then interpolates input power between the adjacent capacities containing the
required heat: `P = Pa + (q-Qa)/(Qb-Qa) * (Pb-Pa)`. COP follows from `q/P`.
This is a named SCN choice, not a manufacturer control rule or HEM implementation.
The frequency order must hold; reversed capacities, missing support and unequal
input at equal capacity cannot be sorted or averaged into an admitted result.
Exact coincident points retain all supporting modes and source annotations.

The existing exponential thermal path has constant reconstructed heat demand
within each of these hours. Therefore its complete-hour classifications have no
hidden MIN/MAX crossings. This consumer accepts only that pinned case, not an
arbitrary hourly-mean demand series.

With the qualified external inputs, the component reference gives:

| Scope | Hours | Thermal component, kWh | Rating input component, kWh |
|---|---:|---:|---:|
| Supported continuous MIN/MID interpolation | 23 | 50.524661 | 27.287205 |
| Separate full-MAX component during overload | 3 | 13.066667 | 6.669019 |
| Below-MIN requirement | 40 | 70.064635 | Q |
| Zero heating demand | 6 | 0, up to floating-point roundoff | Q |

The overload hours still require an additional 9.028231 kWh of heat, with a
3.064339 kW peak. No backup, reduced service or new indoor-temperature path is
selected. The two electrical subtotals remain separate labelled subsets with
their exact included intervals; they are never returned as period electricity.
Missing middle-mode data blocks the dependent continuous component without
erasing an independently supported MAX component or thermal requirement.

Thirteen continuous hours combine integrated-defrost and unmarked source cells.
Every contributing annotation remains attached to the result. Unmarked does not
mean zero defrost; these numbers are arithmetic on the rating surface, not
weather-realized electricity. No Cdh, extra defrost factor, pump correction or
arbitrary auxiliary duration is added. The 40 cycling hours contain almost half
the prescribed heat requirement and remain a material unresolved part of the
calculation. For comparison, interpolating COP instead of P gives 27.389685 kWh
over the same 23 hours, a 0.376% method sensitivity; it is not the selected rule.

Whole-period rating input, actual electricity, SPF, cycling, auxiliaries,
weather-specific defrost, backup electricity and payback remain null. The output
explicitly disallows complete-load admission to B08/B12. No readiness score,
slice status, national assumption or empirical-validation claim changes. Source
and software checks do not replace measurements of buildings, runtime or networks.

The alternative complete HEM route still needs qualified product test-water and
control metadata, minimum modulation and compatible operating boundaries, plus
verification of the full pinned executable. Available normative defaults do not
supply those missing mappings. The paired-power consumer does not mix in HEM's
different capacity, input or inertia formulas.

Verification includes synthetic boundary and adverse tests, genuine manufacturer
corners, absent/substituted external input, independently replayed source-path
components and exact-content review. The external full panel is not published.
The [previous CI receipt](V1_035_CI.json) remains historical; this change requires
its own final-head hosted aggregate before completion.
