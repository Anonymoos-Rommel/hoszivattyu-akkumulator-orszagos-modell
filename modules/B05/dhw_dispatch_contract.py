"""B05-P29 controller-bound domestic-hot-water dispatch contract.

Controller scheduling evidence is kept separate from high-temperature
heat-pump performance evidence.  The generic B05 engine remains fail-closed
unless the required controller identity and runtime state are explicit.
"""

from __future__ import annotations

from dataclasses import dataclass

MITSUBISHI_WM50_FTC6 = "MITSUBISHI_PUZ_WM50VHA_FTC6"
DIMPLEX_LA2030CP_WPM_TOUCH = "DIMPLEX_LA2030CP_WPM_TOUCH"

Q_UNKNOWN_CONTROLLER = "Q_UNKNOWN_PRODUCT_CONTROLLER"
Q_MITSUBISHI_SIMULTANEOUS_SETTING = "Q_MITSUBISHI_SIMULTANEOUS_SETTING_REQUIRED"
Q_MITSUBISHI_PRE_TIMEOUT_STATE = "Q_MITSUBISHI_PRE_TIMEOUT_DHW_STATE_REQUIRED"
Q_SIMULTANEOUS_THERMAL_SPLIT = "Q_SIMULTANEOUS_THERMAL_SPLIT_UNPROVEN"


@dataclass(frozen=True)
class ControllerPolicy:
    controller_id: str
    product_binding: str
    source_ids: tuple[str, ...]
    simultaneous_semantics: str
    dhw_priority_semantics: str
    high_temp_performance_status: str = "Q"


@dataclass(frozen=True)
class DispatchDecision:
    status: str
    active_mode: str | None
    evidence_status: str
    reason: str
    requires_high_temp_performance: bool
    energy_allocation_ready: bool


_POLICIES = {
    MITSUBISHI_WM50_FTC6: ControllerPolicy(
        controller_id=MITSUBISHI_WM50_FTC6,
        product_binding="PUZ-WM50VHA(-BS)+EHPT20X-MHEDW/FTC6",
        source_ids=(
            "SRC-B05-MITSUBISHI-WM50-FTC6-DHW-CONTROL-2026",
            "SRC-B05-MITSUBISHI-WM50-FTC6-BINDING-2026",
        ),
        simultaneous_semantics="CONFIGURABLE_ON_OFF_DEFAULT_OFF",
        dhw_priority_semantics="SPACE_HEATING_PRIORITY_DURING_POST_DHW_RESTRICTION_AFTER_MAX_DHW_TIME",
    ),
    DIMPLEX_LA2030CP_WPM_TOUCH: ControllerPolicy(
        controller_id=DIMPLEX_LA2030CP_WPM_TOUCH,
        product_binding="LA2030CP+WPM_TOUCH",
        source_ids=(
            "SRC-B05-DIMPLEX-LA2030CP-WPMTOUCH-BINDING-2026",
            "SRC-B05-DIMPLEX-WPMTOUCH-DHW-CONTROL-2026",
        ),
        simultaneous_semantics="DHW_REQUEST_SWITCHES_CIRCULATION_AWAY_FROM_SPACE_HEATING",
        dhw_priority_semantics="DHW_REQUEST_PREEMPTS_SPACE_HEATING_CIRCULATION",
    ),
}


def resolve_controller_policy(controller_id: str) -> ControllerPolicy | None:
    """Return only exact product/controller policies admitted by P29."""
    return _POLICIES.get(controller_id)


def classify_simultaneous_dispatch(
    controller_id: str,
    *,
    space_heating_request: bool,
    dhw_request: bool,
    mitsubishi_simultaneous_operation_enabled: bool | None = None,
    mitsubishi_post_dhw_restriction_active: bool | None = None,
) -> DispatchDecision:
    """Classify simultaneous space/DHW requests without inventing allocation.

    This function resolves only source-supported controller behavior.  It does
    not calculate heat, electricity or COP.  Any DHW-active result still
    requires product-specific performance evidence at the dispatched
    temperature before B05 may calculate energy.
    """

    policy = resolve_controller_policy(controller_id)
    if policy is None:
        return DispatchDecision(
            Q_UNKNOWN_CONTROLLER,
            None,
            "Q",
            "No exact product/controller policy is admitted for this controller identity.",
            bool(dhw_request),
            False,
        )

    if not space_heating_request and not dhw_request:
        return DispatchDecision("QUALIFIED_NO_REQUEST", "IDLE", "DER", "No heat request is present.", False, True)
    if space_heating_request and not dhw_request:
        return DispatchDecision("QUALIFIED_SPACE_HEATING_ONLY", "SPACE_HEATING", "DER", "Only space heating is requested.", False, True)
    if dhw_request and not space_heating_request:
        return DispatchDecision(
            "QUALIFIED_DHW_ONLY_REQUEST",
            "DHW",
            "DER",
            "Only DHW is requested; energy evaluation still requires DHW-temperature performance evidence.",
            True,
            False,
        )

    if controller_id == DIMPLEX_LA2030CP_WPM_TOUCH:
        return DispatchDecision(
            "QUALIFIED_DHW_PRIORITY_PREEMPTS_SPACE_HEATING_CIRCULATION",
            "DHW",
            "OBS",
            "WPM Touch deactivates the heat circulating pump and activates the DHW circulating pump when a DHW request occurs during heating.",
            True,
            False,
        )

    if mitsubishi_simultaneous_operation_enabled is None:
        return DispatchDecision(
            Q_MITSUBISHI_SIMULTANEOUS_SETTING,
            None,
            "Q",
            "FTC6 simultaneous DHW/heating is configurable and the actual setting is required.",
            True,
            False,
        )

    if mitsubishi_simultaneous_operation_enabled:
        return DispatchDecision(
            Q_SIMULTANEOUS_THERMAL_SPLIT,
            "SIMULTANEOUS_CONFIGURED",
            "Q",
            "FTC6 permits the simultaneous controller mode, but P29 has no authoritative thermal split or DHW-temperature performance allocation.",
            True,
            False,
        )

    if mitsubishi_post_dhw_restriction_active is None:
        return DispatchDecision(
            Q_MITSUBISHI_PRE_TIMEOUT_STATE,
            None,
            "Q",
            "With simultaneous operation disabled, P29 requires explicit state identifying whether the source-defined post-DHW heating-priority restriction is active.",
            True,
            False,
        )

    if mitsubishi_post_dhw_restriction_active:
        return DispatchDecision(
            "QUALIFIED_SPACE_HEATING_PRIORITY_POST_DHW_RESTRICTION",
            "SPACE_HEATING",
            "OBS",
            "FTC6 documents a post-DHW restriction interval in which space heating has priority after maximum DHW operation time has passed.",
            False,
            True,
        )

    return DispatchDecision(
        Q_MITSUBISHI_PRE_TIMEOUT_STATE,
        None,
        "Q",
        "P29 does not infer the pre-timeout dispatch ordering from the post-timeout restriction rule.",
        True,
        False,
    )


def p29_boundary() -> str:
    return (
        "CONTROLLER_DISPATCH_EVIDENCE != HIGH_TEMPERATURE_CAPABILITY != HIGH_TEMPERATURE_CAPACITY_COP_EVIDENCE; "
        "PRODUCT_CONTROLLER_POLICY != GENERIC_CROSS_PRODUCT_POLICY"
    )
