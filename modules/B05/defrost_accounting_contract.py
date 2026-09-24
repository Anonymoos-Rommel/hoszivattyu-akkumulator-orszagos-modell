"""B05-P14 EN 14511 defrost-accounting contract.

The contract separates rating-point accounting from a weather-driven defrost
runtime model.

EN14511_RATED_POINT -> NO_EXTRA_UNIVERSAL_DEFROST_PENALTY
does not mean that every rating point contained an actual defrost event.
"""

from __future__ import annotations

from dataclasses import dataclass


EN14511 = "EXPLICIT_EN14511"
EXPLICIT_EXCLUSION = "EXPLICIT_DEFROST_EXCLUSION"
UNKNOWN = "TEST_BASIS_NOT_EXPLICITLY_BOUND"

NO_EXTRA_UNIVERSAL_PENALTY = "NO_EXTRA_UNIVERSAL_DEFROST_PENALTY"
DEFROST_EXCLUDED = "DEFROST_EXCLUDED_FROM_SOURCE_CURVE"
ACCOUNTING_Q = "Q / DEFROST_ACCOUNTING_BOUNDARY_UNRESOLVED"
RUNTIME_Q = "Q / WEATHER_DRIVEN_DEFROST_RUNTIME_MODEL_REQUIRED"


@dataclass(frozen=True)
class DefrostAccountingDecision:
    test_basis_status: str
    point_accounting_status: str
    extra_universal_penalty_allowed: bool
    runtime_model_status: str
    reason: str


def decide_defrost_accounting(test_basis_status: str) -> DefrostAccountingDecision:
    if test_basis_status == EN14511:
        return DefrostAccountingDecision(
            test_basis_status=EN14511,
            point_accounting_status=NO_EXTRA_UNIVERSAL_PENALTY,
            extra_universal_penalty_allowed=False,
            runtime_model_status=RUNTIME_Q,
            reason=(
                "EN 14511 heating-capacity/effective-input accounting includes "
                "defrost effects that occur within the rating interval; a second "
                "generic penalty risks double counting."
            ),
        )
    if test_basis_status == EXPLICIT_EXCLUSION:
        return DefrostAccountingDecision(
            test_basis_status=EXPLICIT_EXCLUSION,
            point_accounting_status=DEFROST_EXCLUDED,
            extra_universal_penalty_allowed=False,
            runtime_model_status=RUNTIME_Q,
            reason=(
                "Source explicitly excludes defrost from the published curve; "
                "a separate evidence-backed runtime model would be required."
            ),
        )
    if test_basis_status == UNKNOWN:
        return DefrostAccountingDecision(
            test_basis_status=UNKNOWN,
            point_accounting_status=ACCOUNTING_Q,
            extra_universal_penalty_allowed=False,
            runtime_model_status=RUNTIME_Q,
            reason=(
                "Test basis does not prove the point-level defrost boundary; "
                "no invented penalty or EN14511 promotion is allowed."
            ),
        )
    raise ValueError(f"unsupported defrost test-basis status: {test_basis_status!r}")


def point_test_basis(test_standard: str) -> str:
    normalized = (test_standard or "").upper().replace(" ", "")
    if "EN14511" in normalized:
        return EN14511
    return UNKNOWN
