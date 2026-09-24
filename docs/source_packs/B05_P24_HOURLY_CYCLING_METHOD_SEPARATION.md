# B05-P24 - hourly cycling method separation

## Purpose

P23 left:

`CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED`.

The tempting shortcut would be to interpolate the certified Cdh values across
outdoor temperature and use that as an hourly physical runtime correction.

P24 rejects that shortcut.

## 1. What the Cdh evidence actually supports

The EN14825/DEAP path used in P18 treats Cdh as part of a standard/bin
calculation. The official SEAI methodology applies the to-water equation at
defined calculator bins:

`COPbin = COPd * CR / (Cdh * CR + (1 - Cdh))`.

Therefore B05 retains:

- exact certified Cdh bins;
- exact-bin standard-method COPbin;
- audit comparison against product certification.

It does not infer a continuous `Cdh(T)` field.

## 2. Current hourly-method authority

The current UK Home Energy Model technical methodology is:

- HEM-TP-12;
- version 3.0;
- issue date January 2026;
- HEM 1.0.

It explicitly explains that EN14825 test data are fixed-condition measurements
and are combined with BS EN 15316-4-2 calculations to model a specific dwelling
and timestep.

For variable-capacity heat pumps, on/off operation occurs when load ratio is
below the minimum continuous load ratio.

The hourly/timestep on/off correction is a separate transient-power term:

`P_onoff = P_min_comp * tau_eq * LR * (1 - LR) / tau_out`.

Where:

- `P_min_comp` is compressor power at minimum continuous load;
- `LR` is timestep load ratio;
- `tau_eq` is the heat-pump on/off transient characteristic parameter;
- `tau_out` is the emitter/distribution response-time characteristic.

**Cdh is not an input to this hourly equation.**

## 3. Method separation

P24 therefore defines two non-interchangeable tracks.

### Track A - EN14825/DEAP standard-bin validation

Allowed:

- exact certified Cdh bin;
- exact or otherwise qualified COPd/capacity at that bin;
- P18 COPbin equation.

Forbidden:

- linear Cdh interpolation;
- nearest-neighbour Cdh assignment;
- calling the standard-bin result the generic hourly physical penalty.

### Track B - generic hourly physical runtime

Allowed:

1. compute operating-condition capacity/COP for the timestep;
2. determine load ratio;
3. compare against minimum continuous load ratio;
4. if below the minimum, use the separate on/off-transient method.

Forbidden:

- Cdh as a universal hourly multiplier;
- COP x Cdh;
- silently importing a UK/default transient parameter as product OBS.

## 4. Executable P24 contract

`exact_cdh_bin_lookup()` returns Cdh only on an exact supported bin.

A non-bin hourly temperature returns:

`Q / NO_EXACT_CDH_BIN`.

This is deliberate. The generic hourly runtime does not need that Cdh value.

`onoff_inertia_power_kw()`:

- returns zero if load ratio is not below the minimum continuous load ratio;
- returns Q if transient parameters are not yet qualified;
- evaluates the HEM/EN15316-style transient term only when all inputs are explicit.

## 5. Residual transition

`CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED`
->
`RESOLVED_BY_METHOD_SEPARATION_NO_CDH_INTERPOLATION`.

New runtime residual:

`HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED`.

Q-B05-004 becomes:

`OPEN_NARROWED_TO_DOMAIN_GAPS_AND_HOURLY_ONOFF_PARAMETERS`.

Remaining residuals:

1. `MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`;
2. `DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`;
3. `HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED`.

## 6. Why readiness does not rise

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

The method ambiguity is now removed, but numeric hourly cycling energy remains
fail-closed until the transient time parameters and emitter mapping have a
project-authoritative treatment.

## Sources

UK DESNZ HEM-TP-12 v3.0:
https://assets.publishing.service.gov.uk/media/69a6cbe7723a61518b9f1395/hem-tp-12-heat-pump-methodology.pdf

SEAI DEAP Cdh methodology:
https://www.seai.ie/sites/default/files/publications/DEAP-Heat-pumps-consultation.pdf
