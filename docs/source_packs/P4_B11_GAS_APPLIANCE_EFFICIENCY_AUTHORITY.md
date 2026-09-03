# B11-P4 — Gas-appliance efficiency authority and energy-basis gate

Canonical base: `52e38ed7696f24e7359d3fb658b8a9df15d8dbb7`

## Core boundaries

`EU ETA_S / LABEL != IN-USE SEASONAL FUEL-CONVERSION EFFICIENCY`

`GCV-BASED EFFICIENCY != LHV-BASED EFFICIENCY`

`ECODESIGN MINIMUM != HUNGARIAN STOCK AVERAGE`

B11-P3 converts useful heat to gas input energy and then to gas volume. P4 hardens the efficiency term used in that conversion.

## EU product/regulatory evidence

Commission Regulation (EU) No 813/2013 defines boiler useful efficiency as useful heat output divided by total energy input, with fuel energy expressed on a GCV basis. It also defines seasonal space-heating efficiency (`eta_s`) as a broader product metric with corrections for controls, auxiliary electricity, standby heat loss and ignition-burner consumption.

Commission Delegated Regulation (EU) No 811/2013 defines the seasonal space-heating efficiency classes used by the product label.

These are authoritative product/regulatory definitions. They do **not** establish the distribution of in-use seasonal gas-appliance efficiency in Hungarian homes and do not, by themselves, authorize programme gas-volume calculations.

The European Commission space-heater policy page provides EU-wide context and EPREL access. Its EU-average in-use/sold boiler efficiency figures are not Hungarian stock calibration and are not imported into the B11 runtime.

## Energy-basis gate

P3 uses gas lower heating value (`LHV`) for the physical m3 conversion. An efficiency stated on gross calorific value (`GCV`) basis cannot be inserted directly.

For the same gas quantity:

`eta_LHV = eta_GCV * GCV / LHV`

Conversion is allowed only when both GCV and LHV are explicit, positive and applicable to the same gas-quality context. No generic national ratio is embedded.

Because `GCV > LHV`, an LHV-basis efficiency for a condensing appliance may exceed 1.0. Therefore P3 no longer applies a basis-blind `<= 1.0` cap. Instead it requires the explicit `fraction_lhv` unit and relies on P4 to authorize/normalize the efficiency evidence.

## Metric authority

P4 separates three concepts:

1. `EU_SEASONAL_SPACE_HEATING_ETA_S` — product/regulatory seasonal metric; not direct fuel-volume authority.
2. `EU_USEFUL_EFFICIENCY` — product operating-point efficiency on the regulation's energy basis; not an observed in-use household seasonal value.
3. `SEASONAL_FUEL_CONVERSION_EFFICIENCY` — the metric required by P3 for annual gas-volume derivation. It must be household/archetype/calibration-specific evidence and must carry an explicit GCV or LHV basis.

## Hungarian stock blocker

No authoritative current Hungarian household/archetype distribution of in-use seasonal gas-appliance fuel-conversion efficiency has been established in this slice. Therefore:

- no 0.8/0.9/etc. national default is introduced;
- no boiler-age class is mapped silently to an efficiency;
- no Ecodesign minimum is treated as existing-stock performance;
- no EU average is treated as Hungarian performance;
- no product label/class is treated as programme calibration.

A later numeric calibration requires evidence that is representative of the Hungarian in-use stock or an explicit household/building system record.

## Runtime consequence

`modules/B11/gas_efficiency_authority.py` rejects regulatory/product metrics when asked to authorize P3 fuel volume. GCV-basis seasonal fuel-conversion evidence additionally requires an explicit GCV/LHV gas-quality pair before an LHV-basis value can be returned.

The P3 bridge now accepts only:

- `fraction_lhv` for seasonal fuel-conversion efficiency;
- `MJ/m3_LHV` for gas lower heating value.

This is an interface hardening, not a new programme bcm result.

## Sources

- EUR-Lex: Commission Regulation (EU) No 813/2013.
- EUR-Lex: Commission Delegated Regulation (EU) No 811/2013.
- European Commission: Space Heaters product-policy page / EPREL context.

Retrieved: 2026-09-03.
