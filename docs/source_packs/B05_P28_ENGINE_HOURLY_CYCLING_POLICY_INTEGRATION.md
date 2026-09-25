# B05-P28 - engine hourly cycling policy integration

## Purpose

P24 qualified a separate hourly on/off-transient method.
P25 qualified an explicit HEM-default parameter-policy path.
P27 separated product-level evidence from coordinate coverage and OBS-grade transient fidelity.

Before P28, those contracts were not connected to `simulate_hourly()`.

The engine could report:

`BELOW_MINIMUM_MODULATION / CYCLING_REQUIRED`

while still returning unadjusted `delivered_heat / operating_point_COP` electricity and a VALID row.

P28 closes only that integration gap.

Core rule:

`CYCLING_REQUIRED != CYCLING_PHYSICS_APPLIED`.

## Qualified engine path

For an encountered below-minimum hour the engine now requires:

1. the normal same-product operating point;
2. a same-product `MinimumPointSurface` at the same outdoor/supply coordinate;
3. minimum continuous capacity;
4. the minimum-point COP/input paired to that minimum capacity;
5. an explicit cycling parameter policy;
6. an explicit supported emitter class.

Only then may the engine call the P25 on/off policy.

The engine never derives minimum compressor input from the normal operating-point COP.

## First real-product exact regression

Mitsubishi `PUZ-WM50VHA(-BS)`, A7/W35:

- normal/nominal point: capacity 5.00 kW, input 1.00 kW, COP 5.00;
- minimum point: capacity 1.80 kW, COP 5.46;
- minimum compressor input is therefore derived from the same minimum point as `1.80 / 5.46` kW.

For a 1.00 kW hourly load:

- hourly load ratio = `1.00 / 5.00 = 0.20`;
- minimum continuous load ratio = `1.80 / 5.00 = 0.36`.

Under explicit `HEM_DEFAULT_SCENARIO` plus `RADIATOR_OR_UFH_WET`:

- `tau_eq = 140 s` (POL/default);
- emitter response time = `1370 s` (POL/default);
- the P24/P25 on/off inertia power is evaluated;
- `cycling_inertia_energy_kwh = inertia_power_kw * timestep_hours`;
- that energy is added to heat-pump electricity.

The result is DER under an explicit POL/default scenario, not product OBS.

## Fail-closed cases

An encountered cycling hour is Q if:

- no same-product minimum-point capacity/COP surface is supplied;
- the surface cannot resolve the coordinate;
- the surface minimum conflicts with a simultaneously present engine floor;
- minimum input cannot be derived from the minimum point;
- no explicit cycling policy is selected;
- the emitter mapping is unresolved;
- the fan-coil HEM documentation/code divergence is encountered.

The base COP electricity is retained only as inspectable incomplete output; the row and simulation status become Q, so downstream consumers cannot treat it as qualified total electricity.

## What P28 does not resolve

P28 does not:

- create product-specific `tau_eq`;
- resolve the HEM fan-coil 1370 s versus 360 s divergence;
- fill Mitsubishi A-15/W50;
- fill Dimplex A-10 minimum rows;
- transfer Mitsubishi minimum-point COP coverage to Dimplex;
- change generic product-OBS cycling runtime to resolved.

Therefore:

- `Q-B05-004` remains OPEN as the umbrella;
- `PART_LOAD_MODULATION = 45%`;
- B05 = **64%**.

## Existing authorities

- P20 Mitsubishi source-native Min/Nom/Max A7/W35 point pairing.
- P22 Mitsubishi same-product minimum capacity/COP surface.
- P24 HEM/EN15316-style hourly on/off transient method.
- P25 explicit HEM-default transient parameter policy.
