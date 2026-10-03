# V1-023: gas reference-state contract repair

## Result

B11 P3–P5 now distinguish gas volume state from calorific energy basis. A raw
GCV/LHV ratio cannot silently mix different volume temperatures, pressures,
moisture conventions or gas-quality contexts. Efficiency-to-LHV compatibility
is explicit, and a derived volume retains its reference state.

Arithmetic returns DER or propagates SCN; observed inputs do not turn a derived
efficiency or volume into OBS. P5 preserves individual input statuses and
lineage. P1/P6, household class weights, national admission and readiness30
remain unchanged. No actual FGSZ point values or coefficients are admitted.

## Source and execution boundaries

The source qualification preserves four exact external document identities.
It distinguishes document validity from the historical observation period,
including the new MER revision's stale contents-page year. Numeric model use
and raw redistribution remain unresolved; a synthetic dimensional fix does
not resolve those rights.

B11-D02 is INTEGRATING at contract level only. Seasonal class-efficiency,
gas-quality distribution/weights, multi-fuel and end-use boundaries, rebound,
sales calibration and uncertainty remain separate evidence requirements.
Representative or calibrated national inference remains permitted under P6;
exact participant-to-point mapping is not imposed on national estimates.

## Validation

- 15 previously undiscovered P3–P5 functions converted to discoverable test cases
- 17 new synthetic adverse/positive cases
- 50 discovered B11 checks passed locally
- P1/P6 source modules unchanged
- Full aggregate CI and independent exact-byte review recorded separately

The configured CI test count describes executed tests. A separate read-only
inventory identified other legacy top-level functions elsewhere; P7 does not
claim to repair repository-wide test discovery.

See `docs/source_packs/P7_B11_REFERENCE_STATE_CONTRACT.md` for the input contract,
`registry/b11_reference_state_source_manifest.json` for source metadata, and
`tests/test_b11_reference_state_contract.py` for the synthetic witness closure.
