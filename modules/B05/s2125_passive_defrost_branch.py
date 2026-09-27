"""B05-P52 S2125 passive-defrost branch contract.

Raw owner data remain EXTERNAL_ONLY. This module freezes only the bounded
admission rules and exact aggregate identities derived from the pinned P49
package.
"""

from __future__ import annotations

from dataclasses import dataclass

PINNED_ARCHIVE_SHA256 = (
    "01736c38535b25030800bd2fba12a54f5ddc676304c3458573be1950e8664d92"
)
PINNED_NIBE_MEMBER_SHA256 = (
    "ca79f165777f3626d68def05fda3331678bc73fa29371e74a2530ccc4d850440"
)
PINNED_VICTRON_MEMBER_SHA256 = (
    "a3b6e88a9e2783c35511096192aee1a5aef58b57a9a1b40c9a1eff93e55a4456"
)

EXPECTED_PASSIVE_STATE_SAMPLES = 102
EXPECTED_PASSIVE_STATE_RUNS = 22
EXPECTED_PASSIVE_MEDIAN_DURATION_S = 180.5
PASSIVE_HEAT_RUNS = 9
PASSIVE_DHW_RUNS = 11
PASSIVE_TRANSITION_RUNS = 2
PASSIVE_MEDIAN_MEASURED_COVERED_ENERGY_KWH = 0.004854669
PASSIVE_MEDIAN_ELECTRICAL_COVERAGE_PERCENT = 94.9480
PASSIVE_MEDIAN_MEASURED_INTERVAL_POWER_W = 80.640888
PASSIVE_MIN_NEXT_COMPRESSOR_GAP_MIN = 14.0
PASSIVE_HEAT_EVENTS_WITH_STRICT_MATCH_SUPPORT = 5
PASSIVE_DHW_EVENTS_WITH_STRICT_MATCH_SUPPORT = 0


def raw_identity_admitted(
    archive_sha256: str,
    nibe_member_sha256: str,
    victron_member_sha256: str,
) -> bool:
    """Return True only for the exact P49 external raw package."""

    return (
        archive_sha256 == PINNED_ARCHIVE_SHA256
        and nibe_member_sha256 == PINNED_NIBE_MEMBER_SHA256
        and victron_member_sha256 == PINNED_VICTRON_MEMBER_SHA256
    )


@dataclass(frozen=True)
class PassiveElectricMatchAdmission:
    """Fail-closed admission for one passive-state matched comparison."""

    mode: str
    n_controls: int
    electrical_coverage_fraction: float
    control_has_nonzero_defrost: bool
    control_compressor_off: bool
    stable_control_mode: bool
    event_is_direct_passive_state: bool

    def admitted(self) -> bool:
        return (
            self.mode in {"HEAT", "DHW"}
            and self.n_controls >= 3
            and self.electrical_coverage_fraction >= 0.98
            and not self.control_has_nonzero_defrost
            and self.control_compressor_off
            and self.stable_control_mode
            and self.event_is_direct_passive_state
        )


def passive_branch_matched_parameter_admitted(
    *,
    heat_events_supported: int,
    heat_events_total: int,
    dhw_events_supported: int,
    dhw_events_total: int,
) -> bool:
    """Require material strict support in both principal modes.

    P52 intentionally fails this gate: 5/9 HEAT and 0/11 DHW events have at
    least three strict compressor-off controls.
    """

    return (
        heat_events_total > 0
        and dhw_events_total > 0
        and heat_events_supported == heat_events_total
        and dhw_events_supported == dhw_events_total
    )


def passive_signed_thermal_der_admitted(
    *,
    p50_factor_domain_validated_for_passive: bool,
    flow_and_temperatures_qualified: bool,
) -> bool:
    """Do not transfer P50's active-HEAT factor into passive operation."""

    return (
        p50_factor_domain_validated_for_passive
        and flow_and_temperatures_qualified
    )


def can_admit_passive_penalty_constant() -> bool:
    """P52 does not authorize one universal passive penalty."""

    return False


def p52_boundaries() -> tuple[str, ...]:
    return (
        "PASSIVE_DEFROST != ACTIVE_REVERSE_CYCLE_DEFROST",
        "PASSIVE_STATE_WINDOW_ENERGY != PASSIVE_INCREMENTAL_PENALTY",
        "ZERO_COMPRESSOR_REQUEST_DURING_PASSIVE != ZERO_BUILDING_THERMAL_COST",
        "P50_SIGNED_THERMAL_FACTOR != PASSIVE_THERMAL_DER_WITHOUT_DOMAIN_VALIDATION",
        "22_OBSERVED_PASSIVE_RUNS != POPULATION_PASSIVE_DEFROST_FREQUENCY",
        "ONE_S2125_INSTALLATION != CROSS_PRODUCT_OR_HUNGARIAN_FLEET_PARAMETER",
        "NO_MECHANICAL_READINESS_UPLIFT",
    )
