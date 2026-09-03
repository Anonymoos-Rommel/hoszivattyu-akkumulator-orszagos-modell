# B11-P1 — Physical gas-displacement baseline and fail-closed contract

Audit date: 2026-09-03
Canonical base: `5274acf442d1d37de0ba29d52378875f7826126f`
Issue: #15 — `[B11] Gázkiváltás és importhatás`

## Purpose

B11-P1 establishes the first executable physical boundary between observed
Hungarian household gas use and later programme-specific gas displacement.

Core rule:

`OBSERVED GAS BASELINE != PROGRAMME TARGET != REPLACEABLE GAS FRACTION != PHYSICAL GAS DISPLACEMENT != IMPORT VALUE`

The former policy-proposal shorthand `2 million households × 1,500 m3/year ≈ 3 bcm/year`
is **not** a canonical baseline, calibration target or observed result. If retained
anywhere for policy sensitivity, it is only a `POL/SCN` hypothesis.

## KSH observed baseline evidence

### KSH STADAT 15.1.1.43 — Gázellátás

Official source:

- https://www.ksh.hu/stadat_files/kor/hu/kor0043.html

Current table update: 2025-10-31.

For 2024 the table directly publishes:

- households consuming piped gas: `3,241,811`;
- annual piped-gas consumption per household consumer: `1,049.4 m3`.

These are source-native KSH observations at national annual grain.

### KSH STADAT 15.1.2.25 — regional gas/electricity use

Official source:

- https://www.ksh.hu/stadat_files/kor/hu/kor0068.html

Current table update: 2025-10-31.

The table publishes 2024 monthly average piped-gas use per household consumer
at county/region grain. Examples from the current table include:

- Budapest: `58.4 m3/month`;
- Pest: `87.7 m3/month`;
- Fejér: `65.4 m3/month`;
- Győr-Moson-Sopron: `65.5 m3/month`;
- Borsod-Abaúj-Zemplén: `66.0 m3/month`.

The regional table is retained as an independent spatial baseline control.

## Cross-table control disagreement

B11-P1 does **not** silently reconcile the national annual-average metric from
KOR0043 with values implied by the county/region monthly-average table KOR0068.

The current published tables do not provide sufficient evidence inside this P1
slice to prove that the two metrics have identical denominator/time-weighting/
revision semantics. Therefore:

`KOR0043 ANNUAL AVG != ASSUMED 12 × KOR0068 MONTHLY AVG`

unless a later methodology audit proves the identity.

The source registry records:

`Q_CROSS_TABLE_METRIC_DISAGREEMENT`

This Q does not invalidate either source-native observation; it blocks using one
to back-calculate, overwrite or "correct" the other.

## B02 population context

The existing B02 KSH WBL011 materialization includes a separate observed
projection at:

`county × settlement_type × construction_period × heating_mode × heating_fuel`

This supports population composition context for B11. It does **not** prove:

- annual gas volume of a household;
- technical heat-pump suitability;
- programme eligibility;
- replaceable gas end-use fraction;
- rebound;
- retrofit savings.

No cell-level join to unrelated B02 envelope projections is allowed unless the
upstream B02 contract separately authorizes it.

## Executable physical contract

`modules/B11/physical_displacement_contract.py` requires four explicit values:

1. `baseline_gas_m3` — annual physical gas volume;
2. `retrofit_reduction_fraction` — gas-demand reduction applied before fuel switch;
3. `replaceable_end_use_fraction` — share of post-retrofit gas physically replaced;
4. `rebound_fraction` — bounded share of would-be displacement restored by rebound.

The physical sequence is:

```text
post_retrofit_gas = baseline_gas × (1 − retrofit_reduction)
gross_displaceable = post_retrofit_gas × replaceable_end_use_fraction
displaced_gas = gross_displaceable × (1 − rebound)
remaining_gas = post_retrofit_gas − displaced_gas
```

The contract conserves physical gas balance and rejects:

- missing values as zero;
- `Q` values as numeric authority;
- fractions outside `[0,1]`;
- negative gas baseline;
- hidden household-count multiplication;
- tariffs or import prices inside the physical calculation.

If any input is `SCN`, the output remains `SCN`. An observed baseline cannot
promote scenario assumptions to observed displacement.

## What P1 does not claim

P1 does not yet produce a national programme gas-displacement number.

The following remain unresolved before a canonical `bcm/year` programme output:

- exact participating population from B01/B02;
- household/archetype baseline gas-volume bridge;
- gas-specific end-use split, especially space heating vs DHW/cooking;
- source-supported retrofit impact for the selected household state;
- rebound evidence;
- residual gas uses after heat-pump transition;
- aggregation from household/archetype results to programme year;
- B03 wholesale/import valuation input.

Therefore the Issue #15 acceptance items `1.8 / 2.4 / 3.0 bcm and continuous
scenario` remain future scenario/reporting outputs, not calibration anchors.

## B03 boundary

B03 defines `WHOLESALE_IMPORT` as the only price layer eligible for later B11
import-value calculation. B11-P1 does not consume that price and therefore does
not depend on resolving the current TTF numeric-export blocker for physical
volume accounting.

Residential retail tariff is not an import valuation price.

## Readiness effect

B11 moves from `NOT_STARTED` to `IN_PROGRESS` with a deliberately small readiness
uplift. P1 establishes an observed source boundary and executable physical
contract, but no real programme population or national bcm displacement is yet
produced.
