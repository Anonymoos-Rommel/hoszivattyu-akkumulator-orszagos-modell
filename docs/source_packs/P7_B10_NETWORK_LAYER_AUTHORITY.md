# B10-P7 — Transmission vs distribution authority and project-grain gate

## Purpose

B10-P7 creates the smallest executable boundary required by B10 Issue #10 to
keep **transmission** constraints/projects separate from **distribution**
constraints/projects.

The core rule is:

`VOLTAGE LEVEL != NETWORK LAYER != PROJECT AUTHORITY != PROGRAMME ATTRIBUTION`

A 132 kV value, a company name, a planning-document appearance, or a physical
TSO/DSO connection point cannot by itself classify a project as transmission or
distribution.  Classification requires referenced, claim-specific authority
bound to the exact project and operator.

## Existing source authorities reused

P7 does not introduce a new numerical source dataset.  It reuses the existing
B10 source registry authority families:

- `SRC-B10-MAVIR-GRID-DEVELOPMENT-2026` — official MAVIR system-operator and
  network-planning publication area;
- `SRC-B10-MEKH-NETWORK-DEVELOPMENT-2026` — official MEKH regulatory
  network-development authority portal;
- `SRC-B10-MVM-DEMASZ-RRF-PROJECT-2026` and
  `SRC-B10-MVM-DEMASZ-RRF-COMPLETION-2026` — exact observed MVM Démász DSO
  project identity/scope/completion evidence;
- `SRC-B10-OPUS-TITASZ-RRF-PROJECT-2026` and
  `SRC-B10-OPUS-TITASZ-RRF-COMPLETION-2026` — exact observed OPUS TITÁSZ DSO
  project identity/scope/completion evidence.

Fresh official-source review also confirms the architectural need for the split:
Hungarian network-development planning is coordinated across MAVIR and the
DSOs, while individual assets/projects remain operator- and project-specific.
Therefore a jointly planned interface is not a licence to collapse TSO and DSO
truth into one national network layer.

No raw official document is committed by P7.

## Executable classification

`modules/B10/network_layer_authority_contract.py` exposes four outcomes:

- `TRANSMISSION`
- `DISTRIBUTION`
- `COORDINATED_TSO_DSO`
- `Q_UNRESOLVED_NETWORK_LAYER`

The first three require referenced evidence claims bound to the exact
`PROJECT_ID:<id>` and `NETWORK_OPERATOR:<operator>`.

A coordinated result requires all three claims:

1. `TRANSMISSION_LAYER`
2. `DISTRIBUTION_LAYER`
3. `TSO_DSO_INTERFACE`

If both layer claims exist but the interface claim does not, the result is Q.
Likewise, an interface claim cannot substitute for the missing other layer.

## Voltage is context, not authority

`voltage_kv` is preserved on the runtime record and decision because it is
physically relevant.  It is deliberately **not** a layer-classification rule.
The regression suite includes the same 132 kV voltage represented once with
transmission authority and once with distribution authority.  Both are valid
because the classification comes from claim-specific evidence rather than a
hard-coded voltage threshold.

This prevents invalid rules such as:

- `132 kV => TRANSMISSION`
- `400 kV => programme-level transmission reinforcement`
- `DSO operator name => every referenced asset is DISTRIBUTION`
- `MAVIR planning document => every mentioned asset is TRANSMISSION`

## Relationship to P1-P6

P7 creates **no second attribution classifier**.

- P1/P2 remain source-native DSO headroom contracts.
- P3 remains the WITHOUT_PROGRAM / WITH_PROGRAM baseline/incremental authority.
- P4 remains the two observed completed RRF DSO baseline projects.
- P5 remains the reinforcement requirement and programme-incremental CAPEX gate.
- P6 remains the project-delivery timing evidence gate.

A P7 layer decision cannot mint:

- headroom;
- connection permission;
- reinforcement requirement;
- baseline status;
- programme causality;
- project cost;
- programme-incremental CAPEX;
- completion probability.

## Registry and readiness outcome

P7 adds no national or regional numeric network rows.  In particular:

- `registry/regional_readiness.csv` remains header-only;
- `registry/incremental_capex_attribution.csv` remains header-only;
- `registry/baseline_infrastructure.csv` remains exactly the two P4 observed
  DSO baseline projects;
- no transmission-project cost or national reinforcement amount is published.

B10 readiness remains **15** because P7 bounds an authority distinction but does
not yet provide a complete Hungarian transmission-project inventory, national
DSO coverage, programme-demand-to-node mapping, regional capacity model, or
programme-specific reinforcement evidence.

## Remaining blockers

Still open after P7:

- canonical spatial correspondence / Q-B01-002;
- complete transmission and distribution project/constraint inventory;
- national DSO coverage;
- exact programme demand mapped to DSO nodes;
- managed-peak physical survivability;
- real programme reinforcement studies;
- separable programme-incremental CAPEX;
- calibrated future investment timing path / Q-B10-002.
