# V1-017 — B09 qualified GUI generation reference

Date: 2026-10-01

Scope: **B09-D01**, deterministic reuse of the already admitted P5/P6/P7 source bundle. This adds the source-to-runtime materializer; it does not reopen source acquisition, change policy, promote OBS, or authorize publication of raw values.

## Result and exact source identity

The six existing acquisition records are reused: P5 `B08B09-P5-R03` (A75 generation), P5 `B08B09-P5-R04` (expected-type installed-capacity manifest), and MAVIR `B09-P6-OP01` through `OP04` (selected net-operational basis). Original byte counts and complete SHA-256 hashes must match both the existing acquisition registries and `registry/b09_gui_reference_manifest.json` before a workbook is parsed. Renamed external files do not change semantic identity: the Python API accepts paths keyed by acquisition ID.

The manifest retains stable source IDs, original official URLs, source-product identity, date-level acquisition provenance, code-mapping authority, pinned hashes, scope, expected reproduction counters, and external-only reuse status. The older acquisition records supply dates rather than exact retrieval timestamps; this checkpoint does not invent timestamp precision or source revision IDs.

Reproduced results:

| Measure | Result |
| --- | ---: |
| UTC PT15M intervals | 35,040 |
| Expected numeric production types | 14 |
| Structural `n/e` production types | 7 |
| Original numeric A75 cells preserved | 485,740 |
| Exact A75 missing-cell recoveries | 4,820 |
| Recovery signs: negative / zero / positive | 4,812 / 6 / 2 |
| Final type × interval supply records | 490,560 |
| MAVIR timestamps with identical overlapping full rows | 26,404 |
| Missing Gas / Oil / Water Reservoir cells | 2 / 4,817 / 1 |

These counts reproduce the existing acquisition/recovery authority. There is no interpolation, estimated replacement series, or zero-fill.

## Source parsing and mapping

`modules/B09/gui_generation_reference.py` uses streaming standard-library XLSX/XML reading. The A75 worksheet's dimension hint is stale; its real XML is approximately 162 MB uncompressed. The adapter reads actual row/cell addresses and removes parsed rows instead of loading a whole-sheet tree. Formula cells, unknown cell kinds, invalid or duplicate addresses, unexpected worksheet identities, missing grids, changed units, and changed production/area/time headers fail closed.

The capacity export defines active versus structural types. The `Total Grand Capacity` footer is explicitly excluded. Numeric capacity, including an explicit zero, is a numeric-type declaration; it is not used as a generation value. All seven structural categories must remain source-native `n/e` at every A75 interval. Active blanks, including whitespace-only text, remain missing until exact P7 recovery.

The official ENTSO-E [PsrType reference](https://transparencyplatform.zendesk.com/hc/en-us/articles/15856995130004-PsrType), updated 2024-10-11 and inspected 2026-10-01, supplies the explicit label-to-Bxx mapping. The GUI's B11 label uses “pondage”; that reference page uses “poundage”. The manifest records this lexical normalization. B25 is Energy storage and remains structural `n/e` in this source bundle.

The GUI header explicitly identifies the generation-only product. The adapter's A01 binding is a production-direction representation for the existing record interface, not a claim that the workbook supplied an XML `businessType` field. The source-semantic caveat `ENTSOE_PUBLISHED_ACTUAL_MAY_INCLUDE_PROVIDER_ESTIMATES` remains explicit.

## MAVIR interval and overlap contract

MAVIR labels are interval ends with explicit UTC offsets. Convert the offset-aware label to UTC, then subtract 15 minutes. DST repeated wall-clock labels remain distinct because the offsets are retained. Parse and validate the raw timestamp sequence and source row counts, then select the explicit half-open interval `[2025-01-01T00:00:00Z, 2026-01-01T00:00:00Z)`.

Some raw files end with an out-of-window timestamp-only row. Numeric payload requirements apply after this time filter; an incomplete in-window row always fails. Every numeric field in overlapping in-window full rows is compared exactly using `Decimal`, including fields not used for recovery. Conflicts and within-artifact duplicate timestamps fail closed.

The lowest acquisition ID provides the deterministic selected copy. Every identical-copy cell locator is retained in the private recovery-lineage CSV, with acquisition ID, exact source SHA-256, source cell, original signed MW value, corresponding A75 blank cell, and a selected-copy flag.

## Existing P7 consumer and evidence boundary

The adapter calls `materialize_recovered_generation_panel` from the existing P7 module. It does not duplicate or replace that consumer's admission logic:

- Numeric A75 cells retain their original values
- Recovery keys equal A75 missing keys exactly
- Only B04, B06 and B12 use the selected MAVIR operational source
- MW enters the existing kW interface through multiplication by 1,000
- Signed recovery is represented as `injection = max(v, 0)` and `source_withdrawal = max(-v, 0)`
- The signed contribution is `injection - source_withdrawal`; the withdrawal is not also added to B08 load

All materialized rows retain **Q** evidence under the existing P7 semantics. The containing reference explicitly carries **E2_PROVISIONAL_BASE / QUALIFIED_E2_MODEL_USE** and **EXTERNAL_ONLY / NOT_ESTABLISHED_FREE_REUSE**. The new adapter verifies the current P7 executable/qualified statuses and Q-B09-001's E2/MODEL_CONTINUE authority. It does not alter the older XML parser's `REUSE_CLEARED` requirement or its verified OBS construction gate.

## Coverage boundary

This bundle supplies the complete **2025 UTC year**, not the complete 2025 Europe/Budapest civil year. The generation intervals from `2024-12-31T23:00:00Z` through `2025-01-01T00:00:00Z` are absent. The B08 2024 load companion cannot stand in for generation. No complete Budapest civil-year or meteorological-winter result is asserted, and both limitations are machine-readable in the manifest and private receipt.

No regional generation allocation, storage dispatch, household effect, tariff/value, network headroom, reinforcement, or programme adequacy result is introduced.

## Private reproduction

From the repository root, set `B09_EXTERNAL_SOURCE_DIR` to a directory containing the six registered external files, then run:

```sh
python tools/materialize_b09_gui_generation_reference.py \
  --source-dir "$B09_EXTERNAL_SOURCE_DIR" \
  --output-dir data/interim/b09_gui_reference
```

The destination must be a fresh directory under the repository's ignored `data/interim`. The tool refuses public paths, symlinked paths, outputs tracked by Git, outputs not covered by the ignore policy, and existing output files. Neither external workbooks nor a complete transformed numeric panel is added to Git.

Outputs:

- `hu_generation_utc_2025_pt15m.csv`: complete P7 supply panel with source-cell provenance
- `recovery_cell_lineage.csv`: all selected and identical-overlap copies for every recovered cell
- `receipt.json`: compact evidence, scope, counts and output hashes

Exact reproduction digests:

- Panel CSV SHA-256: `88d23d3d4ea2d5e5d130106fc3d8c0801e93743759c3012f225d9b2bf3030bc3`
- Recovery-lineage CSV SHA-256: `07067299bd825b68da065aed1233939bc846afccc386c644b993dcd090f88019`

## Verification

- 32 new synthetic-only tests pass; no real source numeric panel is in test fixtures
- 105 B09 tests pass, including the existing observed-generation, signed-recovery and engine contracts
- 8 shared B08/B09-P5 acquisition tests pass
- Registry contracts and B01–B20 dependency gates validate
- Full-source reproduction matches all six exact source hashes and all stated counts
- `git check-ignore` covers every private output; no private output is tracked

Independent review and any later publication/merge are separate steps. This checkpoint alone does not claim those steps occurred.
