# V1-040: annual same-service gas and electricity reference

The B11 consumer now pairs the complete V1-039 heat-pump device case with the
same TABULA building and heating service's native annual gas account. It uses
the source seasonal expenditure factor, rather than substituting a product
efficiency or converting gas volume with an unsupported calorific value.

For the 56 m² ambitious SFH01 reference, useful space heat is 5,748.154 kWh/year
and generator heat is 6,050.554 kWh/year. Original system cell BO3392 supplies a
GCV gas-input/generator-output factor of 1.05. The source space-heating fuel in
CI3392 therefore gives 6,353.082 kWh_GCV/year. The separate heating auxiliary
allocation in BW3392 is 156.8 kWh/year. These are historical source-method
outputs, not measured 2025 household consumption.

## Source labels and accounting boundary

The workbook's DQ3392 field is labelled as heating gas, but its formula adds
space-heating CI3392 and DHW AT3392. Using it would wrongly displace 542.976
kWh/year of DHW gas. DU3392 similarly includes the separate 72.8 kWh/year DHW
auxiliary allocation. This consumer uses the actual space-heating cells;
neither DHW quantity is displaced or silently zeroed.

The 1.05 factor is seasonal generator expenditure on a gross calorific basis.
Its reciprocal is generator-output/fuel efficiency, not useful-room-heat or
whole-system efficiency. It does not establish an hourly boiler curve. The
existing LHV/reference-volume API remains unchanged and is not used to relabel
this source-native energy account.

Common Method Table 14 defines heating auxiliary electricity across available
generation, storage, distribution and emission auxiliaries. The Hungarian
source supplies one aggregate and does not identify its component composition.
It is neither proven pump-only consumption nor measured removable hardware
consumption. The source describes a combi boiler; retaining it for DHW can
retain or reallocate control/standing consumption. The separate DHW allocation
does not establish that every retained control is covered.

## Explicit conditional comparison

The caller must explicitly select
`FULL_SOURCE_ALLOCATED_SPACE_HEATING_REPLACEMENT`. This is an SCN condition for
the bounded reference, not a boiler-retirement, rollout or national policy.
Arithmetic is DER, with E2 applicability to the stated source and service.

The reference gas account decreases by 6,353.082 kWh_GCV/year. It is not labelled
measured whole-boiler fuel savings. The published rating-derived device input
is 2,472.634 kWh/year. Let A be installed-case electricity for the declared
heating service minus that rating-derived reference. This is a signed
reconciliation, including electricity consequences of matching installed heat
delivery/duty, replacement of embedded pump conventions, and genuinely
additional/excluded or retained/reallocated combi controls. Then:

- Electricity after minus before is `2,315.834 + A` kWh/year
- Purchased final energy before minus after is `4,037.248 - A` kWh/year, with
  GCV gas and electricity explicitly retained as different carriers

The second expression is not primary energy, money or a thermodynamic
efficiency. Both complete totals remain unknown. A may have either sign; its
known intercept is not a lower bound. A is not set to zero, bounded by the old
156.8 kWh allocation or cancelled by an unsupported unchanged-pump assumption.
One compatible signed aggregate can close this boundary; separate measurements
of every component are not required by the E2 route.

The exact EN14511:2013 convention adjusts both effective electrical input and
heating capacity for pump effects. Mitsubishi's 10 W allowance is a nominal
W35 table fact, not a constant established across the W55 map. EN14511-1:2013
already includes rated-unit control/safety input; no blanket controller
addition or new submeter requirement is justified for those included devices.
Actual installed heat delivery/duty and physical SPF require coherent
reconciliation, while the existing source-rating results remain valid. The
later V1-041 boundary clarification records the exact supporting sources;
earlier numerical results and their historical verification are preserved.

The existing 8,760-hour device/thermal profile is preserved. Gas and source
auxiliary values remain annual-only, so the consumer supplies no hourly gas,
auxiliary or net grid-increment profile. Gas volume, import value, household
savings, physical SPF and national results remain unavailable here.

## Verification and remaining work

Independent source qualification checked the original workbook cells and
formulas, the Common Method's GCV and auxiliary definitions, and the genuine
published annual-device replay. Implementation review binds the actual final
code and metadata. Focused tests cover source end-use traps, conditional
admission, useful/generator/fuel consistency, missing quantities, shared-control
residuals and producer identity. The configured aggregate and exact-head hosted
checks are recorded separately in the verification receipts.

Original source files and complete panels remain external. B11-D01 advances to
integration; whole-slice acceptance, national appliance weights and module
readiness are unchanged. Field or calibrated evidence is still needed for the
intended installed/stock application, while the bounded reference can be used
now under its explicit E2 limitations.
