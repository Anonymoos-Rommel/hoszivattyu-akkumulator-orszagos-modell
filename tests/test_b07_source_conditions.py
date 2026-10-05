"""Qualified source conditions; no temperature-dependent performance model."""
from dataclasses import replace
import hashlib
import json
import unittest

from modules.B07 import discharge_equivalent_reference as m
from modules.B07.sax_source_reference import source_controls


class SourceConditionTests(unittest.TestCase):
    def reference(self):
        return m.source_reference(discharge_curve_id='BAT2AC_STANDARD',reserve_dc_output_equiv_kwh=0.)

    def active(self,ref=None):
        return m.run(ref or self.reference(),initial_dc_output_equiv_kwh=1.,
                     commands=[dict(charge_ac_kw=0.,discharge_ac_kw=1.,hours=.1)])

    def test_permitted_temperature_is_a_specification_not_lab_observation(self):
        c=source_controls()['source_conditions'];t=c['permitted_operation_temperature']
        self.assertEqual((t['min_c'],t['max_c']),(5,35))
        self.assertEqual(t['applies_to'],['battery','inverter'])
        self.assertEqual(t['quantity_scope'],'REPORTED_MANUFACTURER_PERMITTED_OPERATION')
        self.assertEqual((t['report_pdf_page'],t['report_table']),(13,1))
        self.assertFalse(t['independent_measurement'])
        self.assertFalse(t['is_laboratory_ambient'])
        self.assertFalse(t['is_capacity_or_efficiency_validation_envelope'])

    def test_actual_ambient_and_test_date_remain_unknown(self):
        c=source_controls()['source_conditions']
        self.assertIsNone(c['laboratory_ambient_temperature_c'])
        self.assertIsNone(c['individual_laboratory_test_date'])
        self.assertEqual(c['laboratory_ambient_status'],'Q_NOT_ESTABLISHED')
        self.assertEqual((c['report_declared_version'],c['report_declared_month']),('1.0','2026-03'))
        for key in ('temperature_selected','temperature_adjustment_applied',
                    'performance_guaranteed_across_permitted_range','actual_site_operating_conditions_admitted'):
            self.assertFalse(c['application_boundary'][key])
        self.assertTrue(c['application_boundary']['constant_parameter_transfer_remains_debt'])

    def test_capacity_method_does_not_fabricate_sax_cycle_watts(self):
        p=source_controls()['source_conditions']['capacity_cycle_protocol']
        self.assertEqual(p['scope'],'PUBLISHED_COMMON_GUIDELINE_METHOD_NOT_SAX_RAW_TELEMETRY')
        self.assertEqual(p['nominal_charge_and_discharge_fractions'],[1,.5,.25])
        self.assertEqual(p['cycles_per_power_level'],3)
        self.assertEqual(p['conditioning_cycle_excluded'],1)
        self.assertEqual(p['included_cycle_numbers'],[2,3])
        self.assertEqual(p['included_discharge_energy_cycles_total'],6)
        self.assertEqual(p['usable_capacity_aggregation'],'ARITHMETIC_MEAN_RETAINED_DISCHARGED_DC_ENERGY')
        self.assertEqual(p['battery_efficiency_aggregation'],'RETAIN_REPORTED_ETA_BAT_NO_INVENTED_POOLING')
        self.assertEqual(p['illustrated_system'],'FRONIUS_D1_NOT_SAX_A1')
        self.assertIsNone(p['sax_individual_test_charge_kw'])
        self.assertIsNone(p['sax_individual_test_discharge_kw'])
        self.assertFalse(p['sax_raw_cycle_values_recovered'])
        self.assertFalse(p['catalog_rating_multiplication_admitted'])

    def test_low_load_protocol_is_separate_and_vertex_count_is_not_measurement_count(self):
        p=source_controls()['source_conditions']['additional_low_load_protocol']
        self.assertEqual(p['scope'],'ADDITIONAL_TO_COMMON_GUIDELINE_DISCHARGE_TEST')
        self.assertEqual(p['minimum_measured_supports'],8)
        self.assertEqual(p['upper_nominal_discharge_fraction'],.1)
        self.assertIsNone(p['actual_sax_measurement_count'])
        self.assertFalse(p['fitted_vertices_are_measurement_count'])
        self.assertFalse(p['automatic_fit_join'])

    def test_source_labelled_result_carries_complete_conditions_and_existing_limits(self):
        r=self.active();self.assertEqual(r['source_conditions'],source_controls()['source_conditions'])
        self.assertEqual(r['applicability_evidence_tier'],'E2')
        self.assertEqual(r['capacity_dc_output_equiv_kwh'],7.572)
        self.assertEqual(r['battery_dc_cycle_efficiency'],95.8183/100)
        self.assertFalse(r['complete_hardware_admission'])
        self.assertFalse(r['national_admission'])
        self.assertIsNone(r['annual_result'])

    def test_synthetic_reference_does_not_inherit_source_condition_authority(self):
        ref=replace(self.reference(),identity='EXPLICIT_MATHEMATICAL_EXPERIMENT')
        r=self.active(ref);self.assertEqual(r['applicability_evidence_tier'],'E3')
        self.assertIsNone(r['source_conditions'])

    def test_idle_proxy_retains_conditions_without_physical_allocation(self):
        r=m.provisional_standby_ac_energy(idle_hours=8760.)
        self.assertEqual(r['source_conditions'],source_controls()['source_conditions'])
        self.assertAlmostEqual(r['ac_energy_debit_kwh'],35.6532)
        self.assertIsNone(r['dc_inventory_drain_kwh'])
        self.assertFalse(r['physical_inventory_path_admitted'])
        self.assertFalse(r['all_state_measurement_verified'])
        self.assertFalse(r['is_upper_bound'])

    def test_result_metadata_mutation_cannot_change_fresh_handoff(self):
        r=self.active();r['source_conditions']['laboratory_ambient_temperature_c']=20
        r['source_conditions']['capacity_cycle_protocol']['sax_individual_test_charge_kw']=9.5
        fresh=self.active()['source_conditions']
        self.assertIsNone(fresh['laboratory_ambient_temperature_c'])
        self.assertIsNone(fresh['capacity_cycle_protocol']['sax_individual_test_charge_kw'])

    def test_temperature_is_not_an_unimplemented_runtime_command(self):
        for temperature in (-10,5,20,35,40):
            with self.subTest(temperature=temperature),self.assertRaises(ValueError):
                m.run(self.reference(),initial_dc_output_equiv_kwh=1.,commands=[
                    dict(charge_ac_kw=0.,discharge_ac_kw=1.,hours=.1,temperature_c=temperature)])

    def test_condition_hash_and_original_pins_preserve_lineage(self):
        c=source_controls();manifest=json.loads((m.ROOT/'registry/b07_sax_reference_manifest.json').read_text())
        packed=json.dumps(c['source_conditions'],sort_keys=True,separators=(',',':')).encode()
        self.assertEqual(hashlib.sha256(packed).hexdigest(),manifest['source_conditions']['source_conditions_sha256'])
        self.assertEqual(c['source_pdf_sha256'],'97266383faf3a4257a6a521cd1ce04d02eac2628142716e548333fb0c46cbfc7')
        self.assertEqual(c['source_js_sha256'],'3a843f5e1d3135112d714a274eb22a3ada2cffbec6dda9bb188d2a0d53c59528')
        self.assertEqual(manifest['curve_sha256'],'87d1b6b91950792c429746f71770237afd227e26ff5afd3bc5eb4d2b943ebfd6')
        self.assertFalse(manifest['source_conditions']['source_originals_publication'])


if __name__=='__main__':unittest.main()
