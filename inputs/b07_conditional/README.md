# B07 conditional dossier – explicit external inputs

`DOSSIER_TEMPLATE.json` is an unfilled checklist, not a runnable native Case.
Every null is unresolved, not zero or absence. It chooses no life, replacement
year, horizon, price, discount, household comparison or inventory correction.
Use the existing native Case/Asset/Cost/BillInput records and
`b07_case_payload(case)` for a lossless snapshot after external inputs exist.

`audit_accounting(case, b07_use=B07Use(package_root, None))` gives the separate
INCOMPLETE view and exact known missing native paths. No external review is
approved in this package. The ordinary audit remains Q with empty full rows.

The review envelope schema is `B07_CONDITIONAL_USE_V1`: `review_id`, QUALIFIED
status, CONDITIONAL_CASE mode, B07_BATTERY_ONLY scope, a nonempty subset of
`gross_asset_cost` and `unfinanced_cash`, `case_pin`, `producer_pins`,
`leaf_evidence`, `scope_coverage`, `intervals`, and optionally `operations`.
Pins contain package-relative `path` and exact `sha256`. The Case snapshot
must equal the actual complete Case. Producer hashes bind both the preserved
files and the actual imported native B12, source resolver and B04 modules.

The review itself must be in `APPROVED_REVIEW_PINS.json` in the **actual running
repository**, not in a caller-selected dossier. This file is the separately
reviewed deployment trust root and is deliberately not a producer hash input:
review digest and producer digest can be built without a self-referential hash
cycle. Changes require exact-content review of the new trust root and dossier,
then a fresh process. It is not a runtime configuration or owner-per-datum
approval mechanism. An arbitrary QUALIFIED field or caller-supplied digest
cannot admit data. The shipped `reviews` map is empty. Historical evidence is
not rewritten to approve new input or code.

Every participating Scalar/Reference needs a leaf evidence pin with exact
`case_id`, `input_path`, and `value=b07_case_payload(leaf)`. External SCN/ASS/POL
values require OWNER_SCENARIO authority; References require REVIEWED_USE.
Source OBS/DER values need E1/E2 authority and source bytes; E2 also needs the
existing eight criteria and explicit validation debt. Source-labelled gross
Costs must additionally replay through the existing source catalogue resolver
and equal the actual native Cost exactly. The sealed review binds the complete
nonenergy cost scope, all input rows and target use; a partial quote is not a
complete installed total.

Intervals bind exact leg/component/generation and commissioning date, with
inclusive `start`, exclusive `end_exclusive` and explicit integer `order`.
No dates or order are generated. Their end must match native inclusive
operating_coverage_end plus one day. An explicitly ordered same-day transient
generation may have a zero-length interval; its native end equals its start.
Each component chain must cover the whole evaluation window with no gap,
overlap, fork or cross-component inheritance. Different components can operate
in parallel. Service life never creates a replacement date or coverage.

Cost-only does not require inventory correction and excludes energy and terminal
valuation from its named gross sum. Cash is narrower: both legs require their
own B07 asset/energy operation, a complete matched selected-meter Bill set,
explicit receipt-free declaration, and known supported terminal treatment.
Battery-free baseline cash is currently unsupported/Q. Do not create a battery
in that baseline to obtain a result. No SALE, VAT_REFUND, OPERATING or GRANT
Receipt enters this first cash route. NONCASH terminal value is not cash and
is never added to the output. Unknown terminal treatment blocks cash.

Each operation is a pinned JSON document containing exact `case_id`, unique
`id`, `leg`, `component_id`, `asset_generation_id`, `coordinate` equal to
`kWh_DC_discharge_equivalent`, source `opening`/`closing` decimal strings,
`reference_pin`, explicit `reference_fields` pointers for those two quantities,
`application=EXPLICIT_REVIEWED_TARGET_PERIOD`, target `start`/`end_exclusive`,
and `bill_ids`. `bill_bindings` maps every listed Bill to its exact
`physical_ref`, complete encoded quantity Scalar, and
`source_quantity_pointer` into that reference. The full-meter source quantity
must equal the native Bill quantity. The same-leg, single selected-meter/service
Bill intervals must cover the entire operation without gaps or overlap. This
does not rewrite the original source timestamps or admit arbitrary future prices.

Successive used operations, including generation changes, require a pinned
explicit boundary document with exact case/from/to IDs, source closing/opening,
boundary and `kind=EXPLICIT_CONTINUITY`. This only verifies an externally
declared conserved boundary. Unequal inventory, date gaps, implicit reset or
inheritance remains INCOMPLETE: no correction method is supplied. A finite
one-period cash view reports its source opening/closing and is not a claim of
equal-final-state service. Only actually used branches are required; HH2 is not
inferred into a HH1-only case.

The production trust map contains no real dossier; all positive tests are
TEST_ONLY witnesses and patch only their test trust pin. No warranty statement
is a service-life input. NPV, financing, liquidity, affordability, national
weighting and runtime aging remain outside this route.
