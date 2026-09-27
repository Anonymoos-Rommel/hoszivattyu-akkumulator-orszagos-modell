# B05-P47 - Mitsubishi SZU certification sampling and report-identity boundary

Date: 2026-09-27
Canonical base: `717e1788afd6a9cf3026e229973d8fa52fc56e71`

## Purpose

P47 attacks the P44/P45-era Mitsubishi transient residual:

`MITSUBISHI_SZU_037_0032_20_TRANSIENT_REPORT_OR_TRACE_ID_REQUIRED`

The initial assumption behind that wording was that registration `037-0032-20 rev.2` would lead directly to one exact SZU test report for PUZ-WM50VHA(-BS).

P47 tests that assumption before any external request.

## 1. Exact SZU certificate lineage

The original first-party SZU certificate is explicit:

- registration: `037-0032-20`;
- date: 2020-06-22;
- subtype: Ecodan Power Inverter 5-200D Packaged;
- model scope includes PUZ-WM50VHA(-BS);
- testing basis includes EN 14511-2..4:2018, EN 14825:2018, EN 16147:2017 and EN 12102-1:2017;
- KEYMARK scheme basis: Revision No. 6 dated 2019-03-19.

The certificate contains no:

- test-report number;
- test protocol number;
- selected sample serial number;
- raw test trace;
- product `tau_eq`.

The current rev.2 certificate dated 2023-12-19 preserves the same registration and product family but likewise exposes no underlying report identity.

Therefore:

```
CERTIFICATE_REGISTRATION != TEST_REPORT_ID
```

## 2. Current public KEYMARK surface

The current HP KEYMARK database identifies:

- certification body: SZU;
- testing laboratory: SZU Brno, CZ;
- registration: `037-0032-20 / rev.2`;
- PUZ-WM50VHA(-BS) models;
- EN14511-4 operating tests as pass/fail;
- EN14825 Prated/SCOP/Tbiv/TOL/Pdh/COP/Cdh;
- WTOL and auxiliary powers.

It does not expose:

- exact tested-unit serial;
- certification-body sample-selection record;
- test-report identifier;
- seconds-scale start/restart trace;
- `tau_eq`.

A "passed" starting/operating or defrost test is not the raw transient record.

## 3. Same outdoor unit spans multiple registrations

The current HP KEYMARK database also contains registration:

`037-0030-20 / rev.2`

for Ecodan Power Inverter 5-170D Packaged.

That separate registration also contains the exact outdoor unit:

`PUZ-WM50VHA(-BS)`.

Thus:

```
SAME_OUTDOOR_UNIT
CAN_APPEAR_IN_MULTIPLE_CERTIFICATE_REGISTRATIONS
```

and:

```
REGISTRATION_ID != UNIQUE_PHYSICAL_TEST_IDENTITY
```

This is not evidence that the two registrations necessarily share one report. It proves only that outdoor-unit identity and certificate-registration identity are different grains.

## 4. KEYMARK sampling architecture

The official Annex A Rev.3 dated 2017 already defined for non-air/air types:

| certified sub-types | tested sub-types |
|---:|---:|
| <=5 | 1 |
| >5 <=10 | 2 |
| >10 <=15 | 3 |

This document predates the 2020 Mitsubishi certificate and proves that Heat Pump KEYMARK used sampled subtype certification architecture before the certificate was issued.

P47 does **not** claim that the 2017 Annex A revision alone identifies the exact rule revision attached to the 2020 application.

The current European KEYMARK Scheme Rev.15 independently makes the current semantics explicit:

- admission tests are conducted by a recognised laboratory;
- the test report is communicated to the certification body;
- for air/water, one test may certify five sub-types;
- additional sub-types can therefore be certified without each having its own new test report.

This establishes the canonical caution:

```
CERTIFIED_SUBTYPE
!=
PROVEN_DIRECTLY_TESTED_SUBTYPE
```

until the actual certification-body sampling record or exact test-report lineage is recovered.

## 5. The 037-0032-20-01/02 suffixes are not test-report IDs

Mitsubishi public product literature displays `037-0032-20-01` on the PUZ-WM50VHA product sheet.

A historical MCS product-directory capture dated 2022-10-07 resolves the pair explicitly:

- `037-0032-20-01` -> model `PUZ-WM50VHA`;
- `037-0032-20-02` -> model `PUZ-WM50VHA-BS`.

Thus those suffixes are model-level certification identifiers in the MCS product-directory layer.

P47 therefore freezes:

```
037-0032-20-01_OR_02 != SZU_TEST_REPORT_ID
```

unless a source-native SZU/Mitsubishi authority states otherwise.

## 6. Public report/protocol recovery

P47 searched combinations of:

- `037-0032-20`;
- `037-0032-20 rev.2`;
- `PUZ-WM50VHA`;
- SZU;
- test report;
- protocol;
- Czech forms including `zkušební protokol` / `protokol o zkoušce`;
- EN14825 / EN14511.

The indexed public surfaces recovered certificate/database/product references but no underlying SZU report/protocol identifier.

Canonical boundary:

```
PUBLIC_REPORT_ID_NOT_RECOVERED
!=
NO_REPORT_EXISTS
!=
PUZ_WM50_WAS_NOT_TESTED
```

## 7. Correct acquisition object

The Mitsubishi transient route must first bind the physical test object.

A qualified closure can come from either:

1. a certification-body/SZU sampling record that identifies the tested PUZ-WM50VHA(-BS) subtype/model/specimen and its exact report ID;
2. an exact SZU report whose product/sample identity explicitly binds PUZ-WM50VHA(-BS);
3. another exact manufacturer/laboratory source-native PUZ-WM50VHA(-BS) transient record meeting the P43 gate.

Only after that binding can report content be tested for product `tau_eq` or a derivable seconds-scale transient trace.

## 8. Residual transition

Previous:

`MITSUBISHI_SZU_037_0032_20_TRANSIENT_REPORT_OR_TRACE_ID_REQUIRED`

becomes:

`EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`

This is a stricter and more physically correct blocker.

## 9. Readiness

No product transient parameter is recovered.

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

## Public sources

- Original first-party SZU certificate 037-0032-20:
  https://www.szutest.cz/www/upload/Keymark%20certifik%C3%A1ty/037-0032-20_HPK_web.pdf
- Current HP KEYMARK 037-0032-20 rev.2:
  https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?cHash=0aecf6bcedcd369e5acf7a509916b562&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=4300
- Current HP KEYMARK 037-0030-20 rev.2:
  https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?cHash=a8f7f03b2d131ddc468469ff036910f7&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=4298
- Heat Pump KEYMARK Annex A Rev.3:
  https://www.heatpumpkeymark.com/fileadmin/user_upload/documents/2HPK_Annex_A_KEYMARK_requirements.pdf
- European KEYMARK Scheme Rev.15:
  https://keymark.eu/en/documents/heat-pumps/118-heat-pump-keymark-scheme-rules-v15/file
- Mitsubishi PUZ-WM50VHA official product sheet:
  https://library.mitsubishielectric.co.uk/pdf/download_full/4144
- Historical MCS product-directory capture:
  https://docs.planning.org.uk/20240801/58/SE6RPMJNMDK00/oxmqwbzwvsdzabke.pdf
