"""B11-P4 gas-appliance efficiency authority and energy-basis gate.

Regulatory/product efficiency metrics are not automatically seasonal fuel-volume
authority. GCV and LHV bases are explicit and may not be mixed silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real

from .gas_reference_contract import CalorificBasis

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
    calorific_basis: CalorificBasis | None = None


@dataclass(frozen=True)
class GasQualityPair:
    gcv_mj_m3: PhysicalEvidence
    lhv_mj_m3: PhysicalEvidence

    def validated_values(self) -> tuple[float, float]:
        """Return values only for the same volume state and gas-quality context.

        GCV/LHV may have distinct calorific temperatures: each side retains its
        convention, and an efficiency must match the side it was measured on.
        This is not an implicit volume-state or calorimetric normalization.
        """
        gcv = self.gcv_mj_m3.numeric("MJ/m3_GCV")
        lhv = self.lhv_mj_m3.numeric("MJ/m3_LHV")
        _finite_positive(gcv, "GCV")
        _finite_positive(lhv, "LHV")
        if self.gcv_mj_m3.reference_state != self.lhv_mj_m3.reference_state:
            raise ValueError("GCV and LHV gas volume reference states do not match")
        if self.gcv_mj_m3.calorific_basis.gas_quality_context_id != self.lhv_mj_m3.calorific_basis.gas_quality_context_id:
            raise ValueError("GCV and LHV gas-quality contexts do not match")
        if gcv <= lhv:
            raise ValueError("GCV must be greater than LHV for basis conversion")
        return gcv, lhv


def _finite_positive(value: float | None, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value <= 0:
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

    if evidence.status not in {EvidenceStatus.OBS, EvidenceStatus.DER, EvidenceStatus.SCN}:
        raise ValueError("Q/unsupported efficiency status cannot authorize gas-volume derivation")
    if evidence.metric != EfficiencyMetric.SEASONAL_FUEL_CONVERSION_EFFICIENCY:
        raise ValueError("product/regulatory efficiency metric is not fuel-volume authority")

    efficiency = _finite_positive(evidence.value, "efficiency")
    if not isinstance(evidence.calorific_basis, CalorificBasis):
        raise ValueError("explicit efficiency calorific reference and gas-quality context are required")
    if evidence.energy_basis not in {EnergyBasis.GCV, EnergyBasis.LHV}:
        raise ValueError("explicit supported efficiency energy basis is required")

    if evidence.energy_basis == EnergyBasis.LHV:
        # LHV-basis condensing efficiencies may legitimately exceed 1.0.
        return PhysicalEvidence(
            value=efficiency,
            unit="fraction_lhv",
            status=evidence.status,
            source_ref=evidence.source_ref,
            calorific_basis=evidence.calorific_basis,
        )

    if gas_quality is None:
        raise ValueError("GCV-to-LHV conversion requires an explicit gas-quality pair")
    gcv, lhv = gas_quality.validated_values()
    if evidence.calorific_basis != gas_quality.gcv_mj_m3.calorific_basis:
        raise ValueError("efficiency and GCV calorific reference / gas-quality context do not match")

    lhv_efficiency = _finite_positive(efficiency * (gcv / lhv), "derived LHV efficiency")
    return PhysicalEvidence(
        value=lhv_efficiency,
        unit="fraction_lhv",
        status=EvidenceStatus.SCN if EvidenceStatus.SCN in {
            evidence.status, gas_quality.gcv_mj_m3.status, gas_quality.lhv_mj_m3.status
        } else EvidenceStatus.DER,
        source_ref=evidence.source_ref,
        calorific_basis=gas_quality.lhv_mj_m3.calorific_basis,
    )


def eu_eta_s_authorizes_programme_efficiency() -> bool:
    return False


def eu_ecodesign_minimum_authorizes_stock_average() -> bool:
    return False
