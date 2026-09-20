# B02-P62 — EHI surface-heating presence band and design-temperature scenario calibration

**State:** `Q-B02-004 OPEN / CURRENT EXTERNAL SURFACE-PRESENCE BAND MATERIALIZED / EXCLUSIVE EMITTER MIX STILL Q`

**Canonical base:** `141846551a56087056af08bdc5566788a4842e2c`

**Research / implementation date:** 2026-09-20

## 1. Purpose

P61 repaired the decision layer:

`CURRENT EMITTER MIX != TECHNICAL ELIGIBILITY PRECONDITION`

and left Q-B02-004 as a programme-sufficiency gap affecting:

- seasonal COP;
- emitter retrofit quantity;
- KEEP / UPSIZE / CHANGE / ADD / REPLACE shares;
- CAPEX;
- procurement and installation capacity.

P62 asks the next narrower question:

> Is there a current, country-specific, externally published quantitative constraint on Hungarian surface-heating prevalence that can bound the emitter-population model without inventing a point estimate?

The answer is **yes, as a bin**, not as an exact share.

## 2. Primary source

Source ID:

`SRC-B02-EHI-HMR-2024-SURFACE-PENETRATION`

Authority:

Association of the European Heating Industry (EHI), *Heating Market Report 2024*.

Public PDF:

`https://ehi.eu/wp-content/uploads/2025/04/HMR2024_web.pdf`

Exact relevant locators:

- PDF page 26 / section 1.8 — surface heating and cooling;
- PDF page 27 / section 1.9 — radiators;
- PDF page 59 / Figure 50 — surface heating & cooling penetration (% apartments);
- PDF page 59 / Figure 51 — surface heating & cooling penetration (% houses).

The country classification is encoded by map colour, so P62 does not rely only on PDF text extraction. Figure 50 and Figure 51 were visually inspected from the rendered PDF page.

## 3. Screenshot-verified Hungarian band

EHI defines four penetration categories:

- `<10%` — Very Low Penetration;
- `10% to 33%` — Low Penetration;
- `33% to 66%` — Medium Penetration;
- `>66%` — High Penetration.

On the rendered EHI 2024 maps, Hungary is coloured in the **Medium Penetration** category for both:

1. apartments;
2. houses.

P62 therefore materializes:

`HUNGARY_APARTMENTS_SURFACE_PRESENT in [0.33, 0.66]`

and:

`HUNGARY_HOUSES_SURFACE_PRESENT in [0.33, 0.66]`.

The bounds are **category boundaries**, not observations that Hungary equals either endpoint.

Hard rule:

`BINNED CLASSIFICATION != POINT ESTIMATE`.

Therefore P62 does not create:

- 49.5%;
- 50%;
- any other midpoint;
- any synthetic confidence interval inside the EHI bin.

## 4. Presence is not an exclusive emitter share

The EHI quantity is **surface heating & cooling penetration**, i.e. presence of that technology in the relevant dwelling/building category.

It does not publish, for Hungary:

- surface-only share;
- radiator-only share;
- radiator + surface mixed share;
- fan-coil share;
- other-emitter share.

Therefore:

`SURFACE_PRESENT != SURFACE_ONLY`

and:

`RADIATOR_SHARE != 1 - SURFACE_PRESENT`.

A dwelling can contain both radiators and surface heating.

The EHI band also cannot be silently conditioned onto:

- non-district hydronic dwellings;
- gas-boiler dwellings;
- P21 `FAMILY_HOUSE`;
- P21 `MULTI_DWELLING`.

The EHI labels `houses` and `apartments` are retained source-native until an explicit mapping/denominator bridge is admitted.

## 5. Relation to existing Hungarian evidence

### 5.1 Gas convectors

P39 remains the admitted calibrated national gas-convector branch.

It is independent of the EHI surface-presence band and is not subtracted from that band without an explicit joint model.

### 5.2 KSH / P21 building-stock controls

P15/P21 provide the canonical Hungarian occupied-stock and calibrated building-type surfaces.

P62 does not yet map EHI `houses/apartments` to P21 `FAMILY_HOUSE/MULTI_DWELLING`.

That missing mapping is now explicit:

`KSH_DENOMINATOR_BRIDGE`.

### 5.3 NÉER2

The NÉER2 realised N=2029 technical survey remains the historical representative engineering calibration surface.

EHI gives P62 a newer external prevalence bin; NÉER2 remains useful for covariance/typology structure and historical validation.

### 5.4 Energiaklub prior

P61 retained the qualitative Hungarian prior that central hydronic heating is predominantly radiator-based while surface systems are less common.

P62 does not force that qualitative statement into a numeric radiator share.

The coexistence of:

- a 33–66% surface-presence band; and
- a qualitative radiator-dominance statement

is not necessarily contradictory because surface heating may coexist with radiators in mixed systems.

## 6. Design-temperature engineering references

EHI 2024 section 1.8 states that surface heating systems can operate efficiently at low temperatures around:

`35 / 28 °C`.

P62 records this as:

`SURFACE_HEATING_DESIGN_REFERENCE = 35/28 °C`.

This is **engineering-method/scenario authority**, not a Hungarian population distribution.

Section 1.9 states that modern radiators can operate at medium-to-low temperatures, typically:

`55 °C or lower`

while traditional radiator systems used approximately:

`70–80 °C` water temperature.

P62 therefore has three source-supported engineering temperature classes:

1. surface systems: approximately `35/28 °C`;
2. modern low-temperature-capable radiators: supply typically `<=55 °C`;
3. traditional radiator systems: approximately `70–80 °C` supply context.

But:

`TEMPERATURE CLASS EXISTS != HUNGARIAN POPULATION WEIGHT KNOWN`.

No EHI source provides the Hungarian population share of modern versus traditional radiator systems.

## 7. What P62 materially closes

Before P62, the population residual was broadly:

`NON_DISTRICT_HYDRONIC_EMITTER_MIX + DESIGN_TEMPERATURE_DISTRIBUTION`.

P62 closes one part of that uncertainty:

`CURRENT EXTERNAL HUNGARY SURFACE-PRESENCE BOUND = AVAILABLE`.

The remaining emitter-mix residual is now more specific:

1. `KSH_DENOMINATOR_BRIDGE`
   - map EHI houses/apartments to the canonical P21 population without assuming equivalence;

2. `MIXED_SYSTEM_OVERLAP`
   - estimate how many dwellings contain both radiators and surface heating;

3. `OTHER_EMITTER_SHARE`
   - retain fan-coil / other hydronic possibilities instead of forcing a binary radiator/surface split.

The design-temperature residual becomes:

4. `DESIGN_TEMP_POPULATION_WEIGHTS`
   - population weights across source-supported temperature/emitter classes.

Therefore Q-B02-004 remains `OPEN`.

## 8. Scenario use allowed now

For programme sensitivity only, downstream work may use the exact EHI bin edges as external scenario bounds:

- low-surface validation edge = `0.33`;
- high-surface validation edge = `0.66`.

These values remain:

`DER / EXTERNAL_BINNED_VALIDATION`

and not:

`OBS household prevalence`.

No midpoint is canonical.

If a downstream model chooses an interior SCN point, that point must be explicitly labelled `SCN` and cannot be described as EHI's estimate.

## 9. Machine-readable contract

`registry/b02_p62_ehi_surface_presence_band.csv` freezes:

- houses and apartments bins separately;
- exact source/category boundaries;
- population-use restriction;
- programme sensitivity permission;
- forbidden complement/point-estimate inference;
- engineering temperature references;
- remaining blockers.

## 10. Non-claims

P62 does not claim:

- 33% or 66% is the actual Hungarian share;
- 49.5% is an estimate;
- surface heating is exclusive;
- the non-surface remainder is radiators;
- houses equal P21 FAMILY_HOUSE;
- apartments equal P21 MULTI_DWELLING;
- EHI gives a Hungarian design-temperature distribution;
- Q-B02-004 is resolved;
- B02 readiness should increase.

## 11. Next logical slice

The next high-value task is no longer a generic emitter search.

It is:

`EHI HOUSE/APARTMENT BAND -> CANONICAL KSH/P21 POPULATION BRIDGE`

plus:

`MIXED-SYSTEM OVERLAP / OTHER EMITTER CONTROL`.

If those can be bounded, the exclusive/overlapping emitter-population envelope can be built.

After that, the remaining design-temperature problem is to weight the already source-supported engineering classes rather than inventing temperature levels from scratch.
