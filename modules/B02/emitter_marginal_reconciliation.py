"""B02-P30 bounded gas-convector marginal reconciliation.

This module does not promote a heat emitter to OBS/DER and does not materialize
an emitter WBL surface.  It tests whether the current TARKI-REKK gas-convector
control can be reconciled to the exact KSH WBL gas-heating universe under a
strict room-heating structural domain.

Canonical boundaries:

* GAS-HEATING MARGIN != GAS-CONVECTOR CELL ASSIGNMENT
* ROOM-HEATING GAS DOMAIN != OBSERVED GAS-CONVECTOR DOMAIN
* EXACT MARGINAL RECONCILIATION != INDEPENDENCE CONTROL
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


SURVEY_PRIMARY_GAS_SHARE = 0.5489
SURVEY_SECONDARY_GAS_SHARE = 0.0698
SURVEY_GAS_AT_LEAST_PARTLY_SHARE = SURVEY_PRIMARY_GAS_SHARE + SURVEY_SECONDARY_GAS_SHARE
SURVEY_CONVECTOR_WITHIN_GAS_SHARE = 0.4061

# WBL011 source-native heating-fuel categories containing network gas.
GAS_FUEL_CODES = frozenset({"FUEL11", "FUEL21", "FUEL22"})
ROOM_HEATING_CODE = "NHEAT"


@dataclass(frozen=True)
class MarginalReconciliationResult:
    occupied_dwellings: int
    wbl_gas_heating_dwellings: int
    wbl_room_gas_dwellings: int
    wbl_gas_share: float
    survey_gas_share: float
    gas_share_delta_pp: float
    target_convector_dwellings: float
    room_gas_probability: float | None
    marginal_residual_dwellings: float | None
    marginal_reconciled: bool
    blocker: str | None


def reconcile_gas_convector_margin(path: Path) -> MarginalReconciliationResult:
    occupied = 0
    gas = 0
    room_gas = 0

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"heating_mode_code", "heating_fuel_code", "dwellings"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError("WBL joint is missing required heating fields")

        for row in reader:
            dwellings = int(row["dwellings"])
            if dwellings < 0:
                raise ValueError("negative dwelling count")
            occupied += dwellings
            is_gas = row["heating_fuel_code"] in GAS_FUEL_CODES
            if is_gas:
                gas += dwellings
                if row["heating_mode_code"] == ROOM_HEATING_CODE:
                    room_gas += dwellings

    if occupied <= 0 or gas <= 0 or room_gas <= 0:
        return MarginalReconciliationResult(
            occupied,
            gas,
            room_gas,
            0.0 if occupied <= 0 else gas / occupied,
            SURVEY_GAS_AT_LEAST_PARTLY_SHARE,
            0.0 if occupied <= 0 else (gas / occupied - SURVEY_GAS_AT_LEAST_PARTLY_SHARE) * 100.0,
            gas * SURVEY_CONVECTOR_WITHIN_GAS_SHARE,
            None,
            None,
            False,
            "EMPTY_REQUIRED_WBL_DOMAIN",
        )

    wbl_gas_share = gas / occupied
    target_convector = gas * SURVEY_CONVECTOR_WITHIN_GAS_SHARE
    p_room_gas = target_convector / room_gas

    # A probability above one proves the proposed topology-bounded domain is
    # too small and therefore fails closed instead of leaking convectors into
    # central-heating cells.
    if not 0.0 <= p_room_gas <= 1.0:
        return MarginalReconciliationResult(
            occupied,
            gas,
            room_gas,
            wbl_gas_share,
            SURVEY_GAS_AT_LEAST_PARTLY_SHARE,
            (wbl_gas_share - SURVEY_GAS_AT_LEAST_PARTLY_SHARE) * 100.0,
            target_convector,
            p_room_gas,
            None,
            False,
            "ROOM_GAS_DOMAIN_TOO_SMALL",
        )

    residual = room_gas * p_room_gas - target_convector
    return MarginalReconciliationResult(
        occupied,
        gas,
        room_gas,
        wbl_gas_share,
        SURVEY_GAS_AT_LEAST_PARTLY_SHARE,
        (wbl_gas_share - SURVEY_GAS_AT_LEAST_PARTLY_SHARE) * 100.0,
        target_convector,
        p_room_gas,
        residual,
        abs(residual) <= 1e-9,
        None if abs(residual) <= 1e-9 else "NONZERO_MARGINAL_RESIDUAL",
    )
