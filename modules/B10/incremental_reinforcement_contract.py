"""Fail-closed B10-P5 reinforcement and programme-CAPEX attribution gate.

B10-P5 deliberately keeps four truths separate:

1. published DSO headroom screening;
2. an authoritative DSO/MGT/network-study reinforcement determination;
3. the canonical B10-P3 WITHOUT_PROGRAM/WITH_PROGRAM attribution decision; and
4. claim-specific programme-incremental CAPEX evidence.

A published headroom exceedance is only a screening result.  It cannot mint a
reinforcement project, reinforcement scope, project cost, customer charge or
programme-incremental CAPEX.  B10-P3 remains the sole attribution classifier;
this module adds the stricter physical/evidence gate that must be satisfied
before P3 incremental flags or numeric incremental CAPEX are accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .baseline_infrastructure_contract import (
    AttributionDecision,
    InfrastructureEvidence,
    InfrastructureRecord,
    classify_infrastructure,
)
from .dso_headroom_contract import (
    CONNECTION_AUTHORITY,
    CURRENT,
    FIVE_YEAR,
    HORIZONS,
    MVM_DEMASZ_OPERATOR,
    REGION_SCHEME,
    SOURCE_SEMANTICS,
    DsoHeadroomRecord,
    HeadroomAssessment,
)


class B10IncrementalReinforcementContractError(ValueError):
    """Raised when reinforcement or programme-CAPEX authority is ambiguous."""


DSO_SUBSTATION = REGION_SCHEME
NONE_NON_ADDITIVE = "NONE_NON_ADDITIVE"

WITHIN_PUBLISHED_HEADROOM_SCREENING = "WITHIN_PUBLISHED_HEADROOM_SCREENING"
EXCEEDS_PUBLISHED_HEADROOM_SCREENING = "EXCEEDS_PUBLISHED_HEADROOM_SCREENING"
SCREENING_Q = "Q"
SCREENING_STATUSES = {
    WITHIN_PUBLISHED_HEADROOM_SCREENING,
    EXCEEDS_PUBLISHED_HEADROOM_SCREENING,
    SCREENING_Q,
}
SCREENING_EVIDENCE_STATUSES = {"DER", "SCN", "Q"}

REINFORCEMENT_REQUIRED = "REINFORCEMENT_REQUIRED"
INCREMENTAL_SCOPE = "INCREMENTAL_SCOPE"
INCREMENTAL_CAPACITY = "INCREMENTAL_CAPACITY"
ACCELERATION = "ACCELERATION"
UPSIZE = "UPSIZE"
PROGRAM_INCREMENTAL_COST = "PROGRAM_INCREMENTAL_COST"
ACCELERATION_COST = "ACCELERATION_COST"
UPSIZE_COST = "UPSIZE_COST"
CUSTOMER_CONNECTION_CHARGE = "CUSTOMER_CONNECTION_CHARGE"
TOTAL_REINFORCEMENT_PROJECT_COST = "TOTAL_REINFORCEMENT_PROJECT_COST"

CUSTOMER_CONNECTION_CHARGE_HUF = "CUSTOMER_CONNECTION_CHARGE_HUF"
TOTAL_REINFORCEMENT_PROJECT_COST_HUF = "TOTAL_REINFORCEMENT_PROJECT_COST_HUF"
PROGRAM_INCREMENTAL_CAPEX_HUF = "PROGRAM_INCREMENTAL_CAPEX_HUF"

PROJECT_BINDING_PREFIX = "PROJECT_ID:"
NETWORK_OPERATOR_BINDING_PREFIX = "NETWORK_OPERATOR:"
REGION_BINDING_PREFIX = "REGION_ID:"
REGION_GRAIN_BINDING = "REGION_GRAIN:DSO_SUBSTATION"
HORIZON_BINDING_PREFIX = "HORIZON:"
COST_COMPONENT_BINDING_PREFIX = "COST_COMPONENT:"

_REINFORCEMENT_AUTHORITY_MAX_LEVEL = 2
_COST_AUTHORITY_MAX_LEVEL = 3
_ALLOWED_REINFORCEMENT_EVIDENCE_TRUTH = {"OBS", "DER", "SCN"}


def _finite_nonnegative(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10IncrementalReinforcementContractError(
            f"{field_name} must be finite and non-negative or explicit None"
        )
    return float(value)


@dataclass(frozen=True)
class HeadroomScreeningContext:
    """One exact-node screening result; never a reinforcement decision."""

    network_operator: str
    region_id: str
    region_grain: str
    horizon: str
    screening_status: str
    evidence_status: str
    source_refs: tuple[str, ...]
    incremental_demand_mw: float | None
    published_headroom_mw: float | None
    remaining_headroom_mw: float | None
    overload_mw: float | None
    connection_authority: str = CONNECTION_AUTHORITY
    headroom_semantics: str = SOURCE_SEMANTICS
    aggregation_authority: str = NONE_NON_ADDITIVE

    def __post_init__(self) -> None:
        if not isinstance(self.network_operator, str) or not self.network_operator.strip():
            raise B10IncrementalReinforcementContractError("network_operator is required")
        if not isinstance(self.region_id, str) or not self.region_id.strip():
            raise B10IncrementalReinforcementContractError("region_id is required")
        if self.region_grain != DSO_SUBSTATION:
            raise B10IncrementalReinforcementContractError(
                "headroom screening requires exact DSO_SUBSTATION grain"
            )
        if self.horizon not in HORIZONS:
            raise B10IncrementalReinforcementContractError(
                "screening horizon must be CURRENT or FIVE_YEAR"
            )
        if self.screening_status not in SCREENING_STATUSES:
            raise B10IncrementalReinforcementContractError("invalid screening_status")
        if self.evidence_status not in SCREENING_EVIDENCE_STATUSES:
            raise B10IncrementalReinforcementContractError(
                "derived screening evidence must be DER, SCN or Q; never OBS"
            )
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10IncrementalReinforcementContractError("screening source_refs are required")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B10IncrementalReinforcementContractError("screening source_refs cannot be blank")
        if self.connection_authority != CONNECTION_AUTHORITY:
            raise B10IncrementalReinforcementContractError(
                "published headroom cannot replace MGT authority"
            )
        if self.headroom_semantics != SOURCE_SEMANTICS:
            raise B10IncrementalReinforcementContractError(
                "screening must preserve indicative headroom semantics"
            )
        if self.aggregation_authority != NONE_NON_ADDITIVE:
            raise B10IncrementalReinforcementContractError(
                "substation headroom remains non-additive"
            )

        demand = _finite_nonnegative(self.incremental_demand_mw, "incremental_demand_mw")
        headroom = _finite_nonnegative(self.published_headroom_mw, "published_headroom_mw")
        remaining = _finite_nonnegative(self.remaining_headroom_mw, "remaining_headroom_mw")
        overload = _finite_nonnegative(self.overload_mw, "overload_mw")
        object.__setattr__(self, "incremental_demand_mw", demand)
        object.__setattr__(self, "published_headroom_mw", headroom)
        object.__setattr__(self, "remaining_headroom_mw", remaining)
        object.__setattr__(self, "overload_mw", overload)

        values = (demand, headroom, remaining, overload)
        if self.screening_status == SCREENING_Q:
            if self.evidence_status != "Q":
                raise B10IncrementalReinforcementContractError(
                    "Q screening must preserve Q evidence status"
                )
            return
        if self.evidence_status == "Q" or any(value is None for value in values):
            raise B10IncrementalReinforcementContractError(
                "non-Q screening requires complete non-Q numeric evidence"
            )
        if self.screening_status == EXCEEDS_PUBLISHED_HEADROOM_SCREENING and overload <= 0:
            raise B10IncrementalReinforcementContractError(
                "EXCEEDS screening requires a positive overload"
            )
        if self.screening_status == WITHIN_PUBLISHED_HEADROOM_SCREENING and overload != 0:
            raise B10IncrementalReinforcementContractError(
                "WITHIN screening cannot carry an overload"
            )


@dataclass(frozen=True)
class ReinforcementGateDecision:
    """P5 wrapper around the canonical P3 attribution decision."""

    project_id: str
    region_id: str
    horizon: str
    screening_status: str
    reinforcement_required_proven: bool
    attribution: AttributionDecision
    program_incremental_capex_huf: float | None


def screening_context_from_headroom_assessment(
    record: DsoHeadroomRecord,
    assessment: HeadroomAssessment,
    *,
    programme_horizon: str,
) -> HeadroomScreeningContext:
    """Convert one canonical P1 assessment into a screening-only P5 context.

    No OPUS adapter or cross-DSO assessment is introduced here.  The accepted
    path is deliberately the existing MVM P1 exact-substation assessment.
    """

    if not isinstance(record, DsoHeadroomRecord):
        raise B10IncrementalReinforcementContractError(
            "P5 screening currently accepts only the canonical MVM DsoHeadroomRecord"
        )
    if not isinstance(assessment, HeadroomAssessment):
        raise B10IncrementalReinforcementContractError("assessment must be HeadroomAssessment")
    if programme_horizon not in HORIZONS:
        raise B10IncrementalReinforcementContractError(
            "programme_horizon must be CURRENT or FIVE_YEAR"
        )
    if programme_horizon != record.horizon or assessment.horizon != record.horizon:
        raise B10IncrementalReinforcementContractError(
            "CURRENT and FIVE_YEAR horizons cannot be substituted"
        )
    if assessment.region_scheme != DSO_SUBSTATION or assessment.region_id != record.region_id:
        raise B10IncrementalReinforcementContractError(
            "screening assessment must preserve the exact DSO_SUBSTATION identity"
        )
    if assessment.connection_authority != CONNECTION_AUTHORITY:
        raise B10IncrementalReinforcementContractError(
            "assessment must preserve MGT_REQUIRED authority"
        )
    if assessment.evidence_status not in SCREENING_EVIDENCE_STATUSES:
        raise B10IncrementalReinforcementContractError(
            "screening assessment can be DER, SCN or Q only"
        )

    if (
        assessment.evidence_status == "Q"
        or assessment.published_headroom_mw is None
        or assessment.remaining_headroom_mw is None
        or assessment.overload_mw is None
    ):
        screening_status = SCREENING_Q
    elif assessment.overload_mw > 0:
        screening_status = EXCEEDS_PUBLISHED_HEADROOM_SCREENING
    else:
        screening_status = WITHIN_PUBLISHED_HEADROOM_SCREENING

    return HeadroomScreeningContext(
        network_operator=MVM_DEMASZ_OPERATOR,
        region_id=assessment.region_id,
        region_grain=assessment.region_scheme,
        horizon=assessment.horizon,
        screening_status=screening_status,
        evidence_status="Q" if screening_status == SCREENING_Q else assessment.evidence_status,
        source_refs=assessment.source_refs,
        incremental_demand_mw=assessment.incremental_demand_mw,
        published_headroom_mw=assessment.published_headroom_mw,
        remaining_headroom_mw=assessment.remaining_headroom_mw,
        overload_mw=assessment.overload_mw,
    )


def _record_binding_claims(record: InfrastructureRecord, horizon: str) -> tuple[str, ...]:
    return (
        f"{PROJECT_BINDING_PREFIX}{record.project_id}",
        f"{NETWORK_OPERATOR_BINDING_PREFIX}{record.network_operator}",
        f"{REGION_BINDING_PREFIX}{record.region_id}",
        REGION_GRAIN_BINDING,
        f"{HORIZON_BINDING_PREFIX}{horizon}",
    )


def _evidence_supports_bound_claim(
    evidence: InfrastructureEvidence,
    record: InfrastructureRecord,
    horizon: str,
    claim: str,
    *,
    max_authority_level: int,
    cost_component_id: str | None = None,
) -> bool:
    if evidence.authority_level > max_authority_level:
        return False
    if evidence.truth_status not in _ALLOWED_REINFORCEMENT_EVIDENCE_TRUTH:
        return False
    supports = set(evidence.supports)
    if claim not in supports:
        return False
    if not set(_record_binding_claims(record, horizon)).issubset(supports):
        return False
    if cost_component_id is not None:
        if f"{COST_COMPONENT_BINDING_PREFIX}{cost_component_id}" not in supports:
            return False
    return True


def _referenced_claim_exists(
    record: InfrastructureRecord,
    horizon: str,
    claim: str,
    *,
    max_authority_level: int,
    cost_component_id: str | None = None,
) -> bool:
    return any(
        _evidence_supports_bound_claim(
            item,
            record,
            horizon,
            claim,
            max_authority_level=max_authority_level,
            cost_component_id=cost_component_id,
        )
        for item in record.referenced_evidence
    )


def _require_difference_evidence(record: InfrastructureRecord, horizon: str) -> None:
    checks = (
        (
            record.incremental_scope_proven,
            (REINFORCEMENT_REQUIRED, INCREMENTAL_SCOPE),
            "incremental_scope_proven",
        ),
        (
            record.incremental_capacity_proven,
            (REINFORCEMENT_REQUIRED, INCREMENTAL_CAPACITY),
            "incremental_capacity_proven",
        ),
        (record.acceleration_proven, (ACCELERATION,), "acceleration_proven"),
        (record.upsizing_proven, (UPSIZE,), "upsizing_proven"),
    )
    for enabled, claims, flag_name in checks:
        if not enabled:
            continue
        for claim in claims:
            if not _referenced_claim_exists(
                record,
                horizon,
                claim,
                max_authority_level=_REINFORCEMENT_AUTHORITY_MAX_LEVEL,
            ):
                raise B10IncrementalReinforcementContractError(
                    f"{flag_name} requires referenced claim-specific DSO/MGT/network-study evidence: {claim}"
                )


def _required_specific_cost_claims(record: InfrastructureRecord) -> tuple[str, ...]:
    claims: list[str] = []
    if record.incremental_scope_proven or record.incremental_capacity_proven:
        claims.append(PROGRAM_INCREMENTAL_COST)
    if record.acceleration_proven:
        claims.append(ACCELERATION_COST)
    if record.upsizing_proven:
        claims.append(UPSIZE_COST)
    return tuple(dict.fromkeys(claims))


def validate_programme_incremental_cost_authority(
    record: InfrastructureRecord,
    *,
    horizon: str,
) -> None:
    """Require claim-specific, component-bound authority for numeric P5 CAPEX."""

    if record.incremental_cost_huf is None:
        return
    if horizon not in HORIZONS:
        raise B10IncrementalReinforcementContractError(
            "reinforcement horizon must be CURRENT or FIVE_YEAR"
        )
    if record.cost_component_id is None:
        raise B10IncrementalReinforcementContractError(
            "numeric programme-incremental CAPEX requires exact cost_component_id"
        )
    component = record.cost_component_id

    generic_cost_authority = _referenced_claim_exists(
        record,
        horizon,
        "COST",
        max_authority_level=_COST_AUTHORITY_MAX_LEVEL,
        cost_component_id=component,
    )
    if not generic_cost_authority:
        raise B10IncrementalReinforcementContractError(
            "numeric programme-incremental CAPEX requires referenced component-bound COST authority"
        )

    specific_claims = _required_specific_cost_claims(record)
    if not specific_claims:
        raise B10IncrementalReinforcementContractError(
            "numeric programme-incremental CAPEX requires a proven incremental/acceleration/upsize difference"
        )
    if not any(
        _referenced_claim_exists(
            record,
            horizon,
            claim,
            max_authority_level=_COST_AUTHORITY_MAX_LEVEL,
            cost_component_id=component,
        )
        for claim in specific_claims
    ):
        raise B10IncrementalReinforcementContractError(
            "generic COST, customer connection charge or total project cost cannot mint programme-incremental CAPEX"
        )


def evaluate_programme_incremental_reinforcement(
    record: InfrastructureRecord,
    *,
    reinforcement_horizon: str,
    screening: HeadroomScreeningContext | None = None,
) -> ReinforcementGateDecision:
    """Apply P5 evidence gates, then delegate attribution to canonical B10-P3."""

    if not isinstance(record, InfrastructureRecord):
        raise B10IncrementalReinforcementContractError(
            "reinforcement record must be canonical InfrastructureRecord"
        )
    if reinforcement_horizon not in HORIZONS:
        raise B10IncrementalReinforcementContractError(
            "reinforcement_horizon must be CURRENT or FIVE_YEAR"
        )
    if record.region_grain != DSO_SUBSTATION:
        raise B10IncrementalReinforcementContractError(
            "P5 reinforcement attribution requires exact DSO_SUBSTATION grain"
        )
    if record.region_id == "NATIONAL":
        raise B10IncrementalReinforcementContractError(
            "national records cannot masquerade as exact substation reinforcement"
        )

    screening_status = SCREENING_Q
    if screening is not None:
        if not isinstance(screening, HeadroomScreeningContext):
            raise B10IncrementalReinforcementContractError(
                "screening must be HeadroomScreeningContext"
            )
        if (
            screening.network_operator != record.network_operator
            or screening.region_id != record.region_id
            or screening.region_grain != record.region_grain
        ):
            raise B10IncrementalReinforcementContractError(
                "screening and reinforcement must preserve exact operator/DSO_SUBSTATION identity"
            )
        if screening.horizon != reinforcement_horizon:
            raise B10IncrementalReinforcementContractError(
                "CURRENT and FIVE_YEAR reinforcement horizons cannot be substituted"
            )
        screening_status = screening.screening_status

    _require_difference_evidence(record, reinforcement_horizon)
    validate_programme_incremental_cost_authority(
        record,
        horizon=reinforcement_horizon,
    )

    reinforcement_required_proven = _referenced_claim_exists(
        record,
        reinforcement_horizon,
        REINFORCEMENT_REQUIRED,
        max_authority_level=_REINFORCEMENT_AUTHORITY_MAX_LEVEL,
    )

    attribution = classify_infrastructure(record)
    if record.incremental_cost_huf is not None:
        if attribution.incremental_cost_huf != record.incremental_cost_huf:
            raise B10IncrementalReinforcementContractError(
                "P5 numeric incremental CAPEX must survive canonical P3 attribution unchanged"
            )

    return ReinforcementGateDecision(
        project_id=record.project_id,
        region_id=record.region_id,
        horizon=reinforcement_horizon,
        screening_status=screening_status,
        reinforcement_required_proven=reinforcement_required_proven,
        attribution=attribution,
        program_incremental_capex_huf=attribution.incremental_cost_huf,
    )


__all__ = [
    "ACCELERATION",
    "ACCELERATION_COST",
    "B10IncrementalReinforcementContractError",
    "COST_COMPONENT_BINDING_PREFIX",
    "CURRENT",
    "CUSTOMER_CONNECTION_CHARGE",
    "CUSTOMER_CONNECTION_CHARGE_HUF",
    "DSO_SUBSTATION",
    "EXCEEDS_PUBLISHED_HEADROOM_SCREENING",
    "FIVE_YEAR",
    "HeadroomScreeningContext",
    "HORIZON_BINDING_PREFIX",
    "INCREMENTAL_CAPACITY",
    "INCREMENTAL_SCOPE",
    "NETWORK_OPERATOR_BINDING_PREFIX",
    "NONE_NON_ADDITIVE",
    "PROGRAM_INCREMENTAL_CAPEX_HUF",
    "PROGRAM_INCREMENTAL_COST",
    "PROJECT_BINDING_PREFIX",
    "REGION_BINDING_PREFIX",
    "REGION_GRAIN_BINDING",
    "REINFORCEMENT_REQUIRED",
    "ReinforcementGateDecision",
    "SCREENING_Q",
    "SCREENING_STATUSES",
    "TOTAL_REINFORCEMENT_PROJECT_COST",
    "TOTAL_REINFORCEMENT_PROJECT_COST_HUF",
    "UPSIZE",
    "UPSIZE_COST",
    "WITHIN_PUBLISHED_HEADROOM_SCREENING",
    "evaluate_programme_incremental_reinforcement",
    "screening_context_from_headroom_assessment",
    "validate_programme_incremental_cost_authority",
]
