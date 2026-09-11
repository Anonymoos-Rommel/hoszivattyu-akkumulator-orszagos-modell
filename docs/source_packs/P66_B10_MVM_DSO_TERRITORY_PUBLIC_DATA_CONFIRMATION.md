# B10-P66 — MVM DSO territory public-data confirmation

Status date: `2026-09-11`

Canonical base: `915a4ab9ba2247c0106d008b6c08efb8ca9d3820`

## Purpose

P66 records a bounded written confirmation received from MVM concerning the public-data status of electricity-distribution territory information.

The private correspondence is provenance evidence only. Its binary, full text, personal/contact data, and private storage location are not committed to the public repository.

## Private evidence identity

- request date recorded in the response: `2026-09-09`
- response date: `2026-09-11`
- docket: `EM0140-15118-1/2026`
- issuer recorded at organisation level: `MVM Ügyfélkapcsolati Kft.`
- exact private-document SHA-256:
  `bb38bdd2139ee92411111abcbdbafddc1e524321bc91a4708c96a34f0278f3f1`
- storage class: `PRIVATE_ARCHIVE_ONLY`

The document itself is not committed.

## Source-supported confirmation

The written response supports the following bounded statements:

1. the distribution territories of the individual distributors are public data;
2. the response points to the operating-licence and business-rules document family as the publication location;
3. the response identifies the relevant MVM Émász and MVM Démász publication routes;
4. the response characterises the published information as informative.

No broader permission or technical conclusion is derived from the correspondence.

## Canonical machine decision

Covered operators:

- `MVM_EMASZ`
- `MVM_DEMASZ`

Data scope:

`DSO_DISTRIBUTION_TERRITORY`

Public-data decision:

`PUBLIC_DATA_CONFIRMED`

Referred publication family:

`OPERATING_LICENCE_AND_BUSINESS_RULES`

Publication character:

`INFORMATIVE`

Authority result:

`QUALIFIED_PUBLIC_DATA_CONFIRMATION`

## Public/private boundary

The repository records only bounded provenance metadata and the cryptographic fingerprint of the private evidence.

Public-repository controls:

- correspondence binary: `NOT_COMMITTED`
- raw correspondence text: `NOT_COMMITTED`
- personal/contact data: `NOT_COMMITTED`
- private storage path/locator: `NOT_COMMITTED`
- exact SHA-256 fingerprint: `COMMITTED`

## Non-equivalence boundaries

`PUBLIC DATA != EXPLICIT REUSE LICENCE`

P66 does not replace or broaden the separate P65 E.ON written reuse-permission decision.

`PUBLIC DISTRIBUTION-TERRITORY DATA != EXACT CURRENT BOUNDARY GEOMETRY`

`INFORMATIVE PUBLICATION != CLAIM-SPECIFIC NETWORK-STUDY AUTHORITY`

`PUBLIC STATUS != SOURCE-TRUTH AUTHORITY`

`PUBLIC STATUS != COVERAGE COMPLETENESS`

`PUBLIC STATUS != DSO_SUBSTATION MAPPING`

`PUBLIC STATUS != HOSTING-CAPACITY AUTHORITY`

`PUBLIC STATUS != LIMITING-NODE AUTHORITY`

`PUBLIC STATUS != MODEL ADMISSION`

`PUBLIC STATUS != PROGRAMME USE`

## B10 effect

P66 strengthens provenance for the MVM Émász and MVM Démász service-area evidence route by recording an operator-side written confirmation that the distribution-territory information is public data and by pinning the publication family referred to in that response.

It does not by itself alter B10 readiness or resolve any technical blocker. In particular it does not resolve exact current boundary geometry, partial-settlement allocation, exact node mapping, hosting capacity, reinforcement requirement, reinforcement cost, or programme-incremental CAPEX.

## Canonical files

- `modules/B10/mvm_public_data_confirmation.py`
- `registry/dso_source_public_data_confirmations.csv`
- `tests/test_b10_p66_mvm_public_data_confirmation.py`

No MVM correspondence file or correspondence text is committed.
