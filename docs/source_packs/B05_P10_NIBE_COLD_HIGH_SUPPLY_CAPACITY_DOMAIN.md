# B05-P10 — NIBE cold high-supply capacity-domain evidence

## Purpose

B05-P10 narrows the residual product-domain blocker after P7 and P9 by adding
a third manufacturer whose source-native documentation exposes continuous
heating-capacity curves across the Hungarian P9 cold-stress temperature range
at W35, W45 and W55.

Core boundaries:

`CAPACITY CURVE != CAPACITY / INPUT / COP PERFORMANCE TRIPLE`

`OPERATING DOMAIN != EXACT OPERATING POINT`

`GRAPH DOMAIN COVERAGE != DIGITIZED EXACT PERFORMANCE VALUE`

`DEFROST EXCLUDED != WINTER RUNTIME INCLUDING DEFROST`

`SECOND-MANUFACTURER CAPACITY COVERAGE != CROSS-MANUFACTURER COMPLETE PERFORMANCE ENVELOPE`

P10 does not digitize capacity values from a plotted curve and does not infer
electrical input or COP from the curve.

## 1. Source-native NIBE evidence

The official NIBE S2125 installer manual contains a section titled
"Power during heating operation".

For both S2125-8 and S2125-12 it publishes maximum/minimum heating-capacity
curves as functions of outdoor temperature for:

- flow temperature 35 C;
- flow temperature 45 C;
- flow temperature 55 C.

The plotted outdoor-temperature domain extends well below the P9 cold-stress
lower endpoint. P10 uses the graph only as source-native evidence that the
capacity curve exists over the required cold domain. No plotted kW value is
converted into a canonical numeric operating point.

The same manufacturer section explicitly states that the curves are for
continuous operation and that defrosting is not included.

Therefore the capacity-domain evidence has an explicit runtime boundary.

## 2. P9 stress-domain comparison

P9 materialized the five-station empirical 10-year coldest-72h-mean envelope:

`-13.331944 .. -9.644444 C`

The NIBE W35, W45 and W55 continuous heating-capacity curves all cover that
temperature interval.

P10 therefore qualifies:

- second/third-manufacturer cold W35 capacity-domain coverage;
- cold W45 capacity-domain coverage;
- cold W55 capacity-domain coverage.

This is a domain-coverage statement only.

## 3. Complete performance-triple boundary

The same NIBE technical table provides complete source-native
capacity / electrical-input / COP triples at standard coordinates including:

- A-7/W35;
- A2/W35;
- A2/W45;
- A7/W35;
- A7/W45.

Those tabulated points confirm that the manufacturer distinguishes thermal
capacity, input power and COP.

However, the table does not provide a complete capacity/input/COP triple at the
P9 cold-stress endpoint for W35, W45 or W55.

Therefore P10 must not convert the continuous capacity curves into a complete
cold COP surface.

The residual evidence gaps become more precise:

- `SECOND_MANUFACTURER_COLD_W35_COMPLETE_TRIPLE_REQUIRED`;
- `COLD_W45_TOTAL_INPUT_COP_SURFACE_REQUIRED`;
- `COLD_W55_TOTAL_INPUT_COP_SURFACE_REQUIRED`;
- `BELOW_MINUS15_W35_REQUIRED_IF_HOURLY_EXTREME_EVENT_SIMULATION_IS_IN_SCOPE`.

## 4. Defrost boundary

The NIBE manual states that defrosting is not included in the continuous
capacity curves.

Therefore:

`NIBE CONTINUOUS CAPACITY CURVE != DEFROST-INCLUSIVE WINTER ENERGY MODEL`

P10 does not change Q-B05-003 and does not apply a hidden defrost penalty.

## 5. Effect on Q-B05-001

Q-B05-001 remains `OPEN_NARROWED`.

P10 removes the ambiguity over whether another relevant manufacturer can
physically expose W35/W45/W55 capacity across the P9 mean cold-stress domain.

What remains missing is no longer generic cold high-supply capacity-domain
coverage. The main missing evidence is complete source-native total electrical
input/COP information at the cold coordinates needed for a bounded
cross-manufacturer performance envelope.

No product-specific sizing decision is authorized by P10.

## 6. Readiness effect

B05 module readiness remains **64%**.

P10 strengthens the evidence surface but does not manufacture a percentage
uplift because:

- the complete cold capacity/input/COP surface remains incomplete;
- defrost remains Q;
- part-load/cycling remains partial/Q;
- DHW priority remains partial/Q;
- national physical-demand coupling remains independent.

## Source

### SRC-B05-NIBE-S2125-IHB

NIBE S2125 official installer manual.

Manufacturer source:
https://installer.nibe.eu/download/18.69d23679185eaf109d92e22/1676544183097/S2125-IHB-631676-1.pdf

Role:

- source-native continuous W35/W45/W55 heating-capacity domain;
- explicit continuous-operation boundary;
- explicit statement that defrosting is not included;
- tabulated standard-point capacity/input/COP evidence used only to confirm
  metric semantics, not to invent cold performance values.
