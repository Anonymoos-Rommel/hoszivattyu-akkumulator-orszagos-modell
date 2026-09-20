# B06-P63 — transferable building-state retrofit effect surface

**State:** `Q-B06-007 RESOLVED / PARAMETRIC PHYSICAL SURFACE CONTRACTED / NATIONAL INPUT COVERAGE STILL PARTIAL`

**Canonical base:** `be1165bf7a70099ef636ed7ca47cd8d5fadc3624`

**Implementation date:** 2026-09-20

## 1. Purpose

P63 resolves the question of how annual and design-peak retrofit effects can be
transferred across building types and physical states **without inventing a
generic percentage**.

The answer is not a lookup table.

The canonical transferable object is a **physical calculation method plus an
explicit applicability domain**.

Core boundaries:

`BUILDING TYPE != EFFECT FACTOR`

`ANNUAL EFFECT != PEAK EFFECT`

`TABULA EXAMPLE != HOUSEHOLD OBSERVATION`

`MISSING PHYSICAL INPUT != AVERAGE VALUE`

`OVERLAPPING PHYSICAL CHANGE != SECOND INDEPENDENT SAVING`

## 2. Annual-demand authority — current Hungarian monthly heat balance

Primary method authority:

- 9/2023. (V. 25.) ÉKM rendelet;
- Energiaügyi Minisztérium:
  **Épületek energetikai jellemzőinek meghatározása – számítási módszer**;
- source ID: `SRC-B06-HU-ENERGY-METHOD-2023`.

Public method:
https://kormany.hu/dokumentumtar/epuletek-energetikai-jellemzoinek-meghatarozasa-szamitasi-modszer-2

P63 implements the annual space-heating dimension as twelve explicit monthly
heat balances.

For each month, the physical state carries:

- monthly outdoor temperature;
- annual-average outdoor temperature for the ground-related term;
- direct/unconditioned transmission heat-loss coefficient;
- ground heat-loss coefficient;
- ventilation heat-loss coefficient;
- solar gains;
- internal gains;
- heating gain-utilization factor;
- intermittent-operation correction;
- month hours.

The executable P63 form is:

`Q_trans,m = [H_direct*(Ti-Te,m) + H_ground*(Ti-Te,annual)] * t_m`

`Q_vent,m = H_vent*(Ti-Te,m) * t_m`

`Q_loss,m = f_intermit * (Q_trans,m + Q_vent,m)`

`Q_heat,m = max(0, Q_loss,m - eta_gain*(Q_solar,m + Q_internal,m))`

`Q_heat,annual = sum(Q_heat,m)`

All energy terms are converted consistently to kWh.

No annual consumption ratio is used to generate design peak.

## 3. Peak-demand authority — independent physical design load

The P63 peak dimension remains independent:

`Q_peak = H_design,total * (T_indoor - T_design,outdoor)`

The total design heat-loss coefficient must be explicit/reproducible for the
state. It may be produced by the existing P3 envelope + ventilation +
thermal-bridge route.

Prohibited inputs remain:

- annual kWh converted to kW;
- full-load-hours proxy;
- installed boiler capacity;
- installed heat-pump capacity.

P62 provides the real Hungarian calibration that proves why the dimensions must
remain separate:

- annual net heat: `207172 -> 36687 kWh/a`;
- design peak: `132.35 -> 46.47 kW`;
- annual reduction: about 82.29%;
- peak reduction: about 64.89%.

## 4. Applicability domain

P63 does not transfer an observed percentage from one building to another.

A result is transferable only when the target calculation itself has explicit:

- building type;
- construction period;
- before-state identifier;
- after-state identifier;
- same climate between compared states;
- same indoor-service condition;
- same heated floor area and volume unless the transition explicitly models a
  geometry change;
- monthly physical heat-loss/gain inputs;
- design heat-loss coefficient;
- source references and reproducible binding.

A domain may authorize a method/state axis. It does not supply missing physical
values.

## 5. Hungarian TABULA validation

Source:
`SRC-B06-HU-TABULA-TYPOLOGY-2014`

Public brochure:
https://episcope.eu/fileadmin/tabula/public/docs/brochure/HU_TABULA_TypologyBrochure_BME.pdf

The Hungarian BME / TABULA-EPISCOPE typology provides residential type/age
classes and explicit existing / standard-refurbishment /
ambitious-refurbishment examples.

P63 stores nine source-native annual-heating reference points across three
different Hungarian building-type/state domains:

### Single-family house — SFH.01.Bel80, before 1944

- existing: **320.5 kWh/m2a**
- standard refurbishment: **145.8 kWh/m2a**
- ambitious refurbishment: **102.6 kWh/m2a**

### Multi-family house — MFH.02, 1945–1979

- existing: **136.4 kWh/m2a**
- standard refurbishment: **60.0 kWh/m2a**
- ambitious refurbishment: **38.9 kWh/m2a**

### Industrialized apartment block — AB.03.Ind, 1980–1989

- existing: **89.9 kWh/m2a**
- standard refurbishment: **56.3 kWh/m2a**
- ambitious refurbishment: **37.0 kWh/m2a**

These cases establish that the response changes materially with building
type/state.

They are **validation-only**:

- `usable_for_engine = NO`;
- no TABULA annual percentage is copied into the runtime;
- no national prevalence is inferred;
- no example building is relabelled as household observation.

The brochure itself treats the example buildings as illustrative/modelled and
not a substitute for an individual building audit.

## 6. Why this is a surface rather than a factor table

The same intervention name can produce different physical effects because the
before state differs.

For example, external-wall insulation depends on:

- original wall U-value;
- post-retrofit wall U-value;
- actual wall area;
- boundary/correction conditions;
- climate;
- ventilation/service state;
- gains.

Therefore P63 represents the mapping:

`physical before state + physical after state + applicability domain -> annual effect, peak effect`

not:

`building label + intervention name -> fixed percentage`.

## 7. Double-count prevention

Every P63 intervention declares the broad physical channels it changes:

- `TRANSMISSION`;
- `GROUND_TRANSMISSION`;
- `VENTILATION`;
- `SOLAR_GAIN`;
- `THERMAL_DYNAMICS`.

The gate independently infers changed channels from before/after states and
requires exact agreement with the declaration.

Within a sequential B06 run, an already-claimed P63 physical channel cannot be
claimed again by a later P63 intervention.

Example:

- window replacement changes transmission **and** ventilation;
- a later airtightness package also claims ventilation.

Those two effects cannot be multiplied as independent percentages. They must be
represented as one combined state transition, or otherwise separated by a
physically non-overlapping evidence model.

Each later P63 transition must also start from the **current sequential annual
and peak state**, not the original S0 baseline.

## 8. Runtime authority

For real `OBS/DER` numeric intervention effects, B06 now admits exactly one of:

1. **P62 linked before/after evidence**
   - bounded real/project case;
2. **P63 parametric physical surface**
   - record/archetype-specific DER from explicit physical states.

Both at once are rejected as `MULTIPLE_EFFECT_AUTHORITIES`.

P63 physical-surface output is `DER`, not `OBS`.

A P63 intervention is rejected when:

- the applicability domain does not contain the building/state;
- climate or service changes silently between before/after;
- physical changes are undeclared;
- physical-change keys overlap a prior P63 intervention;
- the P63 before-state annual or peak does not match the current sequential B06
  state;
- supplied intervention fractions do not equal the independently recalculated
  P63 fractions.

## 9. What P63 resolves

P63 resolves **Q-B06-007 as a methodology/transferability blocker**.

The project now has an executable, fail-closed way to calculate a
building-type/state-dependent annual + peak effect without using a universal
percentage.

## 10. What P63 does not claim

P63 does not create:

- a national household physical-input dataset;
- a national distribution of wall/window/roof U-values;
- national renovation prevalence;
- a fixed saving factor for any intervention family;
- realized completion evidence;
- a replacement for P60/P62 record evidence;
- a direct household inference from TABULA.

Missing record/archetype physical inputs remain `Q`.

Therefore:

`TRANSFER FUNCTION CONTRACTED != NATIONAL INPUT COVERAGE COMPLETE`

## 11. Search / evidence trail

P63 reviewed:

- the current Hungarian building-energy calculation method and monthly climate
  inputs;
- the existing B06 P3 design-load implementation;
- Hungarian TABULA/EPISCOPE residential type-age/refurbishment variants;
- the P62 Zalavár real-building paired calibration.

TABULA was retained only as an applicability/shape validation source because
its example buildings are modelled and explicitly non-representative.

No generic percentage source was promoted, because doing so would violate the
programme intent and reintroduce double counting.
