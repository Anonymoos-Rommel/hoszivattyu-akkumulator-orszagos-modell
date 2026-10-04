# V1-060 dated regional keys and owner policy

The existing P63/P64 evidence can supply the original B08-D03 regional-key
data handoff. Separately, the owner's 4 October answers select household
cash-flow protection, benefit-per-public-HUF priority and a 2028 planning
start. No physical calculation or source input cell changes in this slice.

## B08-D03 handoff by verified reuse

The original task asks for a DSO/layer or county key, proved mapping,
disclosed noncoverage, and separation of national control-area facts from
substation facts. It does not require new regional MW series, population
weights, full residual identity enumeration or electrical headroom before
the key data can be handed off.

`registry/b08_dated_regional_key_handoff.json` binds the exact curated source
snapshot at commit `b7cabc95c181135bbdf02239015e3e0a9f26484a` to the existing
callable `modules.B10.effective_service_area_projection.build_effective_service_area_projection`.
Its output has 3,052 unique whole-settlement keys and one exact Tass
usage-location key across six operators, after 13 explicit supersessions.
Every row and source lineage was independently reconstructed. The handoff
retains all ten emitted positive source IDs and the separate MVM Démász M1
authority that supports the excluded whole-settlement claims.

The offered region scheme is `DSO_SERVICE_AREA`; the region identifier is
`service_area_id`. Whole mappings require an exact five-digit KSH settlement
code. The Tass subset requires `ELMU:TASS:UDULOTERULET` or an independently
proved upstream mapping to that exact usage location. Code `20525` alone
does not establish the subset. No fuzzy-name, parent, complement, nearest
region or default-DSO assignment is admitted.

The existing callable enumerates qualified rows; this slice does not claim
a new resolver. B08's generic region-string fields do not themselves verify
geographical membership. A consumer must retain the source identity, scope,
status and lineage and keep unknown/ambiguous mappings Q or refuse them.
An absent key is not automatically a proved member of the counted residual.

## Residual and date limits

P64 uses the 2025-01-01 denominator of 3,155 settlements. There are 103
whole-unproven settlements including the one exact partial-only case, and
102 with no materialized effective resolution. These are settlement counts,
not household, population or load coverage. The residual identities are not
fully enumerated and no assignment is imputed.

The 4 October review date identifies reuse of a published snapshot. It is
not a new DSO source retrieval or a legal effective-from date. Source-native
revision and currentness fields, including P22's DER package-lineage route,
are retained. This handoff does not establish assignment throughout the
2025 load year or future programme years. A live operational territory claim
would require its own applicable evidence check.

The national observed load series is not split into these regions. No
electrical node, headroom, reinforcement, connection permission, programme
eligibility or complete national-readiness result follows. B08-D02 and
broader Q-B01-002/Q-B08-001 matters remain separate.

Already published facts and attribution are reused. Original DSO/KSH
documents and private P65/P66 correspondence are not added to the public
repository. This work does not claim new raw-document review or blanket
republication permission.

## Owner choices and clarified cohort mechanism

The policy digest retains mandatory household non-worsening from the first
day, benefit per public HUF as conflict priority under that constraint, and
planning start2028-01-01. Later same-day clarification adds completed
heat-pump+battery+insulation cohorts: subsidy exit requires an unsubsidized
total energy bill below the prior subsidized comparison baseline and the
separate full household cash-flow protection. Work underway does not qualify.

Each qualifying cohort can release attributable recurring state subsidy in
later applicable periods, counted once per cohort/period. Only net actually
available fiscal cash can be reinvested, with a time-varying0..1 share. Seed
finance and timing bridges are separate; an unset annual ceiling is not an
unlimited budget. Capacity/training constraints can limit any endogenous
acceleration. Formal delivery and eventual explicit user scenario controls
are recorded in the parameter/accounting contract, without implementing a
full numerical programme or final user interface.

The original15-year registry default is cleared. A later possible10–20year
range is not a selected horizon. Exact target, ceiling, share, debt limits,
benefit metric, numerical weights and output tolerances remain unset. The
owner's illustrative subsidy/bill amounts and conditionalSPF3 are not inputs.
See `registry/subsidy_reinvestment_policy_contract.json` and
`docs/methodology/owner_policy_20261004.md` for actor, timing, source and
no-double-counting requirements. No physical source cell changes.

## Verification and acceptance boundary

The independent reuse audit checked all 3,053 rows/lineages, all 13 exclusions,
the residual arithmetic and 44 published repository artifacts. Its 33 focused
tests passed with zero skips. It found all original B08-D03 data clauses
satisfiable by this dated handoff; this is not acceptance of the whole B08
module or every programme-input dependency.

The exact new packet still requires independent review and canonical checks.
At first-stage preparation, B08-D03 was recorded as `REVIEW_REQUIRED`.
Acceptance is a separate later record bound to the actual published
implementation, successful skip-free hosted verification and exact review;
the handoff itself does not confer registry acceptance.
B01-P01/B13-P01 remain partial; B19-D02 is not closed by these choices.
