# B06-P64 — realized completion and S1 handoff

**State:** `Q-B06-009 RESOLVED / REALIZED COMPLETION SEPARATED FROM ENERGY OUTCOME`

**Canonical base:** `bfb7a1f1a67a3d9aaabe450c2226265e392fda75`

**Implementation date:** 2026-09-20

## 1. Purpose

P64 resolves when a retrofit intervention may be treated as **physically
completed** and handed from an S0/S1 candidate state into S1.

The key repair is architectural:

`FINAL INVOICE != ENERGY OUTCOME`

`FINAL HET != DELIVERED SCOPE`

`PLANNED POST != REALIZED POST`

`S1 READY = REALIZED COMPLETION + LINKED OUTCOME`

P60 already established the linked before/after energy-outcome gate. P64 adds
the missing realized-delivery gate in front of it.

## 2. Current Hungarian programme authority

### 2.1 Official current programme page

Source:
`SRC-B06-HU-OFP-KEHOP-2026`

The current Magyar Fejlesztési Bank Otthonfelújítási Program page confirms the
active programme logic, including the requirement for at least 30% demonstrated
primary-energy saving and recovery of financing where the post-project
requirement is not achieved.

This is current programme authority, but the public page does not expose every
closing-document field directly.

### 2.2 Exact current programme-call document

Source:
`SRC-B06-HU-KEHOP-417-COMPLETION-2025`

Document version:
**KEHOP Plusz-4.1.7-24 Felhívás — Hatályos: 2025. október 15-től**

The exact MFB-branded programme document is publicly available through a third
party mirror. The current MFB programme page points users to the programme
document set; the automated public programme-document endpoint was not
reliably retrievable during this audit, so the exact-version mirror is retained
for clause-level provenance.

The document establishes two distinct closing layers.

### A. Physical/delivery completion evidence

Following supplier advance, the final draw requires:

- an itemized **final invoice** describing the materials used and services
  delivered;
- a **performance confirmation / teljesítés igazolás**;
- the documents are submitted by the Final Beneficiary.

These prove delivered scope and financial/physical performance. They do not by
themselves prove the energy outcome.

### B. Result verification after physical completion

For the result criterion, after **physical completion** the beneficiary must
submit:

- the **final Hiteles Energetikai Tanúsítvány**;
- the supporting **energy calculations**;
- the prescribed **closing documentation**.

The programme compares annual primary-energy values in the opening and final
HET. If the minimum saving is not met, financing is refused/recovered under the
programme rules.

Thus the programme itself separates:

`physical completion -> closing documents -> final HET result test`.

## 3. P64 realized-completion evidence

The executable gate is:

`modules/B06/realized_completion_gate.py`

Required fields:

- record ID;
- intervention ID;
- project ID;
- site-link ID;
- OBS completion status;
- physical-completion date;
- final-HET date;
- contract scope IDs;
- realized scope IDs;
- final-invoice references;
- performance-confirmation references;
- final-HET references;
- final-energy-calculation references;
- verifier ID;
- final HET linked to the same record and site;
- explicit physical-completion declaration;
- reproducible repository binding.

The final HET must not pre-date physical completion.

## 4. Scope deviations

The contract scope and realized scope are compared explicitly.

If they differ:

- no approved amendment -> `BLOCKED / UNAPPROVED_SCOPE_DEVIATION`;
- approved amendment but no amendment evidence -> `Q`;
- approved amendment with references -> the realized scope may continue to the
  final-outcome gate.

This prevents an S1 promotion where the planned envelope package and the
actually delivered package silently diverge.

## 5. Completion evidence vs outcome evidence

P64 treats completion documents as **OBS**:

- invoice exists;
- performance confirmation exists;
- the scope/date/site linkage exists.

The energetic result may be **DER** because a HET/calculation is a calculated
engineering result.

Therefore the engine no longer requires:

`completion_status == outcome_evidence_status`

Instead:

`completion_status == OBS realized-completion evidence`

and independently:

`P60 outcome = OBS or DER`.

This is the correct epistemic split.

## 6. S1 engine rule

Before P64, the B06 engine could promote S1 when a linked P60 outcome existed
and the generic completion status/source IDs were present.

After P64, every intervention must satisfy **both**:

1. `assess_realized_completion(...) == QUALIFIED`
2. `assess_s1_demand_outcome(...) == READY`

and the realized-completion and outcome records must have:

- the same record ID;
- the same intervention ID.

Only then:

`S1_DEMAND_REDUCED / READY`

may be emitted.

## 7. What counts as insufficient evidence

The following are deliberately insufficient:

### Invoice only

`FINAL INVOICE != PHYSICAL COMPLETION`

Without performance confirmation, final HET and final calculation the chain is
incomplete.

### Final HET only

`FINAL HET != DELIVERED SCOPE`

A calculated final building state does not prove which contracted works were
actually delivered unless the delivery/scope chain is present.

### Planned post calculation

`PLANNED POST DER != REALIZED POST DER`

P62's Zalavár planned post state remains calibration evidence only and cannot
open S1.

### Claimed completion without date/site linkage

`DECLARED COMPLETE != LINKED COMPLETION`

Missing record/site/date/verifier or missing repository binding stays `Q`.

## 8. B02 readiness-bridge repair

P64 also repairs stale canonical bridge rows left behind after P57-P59.

### Hydraulic

The old bridge still said no B02 source existed.

Canonical replacement:

- `modules/B02/hydraulic_transition_gate.py`
- `registry/b02_p57_hydraulic_transition_authority.csv`
- status: `CONTRACTED`
- grain: record/project.

### Electrical

Canonical replacement:

- `modules/B02/electrical_transition_gate.py`
- `registry/b02_p58_electrical_transition_authority.csv`
- status: `CONTRACTED`
- DSO pending remains Q; refusal remains BLOCKED.

### Permit / site legal delivery

P59 removed permit from technical S2 eligibility.

Canonical bridge now states:

- `modules/B02/site_legal_delivery_gate.py`
- `registry/b02_p59_site_legal_delivery_authority.csv`
- status: `CONTRACTED`;
- not required for the B02 technical S2 gate;
- still mandatory as a separate site legal/delivery gate.

Historical gap rows remain lineage only.

## 9. Programme effect

P64 resolves **Q-B06-009** as a completion-authority question.

The project now has a fail-closed rule for:

`planned retrofit -> delivered scope -> physically completed building -> final HET -> linked outcome -> S1`.

It does **not** create:

- a public national completed-project microdataset;
- a national completion rate;
- evidence that a particular private household has completed works;
- an automatic S1 count;
- a replacement for P60 outcome evidence.

Each real household remains independently evidence-bound.

## 10. Next boundary

After P64, the logical next B06 technical blocker remains:

`Q-B06-008`

— building-level emitter inventory / real supply-return-temperature evidence for
S2 and B05 operating-point handoff.

The heat-emitter national-stock branch remains parked pending the KSH response;
P64 does not weaken that requirement.
