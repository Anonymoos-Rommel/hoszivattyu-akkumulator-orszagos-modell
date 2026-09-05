"""Fail-closed WBL017 code-set and gap-cause authority gates.

B02-P11 separates source-code existence from proof that a selected code set is
an exhaustive, disjoint source-native partition. B02-P13 adds source-native V67
hierarchy evidence proving that code-set completeness and population coverage
are separate claims: a complete non-TOTAL partition may coexist with records
present only in TOTAL.
"""

from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
QUALIFIED = "QUALIFIED"
REAL_EVIDENCE = frozenset({"OBS", "DER"})


@dataclass(frozen=True)
class AuthorityDecision:
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class CodeSetAuthorityInputs:
    structure_pinned: bool
    selected_codes_exist_in_source: bool
    source_leaf_partition_explicitly_proven: bool
    selected_codes_exhaustive: bool
    selected_codes_disjoint: bool
    leaf_projection_reconciled_to_total: bool


def assess_codeset_authority(inputs: CodeSetAuthorityInputs) -> AuthorityDecision:
    """Assess source-native non-TOTAL partition authority.

    ``leaf_projection_reconciled_to_total`` is retained as a population-coverage
    diagnostic, but it is not a code-set-authority requirement after P13 proved
    that V67 TOTAL contains records outside every non-TOTAL FUTMODAG_V3 branch.
    """

    blockers: list[str] = []
    if not inputs.structure_pinned:
        blockers.append("STRUCTURE_NOT_PINNED")
    if not inputs.selected_codes_exist_in_source:
        blockers.append("SELECTED_CODE_NOT_SOURCE_NATIVE")
    if not inputs.source_leaf_partition_explicitly_proven:
        blockers.append("SOURCE_LEAF_PARTITION_NOT_PROVEN")
    if not inputs.selected_codes_exhaustive:
        blockers.append("SELECTED_CODESET_NOT_EXHAUSTIVE")
    if not inputs.selected_codes_disjoint:
        blockers.append("SELECTED_CODESET_NOT_DISJOINT")

    if blockers:
        return AuthorityDecision(Q, tuple(blockers))
    return AuthorityDecision(QUALIFIED, ())


@dataclass(frozen=True)
class GapCauseInputs:
    source_native_cause_identified: bool
    cause_evidence_status: str
    cause_reconciles_exact_gap: bool


def assess_gap_cause(inputs: GapCauseInputs) -> AuthorityDecision:
    """Require source-native evidence before assigning a mechanism to a count gap."""

    blockers: list[str] = []
    if not inputs.source_native_cause_identified:
        blockers.append("SOURCE_NATIVE_CAUSE_UNRESOLVED")
    if inputs.cause_evidence_status not in REAL_EVIDENCE:
        blockers.append("CAUSE_EVIDENCE_NOT_OBS_OR_DER")
    if not inputs.cause_reconciles_exact_gap:
        blockers.append("CAUSE_DOES_NOT_RECONCILE_EXACT_GAP")

    if blockers:
        return AuthorityDecision(Q, tuple(blockers))
    return AuthorityDecision(QUALIFIED, ())
