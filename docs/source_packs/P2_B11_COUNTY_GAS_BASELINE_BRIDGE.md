# B11-P2 — KSH county household-gas baseline bridge

Audit date: 2026-09-03
Canonical base: `a51761e56c5b31170be0cc43ddb4a7e1950ff4dd`
Issue: #15

## Decision

P2 materializes a source-native 2024 county/capital household-gas utility baseline from KSH Területi statisztikai évkönyv 2024, table 6.10.

Core rule:

`KSH UTILITY CUSTOMER != KSH HEATING CUSTOMER != CENSUS GAS-USING DWELLING != PROGRAMME PARTICIPANT`

The table directly publishes, by county/capital:

- household gas-consumer count;
- of which gas-heating consumer count;
- household gas sales in thousand m3;
- monthly m3 per household consumer.

National source controls are:

- household consumers: `3,241,811`;
- heating consumers: `3,022,115`;
- household gas sold: `2,654,311 thousand m3`;
- monthly use per household consumer: `68.2 m3`.

The 20 county/capital rows sum exactly to both consumer-count controls. Their separately rounded gas-volume rows sum to `2,654,310 thousand m3`, one thousand m3 below the national source control. KSH states that component data are rounded independently, so P2 preserves this as source-native rounding rather than forcing a row adjustment.

## Canonical artifact

`registry/b11_county_gas_baseline_2024.csv`

The registry stores only source-native county/capital values and lineage. It does not allocate gas to programme households.

`modules/B11/county_baseline_contract.py` validates:

- the exact 20 county/capital codes;
- uniqueness and OBS lineage;
- `heating_consumers <= household_consumers`;
- exact national consumer-count reconciliation;
- gas-volume reconciliation within 1 thousand m3 source-rounding tolerance;
- reconciliation of the derived weighted monthly average to the published 68.2 m3 control.

## Relationship to B02

B02 WBL011 provides a 2022 observed population projection by county × settlement type × construction period × heating mode × heating fuel. It does not provide annual gas volume.

The P2 utility baseline therefore does **not** join or distribute the 2024 gas volume across WBL011 cells. In particular:

- `FUEL11` alone is not total gas-using housing stock;
- multi-fuel categories may contain gas users;
- census dwelling counts are not utility account counts;
- a heating-consumer account is not a programme-eligible dwelling;
- year 2022 census population and year 2024 utility volumes cannot be silently treated as same-period household records.

A later bridge requires explicit allocation authority/calibration evidence.

## End-use boundary

The KSH 6.10 `heating consumers` count does not provide gas volume used specifically for space heating. Household gas sales can also include DHW/cooking and other household uses. P2 therefore does not derive a heating-volume fraction.

`HEATING_CUSTOMER_COUNT != HEATING_GAS_VOLUME`

This leaves the P1 `replaceable_end_use_fraction` input Q for real programme calculations.

## Legacy programme numbers

P2 does not use or calibrate to the prior shorthand:

- 2 million households;
- 1,500 m3/year per household;
- 3 bcm/year displacement.

Those values remain policy/scenario hypotheses only, not observed baselines.

## Licensing

KSH table content is reusable under CC BY 4.0 subject to attribution. Source: Központi Statisztikai Hivatal (KSH).

Official source:

https://www.ksh.hu/evkonyvek/2024/teruleti-statisztikai-evkonyv-2024/pdf/terstat_2024_6.pdf

## Remaining blockers

P2 still does not prove:

- exact participating household population;
- household/archetype annual gas-volume bridge;
- gas-specific space-heating/DHW/cooking split;
- real retrofit reduction factors;
- rebound calibration;
- residual programme gas use;
- programme bcm aggregation;
- wholesale/import-value effect from B03.

B11 therefore remains `IN_PROGRESS`. P2 raises readiness only because a real observed regional physical baseline is now materialized and machine-validated; it does not mint a programme result.
