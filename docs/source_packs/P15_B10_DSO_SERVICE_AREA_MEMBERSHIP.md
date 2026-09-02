# B10-P15 — DSO service-area membership acquisition and normalization gate

## Purpose

P14 proved the current six Hungarian electricity DSO operator inventory and fixed
`DSO_SERVICE_AREA` as the canonical B10 network-regional grain. P15 adds the
next fail-closed boundary required before administrative programme geography can
be joined to that network grain.

Core rule:

`SETTLEMENT NAME != KSH SETTLEMENT ID != WHOLE-SETTLEMENT DSO MEMBERSHIP != PARTIAL-SETTLEMENT USAGE-LOCATION MEMBERSHIP != EXACT DSO NODE`

P15 does **not** publish a national crosswalk yet. It defines the authority and
normalization conditions under which such a crosswalk may later be populated.

## Fresh official-source audit — 2026-09-02

### National locator and operator boundary

MVM Next's current technical-administration page links the six territorial
network operators and provides a separate current page for identifying the
network provider at a consumption location:

- https://www.mvmenergiakereskedo.hu/oldalak/70562
- https://www.mvmenergiakereskedo.hu/oldalak/70260

These pages support the operator-boundary context but do not provide a reusable
normalized KSH-settlement crosswalk.

### MVM Démász

Current official service-area page:

- https://mvmhalozat.hu/aram/oldalak/6454

The page states that the settlement list is contained in the operating licence
and business-rule annex and also publishes settlements by county. Critically, it
separately lists settlements where **only part of the administrative settlement**
belongs to the MVM Démász service area.

Therefore a rule such as `settlement name -> exactly one DSO` is not universally
valid. A partial-settlement row requires more precise usage-location authority.

### OPUS TITÁSZ

Current official operating-area page states that the service-area settlement list
is contained in business-rule annex M1:

- https://www.opustitasz.hu/tarsasagunk/tevekenysegunk/mukodesi-terulet

Current business-rule landing, effective from 2026-06-03:

- https://www.opustitasz.hu/tarsasagunk/szabalyzatok/uzletszabalyzat

The list has not yet been normalized to KSH settlement identifiers in this
repository.

### MVM Émász

Current official business-rule landing exposes the effective 2026 package:

- https://mvmemaszhalozat.hu/tarsasagunk/jogszabalyok-szabalyzatok/uzletszabalyzat

The exact M1 attachment and its normalized KSH settlement extraction remain an
acquisition task.

### E.ON / ELMŰ

Official E.ON-hosted business-rule attachment families expose M1 territorial
jurisdiction for E.ON Dél-dunántúli, E.ON Észak-dunántúli and ELMŰ Hálózati.
The repository records the currently discovered official 2025 attachment URLs as
**candidate acquisition sources only**. P15 does not assert that those attachment
versions are the effective 2026 versions.

Before any rows can become canonical, the exact current document version must be
pinned and the M1 list must be extracted and normalized reproducibly.

## Executable membership contract

`modules/B10/service_area_membership_contract.py` separates four propositions.

### 1. Administrative identity

A source settlement name alone is not a canonical KSH administrative identifier.
The exact settlement name must be bound to a `KSH_SETTLEMENT_CODE` by separate
administrative authority.

Missing normalization yields:

- `Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION`

### 2. Whole-settlement DSO membership

Automatic settlement-level DSO membership is allowed only when referenced
authority explicitly binds:

- exact settlement name;
- exact network operator;
- exact canonical `*:SERVICE_AREA` id;
- `WHOLE_SETTLEMENT` scope.

Together with proven KSH normalization this yields:

- `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`

### 3. Partial-settlement boundary

A source indicating that only part of an administrative settlement belongs to a
DSO cannot authorize the whole KSH settlement row. Without location-specific
authority it yields:

- `Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED`

### 4. Usage-location membership

A partial settlement may become usable for a concrete household/programme entity
only when higher-authority evidence binds the exact usage location to the exact
operator and service area. This may yield:

- `USAGE_LOCATION_MEMBERSHIP_PROVEN`

This still does **not** prove an exact supplying substation or feeder.

## Crosswalk registry state

`registry/dso_service_area_membership_crosswalk.csv` is intentionally header-only.
No national normalized rows are published by P15.

`registry/dso_service_area_membership_sources.csv` is a source-acquisition
manifest. It records:

- current sources where currentness is actually established;
- candidate official E.ON attachment families where 2026 current-version pinning
  is still required;
- extraction status separately from source discovery.

`NOT_EXTRACTED` is not zero and is not membership evidence.

## Q-B01-002 effect

P14/P15 now make the architecture explicit:

- B10 network planning grain: `DSO_SERVICE_AREA`;
- KSH county/settlement geography: independent administrative/reporting axis;
- a reproducible administrative-to-DSO crosswalk is an explicit bridge, not an
  identity assumption.

`Q-B01-002` remains OPEN because the evidence requested by the question includes
that reproducible bridge and it is not yet populated nationally.

## Non-authorities

P15 cannot mint:

- exact DSO substation/node mapping;
- feeder topology;
- headroom or connection permission;
- hosting capacity;
- reinforcement requirement;
- programme attribution;
- programme CAPEX;
- managed-peak survivability;
- national programme connection demand.

## Readiness effect

B10 remains `IN_PROGRESS` at readiness **15**. P15 narrows the spatial blocker but
does not populate a primary B10 output.
