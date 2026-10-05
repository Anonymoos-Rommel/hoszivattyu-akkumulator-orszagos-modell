# B18: construction and supplier capacity

V1-022 introduces a **research-reference reader**, not an installation-capacity
model. National capacity, import penetration, domestic content, delivery lead
times and the feasible rollout remain unknown. B01/B06/B10/B15 dependencies
are unchanged; readiness remains zero.

## Source-native supply references

`supply_source_reference.py` reads two exact external JSON-stat snapshots:

- `SRC-B18-COMEXT-HU-CN84186100-2025`: annual Hungarian gross trade, CN2025
  84186100, dated dataset revision 2026-09-15
- `SRC-B18-PRODCOM-HU-28211400-2025`: annual Hungarian PRODCOM2025/CPA2.2
  28211400, dated dataset revision 2026-09-29

The caller must select the source, dataset, revision, classification, product,
year, reporter and native metrics explicitly. Trade requires exactly one native
partner aggregate and flow. The reader never sums WORLD with its components.
Production has no partner/flow dimension. Different datasets cannot substitute
for each other just because their product classifications correspond.

Records retain exact Decimal values, sparse-cell indices, source metric and
product labels, separate flag-cell indices and native flags. Numeric publication
controls are OBS; absent values remain Q. This does not imply a census of
individual installations. No rounding, interpolation or zero filling is provided.

### Classification and missingness

KSH's explicit correspondence tables map historical PRODCOM28251380 to current
28211400, and the latter to CN84186100. The separate reversible product28251252
maps to CN84158100. Label similarity cannot override this crosswalk. Mapping
documents and exact row locators are pinned in the public manifest.

CN84186100 has no supplementary unit in 2025. Its mass unit is100kg, not pieces,
thermal kW or household installations. The selected PRODCOM production value is
confidential, while its production quantity is not applicable. A missing numeric
cell, a confidential cell, an inapplicable quantity and an observed zero are
distinct. The reader rejects unreviewed flags and never borrows historical P/ST
or the reversible category's counts.

Direct Comext and PRODCOM-associated 2025 trade values differ. Both retain their
own source identity and revision; reconciliation remains Q-B18-002. Neither
can supply an import-share denominator or domestic-availability balance.

### Reproduction and storage

Run `python tools/materialize_b18_supply_source_reference.py --help` for the
required selectors. `NONE` is explicit for the two absent production axes.
Outputs must be external to Git or inside untracked, ignored `data/interim`.
The command does not download, overwrite existing outputs or publish numeric
panels. Exact source bytes must be supplied externally.

## Workforce and quality evidence

The separate workforce manifest qualifies historical studies and KSH broad
sector controls; it is not a worker-capacity consumer. ConstructSkills4LIFE's
53-response industry survey is nonrepresentative. Its annual training-demand
figures are assumption-driven SCN. The SQA's inconsistent2,600+1,200 versus
4,800 total is preserved; the later roadmap separately gives3,200+1,600.
Versions and derivative project documents are not independent samples.

Current KSH construction employment and older SQA headcounts have different
publication vintages. Neither gives active installer FTE, available regional
hours, work-package labour time, competing workloads or measured rework.
Q-B18-001/003 require claim-matched observations or defensible calibrated
inference. No arbitrary jobs-per-certificate multiplier is admitted.

## Checks

- `python -m unittest tests.test_b18_supply_source_reference`
- `python -m unittest tests.test_registry_contract tests.test_v1_research_plan`
- `python tools/validate_registry.py`

Synthetic unit tests validate the reader, not national feasibility. Original
data and documents remain EXTERNAL_ONLY; public manifests retain provenance.
