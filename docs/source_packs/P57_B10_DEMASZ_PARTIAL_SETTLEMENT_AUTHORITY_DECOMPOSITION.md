# B10-P57 — MVM Démász partial-settlement authority decomposition

Status date: 2026-09-05

Canonical base: `82354655e5b157958e132fc329dea6cef7e5d883`

## Purpose

P57 is a fail-closed residual-authority slice over the exact 20 current MVM Démász settlements that P45 already established as only **partly** inside the operator service area.

P57 does not resolve those partial settlements. It converts the previously documented 20-name obligation into a machine-auditable residual surface and preserves the evidence boundary needed for any later exact usage-location work.

## Frozen source population

P45 established the exact current MVM Démász source accounting:

- 256 settlements wholly inside the service area;
- 20 settlements partly inside the service area;
- 276 source settlement labels across those two distinct grains.

P57 freezes exactly the same 20 partial-settlement source labels:

- `Baja`
- `Csongrád`
- `Csabacsűd`
- `Dabas`
- `Dévaványa`
- `Érsekcsanád`
- `Gyomaendrőd`
- `Kunszentmárton`
- `Mohács`
- `Péteri`
- `Solt`
- `Szeghalom`
- `Szentes`
- `Tápiószőlős`
- `Tass`
- `Tiszakécske`
- `Tiszasas`
- `Tiszaug`
- `Újhartyán`
- `Zsadány`

All 20 are stored as:

- `residual_class = PARTIAL_SETTLEMENT_ADMINISTRATIVE_SCOPE`
- `admission_status = UNRESOLVED_USAGE_LOCATION_AUTHORITY_REQUIRED`
- `authority_basis = P45_CURRENT_MVM_DEMASZ_PARTIAL_SETTLEMENT_GRAIN`

Every source form occurs exactly once in the P57 residual audit.

## Exact audit digest

The canonical P57 audit projection uses these ordered fields:

`source_token | source_occurrence_count | residual_class | admission_status | authority_basis | cross_operator_context`

sorted by `source_token` and newline terminated.

SHA-256:

`6dad102a2d23f18daf88620761c786072111990b2882261bd48539a05e767c7f`

## Tass cross-operator context

P55 independently preserved the current ELMŰ M1 source token:

`Tass üdülőterület`

and classified it as:

`EXPLICIT_SUBSETTLEMENT_AREA`

P57 therefore records one bounded cross-operator context marker on the MVM Démász `Tass` partial-settlement row:

`P55_ELMU_EXPLICIT_SUBSETTLEMENT_AREA_PRESENT`

This is useful evidence that the published territorial surfaces around Tass are finer than a single whole-settlement assignment. It is **not** authority to infer the exact complementary MVM Démász area, an address list, a polygon, a feeder boundary, or whole-settlement membership for either operator.

The other 19 P57 rows carry no cross-operator context claim in this slice.

## Fail-closed boundaries

`PARTIAL SETTLEMENT LABEL != WHOLE-SETTLEMENT MEMBERSHIP`

`PARTIAL SETTLEMENT LABEL != EXACT USAGE-LOCATION MEMBERSHIP`

`CROSS-OPERATOR SUBSETTLEMENT CONTEXT != COMPLETE TERRITORIAL BOUNDARY`

`NAMED SUBSETTLEMENT != AUTHORITY TO INFER THE COMPLEMENT AREA`

`SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

No parent inference, complement inference, suffix stripping, geometric interpolation, nearest-area assignment, address inference, or node inference is authorized.

## Membership consequence

P57 adds **zero** service-area membership rows.

MVM Démász remains:

`40 historical + 216 P45 = 256 materialized current whole-settlement memberships`

P57 does not rewrite the historical tranche or P45 completion surface.

The operator extraction state remains:

`PARTIAL_TRANCHE_MATERIALIZED`

because the 20 exact usage-location obligations remain unresolved.

## Canonical and closure state

`registry/dso_service_area_membership_crosswalk.csv` remains header-only.

The blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

P57 does not prove programme entity-to-node mapping, complete node inventory, headroom sufficiency, limiting-node status, reinforcement requirement, reinforcement cost, programme-incremental CAPEX, or timed programme CAPEX.

B10 remains `IN_PROGRESS`; readiness remains **15%**.

## Files

- `registry/dso_service_area_membership_demasz_p57_partial_settlement_authority_audit.csv`
- `registry/dso_service_area_membership_demasz_p57_authority_manifest.csv`
- `tests/test_b10_p57_demasz_partial_settlement_authority_decomposition.py`
