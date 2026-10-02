# V1-043: civil-year device reference and explicit tariff response

The annual device profile now has a separately named Europe/Budapest civil-2025 handoff into B04. Its energy is DER/E2 under the existing source-rating method. Its pricing is an explicitly conditional, constant-2026-tariff SCN. It is not a complete installed-system or household bill.

## Exact calendar and physical scope

The existing historical weather panel covers 2024-12-31T23:00Z to 2025-12-31T23:00Z: all 8760 physical hours of local civil2025. The new producer renormalizes the existing source annual heat on that exact period. It does not clip or relabel the published UTC2025 result, whose first and last local hours differ. The published UTC/grid producer, its inputs and results remain unchanged. B09's missing previous-year generation hour is not filled by this tariff handoff.

| Source package | Civil2025 device reference, kWh | H heating-season portion | Outside-season portion |
|---|---:|---:|---:|
| Standard |3345.787211706|2907.368479637|438.418732070|
| Ambitious |2472.673257555|2151.590533480|321.082724075|

The four transport segments contain 2519, 2568, 1800 and 1873 physical hours: Jan1–Apr15, Apr16–Jul31, Aug1–Oct14 and Oct15–Dec31. The DST transition days contain 23 and 25 hours. UTC half-open intervals and explicit-offset local intervals are both retained. The annual thermal totals are preserved, but do not become observed2025 demand or actual indoor service.

For comparison, the published UTC2025 device quantities remain 3345.735651340 and 2472.633793065 kWh. These distinct figures must not be substituted for each other. The original package still has incomplete source-rating service in the civil-year probe: 355 above-MAX hours and170.241413671 kWh unserved. It is excluded from complete annual pricing; no backup or larger device is supplied.

## Three public entry points

`modules.B04.annual_reference.calculate_reference` requires the pinned civil weather and an explicit standard/ambitious package. It exposes the known energy without selecting a tariff area, entitlement or fee rule.

`price_response` additionally requires A1 or H, the distributor area and the explicit condition `SOURCE_RATING_ELECTRICITY_AS_IMPORTED_REFERENCE_SCN`. It returns source-backed coefficients, with no evaluated total. H also requires the declared eligible thermal-load and profiled-low-voltage scopes. These declarations do not grant site permission or certify the modelled generator/input ratio as an H eligibility factor.

`evaluate_reference` also requires discounted-allocation arguments and one connection ledger. Missing or invalid arguments cannot become zeros. It invokes the existing native B04 functions and reports reference consumption charges and declared connection charges separately. Its combined arithmetic is the declared reference-plus-connection scenario, not an end-use-attributed or whole-household invoice. B12 cashflow admission remains false.

## Allowances are supplied and consumed once

A1 has two calendar-year portions of settlement windows: Jan–Jul and Aug–Dec. Each gets one caller-supplied allocation, consumed after aggregating all its transport segments. The same remaining headroom is never applied independently to Jan–Apr and Apr–Jul. Other months of those settlement years and household baseline consumption are not recovered from this profile. No2523-kWh headroom default is selected and supplied SCN quantities do not themselves prove an entitlement.

H has two heating-season calls and one continuous Apr16–Oct14 outside-season call. It uses one supplied outside allocation. The informational August split needed for A1 does not reset H's allowance. More granular actual settlement would need its own evidenced period allocations.

At area a, the H reference response is:

`rH(a)*EH +70.104*EO -(70.104-rA1(a))*min(EO,qO) +50.165*mH +153.035*mO`

All rates come from the existing B04 producer; the annual consumer does not duplicate tariff rows, VAT or rate arithmetic. The coefficients are reference quantities. An all-excess intercept in the response is not a selected allowance or an installed-cost bound.

## One connection-fee ledger

Fees belong to a declared connection, not automatically to a device or end use. The supported scenario is an explicitly continuous civil-year connection. `ConnectionLedger` requires an identity, year, coverage and twelve unique `MonthFee` records. Each month contains its applicable tariff regime(s), and exact fractions sum to one. A1 has one regime in every month. H has heating in Jan–Mar/Nov–Dec, outside in May–Sep, and both regimes in April/October. The two crossing-month fractions are mandatory supplied inputs. No automatic day-prorating or6+6-month rule is introduced.

The same ledger is apportioned to native pricing periods, totaling twelve months once. Duplicate/missing months, unknown fractions, inappropriate summer heating regimes and double budgets reject. A zero-energy period retains its connection charge. A1 and H are alternative scenarios, not charges to add together. Device attribution of the connection fee remains unknown; a later explicit end-use allocation must conserve the single connection charge.

For illustration only, supplied day-based fractions15/30 and17/31 would produce1214.222419 HUF/year, compared with1219.2 for6+6 months. The4.977581-HUF difference is small, but does not establish the supplier's actual invoice rule. This comparison does not activate either convention.

## Source and claim boundaries

Both MVM PDFs were reacquired byte-for-byte against the existing pins. The source verifier reproduced56 rate comparisons;90 existing B04/B12 tests passed during source qualification. A current original NJT text was also retained externally. [MVM M.1](https://www.mvmnext.hu/aram/servlet/download?id=16548&type=file) supplies the season and allowance conditions; [MEKH10/2024](https://njt.jog.gov.hu/jogszabaly/2024-10-20-5Z), sections14(1),26(3),(7), supports the existing seasonal fee-rate mapping. Their exact source identities are in the new manifest. No source document or complete profile is republished.

The tariff listing could not be checked through the available web read, so the price boundary remains the accepted2026-10-01 snapshot. Reacquiring identical PDF bytes does not silently establish new currentness. The outputs preserve SCN_CONSTANT_2026_TARIFF_SNAPSHOT, nominal HUF and the source date; they are neither observed2025 bills nor future price forecasts.

The signed installed-minus-rating electricity reconciliation remains unknown, including its meter, season and threshold effects. It cannot be priced by multiplying one annual residual by a single rate. Source gas auxiliary scalars are not removable, time-allocated electric baseline profiles. Whole installed cost, before/after household savings, H site/battery/export permission, programme weights and national claims remain unavailable. No B12 adapter, source-price slice acceptance or existing gate changes.

The implementation is verified separately against synthetic adversarial calendar/accounting cases and genuine pinned civil-year source replay. Exact review, configured-suite and hosted-CI evidence are recorded in the verification receipts; these checks do not establish actual household invoices.
