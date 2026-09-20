# B02-P58 — electrical transition authority repair

**State:** `CURRENT ELECTRICAL READINESS RETIRED AS NATIONAL PRECONDITION / DSO-BOUND TRANSITION GATE ADDED`

**Base:** `43e62c43854403f6abf4d79fd6c7433852ae337e`

**Implementation date:** 2026-09-20

## 1. Purpose

The old B02 wording treated current connection/meter readiness as though a
dwelling had to be electrically ready **before** the programme could consider it
technically eligible.

Hungarian DSO procedures show a different reality: existing customers can submit
additional-capacity requests, meter/service alterations and heat-pump/H-tariff
requests.

Therefore:

`CURRENT ELECTRICAL READY != ONLY ELIGIBLE STATE`

`CURRENT ELECTRICAL NOT READY != AUTOMATIC INELIGIBILITY`

`UPGRADE REQUIRED != UPGRADE IMPOSSIBLE`

`UNKNOWN DSO FEASIBILITY != PASS`

`PROVEN DSO REFUSAL / UNSERVABLE DEMAND = BLOCKED`

## 2. Hungarian evidence

### MVM Hálózat — additional capacity

The MVM public process explicitly covers a **new or existing connection point**
where additional electrical demand is requested. It states that existing public
network supply may be used while the service line and meter location may need to
be built or upgraded.

This is direct evidence that insufficient **current** service capacity is not
semantically identical to permanent technical ineligibility.

### MVM H tariff declaration

The current MVM H-tariff declaration requires heat-pump manufacturer/model,
nominal electrical power, thermal output, SCOP, operating type and the **total
simultaneous electrical power** of the separately metered heat-pump system.

This proves that the connection decision is based on explicit equipment demand,
not a generic household-ready flag.

### E.ON / ELMŰ DSO connection form

The current DSO form explicitly captures requested amperage by phase, H/Geo
heat-pump tariff and whether the service connection is existing or changed.

### MVM H-tariff meter-place guidance

MVM guidance states that an existing meter location is assessed to determine
whether the new measurement can be accommodated there; if not, the site must be
modified. Again, this is a transition/upgrade decision.

## 3. New electrical transition gate

The canonical record/project question is:

> Can the selected heat-pump system's electrical demand be served through an
> explicit existing, upgraded or new-dedicated connection path admitted by the DSO?

Permitted paths:

- `USE_EXISTING_CONNECTION`
- `UPGRADE_CONNECTION`
- `NEW_DEDICATED_CONNECTION_OR_METER`

Required evidence includes:

- current phase/count and available current;
- heat-pump nominal electrical power;
- auxiliary electrical power;
- starting-current or inverter basis;
- required phase/count and current;
- meter/service upgrade scope when required;
- dedicated heat-pump circuit basis;
- DSO status and evidence;
- reproducible binding.

## 4. DSO semantics

`DSO_APPROVED` -> may qualify if all other inputs are complete.

`DSO_NOT_REQUIRED` -> may qualify only with evidence that no separate approval is required.

`DSO_PENDING` -> `Q`.

`DSO_REFUSED` -> explicit `BLOCKED`.

Thus P58 does not weaken network feasibility. It relocates it to the correct
authority and decision grain.

## 5. H tariff boundary

H-tariff eligibility is **not** the same as technical electrical connectability.

`H_TARIFF_AVAILABLE != TECHNICALLY_CONNECTABLE`

`H_TARIFF_UNAVAILABLE != HEAT_PUMP_IMPOSSIBLE`

Tariff/legal/economic treatment remains under the existing B04/B07 contract.

## 6. Programme effect

P58 retires `GAP-B02-S2-ELECTRICAL` as a **current-stock national precondition**.

Electrical transition work remains mandatory at record/project grain and may
produce PASS/Q/BLOCKED depending on actual DSO evidence.

No national eligible-dwelling count is created.
