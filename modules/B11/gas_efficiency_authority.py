"""B11-P4 gas-appliance efficiency authority and energy-basis gate.

Regulatory/product efficiency metrics are not automatically seasonal fuel-volume
authority. GCV and LHV bases are explicit and may not be mixed silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from .gas_volume_bridge_contract import EvidenceStatus, PhysicalEvidence


class EnergyBasis(str, Enum):
    GCV = "GCV"
    LHV = "LHV"


class EfficiencyMetric(str, Enum):
    EU_SEASONAL_SPACE_HEATING_ETA_S = "EU_SEASONAL_SPACE_HEATING_ETA_S"
    EU_USEFUL_EFFICIENCY = "EU_USEFUL_EFFICIENCY"
    SEASONAL_FUEL_CONVERSION_EFFICIENCY = "SEASONAL_FUEL_CONVERSION_EFFICIENCY"


@dataclass(frozen=True)
class GasEfficiencyEvidence:
    value: float | None
    status: EvidenceStatus
    metric: EfficiencyMetric
    energy_basis: EnergyBasis
    source_ref: str | None = None


@dataclass(frozen=True)
class GasQualityPair:
    gcv_mj_m3: PhysicalEvidence
    lhv_mj_m3: PhysicalEvidence


def _finite_positive(value: float | None, label: str) -> float:
    if value is None or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return float(value)


def authorize_fuel_volume_efficiency(
    evidence: GasEfficiencyEvidence,
    gas_quality: GasQualityPair | None = None,
) -> PhysicalEvidence:
    """Return an LHV-basis seasonal fuel-conversion efficiency for P3.

    EU eta_s and product useful-efficiency points remain evidence but are not
    interchangeable with an in-use seasonal fuel-conversion efficiency.
    """

    if evidence.status == EvidenceStatus.Q:
        raise ValueError("Q efficiency cannot authorize gas-volume derivation")
    if evidence.metric != EfficiencyMetric.SEASONAL_FUEL_CONVERSION_EFFICIENCY:
        raise ValueError("product/regulatory efficiency metric is not fuel-volume authority")

    efficiency = _finite_positive(evidence.value, "efficiency")

    if evidence.energy_basis == EnergyBasis.LHV:
        # LHV-basis condensing efficiencies may legitimately exceed 1.0.
        return PhysicalEvidence(
            value=efficiency,
            unit="fraction_lhv",
            status=evidence.status,
            source_ref=evidence.source_ref,
        )

    if gas_quality is None:
        raise ValueError("GCV-to-LHV conversion requires an explicit gas-quality pair")
    gcv = gas_quality.gcv_mj_m3.numeric("MJ/m3_GCV")
    lhv = gas_quality.lhv_mj_m3.numeric("MJ/m3_LHV")
    if gcv <= lhv:
        raise ValueError("GCV must be greater than LHV for basis conversion")

    lhv_efficiency = efficiency * gcv / lhv
    return PhysicalEvidence(
        value=lhv_efficiency,
        unit="fraction_lhv",
        status=evidence.status if EvidenceStatus.SCN not in {gas_quality.gcv_mj_m3.status, gas_quality.lhv_mj_m3.status} else EvidenceStatus.SCN,
        source_ref=evidence.source_ref,
    )


def eu_eta_s_authorizes_programme_efficiency() -> bool:
    return False


def eu_ecodesign_minimum_authorizes_stock_average() -> bool:
    return False
