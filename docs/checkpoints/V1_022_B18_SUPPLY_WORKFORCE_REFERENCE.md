# V1-022: B18 source references with explicit capacity gaps

## Scope and status

Approved slices B18-D01/D02/D03 now have a bounded source review. D02 has a
source-native read-only consumer; D01/D03 remain RESEARCHING. No slice is
ACCEPTED and B18 readiness stays0. The three Q records express existing
approved-scope unknowns, not three new mandatory gates.

No national supply or installation limit, import share, programme phase pacing,
financing result or household eligibility decision is introduced.

## Product and statistical boundaries

The exact KSH classification evidence distinguishes historical28251380,
current2025 PRODCOM28211400, and the separate reversible28251252 branch.
CN2025 84186100 has no supplementary unit. Mass cannot become a device count
through an assumed weight. Product scope does not identify household versus
industrial applications or supply lead time.

Two Eurostat snapshots preserve their separate dataset revisions. Direct
Comext observations contain gross statistical value and net mass. The
PRODCOM snapshot preserves confidential production value, inapplicable
production quantity, other missing fields and its own associated trade series.
The import and export differences between datasets are respectively142,546EUR
and16,486EUR (DER diagnostic subtraction, not a correction). Their cause remains
unresolved. No averaging or interchangeable-series claim is authorized.

Native product/metric labels, coordinate indices, Decimal values, flag indices,
flags and missingness are retained. Each read uses a single partner aggregate;
there is no aggregate, conversion-to-count or supply-use balance function.
Border statistical trade values are not retail purchase prices or domestic
value added. Dispatch country is not automatically manufacturing origin.

## Workforce evidence

ConstructSkills4LIFE's source-method facts are useful, but its 53 industry
responses are explicitly nonrepresentative. Its13,600/year entry demand and
4,800/year additional training need are external SCN outputs, dependent on
renovation, task-allocation and retirement assumptions. Its1% starting renovation
rate refers to2010 and its calculation horizon is2020–2030. No programme
adoption of those assumptions occurs here.

The original SQA Table35's2,600+1,200 does not reconcile to4,800. The later
roadmap Table4 gives3,200+1,600 instead. Both versions remain identifiable.
KSH's revised construction-sector headcount is a broad employment control,
not active installation FTE. Repeated publications from this source family
are not independent national evidence.

The reviewed source family supplies no measured work-package installation
time or rework sample. This is an acquisition gap, not proof that no such data
exists. Next useful acquisition is trade/region active work availability and
completed-job labour/quality records with sampling, calibration and competing
workloads. More broad sector headcounts cannot resolve the missing coefficient.

## Evidence and verification

- Supply provenance: `registry/b18_supply_source_reference_manifest.json`
- Workforce provenance: `registry/b18_workforce_source_review_manifest.json`
- Executable reader: `modules/B18/supply_source_reference.py`
- Private-output materializer: `tools/materialize_b18_supply_source_reference.py`
- Synthetic tests: `tests/test_b18_supply_source_reference.py`

Lead verification reproduces all28 selected source measure cells:14 numeric and
14 missing/flagged. A separate Cartesian-coordinate oracle compares exact
Decimal values and separate flag indices, rather than calling the reader's
index calculation. The six trade scopes reconcile WORLD to intra+extra without
adding overlapping totals. All admitted source byte identities are checked.

Focused and shared tests, exact candidate review, and final exact-content hosted
CI must be recorded separately. Local synthetic tests are not full-suite or
national-result validation. Source PDFs/XLSXs/JSON, research renders and complete
normalized panels remain outside the public repository.

## Remaining debt

- Q-B18-001: active trade/region FTE and available labour, mapped to work packages
- Q-B18-002: product-matched supply, stocks/re-exports, lead time and domestic
  content; confidential production and cross-dataset reconciliation
- Q-B18-003: measured rework, quality, elapsed work time and learning

All three remain E3 for a claimed national capacity base. A future defensible
representative sample or calibrated inference may support the claim under the
existing policy; exhaustive household or firm census is not required. An
explicitly conditional scenario must remain labelled SCN.
