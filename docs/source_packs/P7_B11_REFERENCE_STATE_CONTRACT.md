# B11-P7: explicit gas reference states

V1-023, 2026-10-02. This extends P3–P5's unit contract using synthetic checks.
It does not admit new gas-quality values, source-use permission, appliance
efficiencies or national displacement results. P1 and P6 are unchanged.

## Problem and corrected behavior

The previous per-volume evidence type distinguished GCV from LHV but could not
express the temperature, absolute pressure or moisture convention of its cubic
metre. The P4 ratio could therefore accept two incompatible denominators. P3's
output likewise lacked a named reference state. A free-text source note did not
make either prerequisite executable.

`GasReferenceState` now carries volume-reference temperature (degrees Celsius),
absolute reference pressure (Pa), and an explicit dry or water-saturated basis.
`CalorificBasis` separately carries calorific-reference temperature and a
gas-quality context ID. That context may identify a justified population
distribution or a synthetic scenario; it need not identify every participant.
Its provenance must establish the composition, scope and period it represents.

Gas per-volume inputs require both objects. The GCV/LHV ratio requires the same
volume state and gas-quality context. It performs no implicit ideal-gas,
pressure, moisture or calorimetric conversion. Different calorific-reference
temperatures may be declared on the two energy bases: the efficiency must
match the GCV side, and the converted result retains the LHV side's basis.

An efficiency is dimensionless. It requires its calorific basis/context but
does not require a volume temperature or pressure. The P3 bridge checks its
calorific basis against the supplied LHV and reports the resulting cubic
metres with that LHV's explicit volume state. A producer must supply a valid
per-volume value at the declared state; relabelling does not convert a value.

Missing metadata, incompatible states/contexts, unknown moisture, booleans,
nonfinite values and nonpositive pressure fail closed. No reference-state
defaults or gas conversion factors are embedded.

## Evidence status and P5 preservation

GCV-to-LHV efficiency conversion and useful-heat-to-volume arithmetic produce
DER when their accepted inputs are OBS/DER. Any SCN input propagates SCN.
An unchanged direct LHV efficiency can retain its input status. Q never
authorizes numeric arithmetic.

P5 retains each value's own state, calorific basis, status and source lineage
after its existing point/period/mapping checks. It does not flatten the pair's
metadata. The source-copy and national-inference boundaries remain separate;
P7 does not turn a metadata match into source permission or population evidence.

## Current source qualification

The FGSZ revision issued 2026-09-30 applies to gas year 2026/2027. Its PDF body
and corresponding workbook identify calendar-2025 statistics, while the PDF
contents page still labels those tables 2024. Source identity and exact header
locations are preserved in `registry/b11_reference_state_source_manifest.json`.
The validity period must not replace the observation period.

The published copyright notice addresses use of FGSZ regulations and requires
express written permission. No such permission is established here. Original
documents and point tables stay external, and numeric source-specific model
use remains unresolved. The synthetic contract does not depend on importing
actual FGSZ point values or conversion coefficients.

## Verification and compatibility

The 15 existing P3–P5 test functions are now discoverable `unittest.TestCase`
methods, retaining their prior assertions with explicit synthetic metadata.
Seventeen new adversarial cases cover the observed dimensional gap, truth
propagation, metadata preservation and overflow. All 50 discovered B11 tests
pass locally; exact-candidate independent review and hosted aggregate CI are
separate requirements.

Older calls that omit required gas/calorific metadata now fail closed. Supply
the source-supported state and context explicitly. Do not fill them from a
generic national constant or infer authorization from a successful test.
