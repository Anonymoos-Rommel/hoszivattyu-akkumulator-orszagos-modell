"""Only synthetic numeric values; real fiscal panel and originals stay private."""
import copy
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B13 import fiscal_reference as ref
from tools import materialize_b13_fiscal_reference as tool
from tests.test_b13_fiscal_reference import fixture, pin

NEW = ref.SOURCE_LED_REFERENCE_ID
OLD = ref.LEGACY_REFERENCE_ID


def decimal_json(value):
    """Small synthetic fixture encoder; never convert Decimal to float."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError('nonfinite fixture')
        return str(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k) + ':' + decimal_json(v) for k,v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(decimal_json(v) for v in value) + ']'
    if isinstance(value, float):
        raise TypeError('no float fixture normalization')
    return json.dumps(value)


def fresh_fixture():
    _, rows, sources, books = fixture()
    manifest = copy.deepcopy(ref.source_manifest(NEW))
    by_id = {r['record_id']: r for r in rows}
    result = []
    for spec in manifest['records']:
        rid = spec['record_id']
        old_id = 'REZSI_ORIGINAL_ENVELOPE' if rid == 'REZSI_ANNEX_PUBLISHED_ENVELOPE' else rid
        row = copy.deepcopy(by_id[old_id]); row['record_id'] = rid
        for key in ('unit','period','boundary','accounting_basis','status','evidence_tier','source_id','source_locator'):
            row[key] = spec[key]
        row['quantity'] = 'Synthetic source-led quantity ' + rid
        row['normalization'] = 'Synthetic direct-source Decimal fixture'
        if row['source_id'] in books:
            sheet, cell = row['source_locator'].split('!')
            row['value'] = books[row['source_id']][sheet][cell]
        result.append(row)
    return manifest, result, sources, books


def write_bundle(directory, manifest, rows, sources):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    panel = directory / 'synthetic_source_led_panel.json'
    panel.write_text(decimal_json(rows), encoding='utf-8')
    pin(panel.read_bytes(), manifest['external_panel'])
    paths = {}
    for i, spec in enumerate(manifest['source_artifacts']):
        sid = spec['source_id']; path = directory / f'not_a_semantic_identifier_{i}'
        path.write_bytes(sources[sid]); paths[sid] = path; pin(sources[sid], spec)
    return panel, paths


class SourceLedFiscalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.rows, self.sources, self.books = fresh_fixture()

    def decode(self, rows=None):
        return ref._decode_panel(decimal_json(self.rows if rows is None else rows), self.manifest, self.books)

    def test_legacy_manifest_and_default_identity_are_preserved(self):
        self.assertEqual('ea2758707c05e9757b8efb8c5783c4081f06cda8bc9eb41900291e7303916cf2', hashlib.sha256(ref.MANIFEST_PATH.read_bytes()).hexdigest())
        self.assertEqual(ref.source_manifest(), ref.source_manifest(OLD))
        self.assertEqual('afa957ba0d52d78e7fa04995b87f0fbbb3bada18015edc2737895c91a6e1832a', ref.source_manifest()['external_panel']['sha256'])
        self.assertNotEqual(ref.source_manifest()['external_panel']['sha256'], ref.source_manifest(NEW)['external_panel']['sha256'])

    def test_new_reference_keeps_exact_original_pins_and_private_panel(self):
        old = {s['source_id']: (s['sha256'], s['byte_count']) for s in ref.source_manifest()['source_artifacts']}
        new = ref.source_manifest(NEW)
        self.assertEqual(old, {s['source_id']: (s['sha256'], s['byte_count']) for s in new['source_artifacts']})
        self.assertEqual(51, len(new['records']))
        self.assertTrue(all('value' not in row for row in new['records']))
        self.assertIs(new['confers_registry_acceptance'], False)
        self.assertNotIn('/workspace/', json.dumps(new, default=str))
        self.assertNotIn('local_snapshot_path', json.dumps(new, default=str))
        self.assertEqual('NOT_GRANTED', new['b15_admission_status'])

    def test_unknown_reference_selectors_fail_closed(self):
        for value in (None, True, 1, [], {}, 'latest', '2026-10-03'):
            with self.subTest(value=value), self.assertRaises(ref.FiscalReferenceError):
                ref.source_manifest(value)

    def test_manifest_mutation_and_cross_revision_swap_reject(self):
        changed = copy.deepcopy(self.manifest); changed['headroom_status'] = 'ESTABLISHED'
        for raw in (decimal_json(changed).encode(), ref.MANIFEST_PATH.read_bytes()):
            with patch.object(Path, 'read_bytes', return_value=raw), self.assertRaises(ref.FiscalReferenceError):
                ref.source_manifest(NEW)

    def test_annex_operative_metadata_is_descriptive_not_original_authority(self):
        new = ref.source_manifest(NEW)
        row = next(r for r in new['records'] if r['record_id'] == 'REZSI_ANNEX_PUBLISHED_ENVELOPE')
        self.assertEqual('pinned_annex_appropriation_context', row['accounting_basis'])
        self.assertEqual('DESCRIPTIVE_PINNED_ANNEX_CONTEXT', row['reference_role'])
        self.assertEqual('UNVERIFIED_NOT_ADMITTED', row['legal_effectivity_status'])
        source = next(s for s in new['source_artifacts'] if s['source_id'] == row['source_id'])
        self.assertEqual('UNVERIFIED_NOT_ADMITTED', source['legal_effectivity_status'])
        self.assertIn('not independently established', source['document_date'])
        self.assertIn('no effective-law', source['claim_scope'])
        self.assertNotIn('REZSI_ORIGINAL_ENVELOPE', {r['record_id'] for r in new['records']})

    def test_new_record_preserves_unverified_annex_status_in_consumer(self):
        row = next(r for r in self.decode() if r.record_id == 'REZSI_ANNEX_PUBLISHED_ENVELOPE')
        self.assertEqual('pinned_annex_appropriation_context', row.accounting_basis)
        self.assertEqual('PINNED_ANNEX_CONTENT_EFFECTIVITY_UNVERIFIED', row.source_status)
        self.assertIn('not independently established', row.source_document_dates[0])

    def test_native_decimal_values_are_exact_in_new_revision(self):
        rows = self.decode()
        self.assertTrue(all(r.native_minus_normalized in (None, Decimal(0)) for r in rows))
        row = next(r for r in rows if r.record_id == 'PRELIM_REVENUE')
        self.assertEqual(Decimal('1.000000002'), row.normalized_value)

    def test_legacy_serialization_tolerance_is_not_new_normalization(self):
        rows = copy.deepcopy(self.rows)
        next(r for r in rows if r['record_id'] == 'PRELIM_REVENUE')['value'] = 1
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'source-led workbook values'):
            self.decode(rows)

    def test_blank_zero_and_native_flags_remain_distinct(self):
        rows = self.decode(); by_id = {r.record_id:r for r in rows}
        self.assertIsNone(by_id['INSTITUTIONAL_REZSI_RESERVE_CASH'].value)
        self.assertEqual('Q', by_id['INSTITUTIONAL_REZSI_RESERVE_CASH'].status)
        self.assertEqual(Decimal(0), by_id['CASH_INTEREST_PAID'].value)
        self.assertEqual('OBS', by_id['CASH_INTEREST_PAID'].status)
        checks, flags = ref._reconcile(rows, self.sources, self.books[ref.EDP])
        self.assertEqual(32, len(checks)); self.assertEqual(7, len(flags))
        self.assertEqual({'M','L'}, {row[2] for row in flags})

    def test_accounting_and_stock_flow_roles_are_not_collapsed(self):
        rows = {r.record_id:r for r in self.decode()}
        self.assertNotEqual(rows['CASH_BALANCE'].accounting_basis, rows['ESA_DEFICIT'].accounting_basis)
        self.assertEqual('STOCK', rows['ESA_DEBT'].value_kind)
        self.assertEqual('STOCK', rows['MVM_REZSI_ACCRUAL'].value_kind)
        self.assertEqual('FLOW', rows['MVM_REZSI_CASH'].value_kind)
        self.assertEqual('RECIPIENT_CORROBORATION', rows['MVM_REZSI_CASH'].reference_role)

    def test_real_reader_entrypoint_binds_selected_identity_and_controls(self):
        with tempfile.TemporaryDirectory() as d:
            panel, paths = write_bundle(d, self.manifest, self.rows, self.sources)
            with patch.object(ref, 'source_manifest', return_value=self.manifest), localcontext() as ctx:
                ctx.prec = 5
                result = ref.read_fiscal_reference(panel, paths, reference_id=NEW)
            summary = ref.reference_summary(result)
            self.assertEqual(NEW, result.reference_id)
            self.assertEqual(51, summary['record_count']); self.assertEqual(32, summary['reconciliation_count'])
            self.assertEqual(0, summary['native_lexeme_difference_count'])
            self.assertIs(summary['legacy_panel_recovered'], False)
            self.assertEqual('NOT_ESTABLISHED', summary['headroom_status'])
            self.assertIsNone(summary['programme_fiscal_result'])
            self.assertEqual('UNVERIFIED_PINNED_DOCUMENT_CONTEXT_ONLY', summary['budget_annex_legal_effectivity'])
            with self.assertRaises(FrozenInstanceError): result.reference_id = OLD

    def test_new_panel_does_not_silently_replace_legacy_pin(self):
        with tempfile.TemporaryDirectory() as d:
            panel, paths = write_bundle(d, self.manifest, self.rows, self.sources)
            wrong = copy.deepcopy(self.manifest)
            wrong['external_panel'] = copy.deepcopy(ref.source_manifest()['external_panel'])
            with patch.object(ref, 'source_manifest', return_value=wrong), self.assertRaisesRegex(ref.FiscalReferenceError, 'exact external bytes'):
                ref.read_fiscal_reference(panel, paths)

    def test_changed_panel_or_original_source_rejects(self):
        for change in ('panel', 'source'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as d:
                panel, paths = write_bundle(d, self.manifest, self.rows, self.sources)
                target = panel if change == 'panel' else next(iter(paths.values()))
                target.write_bytes(target.read_bytes() + b' ')
                with patch.object(ref, 'source_manifest', return_value=self.manifest), self.assertRaisesRegex(ref.FiscalReferenceError, 'exact external bytes'):
                    ref.read_fiscal_reference(panel, paths, reference_id=NEW)

    def test_summary_cannot_label_an_unsupported_revision(self):
        fake = ref.FiscalReference((),(),(),'x',(), reference_id='unreviewed')
        with self.assertRaises(ref.FiscalReferenceError): ref.reference_summary(fake)

    def test_private_materializer_records_new_identity_and_decimal_strings(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); panel, paths = write_bundle(root/'inputs', self.manifest, self.rows, self.sources)
            out = root/'private-output'
            with patch.object(tool, 'guard_private_output', return_value=out), patch.object(ref, 'source_manifest', return_value=self.manifest):
                result = tool.materialize(panel, paths, out, reference_id=NEW)
            receipt = json.loads((out/'receipt.json').read_text())
            values = json.loads((out/'fiscal_reference.json').read_text())
            self.assertEqual(NEW, result['reference_id']); self.assertEqual(NEW, receipt['reference_id'])
            self.assertEqual('1.000000002', next(r for r in values if r['record_id']=='PRELIM_REVENUE')['normalized_value'])
            self.assertIsNone(next(r for r in values if r['record_id']=='INSTITUTIONAL_REZSI_RESERVE_CASH')['value'])
            self.assertEqual('EXTERNAL_ONLY_NOT_FOR_PUBLIC_COMMIT', receipt['normalized_storage_policy'])

    def test_source_map_list_uses_selected_reference(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'sources.json'; path.write_text(json.dumps([{'source_id':s['source_id'],'local_snapshot_path':f'/synthetic/{i}'} for i,s in enumerate(self.manifest['source_artifacts'])]))
            with patch.object(tool, 'source_manifest', return_value=self.manifest) as called:
                mapping = tool.source_map(path, reference_id=NEW)
            called.assert_called_once_with(NEW); self.assertEqual(14, len(mapping))

    def test_cli_forwards_explicit_reference_without_changing_output_policy(self):
        with patch.object(tool, 'source_map', return_value={}) as sm, patch.object(tool, 'materialize', return_value={'reference_id':NEW}) as materialized, redirect_stdout(io.StringIO()):
            tool.main(['--panel','synthetic-panel.json','--source-map','synthetic-map.json','--output-dir','private-output','--reference-id',NEW])
        sm.assert_called_once_with(Path('synthetic-map.json'), reference_id=NEW)
        materialized.assert_called_once_with(Path('synthetic-panel.json'), {}, Path('private-output'), reference_id=NEW)

    def test_public_repository_storage_is_still_rejected_for_new_reference(self):
        with self.assertRaises(ref.FiscalReferenceError):
            tool.materialize('absent-private-panel', {}, tool.ROOT/'data/processed/forbidden-numeric-output', reference_id=NEW)


if __name__ == '__main__':
    unittest.main()
