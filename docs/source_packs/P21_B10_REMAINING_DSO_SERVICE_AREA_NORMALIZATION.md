# B10-P21 — Remaining DSO service-area normalization

Canonical base: `2c2a9a33deab4176d45eeaac83bf195786fd83bf`

## Core rules

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

`OFFICIAL HOSTING != CURRENTNESS PROOF`

`SETTLEMENT NAME != KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

## Scope

P21 re-audits the four DSO service-area authorities that remained unresolved after P20:

- ELMŰ Hálózati Kft.;
- E.ON Dél-dunántúli Áramhálózati Zrt.;
- E.ON Észak-dunántúli Áramhálózati Zrt.;
- MVM Émász Áramhálózati Kft.

The objective is not to force all four to the same status. The objective is to use every public fact that is actually supported while keeping currentness and administrative-identity claims fail-closed.

## MVM Émász — current authority proven

The current MVM Émász business-rule package exposes an official M1 territorial-jurisdiction attachment. P21 therefore registers `SRC-B10-MVM-EMASZ-M1-2026` as a current authority and materializes five bounded whole-settlement observations:

- Abasár — KSH `24554`;
- Adács — KSH `23241`;
- Aggtelek — KSH `09362`;
- Aldebrő — KSH `06345`;
- Harsány — KSH `05847`.

Each row is `OBS / WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN` because the DSO M1 settlement fact is joined to the immutable five-digit KSH settlement identifier authority already established in P20.

The M1 also contains named settlement-parts in parentheses, such as forms like `Abaújdevecser (Encs)` or `Baglyasalja (Salgótarján)`. These are not silently promoted to independent whole-settlement KSH identities. They remain outside the whole-settlement tranche unless a separate administrative/usage-location mapping contract authorizes them.

## ELMŰ / DDÁSZ / ÉDÁSZ — public source yes, currentness still Q

P21 confirms that the three previously identified E.ON-hosted M1 attachments are official published source documents. That makes the facts in them usable as attributed historical/source facts.

However, P21 did not establish that those exact 2025 attachment objects are the current 2026 authority. Therefore their status remains:

`Q_CURRENT_VERSION_PIN_REQUIRED`

and they authorize:

`NO_CURRENT_MEMBERSHIP_AUTHORIZATION`

This is deliberate. Public availability and official hosting do not justify a false currentness claim.

## Completeness boundary

The national canonical registry:

`registry/dso_service_area_membership_crosswalk.csv`

remains header-only.

The bounded tranche registry now contains observed rows from:

- MVM Démász;
- OPUS TITÁSZ;
- MVM Émász.

It still does not represent a complete six-DSO national crosswalk.

## Still Q

- exact current ELMŰ M1 authority;
- exact current E.ON DDÁSZ M1 authority;
- exact current E.ON ÉDÁSZ M1 authority;
- complete normalized MVM Émász settlement inventory;
- partial/named-subsettlement usage-location resolution;
- complete national KSH-to-DSO crosswalk;
- exact programme entity-to-node mapping;
- topology, headroom, limiting-node, reinforcement and programme-incremental CAPEX.

B10 readiness remains **15**. P21 improves attributable usable evidence and removes one false blocker, but it does not prove national completeness.
