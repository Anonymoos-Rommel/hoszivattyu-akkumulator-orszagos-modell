# B10-P61 — E.ON ÉDÁSZ geographic-data reuse permission

Status date: 2026-09-09

Canonical base: `e941baec5da8a0d246d0e737f525a02ad142fabf`

## Purpose

P61 records a bounded written reuse permission received from E.ON without publishing the correspondence, its binary file, or personal/contact data.

The permission is provenance metadata only. It is not a new service-area membership source and does not alter any B10 technical or evidence-readiness claim.

## Private permission evidence

A request received by E.ON on `2026-09-03` was answered on `2026-09-09` under docket:

`1/02182346-01/2026/1`

The response was issued by E.ON Ügyfélszolgálati Kft. acting on behalf of E.ON Észak-dunántúli Áramhálózati Zrt.

The operative permission scope is recorded as:

`OPERATING_LICENCE_GEOGRAPHIC_DATA`

The bounded decision is:

`USE_ALLOWED`

The source wording confirms that geographic data contained in the operating licence available on E.ON's rules/legal page may be used.

## Public/private boundary

The response document itself is private evidence and is not committed to the public repository.

Public-repository controls:

- private correspondence binary: `NOT_COMMITTED`
- raw correspondence text: `NOT_COMMITTED`
- personal/contact data: `NOT_COMMITTED`
- private evidence locator/path: `NOT_COMMITTED`
- private evidence storage: `PRIVATE_ARCHIVE_ONLY`
- exact private-document SHA-256 fingerprint:
  `9cb9a07e9cf317db56700072850f09e916f5c3817b5b9babc467e36ba3fa7771`

The hash provides exact private provenance without exposing the document.

## Relationship to the current ÉDÁSZ service-area source

The current repository service-area source remains:

`SRC-B10-EON-EDASZ-M1-CANDIDATE-2025`

The current E.ON ÉDÁSZ Elosztói Üzletszabályzat states that the operating area is the area defined in the electricity-distribution operating licence and that the administrative units belonging to that operating area are listed in M1.

P61 records the current M1 source id only as related lineage.

It does **not** broaden the written permission beyond its exact wording.

Therefore:

`OPERATING-LICENCE GEOGRAPHIC-DATA PERMISSION != BLANKET PERMISSION FOR ALL M1 CONTENT`

`REUSE PERMISSION != SOURCE-TRUTH AUTHORITY`

`REUSE PERMISSION != CURRENTNESS AUTHORITY`

`REUSE PERMISSION != COVERAGE COMPLETENESS`

`REUSE PERMISSION != MODEL ADMISSION`

`REUSE PERMISSION != PROGRAMME USE`

## Licensing boundary

The repository-wide `LICENSE_POLICY.md` remains controlling. Third-party material is not automatically relicensed under the repository's software or documentation licences.

P61 records a claim-specific permission decision only and does not purport to replace any applicable third-party licence, statutory restriction, attribution requirement, database right, trademark right, privacy obligation, or other term outside the exact permission scope.

## B10 effect

P61 resolves a narrow external reuse-permission uncertainty for the permitted E.ON ÉDÁSZ operating-licence geographic data.

It does not resolve any standing technical blocker, including:

- complete KSH-to-DSO membership crosswalk;
- partial-settlement usage-location resolution;
- exact current DSO boundary geometry;
- node mapping;
- hosting capacity or limiting-node evidence;
- reinforcement requirement;
- reinforcement CAPEX;
- programme-incremental CAPEX.

B10 remains `IN_PROGRESS`; no readiness uplift is created by this permission record.

## Canonical files

- `modules/B10/source_reuse_permission.py`
- `registry/dso_source_reuse_permissions.csv`
- `tests/test_b10_p61_eon_edasz_geographic_data_reuse_permission.py`

No E.ON correspondence file or correspondence text is committed.
