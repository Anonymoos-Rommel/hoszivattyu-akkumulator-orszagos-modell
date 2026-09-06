# B02-P24 — OÉNY / e-tanúsítás certificate-level current-emitter route

**State:** `PUBLIC_RECORD_ROUTE_QUALIFIED / STOCK_ASSIGNMENT_Q`

**Reference date:** 2026-09-06

## 1. Purpose

P23 bounded the public aggregate emitter surfaces. P24 audits a different public authority surface: the official Hungarian e-tanúsítás certificate itself.

The question is deliberately narrow:

> Does the official current certificate format expose current heat-emitter evidence at individual certificate level, and does that surface also prove a complete occupied-stock emitter assignment or current hydronic design-temperature assignment?

## 2. Official current-certificate evidence

The official Építésügyi Portál states that the detailed energetic certificate contains current-state technical information including:

- current heating-system type;
- the mode of heat emission, with `radiátor` given as an example;
- modernization proposals;
- photographic documentation.

Source:

- https://www.e-epites.hu/energetika/lakossag/az-energetikai-tanusitas-es-az-energetikai-tanusitvany

The official e-tanúsítás preview also contains a dedicated photo-documentation slot labelled:

`JELLEMZŐ HŐLEADÓ ÉS ANNAK SZABÁLYOZÁSA`

Source preview:

- https://dok.e-epites.hu/e-tanusitas/elonezet_Szepegyhaz_Szel_20.pdf

The preview is explicitly a **non-authentic synthetic example**. Its values and example images are therefore not current-building evidence. It is used only to prove the public certificate template/content surface.

The official launch documentation states that the uploaded certificate files contain energetic calculations, site photos and property data, while the public certificate search is address-oriented. It also links the public XML/JSON examples used by the preview workflow.

Source:

- https://www.e-epites.hu/hirek/e-tanusitas/elerheto-az-uj-e-tanusitas

## 3. Canonical result for current heat emitters

P24 therefore refines the public-evidence state:

`PUBLIC CERTIFICATE FORMAT CAN CARRY CURRENT HEAT-EMITTER EVIDENCE`

but:

`CERTIFICATE-LEVEL EMITTER EVIDENCE != COMPLETE OCCUPIED-STOCK EMITTER ASSIGNMENT`

and:

`PUBLIC ADDRESS/HET SEARCH != DOCUMENTED BULK STOCK DATASET`

The existing P1M machine-access audit remains historically correct for its 2026-08-17 scope: it did not prove a P1K-compatible bulk/public machine-readable current-emitter field. P24 does **not** rewrite that historical result. P24 adds a later, document-level evidence route.

For P18 direct authority, an individual real certificate could potentially support a bounded dwelling/building current-emitter claim if the evidence is explicit and locatable. It still cannot, by itself, satisfy the national current-stock requirement because P18 requires complete occupied-stock assignment or a reproducible binding at the required stock grain.

Therefore:

`CURRENT_HEAT_EMITTER_EVIDENCE = Q` for the complete B02 technical-readiness archetype.

## 4. Design-temperature audit

P24 also checks whether the same public surface proves the remaining current design-temperature blocker.

The current public certification information and the public certificate preview prove current heating-system/heat-emission documentation, but they do **not** publicly establish a complete current-system supply/return design-temperature pair for the occupied stock.

The public energetic guidance also uses standard **indoor/outdoor design temperatures** for load/calculation context (for residential buildings, the public guidance gives 20 °C indoors and -15 °C outdoors). Those are ambient calculation conditions, not hydronic system supply/return temperatures.

Source:

- https://www.e-epites.hu/energetika/lakossag/altalanos-informaciok

Canonical boundary:

`INDOOR/OUTDOOR DESIGN CONDITION != HYDRONIC SUPPLY/RETURN DESIGN TEMPERATURE`

Likewise:

`REFERENCE OR CALCULATION TEMPERATURE != CURRENT BUILDING SYSTEM DESIGN-TEMPERATURE EVIDENCE`

This preserves the P18 rule:

`REFERENCE 55/45 C != CURRENT BUILDING DESIGN TEMPERATURE`

No public P24 source proves a complete current supply/return assignment.

Therefore:

`CURRENT_DESIGN_TEMPERATURE_EVIDENCE = Q`.

## 5. Admission impact

P24 adds one bounded public evidence route to the existing emitter audit:

- official e-tanúsítás certificate/document surface: `QUALIFIED_RECORD_ROUTE_ONLY`;
- explicit current heat-emission mode/documentation exists at certificate level;
- no documented public complete stock assignment;
- no WBL direct join;
- no national completeness proof;
- no complete current supply/return design-temperature assignment.

No new runtime gate is required. The existing P18 direct-authority contract already expresses the correct admission boundary.

Technical readiness remains:

`TECHNICAL_READINESS_ARCHETYPE = Q`

with exactly:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`

## 6. Non-claims

P24 does not claim that:

- every public certificate exposes the same detailed document payload;
- certificate records are nationally representative of all occupied dwellings;
- the public UI is a documented bulk API;
- a certificate photograph automatically identifies emitter type without explicit adjudication;
- indoor/outdoor design temperatures are hydronic supply/return temperatures;
- current emitter evidence closes the design-temperature blocker;
- OÉNY request dispatch or this public audit raises B02 readiness.

## 7. Decision

`PUBLIC DOCUMENT-LEVEL CURRENT-EMITTER ROUTE = QUALIFIED_RECORD_ROUTE_ONLY`

`COMPLETE CURRENT-STOCK EMITTER AUTHORITY = Q`

`COMPLETE CURRENT DESIGN-TEMPERATURE AUTHORITY = Q`

No readiness uplift.
