# B05-P44 - transient report lineage and content boundary

Date: 2026-09-26
Canonical base: `3ca7f06feffe0eee6a3ca5362606c172985bf6b7`

## Purpose

P44 continues the P43 transient-fidelity attack before any external data request.

It asks three narrower questions:

1. Can the exact certification/test-report objects behind a canonical product be identified?
2. Does existence of a complete EN14825 report prove that product `tau_eq` or a seconds-scale transient trace is present?
3. Can independent public evidence provide the missing fan-coil heating emitter response without conflating room/system response with emitter output?

Core boundary:

```
CERTIFIED EN14825 TEST EXISTS
!=
PUBLIC TEST REPORT AVAILABLE
!=
TAU_EQ FIELD PUBLISHED
!=
SECONDS-SCALE TRANSIENT TRACE PUBLISHED
```

## 1. Dimplex exact VDE report lineage

The public VDE / Heat Pump KEYMARK certificate for LA 2030CP is exact:

- registration / ID: `40060852`;
- test report: `328782-TL2-1`;
- further information: Appendix 601 dated 2025-08-29;
- testing basis includes EN 14825:2022, EN 14511:2022 and EN 12102-1:2022.

Therefore the previous generic target "manufacturer or named laboratory" is narrowed for Dimplex to one exact report lineage.

This **does not** close product `tau_eq`: the public certificate identifies the report but does not expose its transient content.

## 2. What KEYMARK and PCDB actually prove about report content

Current Heat Pump KEYMARK Annex A requires admission/surveillance testing in recognised laboratories. The certification body selects bivalent and additional part-load conditions according to EN14825.

Current UK PCDB heat-pump requirements similarly require complete EN14825 reports for space-heating heat pumps.

However, the public PCDB optional EN14825 declaration form asks for:

- laboratory identity/date;
- part-load condition;
- capacity;
- COP;
- degradation coefficient `Cdh`.

It does **not** expose a product `tau_eq` or raw seconds-scale transient trace field.

Therefore P44 explicitly rejects:

`EN14825_REPORT_REQUIRED -> TAU_EQ_MUST_BE_PUBLIC/PRESENT`.

The underlying laboratory report or raw acquisition may still contain sufficient transient data, but this remains to be demonstrated source-native.

## 3. Bosch / Dimplex cross-brand evidence path

A fresh search revealed a strong but bounded cross-brand link.

The Bosch CS5001AW22 VDE KEYMARK certificate:

- names **Glen Dimplex Deutschland GmbH, Kulmbach** as the production site;
- uses VDE testing;
- has its own report lineage `336398-TL2-1`.

Separately, Bosch EU Declaration of Conformity 6721894401 cites `328782-TL2-1` among the ErP evidence associated with EN14825:2022, EN14511:2022 and EN12102:2022.

Bosch public technical data also reproduce key LA2030CP-scale performance values, but P44 does **not** promote this to exact product identity.

Canonical boundary:

```
COMMON PRODUCTION SITE
+ SHARED REPORT REFERENCE
+ STRONGLY MATCHING STATIC PERFORMANCE
!=
EXPLICIT PRODUCT EQUIVALENCE
!=
TRANSIENT PARAMETER TRANSFER
```

This is an additional acquisition route only: Bosch public technical files may expose more of the shared evidence lineage, but a Bosch-derived transient value cannot populate LA2030CP without explicit equivalence authority.

## 4. Default-authority divergence is real

U-CERT's EN15316-4-2/prEN2022 national-datasheet review reproduces:

`TAU_EQ = 30 s`

as the heat-pump inertia default.

The UK SAP/HEM lineage used elsewhere in B05 exposes a separate default branch of 140 s.

This confirms:

```
EN15316 DEFAULT 30 s = POL
UK SAP/HEM DEFAULT 140 s = POL
POL DEFAULT != PRODUCT OBS
```

P44 does not choose a winner and does not average them.

## 5. Fan-coil heating search result

Additional 2026 experimental heating evidence was found for ASHP-driven radiant-floor + FCU systems.

The work shows FCU-dominated startup and reports room/system response; for example the time for average indoor temperature to reach 18 C decreases from 5.5 h at W35 to 2.2 h at W45.

This is valuable physical validation but it is not an exact fan-coil emitter heat-output step-response time constant.

Two additional experimental lines move closer to the emitter itself:

- Duan et al. (2021) compare measured fan-coil heating from start-up to stabilization and analyse the complete heat-source -> terminal -> room energy-flow network.
- Duan et al. (2023) validate a simplified 2R1C terminal model on heating-terminal experiments. The required measurements include water flow and dynamic hot-water / terminal-surface / room temperatures; model validation includes heat flux.

These sources prove that direct fan-coil heating-terminal dynamic measurement and heat-flux parameterisation are established experimental methods. The public article layers inspected here still do not expose, at our admission grain, one exact FCU specimen together with a source-reported emitter heat-output step-response time constant. Therefore they strengthen the measurement path without creating the missing numeric OBS parameter.

Therefore:

`EMITTER_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`

narrows to:

`EXACT_FCU_HEATING_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`.

## 6. Q-B05-004 transition

P44 preserves Q-B05-004 OPEN.

Residuals:

1. `MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`;
2. `EXACT_FCU_HEATING_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED`;
3. `DIMPLEX_VDE_328782_TL2_1_TAU_EQ_OR_SECONDS_SCALE_TRACE_CONTENT_REQUIRED`;
4. `MITSUBISHI_SZU_037_0032_20_TRANSIENT_REPORT_OR_TRACE_ID_REQUIRED`.

The Dimplex route is now substantially more specific than P43: an exact VDE report object is known.

The Mitsubishi route is still one level weaker: exact KEYMARK registration/lab are known, but no underlying test-report identifier has been recovered from the public SZU certificate.

## 7. Readiness

No readiness uplift is minted.

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

The research reduced acquisition ambiguity; it did not supply the missing physical constants.

## Sources

- Heat Pump KEYMARK Annex A requirements:
  https://www.heatpumpkeymark.com/fileadmin/user_upload/documents/2HPK_Annex_A_KEYMARK_Requirements_V2.pdf
- LA2030CP VDE certificate:
  https://www.heatpumpkeymark.com/uploads/tx_ehpakeymark/40060852_29.08.2025.pdf
- UK PCDB heat-pump test requirements:
  https://www.ncm-pcdb.org.uk/sap/filelibrary/pdf/Supporting-documents/Heat-pump-test-requirements.pdf
- UK PCDB EN14825 declaration form:
  https://www.ncm-pcdb.org.uk/sap/filelibrary/pdf/Applications/SAP-PCDB---Optional-EN14825-test-data-declaration-form---V2.pdf
- U-CERT EN15316-4-2 datasheet review:
  https://u-cert.epb.center/media/filer_public/0c/ce/0cce6462-3ced-4028-a93c-7b5b6e65a732/u-cert_d31_report_v20_annex_2_2023-02-28_compressed.pdf
- Bosch CS5001AW22 VDE certificate:
  https://www.heatpumpkeymark.com/uploads/tx_ehpakeymark/40061610_05.02.2026.pdf
- Bosch EU Declaration of Conformity:
  https://bosch-de-de.boschhc-documents.com/download/pdf/file/6721894401
- 2026 FCU heating transient experiment:
  https://doi.org/10.3390/buildings16071325
- Duan et al. 2021 fan-coil start-up to stabilization:
  https://doi.org/10.1016/j.enbuild.2021.111391
- Duan et al. 2023 simplified 2R1C heating-terminal model:
  https://doi.org/10.1016/j.energy.2022.125941
