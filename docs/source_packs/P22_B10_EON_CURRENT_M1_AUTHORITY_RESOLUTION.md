# B10-P22 — E.ON current M1 authority resolution

Status date: 2026-09-03

## Core rule

`OFFICIAL HOSTING != REGULATORY APPROVAL != CURRENT LIVE ATTACHMENT BINDING`

and

`APPROVED INDEFINITELY != PROVEN AS THE EXACT SEPTEMBER-2026 LANDING TARGET`

P21 left ELMŰ Hálózati Kft., E.ON Dél-dunántúli Áramhálózati Zrt. and E.ON Észak-dunántúli Áramhálózati Zrt. at `Q_CURRENT_VERSION_PIN_REQUIRED` because only official E.ON-hosted 2025 M1 candidates had been pinned.

P22 narrows that uncertainty materially.

## What is now proven

### ELMŰ Hálózati Kft.

- official M1 attachment: `ELMu_elo_usz_melleklet_20250410.pdf`;
- MEKH approval decision: H1728/2025, dated 2025-06-13;
- the decision approves the consolidated distribution business-rule package with appendices and attachments for an indefinite duration;
- a 2026-published ELMŰ compliance report corroborates that the business rules were modified during 2025.

### E.ON Dél-dunántúli Áramhálózati Zrt.

- official M1 attachment: `EDE_elo_usz_melleklet_20241209 (v1).pdf`;
- MEKH approval decision: H442/2025, dated 2025-02-13;
- the decision approves the consolidated distribution business-rule package with appendices and attachments for an indefinite duration;
- a 2026-published compliance report corroborates the 2025 business-rule modification.

### E.ON Észak-dunántúli Áramhálózati Zrt.

- official M1 attachment: `EED_elo_usz_melleklet_20241209 (v1).pdf`;
- MEKH approval decision: H440/2025, dated 2025-02-13;
- the decision approves the consolidated distribution business-rule package with appendices and attachments for an indefinite duration;
- a 2026-published compliance report corroborates the 2025 business-rule modification.

## What remains unresolved

The current E.ON rules landing is live in September 2026, but the document list is client-side/dynamic in the auditable representation available to this workflow. Therefore the exact edge

`CURRENT RULES LANDING -> EXACT M1 ATTACHMENT`

cannot yet be read back deterministically.

This means the prior broad blocker is narrowed from:

`Q_CURRENT_VERSION_PIN_REQUIRED`

to:

`Q_CURRENT_LANDING_TO_EXACT_M1_BINDING_REQUIRED`

for all three E.ON-network operators.

This is not a claim that the 2025 packages are obsolete. It is the opposite: source authenticity and regulatory approval are now proven. The remaining uncertainty is only the exact current-live selector edge as of 2026-09-03.

## Why no settlement rows are promoted in P22

P22 intentionally does **not** materialize ELMŰ/DDÁSZ/ÉDÁSZ settlement memberships into the observed service-area tranche. Regulatory approval of a package does not, by itself, satisfy the project's stricter currentness rule when the exact live landing-to-M1 binding cannot be read back.

Therefore:

- no ELMŰ rows are added;
- no E.ON DDÁSZ rows are added;
- no E.ON ÉDÁSZ rows are added;
- `registry/dso_service_area_membership_crosswalk.csv` remains header-only;
- the existing bounded tranche remains three operators only;
- no exact DSO node mapping is minted;
- no topology/headroom/reinforcement/CAPEX claim is affected.

## Closure impact

P22 improves evidence quality and makes the remaining E.ON currentness blocker much narrower, but it does not complete the six-DSO crosswalk.

B10 remains `IN_PROGRESS`; readiness remains **15**.
