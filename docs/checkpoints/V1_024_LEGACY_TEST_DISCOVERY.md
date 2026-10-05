# V1-024: legacy unittest discovery repair (draft)

## Scope

This validation-only checkpoint admits 109 previously dormant function tests in
16 B05/B06/B10 modules through explicit per-module `load_tests` lists. Each
function becomes its own `unittest.FunctionTestCase` with its original name.
The configured `python -m unittest discover -s tests -v` runner therefore
executes them. The separate `tests/test_v1_024_legacy_discovery.py` guard checks
the exact module/name inventory and prevents missing or aggregated admission.

The 101 previously passing function bodies and all 36 existing helpers are
unchanged. Only the eight historically superseded functions are refreshed.
B08's existing bridge still covers its 31 functions in one discovered case;
B05's `test_map` remains a fixture used by its 15 existing cases. Neither is
new coverage. No skip, expected failure, broad status allowance, production
change, source-data change or readiness uplift is introduced.

## Authority corrections

- B05 P10 retains its historical capacity-only and defrost exclusions. The live
  Q-B05-001 test now binds the physical-only closure to the admitted P11/P12/P13
  product rectangles and stable source IDs. Market, procurement and universal
  product qualification remain excluded; readiness remains 80/60
- B05 P6 retains the regulatory fallback as POL with no canonical default.
  P15/P23 product-specific Cdh lineage supersedes the former absence claim.
  Exact 0.9 remains ambiguous, certified Cdh cannot become a generic hourly
  multiplier, and runtime cycling penalties remain Q
- B06 P61 keeps its exact baseline fixture. Missing P62/P63 effect authority
  must produce the specific Q reason, no annual/peak result, no applied
  intervention, no B05 sizing output and no S1 admission. The non-national
  question assertion is only normalized for capitalization
- B06 P62 retains the exact annual/peak pair and PLANNED_DESIGN DER status.
  Later P63/P64 methodology closures bind explicit physical inputs, independent
  annual/peak methods, overlap prevention, and realized completion AND linked
  outcome. Both national-prevalence and national-completed-stock flags stay NO
- B06 P64 tests the structured exclusion of permits from technical S2 while
  retaining the separate mandatory programme legal/delivery gate. Existing
  P59 executable witnesses retain pending-Q and final-refusal-BLOCKED behavior
- B10 P17 binds each ELMU/EON_DDASZ/EON_EDASZ bounded consumption source to its
  own exact P34 source ID and matching operator authority, consumption role,
  currentness and publication URL. Generation-only publication, legal duty,
  a common URL, missing authority or an operator mismatch cannot qualify.
  Historical P17 exclusions and current incomplete-inventory/downstream-Q
  checks remain in force; all seven P34 functions now execute

The corresponding authority records remain in `registry/heat_pump_sources.csv`,
`registry/b05_p11_teknopoint_cold_high_supply_rectangle.csv`,
`registry/b05_p12_ecpower_cross_manufacturer_cold_surface.csv`,
`registry/b05_p13_wamak_extreme_cold_closure.csv`,
`registry/b06_p63_effect_surface_authority.csv`,
`registry/b06_p64_realized_completion_authority.csv`,
`registry/b02_p59_site_legal_delivery_authority.csv` and
`registry/dso_consumption_publication_authorities.csv`. This checkpoint changes
none of those authorities and admits no new observed dataset or model result.

## Validation before integration

Accepted parent: `2cd8767fd5db7f98bf20279930c9668f6896bd50` (V1-023/B11).
The prior read-only audit directly invoked these same 109 functions on both
`16962c2f6e8313b68f2c0736718a03144c5b01b8` and the frozen B11 tree
`9ef4c8e3bac7ba7c049b865b3e3044c7378cdc12`: 101 passed and the same eight failed.
Those were diagnostic counts, not extra configured CI cases.

Local focused validation of this draft on 2026-10-02:

- All 109 formerly dormant cases pass through unittest discovery; call tracing
  confirms each original function executes exactly once
- The one separately counted discovery guard passes
- 46 existing later-authority witness cases pass; these are not new coverage
- 56 external negative probes are rejected, including source/operator mismatch,
  generation/legal-only authority, generic Cdh runtime use, unauthorized S1,
  forbidden national claims and missing/aggregated discovery
- Registry validation and `git diff --check` pass
- Full configured discovery collects 2,886 cases: 2,776 existing + 109 admitted
  functions + one guard. Collection is not a full-suite pass

The full aggregate run and independent exact-byte review are held for
coordinated integration and must be recorded separately. This draft makes no
publication, CI-success or merge claim.
