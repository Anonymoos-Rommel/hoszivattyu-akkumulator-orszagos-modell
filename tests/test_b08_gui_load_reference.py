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


if __name__ == '__main__':
    unittest.main()
