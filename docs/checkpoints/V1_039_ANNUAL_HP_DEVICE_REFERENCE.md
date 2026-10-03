# V1-039: one complete annual E2 heat-pump device reference

The new consumer connects a native TABULA annual thermal reference, an explicit
useful-to-generator bridge, the WM50 manufacturer map, a qualified provisional
on/off method and the complete UTC 2025 weather chronology. It also compares the
result's timing with the existing original-source-validated B08/B09 balance.
This advances the annual calculation without treating every missing component
measurement as a reason to stop E2 modelling.

## Result and boundary

For the historical 56 m² ambitious SFH01 reference, useful space heat is
5,748.154 kWh/year. The same source system contributes 302.4 kWh of effective
distribution loss, giving 6,050.554 kWh at the heat generator. The declared
device reference consumes 2,472.634 kWh: 2,321.747 kWh active rating input,
68.777 kWh inertia allowance and 82.109 kWh nonoverlapping inactive input.
All 8,760 hours are covered: 6,028 equivalent minimum-stage cycling hours,
72 continuous hours and 2,660 zero-heat hours. The reference has no capacity
shortfall, so it needs no backup selection. Its maximum hourly mean device
input is 1.400314 kW; this is not a subhourly or connection-design peak.

The historical thermal total is preserved and allocated onto observed weather;
it is not called observed or weather-corrected 2025 building demand. The annual
profile is a DER calculation with E2 applicability and explicit validation debt.
Outside-unit pump/controller/emitter electricity remains a separate missing
aggregate. Whole installed-system electricity, physical SPF, household savings
and national programme results remain unadmitted. That boundary does not erase
the complete, usable device-reference profile.

## Reused evidence and named transfers

The existing TABULA seasonal API calculates the native useful heat. Original
workbook system row 3392 supplies 5.4 kWh/m² effective distribution loss and zero
storage loss. Common Method equation 20 adds these effective losses after
usable recovered gains; no recovered pipe heat is subtracted again. Transferring
that source distribution class from its gas system to this fixed-W55 reference
is explicitly E2, with temperature and control applicability debt. The original
mixed gas auxiliary value, 2.8 kWh/m², is not added to the heat-pump input.

Source heat-loss coefficients, nonuniform-heating reduction and source climate
define an equivalent balance temperature of 17.873392°C. Positive degree-hour
weights around that coordinate distribute the annual useful and distribution
heat while preserving their totals. This coordinate is not a thermostat or a
new national comfort choice. The previous E3 72-hour temperature trajectory,
ground-reservoir fixture and 20/18°C schedule are not promoted or reused here.

The manufacturer MIN/MID/NOMINAL/MAX map retains paired Q/P interpolation and
the source's fixed-W55 domain. Below MIN, the minimum-speed stage is modelled as
an equivalent fixed-capacity on/off unit, with d = required heat / MIN heat and
m_stage = 1. The selected HEM/CALCM reference constants are 140 s and 1370 s:

`P_active = P_min * [d + (140/1370) * d * (1-d)]`.

The input retains its manufacturer total-unit rating boundary. It is not
relabeled an observed compressor submeter. The inertia term is already averaged
over the interval and receives no second duty multiplier. At d→1 it vanishes and
joins MIN continuously; at d→0 active input vanishes. A separate 15 W inactive
term covers 1−d, or the whole zero-heat hour. The matched standalone WM50 source
reports equal Poff/PTO/PSB values and zero PCK, so their internal split does not
change this declared aggregate. The rendered source read is retained honestly;
no unavailable original-HTML/PDF hash is invented.

This is a named engineering reduction, not a full HEM port or a certified
Cdh-to-MIN join. The V1-035 exact-join withdrawal and original P59 criterion are
unchanged. All 58 active hours with mixed grey/unmarked source supports retain
that provenance. Unmarked supports do not mean defrost-free operation, and no
universal defrost factor or private cross-product correction is added.

## Exact time and downstream composition

The external weather panel preserves 8,759 historical records and adds the
actual station 44527 observation ending at 2026-01-01T00:00Z. The panel now spans
2025-01-01T00:00Z through 2026-01-01T00:00Z, with no imputation. The original
Hungarian civil-year panel is preserved as a different reporting period.
Recent source documentation confirms UTC timestamps and preceding-hour mean
temperature. Reserved quality fields are not interpreted as pass flags.

The historical comparison calls the existing B08/B09 source reader and reuses
its conservation and recovery accounting. Each hourly mean is explicitly held
over four physical quarters; all 35,040 intervals align and annual energy is
preserved. The reference device's mean input at the historical load peak is
0.902932 kW. Original load, signed generation and source-reference residuals are
unchanged. No reference household count, B01 state, existing-stock subtraction,
programme increment, dispatch or observed-import claim is inferred.

## Evidence and completion

The exact source/method proposal received independent E2 admission before this
implementation. The implementation requires its own exact-content review,
focused guards, configured aggregate and exact-head hosted CI, recorded in the
verification receipt. Local genuine execution separately checks the complete
weather/profile and original-source historical join; source panels remain
external and are not embedded in the public tests or repository.

The manifest records the source facts, defaults, named transfers and E1 upgrade
routes. Aggregate validation or calibrated inference may close relevant debt;
every internal component need not be separately measured. Module readiness,
whole-slice acceptance, national weights, rollout and comfort policy are not
changed by this checkpoint.
