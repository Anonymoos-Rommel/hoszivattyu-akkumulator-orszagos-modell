"""B10-P62 effective DSO service-area membership admission.

Raw materialization is an audit surface, not automatically an effective current
claim.  P61 exposed thirteen cases where a counterpart DSO had previously been
materialized as WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN while the current MVM
Demasz M1 explicitly states that MVM Demasz operates low-/medium-voltage
network on part of the same administrative settlement.

Core rule:

    RAW MATERIALIZED WHOLE CLAIM
    !=
    EFFECTIVE CURRENT WHOLE-SETTLEMENT ADMISSION

A later current claim-specific partial-settlement conflict can supersede the
whole-settlement admission without deleting the historical/raw evidence row.
"""

from __future__ import annotations

from dataclasses import dataclass


WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN = "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN"
EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP = "EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP"
WHOLE_SETTLEMENT_CLAIM_SUPERSEDED = "WHOLE_SETTLEMENT_CLAIM_SUPERSEDED"


class B10EffectiveMembershipError(ValueError):
    """Raised when effective-membership admission is ambiguous or malformed."""


@dataclass(frozen=True)
class WholeMembershipSupersession:
    settlement_name: str
    prior_operator_id: str
    conflict_operator_id: str
    authority_source_id: str
    reason: str

    def __post_init__(self) -> None:
        for name in (
            "settlement_name",
            "prior_operator_id",
            "conflict_operator_id",
            "authority_source_id",
            "reason",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10EffectiveMembershipError(f"{name} is required")
        if self.prior_operator_id == self.conflict_operator_id:
            raise B10EffectiveMembershipError("supersession requires a cross-operator conflict")

    @property
    def key(self) -> tuple[str, str]:
        return (self.settlement_name, self.prior_operator_id)


@dataclass(frozen=True)
class EffectiveWholeMembershipDecision:
    settlement_name: str
    operator_id: str
    raw_status: str
    effective_status: str
    authority_source_id: str | None
    reason: str

    def __post_init__(self) -> None:
        if self.raw_status != WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN:
            raise B10EffectiveMembershipError(
                "P62 effective-whole admission only evaluates raw proven-whole claims"
            )
        if self.effective_status not in {
            EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP,
            WHOLE_SETTLEMENT_CLAIM_SUPERSEDED,
        }:
            raise B10EffectiveMembershipError("invalid effective membership status")
        if self.effective_status == WHOLE_SETTLEMENT_CLAIM_SUPERSEDED:
            if not self.authority_source_id:
                raise B10EffectiveMembershipError(
                    "superseded whole claim requires the conflicting authority source"
                )
        elif self.authority_source_id is not None:
            raise B10EffectiveMembershipError(
                "non-superseded effective claim cannot invent a supersession authority"
            )


def classify_effective_whole_membership(
    *,
    settlement_name: str,
    operator_id: str,
    raw_status: str,
    supersessions: tuple[WholeMembershipSupersession, ...],
) -> EffectiveWholeMembershipDecision:
    """Apply exact-pair supersessions to a raw whole-settlement claim.

    Supersessions are deliberately exact on (settlement_name, operator_id).
    There is no fuzzy name matching, parent-settlement inference, source-form
    normalization, or propagation to other operators/settlements.
    """

    if not isinstance(settlement_name, str) or not settlement_name.strip():
        raise B10EffectiveMembershipError("settlement_name is required")
    if not isinstance(operator_id, str) or not operator_id.strip():
        raise B10EffectiveMembershipError("operator_id is required")
    if raw_status != WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN:
        raise B10EffectiveMembershipError(
            "raw_status must be WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN"
        )
    if isinstance(supersessions, (str, bytes)):
        raise B10EffectiveMembershipError("supersessions must be a collection")

    by_key: dict[tuple[str, str], WholeMembershipSupersession] = {}
    for item in supersessions:
        if not isinstance(item, WholeMembershipSupersession):
            raise B10EffectiveMembershipError(
                "supersessions must contain WholeMembershipSupersession values"
            )
        if item.key in by_key:
            raise B10EffectiveMembershipError("duplicate exact supersession key")
        by_key[item.key] = item

    key = (settlement_name, operator_id)
    item = by_key.get(key)
    if item is not None:
        return EffectiveWholeMembershipDecision(
            settlement_name=settlement_name,
            operator_id=operator_id,
            raw_status=raw_status,
            effective_status=WHOLE_SETTLEMENT_CLAIM_SUPERSEDED,
            authority_source_id=item.authority_source_id,
            reason=item.reason,
        )

    return EffectiveWholeMembershipDecision(
        settlement_name=settlement_name,
        operator_id=operator_id,
        raw_status=raw_status,
        effective_status=EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP,
        authority_source_id=None,
        reason="no exact P62 supersession applies to this raw whole-settlement claim",
    )


def require_effective_whole_membership(decision: EffectiveWholeMembershipDecision) -> None:
    """Fail closed unless a raw whole-settlement claim remains effectively admitted."""

    if not isinstance(decision, EffectiveWholeMembershipDecision):
        raise B10EffectiveMembershipError(
            "decision must be EffectiveWholeMembershipDecision"
        )
    if decision.effective_status != EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP:
        raise B10EffectiveMembershipError(
            "effective whole-settlement membership is required"
        )


__all__ = [
    "B10EffectiveMembershipError",
    "EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP",
    "EffectiveWholeMembershipDecision",
    "WHOLE_SETTLEMENT_CLAIM_SUPERSEDED",
    "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN",
    "WholeMembershipSupersession",
    "classify_effective_whole_membership",
    "require_effective_whole_membership",
]
