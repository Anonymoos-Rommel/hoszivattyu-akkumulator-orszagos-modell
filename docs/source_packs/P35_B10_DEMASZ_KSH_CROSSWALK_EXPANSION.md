# B10-P35 — MVM Démász / KSH crosswalk evidence expansion

Status date: 2026-09-04
Canonical base: `e7cff3b65bec7c82cf2e9ae51fe9003d11b338bb`

## Scope

P35 is an **evidence/data slice**, not a new semantic gate.

It expands the existing `registry/dso_service_area_membership_crosswalk_tranche.csv` with 30 additional whole-settlement MVM Démász memberships in Bács-Kiskun, while preserving the existing P15/P20 boundary:

`SETTLEMENT NAME != KSH SETTLEMENT ID != WHOLE-SETTLEMENT DSO MEMBERSHIP != PARTIAL-SETTLEMENT USAGE-LOCATION MEMBERSHIP != EXACT DSO NODE`

and:

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

## DSO authority

Current official MVM Démász service-area page:

`https://mvmhalozat.hu/aram/oldalak/6454`

The page explicitly separates:

1. settlements whose administrative territory belongs to the service area; and
2. settlements only **partly** inside the service area.

P35 admits only names from the first category.

The following current partial-settlement list remains excluded from whole-settlement materialization:

- Baja
- Csongrád
- Érsekcsanád
- Gyomaendrőd
- Kunszentmárton
- Mohács
- Solt
- Szeghalom
- Szentes
- Tápiószőlős
- Tass
- Tiszakécske
- Tiszasas
- Tiszaug
- Újhartyán
- Zsadány

Therefore `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED` remains active.

## KSH identity authority and derivation boundary

Primary KSH locator:

`https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2025.xlsx`

This is the current 2025 Detailed Gazetteer download and is treated as the primary settlement-identity authority.

The auditable web workflow cannot directly parse the binary XLSX. P35 therefore uses the public reproducible `IrszHnk` CSV only as a machine-readable locator:

`https://github.com/ferenci-tamas/IrszHnk/blob/master/IrszHnk.csv`

The derivative documents the official KSH `hnt_letoltes_2025.xlsx` as its upstream source. It does not replace KSH authority.

Consequently:

`KSH PRIMARY SOURCE LOCATOR + REPRODUCIBLE DERIVED ROW LOCATOR != DIRECT PRIMARY ROW OBSERVATION`

All 30 new P35 rows are therefore **DER**, not OBS.

## Materialized P35 rows

P35 adds exactly these 30 MVM Démász whole-settlement name / KSH-code pairs:

| KSH code | Settlement |
|---|---|
| 03656 | Bátmonostor |
| 11961 | Bátya |
| 08305 | Bócsa |
| 19327 | Borota |
| 32823 | Bugac |
| 33631 | Bugacpusztaháza |
| 10472 | Császártöltés |
| 26471 | Csátalja |
| 16373 | Csávoly |
| 12344 | Csengőd |
| 15699 | Csikéria |
| 12025 | Csólyospálos |
| 10533 | Dávod |
| 07524 | Drágszél |
| 21069 | Dunaegyháza |
| 12566 | Dunafalva |
| 07861 | Dunapataj |
| 11606 | Dunaszentbenedek |
| 14766 | Dunatetétlen |
| 07612 | Dunavecse |
| 04109 | Dusnok |
| 33589 | Érsekhalma |
| 03230 | Fajsz |
| 33598 | Felsőlajos |
| 02954 | Felsőszentiván |
| 02149 | Foktő |
| 31468 | Fülöpháza |
| 33622 | Fülöpjakab |
| 14058 | Fülöpszállás |
| 31848 | Gara |

Together with the 10 historical P20 MVM Démász rows, the evolving tranche now contains **40 MVM Démász whole-settlement rows**. Existing OPUS TITÁSZ, MVM Émász and E.ON-family tranches remain unchanged.

## What P35 does not prove

P35 does not prove:

- complete MVM Démász settlement coverage;
- complete national six-DSO settlement crosswalk;
- any partial-settlement usage-location membership;
- exact supplying substation or feeder;
- complete DSO node inventory;
- programme entity-to-node mapping;
- managed peak, survivability, reinforcement or CAPEX.

`registry/dso_service_area_membership_crosswalk.csv` therefore remains header-only.

The blockers `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`, `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`, `Q-B01-002` and the downstream programme/network evidence blockers remain active.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
