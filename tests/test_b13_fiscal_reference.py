"""Synthetic values only: no external normalized numeric panel is a fixture."""
import copy
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

from modules.B13 import fiscal_reference as ref
from tools.materialize_b13_fiscal_reference import guard_private_output, materialize, source_map


def workbook(sheets):
    """Tiny synthetic OOXML with literal source lexemes, not Python floats."""
    ns = ref.NS['m']
    book = ET.Element(f'{{{ns}}}workbook')
    names = ET.SubElement(book, f'{{{ns}}}sheets')
    rels = ET.Element('Relationships')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        for index, (name, cells) in enumerate(sheets.items(), 1):
            ET.SubElement(names, f'{{{ns}}}sheet', name=name,
                          attrib={f'{{{ref.REL_NS}}}id': f'rId{index}'})
            ET.SubElement(rels, 'Relationship', Id=f'rId{index}', Target=f'worksheets/sheet{index}.xml')
            sheet = ET.Element(f'{{{ns}}}worksheet')
            for address, value in cells.items():
                cell = ET.SubElement(sheet, f'{{{ns}}}c', r=address)
                if isinstance(value, Decimal):
                    ET.SubElement(cell, f'{{{ns}}}v').text = str(value)
                elif value is not None:
                    cell.set('t', 'inlineStr')
                    ET.SubElement(ET.SubElement(cell, f'{{{ns}}}is'), f'{{{ns}}}t').text = value
            archive.writestr(f'xl/worksheets/sheet{index}.xml', ET.tostring(sheet))
        archive.writestr('xl/workbook.xml', ET.tostring(book))
        archive.writestr('xl/_rels/workbook.xml.rels', ET.tostring(rels))
    return output.getvalue()


def fixture():
    manifest = copy.deepcopy(ref.source_manifest())
    toy = {'CASH_REVENUE':100, 'CASH_EXPENDITURE':120, 'CASH_BALANCE':-20,
           'CASH_CENTRAL_REVENUE':60, 'CASH_CENTRAL_EXPENDITURE':75, 'CASH_CENTRAL_BALANCE':-15,
           'CASH_FUNDS_REVENUE':10, 'CASH_FUNDS_EXPENDITURE':9, 'CASH_FUNDS_BALANCE':1,
           'CASH_SS_REVENUE':30, 'CASH_SS_EXPENDITURE':36, 'CASH_SS_BALANCE':-6,
           'ORIGINAL_REVENUE':200, 'ORIGINAL_EXPENDITURE':210, 'ORIGINAL_BALANCE':-10,
           'AMENDED_REVENUE':300, 'AMENDED_EXPENDITURE':330, 'AMENDED_BALANCE':-30,
           'ESA_DEFICIT':-8, 'ESA_CENTRAL_DEFICIT':-6, 'ESA_LOCAL_BALANCE':2, 'ESA_SS_BALANCE':-4,
           'ESA_DEBT':20, 'ESA_INTEREST':4, 'GDP_UNADJUSTED':100,
           'ESA_REVENUE':40, 'ESA_EXPENDITURE':48, 'ESA_INTEREST_QUARTER_SUM':4,
           'ESA_BALANCE_QUARTER_SUM':-8}
    rows = []
    for spec in manifest['records']:
        row = {k: spec[k] for k in ('record_id','unit','period','boundary','accounting_basis',
                                    'status','evidence_tier','source_id','source_locator')}
        row.update(quantity='Synthetic quantity ' + row['record_id'],
                   value=None if spec['status'] == 'Q' else toy.get(spec['record_id'], 0),
                   price_basis='nominal current HUF', normalization='synthetic source', notes='Synthetic')
        if row['record_id'].startswith('REZSI_ORDER_'):
            row['notes'] = '0 immediately after funds available; instruction is not paid cash'
        if row['record_id'] == 'PRELIM_REVENUE':
            row['value'] = 1
        if row['record_id'] == 'MVM_REZSI_CASH':
            row['value'] = 2
        rows.append(row)
    edp = {name: {f'G{i}': Decimal(0) for i in range(1,70)}
           for name in ('Table 1','Table 2A','Table 2D','Table 3A')}
    for row in rows:
        if row['source_id'] == ref.EDP:
            sheet, cell = row['source_locator'].split('!')
            edp[sheet][cell] = Decimal(row['value'])
    edp['Table 1'].update(H5=Decimal(2025), I5=Decimal(2026), H8='half-finalized',
                          H16='half-finalized', I8='planned', I16='planned', H12='M')
    edp['Table 2A'].update(G22='M', G52='M', G17='L')
    edp['Table 2D'].update(G20='M', G35='M', G36='M')
    edp['Table 1']['G18'] = Decimal(10)
    edp['Table 2A'].update(G8=Decimal(-14), G11=Decimal(8), G67=Decimal(-6))
    edp['Table 2D'].update(G8=Decimal(-6), G26=Decimal(2), G45=Decimal(-4))
    edp['Table 3A'].update(G10=Decimal(8), G12=Decimal(1), G31=Decimal(1), G32=Decimal(1), G48=Decimal(10))
    monthly = {'MERLEG': {r['source_locator'].split('!')[1]: Decimal(r['value'])
                         for r in rows if r['source_id'] == ref.MONTHLY}}
    monthly['MERLEG']['G9'] = Decimal('1.000000002')
    quarters = ['synthetic', 'synthetic headers']
    for quarter in ('Q1','Q2','Q3','Q4'):
        cells = ['2025',quarter] + ['0']*47
        for column, value in ((19,'1'), (46,'-2'), (47,'12'), (48,'10')):
            cells[column] = value
        quarters.append(';'.join(cells))
    sources = {s['source_id']: ('synthetic ' + s['source_id']).encode()
               for s in manifest['source_artifacts']}
    sources.update({ref.EDP: workbook(edp), ref.MONTHLY: workbook(monthly),
                    ref.QUARTERLY: '\n'.join(quarters).encode(),
                    ref.ANNUAL_GDP: b'synthetic\nheader\n2025;100\n',
                    ref.ADJUSTED_GDP: ('synthetic\nheader\n' + ';'.join(['2025','Q1-Q4'] + ['0']*16 + ['0,2']) + '\n').encode()})
    return manifest, rows, sources, {ref.EDP: edp, ref.MONTHLY: monthly}


def pin(data, spec):
    spec.update(byte_count=len(data), sha256=hashlib.sha256(data).hexdigest())


def bundle(directory, manifest, rows, sources):
    directory = Path(directory)
    panel = directory / 'synthetic_panel.json'
    panel.write_text(json.dumps(rows))
    pin(panel.read_bytes(), manifest['external_panel'])
    paths = {}
    for index, spec in enumerate(manifest['source_artifacts']):
        sid = spec['source_id']
        paths[sid] = directory / f'arbitrary_name_{index}'
        paths[sid].write_bytes(sources[sid])
        pin(sources[sid], spec)
    return panel, paths


class FiscalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.rows, self.sources, self.books = fixture()

    def decode(self):
        return ref._decode_panel(json.dumps(self.rows), self.manifest, self.books)

    def test_public_manifest_contains_metadata_not_values_or_local_paths(self):
        manifest = ref.source_manifest()
        self.assertEqual(len(manifest['records']), 51)
        self.assertEqual(len(manifest['source_artifacts']), 14)
        self.assertTrue(all('value' not in r for r in manifest['records']))
        self.assertNotIn('local_snapshot_path', json.dumps(manifest, default=str))
        self.assertNotIn('/workspace/', json.dumps(manifest, default=str))
        self.assertTrue(all(s['original_url'].startswith('https://') for s in manifest['source_artifacts']))
        self.assertEqual(manifest['b15_admission_status'], 'NOT_GRANTED')

    def test_manifest_change_fails_before_repin_or_promotion(self):
        for key in ('model_use_status','headroom_status','raw_storage_policy'):
            changed = copy.deepcopy(self.manifest); changed[key] = 'ADMITTED'
            with patch.object(Path, 'read_bytes', return_value=json.dumps(changed, default=str).encode()):
                with self.assertRaises(ref.FiscalReferenceError): ref.source_manifest()

    def test_blank_stays_q_and_observed_zero_stays_numeric(self):
        rows = {r.record_id:r for r in self.decode()}
        self.assertIsNone(rows['INSTITUTIONAL_REZSI_RESERVE_CASH'].value)
        self.assertEqual(rows['INSTITUTIONAL_REZSI_RESERVE_CASH'].status, 'Q')
        self.assertEqual(rows['CASH_INTEREST_PAID'].value, Decimal(0))
        self.assertEqual(rows['CASH_INTEREST_PAID'].status, 'OBS')

    def test_native_decimal_and_legacy_value_remain_separate(self):
        row = next(r for r in self.decode() if r.record_id == 'PRELIM_REVENUE')
        self.assertEqual(row.value, Decimal('1.000000002'))
        self.assertEqual(row.normalized_value, Decimal(1))
        self.assertEqual(row.native_minus_normalized, Decimal('0.000000002'))
        self.assertEqual(row.reference_role, 'HISTORICAL_PROVISIONAL')

    def test_no_cross_basis_or_stock_flow_collapse(self):
        rows = {r.record_id:r for r in self.decode()}
        self.assertEqual(rows['ESA_DEBT'].value_kind, 'STOCK')
        self.assertEqual(rows['MVM_REZSI_ACCRUAL'].value_kind, 'STOCK')
        self.assertEqual(rows['ESA_INTEREST'].value_kind, 'FLOW')
        self.assertNotEqual(rows['CASH_INTEREST_PAID'].accounting_basis, rows['ESA_INTEREST'].accounting_basis)
        self.assertEqual(rows['ORIGINAL_REVENUE'].reference_role, 'APPROPRIATION_OR_INSTRUCTION')
        self.assertEqual(rows['MVM_REZSI_CASH'].reference_role, 'RECIPIENT_CORROBORATION')

    def test_record_is_immutable(self):
        with self.assertRaises(FrozenInstanceError): self.decode()[0].value = 999

    def test_unknown_duplicate_or_missing_records_rejected(self):
        for operation in ('unknown','duplicate','missing'):
            rows = copy.deepcopy(self.rows)
            if operation == 'unknown': rows[0]['record_id'] = 'FISCAL_HEADROOM'
            elif operation == 'duplicate': rows[0] = rows[1]
            else: rows.pop()
            with self.subTest(operation=operation), self.assertRaises(ref.FiscalReferenceError):
                ref._decode_panel(json.dumps(rows), self.manifest, self.books)

    def test_scope_vintage_units_and_status_cannot_be_promoted(self):
        for key, value in [('unit','HUF'), ('period','2026'), ('boundary','S.13'),
                           ('accounting_basis','ESA2010_final'), ('status','POL'),
                           ('source_id','SRC-OTHER'), ('source_locator','Table 1!I10'),
                           ('price_basis','real 2025 HUF')]:
            rows = copy.deepcopy(self.rows); rows[0][key] = value
            with self.subTest(key=key), self.assertRaises(ref.FiscalReferenceError):
                ref._decode_panel(json.dumps(rows), self.manifest, self.books)

    def test_missing_value_cannot_be_zero_imputed(self):
        row = next(r for r in self.rows if r['status'] == 'Q'); row['value'] = 0
        with self.assertRaises(ref.FiscalReferenceError): self.decode()

    def test_boolean_nonfinite_and_numeric_strings_rejected(self):
        for value in (True, '0', float('inf'), float('nan')):
            self.rows[0]['value'] = value
            with self.subTest(value=value), self.assertRaises(ref.FiscalReferenceError): self.decode()

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ref.FiscalReferenceError): ref._json('{"value":0,"value":1}')

    def test_workbook_blank_and_flags_are_not_numeric(self):
        data = workbook({'Synthetic': {'A1': Decimal('0.00000000000000000001'), 'A2': None, 'A3': 'M', 'A4': 'L'}})
        cells = ref._xlsx(data)['Synthetic']
        self.assertEqual(cells['A1'], Decimal('1E-20'))
        self.assertIsNone(cells['A2'])
        for key in ('A2','A3','A4'):
            with self.assertRaises(ref.FiscalReferenceError): ref._decimal(cells[key])

    def test_native_disagreement_is_not_silently_repaired(self):
        self.books[ref.MONTHLY]['MERLEG']['G9'] = Decimal(2)
        with self.assertRaises(ref.FiscalReferenceError): self.decode()

    def test_reconciliations_recompute_and_preserve_unresolved_gap(self):
        checks, flags = ref._reconcile(self.decode(), self.sources, self.books[ref.EDP])
        controls = {c.control_id:c for c in checks}
        self.assertEqual(len(checks), 32)
        self.assertEqual(controls['mvm_receipt_minus_orders'].value, Decimal(2000000))
        self.assertEqual(controls['mvm_receipt_minus_orders'].status, 'UNRESOLVED')
        self.assertIsNone(controls['mvm_receipt_minus_orders'].absolute_tolerance)
        self.assertEqual(controls['adjusted_gdp_difference'].status, 'RETAINED_DIAGNOSTIC')
        self.assertIn(('Table 2A','G17','L'), flags)

    def test_cash_identity_is_recomputed(self):
        self.rows[0]['value'] = 1
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'cash_identity'):
            ref._reconcile(self.decode(), self.sources, self.books[ref.EDP])

    def test_bridge_is_recomputed(self):
        self.books[ref.EDP]['Table 2A']['G11'] = Decimal(1)
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'central_bridge'):
            ref._reconcile(self.decode(), self.sources, self.books[ref.EDP])

    def test_planned_column_cannot_be_called_actual(self):
        self.books[ref.EDP]['Table 1']['I8'] = 'finalized'
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'year/status'):
            ref._reconcile(self.decode(), self.sources, self.books[ref.EDP])

    def test_source_m_cannot_be_replaced_by_missing_l(self):
        self.books[ref.EDP]['Table 2A']['G22'] = 'L'
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'flag changed'):
            ref._reconcile(self.decode(), self.sources, self.books[ref.EDP])

    def test_duplicate_quarters_rejected(self):
        self.sources[ref.QUARTERLY] = self.sources[ref.QUARTERLY].replace(b'Q4', b'Q3')
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'four distinct'):
            ref._reconcile(self.decode(), self.sources, self.books[ref.EDP])

    def test_instruction_schedule_sum_is_recomputed(self):
        next(r for r in self.rows if r['record_id'] == 'REZSI_ORDER_1003')['notes'] = '1 immediately after funds available'
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'instruction_components'):
            ref._reconcile(self.decode(), self.sources, self.books[ref.EDP])

    def test_exact_entrypoint_and_private_materialization_with_synthetic_bytes(self):
        base = ref.ROOT/'data/interim'; base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as d:
            panel, paths = bundle(d, self.manifest, self.rows, self.sources)
            with patch.object(ref, 'source_manifest', return_value=self.manifest), localcontext() as context:
                context.prec = 6
                result = ref.read_fiscal_reference(panel, paths)
                row = next(r for r in result.records if r.record_id == 'PRELIM_REVENUE')
                self.assertEqual(row.native_minus_normalized, Decimal('2E-9'))
                summary = materialize(panel, paths, Path(d)/'output')
                self.assertEqual(summary['record_count'], 51)
                self.assertIsNone(summary['programme_fiscal_result'])
                self.assertEqual(summary['native_lexeme_difference_count'], 1)
                with self.assertRaises(ref.FiscalReferenceError): materialize(panel, paths, Path(d)/'output')
            output = json.loads((Path(d)/'output/fiscal_reference.json').read_text())
            self.assertIsNone(next(r for r in output if r['status'] == 'Q')['value'])
            self.assertEqual(next(r for r in output if r['record_id'] == 'PRELIM_REVENUE')['value'], '1.000000002')

    def test_pinned_bytes_cannot_be_changed_or_replaced_with_normalized_copy(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            panel, paths = bundle(d, self.manifest, self.rows, self.sources)
            with patch.object(ref, 'source_manifest', return_value=self.manifest):
                original = panel.read_bytes(); panel.write_bytes(original + b' ')
                with self.assertRaisesRegex(ref.FiscalReferenceError, 'exact external bytes'): ref.read_fiscal_reference(panel, paths)
                panel.write_bytes(original); paths[ref.EDP].write_bytes(original)
                with self.assertRaisesRegex(ref.FiscalReferenceError, 'exact external bytes'): ref.read_fiscal_reference(panel, paths)

    def test_missing_or_extra_source_map_rejected(self):
        for mapping in ({}, {'SRC-OTHER': 'unread'}):
            with self.assertRaisesRegex(ref.FiscalReferenceError, 'source-ID/path'): ref.read_fiscal_reference('unread', mapping)

    def test_source_map_resolves_selected_ids_without_filename_authority(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            path = Path(d)/'map.json'
            path.write_text(json.dumps([{'source_id':s['source_id'], 'local_snapshot_path':'/tmp/arbitrary'}
                                        for s in self.manifest['source_artifacts']] + [{'source_id':'UNUSED'}]))
            self.assertEqual(len(source_map(path)), 14)

    def test_duplicate_source_map_is_rejected(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            path = Path(d)/'map.json'; path.write_text('{"SRC":"a","SRC":"b"}')
            with self.assertRaises(ref.FiscalReferenceError): source_map(path)

    def test_public_output_rejected(self):
        with self.assertRaises(ref.FiscalReferenceError): guard_private_output(ref.ROOT/'evidence/b13')

    def test_other_checkout_output_rejected(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            (Path(d)/'.git').mkdir()
            with self.assertRaises(ref.FiscalReferenceError): guard_private_output(Path(d)/'output')

    def test_symlinked_output_rejected(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            path = Path(d); (path/'real').mkdir(); (path/'link').symlink_to(path/'real')
            with self.assertRaises(ref.FiscalReferenceError): guard_private_output(path/'link'/'output')

    def test_ignored_untracked_output_and_lexical_normalization(self):
        base = ref.ROOT/'data/interim'; base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as d:
            self.assertEqual(guard_private_output(Path(d)/'nested/../out'), Path(d)/'out')

    def test_nested_repository_and_linked_worktree_cannot_use_outer_ignore(self):
        def git(*args, cwd=None):
            return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True)

        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            outer = Path(d)/'outer'
            git('init', '-q', str(outer))
            (outer/'.gitignore').write_text('/data/interim/\n')
            git('add', '.gitignore', cwd=outer)
            git('-c', 'user.name=Synthetic Test', '-c', 'user.email=test@example.invalid',
                'commit', '-q', '-m', 'Synthetic storage fixture', cwd=outer)
            nested = outer/'data/interim/nested-repository'
            nested.mkdir(parents=True)
            git('init', '-q', str(nested))
            linked = outer/'data/interim/nested-worktree'
            git('worktree', 'add', '--detach', str(linked), 'HEAD', cwd=outer)
            self.assertTrue((nested/'.git').is_dir())
            self.assertTrue((linked/'.git').is_file())
            for checkout in (nested, linked):
                for tail in ('output', 'absent/deep/output'):
                    target = checkout/tail
                    with self.subTest(checkout=checkout.name, tail=tail):
                        self.assertFalse(target.exists())
                        for filename in ('fiscal_reference.json', 'receipt.json'):
                            relative = str((target/filename).relative_to(checkout))
                            ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--no-index', '--', relative],
                                                     cwd=checkout, capture_output=True)
                            self.assertEqual(ignored.returncode, 1)
                        with self.assertRaisesRegex(ref.FiscalReferenceError, 'nested Git'):
                            guard_private_output(target, root=outer)
                        self.assertFalse(target.exists())
                # Even a nested checkout's own ignore file cannot grant it this
                # consumer's storage admission under the outer checkout.
                (checkout/'.gitignore').write_text('/output/\n')
                with self.assertRaises(ref.FiscalReferenceError):
                    guard_private_output(checkout/'output', root=outer)
            legitimate = outer/'data/interim/legitimate/absent/deep/output'
            self.assertEqual(guard_private_output(legitimate, root=outer), legitimate)
            self.assertEqual(guard_private_output(outer/'data/interim/nested-repository/../legitimate/output', root=outer),
                             outer/'data/interim/legitimate/output')

    def test_effective_git_root_must_be_the_intended_checkout(self):
        base = ref.ROOT/'data/interim'; base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as d:
            claimed_root = Path(d)
            with self.assertRaisesRegex(ref.FiscalReferenceError, 'intended Git checkout'):
                guard_private_output(claimed_root/'data/interim/deep/output', root=claimed_root)

    def test_broken_git_marker_and_broken_symlink_parent_rejected(self):
        base = ref.ROOT/'data/interim'; base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as d:
            path = Path(d)
            (path/'.git').symlink_to(path/'missing-metadata')
            with self.assertRaisesRegex(ref.FiscalReferenceError, 'nested Git'):
                guard_private_output(path/'absent/deep/output')
        with tempfile.TemporaryDirectory(dir=base) as d:
            path = Path(d)
            (path/'link').symlink_to(path/'missing-directory')
            with self.assertRaisesRegex(ref.FiscalReferenceError, 'symlinked output'):
                guard_private_output(path/'link'/'absent/output')

    def test_parent_traversal_to_public_output_stays_rejected(self):
        with self.assertRaisesRegex(ref.FiscalReferenceError, 'ignored data/interim'):
            guard_private_output(ref.ROOT/'data/interim/../../public-output')


if __name__ == '__main__':
    unittest.main()
