"""Synthetic-only tests; external numeric panels are not test fixtures."""
import copy
import csv
import hashlib
import io
import json
import stat
import subprocess
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from modules.B09 import future_supply_reference as ref
from tools.materialize_b09_future_supply_reference import guard_private_output, write_reference


def selection(source_id=ref.CAPACITY_SOURCE, **changes):
    spec = ref.PINS[source_id]
    result = ref.ReferenceSelection(source_id, spec['source_revision'], spec['scenario_id'],
                                    spec['model_stage'], ref.YEARS, ref.DATE_CONVENTION, ref.ROLES)
    return replace(result, **changes)


def cap_row(technology='Nuclear', value='12.50', year='2028', **changes):
    result = dict(zip(ref.CAPACITY_HEADER, (
        'ERAA 2025 final', year, 'HU00', technology, 'Synthetic category',
        'Available on market', value)))
    result.update(changes)
    return result


def eva_row(technology='Gas CCGT old 2', value='-12.5', year='2028', decision='Retirement'):
    return dict(zip(ref.EVA_HEADER, ('HU00', technology, decision, year, value)))


def csv_bytes(rows, header=ref.CAPACITY_HEADER):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(header)
    for row in rows:
        writer.writerow([row[k] for k in header])
    return ('\ufeff' + stream.getvalue()).encode('utf-8')


def zip_bytes(entries):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(stream, 'w') as z:
            for name, content in entries:
                z.writestr(name, content)
    return stream.getvalue()


def xlsx_bytes(rows=None, *, mutate=None, target='worksheets/sheet2.xml'):
    rows = rows or [(1, dict(zip('ABCDE', ref.EVA_HEADER))),
                    (2, dict(zip('ABCDE', eva_row().values())))]
    ns = ref.NS['m']
    sheet = ET.Element('worksheet', xmlns=ns)
    ET.SubElement(sheet, 'dimension', ref='A1:A1')  # Stale dimension must be ignored.
    data = ET.SubElement(sheet, 'sheetData')
    for n, values in rows:
        row = ET.SubElement(data, 'row', r=str(n))
        for col, value in values.items():
            cell = ET.SubElement(row, 'c', r=f'{col}{n}', t='inlineStr')
            ET.SubElement(ET.SubElement(cell, 'is'), 't').text = value
            if mutate:
                mutate(cell)
    workbook = (f'<workbook xmlns="{ns}" xmlns:r="{ref.REL_NS}"><sheets>'
                '<sheet name="Readme" r:id="rId1"/><sheet name="Cost Based" r:id="rId2"/>'
                '<sheet name="Revenue Based" r:id="rId3"/></sheets></workbook>')
    relations = (f'<Relationships><Relationship Id="rId2" Type="{ref.REL_NS}/worksheet" '
                 f'Target="{target}"/></Relationships>')
    return zip_bytes([('xl/workbook.xml', workbook),
                      ('xl/_rels/workbook.xml.rels', relations),
                      ('xl/worksheets/sheet2.xml', ET.tostring(sheet))])


class AuthorityTests(unittest.TestCase):
    def test_manifest_pins_and_research_only_policy(self):
        manifest = ref.source_manifest()
        self.assertEqual(len(manifest['source_artifacts']), 2)
        self.assertEqual(manifest['model_use_status'], 'SOURCE_SPECIFIC_REVIEW_REQUIRED')
        self.assertEqual(manifest['future_runtime_status'], 'NOT_AUTHORIZED_BY_THIS_REFERENCE')
        self.assertEqual(manifest['central_future_baseline_status'], 'NOT_SELECTED')
        self.assertEqual(manifest['record_evidence_status'], 'SCN')

    def test_manifest_policy_hash_identity_and_selector_drift_rejected(self):
        base = ref.source_manifest()
        mutations = (
            lambda m: m.update(model_use_status='QUALIFIED_E2_MODEL_USE'),
            lambda m: m.update(public_raw_reuse_status='REUSE_CLEARED'),
            lambda m: m.update(record_evidence_status='OBS'),
            lambda m: m.update(central_future_baseline_status='SELECTED'),
            lambda m: m.update(capacity_date_convention='START_OF_YEAR'),
            lambda m: m['source_artifacts'][0].update(sha256='0' * 64),
            lambda m: m['source_artifacts'][0].update(member_sha256='0' * 64),
            lambda m: m['source_artifacts'][0].update(source_id='OTHER'),
            lambda m: m['source_artifacts'].pop(),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as d:
                manifest = copy.deepcopy(base)
                mutate(manifest)
                path = Path(d) / 'manifest.json'
                path.write_text(json.dumps(manifest))
                with patch.object(ref, 'MANIFEST_PATH', path), self.assertRaises(ValueError):
                    ref.source_manifest()

    def test_explicit_compatible_selectors_required(self):
        invalid = [None, selection(source_revision='latest'),
                   selection(scenario_id=ref.PINS[ref.EVA_SOURCE]['scenario_id']),
                   selection(model_stage='POST_EVA_CAPACITY_CHANGE'),
                   selection(capacity_date_convention='MAVIR_START_OF_YEAR'),
                   selection(target_years=()), selection(target_years=(2028, 2028)),
                   selection(target_years=(2031,)), selection(target_years=(2028.0,)),
                   selection(resource_roles=()), selection(resource_roles=('ALL',)),
                   selection(resource_roles=('GENERATION', 'GENERATION'))]
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                ref._validate_selection(item)
        ref._validate_selection(selection(ref.EVA_SOURCE))

    def test_altered_bytes_fail_before_archive_parser(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fake.zip'
            path.write_bytes(b'altered source')
            with patch.object(ref, '_safe_archive') as archive, self.assertRaisesRegex(ValueError, 'bytes/hash'):
                ref.read_future_supply_reference(path, selection())
            archive.assert_not_called()


class SourceParsingTests(unittest.TestCase):
    def test_csv_selects_only_final_hu_and_retains_original_row(self):
        rows = [cap_row(Market_Node='AT00'), cap_row(data_version='ERAA 2024'),
                cap_row(data_version='ERAA 2025 pre-CfE'), cap_row(value='0')]
        parsed = ref._capacity_rows(csv_bytes(rows))
        self.assertEqual(parsed, [(5, rows[3])])
        records = ref._records(parsed, ref.CAPACITY_SOURCE, ref.PINS[ref.CAPACITY_SOURCE])
        self.assertEqual(records[0].value_mw, Decimal('0'))
        self.assertEqual(records[0].source_row, 5)
        self.assertEqual(records[0].source_value_cell, 'G5')
        self.assertEqual(dict(records[0].source_fields), rows[3])

    def test_header_width_and_encoding_rejected(self):
        for data in (b'a,b\n1,2\n', csv_bytes([]) + b'x,y\n', b'\xff'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                ref._capacity_rows(data)

    def test_zero_missing_and_sparse_eva_remain_distinct(self):
        rows = [(2, cap_row('Hard coal', '0', '2030'))]
        records = ref._records(rows, ref.CAPACITY_SOURCE, ref.PINS[ref.CAPACITY_SOURCE])
        self.assertEqual(len(records), 1)
        self.assertFalse(any(r.technology == 'Lignite' for r in records))
        with self.assertRaises(ValueError):
            ref._records([(2, cap_row(value=''))], ref.CAPACITY_SOURCE, ref.PINS[ref.CAPACITY_SOURCE])
        eva = ref._records([(9, eva_row('DSR', '7', '2035', 'Expansion'))],
                           ref.EVA_SOURCE, ref.PINS[ref.EVA_SOURCE])
        self.assertEqual([r.target_year for r in eva], [2035])
        self.assertEqual(eva[0].value_basis, 'NONCUMULATIVE_CHANGE_FROM_NATIONAL_TRENDS')
        self.assertEqual(eva[0].source_value_cell, 'E9')

    def test_roles_and_non_lifecycle_market_status(self):
        technologies = ('Nuclear', 'Battery utility scale', 'HP - iDSR', 'Electrolyser', 'Power to heat')
        records = ref._records([(i + 2, cap_row(t)) for i, t in enumerate(technologies)],
                               ref.CAPACITY_SOURCE, ref.PINS[ref.CAPACITY_SOURCE])
        self.assertEqual([r.resource_role for r in records],
                         ['GENERATION', 'STORAGE', 'DEMAND_RESPONSE', 'CONSUMPTION', 'CONSUMPTION'])
        for record in records:
            self.assertEqual(record.evidence_status, 'SCN')
            self.assertEqual(record.lifecycle_status, 'NOT_ESTABLISHED_BY_REFERENCE')
            self.assertEqual(record.financing_status, 'NOT_ESTABLISHED_BY_REFERENCE')
        with self.assertRaises(ValueError):
            replace(records[0], evidence_status='OBS')

    def test_duplicate_unknown_and_bad_numbers_rejected(self):
        cases = [[(2, cap_row()), (3, cap_row())], [(2, cap_row('Unknown'))],
                 [(2, cap_row(Operational_Status='Financed'))],
                 *[[(2, cap_row(value=v))] for v in ('', 'NaN', 'Infinity', '-1', '1,2', ' 3 ')]]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                ref._records(rows, ref.CAPACITY_SOURCE, ref.PINS[ref.CAPACITY_SOURCE])

    def test_eva_decision_sign_and_duplicate_guards(self):
        for row in (eva_row(value='1'), eva_row(value='-1', decision='Expansion'),
                    eva_row(decision='Finance'), eva_row(value='NaN')):
            with self.subTest(row=row), self.assertRaises(ValueError):
                ref._records([(2, row)], ref.EVA_SOURCE, ref.PINS[ref.EVA_SOURCE])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            ref._records([(2, eva_row()), (3, eva_row())], ref.EVA_SOURCE, ref.PINS[ref.EVA_SOURCE])

    def test_xlsx_cost_based_and_stale_dimensions(self):
        data = xlsx_bytes([(1, dict(zip('ABCDE', ref.EVA_HEADER))),
                           (100, dict(zip('ABCDE', eva_row().values())))])
        with ref._safe_archive(data) as z:
            self.assertEqual(ref._eva_rows(z), [(100, eva_row())])

    def test_xlsx_formula_type_address_and_rows_rejected(self):
        def formula(cell):
            ET.SubElement(cell, 'f').text = '1+1'
        for mutate in (formula, lambda c: c.set('t', 'e'), lambda c: c.set('t', 'b'),
                       lambda c: c.set('r', 'BAD'), lambda c: c.set('r', 'A99')):
            with self.subTest(mutate=mutate), ref._safe_archive(xlsx_bytes(mutate=mutate)) as z:
                with self.assertRaises(ValueError):
                    ref._eva_rows(z)
        for rows in ([(2, dict(zip('ABCDE', eva_row().values())))],
                     [(1, dict(zip('ABCDE', ref.EVA_HEADER))),
                      (1, dict(zip('ABCDE', ref.EVA_HEADER)))],
                     [(1, {'A': 'missing header'})]):
            with ref._safe_archive(xlsx_bytes(rows)) as z, self.assertRaises(ValueError):
                ref._eva_rows(z)

    def test_xlsx_relationship_escape_rejected(self):
        for target in ('../outside.xml', '/xl/worksheets/sheet2.xml', 'worksheets/sheet3.xml',
                       'https://example.test/sheet.xml'):
            with ref._safe_archive(xlsx_bytes(target=target)) as z, self.assertRaises(ValueError):
                ref._eva_rows(z)

    def test_archive_traversal_duplicates_symlinks_rejected(self):
        for name in ('../x', '/x', 'a/../b', 'a\\b', 'a//b', 'C:/x', './x'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                ref._safe_archive(zip_bytes([(name, b'x')]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            ref._safe_archive(zip_bytes([('x', b'a'), ('x', b'b')]))
        link = zipfile.ZipInfo('link')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            ref._safe_archive(zip_bytes([(link, b'target')]))

    def test_xml_entity_rejected(self):
        for data in (b'<!DOCTYPE x><x/>', b'<!ENTITY x "123"><x/>', '<!DOCTYPE x><x/>'.encode('utf-16'), b'<bad'):
            with self.assertRaises(ValueError):
                ref._xml(data)


class SyntheticIntakeTests(unittest.TestCase):
    def test_full_intake_selection_member_hash_and_counts(self):
        rows = []
        # 22 rows/year, invented values only. One source technology has two market treatments.
        for year in ref.YEARS:
            rows.extend(cap_row(t, '12.5', str(year)) for t in ref.CAPACITY_ROLES)
            rows.append(cap_row('Solar PV rooftop residential', '0', str(year),
                                Operational_Status='Out of market – for PV/battery dispatch optimization'))
        self.assertEqual(len(rows), 88)
        member = csv_bytes(rows)
        spec = dict(ref.PINS[ref.CAPACITY_SOURCE])
        data = zip_bytes([(spec['member'], member)])
        spec.update(sha256=hashlib.sha256(data).hexdigest(), byte_count=len(data),
                    member_sha256=hashlib.sha256(member).hexdigest(), member_byte_count=len(member))
        pins = {**ref.PINS, ref.CAPACITY_SOURCE: spec}
        with tempfile.TemporaryDirectory() as d, patch.object(ref, 'PINS', pins), patch.object(ref, 'source_manifest'):
            path = Path(d) / 'synthetic.zip'
            path.write_bytes(data)
            all_records = ref.read_future_supply_reference(path, selection())
            self.assertEqual(len(all_records.records), 88)
            chosen = ref.read_future_supply_reference(path, selection(target_years=(2030,), resource_roles=('CONSUMPTION',)))
            self.assertEqual({r.technology for r in chosen.records}, {'Electrolyser', 'Power to heat'})
            self.assertEqual({r.target_year for r in chosen.records}, {2030})
            self.assertEqual(chosen.full_source_record_count, 88)
            summary = ref.reference_summary(chosen)
            self.assertNotIn('total_capacity_mw', summary)
            self.assertEqual(summary['central_future_baseline_status'], 'NOT_SELECTED')
            private_parent = ref.ROOT / 'data/interim'
            private_parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=private_parent) as output:
                result = write_reference(chosen, Path(output) / 'result')
                self.assertEqual(result['selected_record_count'], 2)
                output_file = Path(output) / 'result/future_supply_source_reference.csv'
                self.assertNotIn(b'\r\n', output_file.read_bytes())
                with self.assertRaises(ValueError):
                    write_reference(chosen, Path(output) / 'result')
            spec['member_sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'member bytes/hash'):
                ref.read_future_supply_reference(path, selection())
            spec['member_sha256'] = hashlib.sha256(member).hexdigest()
            spec['selected_source_record_count'] = 99
            with self.assertRaisesRegex(ValueError, 'record count'):
                ref.read_future_supply_reference(path, selection())


class StorageBoundaryTests(unittest.TestCase):
    def test_public_repository_output_and_symlinks_rejected(self):
        with self.assertRaises(ValueError):
            guard_private_output(ref.ROOT / 'data/public-future')
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'real').mkdir()
            (root / 'link').symlink_to(root / 'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                guard_private_output(root / 'link/result')
            (root / 'foreign').mkdir()
            (root / 'foreign/.git').write_text('gitdir: somewhere')
            with self.assertRaises(ValueError):
                guard_private_output(root / 'foreign/result')

    def test_ignored_untracked_repo_path_allowed(self):
        path = ref.ROOT / 'data/interim/b09_future_synthetic_test_not_created'
        self.assertEqual(guard_private_output(path), path)

    def test_public_source_text_matches_git_clean_bytes(self):
        paths = (
            'modules/B09/future_supply_reference.py',
            'tools/materialize_b09_future_supply_reference.py',
            'tests/test_b09_future_supply_reference.py',
            'registry/b09_future_supply_reference_manifest.json',
            'docs/checkpoints/V1_020_B09_FUTURE_SUPPLY_REFERENCE.md',
        )
        for relative in paths:
            path = ref.ROOT / relative
            self.assertTrue(path.is_file())
            with self.subTest(path=relative):
                data = path.read_bytes()
                self.assertNotIn(b'\r', data)
                clean = subprocess.run(['git', 'hash-object', f'--path={relative}', '--stdin'],
                                       cwd=ref.ROOT, input=data, capture_output=True, check=True).stdout.strip()
                raw = subprocess.run(['git', 'hash-object', '--stdin'], cwd=ref.ROOT,
                                     input=data, capture_output=True, check=True).stdout.strip()
                self.assertEqual(clean, raw)


class AdversarialStorageTests(unittest.TestCase):
    """Disposable Git fixtures only; rejection must precede source access."""

    def test_storage_boundaries_before_first_source_read(self):
        from contextlib import ExitStack, redirect_stderr
        import io
        import subprocess
        import sys
        from tools import materialize_b09_future_supply_reference as materializer

        cases = (
            'deep_ignored', 'normalized_ignored', 'external_non_git_controlled_metadata',
            'nested_git', 'nested_git_deep', 'nested_worktree', 'nested_worktree_deep',
            'nested_output_root', 'nested_tracked_deleted', 'worktree_tracked_deleted',
            'foreign_git', 'foreign_worktree', 'removed_ignore', 'outer_tracked_deleted',
            'existing_csv', 'existing_receipt', 'csv_public_symlink', 'receipt_public_symlink',
            'csv_broken_symlink', 'receipt_broken_symlink', 'directory_private_symlink',
            'directory_public_symlink', 'directory_broken_symlink', 'private_root_symlink',
            'public_traversal', 'public_repository', 'broken_git_marker',
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
                base = Path(temporary)
                root = base / 'repository'
                def git(*args, cwd=root):
                    return subprocess.run(['git', *args], cwd=cwd, capture_output=True,
                                          text=True, check=True)
                git('init', '--quiet', str(root), cwd=base)
                (root / '.gitignore').write_text('/data/interim/\n')
                private = root / 'data/interim'
                private.mkdir(parents=True)
                output = private / 'missing/several/ancestors/output'
                if case.startswith('nested_') or case == 'worktree_tracked_deleted':
                    nested = private / 'nested'
                    if 'worktree' in case:
                        git('worktree', 'add', '--quiet', '--orphan', '-b', 'synthetic-only', str(nested))
                        self.assertTrue((nested / '.git').is_file())
                    else:
                        git('init', '--quiet', str(nested))
                        self.assertTrue((nested / '.git').is_dir())
                    self.assertEqual(Path(git('rev-parse', '--show-toplevel', cwd=nested).stdout.strip()), nested)
                    output = nested / ('missing/several/ancestors/output' if 'deep' in case else 'output')
                    if case == 'nested_output_root':
                        output = nested
                if case.startswith('foreign_'):
                    foreign = base / 'foreign'
                    if case == 'foreign_worktree':
                        git('worktree', 'add', '--quiet', '--orphan', '-b', 'foreign-only', str(foreign))
                        self.assertTrue((foreign / '.git').is_file())
                    else:
                        git('init', '--quiet', str(foreign))
                    output = foreign / 'missing/several/ancestors/output'
                if case == 'removed_ignore':
                    (root / '.gitignore').write_text('')
                if case.endswith('tracked_deleted'):
                    output.mkdir(parents=True)
                    target = output / materializer.OUTPUT_NAMES[0]
                    target.write_bytes(b'SYNTHETIC_INDEX_SENTINEL\n')
                    owner = root if case == 'outer_tracked_deleted' else nested
                    git('add', '--force', '--', str(target), cwd=owner)
                    target.unlink()
                    git('ls-files', '--error-unmatch', '--', str(target.relative_to(owner)), cwd=owner)
                sentinels = []
                if case.startswith('existing_'):
                    output.mkdir(parents=True)
                    target = output / (materializer.OUTPUT_NAMES[0] if case == 'existing_csv' else 'receipt.json')
                    target.write_bytes(b'SYNTHETIC_EXISTING_SENTINEL\n')
                    sentinels.append(target)
                if case.startswith(('csv_', 'receipt_')):
                    output.mkdir(parents=True)
                    destination = root / 'public-sentinel'
                    if 'public' in case:
                        destination.write_bytes(b'SYNTHETIC_PUBLIC_SENTINEL\n')
                        sentinels.append(destination)
                    filename = materializer.OUTPUT_NAMES[0] if case.startswith('csv_') else 'receipt.json'
                    (output / filename).symlink_to(destination)
                if case.startswith('directory_'):
                    destination = root / 'public' if 'public' in case else private / 'real'
                    if 'broken' not in case:
                        destination.mkdir()
                    (private / 'link').symlink_to(destination, target_is_directory=True)
                    output = private / 'link/output'
                if case == 'private_root_symlink':
                    private.rmdir()
                    (root / 'public').mkdir()
                    private.symlink_to(root / 'public', target_is_directory=True)
                    output = private / 'output'
                if case == 'normalized_ignored':
                    output = private / 'missing/../output'
                if case == 'external_non_git_controlled_metadata':
                    output = base / 'private/missing/output'
                    # Isolate inherited host checkouts outside the disposable fixture.
                    # Fixture Git markers, indexes, and all output paths stay real.
                    host_markers = {ancestor / '.git' for ancestor in base.parents}
                    exists, is_symlink = Path.exists, Path.is_symlink
                    stack.enter_context(patch.object(Path, 'exists',
                        lambda p: False if p in host_markers else exists(p)))
                    stack.enter_context(patch.object(Path, 'is_symlink',
                        lambda p: False if p in host_markers else is_symlink(p)))
                if case == 'public_traversal':
                    output = private / '../../public/output'
                if case == 'public_repository':
                    output = root / 'public/output'
                if case == 'broken_git_marker':
                    private.joinpath('.git').symlink_to(base / 'missing-git')
                before = {path: path.read_bytes() for path in sentinels}
                entries_before = sorted(str(path.relative_to(base)) for path in base.rglob('*'))
                accepted = case in ('deep_ignored', 'normalized_ignored') or (True and case == 'external_non_git_controlled_metadata')
                guard = materializer.guard_private_output
                if accepted:
                    self.assertEqual(guard(output, root=root), output.resolve())
                else:
                    with self.assertRaises(ValueError):
                        guard(output, root=root)
                argv = ['materializer', *['--source-file', 'missing.zip', '--source-id', 'synthetic', '--source-revision', 'synthetic', '--scenario-id', 'synthetic', '--model-stage', 'synthetic', '--capacity-date-convention', 'synthetic', '--target-years', '2030', '--resource-roles', 'synthetic'], '--output-dir', str(output)]
                with patch.object(materializer, 'guard_private_output', side_effect=lambda p: guard(p, root=root)), \
                        patch.object(materializer, 'read_future_supply_reference', side_effect=RuntimeError('FIRST_SOURCE_READ')) as reader, \
                        patch.object(sys, 'argv', argv), redirect_stderr(io.StringIO()):
                    if accepted:
                        with self.assertRaisesRegex(RuntimeError, 'FIRST_SOURCE_READ'):
                            materializer.main()
                        reader.assert_called_once()
                    else:
                        with self.assertRaises(SystemExit) as error:
                            materializer.main()
                        self.assertEqual(error.exception.code, 2)
                        reader.assert_not_called()
                self.assertEqual({path: path.read_bytes() for path in sentinels}, before)
                self.assertEqual(sorted(str(path.relative_to(base)) for path in base.rglob('*')), entries_before)


    def test_real_external_non_git_directory_remains_allowed(self):
        import os
        import subprocess
        from tools import materialize_b09_future_supply_reference as materializer
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            if any((p / '.git').exists() or (p / '.git').is_symlink()
                   for p in (base, *base.parents)):
                if os.environ.get('GITHUB_ACTIONS') == 'true':
                    self.fail('GitHub Actions must execute the real external-positive case in a Git-free temporary directory')
                self.skipTest('host temporary directory has a Git ancestor; real external-positive requires clean hosted CI')
            root = base / 'repository'
            subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
            output = base / 'external/missing/several/ancestors/output'
            self.assertEqual(materializer.guard_private_output(output, root=root), output)
            self.assertFalse(output.exists())


    def test_git_index_errors_fail_closed_before_source_read(self):
        from contextlib import redirect_stderr
        import io
        import subprocess
        import sys
        from tools import materialize_b09_future_supply_reference as materializer

        for case in ('valid_untracked', 'valid_tracked_deleted', 'unignored',
                     'corrupt_index', 'truncated_index', 'index_is_directory'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                def git(*args):
                    return subprocess.run(['git', *args], cwd=root, capture_output=True)
                self.assertEqual(git('init', '--quiet').returncode, 0)
                (root / '.gitignore').write_text('' if case == 'unignored' else '/data/interim/\n')
                known = root / 'synthetic-known-tracked.txt'
                known.write_bytes(b'SYNTHETIC_INDEX_NEIGHBOR\n')
                self.assertEqual(git('add', '--', known.name).returncode, 0)
                output = root / 'data/interim/deep/missing/output'
                target = output / materializer.OUTPUT_NAMES[0]
                tracked_target = case not in ('valid_untracked', 'unignored')
                if tracked_target:
                    output.mkdir(parents=True)
                    target.write_bytes(b'SYNTHETIC_TRACKED_TARGET\n')
                    self.assertEqual(git('add', '--force', '--', str(target.relative_to(root))).returncode, 0)
                    target.unlink()
                index = root / '.git/index'
                valid_index = index.read_bytes()
                if case == 'corrupt_index':
                    index.write_bytes(b'CORRUPT INDEX')
                elif case == 'truncated_index':
                    index.write_bytes(valid_index[:8])
                elif case == 'index_is_directory':
                    index.unlink()
                    index.mkdir()
                tracked = git('ls-files', '--error-unmatch', '--', str(target.relative_to(root)))
                ignored = git('check-ignore', '--quiet', '--no-index', '--', str(target.relative_to(root)))
                expected_git_code = 0 if case == 'valid_tracked_deleted' else 1 if not tracked_target else 128
                self.assertEqual(tracked.returncode, expected_git_code)
                self.assertEqual(ignored.returncode, 1 if case == 'unignored' else 0)
                before_entries = sorted(str(p.relative_to(root)) for p in root.rglob('*'))
                before_bytes = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
                accepted = case == 'valid_untracked'
                guard = materializer.guard_private_output
                if accepted:
                    self.assertEqual(guard(output, root=root), output)
                else:
                    with self.assertRaises(ValueError):
                        guard(output, root=root)
                argv = ['materializer', *['--source-file', 'missing.zip', '--source-id', 'synthetic', '--source-revision', 'synthetic', '--scenario-id', 'synthetic', '--model-stage', 'synthetic', '--capacity-date-convention', 'synthetic', '--target-years', '2030', '--resource-roles', 'synthetic'], '--output-dir', str(output)]
                with patch.object(materializer, 'guard_private_output', side_effect=lambda p: guard(p, root=root)), \
                        patch.object(materializer, 'read_future_supply_reference', side_effect=RuntimeError('FIRST_SOURCE_READ')) as reader, \
                        patch.object(sys, 'argv', argv), redirect_stderr(io.StringIO()):
                    if accepted:
                        with self.assertRaisesRegex(RuntimeError, 'FIRST_SOURCE_READ'):
                            materializer.main()
                        reader.assert_called_once()
                    else:
                        with self.assertRaises(SystemExit) as error:
                            materializer.main()
                        self.assertEqual(error.exception.code, 2)
                        reader.assert_not_called()
                self.assertEqual(sorted(str(p.relative_to(root)) for p in root.rglob('*')), before_entries)
                self.assertEqual({p: p.read_bytes() for p in root.rglob('*') if p.is_file()}, before_bytes)
                # Recover only this disposable index and prove the deleted target is still tracked.
                if index.is_dir():
                    index.rmdir()
                index.write_bytes(valid_index)
                self.assertEqual(git('ls-files', '--error-unmatch', '--', str(target.relative_to(root))).returncode,
                                 0 if tracked_target else 1)


if __name__ == '__main__':
    unittest.main()
