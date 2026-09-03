"""Fail-closed B11 physical gas-displacement contract.

B11-P1 deliberately separates observed gas baselines from programme-policy
population targets and from scenario assumptions about replaceable end uses.

Core rule:

    OBSERVED GAS BASELINE != PROGRAMME TARGET != REPLACEABLE GAS FRACTION
    != PHYSICAL GAS DISPLACEMENT != IMPORT VALUE

A numeric displacement may only be calculated from explicit physical inputs.
Missing inputs are not zero and no legacy 2 million household / 3 bcm programme
hypothesis is used as a baseline or calibration target.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class EvidenceStatus(str, Enum):
    OBS = "OBS"
    DER = "DER"
    SCN = "SCN"
    Q = "Q"


_ALLOWED_NUMERIC_STATUSES = {EvidenceStatus.OBS, EvidenceStatus.DER, EvidenceStatus.SCN}


@dataclass(frozen=True)
class EvidenceValue:
    value: float | None
    unit: str
    status: EvidenceStatus
    source_ref: str | None = None

    def numeric(self, *, expected_unit: str) -> float:
        if self.unit != expected_unit:
            raise ValueError(f"expected unit {expected_unit!r}, got {self.unit!r}")
        if self.status not in _ALLOWED_NUMERIC_STATUSES:
            raise ValueError("Q evidence cannot authorize a numeric physical calculation")
        if self.value is None or not math.isfinite(self.value):
            raise ValueError("missing/non-finite evidence is not zero")
        return float(self.value)


@dataclass(frozen=True)
class GasDisplacementInputs:
    baseline_gas_m3: EvidenceValue
    replaceable_end_use_fraction: EvidenceValue
    retrofit_reduction_fraction: EvidenceValue
    rebound_fraction: EvidenceValue


@dataclass(frozen=True)
class GasDisplacementResult:
    post_retrofit_gas_m3: float
    displaced_gas_m3: float
    remaining_gas_m3: float
    output_status: EvidenceStatus


def _fraction(value: EvidenceValue) -> float:
    x = value.numeric(expected_unit="fraction")
    if not 0.0 <= x <= 1.0:
        raise ValueError("fraction evidence must be within [0, 1]")
    return x


def _combined_status(values: tuple[EvidenceValue, ...]) -> EvidenceStatus:
    statuses = {v.status for v in values}
    if EvidenceStatus.Q in statuses:
        return EvidenceStatus.Q
    if EvidenceStatus.SCN in statuses:
        return EvidenceStatus.SCN
    if EvidenceStatus.DER in statuses:
        return EvidenceStatus.DER
    return EvidenceStatus.OBS


def calculate_physical_gas_displacement(inputs: GasDisplacementInputs) -> GasDisplacementResult:
    """Calculate bounded physical gas displacement from explicit evidence.

    Semantics:

    1. Retrofit reduces the explicit baseline gas demand first.
    2. Only the explicit replaceable end-use share may then be displaced.
    3. Rebound restores a bounded fraction of the would-be displaced volume.
    4. Non-replaceable gas demand remains gas demand.

    No household count, policy target, tariff or import price enters this function.
    """

    baseline = inputs.baseline_gas_m3.numeric(expected_unit="m3/year")
    if baseline < 0:
        raise ValueError("baseline gas volume cannot be negative")

    retrofit = _fraction(inputs.retrofit_reduction_fraction)
    replaceable = _fraction(inputs.replaceable_end_use_fraction)
    rebound = _fraction(inputs.rebound_fraction)

    post_retrofit = baseline * (1.0 - retrofit)
    gross_displaceable = post_retrofit * replaceable
    displaced = gross_displaceable * (1.0 - rebound)
    remaining = post_retrofit - displaced

    if displaced < -1e-9 or remaining < -1e-9:
        raise ValueError("physical gas balance became negative")
    if abs((displaced + remaining) - post_retrofit) > 1e-9:
        raise ValueError("physical gas balance is not conserved")

    status = _combined_status(
        (
            inputs.baseline_gas_m3,
            inputs.replaceable_end_use_fraction,
            inputs.retrofit_reduction_fraction,
            inputs.rebound_fraction,
        )
    )

    return GasDisplacementResult(
        post_retrofit_gas_m3=post_retrofit,
        displaced_gas_m3=displaced,
        remaining_gas_m3=remaining,
        output_status=status,
    )
