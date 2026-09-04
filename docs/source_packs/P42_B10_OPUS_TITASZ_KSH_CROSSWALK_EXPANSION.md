# B10-P42 — OPUS TITÁSZ / KSH service-area crosswalk expansion III

## Purpose

P42 is an evidence/data slice only. It extends the bounded OPUS TITÁSZ service-area membership materialization from the current official M1 territorial-jurisdiction attachment without changing any B10 semantic gate.

The core boundary remains:

`BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK`

## Authorities

### OPUS TITÁSZ current M1

Source ID: `SRC-B10-OPUS-TITASZ-M1-2026`

The current 2026 OPUS TITÁSZ business-rule attachment publishes `AZ OPUS TITÁSZ ZRT. TERÜLETI ILLETÉKESSÉGE` as a serialised settlement list. P42 materializes exactly serials **91–130**.

### KSH settlement identity

Source ID: `SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`

The official KSH 2019 gazetteer publishes the five-digit `településazonosító törzsszám`. P42 joins the exact OPUS M1 settlement names to their direct official KSH identifiers.

No fuzzy matching, accent normalization, approximate matching, or identity override is introduced in P42.

## Exact P42 materialization

| M1 serial | KSH code | Settlement |
|---:|:---:|---|
| 91 | 05670 | Gégény |
| 92 | 16568 | Görbeháza |
| 93 | 29443 | Gulács |
| 94 | 33455 | Gyomaendrőd |
| 95 | 28945 | Győröcske |
| 96 | 10126 | Győrtelek |
| 97 | 07676 | Gyulaháza |
| 98 | 19558 | Gyügye |
| 99 | 33774 | Gyüre |
| 100 | 26170 | Hajdúbagos |
| 101 | 03045 | Hajdúböszörmény |
| 102 | 12803 | Hajdúdorog |
| 103 | 10393 | Hajdúhadház |
| 104 | 22406 | Hajdúnánás |
| 105 | 31097 | Hajdúsámson |
| 106 | 05175 | Hajdúszoboszló |
| 107 | 17473 | Hajdúszovát |
| 108 | 29391 | Hencida |
| 109 | 12061 | Hermánszeg |
| 110 | 05616 | Hetefejércse |
| 111 | 13019 | Hodász |
| 112 | 04118 | Hortobágy |
| 113 | 06266 | Hosszúpályi |
| 114 | 34050 | Hunyadfalva |
| 115 | 25636 | Ibrány |
| 116 | 09654 | Ilk |
| 117 | 17075 | Jánd |
| 118 | 07843 | Jánkmajtis |
| 119 | 22859 | Jánoshida |
| 120 | 17589 | Jármi |
| 121 | 30711 | Jászalsószentgyörgy |
| 122 | 15811 | Jászboldogháza |
| 123 | 11004 | Jászkarajenő |
| 124 | 21111 | Jászladány |
| 125 | 13143 | Jéke |
| 126 | 02307 | Kaba |
| 127 | 04923 | Karcag |
| 128 | 31404 | Kállósemjén |
| 129 | 27225 | Kálmánháza |
| 130 | 02671 | Kántorjánosi |

P42 therefore adds exactly **40 whole-settlement memberships** and expands the bounded OPUS TITÁSZ materialization from 90 to **130 materialized rows**.

The P42 boundary ends at M1 serial **130, Kántorjánosi**. M1 serial **131, Kemecse** is deliberately not materialized by P42.

## Truth status

Every new P42 row is:

- `coverage_scope = WHOLE_SETTLEMENT`
- `usage_location_requirement = NONE`
- `evidence_status = OBS`
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`
- bound to both the current OPUS M1 authority and the official KSH five-digit settlement identifier authority.

This is direct observed source binding at the service-area membership grain only.

## Fail-closed semantic boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

P42 records only bounded public facts needed for the model contract. It does not republish the source document or claim a reconstructed complete source database.

## What P42 does not prove

P42 does **not** claim:

- complete OPUS TITÁSZ settlement inventory materialization;
- complete national KSH-to-DSO membership coverage;
- resolution of partial-settlement or usage-location membership;
- exact programme entity-to-node mapping;
- exact DSO node identity or topology;
- headroom sufficiency;
- limiting-node status;
- reinforcement need or reinforcement cost;
- programme-incremental CAPEX.

Service-area membership remains strictly upstream of node, headroom, network-study, reinforcement and CAPEX authority.

## Canonical and closure state

`registry/dso_service_area_membership_crosswalk.csv` remains header-only.

The following blockers remain active:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

P42 does not change module status. B10 remains `IN_PROGRESS` and readiness remains **15%**.

## Historical lineage

- P20: OPUS M1 serials 1–10
- P40: serials 11–50
- P41: serials 51–90
- P42: serials 91–130

The resulting 130-row OPUS tranche is still a bounded partial materialization, not a complete operator crosswalk.
