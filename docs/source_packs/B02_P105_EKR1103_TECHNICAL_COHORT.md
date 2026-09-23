# B02-P105 — EKR 1103 TECHNICAL COHORT DISCOVERY

## Goal

Attack the P104 sub-residual:

`EKR_1103_TECHNICAL_COHORT_AGGREGATE_REQUIRED`

by exhausting the current public MEKH/HEM and public EKR-market routes before
falling back to an administrative extract.

## 1. Public HEM surface

The current MEKH HEM module handbook documents a public record lookup.

The public lookup is **identifier-bound**: a HEM identifier is supplied and the
record can expose generic HEM fields including saving amount, implementation
time, lifetime and a public `Megtakarítás típusa` label.

The same handbook exposes a public global summary with:

- total reported/realized HEM count;
- aggregate verified saving.

P105 found no documented public bulk enumeration, measure-code filter or export
that would turn this into a current 1103 cohort.

Therefore:

`KNOWN HEM ID LOOKUP != COHORT ENUMERATION`

and:

`GLOBAL HEM COUNT != EKR 1103 COUNT`.

## 2. The public saving-type label is not silently 1103

The handbook itself separates two concepts.

In the HEM registration workflow, the HEM/saving type distinguishes catalogue
versus individual-audit routes.

Separately, the measure sheet contains:

`Intézkedés típusa`

as its own dropdown, followed by measure-specific technical parameters.

The public record is described with a `Megtakarítás típusa` label.

Without explicit semantic authority equating that public label to the detailed
measure-type field, P105 forbids:

`PUBLIC SAVING TYPE -> ACTION CODE 1103`.

This is a deliberate fail-closed decision.

## 3. Administrative data are richer

The current 17/2020 MEKH data-content regulation separates the statutory
registry surface from the richer submission layer.

The submission data contain, among other fields:

- implemented measure/investment name;
- implemented measure/investment **type**;
- short technical description;
- timing and verification data.

P104 already showed that the current EKR window catalogue has measure-specific
technical records including new-opening U evidence.

Thus the administrative layer has the correct discovery key and technical
context.

## 4. Historical proof that coded aggregation is possible

The official HUPX/CEEGEX EKR market-monitoring report based on the EKR registry
is important because it demonstrates that measure-level aggregation was not
merely theoretical.

At the historical 2022-10-31 cutoff it reports:

- **541** accepted projects;
- **597** entitlements;
- **39** measure categories in six major groups;
- **620 GJ** in the broad building-structure group.

The report also publishes code-level category examples with project and GJ
aggregates.

Therefore:

`ADMINISTRATIVE CODED MEASURE AGGREGATION = PROVEN CAPABILITY`.

But:

`HISTORICAL CODED AGGREGATION != CURRENT 1103 AGGREGATE`.

None of the historical counts are reused as a 2026 window count or population
weight.

## 5. Current public CEEGEX market data

The current public CEEGEX EKR market surface aggregates HEM volumes into broad
tradable product classes, including residential/catalogue classes.

Those market products are not equivalent to a physical measure code.

Therefore:

`CEEGEX RESIDENTIAL HEM PRODUCT != WINDOW ACTION 1103`.

No new-window U field or full-opening coverage variable is exposed through the
market-product aggregate.

## 6. Automated MEKH data connection

The current EKR user guide documents a MEKH-coordinated automated data-service
connection for high-volume data submission.

This is useful capability evidence, but it does not establish an anonymous
public read/export endpoint.

Therefore P105 does not reinterpret a submission interface as a data-extraction
authority.

## 7. Executable future cohort-admission gate

P105 defines the minimum conditions for admitting a future EKR 1103 cohort
extract:

1. current reference period;
2. exact action code `1103`;
3. complete enumeration for the declared extract scope;
4. explicit source-population scope.

Technical-U coverage and full-window coverage do not have to be complete merely
to admit a **counted 1103 cohort**, but they remain mandatory downstream gates
for:

- compliance distribution;
- whole-dwelling window promotion.

This separates acquisition from physical inference.

## 8. Blocker result

The P104 residual:

`EKR_1103_TECHNICAL_COHORT_AGGREGATE_REQUIRED`

is narrowed to the exact access/acquisition requirement:

`MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED`.

This means the unknown is no longer whether MEKH data can support measure-code
aggregation.

The unknown is whether a **current, scope-declared 1103 extract or equivalent
published aggregate** can be obtained.

After such an extract the next gate would be:

`EKR_1103_COHORT_POPULATION_BINDING_REQUIRED`.

That binding remains necessary because:

`EKR 1103 COHORT != ALL REPLACED WINDOW STOCK`.

## 9. Parallel window residuals

P105 does not remove the independent P104 residuals:

- `NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED`;
- `FULL_DWELLING_WINDOW_COVERAGE_OR_REMAINING_STATE_REQUIRED`.

The independent wall residual also remains:

- `MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED`.

## 10. National numeric effect

No current public 1103 cohort count or technical-U distribution was admitted.

Historical registry counts, global HEM totals and current market-product
aggregates are explicitly forbidden as substitutes.

Therefore the validated P102 bounds remain unchanged:

- calibrated retrofit floor: **82.7861029945%**;
- HP_ONLY lower: **0%**;
- HP_ONLY upper: **17.2138970055%**.

## 11. Readiness

- **B02 remains 55%**;
- **PEAK_LOAD_EFFECT remains 50%**;
- **Q-B02-004 remains OPEN_NARROWED**.

## 12. Canonical boundaries

`PUBLIC SAVING TYPE != PROVEN MEASURE CODE`

`KNOWN HEM ID LOOKUP != COHORT ENUMERATION`

`GLOBAL HEM COUNT != EKR 1103 COUNT`

`CEEGEX MARKET PRODUCT != MEASURE CODE 1103`

`HISTORICAL CODE AGGREGATION != CURRENT 1103 AGGREGATE`

`ADMIN SCHEMA CAPABILITY != PUBLIC DATA AVAILABILITY`

`EKR 1103 COHORT != ALL REPLACED WINDOW STOCK`
