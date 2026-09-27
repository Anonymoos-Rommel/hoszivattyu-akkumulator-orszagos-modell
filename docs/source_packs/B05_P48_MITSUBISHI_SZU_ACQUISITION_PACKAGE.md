# B05-P48 - Mitsubishi SZU exact acquisition package

Date: 2026-09-27
Canonical base: `2638e7d088415216491acdf48b70447557f0fb25`

## Purpose

P47 established that:

```
REGISTRATION_ID
!=
UNIQUE_TESTED_SPECIMEN
!=
TEST_REPORT_ID
```

and narrowed the Mitsubishi product-transient blocker to:

`EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`.

P48 converts that blocker into an exact, human-gated acquisition package.

**P48 does not send an email or contact any external party.**

## 1. Why a specimen-binding request is necessary

The original SZU certificate 037-0032-20 identifies PUZ-WM50VHA(-BS) inside the certified product scope but does not publish the selected test specimen or report identifier.

The Heat Pump KEYMARK sampling architecture requires certification-body sample selection. The current scheme states that the applicant supplies at least three units traceable by serial number for the selected model, the certification body selects one random unit, and the test report is communicated to the certification body.

The official public KEYMARK documents index also lists:

`Annex L - Sampling template V2`.

No filled Mitsubishi Annex L/sample-selection record was recovered from the indexed public surfaces.

Therefore the next acquisition target is not simply "send the test report". It is the binding chain:

```
PUZ-WM50VHA(-BS)
-> tested subtype/model
-> selected specimen / direct-test binding
-> exact report/protocol ID
-> report content
```

## 2. Minimum requested fields

A useful response must answer as many of the following source-native fields as releasable:

1. **Certificate context**
   - registration 037-0032-20 and/or 037-0030-20;
   - certification/revision date;
   - applicable KEYMARK scheme revision.

2. **Directly tested subtype/model**
   - exact subtype selected for physical testing;
   - exact model combination;
   - whether the standalone PUZ-WM50VHA(-BS) outdoor unit was directly tested or inherited certification through another subtype/package.

3. **Selected specimen**
   - serial number if releasable; or
   - an authoritative statement identifying the directly tested specimen/model if serial disclosure is restricted.

4. **Report identity**
   - SZU test-report / test-protocol identifier;
   - report date/revision;
   - testing laboratory;
   - whether one report underlies multiple certificate registrations/subtypes.

5. **Test conditions**
   - climate;
   - low/medium temperature application;
   - part-load conditions selected by the certification body;
   - relevant EN14511/EN14825 test conditions.

6. **Transient-content fields**
   - whether the report directly contains `tau_eq` / equivalent transient time constant;
   - whether a seconds-scale start/restart trace exists;
   - sampling cadence;
   - heat-output and electrical-input channels;
   - steady-state reference;
   - derivation method, if a time constant is derived rather than directly reported.

## 3. Admission contract

A response does **not** close product transient evidence merely because it provides a report number.

Required lineage:

```
EXACT_PRODUCT
AND
DIRECT_TEST_BINDING
AND
SOURCE_NATIVE_REPORT_ID
```

is sufficient only for:

`REPORT_ID_BOUND`.

To admit product transient physics, additionally require either:

- a directly reported product `tau_eq`; or
- a seconds-scale source-native trace plus an explicit derivation method.

Thus:

```
REPORT_ID_BOUND != PRODUCT_TAU_EQ_PROVEN
```

## 4. Official acquisition routes

### SZU certification-body route

Official SZU certification-process material states that information about certified clients can be obtained from the head of COSM.

Current public contact:

- **Ing. Lucie Strakova**
- head of COSM
- **strakova@szutest.cz**

General SZU fallback:

- **szu@szutest.cz**

This route is the strongest target for:

- selected subtype/model;
- selected sample/specimen;
- report/protocol ID;
- certification-body sampling record.

### Mitsubishi certificate-holder route

Official Mitsubishi Electric UK Ecodan technical contact:

- **Ecodan.technical@meuk.mee.com**

Current residential technical helpdesk:

- **residential.helpdesk@meuk.mee.com**

This route is appropriate for:

- certificate-holder report identity;
- manufacturer-held copy/excerpt;
- source-native product transient record;
- clarification whether PUZ-WM50VHA(-BS) was directly tested or covered through certification sampling.

## 5. Dispatch state

Canonical state:

`ACQUISITION_PACKAGE_READY_UNSENT`

P48 does not authorize or record any external send.

A future dispatch must be a separate human-authorized action.

## 6. Residual

The residual remains:

`EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`

but it is now operationally exact rather than an open-ended search request.

## 7. Readiness

No physical parameter has been acquired.

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

## Public authorities

- Heat Pump KEYMARK Scheme Rev.15:
  https://keymark.eu/en/documents/heat-pumps/118-heat-pump-keymark-scheme-rules-v15/file
- Heat Pump KEYMARK documents / Annex L index:
  https://keymark.eu/en/products/heatpumps/documents
- SZU certification-process information:
  https://www.szutest.cz/www/upload/categories/documents/20240515093754307.pdf
- Mitsubishi Ecodan technical support:
  https://les.mitsubishielectric.co.uk/housing-developers/technical-design-for-ecodan-air-source-heat-pumps
- Mitsubishi contact page:
  https://les.mitsubishielectric.co.uk/contact-us
