"""Populated conditional physical reference and adversarial admission tests."""
import copy
import csv
from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B05.engine import OperatingPointResult
from modules.B06 import prospective_capacity_reference as ref
from modules.B06.engine import EvidenceValue
from modules.B06.tabula_seasonal_reference import calculate_reference as annual_reference, source_package


class ProspectiveCapacityReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(ref.MANIFEST_PATH.read_text())

    def run_manifest(self, manifest):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'manifest.json'
            path.write_text(json.dumps(manifest))
            return ref.calculate_reference(manifest_path=path)

    def assert_invalid_before_design(self, manifest):
        with patch.object(ref.design_load, 'calculate_design_heat_load') as helper:
            with self.assertRaises(ValueError):
                self.run_manifest(manifest)
            helper.assert_not_called()

    def test_real_canonical_calculation_and_independent_decimal_witness(self):
        with patch.object(ref.design_load, 'calculate_design_heat_load',
                          wraps=ref.design_load.calculate_design_heat_load) as helper:
            result = ref.calculate_reference()
        helper.assert_called_once()
        expected = Decimal('82.200595555556') + Decimal('18.438336')
        expected += Decimal('59.05088') + Decimal('86.08') * Decimal('.26') * Decimal('1.20')
        self.assertAlmostEqual(result['total_h_w_per_k'], float(expected), places=10)
        self.assertAlmostEqual(result['design_heat_kw'], float(expected * Decimal('32') / 1000), places=12)
        self.assertAlmostEqual(sum(result['component_h_w_per_k'].values()) + result['ventilation_h_w_per_k'],
                               result['total_h_w_per_k'], places=12)
        self.assertEqual(result['separate_thermal_bridge_h_w_per_k'], 0)
        self.assertEqual(result['design_inputs']['ventilation']['air_change_rate_h']['value'], .56)
        self.assertEqual(result['design_inputs']['ventilation']['heat_recovery_efficiency']['value'], 0)
        self.assertEqual(result['design_inputs']['ventilation']['volume_m3']['value'], 301.28)
        self.assertEqual(result['design_inputs']['components'][1]['component'], 'aggregate_openings_including_doors')

    def test_independent_source_pair_interpolation_and_signed_margins(self):
        result = ref.calculate_reference()
        with (ref.ROOT / self.manifest['inputs']['wm50_grid']['path']).open() as f:
            rows = list(csv.DictReader(f))
        for probe, supply in zip(result['probes'][:2], ('35', '45')):
            support = {r['outdoor_temperature_c']: r for r in rows
                       if r['mode'] == 'MAX' and r['supply_temperature_c'] == supply}
            low, high = support['-15'], support['-10']
            weight = Decimal('3') / 5
            q0, q1 = Decimal(low['thermal_capacity_kw']), Decimal(high['thermal_capacity_kw'])
            p0, p1 = q0 / Decimal(low['cop']), q1 / Decimal(high['cop'])
            q = q0 + weight * (q1 - q0)
            p = p0 + weight * (p1 - p0)
            self.assertAlmostEqual(probe['thermal_capacity_kw'], float(q), places=13)
            self.assertAlmostEqual(probe['electrical_input_kw'], float(p), places=13)
            self.assertAlmostEqual(probe['cop'], float(q / p), places=13)
            self.assertAlmostEqual(probe['cop'] * probe['electrical_input_kw'], probe['thermal_capacity_kw'])
            self.assertAlmostEqual(probe['signed_capacity_margin_kw'], float(q) - result['design_heat_kw'])
            self.assertLess(probe['signed_capacity_margin_kw'], 0)
            self.assertEqual(probe['physical_comparison_evidence_status'], 'SCN')
            self.assertEqual(probe['performance_status'], 'DER')
        self.assertAlmostEqual(result['probes'][0]['thermal_capacity_kw'], 4.38)
        self.assertAlmostEqual(result['probes'][1]['thermal_capacity_kw'], 4.26)

    def test_higher_w55_source_blank_is_q_never_zero_power(self):
        result = ref.calculate_reference()
        point = result['probes'][2]
        self.assertEqual(point['performance_status'], 'Q / OUT_OF_PERFORMANCE_DOMAIN')
        self.assertEqual(point['physical_comparison_evidence_status'], 'Q')
        for name in ('thermal_capacity_kw', 'electrical_input_kw', 'cop', 'signed_capacity_margin_kw'):
            self.assertIsNone(point[name])
        self.assertGreater(result['design_heat_kw'], 0)
        self.assertIn('SOURCE_BLANK', [r['availability'] for r in point['source_support_cells']])

    def test_missing_manufacturer_corner_is_q_not_interpolated_or_zero(self):
        load = wm50.load_wm50_reference
        def missing(mode, *, fixed_supply_c):
            model = load(mode, fixed_supply_c=fixed_supply_c)
            if fixed_supply_c == 35:
                del model._grid[(-10., 35.)]
            return model
        with patch.object(wm50, 'load_wm50_reference', side_effect=missing):
            result = ref.calculate_reference()
        point = result['probes'][0]
        self.assertEqual(point['performance_status'], 'Q / MISSING_GRID_POINT')
        self.assertIsNone(point['electrical_input_kw'])
        self.assertIsNone(point['signed_capacity_margin_kw'])

    def test_scn_remains_after_unconditional_der_helper_and_no_admission(self):
        result = ref.calculate_reference()
        self.assertEqual(result['canonical_arithmetic_status'], 'DER')
        self.assertEqual(result['design_evidence_status'], 'SCN')
        self.assertEqual(result['evidence_status'], 'SCN')
        self.assertEqual(result['dependence_qualification'], ref.DEPENDENCE)
        self.assertEqual(result['input_lineage']['facade']['source_evidence_status'], 'DER/SCN_PROXY')
        self.assertEqual(result['input_lineage']['top']['source_evidence_status'], 'POL/DER/SCN')
        self.assertTrue(all(s == 'Q / NOT_ASSESSED' for s in result['withheld_claims'].values()))
        self.assertTrue(all(s == 'Q / NOT_POPULATED' for s in result['omitted_inputs'].values()))
        for point in result['probes']:
            self.assertIsNone(point['required_emitter_supply_c'])
            self.assertEqual(point['required_emitter_supply_status'], 'Q / P65_NOT_ASSESSED')
            self.assertEqual(point['probe_role'], ref.PROBE_ROLE)

    def test_exact_source_defrost_annotations_do_not_become_zero_defrost(self):
        result = ref.calculate_reference()
        for point in result['probes']:
            for cell in point['source_support_cells']:
                self.assertEqual(cell['defrost_source_annotation'], 'NOT_GRAY_NO_EXPLICIT_INTEGRATED_LABEL')
                self.assertEqual(cell['mode'], 'MAX')
                self.assertEqual(cell['source_id'], wm50.SOURCE_ID)
        self.assertEqual(result['omitted_inputs']['additional_dynamic_defrost'], 'Q / NOT_POPULATED')
        self.assertEqual(result['omitted_inputs']['numeric_cycling'], 'Q / NOT_POPULATED')

    def test_missing_or_wrong_bottom_boundary_fails_before_design(self):
        for boundary in (None, '', 'GROUND_CONTACT', 'TABULA_SEASONAL_GROUND_FACTOR'):
            with self.subTest(boundary=boundary):
                m = copy.deepcopy(self.manifest)
                m['boundary_declarations']['bottom'] = boundary
                self.assert_invalid_before_design(m)
        m = copy.deepcopy(self.manifest)
        del m['scenario']['bottom_design_boundary_correction']
        self.assert_invalid_before_design(m)

    def test_every_numeric_but_q_scenario_input_is_rejected_before_design(self):
        for key in self.manifest['scenario']:
            with self.subTest(key=key):
                m = copy.deepcopy(self.manifest)
                m['scenario'][key]['evidence_status'] = 'Q'
                self.assertIsNotNone(m['scenario'][key]['value'])
                self.assert_invalid_before_design(m)
        m = copy.deepcopy(self.manifest)
        m['equipment']['fixed_supply_probes_c'][0]['evidence_status'] = 'Q'
        self.assert_invalid_before_design(m)

    def test_missing_nonfinite_boolean_units_and_sources_fail(self):
        for key, value in (('value', None), ('value', float('nan')), ('value', float('inf')),
                           ('value', True), ('unit', 'kW'), ('source_ids', []), ('source_ids', 'invented')):
            with self.subTest(key=key, value=value):
                m = copy.deepcopy(self.manifest)
                m['scenario']['bottom_base_u_w_m2k'][key] = value
                self.assert_invalid_before_design(m)

    def test_numeric_but_q_built_inputs_rejected_before_legacy_helper(self):
        m = ref._load_manifest(ref.MANIFEST_PATH)
        inputs = ref._build_design(m, ref._read_rows(m))
        changes = [
            replace(inputs, design_outdoor_temperature_c=replace(inputs.design_outdoor_temperature_c, status='Q')),
            replace(inputs, thermal_bridge_h_w_per_k=replace(inputs.thermal_bridge_h_w_per_k, status='Q')),
            replace(inputs, location_or_climate_zone=replace(inputs.location_or_climate_zone, status='Q')),
            replace(inputs, ventilation=replace(inputs.ventilation, air_change_rate_h=replace(inputs.ventilation.air_change_rate_h, status='Q'))),
        ]
        for field in ('u_value_w_m2k', 'area_m2', 'correction_factor'):
            component = inputs.components[0]
            bad = replace(component, **{field: replace(getattr(component, field), status='Q')})
            changes.append(replace(inputs, components=(bad, *inputs.components[1:])))
        for bad in changes:
            with patch.object(ref, '_build_design', return_value=bad), patch.object(ref.design_load, 'calculate_design_heat_load') as helper:
                with self.assertRaisesRegex(ValueError, 'Q evidence'):
                    ref.calculate_reference()
                helper.assert_not_called()

    def test_numeric_but_q_source_row_rejected(self):
        m = ref._load_manifest(ref.MANIFEST_PATH)
        rows = ref._read_rows(m)
        rows['bottom']['evidence_status'] = 'Q'
        with patch.object(ref, '_read_rows', return_value=rows), patch.object(ref.design_load, 'calculate_design_heat_load') as helper:
            with self.assertRaisesRegex(ValueError, 'Q evidence'):
                ref.calculate_reference()
            helper.assert_not_called()

    def test_dropped_scn_lineage_is_rejected(self):
        for status in ('DER', 'OBS', 'POL', 'ASS'):
            m = copy.deepcopy(self.manifest)
            m['physical_evidence_status'] = status
            self.assert_invalid_before_design(m)
            m = copy.deepcopy(self.manifest)
            m['scenario']['bottom_base_u_w_m2k']['evidence_status'] = status
            self.assert_invalid_before_design(m)
        m = ref._load_manifest(ref.MANIFEST_PATH)
        inputs = ref._build_design(m, ref._read_rows(m))
        bad = replace(inputs, ventilation=replace(inputs.ventilation, volume_m3=replace(inputs.ventilation.volume_m3, status='DER')))
        with patch.object(ref, '_build_design', return_value=bad), patch.object(ref.design_load, 'calculate_design_heat_load') as helper:
            with self.assertRaisesRegex(ValueError, 'SCN lineage'):
                ref.calculate_reference()
            helper.assert_not_called()

    def test_thermal_bridge_double_count_and_wrong_correction_are_rejected(self):
        for key, value in (('additional_thermal_bridge_h_w_per_k', 20),
                           ('bottom_base_u_w_m2k', .312), ('bottom_zeta', .4),
                           ('bottom_design_boundary_correction', .5)):
            m = copy.deepcopy(self.manifest)
            m['scenario'][key]['value'] = value
            self.assert_invalid_before_design(m)
        m = copy.deepcopy(self.manifest)
        m['thermal_bridge_treatment'] = 'CORRECTED_U_PLUS_SEPARATE_BRIDGES'
        self.assert_invalid_before_design(m)

    def test_wrong_product_mode_source_and_emitter_role_fail(self):
        for key, value in (('product', 'PUZ-WM85VAA'), ('mode', 'MIN'), ('mode', 'AUTOMATIC'),
                           ('source_id', 'unrelated-product'), ('probe_role', 'P65_REQUIRED_SUPPLY')):
            m = copy.deepcopy(self.manifest)
            m['equipment'][key] = value
            self.assert_invalid_before_design(m)
        load = wm50.load_wm50_reference
        with patch.object(wm50, 'load_wm50_reference', side_effect=lambda mode, **kwargs: load('NOMINAL', **kwargs)):
            with self.assertRaisesRegex(ValueError, 'wrong product/mode'):
                ref.calculate_reference()

    def test_false_building_population_p65_eligibility_completion_admission_fails(self):
        for key, value in (('claim_scope', 'REALIZED_ELIGIBILITY'), ('dependence_qualification', 'JOINT_BUILDING_POINT'),
                           ('p65_authority', 'READY'), ('eligibility', 'PASS'), ('completion', 'READY'),
                           ('national_participants', 2000000), ('annual_electricity_kwh', 0)):
            m = copy.deepcopy(self.manifest)
            m[key] = value
            self.assert_invalid_before_design(m)
        m = copy.deepcopy(self.manifest)
        m['scenario']['design_indoor_temperature_c']['value'] = 21.39
        self.assert_invalid_before_design(m)

    def test_source_hash_drift_fails_before_design(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = self.manifest['inputs']['facade']['path']
            (root / first).parent.mkdir(parents=True)
            (root / first).write_bytes((ref.ROOT / first).read_bytes() + b'\n')
            with patch.object(ref, 'ROOT', root), patch.object(ref.design_load, 'calculate_design_heat_load') as helper:
                with self.assertRaisesRegex(ValueError, 'hash mismatch: facade'):
                    ref.calculate_reference()
                helper.assert_not_called()

    def test_silent_source_repin_or_alias_change_is_rejected(self):
        for key, value in (('sha256', hashlib.sha256(b'changed').hexdigest()), ('source_ids', ['other']), ('path', '../other.csv')):
            m = copy.deepcopy(self.manifest)
            m['inputs']['facade'][key] = value
            self.assert_invalid_before_design(m)

    def test_scope_text_and_annual_metadata_cannot_promote_claims(self):
        m = copy.deepcopy(self.manifest)
        m['limitations'] = ['This proves P65 eligibility and completion.']
        self.assert_invalid_before_design(m)
        for key, value in (('claim_scope', 'NATIONAL_ANNUAL_RESULT'), ('service', 'uniform'),
                           ('sha256', 'invented'), ('source_id', 'unrelated')):
            m = copy.deepcopy(self.manifest)
            m['separate_regression'][key] = value
            self.assert_invalid_before_design(m)

    def test_numeric_manufacturer_point_with_q_status_cannot_be_admitted(self):
        load = wm50.load_wm50_reference
        def contradictory(mode, *, fixed_supply_c):
            model = load(mode, fixed_supply_c=fixed_supply_c)
            if fixed_supply_c == 35:
                point = model.evaluate(-12, 35).point
                model.evaluate = lambda *_: OperatingPointResult('Q / MISSING_GRID_POINT', point)
            return model
        with patch.object(wm50, 'load_wm50_reference', side_effect=contradictory):
            with self.assertRaisesRegex(ValueError, 'identity/evidence'):
                ref.calculate_reference()

    def test_duplicate_missing_or_q_selected_source_row_fails_join(self):
        original = ref.ROOT
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_path = self.manifest['inputs']['facade']['path']
            file = root / data_path
            file.parent.mkdir(parents=True)
            with (original / data_path).open() as f:
                reader = csv.DictReader(f)
                headers, rows = reader.fieldnames, list(reader)
            for modified in ([rows[0], rows[0]], rows[1:], [dict(rows[0], evidence_status='Q')]):
                with file.open('w', newline='') as f:
                    writer = csv.DictWriter(f, headers)
                    writer.writeheader()
                    writer.writerows(modified)
                with patch.object(ref, 'ROOT', root):
                    with self.assertRaises(ValueError):
                        ref._read_rows(self.manifest)

    def test_native_nine_annual_references_remain_separate(self):
        package = source_package()
        self.assertEqual(len(package['rows']), 9)
        before = json.dumps(package, sort_keys=True)
        ref.calculate_reference()
        for row in package['rows']:
            values = row['values']
            result = annual_reference(values['Code_BuildingVariant'], service='source')
            self.assertEqual(result['evidence_status'], 'DER')
            self.assertEqual(result['service'], 'source')
            self.assertAlmostEqual(result['annual_heat_kwh_m2'], values['q_h_nd'], places=10)
            self.assertAlmostEqual(result['annual_heat_kwh'], values['q_h_nd'] * values['A_C_Ref'], places=7)
            self.assertEqual(result['indoor_temperature_c'], values['theta_i'])
        self.assertEqual(json.dumps(source_package(), sort_keys=True), before)
        self.assertEqual(self.manifest['separate_regression']['relationship'], 'SEPARATE_NATIVE_ANNUAL_REGRESSION_NOT_A_DESIGN_INPUT')


if __name__ == '__main__':
    unittest.main()
