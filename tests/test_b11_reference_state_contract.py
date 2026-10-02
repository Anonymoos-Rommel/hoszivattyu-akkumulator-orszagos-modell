"""Synthetic reference-state and provenance tests; no FGSZ numeric fixtures."""
from dataclasses import FrozenInstanceError, replace
from datetime import date
import unittest

from modules.B11.gas_reference_contract import CalorificBasis, GasReferenceState, MoistureBasis
from modules.B11.gas_volume_bridge_contract import (
    EvidenceStatus, PhysicalEvidence, GasVolumeBridgeInputs, derive_gas_volume,
)
from modules.B11.gas_efficiency_authority import (
    EnergyBasis, EfficiencyMetric, GasEfficiencyEvidence, GasQualityPair,
    authorize_fuel_volume_efficiency,
)
from modules.B11.gas_quality_snapshot_contract import (
    GasQualitySnapshot, ParticipantGasPointMapping, MappingStatus,
    authorize_programme_gas_quality,
)

STATE = GasReferenceState(15, 100000, MoistureBasis.DRY)
GCV_BASIS = CalorificBasis(25, 'SYNTHETIC_POPULATION_2025')
LHV_BASIS = CalorificBasis(15, 'SYNTHETIC_POPULATION_2025')


def gas(value, unit, basis, *, status=EvidenceStatus.SCN, state=STATE, source='synthetic'):
    return PhysicalEvidence(value, unit, status, source, state, basis)


def pair(status=EvidenceStatus.SCN):
    return GasQualityPair(gas(40, 'MJ/m3_GCV', GCV_BASIS, status=status),
                          gas(35, 'MJ/m3_LHV', LHV_BASIS, status=status))


def efficiency(*, status=EvidenceStatus.SCN, basis=GCV_BASIS, energy=EnergyBasis.GCV):
    return GasEfficiencyEvidence(.9, status, EfficiencyMetric.SEASONAL_FUEL_CONVERSION_EFFICIENCY,
                                 energy, 'synthetic', basis)


def bridge(*, status=EvidenceStatus.SCN, state=STATE):
    return GasVolumeBridgeInputs(
        PhysicalEvidence(9000, 'kWh/year', status, 'synthetic'),
        PhysicalEvidence(.9, 'fraction_lhv', status, 'synthetic', calorific_basis=LHV_BASIS),
        gas(36, 'MJ/m3_LHV', LHV_BASIS, status=status, state=state),
    )


class ReferenceStateContractTests(unittest.TestCase):
    def test_missing_volume_and_calorific_metadata_fail_closed(self):
        for evidence in (
            PhysicalEvidence(40, 'MJ/m3_GCV', EvidenceStatus.SCN, 'synthetic'),
            gas(40, 'MJ/m3_GCV', None),
            gas(40, 'MJ/m3_GCV', GCV_BASIS, state=None),
        ):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                evidence.numeric('MJ/m3_GCV')

    def test_mixed_volume_temperature_pressure_and_moisture_fail(self):
        for state in (replace(STATE, volume_reference_temperature_c=0),
                      replace(STATE, reference_pressure_pa=110000),
                      replace(STATE, moisture_basis=MoistureBasis.WATER_SATURATED)):
            p=pair();p=replace(p, lhv_mj_m3=replace(p.lhv_mj_m3, reference_state=state))
            with self.subTest(state=state), self.assertRaisesRegex(ValueError, 'volume reference'):
                authorize_fuel_volume_efficiency(efficiency(),p)

    def test_same_source_url_does_not_establish_same_gas(self):
        p=pair();p=replace(p,lhv_mj_m3=replace(p.lhv_mj_m3,
            calorific_basis=CalorificBasis(15,'SYNTHETIC_OTHER_POPULATION')))
        self.assertEqual(p.gcv_mj_m3.source_ref,p.lhv_mj_m3.source_ref)
        with self.assertRaisesRegex(ValueError,'gas-quality contexts'):
            authorize_fuel_volume_efficiency(efficiency(),p)

    def test_explicit_distinct_calorific_temperatures_are_preserved(self):
        result=authorize_fuel_volume_efficiency(efficiency(),pair())
        self.assertAlmostEqual(result.value,.9*40/35)
        self.assertEqual(result.calorific_basis,LHV_BASIS)
        self.assertIsNone(result.reference_state)
        self.assertEqual(result.status,EvidenceStatus.SCN)

    def test_efficiency_must_match_gcv_calorific_temperature_and_context(self):
        for basis in (CalorificBasis(20,GCV_BASIS.gas_quality_context_id),
                      CalorificBasis(25,'OTHER'),None):
            with self.subTest(basis=basis),self.assertRaises(ValueError):
                authorize_fuel_volume_efficiency(efficiency(basis=basis),pair())

    def test_derived_efficiency_never_promotes_observed_inputs_to_obs(self):
        r=authorize_fuel_volume_efficiency(efficiency(status=EvidenceStatus.OBS),pair(EvidenceStatus.OBS))
        self.assertEqual(r.status,EvidenceStatus.DER)
        for field in ('gcv_mj_m3','lhv_mj_m3'):
            p=pair(EvidenceStatus.OBS);p=replace(p,**{field:replace(getattr(p,field),status=EvidenceStatus.SCN)})
            self.assertEqual(authorize_fuel_volume_efficiency(efficiency(status=EvidenceStatus.OBS),p).status,EvidenceStatus.SCN)

    def test_direct_lhv_retains_basis_without_volume_state(self):
        r=authorize_fuel_volume_efficiency(efficiency(status=EvidenceStatus.OBS,basis=LHV_BASIS,energy=EnergyBasis.LHV))
        self.assertEqual(r.status,EvidenceStatus.OBS)
        self.assertEqual(r.calorific_basis,LHV_BASIS)
        self.assertIsNone(r.reference_state)

    def test_unknown_energy_basis_and_metric_rejected(self):
        for e in (replace(efficiency(),energy_basis='UNKNOWN'),
                  replace(efficiency(),metric=EfficiencyMetric.EU_USEFUL_EFFICIENCY),
                  replace(efficiency(),status=EvidenceStatus.Q)):
            with self.subTest(e=e),self.assertRaises(ValueError):authorize_fuel_volume_efficiency(e,pair())

    def test_volume_output_names_its_reference_state(self):
        result=derive_gas_volume(bridge(status=EvidenceStatus.OBS))
        self.assertAlmostEqual(result.gas_volume_m3_year,1000)
        self.assertEqual(result.reference_state,STATE)
        self.assertEqual(result.calorific_basis,LHV_BASIS)
        self.assertEqual(result.output_status,EvidenceStatus.DER)

    def test_efficiency_has_no_false_volume_temperature_dependency(self):
        # Dimensionless LHV efficiency depends on calorific context, not a cubic
        # metre. Two explicitly supplied per-volume observations retain their
        # own state; this test does not infer a physical state conversion.
        for state in (STATE,replace(STATE,volume_reference_temperature_c=0)):
            r=derive_gas_volume(bridge(state=state))
            self.assertEqual(r.reference_state,state)
            self.assertEqual(r.calorific_basis,LHV_BASIS)

    def test_lhv_bridge_requires_matching_calorific_context(self):
        for basis in (None,CalorificBasis(20,LHV_BASIS.gas_quality_context_id),CalorificBasis(15,'OTHER')):
            inputs=bridge();inputs=replace(inputs,seasonal_appliance_efficiency=replace(inputs.seasonal_appliance_efficiency,calorific_basis=basis))
            with self.subTest(basis=basis),self.assertRaises(ValueError):derive_gas_volume(inputs)

    def test_invalid_reference_state_values_are_rejected(self):
        for value in (True,None,float('nan'),float('inf'),-273.15,-300):
            with self.subTest(temperature=value),self.assertRaises(ValueError):GasReferenceState(value,100000,MoistureBasis.DRY)
            with self.subTest(calorific=value),self.assertRaises(ValueError):CalorificBasis(value,'synthetic')
        for value in (True,None,float('nan'),float('inf'),0,-1):
            with self.subTest(pressure=value),self.assertRaises(ValueError):GasReferenceState(15,value,MoistureBasis.DRY)
        for moisture in (None,'DRY','UNKNOWN'):
            with self.subTest(moisture=moisture),self.assertRaises(ValueError):GasReferenceState(15,100000,moisture)
        for context in (None,'','  ',123):
            with self.subTest(context=context),self.assertRaises(ValueError):CalorificBasis(15,context)

    def test_nonfinite_bool_and_invalid_numeric_values_are_rejected(self):
        for value in (True,None,float('nan'),float('inf'),0,-1):
            with self.subTest(efficiency=value),self.assertRaises(ValueError):
                authorize_fuel_volume_efficiency(replace(efficiency(),value=value),pair())
        for value in (True,None,float('nan'),float('inf'),0,-1):
            p=pair();p=replace(p,lhv_mj_m3=replace(p.lhv_mj_m3,value=value))
            with self.subTest(lhv=value),self.assertRaises(ValueError):p.validated_values()

    def test_overflow_and_q_cannot_become_numeric_volume(self):
        for heat,eta,lhv in [(1e308,1e-308,36),(9000,.9,1e-323)]:
            b=bridge();b=replace(b,useful_heat_kwh_year=replace(b.useful_heat_kwh_year,value=heat),
                seasonal_appliance_efficiency=replace(b.seasonal_appliance_efficiency,value=eta),
                gas_lower_heating_value_mj_m3=replace(b.gas_lower_heating_value_mj_m3,value=lhv))
            with self.subTest(heat=heat,eta=eta,lhv=lhv),self.assertRaises(ValueError):derive_gas_volume(b)
        b=bridge();b=replace(b,gas_lower_heating_value_mj_m3=replace(b.gas_lower_heating_value_mj_m3,status=EvidenceStatus.Q))
        with self.assertRaises(ValueError):derive_gas_volume(b)

    def test_snapshot_preserves_each_status_basis_state_and_lineage(self):
        p=pair(EvidenceStatus.OBS);p=replace(p,lhv_mj_m3=replace(p.lhv_mj_m3,status=EvidenceStatus.DER,source_ref='synthetic-lhv'))
        s=GasQualitySnapshot('POINT-A',date(2025,1,1),date(2025,12,31),p.gcv_mj_m3,p.lhv_mj_m3,'synthetic-snapshot','2025',False)
        m=ParticipantGasPointMapping('PARTICIPANT-A','POINT-A',MappingStatus.EXACT,'synthetic-map')
        r=authorize_programme_gas_quality(s,m,date(2025,1,1),date(2025,12,31))
        self.assertEqual(r,p)
        self.assertEqual(r.gcv_mj_m3.status,EvidenceStatus.OBS)
        self.assertEqual(r.lhv_mj_m3.status,EvidenceStatus.DER)
        self.assertEqual(r.lhv_mj_m3.source_ref,'synthetic-lhv')

    def test_snapshot_cannot_strip_a_mismatched_state(self):
        p=pair();p=replace(p,lhv_mj_m3=replace(p.lhv_mj_m3,reference_state=replace(STATE,volume_reference_temperature_c=0)))
        s=GasQualitySnapshot('POINT-A',date(2025,1,1),date(2025,12,31),p.gcv_mj_m3,p.lhv_mj_m3,'synthetic','2025',False)
        m=ParticipantGasPointMapping('PARTICIPANT-A','POINT-A',MappingStatus.EXACT,'synthetic')
        with self.assertRaisesRegex(ValueError,'volume reference'):
            authorize_programme_gas_quality(s,m,date(2025,1,1),date(2025,12,31))

    def test_reference_metadata_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):STATE.reference_pressure_pa=120000
        with self.assertRaises(FrozenInstanceError):LHV_BASIS.gas_quality_context_id='OTHER'


if __name__ == '__main__':
    unittest.main()
