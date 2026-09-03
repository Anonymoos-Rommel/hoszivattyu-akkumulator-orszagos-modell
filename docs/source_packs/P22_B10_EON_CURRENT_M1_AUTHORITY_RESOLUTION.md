# B10-P22 — E.ON current M1 authority resolution

Status date: 2026-09-03

## Core rule

`OFFICIAL HOSTING != REGULATORY APPROVAL != CURRENT EUSZ LANDING != EXACT M1 ATTACHMENT IDENTITY`

and

`APPROVED INDEFINITELY != PROVEN EXACT CURRENT M1 FILE`

P21 left ELMŰ Hálózati Kft., E.ON Dél-dunántúli Áramhálózati Zrt. and E.ON Észak-dunántúli Áramhálózati Zrt. at `Q_CURRENT_VERSION_PIN_REQUIRED` because only official E.ON-hosted 2025 M1 candidates had been pinned.

P22 narrows that uncertainty in two stages.

## Regulatory package approval proven

### ELMŰ Hálózati Kft.

- official M1 candidate: `ELMu_elo_usz_melleklet_20250410.pdf`;
- MEKH approval decision: H1728/2025, dated 2025-06-13;
- the decision approves the consolidated distribution business-rule package with appendices and attachments for an indefinite duration;
- a 2026-published ELMŰ compliance report corroborates that the business rules were modified during 2025.

### E.ON Dél-dunántúli Áramhálózati Zrt.

- official M1 candidate: `EDE_elo_usz_melleklet_20241209 (v1).pdf`;
- MEKH approval decision: H442/2025, dated 2025-02-13;
- the decision approves the consolidated distribution business-rule package with appendices and attachments for an indefinite duration and requires publication on the operator website;
- a 2026-published compliance report corroborates the 2025 business-rule modification.

### E.ON Észak-dunántúli Áramhálózati Zrt.

- official M1 candidate: `EED_elo_usz_melleklet_20241209 (v1).pdf`;
- MEKH approval decision: H440/2025, dated 2025-02-13;
- the decision approves the consolidated distribution business-rule package with appendices and attachments for an indefinite duration;
- a 2026-published compliance report corroborates the 2025 business-rule modification.

## Current 2026 E.ON landing authority proven

A current E.ON HMKE declaration published in 2026 explicitly names:

- ELMŰ Hálózati Kft.;
- E.ON Dél-dunántúli Áramhálózati Zrt.;
- E.ON Észak-dunántúli Áramhálózati Zrt.;

and directs users to the official E.ON `Szabályzatok, jogszabályok` page for the operators' current Elosztói Üzletszabályzat.

Therefore the prior residual gate

`Q_CURRENT_LANDING_TO_EXACT_M1_BINDING_REQUIRED`

is now too broad. The current landing itself is proven as the current EÜSZ publication location for all three operators.

## Exact remaining fail-closed gate

The landing's document list is client-side/dynamic in the auditable representation available to this workflow. The current landing does not expose a deterministic machine-readable selector that binds the current EÜSZ package to one exact M1 PDF revision.

Accordingly the remaining blocker is narrowed to:

`Q_EXACT_M1_ATTACHMENT_IDENTITY_REQUIRED`

This is a much narrower claim than P21/P22 initially carried:

- source authenticity is proven;
- MEKH package approval is proven;
- indefinite approval duration is proven;
- the current 2026 E.ON EÜSZ publication landing is proven;
- only the exact M1 file identity inside the current package remains unresolved.

Search absence is not used as proof that no newer M1 exists, and official hosting alone is not used to equate a candidate PDF with the exact current attachment.

## Why no settlement rows are promoted yet

P22 intentionally does **not** materialize ELMŰ/DDÁSZ/ÉDÁSZ settlement memberships into the observed service-area tranche until the exact M1 attachment identity is established.

Therefore:

- no ELMŰ rows are added;
- no E.ON DDÁSZ rows are added;
- no E.ON ÉDÁSZ rows are added;
- `registry/dso_service_area_membership_crosswalk.csv` remains header-only;
- the existing bounded tranche remains three operators only;
- no exact DSO node mapping is minted;
- no topology/headroom/reinforcement/CAPEX claim is affected.

## Closure impact

P22 now proves both regulatory package authority and the current 2026 E.ON EÜSZ landing. The only residual E.ON service-area source blocker is exact M1 attachment identity.

B10 remains `IN_PROGRESS`; readiness remains **15**.