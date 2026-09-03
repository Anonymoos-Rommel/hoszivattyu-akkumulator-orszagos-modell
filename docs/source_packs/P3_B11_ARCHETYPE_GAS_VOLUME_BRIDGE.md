# B11-P3 — household/archetype gas-volume bridge

Audit date: 2026-09-03
Canonical base: `226cfc76fb91da1ff6c6b477a9839626061f926d`
Issue: #15 — `[B11] Gázkiváltás és importhatás`

## Decision

P3 does **not** allocate the KSH county household-gas sales baseline to census or programme archetypes.

Core rules:

`COUNTY GAS SALES != ARCHETYPE GAS VOLUME`

`USEFUL HEAT != GAS INPUT ENERGY != GAS VOLUME`

`UTILITY CUSTOMER != HEATING CUSTOMER != CENSUS GAS-USING DWELLING != PROGRAMME PARTICIPANT`

The canonical physical bridge is:

`useful space heat [kWh/year] / seasonal gas-appliance efficiency -> gas input energy [kWh/year] -> explicit gas heating value [MJ/m3] -> gas volume [m3/year]`

This direction is chosen because B06 already owns the useful-heat / retrofit physics layer. The KSH P2 county utility baseline remains a reconciliation control rather than an allocation key.

## Authority audit

### B02 population context

KSH Census 2022 WBL011 provides observed heating/fuel population counts. The existing B02 contract records 1,788,022 occupied dwellings in the exclusive network-gas category at the national control query, alongside a separate multi-fuel population. The multi-fuel group cannot be decomposed into gas/non-gas usage without additional evidence.

The materialized WBL011 heating/fuel projection is observed at county × settlement type × construction period × heating mode × heating fuel grain. It must not be joined to the separate envelope projection or to modelled building-type/primary-energy layers without explicit authority.

Therefore B02 is population context, not annual gas-volume authority.

### B06 useful-heat path

B06 already defines `VAR-B06-BASELINE-ANNUAL-SPACE-HEAT` as a modelled annual useful-space-heat input and a post-retrofit annual useful-heat output path. This is a physical energy quantity and is the correct upstream layer for a gas-input conversion.

However, the full real national archetype joint is still Q. P3 therefore provides the conversion contract without claiming that every programme household already has a valid useful-heat value.

### Seasonal gas-appliance efficiency

No canonical Hungarian household/archetype distribution of seasonal gas-appliance efficiency is currently established in the repository.

P3 therefore forbids:

- a universal 0.8/0.9/etc. boiler-efficiency default;
- inferring efficiency from appliance age alone;
- treating a regulatory or product nominal efficiency as an observed household seasonal value;
- replacing missing efficiency with zero or one.

A numeric P3 bridge is blocked when this input is Q.

### Gas heating value

B03 already separates physical gas quality from prices. FGSZ/MVM source gates establish that heating value is point/period specific and that billing uses actual/period-specific values. A single national MJ/m3 constant is not authoritative for programme output.

P3 accepts an explicit heating value only when its period/location and evidence status are attached. The bounded unit test uses scenario values solely to prove arithmetic; it is not a Hungarian calibration.

## County reconciliation boundary

`registry/b11_county_gas_baseline_2024.csv` remains an observed 2024 utility-sales control. It can later test whether an aggregated modelled population is physically plausible, but it cannot be distributed to households by:

- household count share;
- heating-customer share;
- census gas-dwelling share;
- floor area share;
- building-type proxy share;
- primary-energy proxy share.

Any such distribution requires a separately evidenced calibration method.

## End-use boundary

P3 only defines the **space-heating** gas-volume bridge.

It does not yet create:

- DHW gas volume;
- cooking gas volume;
- pilot/standby losses outside the seasonal-efficiency boundary;
- multi-fuel gas share;
- rebound;
- programme participation;
- programme bcm aggregation;
- import valuation.

DHW and cooking remain separate because the KSH P2 total household-gas sales contain all household end uses, while B06 explicitly keeps DHW separate from space heat.

## Executable contract

`modules/B11/gas_volume_bridge_contract.py` requires three explicit physical inputs:

1. useful heat, `kWh/year`;
2. seasonal gas-appliance efficiency, fraction in `(0, 1]`;
3. gas lower heating value, `MJ/m3`.

Missing/non-finite evidence is not zero. `Q` cannot authorize a numeric output. Output status inherits the weakest allowed input status (`SCN` before `DER` before `OBS`).

The arithmetic is dimensionally explicit:

- gas input energy = useful heat / efficiency;
- heating value in kWh/m3 = MJ/m3 / 3.6;
- gas volume = gas input energy / heating value.

## Closure effect

P3 improves the B11 physical architecture but does not establish a real programme gas-volume panel. B11 remains `IN_PROGRESS` and readiness increases only modestly from 15 to 20.

Still open:

- real household/archetype useful-heat population;
- seasonal gas-appliance efficiency evidence;
- programme-aligned gas-quality snapshot;
- multi-fuel decomposition;
- DHW/cooking split;
- rebound;
- programme aggregation;
- B03 wholesale/import valuation;
- Issue #15 acceptance outputs.
