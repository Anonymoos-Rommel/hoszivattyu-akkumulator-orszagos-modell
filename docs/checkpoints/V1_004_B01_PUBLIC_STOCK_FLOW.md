# V1 checkpoint 004: public KSH stock-flow controls

Scope: B01-D01 partial integration. Forrás: [KSH](https://www.ksh.hu/), CC BY 4.0. No custom statistical delivery is used.

## Accepted quantity and period

Two public STADAT tables, both updated 2026-07-06, provide [county stock](https://www.ksh.hu/stadat_files/lak/hu/lak0017.html) and [calendar-year completions/removals](https://www.ksh.hu/stadat_files/lak/hu/lak0022.html). The published [methodology](https://www.ksh.hu/docs/hun/modsz/lak_modsz.html) defines total stock to include occupied and unoccupied dwellings plus occupied holiday units. Post-census stock is an official census roll-forward, not a fresh enumeration. The source's 2022 column is **2022-10-01**, despite the general January-1 table title; subsequent selected stock dates are January 1.

The public UTF-8 extracts contain 100 county/date stock rows and 60 county/year flow rows. The 2022 census controls retain OBS; later official rolled-forward stock values are labelled DER with their source method, and administrative completions/removals retain OBS. These are authoritative E1 controls within that declared quantity, not an E1 technical-eligibility estimate.

## Actual reconciliation

The real source data reconcile for all 20 counties in all three full calendar years:

| Year | Opening total stock | Completed | Removed | Closing total stock | National residual |
|---|---:|---:|---:|---:|---:|
| 2023 | 4,586,878 | 18,647 | 1,619 | 4,603,906 | 0 |
| 2024 | 4,603,906 | 13,295 | 1,617 | 4,615,584 | 0 |
| 2025 | 4,615,584 | 12,062 | 1,554 | 4,626,092 | 0 |

The 2022-10-01 stock is 4,580,538. A full 2022 construction/removal flow is not applied to its three-month gap to 2023-01-01. Each county is included once; regional and national aggregate source rows are reconciliation controls, not extra model population.

## Reproduction and integration

`tools/extract_b01_public_stock_flow.py` verifies both original CSV hashes, decodes ISO-8859-2, selects the correct measure sections, maps names to existing canonical county IDs, and reconciles county sums to the source's national totals. Missing/noninteger cells fail closed; a documented non-occurrence marker is accepted as zero only when explicitly enabled for that flow source.

The exact original non-UTF-8 CSV bytes are retained in ignored local raw storage and their digests are in `registry/b01_public_stock_flow_manifest.json`. The current UTF-8-only publication route has not archived original bytes in Git; that archive is not claimed. The published extracts preserve selected source values and disclose selection, date, code and encoding transformations under the [KSH reuse terms](https://www.ksh.hu/copyright).

`modules/B01/public_stock_flow.py` consumes the two canonical extracts and returns county-level bridges. It rejects unsupported time scopes, retains a nonzero residual rather than forcing balance, and explicitly declares that occupancy and eligibility are not identified. Re-extraction from the acquired raw files reproduced both committed extracts byte-for-byte.

## Remaining boundary

The existing 2022 occupied and non-district-heated B01/B02 universe is unchanged. Total-stock growth does not reveal vacancy activation, heating-system changes, renovation, participation, terminal transition success or individual site permission. Those are not replaced by a stock multiplier. No programme target, readiness score, Q-B02-001 or entire B01-D01 slice is closed here.
