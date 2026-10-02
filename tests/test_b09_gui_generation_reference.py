"""Synthetic-only adapter/guard tests; no external numeric panel is committed."""
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from modules.B09 import gui_generation_reference as gui
from modules.B09.engine import GENERATION_BOUNDARY, SIGNED_NET_GENERATION_BOUNDARY
from modules.B09.signed_net_recovery_contract import materialize_recovered_generation_panel
from tools.materialize_b09_gui_generation_reference import guard_private_output

STRUCTURAL = {'Energy storage', 'Fossil Coal-derived gas', 'Fossil Oil shale',
              'Fossil Peat', 'Hydro Pumped Storage', 'Marine', 'Wind Offshore'}
ACTIVE = {name: code for name, code in gui.PSR_CODES.items() if name not in STRUCTURAL}
NE = {name: gui.PSR_CODES[name] for name in STRUCTURAL}
NAMES = sorted(gui.PSR_CODES)
HASH = sorted(gui.MAVIR_OPERATIONAL_SHA256)[0]
SYNTHETIC_ARTIFACT = gui.SourceArtifact(gui.GENERATION_ID, gui.ENTSOE_SOURCE_ID,
                                      'synthetic.xlsx', '0' * 64, 1, 2)


def capacity_rows():
    rows = [(1, {1: 'Installed Capacity per Production Type'}),
            (2, {1: 'Installed Generation Capacity Aggregated [14.1.A]'}),
            (3, {1: '01/01/2025 - 01/01/2026'}),
            (5, {1: 'Production Type', 2: 'BZN|HU'}),
            (6, {1: 'Production Type', 2: '2025 (MW)'})]
    rows.extend((i + 7, {1: name, 2: 'n/e' if name in NE else '1'}) for i, name in enumerate(NAMES))
    rows.append((28, {1: 'Total Grand Capacity', 2: '14'}))
    return rows


def generation_rows(count=2):
    rows = [(1, {1: 'Actual Generation per Production Type - Generation'}),
            (2, {1: 'Aggregated Generation per Type [16.1.B&C]'}),
            (3, {1: '01/01/2025 00:00 - 01/01/2026 00:00 (UTC)'}),
            (5, {1: 'MTU', **{i + 2: 'BZN|HU' for i in range(len(NAMES))}}),
            (6, {1: 'MTU', **{i + 2: name + ' (MW)' for i, name in enumerate(NAMES)}})]
    for n in range(count):
        start = gui.START + n * gui.STEP
        label = start.strftime('%d/%m/%Y %H:%M:%S') + ' - ' + (start + gui.STEP).strftime('%d/%m/%Y %H:%M:%S')
        rows.append((7 + n, {1: label, **{i + 2: 'n/e' if name in NE else '1.25' for i, name in enumerate(NAMES)}}))
    return rows


def parse_generation(rows):
    return gui._parse_generation(rows, ACTIVE, NE, SYNTHETIC_ARTIFACT,
                                 start=gui.START, end=gui.START + 2 * gui.STEP)


def operational_rows(start=gui.START, count=2):
    rows = [(1, dict(enumerate(gui.MAVIR_HEADERS, 1)))]
    for n in range(count):
        label = (start + (n + 1) * gui.STEP).strftime('%Y.%m.%d %H:%M:%S +0000')
        rows.append((n + 2, {1: label, **{c: '1' for c in range(2, len(gui.MAVIR_HEADERS) + 1)}}))
    return rows


def op_artifact(record_id=gui.OPERATIONAL_IDS[0], count=2):
    return gui.SourceArtifact(record_id, gui.MAVIR_NET_OPERATIONAL_SOURCE_ID,
                              'synthetic-op.xlsx', HASH, 1, count)


def workbook(path, rows, *, cell_mutation=None, sheet_name='1', shared=None):
    ns = gui.NS['m']
    root = ET.Element('worksheet', xmlns=ns)
    ET.SubElement(root, 'dimension', ref='A1:A1')  # Deliberately stale.
    data = ET.SubElement(root, 'sheetData')
    for n, values in rows:
        row = ET.SubElement(data, 'row', r=str(n))
        for col, text in values.items():
            cell = ET.SubElement(row, 'c', r=gui._column_name(col) + str(n), t='inlineStr')
            ET.SubElement(ET.SubElement(cell, 'is'), 't').text = text
            if cell_mutation:
                cell_mutation(cell)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="{gui.REL_NS}"><sheets><sheet name="{sheet_name}" r:id="rId1"/></sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', f'<Relationships><Relationship Id="rId1" Type="{gui.REL_NS}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr('xl/worksheets/sheet1.xml', ET.tostring(root, encoding='utf-8'))
        if shared is not None:
            archive.writestr('xl/sharedStrings.xml', shared)
    content = path.read_bytes()
    return replace(SYNTHETIC_ARTIFACT, sha256=hashlib.sha256(content).hexdigest(), byte_count=len(content))


class SourceAuthorityTests(unittest.TestCase):
    def test_existing_six_source_pins_and_qualified_policy(self):
        artifacts = gui.source_artifacts()
        self.assertEqual(tuple(a.acquisition_record_id for a in artifacts), gui.SOURCE_IDS)
        self.assertEqual({a.sha256 for a in artifacts[2:]}, gui.MAVIR_OPERATIONAL_SHA256)

    def test_manifest_policy_mapping_hash_and_identity_drift_fail_closed(self):
        base = json.loads(gui.REFERENCE_MANIFEST.read_text())
        for mutate in (
            lambda m: m.update(model_use_status='OBS'),
            lambda m: m.update(raw_storage_policy='REPOSITORY_ALLOWED'),
            lambda m: m.update(public_raw_reuse_status='REUSE_CLEARED'),
            lambda m: m['psr_codes'].update({'Fossil Gas': 'B05'}),
            lambda m: m['source_artifacts'][0].update(sha256='0' * 64),
            lambda m: m['source_artifacts'][0].update(source_id='OTHER_SOURCE'),
            lambda m: m['source_artifacts'].pop(),
        ):
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                manifest = copy.deepcopy(base)
                mutate(manifest)
                path = Path(directory) / 'manifest.json'
                path.write_text(json.dumps(manifest))
                with patch.object(gui, 'REFERENCE_MANIFEST', path), self.assertRaises(ValueError):
                    gui.source_artifacts()

    def test_p7_runtime_gate_cannot_be_bypassed(self):
        original = gui._registry
        def changed(path):
            rows = original(path)
            if Path(path).name == 'b09_p7_signed_net_generation_semantics.csv':
                rows['B09-P7-R07']['status'] = 'BLOCKED'
            return rows
        with patch.object(gui, '_registry', side_effect=changed), self.assertRaises(ValueError):
            gui.source_artifacts()

    def test_exact_source_id_path_set_required(self):
        with self.assertRaisesRegex(ValueError, 'exactly the six'):
            gui.read_pinned_gui_generation_reference({})

    def test_psr_mapping_retains_b11_spelling_and_b25_storage(self):
        self.assertEqual(gui.PSR_CODES['Hydro Run-of-river and pondage'], 'B11')
        self.assertEqual(gui.PSR_CODES['Energy storage'], 'B25')
        self.assertEqual(set(gui.RECOVERY_COLUMNS), {'B04', 'B06', 'B12'})


class StreamingWorkbookTests(unittest.TestCase):
    def test_stale_dimensions_and_whitespace_blanks_do_not_truncate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.xlsx'
            artifact = workbook(path, [(1, {1: 'first'}), (100, {22: ' \t '})])
            self.assertEqual(list(gui._xlsx_rows(path, artifact, '1')), [(1, {1: 'first'}), (100, {22: ''})])

    def test_byte_and_hash_mutation_rejected_before_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.xlsx'
            artifact = workbook(path, [(1, {1: 'first'})])
            for changed in (replace(artifact, byte_count=1), replace(artifact, sha256='0' * 64)):
                with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'bytes/hash'):
                    list(gui._xlsx_rows(path, changed, '1'))

    def test_formula_error_boolean_bad_address_and_duplicate_row_rejected(self):
        def formula(c):
            ET.SubElement(c, 'f').text = '1+1'
        for mutate in (formula, lambda c: c.set('t', 'b'), lambda c: c.set('t', 'e'),
                       lambda c: c.set('r', 'A2'), lambda c: c.set('r', 'BAD')):
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'source.xlsx'
                artifact = workbook(path, [(1, {1: 'x'})], cell_mutation=mutate)
                with self.assertRaises(ValueError):
                    list(gui._xlsx_rows(path, artifact, '1'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.xlsx'
            artifact = workbook(path, [(1, {1: 'x'}), (1, {1: 'x'})])
            with self.assertRaisesRegex(ValueError, 'source row'):
                list(gui._xlsx_rows(path, artifact, '1'))

    def test_wrong_sheet_identity_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.xlsx'
            artifact = workbook(path, [(1, {1: 'x'})], sheet_name='wrong')
            with self.assertRaisesRegex(ValueError, 'worksheet identity'):
                list(gui._xlsx_rows(path, artifact, '1'))

    def test_shared_strings_supported_with_bounds_checks(self):
        def shared_cell(c):
            c.clear()
            c.set('r', 'A1')
            c.set('t', 's')
            ET.SubElement(c, 'v').text = '0'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.xlsx'
            artifact = workbook(path, [(1, {1: 'unused'})], cell_mutation=shared_cell,
                                shared=f'<sst xmlns="{gui.NS["m"]}"><si><t> shared </t></si></sst>')
            self.assertEqual(list(gui._xlsx_rows(path, artifact, '1')), [(1, {1: 'shared'})])
            artifact = workbook(path, [(1, {1: 'unused'})], cell_mutation=shared_cell)
            with self.assertRaisesRegex(ValueError, 'shared-string'):
                list(gui._xlsx_rows(path, artifact, '1'))


class CapacityAndGenerationTests(unittest.TestCase):
    def test_installed_capacity_defines_types_and_excludes_total_footer(self):
        active, ne = gui._parse_capacity(capacity_rows())
        self.assertEqual(active, ACTIVE)
        self.assertEqual(ne, NE)
        self.assertNotIn('Total Grand Capacity', active)

    def test_capacity_zero_is_numeric_not_structural_absence(self):
        rows = capacity_rows()
        rows[5][1][2] = '0'
        self.assertIn(rows[5][1][1], gui._parse_capacity(rows)[0])

    def test_bad_capacity_manifest_footer_category_and_numeric_value(self):
        for mutate in (lambda rows: rows.pop(),
                       lambda rows: rows[-1][1].update({1: 'unknown total'}),
                       lambda rows: rows[5][1].update({1: 'unknown type'}),
                       lambda rows: rows[5][1].update({2: ''}),
                       lambda rows: rows[5][1].update({2: '-1'}),
                       lambda rows: rows[3][1].update({2: 'BZN|AT'})):
            rows = capacity_rows()
            mutate(rows)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                gui._parse_capacity(rows)

    def test_numeric_zero_and_positive_values_are_retained_as_q(self):
        rows = generation_rows()
        rows[-2][1][NAMES.index('Fossil Oil') + 2] = '0.00'
        records, missing, columns = parse_generation(rows)
        self.assertEqual(len(records), 28)
        self.assertEqual(missing, {})
        self.assertEqual(len(columns), 21)
        oil = next(r for r in records if r.production_type_code == 'B06')
        self.assertEqual(oil.power_mw, 0)
        self.assertTrue(all(r.evidence_status == 'Q' and r.source_semantics == gui.SOURCE_SEMANTICS for r in records))
        self.assertTrue(all(r.production_type_code not in NE.values() for r in records))

    def test_blank_active_cell_is_exposed_for_exact_recovery(self):
        rows = generation_rows()
        col = NAMES.index('Fossil Gas') + 2
        rows[-2][1][col] = ' \t '
        records, missing, _ = parse_generation(rows)
        self.assertEqual(missing, {('B04', gui.START): gui._column_name(col) + '7'})
        self.assertIsNone(next(r.power_mw for r in records if r.production_type_code == 'B04'))

    def test_absent_row_cell_wrong_time_and_duplicate_type_fail_closed(self):
        for mutate in (
            lambda rows: rows.pop(),
            lambda rows: rows[-1][1].pop(2),
            lambda rows: rows[-1][1].update({1: rows[-2][1][1]}),
            lambda rows: rows[4][1].update({2: rows[4][1][3]}),
            lambda rows: rows[3][1].update({2: 'CTA|HU'}),
            lambda rows: rows[0][1].update({1: 'Actual Generation per Production Type - Consumption'}),
            lambda rows: rows[4][1].update({2: 'Biomass (kW)'}),
        ):
            rows = generation_rows()
            mutate(rows)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                parse_generation(rows)

    def test_active_ne_nonfinite_negative_or_unvalidated_blank_fail_closed(self):
        for value in ('n/e', 'NaN', 'Infinity', '-0.1', ''):
            rows = generation_rows()
            rows[-2][1][NAMES.index('Biomass') + 2] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_generation(rows)

    def test_structural_ne_cannot_become_zero_or_blank(self):
        for value in ('0', ''):
            rows = generation_rows()
            rows[-1][1][NAMES.index('Energy storage') + 2] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_generation(rows)


class OperationalAndRecoveryTests(unittest.TestCase):
    def test_explicit_offset_interval_end_conversion_at_dst_boundaries(self):
        self.assertEqual(gui._mavir_start('2025.01.01 01:15:00 +0100'), gui.START)
        fall_a = gui._mavir_start('2025.10.26 02:15:00 +0200')
        fall_b = gui._mavir_start('2025.10.26 02:15:00 +0100')
        self.assertEqual((fall_b - fall_a).total_seconds(), 3600)
        spring_a = gui._mavir_start('2025.03.30 01:45:00 +0100')
        spring_b = gui._mavir_start('2025.03.30 03:00:00 +0200')
        self.assertEqual(spring_b - spring_a, gui.STEP)

    def test_naive_or_invalid_timestamps_rejected(self):
        for label in ('2025.01.01 01:15:00', '2025.02.30 01:15:00 +0100', '2025.01.01 01:15:00 UTC'):
            with self.subTest(label=label), self.assertRaises(ValueError):
                gui._mavir_start(label)

    def test_identical_overlaps_keep_all_source_locators(self):
        panel = {}
        for record_id in gui.OPERATIONAL_IDS[:2]:
            gui._merge_operational(operational_rows(), op_artifact(record_id), panel,
                                   start=gui.START, end=gui.START + 2 * gui.STEP)
        self.assertEqual(len(panel), 2)
        self.assertEqual(len(panel[gui.START][1]), 2)

    def test_conflict_in_even_nonrecovery_mavir_column_rejected(self):
        panel = {}
        gui._merge_operational(operational_rows(), op_artifact(), panel)
        rows = operational_rows()
        rows[1][1][2] = '2'  # Whole-row sum, not a recovery column.
        with self.assertRaisesRegex(ValueError, 'conflicting full MAVIR'):
            gui._merge_operational(rows, op_artifact(gui.OPERATIONAL_IDS[1]), panel)

    def test_duplicate_artifact_timestamp_rejected(self):
        panel = {}
        gui._merge_operational(operational_rows(), op_artifact(), panel)
        with self.assertRaisesRegex(ValueError, 'duplicate MAVIR'):
            gui._merge_operational(operational_rows(), op_artifact(), panel)

    def test_missing_numeric_wrong_count_grid_and_header_rejected(self):
        for mutate in (lambda rows: rows[1][1].pop(5),
                       lambda rows: rows[1][1].update({5: ' '}),
                       lambda rows: rows[1][1].update({5: 'NaN'}),
                       lambda rows: rows[1][1].update({1: '2025.01.01 00:16:00 +0000'}),
                       lambda rows: rows[-1][1].update({1: rows[1][1][1]}),
                       lambda rows: rows[0][1].update({5: 'wrong basis column'}),
                       lambda rows: rows.pop()):
            rows = operational_rows()
            mutate(rows)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                gui._merge_operational(rows, op_artifact(), {})

    def test_half_open_filter_precedes_irrelevant_numeric_payload_validation(self):
        start = gui.END - gui.STEP
        rows = operational_rows(start=start)
        rows[-1] = (3, {1: rows[-1][1][1]})  # Timestamp-only terminal row outside 2025.
        panel = {}
        gui._merge_operational(rows, op_artifact(), panel, start=start, end=gui.END)
        self.assertEqual(set(panel), {start})

    def test_p7_consumer_called_and_sign_and_numeric_precedence_retained(self):
        rows = generation_rows()
        rows[-2][1][NAMES.index('Fossil Gas') + 2] = ' '
        a75, missing, _ = parse_generation(rows)
        operations = {}
        ops = operational_rows()
        ops[1][1][5] = '-1.125'
        ops[2][1][5] = '9999'  # Must never replace the numeric A75 gas cell.
        artifact = op_artifact()
        gui._merge_operational(ops, artifact, operations)
        with patch.object(gui, 'materialize_recovered_generation_panel', wraps=materialize_recovered_generation_panel) as consumer:
            panel, lineage = gui._recover(a75, missing, ACTIVE.values(), operations, (artifact,),
                                          start=gui.START, end=gui.START + 2 * gui.STEP)
        consumer.assert_called_once()
        gas = [r for r in panel.records if r.source_component_id == 'ENTSOE_PSR_B04']
        self.assertEqual(gas[0].net_generation_contribution_kw, -1125)
        self.assertEqual(gas[0].source_withdrawal_kw, 1125)
        self.assertEqual(gas[0].delivered_generation_kw, 0)
        self.assertEqual(gas[0].boundary_id, SIGNED_NET_GENERATION_BOUNDARY)
        self.assertEqual(gas[1].delivered_generation_kw, 1250)
        self.assertEqual(gas[1].boundary_id, GENERATION_BOUNDARY)
        self.assertTrue(all(r.evidence_status == 'Q' for r in panel.records))
        self.assertEqual(lineage[0].signed_power_mw, Decimal('-1.125'))
        self.assertEqual(lineage[0].operational_cells, ((artifact.acquisition_record_id, 'E2'),))
        self.assertEqual(lineage[0].selected_source_sha256, artifact.sha256)

    def test_incomplete_operational_window_fails_before_recovery(self):
        a75, missing, _ = parse_generation(generation_rows())
        with self.assertRaisesRegex(ValueError, 'complete MAVIR UTC'):
            gui._recover(a75, missing, ACTIVE.values(), {}, (), start=gui.START,
                         end=gui.START + 2 * gui.STEP)


class StorageGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('/data/interim/\n')

    def test_only_new_ignored_data_interim_output_allowed(self):
        output = self.root / 'data/interim/reference'
        self.assertEqual(guard_private_output(output, root=self.root), output)
        for bad in (self.root / 'data/raw/ref', self.root / 'registry', self.root.parent / 'ref'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                guard_private_output(bad, root=self.root)

    def test_ignore_policy_cannot_be_removed_or_bypassed(self):
        (self.root / '.gitignore').write_text('')
        with self.assertRaisesRegex(ValueError, 'untracked and covered'):
            guard_private_output(self.root / 'data/interim/reference', root=self.root)

    def test_existing_file_or_symlink_cannot_be_overwritten(self):
        output = self.root / 'data/interim/reference'
        output.mkdir(parents=True)
        target = output / 'receipt.json'
        target.write_text('existing')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            guard_private_output(output, root=self.root)
        target.unlink()
        target.symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            guard_private_output(output, root=self.root)

    def test_symlinked_private_root_and_output_escape_rejected(self):
        (self.root / 'data').mkdir()
        (self.root / 'elsewhere').mkdir()
        (self.root / 'data/interim').symlink_to(self.root / 'elsewhere', target_is_directory=True)
        with self.assertRaises(ValueError):
            guard_private_output(self.root / 'data/interim/reference', root=self.root)

    def test_tracked_output_is_rejected_even_if_ignored(self):
        output = self.root / 'data/interim/reference'
        output.mkdir(parents=True)
        target = output / 'receipt.json'
        target.write_text('tracked')
        subprocess.run(['git', 'add', '--force', str(target)], cwd=self.root, check=True)
        target.unlink()
        with self.assertRaisesRegex(ValueError, 'untracked and covered'):
            guard_private_output(output, root=self.root)


class AdversarialStorageTests(unittest.TestCase):
    """Disposable Git fixtures only; rejection must precede source access."""

    def test_storage_boundaries_before_first_source_read(self):
        from contextlib import ExitStack, redirect_stderr
        import io
        import subprocess
        import sys
        from tools import materialize_b09_gui_generation_reference as materializer

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
                argv = ['materializer', *['--source-dir', 'missing-sources'], '--output-dir', str(output)]
                with patch.object(materializer, 'guard_private_output', side_effect=lambda p: guard(p, root=root)), \
                        patch.object(materializer, 'read_pinned_gui_generation_reference', side_effect=RuntimeError('FIRST_SOURCE_READ')) as reader, \
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


    def test_git_index_errors_fail_closed_before_source_read(self):
        from contextlib import redirect_stderr
        import io
        import subprocess
        import sys
        from tools import materialize_b09_gui_generation_reference as materializer

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
                argv = ['materializer', *['--source-dir', 'missing-sources'], '--output-dir', str(output)]
                with patch.object(materializer, 'guard_private_output', side_effect=lambda p: guard(p, root=root)), \
                        patch.object(materializer, 'read_pinned_gui_generation_reference', side_effect=RuntimeError('FIRST_SOURCE_READ')) as reader, \
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
