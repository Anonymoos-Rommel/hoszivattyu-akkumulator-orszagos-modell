# B10-P22 — E.ON current M1 authority resolution

Status date: 2026-09-03

## Core rule

`OFFICIAL HOSTING != REGULATORY APPROVAL != CURRENT EUSZ LANDING != EXACT M1 ATTACHMENT IDENTITY`

and

`DER != OBS`

P21 left ELMŰ Hálózati Kft., E.ON Dél-dunántúli Áramhálózati Zrt. and E.ON Észak-dunántúli Áramhálózati Zrt. at `Q_CURRENT_VERSION_PIN_REQUIRED`. P22 resolves that currentness blocker through an approved-package revision-lineage proof, without pretending that the dynamic landing exposes a direct machine-readable file selector.

## 1. Regulatory package approval

### ELMŰ Hálózati Kft.

- M1 attachment revision: `ELMu_elo_usz_melleklet_20250410.pdf`;
- MEKH application received: 2025-04-11, VFEO/697-1/2025;
- MEKH approval: H1728/2025, 2025-06-13;
- approval covers the consolidated EÜSZ package with appendices and attachments for an indefinite duration;
- the ELMŰ EÜSZ main body states that operating-area administrative units are listed in M1;
- an official E.ON H1728 content summary explicitly identifies territorial-jurisdiction modification in M1.

### E.ON Dél-dunántúli Áramhálózati Zrt.

- M1 attachment revision: `EDE_elo_usz_melleklet_20241209 (v1).pdf`;
- EÜSZ main-body revision: `20241209`;
- main body explicitly states that operating-area administrative units are listed in M1;
- MEKH application received: 2024-12-11, VFEO/8-1/2025;
- MEKH approval: H442/2025, 2025-02-13;
- approval covers the EÜSZ with appendices and attachments for an indefinite duration and requires web publication.

### E.ON Észak-dunántúli Áramhálózati Zrt.

- M1 attachment revision: `EED_elo_usz_melleklet_20241209 (v1).pdf`;
- EÜSZ main-body revision: `20241209`;
- main body explicitly states that operating-area administrative units are listed in M1;
- MEKH application received: 2024-12-11, VFEO/119-1/2025;
- MEKH approval: H440/2025, 2025-02-13;
- approval covers the EÜSZ with appendices and attachments for an indefinite duration.

## 2. Current 2026 publication authority

A current E.ON HMKE declaration published in 2026 names all three operators and directs users to the official E.ON `Szabályzatok, jogszabályok` page for their current Elosztói Üzletszabályzat.

In addition, current operator-specific E.ON EÜSZ pages are publicly exposed for DDÁSZ and ÉDÁSZ. The dynamic document selector remains non-machine-readable in this workflow, so P22 does not manufacture a direct OBS edge from page to file.

## 3. Exact M1 identity decision

The combined evidence is strong enough to derive exact package attachment identity at DER level:

`CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE`

The derivation uses:

1. official M1 file on the operator host;
2. exact package revision date alignment where available;
3. EÜSZ main-body cross-reference to M1 for territorial jurisdiction;
4. near-immediate MEKH submission of that package revision;
5. MEKH approval covering appendices and attachments for an indefinite duration;
6. current 2026 EÜSZ publication authority;
7. for ELMŰ, an additional official H1728 content summary explicitly confirming the M1 territorial-jurisdiction modification.

This is deliberately **DER**, not OBS. The absence of a machine-readable dynamic selector prevents a direct observed file-edge claim, but it no longer justifies a blanket currentness Q once the approved-package lineage is complete.

## 4. Bounded materialization

P22 materializes nine exact whole-settlement memberships, three per E.ON-network operator:

- ELMŰ: Acsa `18573`, Alsónémedi `23199`, Apaj `33561`;
- E.ON DDÁSZ: Abaliget `12548`, Ádánd `06080`, Adony `08925`;
- E.ON ÉDÁSZ: Aba `17376`, Abda `11882`, Ács `04428`.

All nine rows are:

- `WHOLE_SETTLEMENT`;
- exact five-digit KSH identifiers;
- `DER` evidence status;
- `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`;
- explicitly not exact DSO-node mappings.

The bounded tranche now contains all six operators.

## 5. What this still does not prove

Six-operator tranche presence is **not** national completeness.

The following remain unresolved:

- full normalized settlement inventory for all six operators;
- partial-settlement and usage-location-specific resolution;
- any complete national KSH-to-DSO service-area crosswalk;
- exact programme entity-to-node mapping;
- complete DSO node inventory;
- topology, headroom, limiting-node, reinforcement and programme-incremental CAPEX claims.

Therefore `registry/dso_service_area_membership_crosswalk.csv` — the national canonical crosswalk — remains header-only.

## Closure impact

P22 removes the ELMŰ/DDÁSZ/ÉDÁSZ current-M1 authority blocker at DER level and gives the bounded tranche representation from all six operators. It does **not** satisfy national crosswalk completeness and does not remove the harder electrical node/topology blockers.

B10 remains `IN_PROGRESS`; readiness remains **15**.
