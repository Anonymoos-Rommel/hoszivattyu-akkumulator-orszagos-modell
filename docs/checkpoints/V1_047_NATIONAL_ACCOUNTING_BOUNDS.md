# V1-047: conditional national count and source-accounting screens

Scope: B01-D01, B02-D01 and B11-D01. This is an additional bounded result in
the existing V1 plan, not a replacement for the complete B01–B20 feasibility
calculation. No source-original bytes, new population estimator, central heat
allocation, national point default, policy choice or complete B12 economics
are introduced. All three slices remain INTEGRATING.

## Source and claim boundary

The consumer is `modules/B02/national_accounting_bounds.py`; its exact existing
input identities and provenance are in
`registry/b02_national_accounting_bounds_manifest.json`.

- `SRC-B02-KSH-CENSUS-API-2022`: KSH 2022 occupied conventional dwellings,
  WBL011 V67, native full-stock joint retrieved 2026-09-05. Use its 116,452
  returned positive cells, not a product of marginals or a synthetic join.
  District heating is the mutually exclusive HEAT12/FUEL3 branch. Forrás: KSH.
- `SRC-B02-JRC-IDEES-HU-2023`: European Commission JRC IDEES-2023 v1 Hungary,
  retrieved 2026-10-01, source release dated 2025-11-14, native 2022 energy
  cells. The pre-existing V1-008 scoped E2 admission, cohort reconciliation and
  five validation debts remain authoritative. JRC is compiled/modelled DER,
  not independently metered actual-population heat. Attribution and reuse
  lineage remain in the existing source/history manifests.

Canonical public source links:
[KSH database](https://nepszamlalas2022.ksh.hu/adatbazis/) and
[JRC Hungary source release](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/JRC-IDEES/JRC-IDEES-2023_v1/JRC-IDEES-2023_HU.zip).
No live re-retrieval or new currentness claim is made by this checkpoint.

All count outputs below are DER aggregations of OBS 2022 census cells. Energy
outputs are DER conditional outer bounds from the admitted E2 source-model
ledger. They are not statistical intervals, actual-population confidence
bounds, or assertions of attainable endpoints. Zero means no evidenced
positive numerical floor. It is not a claim that occupied homes use no heat.

## Count constraints

- Occupied non-district stock: 3,389,817 dwellings.
- Census gas-only non-district group (FUEL11): 1,788,022 dwellings.
- Explicit gas-coded union (FUEL11 + FUEL21 + FUEL22): 2,496,034 dwellings.

These are 2022 group sizes before technical, legal, willingness, financing or
rollout restrictions, not annual gas-use membership or present-day eligible
stock. FUEL23 (123,910 dwellings) retains unresolved gas membership. It is not
silently counted in the explicit union or classified as annually gas-free.

For a caller-declared requirement N of distinct dwellings confined to one of
these groups, N greater than the group count is EXCLUDED_BY_CENSUS_COUNT.
Every N at or below the ceiling is INCONCLUSIVE, including exact equality.
In the explicit illustrative SCN N=2,000,000, a census-gas-only programme is
short by at least 211,978 dwellings. A broader programme is not excluded by
this particular count screen. The example is not an active policy target.

## Source-accounting enclosures

On the same native 2022 JRC end-use, carrier and service/final-energy boundary:

- Gas-derived SH service: 0–18,608.558275484032488 GWh/year.
- Gas SH final energy: 0–27,782.192703750693228 GWh/year.
- All-carrier non-district SH service: 0–29,266.7554342249645332516 GWh/year.

The native Gas.SH.Gas leaf is **natural gas and biogas**. It excludes the gas
cohort's electric circulation and DHW. This does not define a pure purchased
natural-gas, GCV billing, gas-volume or import-displacement ledger. Conversion
is 41.868 TJ/ktoe / 3.6 TJ/GWh = 11.63 GWh/ktoe; no new NCV/GCV bridge is applied.
All-carrier service uses the existing V1-008 full district-cohort exclusion,
subtracts circulation and retains advanced-electric service visibly in its
original source ledger. It is not wholly an HP replacement opportunity.

Each result is conditional on the target being a nonnegative subset of that
specific source ledger. Census membership alone does not establish this
applicability. Algebraically, L = target + remainder, where the remainder
retains unknown nonnegative outside-target and coverage components. Neither
component is forced to zero to close occupied-stock energy. Projection gives
0 <= target <= L. These source-domain enclosures do not bound unrepresented
actual service outside that ledger.

A declared nonempty subset of the census gas-only group still has the entire
gas ledger as its ledger-only energy upper bound. Multiplying selected count
by the full-group mean would assume equal selected/unselected intensities.
An empty selected group has exactly zero source energy and no derived mean.
A one-dwelling ledger cap is deliberately loose and need not be physically
attainable. Better within-group heat or selection evidence can tighten it.

Only for the **whole** census gas-only group, division by 1,788,022 yields a
0–approximately 10.407343 MWh/dwelling/year gas-derived service envelope.
The exact ratio is retained; its displayed Decimal upper is rounded upward
at 50 significant digits. Annual gas exclusivity is additionally needed to
call this total SH. It is never a selected-household intensity estimate.

Gas service is part of all-carrier service. Individual interval endpoints
must not be independently combined, added or multiplied as though they were
one compatible physical portfolio. This slice projects accounting totals;
it does not claim a complete jointly feasible physical uncertainty set.

## Parametric gross avoided-gas threshold

For a caller-supplied minimum annual saving S on the exact native final-energy
boundary, additionally condition on nonnegative replacement savings, no added
gas use, and displacement only of baseline direct-gas SH:

- S > 27,782.192703750693228 GWh/year: EXCLUDED_IF_SOURCE_CONDITIONS_HOLD.
- 0 <= S <= that exact cap: INCONCLUSIVE.

The comparison uses unrounded Decimal values, not the displayed 27.782 TWh.
Equality and a zero requirement do not return feasibility PASS. No positive
guaranteed savings floor is established. Without the monotone replacement
condition, before-minus-after savings may be negative, so the nonnegative
screen does not apply. No actual participant savings, net energy, retail
bill, import value, emissions, fiscal or financing result is inferred.

## Unchanged debt and useful next work

VD-B02-V1-HEAT-UNIVERSE, ENDUSE, EFFICIENCY, ALLOCATION and WEATHER remain
open under the V1-008 admission. Central/selected-stock heat is unpopulated;
probabilities, national peak, installed-electricity reconciliation, rollout,
full cost and national feasibility are not resolved. Existing area bounds
remain area bounds and are not converted to actual heat by this change.

The missing allocation does not block these necessary-condition screens or
independent modules. Stronger claims require compatible evidence/model
restrictions or explicitly labelled scenarios, with sensitivity to the
restriction. No new owner-per-datum gate, custom data request, paid
acquisition, external contact or default policy choice is introduced.

## Reproduction and tests

Default report (no policy or threshold selected):

    python -m modules.B02.national_accounting_bounds

Explicit illustrative count and saving thresholds:

    python -m modules.B02.national_accounting_bounds --rollout-count 2000000 --population CENSUS_GAS_ONLY --gas-saving-gwh 30000

Focused and canonical repository checks:

    python -m unittest discover -s tests -p 'test_b02_national_accounting_bounds.py' -v
    python tools/validate_registry.py
    python -m unittest discover -s tests -v

Tests exercise exact source identities and direct-leaf accounting, group
reconciliation, ambiguous FUEL23, empty and nonempty selection, upper-threshold
equality and one-unit-last-place changes, nonfinite/negative/type rejection,
caller Decimal context before and after first import, explicit CLI scope, and no central/default/feasible
promotion. Exact local review/test receipts accompany the final candidate;
local checks are not hosted CI or scientific validation of national outcomes.

### Independent-review correction

The inherited annual consumer previously calculated its 11.63 GWh/ktoe
conversion at import using the caller's Decimal context. A low-precision
context set before import could silently alter the source totals and reverse
a threshold decision. The conversion now constructs the exact terminating
Decimal directly. Fresh-process precision-1/2/6 regressions verify unchanged
native totals and the correct exclusion of a 28,000 GWh saving requirement.
This repairs numeric context dependence without changing the source, nominal
conversion, normal-precision baseline, heat allocation or evidence tier.
