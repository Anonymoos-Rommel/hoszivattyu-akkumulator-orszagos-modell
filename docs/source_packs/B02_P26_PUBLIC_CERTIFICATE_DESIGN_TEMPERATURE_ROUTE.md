# B02-P26 — Public certificate current design-temperature route

**State:** `PUBLIC_RECORD_ROUTE_QUALIFIED / STOCK_ASSIGNMENT_Q`

**Reference date:** 2026-09-06

## 1. Purpose

P24 established that the Hungarian e-tanúsítás certificate surface can carry current heat-emitter evidence at individual-certificate level, but it did not identify a public real certificate with a current hydronic supply/return calculation pair.

P26 answers one narrow follow-up question:

> Can a real current HET-identified certificate carry an explicit current-system hydronic temperature pair that satisfies the P18 `CALCULATION_INPUT` semantic basis at record level?

The answer is yes for the bounded record audited here.

## 2. Source

Publicly accessible certificate copy:

- `HET-1008-3097`
- issue date shown in the certificate: `2024-05-15`
- public copy URL: `https://pic01.ingatlannet.hu/fajlok/ingatlan/energia-tanusitvanyok/2024/08/12/d168d291dd5a41d3787e6b89162a2b04.pdf`

The document identifies itself as a `HITELES ENERGETIKAI TANÚSÍTVÁNY`, gives the HET identifier, and states that the certificate can be checked in the e-tanúsítás application by identifier or QR code.

This repository does **not** retain the property address, certifier phone number, certifier e-mail address, or other unnecessary personal data from the public copy.

Canonical source ID:

`SRC-B02-HET-1008-3097-PUBLIC-CERTIFICATE-2024`

Source role:

`PUBLIC_MIRROR_OF_HET_CERTIFICATE`

The mirror is not treated as a bulk OÉNY dataset and is not promoted to national authority.

## 3. Current-state separation

The certificate summary explicitly labels the technical-system section as:

`JELENLEGI ÁLLAPOT`

and later separates:

`KORSZERŰSÍTÉSI JAVASLATOK`

This matters because P18 requires current-system evidence rather than proposed retrofit values.

The detailed current heating calculation contains:

- `Fűtési rendszer`
- gas boiler with `radiátoros hőleadás`
- `Szabad fűtőfelülettel rendelkező (radiátoros)`
- `kétcsöves fűtés és modernizált egycsöves fűtés 70 °C/55 °C`
- `Elosztó vezetékek a fűtött téren belül, vízhőmérséklet 70/55`
- `hőlépcső 15 K`

The same document later gives lower-temperature values inside modernization proposal calculations, including a 55/45 °C radiator-system case. That proposal section is deliberately **not** used as evidence of the current system.

Canonical boundary:

`CURRENT-SYSTEM CALCULATION 70/55 C != PROPOSED RETROFIT CALCULATION 55/45 C`

and:

`CALCULATION_INPUT != GENERIC REFERENCE ASSUMPTION`

## 4. P18 interpretation

For this bounded certificate record, the current-system calculation supports:

- current-state system context: explicit;
- emitter: radiator;
- temperature basis: `CALCULATION_INPUT`;
- supply temperature: `70.0 °C`;
- return temperature: `55.0 °C`;
- pair validity: supply > return;
- record identifier: HET certificate identifier present.

This is materially stronger than the generic 55/45 reference rejected in P18. P18 rejects an unbound reference assumption; P26 demonstrates a real certificate where the temperature pair is part of the current-system energetic calculation.

However:

`ONE HET RECORD != COMPLETE OCCUPIED-STOCK DESIGN-TEMPERATURE ASSIGNMENT`

`PUBLIC CERTIFICATE COPY != DOCUMENTED BULK OENY DATASET`

`RECORD-LEVEL CALCULATION INPUT != WBL CELL ASSIGNMENT`

Therefore P26 does not satisfy the national technical-readiness gate.

## 5. Machine-readable control

P26 adds:

`registry/b02_current_design_temperature_controls.csv`

with one bounded control row:

- record: `HET-1008-3097`
- state scope: `CURRENT_STATE`
- emitter: `RADIATOR`
- basis: `CALCULATION_INPUT`
- supply/return: `70/55 °C`
- evidence status: `DER`
- status: `QUALIFIED_RECORD_ROUTE_ONLY`

The row explicitly keeps:

- `wbl_direct_join = NO`
- `current_stock_complete = NO`

## 6. Admission impact

P26 changes the evidence map, not the readiness result.

Before P26, the repository had a qualified public record route for current emitter evidence but no demonstrated real public current-system hydronic pair.

After P26:

`PUBLIC RECORD-LEVEL CURRENT DESIGN-TEMPERATURE ROUTE = QUALIFIED_RECORD_ROUTE_ONLY`

but:

`COMPLETE CURRENT DESIGN-TEMPERATURE AUTHORITY = Q`

and:

`COMPLETE CURRENT-STOCK EMITTER AUTHORITY = Q`

Technical readiness remains:

`TECHNICAL_READINESS_ARCHETYPE = Q`

with exactly:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`

No readiness uplift and no new runtime gate.

## 7. Non-claims

P26 does not claim that:

- HET-1008-3097 is representative of the Hungarian dwelling stock;
- all certificates contain a current hydronic pair;
- 70/55 °C is a national default;
- a gas boiler implies a radiator system without explicit certificate evidence;
- proposal values describe current state;
- the public mirror is an official bulk API;
- the record can be joined directly to the 116,452 WBL cells;
- a single certificate closes either technical-readiness blocker.

## 8. Decision

`CURRENT CERTIFICATE CALCULATION CAN CARRY RECORD-LEVEL HYDRONIC SUPPLY/RETURN EVIDENCE`

`QUALIFIED RECORD ROUTE != COMPLETE STOCK AUTHORITY`

No readiness uplift.
