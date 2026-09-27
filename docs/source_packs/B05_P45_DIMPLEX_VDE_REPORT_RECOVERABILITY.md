# B05-P45 - Dimplex VDE report recoverability boundary

Date: 2026-09-27
Canonical base: `27f82490242eae6e2de0a70bc838ff33759b710c`

## Purpose

P45 attacks exactly one P44 residual before any external request:

`DIMPLEX_VDE_328782_TL2_1_TAU_EQ_OR_SECONDS_SCALE_TRACE_CONTENT_REQUIRED`

The target is no longer "find Dimplex transient data". The target is the exact VDE certification report object:

- product: Dimplex LA 2030CP;
- KEYMARK registration: `40060852`;
- certification/testing laboratory: VDE Prüf- und Zertifizierungsinstitut GmbH;
- report: `328782-TL2-1`;
- further information: Appendix 601 dated 2025-08-29.

P45 asks whether the report itself, a partial copy, an annex, or a source-native transient excerpt can be recovered from current public indexed surfaces.

## 1. Exact report identity remains source-native

The official VDE/Heat Pump KEYMARK certificate for LA 2030CP explicitly names:

`Report No. 328782-TL2-1`

and:

`Appendix 601 dated 2025-08-29`.

The Bosch CS5001AW22 EU Declaration of Conformity independently cites the same `328782-TL2-1` identifier in its ErP evidence row together with EN14825:2022, EN14511:2022 and EN12102:2022.

This strengthens report identity and cross-document lineage. It does not expose report content.

## 2. Public exact-ID recovery sweep

P45 searched the exact report identity and format variants across general indexed web surfaces and targeted official domains:

- `"328782-TL2-1"`
- `"328782 TL2 1"`
- `"328782-TL2"`
- report ID + Dimplex
- report ID + Bosch
- report ID + VDE
- report ID + EN14825
- report ID + Cdh
- report ID + tau_eq
- report ID + transient
- targeted `vde.com`, Dimplex and Bosch document domains.

Recovered exact references:

1. the official Dimplex/VDE certificate;
2. the Bosch 2026 EU Declaration of Conformity.

No complete report, partial report, Appendix 601 content, raw trace, or source-native transient excerpt was recovered from the indexed public surfaces audited on 2026-09-27.

Canonical wording is deliberately bounded:

```
NOT_RECOVERED_FROM_INDEXED_PUBLIC_SURFACES
!=
REPORT_IS_NONPUBLIC
!=
REPORT_DOES_NOT_EXIST
!=
REPORT_LACKS_TRANSIENT_CONTENT
```

## 3. Official VDE public-catalogue grain

The official VDE certificate-search page describes the public result/detail surface as providing:

- company name/address;
- product category;
- VDE certificate number;
- type designation;
- VDE mark;
- important technical data.

P45 therefore classifies the official public VDE catalogue as a certificate/product/technical-data surface.

It does **not** infer from this description that the underlying customer test report can never be obtained, nor that it lacks transient content.

## 4. HP KEYMARK public export is richer but still not the test report

The HP KEYMARK public database generates a five-page report for LA 2030CP registration 40060852.

The public export includes:

- EN14511-4 pass/fail items:
  - shutting off heat-transfer-medium flow;
  - complete power-supply failure;
  - defrost test;
  - starting and operating test;
- EN14511 heat output, electrical input and COP;
- EN14825:
  - seasonal efficiency;
  - Prated;
  - SCOP;
  - Tbiv;
  - TOL;
  - Pdh;
  - COP;
  - Cdh;
- WTOL;
- off, thermostat-off, standby and crankcase-heater powers;
- annual energy consumption.

The public export contains no field labelled:

- `tau_eq`;
- `transient`;
- `time constant`;
- seconds-scale trace.

Therefore:

```
PUBLIC_KEYMARK_EXPORT_HAS_CDH
!=
PUBLIC_KEYMARK_EXPORT_HAS_TAU_EQ
!=
UNDERLYING_VDE_REPORT_LACKS_TAU_EQ
```

## 5. Exact admission boundary

P45 freezes the following executable rules:

```
REPORT_ID_REFERENCE != REPORT_CONTENT
PUBLIC_INDEX_SEARCH_MISS != INTERNAL_REPORT_ABSENCE
CERTIFICATE_PASS_STATUS != RAW_TRANSIENT_TRACE
CDH != TAU_EQ
STATIC_OR_SEASONAL_DATABASE_EXPORT != SECONDS_SCALE_TRANSIENT_RECORD
```

A Dimplex product OBS `tau_eq` may be admitted only from:

1. the exact VDE report `328782-TL2-1` if it directly reports the parameter; or
2. a source-native excerpt/raw acquisition from that exact report/test campaign sufficient to derive the parameter under an explicit method; or
3. another exact LA2030CP manufacturer/lab transient record meeting the P43 admission gate.

## 6. Residual transition

P44 residual:

`DIMPLEX_VDE_328782_TL2_1_TAU_EQ_OR_SECONDS_SCALE_TRACE_CONTENT_REQUIRED`

becomes:

`EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED`

This is a narrower acquisition object, not a readiness gain.

Other Q-B05-004 residuals remain unchanged:

- `MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`;
- `EXACT_FCU_HEATING_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`;
- `MITSUBISHI_SZU_037_0032_20_TRANSIENT_REPORT_OR_TRACE_ID_REQUIRED`.

## 7. Readiness

No physical parameter was recovered.

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

P45 reduces uncertainty about *where the missing evidence is not exposed publicly*; it does not fill the missing physics.

## Public sources

- LA2030CP VDE / Heat Pump KEYMARK certificate:
  https://www.heatpumpkeymark.com/uploads/tx_ehpakeymark/40060852_29.08.2025.pdf
- LA2030CP HP KEYMARK public database export:
  https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?tx_pskeymark_frontend%5Baction%5D=generatePdf&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=6778
- VDE public certificate search description:
  https://www.vde.com/tic-en/marks-and-certificates/vde-approved-products/search
- Bosch CS5001AW22 EU Declaration of Conformity:
  https://bosch-de-de.boschhc-documents.com/download/pdf/file/6721894401
