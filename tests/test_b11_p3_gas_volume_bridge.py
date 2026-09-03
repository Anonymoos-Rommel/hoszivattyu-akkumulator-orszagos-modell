from modules.B11.gas_volume_bridge_contract import (
    EvidenceStatus,
    GasVolumeBridgeInputs,
    PhysicalEvidence,
    county_utility_volume_can_allocate_archetypes,
    derive_gas_volume,
)


def test_bridge_converts_useful_heat_to_gas_volume():
    result = derive_gas_volume(
        GasVolumeBridgeInputs(
            useful_heat_kwh_year=PhysicalEvidence(9000.0, "kWh/year", EvidenceStatus.DER, "B06"),
            seasonal_appliance_efficiency=PhysicalEvidence(0.9, "fraction", EvidenceStatus.SCN, "fixture"),
            gas_lower_heating_value_mj_m3=PhysicalEvidence(36.0, "MJ/m3", EvidenceStatus.SCN, "fixture"),
        )
    )
    assert round(result.gas_input_energy_kwh_year, 6) == 10000.0
    assert round(result.gas_volume_m3_year, 6) == 1000.0
    assert result.output_status == EvidenceStatus.SCN


def test_q_efficiency_blocks_numeric_output():
    try:
        derive_gas_volume(
            GasVolumeBridgeInputs(
                useful_heat_kwh_year=PhysicalEvidence(9000.0, "kWh/year", EvidenceStatus.DER),
                seasonal_appliance_efficiency=PhysicalEvidence(None, "fraction", EvidenceStatus.Q),
                gas_lower_heating_value_mj_m3=PhysicalEvidence(36.0, "MJ/m3", EvidenceStatus.SCN),
            )
        )
    except ValueError as exc:
        assert "Q evidence" in str(exc)
    else:
        raise AssertionError("Q efficiency must block derivation")


def test_missing_heating_value_is_not_zero():
    try:
        derive_gas_volume(
            GasVolumeBridgeInputs(
                useful_heat_kwh_year=PhysicalEvidence(9000.0, "kWh/year", EvidenceStatus.DER),
                seasonal_appliance_efficiency=PhysicalEvidence(0.9, "fraction", EvidenceStatus.SCN),
                gas_lower_heating_value_mj_m3=PhysicalEvidence(None, "MJ/m3", EvidenceStatus.SCN),
            )
        )
    except ValueError as exc:
        assert "missing/non-finite" in str(exc)
    else:
        raise AssertionError("missing heating value must block derivation")


def test_invalid_efficiency_is_rejected():
    try:
        derive_gas_volume(
            GasVolumeBridgeInputs(
                useful_heat_kwh_year=PhysicalEvidence(9000.0, "kWh/year", EvidenceStatus.DER),
                seasonal_appliance_efficiency=PhysicalEvidence(0.0, "fraction", EvidenceStatus.SCN),
                gas_lower_heating_value_mj_m3=PhysicalEvidence(36.0, "MJ/m3", EvidenceStatus.SCN),
            )
        )
    except ValueError as exc:
        assert "efficiency" in str(exc)
    else:
        raise AssertionError("zero efficiency must be rejected")


def test_county_utility_volume_cannot_allocate_archetypes():
    assert county_utility_volume_can_allocate_archetypes() is False
