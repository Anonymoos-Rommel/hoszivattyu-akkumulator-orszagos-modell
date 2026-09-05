# B10-P64 — Operational spatial coverage acceptance

## Decision

The P63 resolved-only DSO service-area projection is accepted as **operationally complete for downstream B10 national/regional modelling**, with the unresolved residual disclosed numerically and preserved as Q.

Canonical operational status:

`OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL`

This is a modelling-policy acceptance. It is **not** a claim that every Hungarian settlement has a fully proven whole-settlement DSO membership.

## National denominator

KSH reports **3,155 settlements** for Hungary at 2025-01-01.

Primary identity authority already used by the B10 crosswalk programme:

`SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`

Official KSH detailed gazetteer locator:

`https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2025.xlsx`

Independent KSH STADAT count check:

`https://www.ksh.hu/stadat_files/fol/hu/fol0007.html`

## Exact P64 accounting

| Category | Settlement count | Share of 3,155 |
|---|---:|---:|
| Exact whole-settlement DSO membership proven | **3,052** | **96.735341%** |
| Exact partial-only settlement resolution | **1** | **0.031696%** |
| Any effective resolved settlement presence | **3,053** | **96.767036%** |
| Whole-settlement membership not proven | **103** | **3.264659%** |
| No materialized effective whole or exact-partial resolution | **102** | **3.232964%** |

The one exact partial-only settlement is **Tass**, through the P61 record:

`ELMU:TASS:UDULOTERULET`

Therefore the **103 whole-unproven settlements include Tass**. They are not an additional 103 on top of Tass.

## Interpretation

For national B10 modelling, the 3,052 exact whole-settlement memberships plus the one exact Tass usage-location resolution constitute the accepted current spatial surface.

The remaining 102 settlements do **not** block continuation of B10. They remain an explicitly disclosed residual uncertainty set.

The residual must not be converted into invented DSO assignments. Where a downstream calculation requires an exact unresolved geography, that row remains Q or is excluded according to the consuming contract.

## Frozen boundaries

`OPERATIONALLY COMPLETE != 100% EVIDENCE COMPLETE`

`3052 EXACT WHOLE MEMBERSHIPS != 3155 EXACT WHOLE MEMBERSHIPS`

`103 WHOLE-UNPROVEN SETTLEMENTS != 103 INCORRECT SETTLEMENTS`

`1 EXACT PARTIAL-ONLY SETTLEMENT != WHOLE-SETTLEMENT MEMBERSHIP`

`KNOWN RESIDUAL COUNT != ENUMERATED RESIDUAL IDENTITIES`

`MISSING OR UNRESOLVED GEOGRAPHY != ZERO`

`DISCLOSED RESIDUAL != AUTHORITY TO IMPUTE DSO MEMBERSHIP`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

## Downstream policy

P64 closes the **operational coverage acquisition loop**. Further one-settlement-at-a-time service-area hunting is not required for B10 progression unless a future downstream claim specifically depends on one of the residual settlements.

The evidence-completeness state remains:

`EVIDENCE_NOT_EXHAUSTIVE`

This preserves audit truth while allowing the model to proceed on a 96.767036% resolved settlement-presence surface.

B10 module readiness is not independently uplifted by this policy decision; downstream programme-node, managed-peak, reinforcement and timed-CAPEX gates remain separate.
