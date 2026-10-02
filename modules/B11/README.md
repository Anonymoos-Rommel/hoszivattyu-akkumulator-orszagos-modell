# B11: gas displacement and import value

P1/P2 provide physical and county gas baselines. P3–P5 define the useful-heat,
fuel-energy and reference-volume bridge. P6 keeps representative national
inference separate from exact participant/point claims. National gas
displacement remains Q; module readiness is30.

## Current P7 reference-state contract

For gas per-volume evidence, supply both:

- `GasReferenceState`: volume temperature in°C, absolute pressure inPa and
  `MoistureBasis.DRY` or `WATER_SATURATED`
- `CalorificBasis`: calorific-reference temperature and the applicable
  gas-quality composition/population/period context ID

Dimensionless fuel efficiency carries only `CalorificBasis`. GCV conversion
requires a compatible same-volume gas-quality pair and returns the LHV basis.
P3 checks that basis and attaches the gas volume's reference state to its
result. Missing metadata is not defaulted. Changing metadata is not a physical
conversion, and a context match does not establish empirical applicability.

The evidence producer is responsible for the source-supported meaning of the
context ID. It can represent defensible weighted population evidence without
requiring a point record for every household. Source-specific permission,
seasonal efficiency calibration and national weights remain independent.

See [P7](../../docs/source_packs/P7_B11_REFERENCE_STATE_CONTRACT.md). The
FGSZ material remains external and numerically unadmitted. No source-specific
conversion coefficient or default efficiency is embedded.

Run `python -m unittest discover -s tests -p 'test_b11*.py'` for the discovered
B11 tests and `python tools/validate_registry.py` for registry contracts.

## Annual source-allocated GCV reference

`annual_same_service_reference.calculate_reference(weather_path=...,
condition=FULL_REFERENCE_REPLACEMENT)` connects the published B05 annual device
case to TABULA's same-service seasonal gas account. The caller supplies the
explicit reference substitution condition; no national policy is selected.
It preserves the source's GCV basis and separates space heating from DHW.

The resulting affine electricity account retains one unknown signed
installed-minus-rating reconciliation. It includes any matching heat-delivery/
duty adjustment, replacement of embedded pump conventions and genuinely
additional/excluded or retained controls. Rated-unit control/safety input is
already included. The known term is neither complete household incremental
electricity nor its lower bound. Gas volume, hourly gas/auxiliary profiles, whole-system
SPF and national outputs remain unavailable. See
[V1-040](../../docs/checkpoints/V1_040_ANNUAL_SAME_SERVICE_GAS_REFERENCE.md).

`annual_retrofit_reference.calculate_family_reference(weather_path=...)` adds
the same source building's original and standard packages. The original
WM50 case retains its capacity shortfall and incomplete annual total. Use
`compare_original_to_retrofit` with an explicit standard/ambitious after-case
and source-package replacement condition for the conditional original-gas
pathway. Distinct signed rating-to-installed residuals remain unknown. Source
service completion does not establish actual installed heat delivery. See
[V1-041](../../docs/checkpoints/V1_041_ANNUAL_RETROFIT_PACKAGE_REFERENCE.md).

## V1 conditional national accounting screens

[National count and source-accounting bounds](../../docs/checkpoints/V1_047_NATIONAL_ACCOUNTING_BOUNDS.md)
combine native 2022 census group counts and the admitted JRC ledger in a
parametric necessary-condition screen. Above-cap requirements are excluded
within their stated boundaries; other requirements remain INCONCLUSIVE.
The gas ledger includes natural gas and biogas. Nonempty selected groups
retain the whole ledger cap, with no proportional heat assignment. Central
heat allocation, eligibility and national feasibility remain unresolved.
