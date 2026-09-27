"""B05-P52 S2125 passive-defrost branch admission contract.

This module deliberately does not contain numeric passive-event penalty results.
The P49 owner raw package is EXTERNAL_ONLY. Numeric P52 results may be admitted
only after the exact pinned raw identities are re-materialized and re-analysed.

Known canonical observations inherited from P49:
- direct Defrost=2 samples: 102
- contiguous passive state runs: 22
- median source-sampled state-run duration: 180.5 s

These observations identify the branch but do not establish a causal passive
defrost energy penalty.
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
    """Fail-closed admission for a passive-state matched electrical comparison."""

    mode: str
    n_controls: int
    electrical_coverage_fraction: float
    control_has_nonzero_defrost: bool
    stable_control_mode: bool
    event_is_direct_passive_state: bool

    def admitted(self) -> bool:
        return (
            self.mode in {"HEAT", "DHW"}
            and self.n_controls >= 3
            and self.electrical_coverage_fraction >= 0.98
            and not self.control_has_nonzero_defrost
            and self.stable_control_mode
            and self.event_is_direct_passive_state
        )


def passive_signed_thermal_der_admitted(
    *,
    p50_factor_domain_validated_for_passive: bool,
    flow_and_temperatures_qualified: bool,
) -> bool:
    """P50's HEAT calibration is not automatically transferable to Defrost=2.

    Passive defrost is compressor-off/fan-on under the manufacturer controller
    semantics. Therefore the P50 signed-thermal factor may be used only after
    an explicit passive-domain validation and qualified BF1/BT12/BT3 evidence.
    """

    return (
        p50_factor_domain_validated_for_passive
        and flow_and_temperatures_qualified
    )


def can_admit_passive_penalty_constant() -> bool:
    """P52 preparation does not authorize a universal passive penalty."""

    return False


def p52_boundaries() -> tuple[str, ...]:
    return (
        "PASSIVE_DEFROST != ACTIVE_REVERSE_CYCLE_DEFROST",
        "PASSIVE_STATE_WINDOW_ENERGY != PASSIVE_DEFROST_PENALTY",
        "P50_SIGNED_THERMAL_FACTOR != PASSIVE_THERMAL_DER_WITHOUT_DOMAIN_VALIDATION",
        "22_OBSERVED_PASSIVE_RUNS != POPULATION_PASSIVE_DEFROST_FREQUENCY",
        "EXACT_P49_RAW_IDENTITY_REQUIRED_FOR_NUMERIC_REDERIVATION",
        "ONE_S2125_INSTALLATION != CROSS_PRODUCT_OR_HUNGARIAN_FLEET_PARAMETER",
        "NO_MECHANICAL_READINESS_UPLIFT",
    )
