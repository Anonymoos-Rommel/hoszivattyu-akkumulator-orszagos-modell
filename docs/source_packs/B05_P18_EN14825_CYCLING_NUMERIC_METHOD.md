# B05-P18 - EN14825-based to-water cycling numeric method

## Purpose

P18 attacks the P17 residual:

`CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED`.

It does **not** change the B05 engine energy formula and it does not invent a
product-specific cycling penalty.

## Method authority

EU Regulation 813/2013 defines Cdh as efficiency loss due to cycling and uses
0.9 only as the default when Cdh was not determined by measurement.

EN 14825 defines capacity ratio CR as load divided by declared capacity at the
same temperature conditions, and defines COPbin as COP corrected with the
degradation coefficient where applicable.

SEAI's official DEAP method material gives the explicit EN14825-based
air/brine/water-to-water equation:

`COPbin = COPd * CR / (Cdh * CR + (1 - Cdh))`

The August 2024 DEAP Heat Pump Methodology states that the calculator/guidance
follows the changes proposed in the Q2 2019 methodology document. P18 therefore
qualifies the equation as a reproducible standard-method contract, not as a
Hungarian legal rule and not as product OBS.

## B05 mapping

P16/P17 must prove cycling first.

For a below-minimum-modulation state:

`CR = required_heat / cycling_capacity`

with `0 < CR < 1`.

The COP supplied to the formula must be source-supported at **the same
cycling capacity** used in that denominator.

Therefore:

`NOMINAL COP != COP AT MINIMUM CAPACITY`

`CERTIFIED Pdh-POINT COP != MINIMUM-CAPACITY COP`

unless their capacity coordinates match.

## Current P17 products

### Vaillant VWL 85/6 A 230V S3

A7/W35 minimum modulation:
- 3.00 kW.

Certified P15 +7 C low-temperature point:
- Pdh 3.21 kW;
- COP 6.33;
- Cdh 0.950.

3.21 kW is not exactly 3.00 kW. P18 does not introduce a tolerance-based
physical equivalence.

Status:
`Q / MINIMUM_CAPACITY_COP_INPUT_REQUIRED`.

### Bosch CS5800iAW 4 ORE-S

A2/W35 minimum modulation:
- 1.80 kW.

Certified P16 +2 C low-temperature point:
- Pdh 4.31 kW;
- COP 3.21;
- Cdh 0.990.

4.31 kW is not the 1.80 kW minimum capacity.

Status:
`Q / MINIMUM_CAPACITY_COP_INPUT_REQUIRED`.

## Resolution

`CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED`
->
`RESOLVED_EN14825_WATER_SIDE_FORMULA`.

New narrower residual:

`MINIMUM_CAPACITY_COP_INPUT_REQUIRED`.

The other P17 residual remains:

`MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`.

Q-B05-004 becomes:

`OPEN_NARROWED_TO_MODULATION_SURFACE_AND_MIN_CAPACITY_COP_INPUT`.

## Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

No uplift is minted because the standard method is now executable, but no
current P17 product yet has a qualified COP at the exact cycling/minimum
capacity.

## Sources

- Commission Regulation (EU) No 813/2013:
  https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32013R0813
- EN 14825:2022 public semantics:
  https://standards.iteh.ai/catalog/standards/sist/0d3be441-d22e-447c-8204-e2b4b9c731f4/sist-en-14825-2022
- SEAI Q2 2019 Cdh method exposition:
  https://www.seai.ie/sites/default/files/publications/DEAP-Heat-pumps-consultation.pdf
- SEAI DEAP Heat Pump Methodology 2020 v2.1, August 2024:
  https://www.seai.ie/sites/default/files/publications/DEAP-Heat-pump-methodology-2020-V1.0.pdf
