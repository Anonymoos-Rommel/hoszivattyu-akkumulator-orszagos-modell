"""B02-P100 current-envelope -> programme-action selection crosswalk.

P99 established that fresh envelope-action/state evidence exists, but the
observed categories do not identify reference-programme compliance. P100
therefore makes the missing selection rule executable without promoting
"insulated" or "replaced" labels into U-value compliance.

The crosswalk operates on component-level current U intervals against the
prospective reference-programme component limits already admitted by P80/P96.

Component rule:
- current U upper <= reference U max -> REFERENCE_ENVELOPE_SATISFIED;
- current U lower > reference U max -> REFERENCE_ENVELOPE_DEFICIT;
- interval straddles the limit or U is missing -> UNRESOLVED;
- proven non-applicable component -> NOT_APPLICABLE.

Dwelling/programme rule:
- any proven component deficit -> REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP;
- every applicable component proven satisfied -> AIR_TO_WATER_HP_ONLY candidate;
- otherwise -> UNRESOLVED.

Population shares remain bounded by unresolved mass. No midpoint/default is
introduced.

Critical boundaries:

INSULATED_FACADE != REFERENCE_U_COMPLIANT_WALL
WINDOW_REPLACED != REFERENCE_U_COMPLIANT_WINDOW
RECENT_ENVELOPE_ACTION != CURRENT_COMPONENT_PERFORMANCE
REFERENCE_ENVELOPE_SATISFIED != TECHNICAL_HP_ELIGIBILITY
HP_ONLY_CANDIDATE != FINAL_PROGRAMME_ELIGIBILITY
UNRESOLVED != RETROFIT_REQUIRED
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from modules.B02.fresh_envelope_action_evidence import (
    REKK_2022_STOCK_STATE_SHARES,
    REKK_SOURCE_ID,
)
from modules.B02.keop23_uvalue_poststate import (
    AIR_TO_WATER_HP_ONLY,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    REFERENCE_RETROFIT_U_MAX,
)
from modules.B02.hungarian_facade_opening_split import (
    CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
)
from modules.B02.pitched_roof_poststate_u import (
    PITCHED_ROOF_BASE_U_UPPER_W_M2K,
)


REFERENCE_ENVELOPE_SATISFIED = "REFERENCE_ENVELOPE_SATISFIED"
REFERENCE_ENVELOPE_DEFICIT = "REFERENCE_ENVELOPE_DEFICIT"
CURRENT_ENVELOPE_STATE_UNRESOLVED = "CURRENT_ENVELOPE_STATE_UNRESOLVED"
COMPONENT_NOT_APPLICABLE = "COMPONENT_NOT_APPLICABLE"

HP_ONLY_CANDIDATE = "HP_ONLY_CANDIDATE"
RETROFIT_PLUS_AWHP_REQUIRED = "RETROFIT_PLUS_AWHP_REQUIRED"
PROGRAMME_ACTION_UNRESOLVED = "PROGRAMME_ACTION_UNRESOLVED"

P100_STATUS = "QUALIFIED_REFERENCE_PROGRAMME_ACTION_SELECTION_CROSSWALK"
NEXT_RESIDUAL = "DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED"

REFERENCE_COMPONENT_U_MAX = {
    **REFERENCE_RETROFIT_U_MAX,
    # P80's source-native timber/PVC reference-retrofit value is 1.15,
    # but the prospective programme is governed by the current 9/2023 EKM
    # wood/PVC glazed-opening requirement already admitted in P92: 1.10.
    # P103 therefore supersedes only the WINDOW target while preserving P80
    # as historical calibration.
    "WINDOW": CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
    "PITCHED_ROOF": PITCHED_ROOF_BASE_U_UPPER_W_M2K,
}
REQUIRED_COMPONENT_KEYS = tuple(REFERENCE_COMPONENT_U_MAX)


@dataclass(frozen=True)
class ComponentSelectionAssessment:
    component: str
    current_u_lower_w_m2k: float | None
    current_u_upper_w_m2k: float | None
    reference_u_max_w_m2k: float
    state: str
    evidence_status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class DwellingActionSelection:
    selection_state: str
    programme_action: str | None
    component_states: tuple[tuple[str, str], ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PopulationSelectionRecord:
    population_key: str
    dwelling_equivalents: float
    selection_state: str


@dataclass(frozen=True)
class PopulationActionBounds:
    total_dwelling_equivalents: float
    hp_only_identified_dwelling_equivalents: float
    retrofit_identified_dwelling_equivalents: float
    unresolved_dwelling_equivalents: float
    hp_only_share_lower: float
    hp_only_share_upper: float
    retrofit_share_lower: float
    retrofit_share_upper: float
    status: str
    residual: str | None


@dataclass(frozen=True)
class P99StockStateCrosswalk:
    metric: str
    share: float
    source_id: str
    selection_authority: bool
    status: str
    blocker: str


def reference_programme_component_u_max(component: str) -> float:
    try:
        return float(REFERENCE_COMPONENT_U_MAX[component])
    except KeyError as exc:
        raise ValueError(f"unsupported envelope component {component}") from exc


def assess_component_against_reference(
    *,
    component: str,
    current_u_lower_w_m2k: float | None,
    current_u_upper_w_m2k: float | None,
    applicable: bool | None = True,
    evidence_status: str = "Q",
) -> ComponentSelectionAssessment:
    reference_u = reference_programme_component_u_max(component)

    if applicable is False:
        return ComponentSelectionAssessment(
            component=component,
            current_u_lower_w_m2k=None,
            current_u_upper_w_m2k=None,
            reference_u_max_w_m2k=reference_u,
            state=COMPONENT_NOT_APPLICABLE,
            evidence_status=evidence_status,
            blockers=(),
        )

    if applicable is None:
        return ComponentSelectionAssessment(
            component=component,
            current_u_lower_w_m2k=current_u_lower_w_m2k,
            current_u_upper_w_m2k=current_u_upper_w_m2k,
            reference_u_max_w_m2k=reference_u,
            state=CURRENT_ENVELOPE_STATE_UNRESOLVED,
            evidence_status=evidence_status,
            blockers=("COMPONENT_APPLICABILITY_UNRESOLVED",),
        )

    if current_u_lower_w_m2k is None or current_u_upper_w_m2k is None:
        return ComponentSelectionAssessment(
            component=component,
            current_u_lower_w_m2k=current_u_lower_w_m2k,
            current_u_upper_w_m2k=current_u_upper_w_m2k,
            reference_u_max_w_m2k=reference_u,
            state=CURRENT_ENVELOPE_STATE_UNRESOLVED,
            evidence_status=evidence_status,
            blockers=("CURRENT_COMPONENT_U_INTERVAL_REQUIRED",),
        )

    lower = float(current_u_lower_w_m2k)
    upper = float(current_u_upper_w_m2k)
    if (
        not isfinite(lower)
        or not isfinite(upper)
        or lower <= 0.0
        or upper <= 0.0
        or lower > upper
    ):
        raise ValueError("current component U interval must be finite, positive, and ordered")

    if upper <= reference_u:
        state = REFERENCE_ENVELOPE_SATISFIED
        blockers: tuple[str, ...] = ()
    elif lower > reference_u:
        state = REFERENCE_ENVELOPE_DEFICIT
        blockers = ()
    else:
        state = CURRENT_ENVELOPE_STATE_UNRESOLVED
        blockers = ("CURRENT_COMPONENT_U_INTERVAL_STRADDLES_REFERENCE_LIMIT",)

    return ComponentSelectionAssessment(
        component=component,
        current_u_lower_w_m2k=lower,
        current_u_upper_w_m2k=upper,
        reference_u_max_w_m2k=reference_u,
        state=state,
        evidence_status=evidence_status,
        blockers=blockers,
    )


def select_programme_action(
    assessments: tuple[ComponentSelectionAssessment, ...],
) -> DwellingActionSelection:
    by_component: dict[str, ComponentSelectionAssessment] = {}
    blockers: list[str] = []
    warnings: list[str] = []

    for assessment in assessments:
        if assessment.component in by_component:
            raise ValueError(f"duplicate component assessment {assessment.component}")
        if assessment.component not in REFERENCE_COMPONENT_U_MAX:
            raise ValueError(f"unsupported envelope component {assessment.component}")
        by_component[assessment.component] = assessment

    missing = [
        component for component in REQUIRED_COMPONENT_KEYS if component not in by_component
    ]
    if missing:
        blockers.extend(f"MISSING_COMPONENT_STATE:{component}" for component in missing)

    states = tuple(
        (component, by_component[component].state)
        for component in REQUIRED_COMPONENT_KEYS
        if component in by_component
    )

    if any(
        assessment.state == REFERENCE_ENVELOPE_DEFICIT
        for assessment in by_component.values()
    ):
        return DwellingActionSelection(
            selection_state=RETROFIT_PLUS_AWHP_REQUIRED,
            programme_action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
            component_states=states,
            blockers=(),
            warnings=tuple(blockers),
        )

    unresolved = [
        assessment
        for assessment in by_component.values()
        if assessment.state == CURRENT_ENVELOPE_STATE_UNRESOLVED
    ]
    if blockers or unresolved:
        blockers.extend(
            blocker
            for assessment in unresolved
            for blocker in assessment.blockers
            if blocker not in blockers
        )
        return DwellingActionSelection(
            selection_state=PROGRAMME_ACTION_UNRESOLVED,
            programme_action=None,
            component_states=states,
            blockers=tuple(blockers),
            warnings=(),
        )

    applicable = [
        assessment
        for assessment in by_component.values()
        if assessment.state != COMPONENT_NOT_APPLICABLE
    ]
    if not applicable:
        return DwellingActionSelection(
            selection_state=PROGRAMME_ACTION_UNRESOLVED,
            programme_action=None,
            component_states=states,
            blockers=("NO_APPLICABLE_ENVELOPE_COMPONENT_PROVEN",),
            warnings=(),
        )

    if all(
        assessment.state == REFERENCE_ENVELOPE_SATISFIED
        for assessment in applicable
    ):
        return DwellingActionSelection(
            selection_state=HP_ONLY_CANDIDATE,
            programme_action=AIR_TO_WATER_HP_ONLY,
            component_states=states,
            blockers=(),
            warnings=(
                "HP_ONLY_CANDIDATE_REMAINS_SUBJECT_TO_NON_ENVELOPE_TECHNICAL_GATES",
            ),
        )

    return DwellingActionSelection(
        selection_state=PROGRAMME_ACTION_UNRESOLVED,
        programme_action=None,
        component_states=states,
        blockers=("UNEXPECTED_COMPONENT_SELECTION_STATE",),
        warnings=(),
    )


def bounded_population_action_shares(
    records: tuple[PopulationSelectionRecord, ...],
) -> PopulationActionBounds:
    if not records:
        raise ValueError("at least one population selection record is required")

    seen: set[str] = set()
    hp_only = 0.0
    retrofit = 0.0
    unresolved = 0.0

    for record in records:
        if not record.population_key:
            raise ValueError("population_key is required")
        if record.population_key in seen:
            raise ValueError(f"duplicate population_key {record.population_key}")
        seen.add(record.population_key)

        weight = float(record.dwelling_equivalents)
        if not isfinite(weight) or weight < 0.0:
            raise ValueError("dwelling_equivalents must be finite and non-negative")

        if record.selection_state == HP_ONLY_CANDIDATE:
            hp_only += weight
        elif record.selection_state == RETROFIT_PLUS_AWHP_REQUIRED:
            retrofit += weight
        elif record.selection_state == PROGRAMME_ACTION_UNRESOLVED:
            unresolved += weight
        else:
            raise ValueError(f"unsupported selection_state {record.selection_state}")

    total = hp_only + retrofit + unresolved
    if total <= 0.0:
        raise ValueError("population selection total must be positive")

    residual = NEXT_RESIDUAL if unresolved > 0.0 else None
    status = (
        "PARTIAL_BOUNDED_PROGRAMME_ACTION_SELECTION"
        if unresolved > 0.0
        else "QUALIFIED_COMPLETE_PROGRAMME_ACTION_SELECTION"
    )

    return PopulationActionBounds(
        total_dwelling_equivalents=total,
        hp_only_identified_dwelling_equivalents=hp_only,
        retrofit_identified_dwelling_equivalents=retrofit,
        unresolved_dwelling_equivalents=unresolved,
        hp_only_share_lower=hp_only / total,
        hp_only_share_upper=(hp_only + unresolved) / total,
        retrofit_share_lower=retrofit / total,
        retrofit_share_upper=(retrofit + unresolved) / total,
        status=status,
        residual=residual,
    )


def p99_stock_state_selection_crosswalk() -> tuple[P99StockStateCrosswalk, ...]:
    mapping = (
        ("INSULATED_FACADE", REKK_2022_STOCK_STATE_SHARES["INSULATED_FACADE"]),
        (
            "INSULATED_ATTIC_OR_CEILING",
            REKK_2022_STOCK_STATE_SHARES["INSULATED_ATTIC_OR_CEILING"],
        ),
        ("WINDOW_REPLACED", REKK_2022_STOCK_STATE_SHARES["WINDOW_REPLACED"]),
    )
    return tuple(
        P99StockStateCrosswalk(
            metric=metric,
            share=share,
            source_id=REKK_SOURCE_ID,
            selection_authority=False,
            status="CALIBRATION_ONLY_NOT_PROGRAMME_SELECTION_AUTHORITY",
            blocker=NEXT_RESIDUAL,
        )
        for metric, share in mapping
    )


def p100_state() -> dict[str, object]:
    p99 = p99_stock_state_selection_crosswalk()
    return {
        "status": P100_STATUS,
        "reference_component_u_max": dict(REFERENCE_COMPONENT_U_MAX),
        "p99_stock_state_metric_count": len(p99),
        "p99_stock_state_selection_authority_count": sum(
            1 for row in p99 if row.selection_authority
        ),
        "crosswalk_blocker": None,
        "remaining_population_evidence_residual": NEXT_RESIDUAL,
        "national_programme_action_point_share_identified": False,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "INSULATED_FACADE_IS_NOT_REFERENCE_U_COMPLIANT_WALL",
        "WINDOW_REPLACED_IS_NOT_REFERENCE_U_COMPLIANT_WINDOW",
        "RECENT_ENVELOPE_ACTION_IS_NOT_CURRENT_COMPONENT_PERFORMANCE",
        "REFERENCE_ENVELOPE_SATISFIED_IS_NOT_TECHNICAL_HP_ELIGIBILITY",
        "HP_ONLY_CANDIDATE_IS_NOT_FINAL_PROGRAMME_ELIGIBILITY",
        "UNRESOLVED_IS_NOT_RETROFIT_REQUIRED",
    )
