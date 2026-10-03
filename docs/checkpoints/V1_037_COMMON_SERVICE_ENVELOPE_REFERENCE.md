# Three envelope states at identical modelled service

`modules/B06/common_service_envelope_reference.py` compares the source-defined
existing, standard and ambitious states of the same56m² TABULA example. Workbook
rows1239–1241 supply the three parameter sets. The baseline has zero retrofit
fractions and R_Measure terms; its existing0.3m²K/W attic resistance remains.
Original U-values, geometry and common service controls are checked directly.
These are historical reference alternatives, not observed paired renovations.

The consumer preserves the exact temperature trajectory, weather/radiation,
initial condition and fixed10°C lower reservoir of the
[72-hour thermal reference](V1_033_HOURLY_THERMAL_SERVICE_REFERENCE.md).
Each package changes its own physical insulation/window, infiltration and bridge
parameters. Baseline glazing transmittance is0.75; both retrofit alternatives use
0.6. The calculation retains that change in solar gains rather than applying the
post-state gains to the baseline. No seasonal heating-adjustment factor or annual
source output is used to distribute heat into hours.

For each state, required power is reconstructed from the first law on the same
prescribed path: storage change plus outdoor/lower-boundary exchange minus gains.
Because the shared trajectory is exponential within each hour, the other states'
demand is generally `a + b exp(-kt)`, not an hourly constant. The consumer integrates
that curve and its positive excess over the unchanged W55 source rating, checking
endpoints and every internal capacity crossing. Cooling requirements cannot be
clipped into heating savings. Exact equality with capacity has zero excess time.

With the pinned external radiation input, the finite SCN gives:

| Historical source state | Required heat, kWh | Additional heat beyond source MAX, kWh | Peak additional kW | Above-MAX duration, h |
|---|---:|---:|---:|---:|
| Existing |430.734253|98.557854|8.082835|56.021261|
| Standard |209.628036|12.358225|4.227340|3|
| Ambitious |142.684194|9.028231|3.064339|3|

The baseline crosses capacity76.538seconds into the interval starting
2025-02-19 22:00UTC. Its hourly mean would miss that brief excess. The ambitious
state reproduces the existing thermal/capacity reference. Conditional heat
reductions from the existing state are221.106216 and288.050059kWh for the two
complete packages. Independent percentage savings are never added together.

These figures are conditional useful-heat requirements and source-capacity
residuals over one declared cold block. They do not establish actual renovation
savings, annual demand, avoided gas, equipment selection or served backup heat.
All existing geometry/applicability warnings remain attached. Missing radiation
propagates unknown thermal states and totals; missing source capacity leaves
supported heat visible while blocking the dependent complete capacity result.

Electricity, SPF and payback remain unavailable. The varying baseline curves
cannot enter the [constant-hour partial electrical consumer](V1_036_PAIRED_POWER_COMPONENT_REFERENCE.md)
as if they were its pinned inputs. No national policy, empirical validation,
readiness score or research-slice acceptance changes. Source/software verification
does not replace measurements of buildings, operation or networks.

The qualification independently checked255 relevant original workbook cells and
all216 state-hours using direct physical integration, quadrature and root finding.
Implementation tests additionally cover exact/near capacity, crossings in both
directions, interval partitioning, cooling rejection, original optics/resistance,
source identity and unknown propagation. The prior [CI receipt](V1_036_CI.json)
is historical; this change requires its own exact-head hosted aggregate.
