# B10-P2 — OPUS TITÁSZ consumption-side headroom evidence

Retrieval/audit date: 2026-09-01

## Exact acquisition

The current official landing page is:

`https://www.opustitasz.hu/ugyfelek/halozati-szolgaltatas-es-termekek/alallomasok-szabad-kapacitasai`

Its linked PDF was fetched directly with a fresh HTTP request. The verified
acquisition metadata is:

- request start UTC: `2026-09-01T20:13:58.2948447Z`
- request end UTC: `2026-09-01T20:13:58.5859373Z`
- final URL: `https://www.opustitasz.hu/storage/documents/ugyfelek/halozati-szolgaltatasok/Al%C3%A1llom%C3%A1sok_szabad_kapacit%C3%A1sai.pdf`
- HTTP status: `200`
- Content-Type: `application/pdf`
- Content-Length: `129805`
- ETag: `"1fb0d-6571d7cb62e71"`
- Last-Modified: `Tue, 21 Jul 2026 11:40:18 GMT`
- exact PDF SHA-256: `3550266167435880f2055497aa5da5d5a4d04240cbfaac4c1425c46b8f4e8e48`
- PDF: one page, A4, unencrypted

The PDF was kept only in an external temporary acquisition directory and is
not committed to the repository.

## Text/render consistency

The audit used `curl.exe`, `pdfinfo`, deterministic local `pypdf` extraction,
`pdfplumber` table extraction, `pdftoppm` page-1 rendering and visual inspection
of the rendered image. The extracted and rendered content agree. Both show the
effective date **2026.07.22**.

The table headers are:

1. `Alállomás kódja`
2. `Alállomás neve`
3. `Jelenlegi szabad kapacitás [MW]`
4. `5 éves előrejelzett szabad kapacitás [MW]`

First three rows:

| station_code | station_name | current MW | five-year MW |
|---|---|---:|---:|
| BAKTA | Baktalórántháza | 0,0 | 0,0 |
| BUJF | Berettyóújfalu | 15,2 | 14,4 |
| BUJV | Balmazújváros | 0,0 | 0,0 |

The required DBDK row is `DBDK / Debrecen Délkelet / 17,4 MW / 12,1 MW`.
The last three rows are `TSZM / Törökszentmiklós / 6,8 / 5,2`,
`TUZS / Tuzsár / 28,8 / 27,8` and `VNAM / Vásárosnamény / 22,4 / 9,7`.
The visual values match the extracted values for these controls and for the
full table.

## Source-native schema and identity

The acquired publication contains 48 consumption-purpose data rows with only:

- `station_code`;
- `station_name`;
- current free capacity in MW;
- five-year forecast free capacity in MW.

There is no separate voltage column, N-1 capacity column or winter-evening
peak column. No voltage is parsed from station names. No N-1 or peak value is
invented.

The code lengths in the acquired snapshot are 4 and 5 characters. The code
`DEBR` occurs twice, for `Debrecen OVIT 11 kV` and `Debrecen OVIT 22 kV`.
Station names are unique, exact `(station_code, station_name)` pairs are unique,
and exact duplicate rows are absent. All 48 codes and numeric fields are
present; no negative numeric value was found.

The canonical OPUS row key is therefore the exact source-native tuple
`(station_code, station_name)`. The OPUS region ID is
`OPUS_TITASZ:<station_code>:<station_name>`. It is deliberately not made to
look like the MVM Démász `MVM_DEMASZ:<code>:<voltage>KV` identity.

## Truth, provenance and legal boundary

The normalized TSV is an external transcription and is **never `OBS`**.

`DER` is possible only with all of the following:

- explicit `REUSE_CLEARED`;
- exact source-PDF SHA-256 equal to
  `3550266167435880f2055497aa5da5d5a4d04240cbfaac4c1425c46b8f4e8e48`;
- exact normalized-text SHA-256;
- `VERIFIED_AGAINST_SOURCE`;
- exact acquired effective date `2026-07-22` and source revision
  `EFFECTIVE_2026-07-22`;
- complete source-native fields;
- all four canonical source references.

Otherwise the row remains `Q`. Explicit zero remains zero; missing remains
missing and `Q`; negative values fail closed. A syntactically valid but different
PDF SHA-256 is rejected rather than treated as the acquired source revision.

The OPUS [legal notice](https://www.opustitasz.hu/jogi-nyilatkozat) states that
downloadable documents and information materials are copyright-protected and
that use beyond personal use, including storage, copying and distribution,
requires prior written consent. Public accessibility therefore does not create
`REUSE_CLEARED`. The raw PDF stays external-only.

The publication and methodology are indicative network information. They do not
grant individual connection permission; `MGT_REQUIRED` remains explicit.

## B10 interoperability boundary

The OPUS adapter has no assessment function because its source-native schema does
not establish the MVM voltage-grain identity or a common cross-DSO key. The MVM
`assess_incremental_demand()` path rejects an OPUS record by type. No county →
DSO/substation, ENTSO-E control-area → substation or household/population/
consumption-share proxy is created. OPUS rows are not aggregated and cannot
produce national or DSO-total headroom.

Q-B10-001, Q-B10-002 and Q-B01-002 remain OPEN. B10 readiness remains 15.

## Registered sources

- `SRC-B10-OPUS-TITASZ-CONSUMPTION-HEADROOM-2026`
- `SRC-B10-OPUS-TITASZ-HEADROOM-LANDING-2026`
- `SRC-B10-OPUS-TITASZ-LEGAL-2026`
- `SRC-B10-OPUS-TITASZ-COMPANY-2026`

No OPUS raw PDF, restricted payload, numeric national dataset, regional-readiness
row, baseline infrastructure row or incremental CAPEX row is committed.
