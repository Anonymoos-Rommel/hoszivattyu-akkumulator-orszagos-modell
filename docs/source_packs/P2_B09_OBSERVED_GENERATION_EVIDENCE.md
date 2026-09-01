# B09-P2 — Hungarian observed generation evidence contract

Retrieval/audit date: 2026-09-01
Repository base: `8ec0cde9275121f8e40f78a3fbeba4e4fd3ba539`

## Decision

The selected machine-readable candidate for the next B09 real-generation evidence slice is ENTSO-E Transparency Platform **Actual Generation per Production Type / Aggregated Generation per Type [16.1.B&C]**.

The source-native contract is:

- document type `A75` — Actual generation per type;
- process type `A16` — Realised;
- business type `A01` production, with `A93` wind generation and `A94` solar generation also permitted by ENTSO-E for this article;
- object aggregation `A08` — Resource type;
- Hungarian area `10YHU-MAVIR----U`;
- source-native production type code `Bxx`;
- quantity unit MW (`MAW` in the ENTSO-E message contract);
- explicit MTU resolution `PT15M`, `PT30M`, or `PT60M`;
- UTC-normalised interval semantics.

The Transparency Platform UI exposes the same dataset as **Actual Generation per Production Type**, with selectable Control Area / Bidding zone / Country and production-type columns. It separately exposes production and consumption series; consumption is not negative generation and is excluded from the B09 generation handoff.

## Official evidence inspected

1. **ENTSO-E Detailed Data Descriptions v3r4**, dated 2023-12-15:
   `https://eepublicdownloads.entsoe.eu/clean-documents/Transparency/MoP_Ref2_DDD_v3r4.pdf`.
   - Defines Aggregated Generation per Type [16.1.B&C].
   - Actual aggregated generation is per bidding zone and market time unit.
   - Unit is MW.
   - ENTSO-E notes that when actual values are not available, estimates may be used. Therefore the repository preserves the explicit semantic caveat `ENTSOE_PUBLISHED_ACTUAL_MAY_INCLUDE_PROVIDER_ESTIMATES`; it does not claim meter-only origin.

2. **ENTSO-E Generation and Load Process Implementation Guide version 0.3 – Draft / dependency table**:
   `https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fweb+api%2FIG-for-TP-data-extraction-process.pdf`.
   - `A75` Actual generation per type.
   - `A16` Realised.
   - `A01` Production; `A93` wind generation; `A94` solar generation.
   - `A08` Resource type.
   - `InBiddingZone_Domain` used; production-negative / consumption direction is separate.
   - `PT60M`, `PT30M`, `PT15M` supported.

3. **ENTSO-E Manual of Procedures page and v3.5 package**, current publication inspected 2026-09-01:
   page `https://www.entsoe.eu/data/transparency-platform/mop/`, package
   `https://eepublicdownloads.blob.core.windows.net/public-cdn-container/clean-documents/mc-documents/transparency-platform/MOP/MoP_v3r5_final.zip`.
   - The official page identifies MoP v3.5 as the current revision context and links the exact package registered in `registry/sources.csv`.
   - This does not replace the directly verified v3r4 DDD text for the 16.1.B&C estimate semantics in this slice.

4. **ENTSO-E Transparency Platform Actual Generation per Production Type UI**:
   `https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=`.
   - Confirms the public product identity and production-type table structure.
   - Export requires login; the public UI is corroboration, not the canonical machine intake path.

5. **ENTSO-E General Terms and Conditions**:
   `https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fterms+and+conditions%2F230309_ENTSOE_Transparency_Terms_Conditions_MC_APPROVED.pdf`;
   and **List of Data Available for Free Re-use, last modified 2023-10-18**:
   `https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fterms+and+conditions%2F231018_List_of_Data_available_for_reuse.pdf`.
   - The inspected authority does not establish repository redistribution clearance for the A75 raw response used by this slice.
   - Absence of clearance is not treated as a legal prohibition; it is an unresolved acquisition-specific reuse decision.
   - No ENTSO-E numeric raw payload is committed.

The inspected official free-reuse list is:
`https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fterms+and+conditions%2F231018_List_of_Data_available_for_reuse.pdf`.
It lists specified load forecasts and other items, but not Actual Generation
per Production Type/A75. This is not a prohibition inference; it leaves
acquisition-specific A75 reuse clearance unresolved.

## Runtime truth contract

`observed_generation_contract.py` is an acquisition/parser contract only. A real source-native record becomes `OBS` only when all gates pass:

- canonical ENTSO-E source identity;
- canonical HTTPS API endpoint;
- exact non-secret query semantics: `documentType=A75`, `processType=A16`, `in_Domain=10YHU-MAVIR----U`, `periodStart`, `periodEnd`;
- exact query uniqueness and valid UTC request window;
- payload `A75/A16` identity;
- Hungarian in-domain production direction;
- accepted production business type;
- `A08` resource-type aggregation;
- source-native `Bxx` production type;
- source-native MW unit;
- supported explicit MTU;
- timezone-aware source/acquisition timestamps;
- exact SHA-256 match against the exact UTF-8 parser input;
- explicit `REUSE_CLEARED`;
- complete provenance and source revision or `NOT_PROVIDED_BY_SOURCE`.

Unresolved/restricted/unknown reuse, missing checksum or missing quantity remain `Q`. Explicit zero is not treated as missing.

Direct construction cannot mint an `OBS` record: the verified parser path supplies a private verification token after the canonical checks.

## B09 handoff

The source-native layer remains in MW. The existing B09 adequacy engine expects kW at `GENERATION_AC`, so the conversion is explicit:

`delivered_generation_kw = source_power_mw * 1000`

The handoff row is therefore `DER` when the underlying source row is `OBS`; a Q source row stays Q.

The handoff also requires an explicit acquisition manifest listing the expected production-type set. ENTSO-E does not provide a platform-level declaration of every production type expected for an area, so an absent type is **never inferred to be zero**. Missing component/timestamp cells fail closed.

## Spatial boundary

The selected evidence closes only a **Hungarian ENTSO-E control-area / bidding-zone source contract**. It does not provide or authorize:

- county generation;
- DSO-region generation;
- county↔DSO allocation;
- arbitrary production-type spatial splitting;
- national household scaling;
- system-storage dispatch;
- curtailment, reserve or market dispatch;
- B10 headroom/reinforcement/CAPEX.

Therefore Q-B09-001 remains `OPEN`, but is partially bounded: the canonical source family, source-native production-type grain, time basis and acquisition/provenance mechanics are identified; regional/DSO evidence, acquisition-specific reuse clearance and a real raw snapshot remain open.

Q-B09-002 remains unchanged and fully separate.
