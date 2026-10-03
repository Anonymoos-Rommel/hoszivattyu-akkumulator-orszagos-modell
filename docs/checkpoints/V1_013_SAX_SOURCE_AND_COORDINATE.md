# V1 checkpoint013: SAX source reference and explicit energy coordinate

The pinned [HTW/aquu2026 report](https://solar.htw-berlin.de/wp-content/uploads/HTW-aquu-Stromspeicher-Inspektion-2026.pdf) and its [official inspector data asset](https://solar.htw-berlin.de/stromspeicher-inspektor-2026/js/Daten.js) identify2026:A1 as SAX Power Home Plus, firmwareV23.50. It is not the2023:A1 VARTA product. Exact source hashes, locators, numerical extraction and applicability remain in the manifest. The source JavaScript is read as narrowly whitelisted numeric literals and never executed. Original PDF, figures and JavaScript are not republished.

## Why the source detail matters

Three explicitly selected converter fits preserve their own support: charge-to-DC and discharge-to-AC standard curves from AppendixA3 page64, and a dedicated low-load discharge fit from Figure20 page22. Their1194 vector vertices are fitted-curve coordinates, not1194 independent laboratory observations. Digitization precision does not imply physical measurement precision. There is no automatic curve join, averaging or extrapolation.

At100W AC output the dedicated curve gives approximately84.43% conversion efficiency, compared with the separately reported97.697% standard discharge-path mean. Using that mean at100W would materially understate DC demand. The mean is reproduced only with the source's ten5%-95% output-power points; it is not an annual efficiency. At200W the two published fits differ by about0.557percentage points, retained as fit/method disagreement within one source family.

The7.572kWh usable capacity is discharged-DC energy. The95.8183% battery efficiency is a battery-only DC cycle quantity. Neither supplies observed chemical one-way efficiencies. Charging curves use DC OUTPUT power; discharge curves use AC OUTPUT power. The point consumer returns both path boundaries and computes input=output/efficiency.

Figure24 page26 resolves SAX's reported EMPTY-state4.07W total to AC-system plus AC-sensor draw: cumulative total/AC bars have identical vector heights, and the total digitizes to4.0695W. The sensor portion is about0.86W. This does not establish all-state idle consumption or zero cell/BMS drain; the report expressly excludes unmeasurable cell-powered BMS consumption from that test framework.

## Proposed method before any normative replacement

The [discharge-equivalent reference contract](../methodology/b07_discharge_equivalent_reference_contract.md) is published as PROPOSED and branch-local reviewed, before any canonical adoption or normative replacement. Its state x is remaining usable DC discharge-equivalent inventory, with x_next=x+eta_cycle*DC_charge-DC_discharge. The finite-horizon inventory term remains explicit. This is an accounting coordinate under a declared constant-cycle-efficiency approximation, not an observed chemical loss split or BMS SOC.

The existing BatterySpec, scalar one-way engine, tariffs, export permissions and readiness gates are unchanged. The existing AC household balance function can be reused; scalar-efficiency state clipping cannot. A later reference runtime must solve actual supported converter powers, preserve clipping/unused energy, and use explicit initial/terminal states. No duty-cycle or idle assumption is inserted silently. This checkpoint contains only source-point consumers and the proposed contract, not the new state runtime.

No whole B07 slice, annual/national efficiency, aging, supply-chain, H-tariff or VPP claim is closed. Q-B07-003 remains validation debt under existing E2 continuation authority. The purpose is to calculate a defensible bounded reference without demanding physically unidentifiable chemical one-way measurements.

## Verification

Eight focused tests cover product/year/firmware identity, all1194 native points, power conservation, source hash protection, support rejection, separate fit controls and charging output-axis semantics. The pinned-source extractor reproduces both curated artifacts byte-for-byte. The coordinate algebra and scope received independent mathematical review and a separate narrow methodological review; those are not full independent product or annual-system validation. Full-suite results and artifact hashes are recorded in the verification receipt.
