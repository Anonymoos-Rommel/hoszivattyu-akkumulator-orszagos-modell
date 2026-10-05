# V1-052 — bind the SAX product reference to qualified source conditions

This checkpoint completes the missing temperature/test-condition handoff for B07-D01
using the exact already-pinned sources. It advances a whole-task acceptance review,
without changing the original criteria or adding a new numerical model. Its integration
base is `eee328cf7a86014f4635caeb0887940159ffffa3` (V1-051).

## What the source establishes

- HTW/aquu 2026 report, declared version 1.0 / March 2026; SAX Home Plus, system A1,
  firmware V23.50, identified on printed/PDF page 65. Original SHA-256 remains
  `97266383faf3a4257a6a521cd1ce04d02eac2628142716e548333fb0c46cbfc7`.
- Printed/PDF page 13 Table 1 gives a manufacturer-information-based 5–35 °C
  permissible operating range for the battery and inverter. The exact undated
  manufacturer datasheet corroborates that specification, with no tested firmware.
  Neither is a measured ambient nor a performance-validation envelope.
- Pages 9/15 describe the common guideline capacity protocol: three cycles each at
  100/50/25% nominal charging/discharging power; the first is conditioning; usable
  discharged-DC capacity averages the six remaining cycles. The illustrated system
  is Fronius D1. Its powers are not SAX measurements; SAX-specific cycle watts and
  raw traces are not supplied. The battery-efficiency summary is retained as reported.
- Pages 21–22 describe a separate additional low-load procedure with at least eight
  measured supports up to 10% nominal discharge power. Fitted vertices are not raw
  observations, and no automatic fit joining is justified.
- Actual laboratory ambient and individual SAX test date remain explicit null/Q.
  Page 17 identifies ambient influence without supplying a numeric SAX temperature.

The report, official data asset and manufacturer datasheet were reacquired byte-for-byte
against their existing hashes. Independent qualification inspected 12 relevant report
page images and the datasheet image, and ran 31 offline source checks. None of the
original PDF/JavaScript bytes, extracted page text or images is in the public patch.

## Reused numerical method and actual consumer

The existing 7.572 kWh discharged-DC control, 95.8183% battery-only DC cycle efficiency,
4.5459 kW reported AC discharge control, 4.07 W aggregate idle base and all 1,194 fitted
vertices are unchanged. The conditional runtime's numerical expressions are unchanged;
its new output metadata carries the qualified conditions. Synthetic mathematical
references return no source conditions. The complete pre-change numerical probe is
identical after removing only the two newly added metadata fields.

At an explicitly chosen 2 kW AC discharge, the existing full-capacity reference delivers
7.455870673658136 kWh AC. Its closed active cycle uses 8.025323091108545 kWh AC input and
has ratio 0.9290430539698372. These conditional outputs are neither universal usable AC
nameplate capacity nor annual efficiency. No temperature-dependent correction is added.

## Original D01 acceptance criteria

1. Exact system/revision: existing source pins and page-65 product/firmware join.
2. AC-side usable energy: existing explicit AC/DC converter/profile/reserve calculation.
3. Charge/discharge power and efficiency: supported fits, source power limit, correct
   clipping and one DC-cycle reference; no invented chemical one-way split.
4. Standby: existing source-qualified E2 aggregate AC proxy over explicit idle exposure;
   no invented physical DC idle allocation.
5. Temperature: newly bound permitted-operation specification, explicit null measured
   ambient, and unchanged E2 transfer debt; no performance guarantee across the range.
6. Test load: newly bound published common protocol and separate low-load method,
   retaining unknown SAX raw-cycle watts and the non-SAX illustration boundary.
7. Relevant conservation/loss-once behavior: existing tested energy/inventory/power
   mechanics, unchanged. Legacy B08 double-count tests are reuse evidence; this does
   not add a reference-dispatch-to-B08 integration or accept D02/D03 requirements.

Q-B07-003 remains E2, model_blocker=false, finalization_blocker=true. No component-level
E1 campaign is added as a universal condition for this bounded D01 handoff. No whole
B07, national fleet, actual site operating permission, physical hourly idle inventory,
long-term cost/lifetime or annual system result is accepted.

## Exact review and staged acceptance record

D01 is REVIEW_REQUIRED until this condition patch has an actual independently reviewed
commit identity. The old V1-051 commit is only the reused numerical baseline and is not
mislabelled as containing the new condition handoff. A later metadata-only acceptance
record can reference the real condition commit after its exact review and hosted checks.
That recording step introduces no extra scientific criterion and must not alter the
accepted artifacts. All 58 slice IDs, original requirements and dependencies, previous
accepted slices and module readiness scores remain unchanged.

The exact local test results and independently reviewed file identities are recorded in
`V1_052_VERIFICATION.json` once review is complete. Publication remains separately scoped.
