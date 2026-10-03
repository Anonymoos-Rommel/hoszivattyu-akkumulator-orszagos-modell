# V1-033 — bounded hourly thermal and fixed-service capacity reference

Base: `365a28433f5eda976fa00936282a1565922de45a`. This candidate adds one read-only technical scenario, `SCN-HOURLY-TABULA-SFH01-72H-2025-001`, without changing the native seasonal DER or prospective design reference. It does not complete B02/B05/B06 or admit a central national input. Integration appends five method-source metadata rows, B05-D01/B06-D01 research entries and B05/B06 gate notes; slice statuses, accepted artifacts, module status and readiness remain unchanged. The previous V1-032 CI receipt describes its own verified head.

## Result and boundary

The historical TABULA/EPISCOPE 56 m² ambitious-refurbishment template `HU.N.SFH.01.Bel80.ReEx.001.013`, source worksheet row 1241, supplies the geometry and assembly parameters. The finite initial-value problem consumes the observed Budapest 44527 cold block from **2025-02-18 08:00 to 2025-02-21 08:00 UTC**, including nonzero observed global radiation. The exact first-law solution is an **E3 technical SCN**. Numerical/source review does not empirically validate this one-node model or establish that a real household attains its temperature path.

With the declared ideal endpoint-target controller, the 72 hours require **142.6841939588029 kWh** sensible space heat. Continuous target deficit is **2.9735988080497884 K·h**: a rising endpoint target does not imply the target was met throughout the recovery hour. Passive cooldown may exceed the lower endpoint target; there is no cooling controller.

Reconstructing heat from the derivative and losses along that same continuous exponential path yields **three manufacturer-rating capacity gaps**, totaling **9.028230983764495 kWh**, peak **3.064338584419085 kW**. The capacity-covered component is 133.6559629750384 kWh. The three physical interval starts are 2025-02-19, 20 and 21 at 05:00 UTC. These are conditional additional thermal requirements, not a selected backup, equipment size, dispatch plan, realized unmet heat or electric energy.

A separate ideal actuator capped at MAX/W55 evolves its own lower-service state: 142.1057465631467 kWh, 7.3205985768701884 K·h target deficit and six clipped hours. Its smaller delivered heat follows reduced temperature/losses. **This is not an efficiency comparison or equal-service saving.** The fixed-path comparison never substitutes that path for the prescribed one.

## Sources, time and immutable contract

The new manifest pins exact repository building/weather/map bytes and the B05 source contracts/consumers. Its complete bytes are SHA-256 checked by the consumer, including scenario values, source identities, source/cell/units, rights and claim metadata. An edited manifest cannot repin its own authority. Future source/scenario revisions need separate review. The building parameter ledger retains source-native worksheet units, explicitly correcting the known glazing-transmittance metadata error to a dimensionless ratio for use.

The external radiation extract is supplied by its caller, checked for byte count and SHA-256, then validated against all 8,760 canonical weather endpoints. No private filesystem path is embedded in production. No download, materializer, writer or raw-file copy is included. The public API is:

```python
from modules.B06.hourly_thermal_reference import calculate_reference
result = calculate_reference(radiation_path=external_analytical_extract)
```

Calling without a radiation file returns explicit unknown thermal states/totals. A supplied absent/corrupt/substituted file raises, rather than creating a zero-solar scenario. The optional `manifest_path` accepts only exact reviewed bytes. Private numeric/parser helpers support synthetic tests and do not certify alternative sources or scenarios.

Source `ta` is the previous-hour temperature mean, `u` instantaneous endpoint humidity, and `sr` an hourly global-radiation sum in J/cm². `sg` is gamma dose rate, not solar. The assignment of `sr` to the common ending hour is qualified SCN: the schema explicitly says previous hour for `ta`, but does not repeat that phrase for `sr`. Observed global radiation is treated as horizontal for the declared model; no observed DNI/DHI exists. The source endpoint is retained, while all energy joins use the physical **interval start**. One J/cm² is 1/360 kWh/m² or 25/9 W/m² averaged over one hour.

The existing endpoint panel covers the **Europe/Budapest civil year 2025**, from 2024-12-31 23:00 to 2025-12-31 23:00 UTC. It is not exact UTC calendar 2025. Selection uses all 8,689 contiguous 72-hour windows of observed `ta`, earliest tie, before radiation is inspected. This is a dated station selection, not a return-period event, maximum-load guarantee, future climate or national weather weight.

Original authority and preserved hashes are in the manifest: [TABULA workbook](https://episcope.eu/fileadmin/tabula/public/calc/tabula-calculator.xlsx), [TABULA method](https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_CommonCalculationMethod.pdf), [HungaroMet schema](https://odp.met.hu/climate/observations_hungary/hourly/historical/Leiras_automata_oras-HABP_1H_hist-hu.pdf), [manufacturer databook](https://library.mitsubishielectric.co.uk/pdf/download_full/4099), [NOAA solar equations](https://gml.noaa.gov/grad/solcalc/solareqns.PDF), [pvlib Erbs implementation](https://pvlib-python.readthedocs.io/en/v0.16.1/_modules/pvlib/irradiance.html), and Sandia diffuse/reflection references. The versioned pvlib byte download was unavailable; primary implementation reading is recorded, with no fabricated snapshot hash.

Attribution: **IEE Projects TABULA + EPISCOPE (www.episcope.eu)**. **Adatbázis: Meteorológiai Adattár, HungaroMet Nonprofit Zrt.** Raw ZIP/PDF/XLSX, full private radiation panels and full replay results stay external and untracked. There is no source-rights promotion. The manifest identifies original and supplementary research review digests; original research bytes remain frozen. Production admission requires its own exact-content review.

## Finite equations and explicit SCN choices

All non-observed transfers and chosen controls remain machine-visible SCN, including:

- One effective temperature/mass node; 45 Wh/m²K × 56 m² = 2,520 Wh/K, with no empirical inertia calibration
- Source assembly U/resistance arithmetic and stationary attic resistance; full floor conductance against a fixed **10°C ideal reservoir**, not measured soil or a seasonal ground factor
- Source weighted bridges counted once and assigned to outdoor air; constant source-method ventilation
- Constant 3 W/m² internal gains, all internal/window gains entering one node
- Constant within-hour forcing, NOAA midpoint geometry, Erbs modeled diffuse/DNI, isotropic north-plane and ground reflection with albedo 0.2, and transferred fixed source optics/shading
- Local Europe/Budapest 20°C from 06:00–22:00 and 18°C otherwise, initial 20°C, no warm-up or cyclic initial-state assertion
- Nonnegative constant hourly endpoint-target heat and fixed W55 manufacturer coordinate; no emitter-required flow/return implication

With time measured in hours, H in W/K and C in Wh/K:

```text
H_out = 74.88019103262332 W/K
H_lower = 58.188 W/K
C dT/dt = H_out(Ta - T) + H_lower(10 - T) + Q_internal + Q_solar + Q_heat
T_end = T_eq + (T_start - T_eq) exp(-(H_out + H_lower) Δt / C)
C(T_end - T_start) = E_heat + E_internal + E_solar - E_out - E_lower
```

Analytic integration reports each boundary's exchange and the continuous positive target deficit. The fixed-service calculation reconstructs `Q_heat = C dT/dt + H_out(T-Ta) + H_lower(T-10) - Q_internal - Q_solar` at within-hour points and verifies it equals the ideal path's constant command. The fixed boundary exchanges 39.35201061392162 kWh in this example; its fixed-path sensitivity is 4.189536 kWh per reservoir kelvin over 72 hours. Material coupling/applicability evidence remains necessary before a realistic central-model claim.

Opaque-surface solar, sky longwave, multiple rooms, operative-temperature comfort, actual occupancy, emitter/hydraulic states and heat-recovery control are excluded. These are omissions, not claims that the real phenomena are zero. No source annual heat allocation, seasonal nonuniform heating reduction or seasonal ground factor enters this module.

## Unknowns, manufacturer support and verification

The existing manufacturer Q/P interpolation is reused unchanged, with COP derived consistently. Both MAX and MIN support cells retain source identity, availability and exact integrated-defrost annotations. The fixed path has 40 below-MIN, 23 between-MIN/MAX, six zero-demand and three above-MAX hours. There are 38 below-MIN hours in the separate clipped branch. Unshaded cells do not mean zero defrost. W55 is a source coordinate; continuous modulation below source MIN is an ideal thermal actuator assumption.

A missing gain poisons both dependent thermal states for the remaining finite problem. An unsupported capacity coordinate leaves the ideal prescribed path independent, while the capacity-limited state stays unknown thereafter. Fixed-path capacity comparison retains each later known source coordinate but cannot report a complete period total when any required capacity is unknown. Supported subtotals/counts are explicitly labelled. There is no state restart, zero filling, extrapolation or alternate-source substitution.

Actual electricity, SPF, DHW, emitter-required supply, external auxiliaries, cycling/defrost runtime and energy, backup/dispatch/equipment decisions, national weights and equal-service heat savings remain null or unadmitted. Published off/standby/crankcase power terms do not supply actual auxiliary energy without qualified operating times and component boundaries. No national comfort decision, illustrative two-million population or B07 runtime assumption is adopted.

Focused synthetic tests cover equilibrium/independent numerical integration, energy conservation and state continuity, solar unit/closure checks, source and metadata substitutions, duplicate/missing/boundary observations, observed zero versus missing radiation, Q propagation, the fixed-path differential identity, service-reduction interpretation and null actual-energy claims. A separate external-source replay checks the retained raw weather archive, workbook cell values and manufacturer table lineage, reproduces the published numerical witnesses, and records exact candidate/input/log hashes. Existing seasonal/design/map/time-boundary regressions are run without a full suite. These checks validate the declared computation, not real-building or heat-pump performance.
