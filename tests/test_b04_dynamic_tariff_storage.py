"""Private-output boundary checks using disposable Git and synthetic records only."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from modules.B04.dynamic_tariff import PriceInterval
from tools import materialize_b04_dynamic_tariff as tool


class DynamicTariffStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('/data/interim/\n')
        self.private = self.root / 'data/interim'
        self.private.mkdir(parents=True)
        self.output = self.private / 'missing/deep/output'
        self.guard = tool.guard_private_output

    def git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.root,
                              capture_output=True, text=True, check=True)

    def assert_rejected_before_source_read(self, output):
        entries = sorted(str(p.relative_to(self.base)) for p in self.base.rglob('*'))
        with self.assertRaises(ValueError):
            self.guard(output, root=self.root)
        with patch.object(tool, 'guard_private_output',
                          side_effect=lambda p: self.guard(p, root=self.root)), \
                patch.object(Path, 'read_bytes', side_effect=AssertionError('source read')) as rb, \
                patch.object(Path, 'read_text', side_effect=AssertionError('manifest read')) as rt, \
                patch.object(sys, 'argv', ['materializer', '--pdf', 'missing.pdf',
                                          '--output-dir', str(output)]), \
                redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                tool.main()
            self.assertEqual(error.exception.code, 2)
            rb.assert_not_called()
            rt.assert_not_called()
        self.assertEqual(sorted(str(p.relative_to(self.base)) for p in self.base.rglob('*')), entries)

    def test_deep_and_normalized_ignored_paths_are_accepted_without_writes(self):
        for output in (self.output, self.private / 'missing/../fresh', self.private):
            with self.subTest(output=output):
                self.assertEqual(self.guard(output, root=self.root), output.resolve())
        self.assertFalse(self.output.exists())

    def test_public_external_and_traversal_outputs_reject_before_source(self):
        for output in (self.root / 'public', self.base / 'outside',
                       self.private / '../../public'):
            with self.subTest(output=output):
                self.assert_rejected_before_source_read(output)

    def test_both_existing_outputs_reject_without_overwrite(self):
        for name in tool.OUTPUT_NAMES:
            with self.subTest(name=name):
                output = self.private / name.replace('.', '_')
                output.mkdir()
                target = output / name
                target.write_bytes(b'SYNTHETIC_EXISTING_SENTINEL\n')
                self.assert_rejected_before_source_read(output)
                self.assertEqual(target.read_bytes(), b'SYNTHETIC_EXISTING_SENTINEL\n')
                self.assertEqual(list(output.iterdir()), [target])

    def test_both_output_symlinks_existing_and_dangling_are_rejected(self):
        for name in tool.OUTPUT_NAMES:
            for existing in (True, False):
                with self.subTest(name=name, existing=existing):
                    output = self.private / (name + str(existing))
                    output.mkdir()
                    destination = self.root / ('public-' + name + str(existing))
                    if existing:
                        destination.write_bytes(b'SYNTHETIC_PUBLIC_SENTINEL\n')
                    target = output / name
                    target.symlink_to(destination)
                    self.assert_rejected_before_source_read(output)
                    self.assertTrue(target.is_symlink())
                    if existing:
                        self.assertEqual(destination.read_bytes(), b'SYNTHETIC_PUBLIC_SENTINEL\n')
                    else:
                        self.assertFalse(destination.exists())

    def test_symlinked_output_ancestors_and_private_root_reject(self):
        for location in ('private', 'public', 'missing'):
            with self.subTest(location=location):
                destination = self.private / 'real' if location == 'private' else self.root / location
                if location != 'missing':
                    destination.mkdir()
                link = self.private / ('link-' + location)
                link.symlink_to(destination, target_is_directory=True)
                self.assert_rejected_before_source_read(link / 'deep/output')
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'data').mkdir()
            (root / 'real').mkdir()
            (root / 'data/interim').symlink_to(root / 'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                self.guard(root / 'data/interim/output', root=root)

    def test_nested_git_directory_file_and_dangling_markers_reject(self):
        for kind in ('directory', 'file', 'dangling'):
            with self.subTest(kind=kind):
                nested = self.private / kind
                nested.mkdir()
                marker = nested / '.git'
                if kind == 'directory':
                    self.git('init', '--quiet', str(nested))
                elif kind == 'file':
                    marker.write_text('gitdir: /SYNTHETIC_NONEXISTENT\n')
                else:
                    marker.symlink_to(self.base / 'absent-git')
                self.assert_rejected_before_source_read(nested)
                self.assert_rejected_before_source_read(nested / 'missing/deep/output')

    def test_real_nested_worktree_rejects_before_source(self):
        # Seed a disposable Git commit; no configured user identity or remote is used.
        self.git('add', '.gitignore')
        self.git('-c', 'user.name=Synthetic Test', '-c', 'user.email=synthetic@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'Synthetic fixture')
        nested = self.private / 'worktree'
        self.git('worktree', 'add', '--quiet', '--detach', str(nested))
        self.assertTrue((nested / '.git').is_file())
        self.assert_rejected_before_source_read(nested / 'missing/output')

    def test_both_tracked_deleted_targets_reject(self):
        for name in tool.OUTPUT_NAMES:
            with self.subTest(name=name):
                output = self.private / name.replace('.', '_')
                output.mkdir()
                target = output / name
                target.write_bytes(b'SYNTHETIC_INDEX_SENTINEL\n')
                self.git('add', '--force', '--', str(target))
                target.unlink()
                self.assert_rejected_before_source_read(output)
                self.git('ls-files', '--error-unmatch', '--', str(target.relative_to(self.root)))

    def test_missing_ignore_and_git_errors_fail_closed(self):
        (self.root / '.gitignore').write_text('')
        self.assert_rejected_before_source_read(self.output)
        for codes in ((128, 0), (1, 128), (0, 0)):
            with self.subTest(codes=codes), patch.object(tool.subprocess, 'run',
                    side_effect=[subprocess.CompletedProcess([], code) for code in codes]):
                with self.assertRaises(ValueError):
                    self.guard(self.output, root=self.root)

    def synthetic_run(self, *, during_parse=None, late_open=None, bad_hash=False, bad_count=False):
        pdf = self.root / 'synthetic.pdf'
        pdf.write_bytes(b'SYNTHETIC_NOT_A_SOURCE_DOCUMENT\n')
        manifest = {'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    'start_date_local': '2025-09-01', 'end_date_local_exclusive': '2025-09-02',
                    'source_id': 'SYNTHETIC_ONLY', 'expected_intervals': 1,
                    'expected_negative_net_prices': 1}
        if bad_hash:
            manifest['sha256'] = '0' * 64
        if bad_count:
            manifest['expected_intervals'] = 2
        registry = self.root / 'registry'
        registry.mkdir(exist_ok=True)
        (registry / 'b04_dynamic_tariff_panel_manifest.json').write_text(json.dumps(manifest))
        start = datetime(2025, 9, 1, tzinfo=timezone.utc)
        row = PriceInterval(start, start + timedelta(minutes=15), Decimal('-1.25'), 'SYNTHETIC_ONLY')
        real_run, real_open = subprocess.run, Path.open
        calls = []
        def run(args, **kwargs):
            if args[0] == 'pdftotext':
                calls.append(args)
                return subprocess.CompletedProcess(args, 0, stdout='SYNTHETIC_TEXT')
            return real_run(args, **kwargs)
        def parse(*args):
            if during_parse:
                during_parse()
            return [row]
        def opening(path, mode='r', *args, **kwargs):
            if late_open and path == self.output / late_open[0] and mode == 'x':
                destination = self.root / 'late-public-sentinel'
                destination.write_bytes(b'SYNTHETIC_LATE_SENTINEL\n')
                if late_open[1] == 'symlink':
                    path.symlink_to(destination)
                else:
                    with real_open(path, 'wb') as handle:
                        handle.write(b'SYNTHETIC_LATE_SENTINEL\n')
            return real_open(path, mode, *args, **kwargs)
        with ExitStack() as stack:
            stack.enter_context(patch.object(tool, 'ROOT', self.root))
            stack.enter_context(patch.object(tool, 'guard_private_output',
                side_effect=lambda p: self.guard(p, root=self.root)))
            stack.enter_context(patch.object(tool.subprocess, 'run', side_effect=run))
            stack.enter_context(patch.object(tool, 'parse_mvm_table', side_effect=parse))
            stack.enter_context(patch.object(Path, 'open', opening))
            stack.enter_context(patch.object(sys, 'argv', ['materializer', '--pdf', str(pdf),
                                      '--output-dir', str(self.output)]))
            stack.enter_context(redirect_stdout(io.StringIO()))
            stack.enter_context(redirect_stderr(io.StringIO()))
            tool.main()
        return manifest, calls

    def test_synthetic_writer_preserves_csv_and_receipt(self):
        manifest, calls = self.synthetic_run()
        self.assertEqual(len(calls), 1)
        target = self.output / tool.OUTPUT_NAMES[0]
        expected = ('start_utc,end_utc,net_energy_huf_per_kwh,source_id,evidence_status\n'
                    '2025-09-01T00:00:00+00:00,2025-09-01T00:15:00+00:00,-1.25,SYNTHETIC_ONLY,SCN_PUBLISHED_RETROSPECTIVE_D_TARIFF\n')
        self.assertEqual(target.read_text(), expected)
        receipt = json.loads((self.output / 'receipt.json').read_text())
        self.assertEqual(receipt, {'source_id': 'SYNTHETIC_ONLY', 'source_sha256': manifest['sha256'],
            'csv_sha256': hashlib.sha256(expected.encode()).hexdigest(), 'intervals': 1,
            'negative_net_prices': 1, 'first_utc': '2025-09-01T00:00:00+00:00',
            'end_utc_exclusive': '2025-09-01T00:15:00+00:00',
            'status': 'SCN_EXTERNAL_ONLY_MATERIALIZED_NOT_NATIONAL_INPUT_CLOSURE'})

    def test_source_hash_and_panel_reconciliation_remain_fail_closed(self):
        for kwargs in ({'bad_hash': True}, {'bad_count': True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SystemExit) as error:
                self.synthetic_run(**kwargs)
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(self.output.exists())

    def test_second_guard_rejects_receipt_arriving_during_parse(self):
        def arrive():
            self.output.mkdir(parents=True)
            (self.output / 'receipt.json').write_bytes(b'SYNTHETIC_LATE_RECEIPT\n')
        with self.assertRaises(SystemExit):
            self.synthetic_run(during_parse=arrive)
        self.assertFalse((self.output / tool.OUTPUT_NAMES[0]).exists())
        self.assertEqual((self.output / 'receipt.json').read_bytes(), b'SYNTHETIC_LATE_RECEIPT\n')

    def test_second_guard_rejects_output_directory_symlink_arriving_during_parse(self):
        destination = self.root / 'public'
        destination.mkdir()
        def arrive():
            self.output.parent.mkdir(parents=True)
            self.output.symlink_to(destination, target_is_directory=True)
        with self.assertRaises(SystemExit):
            self.synthetic_run(during_parse=arrive)
        self.assertEqual(list(destination.iterdir()), [])

    def test_exclusive_csv_and_receipt_creation_preserves_late_targets(self):
        for name in tool.OUTPUT_NAMES:
            for kind in ('file', 'symlink'):
                with self.subTest(name=name, kind=kind):
                    self.output = self.private / (name + '-' + kind)
                    with self.assertRaises(FileExistsError):
                        self.synthetic_run(late_open=(name, kind))
                    self.assertEqual((self.output / name).read_bytes(), b'SYNTHETIC_LATE_SENTINEL\n')
                    self.assertEqual((self.root / 'late-public-sentinel').read_bytes(), b'SYNTHETIC_LATE_SENTINEL\n')
                    if name == tool.OUTPUT_NAMES[0]:
                        self.assertFalse((self.output / 'receipt.json').exists())


if __name__ == '__main__':
    unittest.main()
