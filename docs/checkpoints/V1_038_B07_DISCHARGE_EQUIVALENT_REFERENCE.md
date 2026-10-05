# V1-038: B07 conditional discharged-energy reference and E2 validation debt

A separate B07 reference now uses measured discharged-DC capacity and battery
cycle efficiency without inventing observed chemical one-way efficiencies. The
owner approved this bounded method and feature-branch implementation, then
clarified that E2 continuation must not require every component-level E1
measurement. The existing stored-SOC engine and its callers remain unchanged.

## What can now be calculated

The source-qualified SAX2026:A1/V23.50 factory supplies one constant7.572kWh
capacity and0.958183battery-cycle efficiency reference. That use is explicitly
E2/PROVISIONAL_BASE; the coordinate/balances are DER and the supplied command
profile is SCN. Synthetic references remain SCN/E3. The reference solves the
actual supported converter point before admitting power, retains explicit
initial/terminal inventory and reserve, and separately selects the discharge
fit. It neither averages source fits nor invents sub-support duty cycling.

For the established no-idle2kW_DC-charge/2kW_AC-discharge example, the ledger
remains8.025323091kWh AC input and7.455870674kWh AC output, with equal endpoint
inventory and0.929043054 conditional active ratio. This is a source-conditioned
example, not a measured annual system ratio. The previous private candidate's
numerical cycle-eligibility defects are closed: tiny initial-stock draw and
under-resolved subnormal arithmetic cannot acquire a false cycle ratio. Valid
tiny closed cycles remain eligible. No physical minimum duration was introduced.

A separate `provisional_standby_ac_energy` consumer applies one4.07W E2 aggregate
AC-side debit to an explicitly supplied idle exposure. The exact-system HTW
empty-state measurement is corroborated by the manufacturer's approximately4W
Home/Home Plus system specification. This is sufficient support for the declared
provisional aggregate route; exact BMS subcomponents are not a new model stop.
The manufacturer snapshot does not replace the tested capacity, power or
firmware. Its original PDF remains external, with hash and provenance retained.

The proxy is not an all-state measurement, an upper bound, or proof that
cell-powered idle loss is zero. The consumer does not assign that aggregate to
physical DC inventory. The state-path runner therefore retains Q across idle;
this is a limitation of that physical-state consumer, not a project-wide bar on
E2 aggregate finite/annual energy accounting. Physical peak dispatch requires an
explicit allocation contract. Active battery-cycle losses already include their
tested BMS contribution and receive no second active BMS penalty.

## Validation debt remains visible

The existing Q-B07-003 stays E2/VALIDATION_BLOCKER/model_blocker=no/MODEL_CONTINUE.
Its detailed record, `registry/b07_reference_validation_debt.json`, identifies
three later upgrades: constant cycle/capacity applicability, complete idle
aggregate boundary/state transfer, and physical AC/DC allocation if that claim
is activated. Boundary-complete aggregate evidence or qualified calibration may
close the debt; separate laboratory measurements for every component are not
mandatory. Final E1 evidence is not a prerequisite merely to use the E2 base.

Materiality is claim-specific, not an additional universal E2 admission rule.
The selected proxy produces5.0875–14.245kWh for the source's generic1,250–3,500
empty-state hours, and35.6532kWh for an explicitly supplied8,760-hour exposure.
No Hungarian exposure, missing-loss bound, negligible-error threshold or annual
profile is selected. SAX's93.1713% SPI is a cost-saving index at a stated
profile/tariff; it is not used as a round-trip energy efficiency.

## Verification and limits

The independently accepted private revision3 is the implementation predecessor.
All original transition, source-fit, clipping and numerical-cycle behaviors are
preserved; integration adds evidence labels, source-identity checking and the
separate aggregate idle debit. Focused tests include both independent numerical
failure witnesses, their positive neighbors, source/native boundaries, exposure
scaling and prevention of aggregate-to-physical-state promotion. Fresh exact
implementation review and configured full-suite evidence are bound separately.

No raw source or private panel is republished. This checkpoint does not change
module readiness, accept a whole research slice, select a national product or
operating policy, authorize tariff/export/VPP behavior, or merge main. It does
not claim a complete annual system, national savings, procurement suitability
or household payback result. E2 model continuation and later E1 closure remain
distinct throughout.
