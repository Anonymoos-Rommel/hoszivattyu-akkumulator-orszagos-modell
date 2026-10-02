from dataclasses import replace
import io
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from modules.B08.gui_load_reference import (
    SOURCE_YEARS, QualifiedGuiLoadPanel, _manifest, _parse_cells, _xlsx_cells,
    local_2025_reference, read_pinned_gui_workbook, reference_summary,
)
from modules.B08.observed_load_contract import ObservedLoadContractError
from modules.B08.seasonal_reporting_contract import (
    ReportingWindowKind, canonical_reporting_window, seasonal_peak,
)


def cells_for_year(year, power):
    cells = {'A1': 'Total Load - Day-ahead / Actual', 'A2': 'Actual Total Load [6.1.A]',
             'A3': 'Day-ahead Total Load Forecast [6.1.B]',
             'A4': f'01/01/{year} 00:00 - 01/01/{year+1} 00:00 (UTC)',
             'A6': 'MTU', 'B6': 'BZN|HU', 'C6': 'BZN|HU', 'A7': 'MTU',
             'B7': 'Actual Total Load (MW)', 'C7': 'Day-ahead Total Load Forecast (MW)'}
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year+1, 1, 1, tzinfo=timezone.utc)
    step = timedelta(minutes=15)
    for i in range(int((end-start)/step)):
        a = start+i*step
        b = a+step
        cells[f'A{i+8}'] = a.strftime('%d/%m/%Y %H:%M')+' - '+b.strftime('%d/%m/%Y %H:%M')
        cells[f'B{i+8}'] = str(power)
        cells[f'C{i+8}'] = '99999'  # Forecast must never become the actual baseline.
    return cells


class GuiLoadReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = {}
        cls.panels = {}
        for record_id, year in SOURCE_YEARS.items():
            m = _manifest(record_id)
            cells = cells_for_year(year, 100 if year == 2024 else 200)
            cls.cells[record_id] = cells
            records = _parse_cells(cells, record_id=record_id, source_sha256=m['sha256'])
            cls.panels[record_id] = QualifiedGuiLoadPanel(records, (record_id,), (m['sha256'],))
        cls.local = local_2025_reference(cls.panels.values())

    def test_stitch_uses_exact_four_companion_intervals(self):
        rows = self.local.records
        self.assertEqual(len(rows), 35040)
        self.assertEqual(rows[0].timestamp_utc.isoformat(), '2024-12-31T23:00:00+00:00')
        self.assertEqual(rows[-1].interval_end_utc.isoformat(), '2025-12-31T23:00:00+00:00')
        self.assertEqual([r.power_mw for r in rows[:5]], [100]*4+[200])
        self.assertEqual(sum('2024' in r.source_series_id for r in rows), 4)

    def test_forecast_is_ignored_and_source_power_is_not_energy(self):
        summary = reference_summary(self.local)
        self.assertEqual(Decimal(summary['energy_mwh']), Decimal(4*100+35036*200)/4)
        self.assertEqual(summary['peak_mw'], 200)
        self.assertEqual(summary['evidence_status'], 'DER')
        self.assertEqual(summary['evidence_tier'], 'E2_PROVISIONAL_BASE')
        self.assertEqual(summary['public_raw_reuse_status'], 'NOT_ESTABLISHED_FREE_REUSE')
        self.assertIn('NOT_PROGRAMME_RESULT', summary['scope'])

    def test_dst_short_and_long_days_keep_real_intervals(self):
        local = [r.timestamp_utc.astimezone(ZoneInfo('Europe/Budapest')) for r in self.local.records]
        spring = [x for x in local if x.date().isoformat() == '2025-03-30']
        autumn = [x for x in local if x.date().isoformat() == '2025-10-26']
        self.assertEqual(len(spring), 92)
        self.assertEqual(len(autumn), 100)
        repeated = [x for x in autumn if x.hour == 2 and x.minute == 0]
        self.assertEqual(len(repeated), 2)
        self.assertNotEqual(repeated[0].utcoffset(), repeated[1].utcoffset())

    def test_full_2025_winter_is_supported_but_partial_2026_winter_fails(self):
        all_rows = tuple(r for p in self.panels.values() for r in p.records)
        for year in (2025, 2026):
            window = canonical_reporting_window(ReportingWindowKind.METEOROLOGICAL_WINTER, year)
            rows = [r for r in all_rows if window.utc_start <= r.timestamp_utc < window.utc_end]
            if year == 2025:
                self.assertEqual(len(rows), 90*96)
                self.assertEqual(seasonal_peak(rows, window).peak_mw, 200)
            else:
                with self.assertRaises(ValueError):seasonal_peak(rows, window)

    def test_byte_mismatch_fails_before_spreadsheet_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'wrong.xlsx'
            path.write_bytes(b'not the authorized exact source')
            with patch('modules.B08.gui_load_reference._xlsx_cells') as parser:
                with self.assertRaises(ObservedLoadContractError):
                    read_pinned_gui_workbook(path, 'B08B09-P5-R01')
                parser.assert_not_called()

    def test_forecast_area_or_time_header_cannot_be_relabelled(self):
        for field, value in [('B7', 'Day-ahead Total Load Forecast (MW)'), ('B6', 'BZN|DE'),
                             ('A4', '01/01/2025 00:00 - 01/01/2026 00:00 (CET)')]:
            cells = dict(self.cells['B08B09-P5-R01'])
            cells[field] = value
            with self.assertRaises(ObservedLoadContractError):
                _parse_cells(cells, record_id='B08B09-P5-R01', source_sha256='x')

    def test_missing_duplicate_mtu_and_non_quarter_interval_fail(self):
        for mode in ('MISSING', 'DUPLICATE', 'DURATION'):
            cells = dict(self.cells['B08B09-P5-R01'])
            if mode == 'MISSING':del cells['B8']
            elif mode == 'DUPLICATE':cells['A9'] = cells['A8']
            else:cells['A8'] = '01/01/2025 00:00 - 01/01/2025 00:30'
            with self.assertRaises(ObservedLoadContractError):
                _parse_cells(cells, record_id='B08B09-P5-R01', source_sha256='x')

    def test_missing_negative_nonfinite_actuals_fail_not_zero(self):
        for value in ('', '-1', 'NaN', 'Infinity', 'n/e'):
            cells = dict(self.cells['B08B09-P5-R01'])
            cells['B8'] = value
            with self.assertRaises(ObservedLoadContractError):
                _parse_cells(cells, record_id='B08B09-P5-R01', source_sha256='x')

    def test_manifest_may_not_silently_relax_model_use_or_raw_reuse(self):
        for record_id in ('B08B09-P5-R03', 'UNKNOWN'):
            with self.assertRaises(ObservedLoadContractError):_manifest(record_id)
        a, b = self.panels.values()
        for replacement in ({'raw_storage_policy': 'REPOSITORY_ALLOWED'},
                            {'public_raw_reuse_status': 'REUSE_CLEARED'},
                            {'evidence_tier': 'E1'}, {'source_sha256': ('0'*64,)},
                            {'records': a.records[:-1]}):
            with self.assertRaises(ObservedLoadContractError):
                local_2025_reference([replace(a, **replacement), b])

    def test_both_sources_and_original_record_provenance_are_required(self):
        a, b = self.panels.values()
        for panels in ([a], [a, a], [a, b, b]):
            with self.assertRaises(ObservedLoadContractError):local_2025_reference(panels)
        changed = replace(a.records[0], source_revision='UNREVIEWED_REVISION')
        with self.assertRaises(ObservedLoadContractError):
            local_2025_reference([replace(a, records=(changed,)+a.records[1:]), b])


    def test_summary_cannot_promote_scenario_or_other_reuse_status(self):
        first = self.local.records[0]
        scenario = replace(first, truth_context='SCN', evidence_status='SCN')
        with self.assertRaises(ObservedLoadContractError):
            reference_summary(replace(self.local, records=(scenario,)+self.local.records[1:]))
        with self.assertRaises(ObservedLoadContractError):
            reference_summary(replace(self.local, model_use_status='Q'))


    def test_raw_xml_reader_does_not_truncate_at_stale_sheet_dimensions(self):
        xml = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:C19"/><sheetData><row r="35047"><c r="B35047" t="inlineStr"><is><t>123.45</t></is></c></row></sheetData></worksheet>'
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('xl/worksheets/sheet1.xml', xml)
        self.assertEqual(_xlsx_cells(buffer.getvalue())['B35047'], '123.45')

    def test_source_formulas_and_duplicate_cells_are_rejected(self):
        for content in ('<c r="B8"><f>1+1</f><v>2</v></c>',
                        '<c r="B8"><v>2</v></c><c r="B8"><v>3</v></c>'):
            xml = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="8">'+content+'</row></sheetData></worksheet>'
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as archive:
                archive.writestr('xl/worksheets/sheet1.xml', xml)
            with self.assertRaises(ObservedLoadContractError):_xlsx_cells(buffer.getvalue())


    def test_materializer_rejects_public_output_before_reading_sources(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(root/'tools/materialize_b08_gui_load_reference.py'),
                                     '--source-2025', 'missing2025.xlsx', '--source-2024', 'missing2024.xlsx',
                                     '--output-dir', directory], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('complete numeric panel must remain in ignored data/interim', result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])


    def test_energy_is_independent_of_callers_decimal_precision(self):
        expected = reference_summary(self.local)
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(reference_summary(self.local), expected)


class AdversarialStorageTests(unittest.TestCase):
    """Disposable Git fixtures only; rejection must precede source access."""

    def test_storage_boundaries_before_first_source_read(self):
        from contextlib import ExitStack, redirect_stderr
        import io
        import subprocess
        import sys
        from tools import materialize_b08_gui_load_reference as materializer

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
                accepted = case in ('deep_ignored', 'normalized_ignored') or (False and case == 'external_non_git_controlled_metadata')
                guard = materializer.guard_private_output
                if accepted:
                    self.assertEqual(guard(output, root=root), output.resolve())
                else:
                    with self.assertRaises(ValueError):
                        guard(output, root=root)
                argv = ['materializer', *['--source-2025', 'missing-2025.xlsx', '--source-2024', 'missing-2024.xlsx'], '--output-dir', str(output)]
                with patch.object(materializer, 'guard_private_output', side_effect=lambda p: guard(p, root=root)), \
                        patch.object(materializer, 'read_pinned_gui_workbook', side_effect=RuntimeError('FIRST_SOURCE_READ')) as reader, \
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


    def _write_synthetic(self, root, output, *, arrive=None):
        from contextlib import ExitStack, redirect_stdout
        from types import SimpleNamespace
        from tools import materialize_b08_gui_load_reference as materializer

        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = start + timedelta(minutes=15)
        record = SimpleNamespace(timestamp_utc=start, interval_end_utc=end, power_mw=7,
            timestep_hours=0.25, source_refs=('SYNTHETIC_ONLY',),
            source_revision='SYNTHETIC_ONLY', evidence_status='ASS')
        panel = SimpleNamespace(records=(record,), evidence_tier='SYNTHETIC_ONLY',
            acquisition_record_ids=('SYNTHETIC_ONLY',), source_sha256=('0' * 64,))
        window = SimpleNamespace(utc_start=start, utc_end=end)
        peak = SimpleNamespace(peak_mw=7, tied_timestamps_utc=(start,), evidence_status='ASS')
        guard = materializer.guard_private_output
        def read(*args):
            if arrive is not None and not (output / arrive[0]).is_symlink() and not (output / arrive[0]).exists():
                output.mkdir(parents=True, exist_ok=True)
                target = output / arrive[0]
                if arrive[1] == 'symlink':
                    target.symlink_to(root / 'public-sentinel')
                else:
                    target.write_bytes(b'SYNTHETIC_LATE_SENTINEL\n')
            return panel
        with ExitStack() as stack:
            for name, value in {
                'guard_private_output': lambda p: guard(p, root=root),
                'read_pinned_gui_workbook': read,
                'local_2025_reference': lambda panels: panel,
                'reference_summary': lambda panel: {'synthetic_only': True},
                'canonical_reporting_window': lambda *args: window,
                'seasonal_peak': lambda *args: peak,
            }.items():
                stack.enter_context(patch.object(materializer, name, value))
            stack.enter_context(patch.object(sys, 'argv', ['materializer', '--source-2025',
                'synthetic-2025', '--source-2024', 'synthetic-2024', '--output-dir', str(output)]))
            stack.enter_context(redirect_stdout(io.StringIO()))
            materializer.main()

    def test_synthetic_writer_preserves_csv_and_receipt_semantics(self):
        import hashlib
        import json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
            (root / '.gitignore').write_text('/data/interim/\n')
            output = root / 'data/interim/deep/missing/output'
            self._write_synthetic(root, output)
            expected = (
                'start_utc,end_utc,actual_load_mw,timestep_hours,source_id,source_revision,evidence_status,evidence_tier\n'
                '2025-01-01T00:00:00+00:00,2025-01-01T00:15:00+00:00,7,0.25,SYNTHETIC_ONLY,SYNTHETIC_ONLY,ASS,SYNTHETIC_ONLY\n'
            ).encode()
            self.assertEqual((output / 'hu_actual_load_local_2025_pt15m.csv').read_bytes(), expected)
            receipt = json.loads((output / 'receipt.json').read_text())
            self.assertEqual(receipt, {
                'synthetic_only': True,
                'winter_2025': {'intervals': 2, 'start_utc': '2025-01-01T00:00:00+00:00',
                    'end_utc_exclusive': '2025-01-01T00:15:00+00:00', 'peak_mw': 7,
                    'peak_timestamps_utc': ['2025-01-01T00:00:00+00:00'], 'evidence_status': 'ASS'},
                'source_acquisition_record_ids': ['SYNTHETIC_ONLY'], 'source_sha256': ['0' * 64],
                'csv_sha256': hashlib.sha256(expected).hexdigest(),
                'csv_storage_policy': 'EXTERNAL_ONLY_IGNORED_NOT_FOR_PUBLIC_COMMIT',
            })

    def test_exclusive_creation_preserves_targets_arriving_after_preflight(self):
        for name in ('hu_actual_load_local_2025_pt15m.csv', 'receipt.json'):
            for kind in ('file', 'symlink'):
                with self.subTest(name=name, kind=kind), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
                    (root / '.gitignore').write_text('/data/interim/\n')
                    sentinel = root / 'public-sentinel'
                    sentinel.write_bytes(b'SYNTHETIC_PUBLIC_SENTINEL\n')
                    output = root / 'data/interim/fresh'
                    with self.assertRaises(FileExistsError):
                        self._write_synthetic(root, output, arrive=(name, kind))
                    self.assertEqual(sentinel.read_bytes(), b'SYNTHETIC_PUBLIC_SENTINEL\n')
                    if kind == 'symlink':
                        self.assertTrue((output / name).is_symlink())
                    else:
                        self.assertEqual((output / name).read_bytes(), b'SYNTHETIC_LATE_SENTINEL\n')


    def test_git_index_errors_fail_closed_before_source_read(self):
        from contextlib import redirect_stderr
        import io
        import subprocess
        import sys
        from tools import materialize_b08_gui_load_reference as materializer

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
                argv = ['materializer', *['--source-2025', 'missing-2025.xlsx', '--source-2024', 'missing-2024.xlsx'], '--output-dir', str(output)]
                with patch.object(materializer, 'guard_private_output', side_effect=lambda p: guard(p, root=root)), \
                        patch.object(materializer, 'read_pinned_gui_workbook', side_effect=RuntimeError('FIRST_SOURCE_READ')) as reader, \
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
