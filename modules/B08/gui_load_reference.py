"""Hash-pinned P5 GUI load reuse with qualified E2 model-use boundaries.

This source-specific adapter does not change the older XML/OBS reuse gate.
Workbook bytes and the full numeric panel must remain external-only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from .observed_load_contract import (
    CONTROL_AREA_SCHEME, ENTSOE_SOURCE_ID, HUNGARY_CONTROL_AREA,
    ObservedLoadContractError, ObservedLoadRecord,
)
from .seasonal_reporting_contract import (
    ReportingWindowKind, canonical_reporting_window, seasonal_peak,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b08_b09_p5_entsoe_gui_export_acquisition.csv'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
SOURCE_YEARS = {'B08B09-P5-R01': 2025, 'B08B09-P5-R02': 2024}
SOURCE_ROLES = {'B08B09-P5-R01': 'OBSERVED_LOAD_BASELINE',
                'B08B09-P5-R02': 'LOCAL_YEAR_BOUNDARY_COMPANION'}
STEP = timedelta(minutes=15)


@dataclass(frozen=True)
class QualifiedGuiLoadPanel:
    records: tuple[ObservedLoadRecord, ...]
    acquisition_record_ids: tuple[str, ...]
    source_sha256: tuple[str, ...]
    evidence_tier: str = 'E2_PROVISIONAL_BASE'
    model_use_status: str = 'QUALIFIED_E2_MODEL_USE'
    raw_storage_policy: str = 'EXTERNAL_ONLY'
    public_raw_reuse_status: str = 'NOT_ESTABLISHED_FREE_REUSE'


def _manifest(record_id):
    if record_id not in SOURCE_YEARS:
        raise ObservedLoadContractError('only the two approved P5 load exports are supported')
    with MANIFEST.open(encoding='utf-8', newline='') as handle:
        matches = [r for r in csv.DictReader(handle) if r['record_id'] == record_id]
    if len(matches) != 1:
        raise ObservedLoadContractError('exactly one acquisition manifest row required')
    m = matches[0]
    expected = {'module_id': 'B08', 'artifact_role': SOURCE_ROLES[record_id],
                'source_product': 'Actual Total Load [6.1.A]', 'spatial_grain': 'BZN|HU',
                'resolution': 'PT15M', 'raw_storage_policy': 'EXTERNAL_ONLY',
                'model_use_status': 'QUALIFIED_E2_MODEL_USE',
                'public_raw_reuse_status': 'NOT_ESTABLISHED_FREE_REUSE',
                'current_state': 'ACQUIRED_COMPLETE_UTC_YEAR', 'missing_value_cells': '0'}
    if any(m.get(k) != v for k, v in expected.items()):
        raise ObservedLoadContractError('P5 source identity/model-use boundary changed; review required')
    return m


def _xlsx_cells(content):
    """Read text/numeric cells without spreadsheet evaluation or dependencies."""
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(x.itertext()) for x in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    cells = {}
    for c in sheet.findall('m:sheetData/m:row/m:c', NS):
        ref = c.get('r')
        if not ref or not re.fullmatch(r'[A-Z]+[1-9][0-9]*', ref) or ref in cells:
            raise ObservedLoadContractError('missing/duplicate/invalid source cell address')
        if c.find('m:f', NS) is not None:
            raise ObservedLoadContractError('source formulas are not evaluated')
        kind = c.get('t')
        if kind == 'inlineStr':
            value = ''.join(t.text or '' for t in c.findall('m:is//m:t', NS))
        else:
            v = c.find('m:v', NS)
            value = '' if v is None else (v.text or '')
            if kind == 's':
                value = shared[int(value)]
            elif kind not in (None, 'n') and value:
                raise ObservedLoadContractError('unsupported source cell type')
        cells[ref] = value.strip()
    return cells


def _parse_cells(cells, *, record_id, source_sha256):
    """Private source parser; canonical admission also requires the byte gate."""
    year = SOURCE_YEARS[record_id]
    headers = {'A1': 'Total Load - Day-ahead / Actual', 'A2': 'Actual Total Load [6.1.A]',
               'A3': 'Day-ahead Total Load Forecast [6.1.B]',
               'A4': f'01/01/{year} 00:00 - 01/01/{year+1} 00:00 (UTC)',
               'A6': 'MTU', 'B6': 'BZN|HU', 'C6': 'BZN|HU', 'A7': 'MTU',
               'B7': 'Actual Total Load (MW)', 'C7': 'Day-ahead Total Load Forecast (MW)'}
    if any(cells.get(k) != v for k, v in headers.items()):
        raise ObservedLoadContractError('GUI source header/area/actual-vs-forecast boundary mismatch')
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year+1, 1, 1, tzinfo=timezone.utc)
    count = int((end-start)/STEP)
    expected_refs = {f'{column}{n}' for column in 'ABC' for n in range(8, count+8)}
    data_refs = {ref for ref in cells if int(re.sub('[A-Z]', '', ref)) >= 8}
    if data_refs != expected_refs:
        raise ObservedLoadContractError('complete source row/cell grid required; blanks are not zero')
    records = []
    for n in range(count):
        row = n+8
        ts = start+n*STEP
        finish = ts+STEP
        expected_mtu = ts.strftime('%d/%m/%Y %H:%M')+' - '+finish.strftime('%d/%m/%Y %H:%M')
        if cells[f'A{row}'] != expected_mtu:
            raise ObservedLoadContractError('source MTU gap, duplicate, ordering or duration mismatch')
        try:
            power = Decimal(cells[f'B{row}'])
        except (InvalidOperation, ValueError) as exc:
            raise ObservedLoadContractError('explicit finite actual load required') from exc
        if not power.is_finite() or power < 0:
            raise ObservedLoadContractError('actual load must be finite and nonnegative')
        records.append(ObservedLoadRecord(
            source_series_id='P5_GUI_ACTUAL_TOTAL_LOAD_'+str(year),
            timestamp_utc=ts, interval_end_utc=finish, timestep_hours=0.25,
            power_mw=float(power), region_id=HUNGARY_CONTROL_AREA,
            region_scheme=CONTROL_AREA_SCHEME, source_time_basis='UTC',
            interval_convention='INTERVAL_START', truth_context='REAL',
            evidence_status='DER', source_refs=(ENTSOE_SOURCE_ID,),
            source_revision=record_id+':'+source_sha256,
        ))
    return tuple(records)


def read_pinned_gui_workbook(path: Path, record_id: str) -> QualifiedGuiLoadPanel:
    """Reuse the existing E2 admission only after verifying the exact workbook."""
    path = Path(path)
    m = _manifest(record_id)
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != m['sha256'] or len(content) != int(m['bytes']):
        raise ObservedLoadContractError('exact P5 source bytes/hash required; no silent revision adoption')
    records = _parse_cells(_xlsx_cells(content), record_id=record_id, source_sha256=digest)
    if len(records) != int(m['data_rows']):
        raise ObservedLoadContractError('source row count differs from acquisition manifest')
    return QualifiedGuiLoadPanel(records, (record_id,), (digest,))


def local_2025_reference(panels) -> QualifiedGuiLoadPanel:
    """Source-native local-year stitch, with no interpolation or downscaling."""
    panels = tuple(panels)
    if len(panels) != 2 or {p.acquisition_record_ids for p in panels} != {(x,) for x in SOURCE_YEARS}:
        raise ObservedLoadContractError('both distinct P5 calendar exports are required')
    for p in panels:
        record_id = p.acquisition_record_ids[0]
        m = _manifest(record_id)
        if (p.source_sha256 != (m['sha256'],) or p.model_use_status != 'QUALIFIED_E2_MODEL_USE'
                or p.raw_storage_policy != 'EXTERNAL_ONLY' or p.evidence_tier != 'E2_PROVISIONAL_BASE'
                or p.public_raw_reuse_status != 'NOT_ESTABLISHED_FREE_REUSE'):
            raise ObservedLoadContractError('qualified external-only P5 provenance required')
        year = SOURCE_YEARS[record_id]
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        if len(p.records) != int(m['data_rows']):
            raise ObservedLoadContractError('source panel was truncated before stitching')
        for i, r in enumerate(p.records):
            if (r.timestamp_utc != start+i*STEP or r.interval_end_utc != start+(i+1)*STEP
                    or r.timestep_hours != 0.25 or r.evidence_status != 'DER'
                    or r.truth_context != 'REAL' or r.source_refs != (ENTSOE_SOURCE_ID,)
                    or r.source_revision != record_id+':'+m['sha256']):
                raise ObservedLoadContractError('source panel provenance or interval changed')
    window = canonical_reporting_window(ReportingWindowKind.CALENDAR_YEAR, 2025)
    records = tuple(sorted((r for p in panels for r in p.records
                            if window.utc_start <= r.timestamp_utc < window.utc_end),
                           key=lambda r: r.timestamp_utc))
    seasonal_peak(records, window)  # Existing complete-window consumer verifies the handoff.
    ordered = sorted(panels, key=lambda p: p.acquisition_record_ids)
    return QualifiedGuiLoadPanel(records, tuple(p.acquisition_record_ids[0] for p in ordered),
                                 tuple(p.source_sha256[0] for p in ordered))


def reference_summary(panel: QualifiedGuiLoadPanel):
    expected_ids = tuple(sorted(SOURCE_YEARS))
    expected_hashes = tuple(_manifest(x)['sha256'] for x in expected_ids)
    revisions = {i+':'+h for i, h in zip(expected_ids, expected_hashes)}
    if (panel.acquisition_record_ids != expected_ids or panel.source_sha256 != expected_hashes
            or panel.evidence_tier != 'E2_PROVISIONAL_BASE'
            or panel.model_use_status != 'QUALIFIED_E2_MODEL_USE'
            or panel.raw_storage_policy != 'EXTERNAL_ONLY'
            or panel.public_raw_reuse_status != 'NOT_ESTABLISHED_FREE_REUSE'
            or len(panel.records) != 35040):
        raise ObservedLoadContractError('summary requires the qualified complete 2025 local-year handoff')
    if any(r.truth_context != 'REAL' or r.evidence_status != 'DER'
           or r.source_refs != (ENTSOE_SOURCE_ID,) or r.source_revision not in revisions
           or r.timestep_hours != 0.25 for r in panel.records):
        raise ObservedLoadContractError('summary must preserve P5 source and DER evidence boundary')
    window = canonical_reporting_window(ReportingWindowKind.CALENDAR_YEAR, 2025)
    peak = seasonal_peak(panel.records, window)
    with localcontext() as context:
        context.prec = 40
        energy = sum((Decimal(str(r.power_mw))*Decimal('0.25') for r in panel.records), Decimal(0))
    return {'intervals': len(panel.records), 'start_utc': window.utc_start.isoformat(),
            'end_utc_exclusive': window.utc_end.isoformat(), 'energy_mwh': str(energy),
            'peak_mw': peak.peak_mw, 'peak_timestamps_utc': [t.isoformat() for t in peak.tied_timestamps_utc],
            'evidence_status': 'DER', 'evidence_tier': panel.evidence_tier,
            'model_use_status': panel.model_use_status, 'raw_storage_policy': panel.raw_storage_policy,
            'scope': 'HISTORICAL_NATIONAL_CONTROL_AREA_LOAD_BASELINE_NOT_PROGRAMME_RESULT',
            'public_raw_reuse_status': panel.public_raw_reuse_status}
