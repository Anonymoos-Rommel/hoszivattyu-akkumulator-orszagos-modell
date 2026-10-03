"""Synthetic numbers and tiny source bytes only; no external numeric panel fixture."""
import copy
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B17 import emission_factor_reference as ref


def encoded(value):
    """Serialize synthetic Decimal tokens without using binary floats."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k) + ':' + encoded(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(encoded(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False)


def pin(data, spec):
    spec.update(sha256=hashlib.sha256(data).hexdigest(), byte_count=len(data))


def fixture():
    manifest = copy.deepcopy(ref.source_manifest())
    rows, originals = [], []
    sources = {s['source_id']: b'%PDF-1.4\nSYNTHETIC SOURCE ' + s['source_id'].encode()
               for s in manifest['source_artifacts']}
    for source in manifest['source_artifacts']:
        pin(sources[source['source_id']], source)
    hashes = {s['source_id']: s['sha256'] for s in manifest['source_artifacts']}
    for spec in manifest['records']:
        metadata = spec['metadata']
        metadata['source_sha256'] = hashes[metadata['source_id']]
        row = {**metadata, 'value': Decimal('1.234567890123456789012345678901'),
               'lower': Decimal('0.123456789012345678901234567890'),
               'upper': Decimal('2.345678901234567890123456789012')}
        old = {k: row[k] for k in ('source_id', 'source_coordinate', 'pollutant', 'value', 'lower', 'upper',
               'unit', 'calorific_basis', 'evidence_class', 'method_tier', 'sector', 'abatement',
               'uncertainty_type', 'application_status')}
        if row['source_id'] == ref.IPCC:
            old.update(fuel=row['fuel'], notes=row['notes'])
        else:
            old.update(fuel_device_scope=row['source_fuel_device_scope'],
                       pm_measurement_boundary=row['pm_measurement_boundary'], missing_bridge=row['missing_bridge'])
        for correction in manifest['metadata_corrections']:
            if correction['row_one_based'] == row['original_row_ordinal']:
                old[correction['field']] = correction['original']
        spec['original_metadata_sha256'] = ref._metadata_digest(old)
        rows.append(row)
        originals.append(old)
    qualification = {
        'original_artifacts': [
            {'sha256': p['sha256'], 'bytes': p['byte_count']}
            for p in (manifest['lineage']['original_panel'], manifest['lineage']['original_source_manifest'])],
        'corrections': [{**c, 'numbers_unchanged': {
            k: originals[c['row_one_based'] - 1][k] for k in ('value', 'lower', 'upper', 'unit')}}
                       for c in manifest['metadata_corrections']],
    }
    panel = {'schema_version': 1, 'reference_id': ref.REFERENCE_ID,
             'original_panel_sha256': '', 'qualification_sha256': '', 'rows': rows}
    repin(manifest, panel, originals, qualification)
    return manifest, panel, originals, qualification, sources


def repin(manifest, panel, originals, qualification):
    pin(encoded(originals).encode(), manifest['lineage']['original_panel'])
    qualification['original_artifacts'][0].update(
        sha256=manifest['lineage']['original_panel']['sha256'],
        bytes=manifest['lineage']['original_panel']['byte_count'])
    pin(encoded(qualification).encode(), manifest['lineage']['qualification'])
    panel.update(original_panel_sha256=manifest['lineage']['original_panel']['sha256'],
                 qualification_sha256=manifest['lineage']['qualification']['sha256'])
    pin(encoded(panel).encode(), manifest['external_panel'])


class EmissionFactorReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.panel, self.originals, self.qualification, self.sources = fixture()

    def decode(self):
        return ref._decode_panel(encoded(self.panel), encoded(self.originals),
                                 encoded(self.qualification), self.manifest)

    def bundle(self, directory):
        directory = Path(directory)
        args = []
        for name, data in (('qualified', self.panel), ('original', self.originals), ('qualification', self.qualification)):
            path = directory / name
            path.write_text(encoded(data))
            args.append(path)
        paths = {}
        for index, (sid, data) in enumerate(self.sources.items()):
            path = directory / ('arbitrary-source-name-' + str(index))
            path.write_bytes(data)
            paths[sid] = path
        return (*args, paths)

    def test_public_manifest_has_metadata_not_numeric_panel_or_local_paths(self):
        manifest = ref.source_manifest()
        self.assertEqual(len(manifest['records']), 36)
        self.assertEqual(manifest['external_panel']['numeric_cell_count'], 108)
        self.assertEqual(manifest['readiness_percent'], 0)
        self.assertEqual(manifest['accepted_artifacts'], [])
        for spec in manifest['records']:
            self.assertEqual(set(spec['metadata']), ref.METADATA)
            self.assertFalse(ref.NUMBERS & set(spec['metadata']))
        serialized = json.dumps(manifest)
        self.assertNotIn('/workspace/', serialized)
        self.assertNotIn('"value":', serialized)
        self.assertNotIn('"lower":', serialized)
        self.assertNotIn('"upper":', serialized)
        for s in manifest['source_artifacts'] + manifest['contextual_source_artifacts']:
            self.assertEqual(s['source_priority'], 'P2' if s['source_id'].startswith('SRC-B17-AIB-') else 'P1')
            self.assertIsNone(s['repo_snapshot_path'])
            self.assertTrue(s['document_title'] and s['authority'] and s['claim_scope'])
            self.assertEqual(s['reuse_status'], 'EXTERNAL_ONLY')

    def test_decimal_lexemes_survive_low_precision_context(self):
        with localcontext() as context:
            context.prec = 4
            records = self.decode()
        self.assertEqual(records[0].value, Decimal('1.234567890123456789012345678901'))
        self.assertEqual(records[0].lower, Decimal('0.123456789012345678901234567890'))
        self.assertTrue(all(type(r.value) is Decimal for r in records))

    def test_integer_and_zero_are_exact_finite_values(self):
        self.panel['rows'][0].update(value=0, lower=0, upper=3)
        self.originals[0].update(value=0, lower=0, upper=3)
        self.assertEqual(self.decode()[0].value, Decimal(0))
        self.assertEqual(self.decode()[0].evidence_class, 'ASS_OFFICIAL_DEFAULT_METHOD_PARAMETER')

    def test_native_boundaries_and_original_metadata_are_preserved(self):
        rows = self.decode()
        self.assertEqual(rows[18].method_tier, 1)
        self.assertIn('Tier 1 average', rows[18].abatement)
        self.assertIn('Tier 2', rows[18].original_abatement)
        self.assertEqual(rows[22].device, 'Stoves')
        self.assertEqual(rows[22].source_fuel_device_scope, 'Solid fuels excluding biomass: stoves')
        self.assertIn('conventional stoves', rows[22].original_fuel_device_scope)
        self.assertEqual(rows[20].abatement_source_status, 'NA_IN_SOURCE_TIER2_TABLE')
        self.assertEqual(rows[20].numerical_abatement_adjustment, 'NOT_SELECTED')
        self.assertEqual(rows[15].carbon_reporting, 'BIOGENIC_CO2_SEPARATE_NOT_ZERO_OR_NEUTRAL')
        self.assertEqual(rows[0].carbon_reporting, 'FOSSIL_CO2')
        self.assertEqual(rows[16].carbon_reporting, 'INDIVIDUAL_POLLUTANT_MASS_NO_GWP')
        self.assertEqual(rows[19].pm_measurement_boundary, 'Unclear filterable versus total')
        self.assertEqual(rows[25].pm_measurement_boundary, 'Filterable only')
        self.assertEqual(rows[27].pm_measurement_boundary, 'Total primary particles: filterable plus condensable')
        self.assertNotEqual(rows[18].source_fuel_device_scope, rows[20].source_fuel_device_scope)
        self.assertTrue(all(r.application_status == 'REFERENCE_ONLY_NOT_PROGRAMME_INPUT' for r in rows))

    def test_records_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.decode()[0].value = Decimal(100)

    def test_duplicate_missing_reordered_unknown_rows_rejected(self):
        for case in ('duplicate', 'missing', 'reordered', 'unknown'):
            with self.subTest(case=case):
                original = copy.deepcopy(self.panel)
                if case == 'duplicate': self.panel['rows'][0] = self.panel['rows'][1]
                elif case == 'missing': self.panel['rows'].pop()
                elif case == 'reordered': self.panel['rows'].reverse()
                else: self.panel['rows'][0]['record_id'] = 'UNREVIEWED'
                with self.assertRaises(ref.EmissionFactorReferenceError): self.decode()
                self.panel = original

    def test_boolean_ordinal_and_tier_rejected_even_when_equal_to_one(self):
        for key in ('original_row_ordinal', 'method_tier'):
            row = self.panel['rows'][0]
            old = row[key]
            row[key] = True
            with self.assertRaises(ref.EmissionFactorReferenceError): self.decode()
            row[key] = old

    def test_malformed_json_and_duplicate_keys_rejected(self):
        for data in ('{', 'null', '[]', '{"schema_version":1,"schema_version":1}',
                     encoded(self.panel).replace('1.234567890123456789012345678901', 'NaN', 1)):
            with self.subTest(data=data[:70]), self.assertRaises(ref.EmissionFactorReferenceError):
                ref._decode_panel(data, encoded(self.originals), encoded(self.qualification), self.manifest)
        with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'duplicate JSON'):
            ref._json('{"x":{"y":1,"y":2}}')

    def test_boolean_string_blank_negative_nonfinite_numbers_rejected(self):
        for value in (True, '1.234', None, -1, Decimal('NaN'), Decimal('Infinity')):
            with self.subTest(value=str(value)):
                self.panel['rows'][0]['value'] = value
                with self.assertRaises(ref.EmissionFactorReferenceError): self.decode()

    def test_changed_numeric_cell_and_unordered_interval_rejected(self):
        self.panel['rows'][0]['value'] = Decimal('1.234567890123456789012345678902')
        with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'changed a source numeric'): self.decode()
        self.originals[0]['value'] = self.panel['rows'][0]['value'] = Decimal(9)
        with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'unordered'): self.decode()

    def test_changed_interpretation_is_not_admitted(self):
        cases = {'fuel': 'Hungarian 2025 gas', 'device': 'Any device', 'unit': 'kgCO2e/kWh useful heat',
                 'calorific_basis': 'GCV', 'sector': 'Power plants', 'evidence_class': 'OBS',
                 'source_coordinate': 'Different table', 'source_id': 'SRC-B17-HU-NID-2026',
                 'source_sha256': '0' * 64, 'application_status': 'PROGRAMME_DEFAULT',
                 'uncertainty_type': 'Independent normal distribution', 'carbon_reporting': 'ZERO',
                 'numerical_abatement_adjustment': '0', 'pm_measurement_boundary': 'Ambient PM2.5'}
        for key, value in cases.items():
            with self.subTest(key=key):
                row = self.panel['rows'][0]
                old = row[key]
                row[key] = value
                with self.assertRaises(ref.EmissionFactorReferenceError): self.decode()
                row[key] = old

    def test_lineage_and_correction_fail_closed(self):
        self.originals[18]['abatement'] = 'Invented correction'
        with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'original row metadata'): self.decode()
        self.originals[18]['abatement'] = self.qualification['corrections'][0]['original']
        self.qualification['corrections'][0]['qualified_interpretation'] = 'Tier 2'
        with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'qualified correction lineage'): self.decode()

    def test_panel_lineage_wrong_type_missing_extra_field_rejected(self):
        for case in ('lineage', 'schema_boolean', 'extra', 'missing'):
            panel = copy.deepcopy(self.panel)
            if case == 'lineage': panel['original_panel_sha256'] = '0' * 64
            elif case == 'schema_boolean': panel['schema_version'] = True
            elif case == 'extra': panel['rows'][0]['programme_weight'] = 1
            else: del panel['rows'][0]['missing_bridge']
            with self.subTest(case=case), self.assertRaises(ref.EmissionFactorReferenceError):
                ref._decode_panel(encoded(panel), encoded(self.originals), encoded(self.qualification), self.manifest)

    def test_exact_pinned_entrypoint_read_only_positive(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.bundle(directory)
            before = {p: p.read_bytes() for p in Path(directory).iterdir()}
            with patch.object(ref, 'source_manifest', return_value=self.manifest):
                result = ref.read_emission_factor_reference(*args)
            self.assertEqual(len(result.records), 36)
            self.assertEqual(result.programme_input_status, 'NOT_ADMITTED')
            self.assertEqual(result.national_emissions_status, 'NOT_ESTABLISHED')
            self.assertEqual(result.gwp_status, 'NOT_SELECTED')
            self.assertEqual(set(result.verified_source_ids), {ref.IPCC, ref.EEA})
            self.assertEqual(before, {p: p.read_bytes() for p in Path(directory).iterdir()})

    def test_every_external_pin_is_enforced_including_exact_length(self):
        for target in ('qualified', 'original', 'qualification', 'arbitrary-source-name-0', 'arbitrary-source-name-1'):
            for mutation in ('same_length', 'longer', 'shorter'):
                with self.subTest(target=target, mutation=mutation), tempfile.TemporaryDirectory() as directory:
                    args = self.bundle(directory)
                    path = Path(directory) / target
                    data = path.read_bytes()
                    path.write_bytes(b'!' + data[1:] if mutation == 'same_length' else
                                     data + b'\n' if mutation == 'longer' else data[:-1])
                    with patch.object(ref, 'source_manifest', return_value=self.manifest):
                        with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'bytes/hash'):
                            ref.read_emission_factor_reference(*args)

    def test_exact_source_mapping_requires_successful_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.bundle(directory)
            mappings = [None, {}, {ref.IPCC: args[3][ref.IPCC]},
                        {**args[3], 'SRC-B17-HU-NID-2026': args[3][ref.IPCC]},
                        {'SRC-B17-HU-NID-2026-OFFICIAL': args[3][ref.IPCC], ref.EEA: args[3][ref.EEA]}]
            for mapping in mappings:
                with self.subTest(mapping=str(mapping)), patch.object(ref, 'source_manifest', return_value=self.manifest):
                    with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'source mapping'):
                        ref.read_emission_factor_reference(*args[:3], mapping)

    def test_correct_hash_is_insufficient_for_html_masquerading_as_pdf(self):
        data = b'<html>synthetic bot placeholder</html>'
        self.sources[ref.IPCC] = data
        pin(data, self.manifest['source_artifacts'][0])
        with tempfile.TemporaryDirectory() as directory:
            args = self.bundle(directory)
            with patch.object(ref, 'source_manifest', return_value=self.manifest):
                with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'PDF signature'):
                    ref.read_emission_factor_reference(*args)

    def test_failed_acquisition_status_is_not_success(self):
        self.manifest['source_artifacts'][0]['acquisition_status'] = 'BOT_PLACEHOLDER_NOT_DOCUMENT'
        with tempfile.TemporaryDirectory() as directory:
            args = self.bundle(directory)
            with patch.object(ref, 'source_manifest', return_value=self.manifest):
                with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'successful document'):
                    ref.read_emission_factor_reference(*args)

    def test_public_manifest_tampering_cannot_repin_policy_or_sources(self):
        for key, value in [('programme_input_status', 'ADMITTED'), ('source_artifacts', []),
                           ('accepted_artifacts', ['accepted']), ('readiness_percent', 100)]:
            manifest = copy.deepcopy(self.manifest)
            manifest[key] = value
            with patch.object(Path, 'read_bytes', return_value=encoded(manifest).encode()):
                with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'manifest changed'):
                    ref.source_manifest()

    def test_context_verifies_successful_official_identity_without_factor(self):
        sid = 'SRC-B17-HU-NID-2026-OFFICIAL'
        spec = next(s for s in self.manifest['contextual_source_artifacts'] if s['source_id'] == sid)
        data = b'%PDF-1.4\nSYNTHETIC CONTEXT'
        pin(data, spec)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'arbitrary-filename'
            path.write_bytes(data)
            with patch.object(ref, 'source_manifest', return_value=self.manifest):
                context = ref.read_context_reference(path, sid)
                self.assertEqual(context.source_id, sid)
                self.assertEqual(context.reference_role, 'CONTEXT_ONLY_NOT_FACTOR_SELECTION')
                self.assertEqual(context.programme_input_status, 'NOT_ADMITTED')
                self.assertFalse(hasattr(context, 'value'))
                with self.assertRaises(FrozenInstanceError): context.source_id = 'other'
                for bad in ('SRC-B17-HU-NID-2026', 'SRC-B17-HU-NID-MIRROR-2023',
                            'SRC-B17-HU-IIR-2025-V1', ref.IPCC, '', None, []):
                    with self.subTest(source_id=bad), self.assertRaises(ref.EmissionFactorReferenceError):
                        ref.read_context_reference(path, bad)
                path.write_bytes(data + b'changed')
                with self.assertRaisesRegex(ref.EmissionFactorReferenceError, 'bytes/hash'):
                    ref.read_context_reference(path, sid)

    def test_missing_external_file_is_a_domain_error(self):
        with self.assertRaises(ref.EmissionFactorReferenceError):
            ref._pinned_bytes('/does/not/exist', self.manifest['external_panel'])


if __name__ == '__main__':
    unittest.main()
