"""B05-P51 S2125 post-defrost recovery-tail and state-surface contract.

The module exposes only bounded exact-system E2 rules. Raw owner data remain
EXTERNAL_ONLY. No universal full-cycle penalty or cross-product transfer is
authorized here.
"""

from __future__ import annotations

STATE_BINS_HZ = (
    ("LE_30", float("-inf"), 30.0),
    ("GT30_LE40", 30.0, 40.0),
    ("GT40_LE50", 40.0, 50.0),
    ("GT50", 50.0, float("inf")),
)

RECOVERY_CHECKPOINTS_MIN = (0, 5, 10, 15, 20, 30, 45)


def compressor_state_bin(pre_frequency_hz: float) -> str:
    if pre_frequency_hz <= 30.0:
        return "LE_30"
    if pre_frequency_hz <= 40.0:
        return "GT30_LE40"
    if pre_frequency_hz <= 50.0:
        return "GT40_LE50"
    return "GT50"


def p51_boundaries() -> tuple[str, ...]:
    return (
        "ACTIVE_STATE_UPLIFT != FULL_CYCLE_PENALTY",
        "CLEAN_45MIN_COMPLETE_CASE != ALL_DEFROST_EVENTS",
        "SUSTAINED_RECOVERY_OBSERVED_SUBSET != POPULATION_RECOVERY_TIME_DISTRIBUTION",
        "STATE_BIN_SURFACE != CONTINUOUS_PREDICTIVE_FORMULA",
        "ONE_S2125_INSTALLATION != CROSS_PRODUCT_OR_HUNGARIAN_FLEET_PARAMETER",
        "HEAT_DEFROST != DHW_DEFROST",
        "PASSIVE_DEFROST_REMAINS_SEPARATE",
        "NO_MECHANICAL_READINESS_UPLIFT",
    )


def can_admit_full_cycle_constant() -> bool:
    """P51 intentionally does not authorize one full-cycle constant."""
    return False
