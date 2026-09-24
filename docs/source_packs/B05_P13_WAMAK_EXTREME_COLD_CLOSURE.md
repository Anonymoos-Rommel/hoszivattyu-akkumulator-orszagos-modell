# B05-P13 - WAMAK observed hourly extreme cold performance closure

## Purpose

B05-P13 resolves the last Q-B05-001 physical performance-domain residual by
admitting a manufacturer performance surface that covers the observed B05
72-hour event minimum of -21.9 C at W35/W45/W55 without extrapolation.

Core boundaries:

`OBSERVED EVENT MINIMUM != FUTURE DESIGN MINIMUM`

`OPERATING LIMIT != PERFORMANCE POINT`

`SOURCE-INCONSISTENT TRIPLE != OBS COMPLETE POINT`

`SOURCE-NATIVE CAPACITY + COP -> ELECTRICAL INPUT DER WHEN SOURCE INPUT FAILS CONSISTENCY`

`PHYSICAL PRODUCT-MAP CLOSURE != MARKET SHARE != PROCUREMENT AUTHORIZATION`

P13 does not convert the historical -21.9 C observation into a future
probability or national design-temperature rule.

## 1. Weather target

The canonical B05 observed 72-hour extreme cold event is:

`B05-EXTREME-OBSERVED-72H-15310`

Its observed minimum outdoor temperature is:

`-21.9 C`

The existing coverage materialization explicitly recorded that the previous
-15 C W35 performance floor left 37 of the 72 event hours below the admitted
domain.

P13 targets this exact historical physical-domain residual only.

## 2. Manufacturer authority

The current WAMAK AWK 35 EVI manufacturer product sheet identifies:

- model: AWK 35 EVI;
- air-to-water heat pump;
- heating performance data version: v2024.010-AW;
- product sheet version: 2024/25;
- source operating limit: -22 C;
- heating water operating limit: 65 C.

The manufacturer states that its heat pumps are regularly tested/certified
according to EN 14511:2018 and EN 14825:2018.

P13 uses the product sheet performance tables as the numeric authority.

## 3. Extreme-domain source corners

### A-22/W35

Manufacturer detailed table:

- Qh = 19.2 kW;
- P = 8.8 kW;
- COP = 2.18.

The triple is internally consistent within the existing B05 tolerance and is
admitted as OBS.

### A-10/W35

- Qh = 26.5 kW;
- P = 8.8 kW;
- COP = 3.02.

Admitted as OBS.

### A-10/W55

- Qh = 28.2 kW;
- P = 13.9 kW;
- COP = 2.04.

Admitted as OBS.

### A-22/W55 - explicit source inconsistency

The detailed table publishes:

- Qh = 21.2 kW;
- P = 13.0 kW;
- COP = 1.51.

But:

`21.2 / 13.0 ~= 1.63`

which exceeds the canonical B05 manufacturer-rounding tolerance relative to
the published COP 1.51.

Therefore the published 13.0 kW field is **not admitted as a complete-point
electrical-input observation**.

The same manufacturer sheet's ErP medium-temperature section independently
reports at the operation-limit temperature:

- Pdh = 21.2 kW;
- COPd = 1.5;
- TOL = -22 C.

This corroborates the source-native capacity/COP relationship at the same
temperature and application class.

P13 therefore preserves the detailed-table source observation separately and
materializes the canonical A-22/W55 point as:

- capacity = 21.2 kW OBS;
- COP = 1.51 OBS;
- electrical input = 21.2 / 1.51 = 14.039735099 kW DER;
- canonical complete point evidence status = DER.

No silent correction of the source's 13.0 kW field is made.

## 4. Complete admitted rectangle

The canonical AWK 35 EVI map has complete admissible corners at:

- A-22/W35;
- A-22/W55;
- A-10/W35;
- A-10/W55.

Thus the admitted rectangle is:

`outdoor -22..-10 C x supply 35..55 C`.

The observed event minimum:

`-21.9 C`

lies inside the outdoor domain.

W35, W45 and W55 lie on or inside the supply domain.

The existing B05 bounded bilinear engine can therefore evaluate the observed
-21.9 C extreme at W35/W45/W55 without extrapolation.

Exact source coordinates may be OBS or DER according to the point-level
evidence boundary above; W45 and -21.9 C interior evaluations are DER.

## 5. Effect on Q-B05-001

P12 left one conditional physical-map residual:

`BELOW_MINUS15_W35_REQUIRED_IF_HOURLY_EXTREME_EVENT_SIMULATION_IS_IN_SCOPE`.

P13 resolves that residual for the canonical observed hourly extreme event.

Q-B05-001 therefore becomes:

`RESOLVED_FOR_PHYSICAL_MODEL`.

This closure means the declared B05 physical performance-map acquisition
question has sufficient source-supported product surfaces for:

- the P9 reference mean cold-stress domain;
- W35/W45/W55 high-supply operation;
- the canonical observed -21.9 C event minimum.

It does not mean that every product is qualified at every coordinate.

## 6. Remaining independent runtime questions

P13 does not close:

- Q-B05-003 defrost accounting;
- Q-B05-004 modulation/cycling/part-load degradation;
- Q-B05-005 DHW priority;
- market-share weighting;
- procurement eligibility.

The WAMAK sheet mentions reversible/enhanced defrost features, but does not
provide a separable point-level defrost-energy accounting series admitted by
B05.

## 7. Readiness

B05 module readiness remains **64%**.

P13 resolves a critical product-domain blocker but does not mint a module
percentage uplift because independent runtime gates remain.

Component percentages are also left unchanged pending a separate readiness
recalibration slice.

## Source

### SRC-B05-WAMAK-AWK35-EVI-2026

WAMAK AWK 35 EVI manufacturer product sheet.

https://www.wamak.eu/wapps/product-sheets/combine.php?code_id=WA001448&coverpg=&descriptmrktadv=&lang=en-GB

Role:

- source-native extreme-cold W35/W55 capacity, input and COP evidence;
- product identity;
- operating-envelope control;
- explicit source inconsistency at A-22/W55 preserved fail-closed.

The manufacturer PDF is referenced only and is not stored in the repository.
