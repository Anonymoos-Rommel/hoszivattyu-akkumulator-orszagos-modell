from modules.B11.gas_efficiency_authority import (
    EfficiencyMetric,
    EnergyBasis,
    GasEfficiencyEvidence,
    GasQualityPair,
    authorize_fuel_volume_efficiency,
    eu_ecodesign_minimum_authorizes_stock_average,
    eu_eta_s_authorizes_programme_efficiency,
)
from modules.B11.gas_volume_bridge_contract import EvidenceStatus, PhysicalEvidence


def test_eu_eta_s_is_not_direct_fuel_volume_authority():
    try:
        authorize_fuel_volume_efficiency(
            GasEfficiencyEvidence(
                0.92,
                EvidenceStatus.OBS,
                EfficiencyMetric.EU_SEASONAL_SPACE_HEATING_ETA_S,
                EnergyBasis.GCV,
                "EU-811-813",
            )
        )
    except ValueError as exc:
        assert "not fuel-volume authority" in str(exc)
    else:
        raise AssertionError("eta_s must not authorize gas-volume derivation")


def test_gcv_seasonal_fuel_efficiency_requires_quality_pair():
    evidence = GasEfficiencyEvidence(
        0.90,
        EvidenceStatus.DER,
        EfficiencyMetric.SEASONAL_FUEL_CONVERSION_EFFICIENCY,
        EnergyBasis.GCV,
        "calibration",
    )
    try:
        authorize_fuel_volume_efficiency(evidence)
    except ValueError as exc:
        assert "gas-quality pair" in str(exc)
    else:
        raise AssertionError("basis conversion must fail closed")


def test_gcv_to_lhv_conversion_can_exceed_one_without_error():
    normalized = authorize_fuel_volume_efficiency(
        GasEfficiencyEvidence(
            0.95,
            EvidenceStatus.SCN,
            EfficiencyMetric.SEASONAL_FUEL_CONVERSION_EFFICIENCY,
            EnergyBasis.GCV,
            "fixture",
        ),
        GasQualityPair(
            PhysicalEvidence(39.5, "MJ/m3_GCV", EvidenceStatus.SCN, "fixture"),
            PhysicalEvidence(35.5, "MJ/m3_LHV", EvidenceStatus.SCN, "fixture"),
        ),
    )
    assert normalized.unit == "fraction_lhv"
    assert normalized.value > 1.0
    assert normalized.status == EvidenceStatus.SCN


def test_ecodesign_floor_is_not_hungarian_stock_average():
    assert eu_ecodesign_minimum_authorizes_stock_average() is False
    assert eu_eta_s_authorizes_programme_efficiency() is False
