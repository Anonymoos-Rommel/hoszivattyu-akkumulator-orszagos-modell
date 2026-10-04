"""Synthetic source and real filesystem-policy checks; no FGSZ numeric fixtures."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from modules.B11 import gas_quality_reference as q
from tools import materialize_b11_gas_quality_reference as materializer
from tools.materialize_b13_fiscal_reference import guard_private_output


NS = q.NS


def workbook(points=None, *, year=2024, mutate=None):
    if points is None:
        points = [('Synthetic group', 'SYNTH-GROUP', 'SYNTH-EIC-GROUP', ['12.300000000000001', '12.2', '12.4', '38.0'], 1),
                  ('Synthetic child', 'SYNTH-CHILD', 'SYNTH-EIC-CHILD', ['12.0', '12.1', '12.4', 'N.A'], 2)]
    sheet = ET.Element(f'{{{NS}}}worksheet'); data = ET.SubElement(sheet, f'{{{NS}}}sheetData')
    def row(number, values, fill=0):
        r = ET.SubElement(data, f'{{{NS}}}row', r=str(number))
        for col, value in values.items():
            if value is None:
                continue
            numeric = col in 'EFGH' and number > 2 and value not in ('N.A', '-')
            c = ET.SubElement(r, f'{{{NS}}}c', r=f'{col}{number}', s=str(fill if col == 'A' else 0), t='n' if numeric else 'inlineStr')
            if numeric:
                ET.SubElement(c, f'{{{NS}}}v').text = value
            else:
                ET.SubElement(ET.SubElement(c, f'{{{NS}}}is'), f'{{{NS}}}t').text = value
    row(1, {'A': f'WEIGHTED AVERAGE OF GROSS CALORIFIC VALUE AT EXIT POINTS BASED ON {year} DATA'})
    headers = ['EXIT POINT', 'NETWORK CODE', 'EIC', 'NNO',
               f'{year} Yearly weighted average gross calorific value kWh/m3',
               f'{year} Yearly minimum gross calorific value kWh/m3',
               f'{year} Yearly maximum gross calorific value kWh/m3',
               f'{year} Yearly weighted average net calorific value MJ/m3']
    row(2, dict(zip('ABCDEFGH', headers)))
    for i, (name, code, eic, numbers, fill) in enumerate(points, 3):
        row(i, dict(zip('ABCDEFGH', [name, code, eic, 'Synthetic operator', *numbers])), fill)
    row(len(points) + 4, {'A': 'The net calorific value is informative data'})
    book = f'<workbook xmlns="{NS}" xmlns:r="{q.RID}"><sheets><sheet name="Entry_points" r:id="unused"/><sheet name="Exit_points" r:id="exit"/></sheets></workbook>'
    rel = f'<Relationships xmlns="{q.REL}"><Relationship Id="exit" Type="{q.RID}/worksheet" Target="worksheets/exit.xml"/></Relationships>'
    styles = f'<styleSheet xmlns="{NS}"><numFmts><numFmt numFmtId="164" formatCode="0.000000"/></numFmts><fills><fill><patternFill/></fill><fill><patternFill><fgColor indexed="13"/></patternFill></fill><fill><patternFill><fgColor indexed="42"/></patternFill></fill></fills><cellXfs><xf numFmtId="164" fillId="0"/><xf numFmtId="164" fillId="1"/><xf numFmtId="164" fillId="2"/></cellXfs></styleSheet>'
    files = {'xl/workbook.xml': book.encode(), 'xl/_rels/workbook.xml.rels': rel.encode(),
             'xl/styles.xml': styles.encode(), 'xl/worksheets/exit.xml': ET.tostring(sheet)}
    if mutate:
        mutate(files)
    out = io.BytesIO()
    with ZipFile(out, 'w') as archive:
        for path, raw in files.items():
            archive.writestr(path, raw)
    return out.getvalue()


def descriptor(year=2024, count=2):
    return {'observation_year': year, 'sheet': 'Exit_points', 'source_id': 'SYNTHETIC-SOURCE',
            'artifact_id': 'SYNTHETIC-ARTIFACT', 'expected_rows': count}


def eurostat(kind='hhq', *, mutate=None):
    dataset = {'hhq': 'NRG_D_HHQ', 'balance': 'NRG_BAL_C', 'commodity': 'NRG_CB_GAS'}[kind]
    ends = [q.enduse.TOTAL_END_USE, *q.enduse.END_USES] if kind == 'hhq' else [q.enduse.TOTAL_END_USE]
    units = ['MIO_M3', 'KJ_M3_GCV', 'KJ_M3_NCV', 'TJ_GCV'] if kind == 'commodity' else ['TJ']
    axes = [['A'], ends, ['G3000'], units, ['HU'], ['2024']]
    j = {'class': 'dataset', 'version': '2.0', 'source': 'ESTAT', 'updated': 'SYNTHETIC-VINTAGE',
         'extension': {'id': dataset}, 'id': q.DIMS, 'size': [len(x) for x in axes],
         'dimension': {d: {'category': {'index': dict(zip(axis, range(len(axis))))}} for d, axis in zip(q.DIMS, axes)},
         'value': {'0': 100, '1': 70, '3': 20, '4': 10, '6': 0} if kind == 'hhq' else ({'3': 100} if kind == 'commodity' else {'0': 90}),
         'status': {'1': 'e'} if kind == 'hhq' else {}}
    meta = {'dataset_id': dataset, 'updated': 'SYNTHETIC-VINTAGE', 'units': units, 'evidence_status': 'DER'}
    if mutate:
        mutate(j)
    return json.dumps(j).encode(), meta, {'source_id': 'SYNTHETIC-ESTAT', 'artifact_id': 'SYNTHETIC-ARTIFACT'}


def ksh_html(*, charset='ISO-8859-2', year='2024', consumers='1 000', average='12,3'):
    s = f'''<html><meta charset="{charset}"><table><tr><th>Vezetékes gázt fogyasztó háztartás</th><th>Egy háztartási fogyasztóra jutó évi vezetékes gázfogyasztás, m&sup3;</th></tr><tr><th>{year}</th><td>10</td><td>50,0</td><td>{consumers}</td><td>50,0</td><td>20</td><td>{average}</td></tr></table></html>'''
    return s.encode('iso-8859-2')


class GasQualitySourceTests(unittest.TestCase):
    def test_manifest_pins_originals_and_separates_revision_observation(self):
        m = q.source_manifest(); self.assertEqual(m['reference_id'], q.REFERENCE_ID)
        self.assertEqual(len(m['source_artifacts']), 13)
        old, new = m['panels']
        self.assertEqual((old['observation_year'], old['revision_valid_from'], old['revision_valid_through']), (2024, '2026-04-01', '2026-09-30'))
        self.assertEqual((new['observation_year'], new['revision_valid_from']), (2025, '2026-10-01'))
        pdf = next(a for a in m['source_artifacts'] if a['artifact_id'] == old['authority_artifact_id'])
        self.assertEqual(pdf['source_id'], 'SRC-B11-FGSZ-GAS-QUALITY-RULES-2025-2026')
        self.assertTrue(all(a['repo_snapshot_path'] is None for a in m['source_artifacts']))
        self.assertEqual(len({a['artifact_id'] for a in m['source_artifacts']}), 13)

    def test_incomplete_physical_state_stays_distinct_from_p7(self):
        m = q.source_manifest(); g, n = m['calorific_fields']['E'], m['calorific_fields']['H']
        self.assertEqual((g['unit'], g['calorific_reference_temperature_c'], g['volume_reference_temperature_c']), ('kWh/m3', 25, 0))
        self.assertEqual((n['unit'], n['calorific_reference_temperature_c'], n['volume_reference_temperature_c']), ('MJ/m3', 15, 15))
        self.assertEqual(g['absolute_pressure_pa'], 101325)
        self.assertIsNone(g['moisture_basis']); self.assertIsNone(n['moisture_basis'])
        self.assertIn('INFORMATIVE', n['quantity'])
        self.assertFalse(hasattr(q, 'GasReferenceState'))
        self.assertIsNone(m['methodology_evidence']['balance_guide_2019']['sha256'])

    def test_no_default_scope_or_source_namespace_substitution(self):
        with self.assertRaises(TypeError):
            q.read_gas_quality_reference({})
        for scope in (None, '', '2024', 2024, True, 'NATIONAL', 'CALENDAR_2025_SOURCE_AND_CONTROL_HANDOFF'):
            with self.subTest(scope=scope), self.assertRaises(q.GasQualityReferenceError):
                q.read_gas_quality_reference({}, historical_scope=scope)
        with self.assertRaisesRegex(q.GasQualityReferenceError, 'namespace'):
            q.read_gas_quality_reference({'SYNTHETIC-SOURCE': 'path'}, historical_scope=q.HISTORICAL_SCOPE)

    def test_exact_hash_and_size_both_required(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'bytes'; path.write_bytes(b'synthetic')
            pin = {'byte_count': 9, 'sha256': hashlib.sha256(b'synthetic').hexdigest()}
            self.assertEqual(q._pinned_bytes(path, pin), b'synthetic')
            for change in ({'byte_count': 8}, {'sha256': '0' * 64}):
                with self.assertRaises(q.GasQualityReferenceError):
                    q._pinned_bytes(path, {**pin, **change})

    def test_source_map_duplicate_keys_and_nonpaths_fail(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'map.json'
            for raw in ['{"x":"a","x":"b"}', '{"x":null}', '[]', '{"x":""}']:
                p.write_text(raw)
                with self.assertRaises(q.GasQualityReferenceError): q.source_map(p)

    def test_native_lexeme_precision_missingness_qc_and_overlap_survive(self):
        panel = q._exit_panel(workbook(), descriptor()); group, child = panel['records']
        self.assertEqual(group['quality']['E']['raw'], '12.300000000000001')
        self.assertEqual(group['quality']['E']['displayed'], '12.300000')
        self.assertEqual(group['quality']['E']['displayed_decimal_places'], 6)
        self.assertEqual(child['quality']['H']['raw'], 'N.A')
        self.assertIsNone(child['quality']['H']['displayed'])
        self.assertEqual(child['quality']['H']['evidence_status'], 'Q')
        self.assertIn('PUBLISHED_MEAN_OUTSIDE_PUBLISHED_EXTREMA', child['qc_flags'])
        self.assertEqual(child['source_colour_parent_eic_hint'], group['eic'])
        self.assertFalse(panel['aggregation_authorized']); self.assertFalse(panel['physical_ratio_authorized'])
        self.assertEqual(panel['summary']['numeric_average_pairs'], 1)

    def test_display_general_two_and_five_places_are_not_six_place_defaults(self):
        cell = {'raw': '12.345670000000001', 'cell_type': 'n', 'number_format': 'BUILTIN:0'}
        general = q._quality_cell(cell)
        self.assertEqual(general['availability'], 'PRESENT'); self.assertIsNone(general['displayed'])
        self.assertEqual(q._quality_cell({**cell, 'number_format': 'BUILTIN:4'})['displayed'], '12.35')
        self.assertEqual(q._quality_cell({**cell, 'number_format': '#,##0.00000'})['displayed'], '12.34567')

    def test_binary_serialization_tails_do_not_create_extrema_failure(self):
        pts = [('Synthetic point', 'SYNTH-CODE', 'SYNTH-EIC', ['12.299999999999999', '12.3', '12.3', '38'], 0)]
        p = q._exit_panel(workbook(pts), descriptor(count=1))
        self.assertNotIn('PUBLISHED_MEAN_OUTSIDE_PUBLISHED_EXTREMA', p['records'][0]['qc_flags'])

    def test_missing_extrema_do_not_drop_numeric_average_pair(self):
        pts = [('Synthetic virtual MGP', 'SYNTH-CODE', 'SYNTH-EIC', ['12', '-', '-', '38'], 0)]
        p = q._exit_panel(workbook(pts), descriptor(count=1))
        self.assertEqual(p['summary']['numeric_average_pairs'], 1)
        self.assertEqual(p['summary']['complete_four_numeric_fields'], 0)
        self.assertEqual(p['records'][0]['nonresidential_name_cues'], ['VIRTUAL'])

    def test_blank_cell_remains_distinct_from_source_missing_marker(self):
        pts = [('Synthetic point', 'SYNTH-CODE', 'SYNTH-EIC', [None, 'N.A', '-', None], 0)]
        r = q._exit_panel(workbook(pts), descriptor(count=1))['records'][0]
        self.assertEqual(r['quality']['E']['cell_type'], 'ABSENT')
        self.assertEqual(r['quality']['F']['raw'], 'N.A'); self.assertEqual(r['quality']['G']['raw'], '-')

    def test_year_headers_sheet_namespace_and_coverage_fail_closed(self):
        for desc in ({**descriptor(), 'observation_year': 2025}, {**descriptor(), 'sheet': 'Entry_points'}, {**descriptor(), 'expected_rows': 3}):
            with self.assertRaises(q.GasQualityReferenceError): q._exit_panel(workbook(), desc)
        def change(files):
            files['xl/worksheets/exit.xml'] = files['xl/worksheets/exit.xml'].replace(NS.encode(), b'urn:other')
        with self.assertRaises(q.GasQualityReferenceError): q._exit_panel(workbook(mutate=change), descriptor())

    def test_2025_panel_has_own_observation_identity(self):
        p = q._exit_panel(workbook(year=2025), descriptor(year=2025))
        self.assertTrue(all(r['observation_year'] == 2025 for r in p['records']))

    def test_duplicate_point_and_network_identity_fail(self):
        for duplicate in ('eic', 'network'):
            pts = [('Synthetic first', 'ONE', 'FIRST', ['12', '11', '13', '38'], 0),
                   ('Synthetic second', 'ONE' if duplicate == 'network' else 'TWO', 'FIRST' if duplicate == 'eic' else 'SECOND', ['12', '11', '13', '38'], 0)]
            with self.assertRaises(q.GasQualityReferenceError): q._exit_panel(workbook(pts), descriptor())

    def test_duplicate_cell_row_and_formula_fail(self):
        for mode in ('cell', 'row', 'formula'):
            def change(files):
                tree = ET.fromstring(files['xl/worksheets/exit.xml']); data = tree.find(f'{{{NS}}}sheetData'); row = data[2]
                if mode == 'cell': row.append(deepcopy(row[0]))
                elif mode == 'row': data.append(deepcopy(row))
                else: ET.SubElement(row[4], f'{{{NS}}}f').text = '1+1'
                files['xl/worksheets/exit.xml'] = ET.tostring(tree)
            with self.subTest(mode=mode), self.assertRaises(q.GasQualityReferenceError):
                q._exit_panel(workbook(mutate=change), descriptor())

    def test_external_relationship_and_entity_rejected(self):
        for mode in ('external', 'traversal', 'entity'):
            def change(files):
                key = 'xl/_rels/workbook.xml.rels'; text = files[key]
                if mode == 'external': text = text.replace(b'Target=', b'TargetMode="External" Target=')
                elif mode == 'traversal': text = text.replace(b'worksheets/exit.xml', b'../exit.xml')
                else: text = b'<!DOCTYPE x [<!ENTITY x "bad">]>' + text
                files[key] = text
            with self.subTest(mode=mode), self.assertRaises(q.GasQualityReferenceError):
                q._exit_panel(workbook(mutate=change), descriptor())

    def test_unidentified_values_and_missing_qualification_rejected(self):
        def change(files):
            tree = ET.fromstring(files['xl/worksheets/exit.xml']); data = tree.find(f'{{{NS}}}sheetData'); data[2].remove(data[2][2]);files['xl/worksheets/exit.xml'] = ET.tostring(tree)
        with self.assertRaises(q.GasQualityReferenceError): q._exit_panel(workbook(mutate=change), descriptor())
        def strip(files):
            files['xl/worksheets/exit.xml'] = files['xl/worksheets/exit.xml'].replace(b'The net calorific value is informative data', b'Synthetic unrelated text')
        with self.assertRaises(q.GasQualityReferenceError): q._exit_panel(workbook(mutate=strip), descriptor())

    def test_quality_nonfinite_negative_zero_and_text_are_not_source_numbers(self):
        for value in ('NaN', 'Infinity', '-1', '0', 'unexpected'):
            cell = {'raw': value, 'cell_type': 'n', 'number_format': '0.000000'}
            with self.subTest(value=value), self.assertRaises(q.GasQualityReferenceError): q._quality_cell(cell)
        with self.assertRaises(q.GasQualityReferenceError):
            q._quality_cell({'raw': '12', 'cell_type': 's', 'number_format': '0.000000'})

    def test_eurostat_preserves_status_missing_zero_and_decimal_lexeme(self):
        raw, meta, artifact = eurostat(); raw = raw.replace(b'"0": 100', b'"0": 100.000')
        p = q._eurostat(raw, meta, artifact); rows = p['records']
        self.assertEqual(rows[0]['raw_value'], '100.000'); self.assertEqual(rows[1]['source_status'], 'e')
        self.assertEqual(rows[2]['native_value_state'], 'ABSENT'); self.assertIsNone(rows[2]['raw_value'])
        self.assertEqual(rows[6]['raw_value'], '0'); self.assertEqual(rows[6]['evidence_status'], 'DER')
        self.assertEqual(rows[2]['evidence_status'], 'Q')

    def test_eurostat_explicit_null_is_preserved(self):
        raw, meta, artifact = eurostat(mutate=lambda j: j['value'].update({'2': None}))
        self.assertEqual(q._eurostat(raw, meta, artifact)['records'][2]['native_value_state'], 'NULL')

    def test_eurostat_rejects_wrong_identity_period_units_population_and_vintage(self):
        for change in (lambda j: j.update(updated='OTHER'), lambda j: j['extension'].update(id='OTHER'),
                       lambda j: j.update(source='OTHER'), lambda j: j['dimension']['time']['category'].update(index={'2025': 0}),
                       lambda j: j['dimension']['siec']['category'].update(index={'TOTAL': 0}),
                       lambda j: j['dimension']['unit']['category'].update(index={'TJ_GCV': 0}),
                       lambda j: j['dimension']['geo']['category'].update(index={'DE': 0})):
            raw, meta, artifact = eurostat(mutate=change)
            with self.assertRaises(q.GasQualityReferenceError): q._eurostat(raw, meta, artifact)

    def test_eurostat_index_alias_duplicate_and_bad_values_fail(self):
        changes = [lambda j: j['value'].update({'00': 5}), lambda j: j['status'].update({'99': 'e'}),
                   lambda j: j['value'].update({'0': True}), lambda j: j['value'].update({'0': -1}),
                   lambda j: j['value'].update({'0': 'NaN'}), lambda j: j['status'].update({'0': None}),
                   lambda j: j['dimension']['freq']['category'].update(index={'A': True}), lambda j: j.update(size=[1])]
        for change in changes:
            with self.assertRaises(q.GasQualityReferenceError): q._eurostat(*eurostat(mutate=change))
        raw, meta, artifact = eurostat(); raw = raw.replace(b'"0": 100', b'"0": 100,"0": 101')
        with self.assertRaises(q.GasQualityReferenceError): q._eurostat(raw, meta, artifact)

    def test_commodity_keeps_missing_volume_and_calorific_units(self):
        p = q._eurostat(*eurostat('commodity'))
        self.assertEqual([r['coordinates']['unit'] for r in p['records']], ['MIO_M3', 'KJ_M3_GCV', 'KJ_M3_NCV', 'TJ_GCV'])
        self.assertEqual([r['availability'] for r in p['records']], ['MISSING'] * 3 + ['PRESENT'])

    def test_ksh_declared_charset_native_lexemes_and_annual_header(self):
        row = q._ksh_annual_average(ksh_html())
        self.assertEqual(row['charset'], 'ISO-8859-2'); self.assertEqual(row['native_cells'][6], '12,3')
        self.assertEqual(row['annual_m3_per_consumer'], '12.3'); self.assertEqual(row['volume_reference_state'], 'UNKNOWN')
        for raw in (ksh_html(charset='UTF-8'), ksh_html(year='2025'), ksh_html(average='..'),
                    ksh_html().replace('évi'.encode('iso-8859-2'), 'havi'.encode('iso-8859-2'))):
            with self.assertRaises(q.GasQualityReferenceError): q._ksh_annual_average(raw)

    def test_reconciliation_preserves_missing_and_never_activates_calibration(self):
        c = {key: q._eurostat(*eurostat(key)) for key in ('hhq', 'balance', 'commodity')}
        c.update(ksh_annual_average={'household_consumers': '1000', 'annual_m3_per_consumer': '12.3'},
                 county={'national_household_consumers': 1000, 'national_household_sales_thousand_m3': 10})
        result = q._reconcile(c)
        self.assertEqual(result['ksh_annual_average_implied_minus_sales_m3'], '2300.0')
        self.assertEqual(result['known_present_end_use_residual_tj'], '0')
        self.assertFalse(result['complete_end_use_closure']); self.assertFalse(result['missing_is_zero'])
        self.assertEqual(result['diagnostic_090_status'], 'STATISTICAL_SERIES_ONLY_NOT_PHYSICAL_RATIO')
        self.assertIsNone(result['physical_calorific_mean']); self.assertIsNone(result['national_displacement'])
        c['ksh_annual_average']['household_consumers'] = '1001'
        with self.assertRaises(q.GasQualityReferenceError): q._reconcile(c)

    def test_source_arithmetic_is_ambient_decimal_context_independent(self):
        baseline = q._exit_panel(workbook(), descriptor())
        c = {key: q._eurostat(*eurostat(key)) for key in ('hhq', 'balance', 'commodity')}
        c.update(ksh_annual_average={'household_consumers': '1000', 'annual_m3_per_consumer': '12.3456789'},
                 county={'national_household_consumers': 1000, 'national_household_sales_thousand_m3': 10})
        expected = q._reconcile(c)
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(q._exit_panel(workbook(), descriptor()), baseline)
            self.assertEqual(q._reconcile(c), expected)


class GasQualityPrivateStorageTests(unittest.TestCase):
    def private_temporary_directory(self):
        parent = q.ROOT / 'data/interim'
        parent.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=parent)

    def git(self, root, *args):
        return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)

    def test_real_guard_private_mode_and_no_overwrite(self):
        with self.private_temporary_directory() as td:
            output = Path(td) / 'fresh'
            materializer._write_receipt(b'{"synthetic": true}\n', output)
            self.assertEqual(stat.S_IMODE((output / 'receipt.json').stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
            with self.assertRaises(ValueError): materializer._write_receipt(b'overwrite', output)
            self.assertEqual((output / 'receipt.json').read_bytes(), b'{"synthetic": true}\n')

    def test_invalid_input_does_not_create_output(self):
        with self.private_temporary_directory() as td:
            output = Path(td) / 'fresh'
            with self.assertRaises(q.GasQualityReferenceError):
                materializer.materialize({}, historical_scope=q.HISTORICAL_SCOPE, output_dir=output)
            self.assertFalse(output.exists())

    def test_real_guard_rejects_symlink_ancestor_and_existing_directory(self):
        with self.private_temporary_directory() as td:
            root = Path(td); (root / 'real').mkdir(); (root / 'alias').symlink_to(root / 'real', target_is_directory=True)
            with self.assertRaises(ValueError): guard_private_output(root / 'alias' / 'fresh')
            with self.assertRaises(q.GasQualityReferenceError): materializer._write_receipt(b'{}', root / 'real')

    def test_real_guard_rejects_external_checkout_and_nested_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self.git(root, 'init', '-q')
            with self.assertRaises(ValueError): guard_private_output(root / 'fresh')
            (root / '.gitignore').write_text('/data/interim/\n')
            nested = root / 'data/interim/nested'; nested.mkdir(parents=True); self.git(nested, 'init', '-q')
            with self.assertRaises(ValueError): guard_private_output(nested / 'fresh', root=root)

    def test_real_guard_requires_ignored_untracked_repo_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self.git(root, 'init', '-q'); (root / '.gitignore').write_text('/data/interim/\n')
            self.assertEqual(guard_private_output(root / 'data/interim/fresh', root=root), root / 'data/interim/fresh')
            with self.assertRaises(ValueError): guard_private_output(root / 'public/fresh', root=root)
            p = root / 'data/interim/tracked'; p.mkdir(parents=True); (p / 'receipt.json').write_text('{}')
            self.git(root, 'add', '-f', 'data/interim/tracked/receipt.json'); (p / 'receipt.json').unlink()
            with self.assertRaises(ValueError): guard_private_output(p, root=root)
            (root / '.gitignore').write_text('')
            with self.assertRaises(ValueError): guard_private_output(root / 'data/interim/unignored', root=root)

    def test_real_guard_rejects_git_marker_file_and_nondirectory_ancestor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / '.git').write_text('gitdir: /nonexistent')
            with self.assertRaises(ValueError): guard_private_output(root / 'fresh')
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'file'; p.write_text('x')
            with self.assertRaises(ValueError): guard_private_output(p / 'fresh')


if __name__ == '__main__':
    unittest.main()
