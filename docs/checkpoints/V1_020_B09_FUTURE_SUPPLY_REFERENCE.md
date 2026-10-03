# V1-020: B09 future supply source reference

## Scope

This checkpoint adds a **research/reference-only** intake for two exact external
ERAA 2025 snapshots. It does not select the programme's central future, authorize
a future runtime, join observed generation to future capacity, or change an
existing B09 engine. B09-D02 acceptance remains subject to independent review and
the wider slice requirements.

- National Trends, pre-EVA: 88 HU00 capacity records, 22 in each source target year
- Current amended cost-based EVA: 49 HU00 non-cumulative capacity-change records
- Target years: 2028, 2030, 2033 and 2035
- Every selected source field, source row and exact Decimal MW value is preserved
- All future records remain `SCN`, including explicit zeros

The adapter requires explicit source ID, revision, scenario, model stage, target
years, capacity-date convention and resource-role selection. It returns only
source-present rows and never fills absent technology/year combinations. A
caller can select reference rows without declaring that reference the programme
baseline. No owner-per-datum approval mechanism is introduced.

## Artifacts

- `modules/B09/future_supply_reference.py`
- `tools/materialize_b09_future_supply_reference.py`
- `tests/test_b09_future_supply_reference.py`
- `registry/b09_future_supply_reference_manifest.json`

The public manifest contains stable source IDs, exact artifact/member hashes,
revision and retrieval metadata, semantic scope and rights caveats. Original
ZIP/XLSX/PDF bytes and normalized numeric outputs remain external-only. No
transformed raw text is published as a substitute for an uncleared source file.

## Source and revision authority

The current [ERAA 2025 modelling-data page](https://www.entsoe.eu/eraa/2025/modelling-data/)
links the input ZIP. Its `GenerationCapacities.csv` mixes ERAA 2024, preliminary
2025 and final 2025 records. The intake selects only `ERAA 2025 final` and `HU00`.
The input scenario is National Trends; it is not the post-EVA central reference.

The current [reports page](https://www.entsoe.eu/eraa/2025/reports%26results/)
links an amended report and the cost-based/revenue-based EVA workbook. The
selected workbook snapshot was last modified 30 July 2026. Only `Cost Based` is
read. The separate `Revenue Based` A/B implementations are not substituted for
it. The [ACER 1 July 2026 corrigendum](https://www.acer.europa.eu/sites/default/files/documents/Individual%20Decisions_annex/20260701-Corrigendum-Annex-II-ACER-Decision-06-2026-ERAA-2025.pdf)
and the amended edition must accompany interpretation of the current reference.

The snapshot revision IDs are adapter identifiers bound to exact bytes and HTTP
revision context, not invented publisher version numbers. Changed bytes,
member hashes or semantic selectors fail closed; there is no automatic update
or network request in the consumer.

## Boundaries retained

1. `Operational_Status` becomes market-treatment status. It does not establish
   current commissioning, lifecycle or financing. Those record fields explicitly
   remain `NOT_ESTABLISHED_BY_REFERENCE`.
2. Generation, storage, demand response and consumption have separate roles.
   Electrolysers and power-to-heat cannot enter a generation total. No MW-summing
   function or conversion to hourly delivered generation is provided.
3. ERAA uses a 1 July capacity threshold. MAVIR HFT uses start-of-year target
   conventions, with within-year connection dates distinguished separately.
   This adapter cannot silently shift or interpolate these horizons.
4. EVA changes remain separate from input capacities and are non-cumulative
   relative to National Trends. They are not observed plant retirements,
   completed investment, or incremental programme effects.
5. Maintenance, outages, reserves, storage SOC, correlated weather and network
   boundaries remain metadata-only references here. No dispatch, import
   availability guarantee, adequacy/LOLE calculation or revenue is admitted.
6. B07 assets already included in B08 net load cannot be counted again by
   reusing national residential PV/battery assumptions. No such join occurs.
7. ERAA and MAVIR share TSO/PEMMDB lineage; they are not independent observations.
   MAVIR's May 2026 planning volume and HFT2025 approval are contextual controls,
   not a replacement capacity dataset or financing certificate.

## Rights and use qualification

`materialization_scope = RESEARCH_REFERENCE_ONLY`

`model_use_status = SOURCE_SPECIFIC_REVIEW_REQUIRED`

`public_raw_reuse_status = REPOSITORY_COPY_NOT_CLEARED`

`central_future_baseline_status = NOT_SELECTED`

The [ENTSO-E website disclaimer](https://www.entsoe.eu/about/legal-and-regulatory/disclaimer/)
permits non-commercial personal downloading subject to retained notices while
restricting broader copying/distribution/reuse absent applicable permission.
The PECD-specific licence does not automatically cover capacity/EVA files.
Research materialization and public raw republication are separate questions.
Existing Q-B09-001 and observed-generation qualification do not cover these new
sources automatically. The adapter makes no model-use permission determination.

## Reproduction

Supply the two exact external files named below. Run from the repository root;
`SOURCE_ROOT` is the local directory holding those files. Use a fresh ignored
output directory for each run. The command performs no acquisition.

```sh
python tools/materialize_b09_future_supply_reference.py \
  --source-file "$SOURCE_ROOT/ERAA_2025_Dashboard_RawData.zip" \
  --source-id SRC-B09-ERAA2025-DASHBOARD-FINAL \
  --source-revision ERAA2025_FINAL_INPUTS_SNAPSHOT_2026-02-04 \
  --scenario-id ERAA2025_NATIONAL_TRENDS \
  --model-stage PRE_EVA_RESOURCE_CAPACITY \
  --capacity-date-convention ERAA_1_JULY_CAPACITY_THRESHOLD \
  --target-years 2028 2030 2033 2035 \
  --resource-roles GENERATION STORAGE DEMAND_RESPONSE CONSUMPTION \
  --output-dir data/interim/b09_future_reference_capacity

python tools/materialize_b09_future_supply_reference.py \
  --source-file "$SOURCE_ROOT/ERAA_2025_EVA.xlsx" \
  --source-id SRC-B09-ERAA2025-EVA-CURRENT \
  --source-revision ERAA2025_COST_BASED_EVA_SNAPSHOT_2026-07-30 \
  --scenario-id ERAA2025_AMENDED_CENTRAL_REFERENCE_COST_BASED \
  --model-stage POST_EVA_CAPACITY_CHANGE \
  --capacity-date-convention ERAA_1_JULY_CAPACITY_THRESHOLD \
  --target-years 2028 2030 2033 2035 \
  --resource-roles GENERATION STORAGE DEMAND_RESPONSE CONSUMPTION \
  --output-dir data/interim/b09_future_reference_eva
```

Output is a source-row-preserving CSV plus a metadata receipt. Public/tracked
repository output, symlinked paths and overwriting existing outputs are rejected.
Archive paths, duplicated ZIP members, XML formulas/entities, incorrect cell
addresses, unknown roles/statuses and malformed numbers are rejected. No source
archive member is extracted onto the filesystem.

## Verification at author handoff

Focused command: `python -m unittest tests.test_b09_future_supply_reference -v`

Nineteen synthetic-only tests passed. The external reproduction compared every
field and source row against the separately prepared research extracts for all
137 records. Normalized CSV SHA-256:

- Capacity: `2a481c65da2b3ac962d00e37ebf356a53a6c35d1c3cf049808de6272a21489b2`
- Cost-based EVA: `9561038c694433c42bce0c0e0afbae1a99f208950770c0943529e4db0c7a790e`

On the shared host, the two source parses took approximately 0.016 and 0.020
seconds; process peak RSS was 19,796 KiB. These are execution diagnostics,
not model-performance or adequacy claims. No full suite was run because of
shared-host pressure. Public text uses LF; the handoff verifies Git-clean blob
bytes against worktree bytes before independent review. No commit or publication
was made by the author.
