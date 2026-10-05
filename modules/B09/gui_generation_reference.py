"""External-only, hash-pinned reuse of the existing B09 P5/P6/P7 authority.

The GUI is a production-only source, with the provider-estimate caveat retained.
This adapter does not mint OBS, change XML reuse gates, or infer absent types.
The full numeric panel and recovery-cell lineage belong only in ignored storage.
"""
from __future__ import annotations

import csv
import hashlib
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping

from modules.B08.observed_load_contract import CONTROL_AREA_SCHEME, HUNGARY_CONTROL_AREA
from modules.B09.engine import GENERATION_BOUNDARY, SIGNED_NET_GENERATION_BOUNDARY
from modules.B09.observed_generation_contract import (
    ENTSOE_SOURCE_ID, SOURCE_SEMANTICS, ObservedGenerationRecord,
)
from modules.B09.signed_net_recovery_contract import (
    MAVIR_NET_OPERATIONAL_SOURCE_ID, MAVIR_OPERATIONAL_SHA256,
    RecoveredGenerationPanel, SignedNetRecoveryRecord,
    materialize_recovered_generation_panel,
)

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_MANIFEST = ROOT / 'registry/b09_gui_reference_manifest.json'
P5_REGISTRY = ROOT / 'registry/b08_b09_p5_entsoe_gui_export_acquisition.csv'
P6_REGISTRY = ROOT / 'registry/b09_p6_mavir_operational_acquisition.csv'
STEP = timedelta(minutes=15)
START = datetime(2025, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 1, 1, tzinfo=timezone.utc)
GENERATION_ID = 'B08B09-P5-R03'
CAPACITY_ID = 'B08B09-P5-R04'
OPERATIONAL_IDS = tuple(f'B09-P6-OP{i:02d}' for i in range(1, 5))
SOURCE_IDS = (GENERATION_ID, CAPACITY_ID, *OPERATIONAL_IDS)
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PSR_CODES = {
    'Biomass': 'B01', 'Fossil Brown coal/Lignite': 'B02',
    'Fossil Coal-derived gas': 'B03', 'Fossil Gas': 'B04',
    'Fossil Hard coal': 'B05', 'Fossil Oil': 'B06', 'Fossil Oil shale': 'B07',
    'Fossil Peat': 'B08', 'Geothermal': 'B09', 'Hydro Pumped Storage': 'B10',
    'Hydro Run-of-river and pondage': 'B11', 'Hydro Water Reservoir': 'B12',
    'Marine': 'B13', 'Nuclear': 'B14', 'Other renewable': 'B15', 'Solar': 'B16',
    'Waste': 'B17', 'Wind Offshore': 'B18', 'Wind Onshore': 'B19',
    'Other': 'B20', 'Energy storage': 'B25',
}
MAVIR_HEADERS = (
    'Időpont', 'Hazai termelés (erőművi szumma)', 'Nukleáris erőművek',
    'Barnakőszén-lignit erőművek', 'Gáz (fosszilis) erőművek',
    'Feketekőszén erőművek', 'Olaj (fosszilis) erőművek',
    'Szárazföldi szélerőművek', 'Biomassza erőművek', 'Ipari PV',
    'Szemétégető erőművek', 'Folyóvizes erőművek', 'Víztározós vízerőművek',
    'Egyéb megújuló erőművek', 'Egyéb erőművek',
)
RECOVERY_COLUMNS = {'B04': 5, 'B06': 7, 'B12': 13}  # One-based XLSX columns.


class GuiGenerationReferenceError(ValueError):
    """The pinned source, semantic, evidence or storage boundary did not pass."""


@dataclass(frozen=True)
class SourceArtifact:
    acquisition_record_id: str
    source_id: str
    external_filename: str
    sha256: str
    byte_count: int
    data_rows: int
    first_interval_start_utc: str = ''
    last_interval_start_utc: str = ''


@dataclass(frozen=True)
class RecoveryCellLineage:
    timestamp_utc: datetime
    production_type_code: str
    a75_cell: str
    signed_power_mw: Decimal
    # All identical copies are retained; the first acquisition ID is the winner.
    operational_cells: tuple[tuple[str, str], ...]
    selected_source_sha256: str


@dataclass(frozen=True)
class QualifiedGuiGenerationReference:
    recovered_panel: RecoveredGenerationPanel
    artifacts: tuple[SourceArtifact, ...]
    active_production_types: tuple[str, ...]
    structural_ne_types: tuple[str, ...]
    a75_columns: tuple[tuple[str, int], ...]
    recovery_lineage: tuple[RecoveryCellLineage, ...]
    numeric_a75_cells_preserved: int
    mavir_overlapped_timestamps: int
    evidence_tier: str = field(default='E2_PROVISIONAL_BASE', init=False)
    model_use_status: str = field(default='QUALIFIED_E2_MODEL_USE', init=False)
    raw_storage_policy: str = field(default='EXTERNAL_ONLY', init=False)
    public_raw_reuse_status: str = field(default='NOT_ESTABLISHED_FREE_REUSE', init=False)
    source_semantics: str = field(default=SOURCE_SEMANTICS, init=False)
    request_start_utc: datetime = field(default=START, init=False)
    request_end_utc: datetime = field(default=END, init=False)

    @property
    def records(self):
        return self.recovered_panel.records


def _registry(path):
    with Path(path).open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    keys = [row['record_id'] for row in rows]
    if len(keys) != len(set(keys)):
        raise GuiGenerationReferenceError('duplicate acquisition/authority record ID')
    return dict(zip(keys, rows))


def _require_fields(row, fields, context):
    if any(row.get(key) != value for key, value in fields.items()):
        raise GuiGenerationReferenceError(f'{context} authority changed; review required')


def source_artifacts() -> tuple[SourceArtifact, ...]:
    """Check current P5/P6/P7 authority, not just the new adapter's metadata."""
    contract = json.loads(REFERENCE_MANIFEST.read_text(encoding='utf-8'))
    _require_fields(contract, {
        'model_use_status': 'QUALIFIED_E2_MODEL_USE', 'raw_storage_policy': 'EXTERNAL_ONLY',
        'evidence_tier': 'E2_PROVISIONAL_BASE',
        'public_raw_reuse_status': 'NOT_ESTABLISHED_FREE_REUSE',
        'source_semantics': SOURCE_SEMANTICS,
    }, 'reference')
    if contract['psr_codes'] != PSR_CODES:
        raise GuiGenerationReferenceError('source-label/PSR mapping changed')
    p5, p6 = _registry(P5_REGISTRY), _registry(P6_REGISTRY)
    for record_id, role, product, status, resolution in (
        (GENERATION_ID, 'OBSERVED_GENERATION_PANEL',
         'Actual Generation per Production Type [16.1.B&C]', 'PARTIAL_FAIL_CLOSED', 'PT15M'),
        (CAPACITY_ID, 'EXPECTED_PRODUCTION_TYPE_MANIFEST',
         'Installed Generation Capacity Aggregated [14.1.A]', 'QUALIFIED_MANIFEST_SUPPORT', 'YEAR'),
    ):
        _require_fields(p5.get(record_id, {}), {
            'module_id': 'B09', 'artifact_role': role, 'source_product': product,
            'spatial_grain': 'BZN|HU', 'resolution': resolution,
            'raw_storage_policy': 'EXTERNAL_ONLY', 'model_use_status': status,
            'public_raw_reuse_status': 'NOT_ESTABLISHED_FREE_REUSE',
            'expected_numeric_series': '14', 'structural_ne_series': '7',
        }, record_id)
    p7 = _registry(ROOT / 'registry/b09_p7_signed_net_generation_semantics.csv')
    for i in range(1, 7):
        _require_fields(p7.get(f'B09-P7-R{i:02d}', {}), {'status': 'EXECUTABLE'}, 'P7 runtime')
    _require_fields(p7.get('B09-P7-R07', {}), {'status': 'QUALIFIED_MODEL_USE'}, 'P7 evidence')
    with (ROOT / 'registry/project_blocker_evidence_audit.csv').open(encoding='utf-8', newline='') as handle:
        blockers = [r for r in csv.DictReader(handle) if r['blocker_id'] == 'Q-B09-001']
    if len(blockers) != 1:
        raise GuiGenerationReferenceError('exactly one Q-B09-001 authority required')
    # CSV authority retains its own literal field names and cannot be promoted here.
    _require_fields(blockers[0], {'evidence_tier': 'E2', 'model_blocker': 'no',
                                 'canonical_use': 'MODEL_CONTINUE'}, 'Q-B09-001')
    artifacts = []
    pins = contract['source_artifacts']
    if [pin['acquisition_record_id'] for pin in pins] != list(SOURCE_IDS):
        raise GuiGenerationReferenceError('exact six existing source artifacts required')
    for pin in pins:
        record_id = pin['acquisition_record_id']
        row = (p5 if record_id in (GENERATION_ID, CAPACITY_ID) else p6)[record_id]
        expected_source_id = (ENTSOE_SOURCE_ID if record_id == GENERATION_ID else
                              'SRC-B09-ENTSOE-INSTALLED-CAPACITY-2025' if record_id == CAPACITY_ID else
                              MAVIR_NET_OPERATIONAL_SOURCE_ID)
        if pin['source_id'] != expected_source_id:
            raise GuiGenerationReferenceError('source identity changed for an acquisition record')
        _require_fields(row, {'sha256': pin['sha256'], 'bytes': str(pin['bytes']),
                              'raw_storage_policy': 'EXTERNAL_ONLY'}, record_id)
        if record_id in OPERATIONAL_IDS:
            _require_fields(row, {'canonical_2025_subset': 'INCLUDED_FILTER_2025_HALF_OPEN'}, record_id)
            if row['sha256'] not in MAVIR_OPERATIONAL_SHA256:
                raise GuiGenerationReferenceError('source hash is outside the P7 recovery admission')
        artifacts.append(SourceArtifact(
            record_id, pin['source_id'], row['external_filename'], row['sha256'], int(row['bytes']),
            int(row['data_rows'] if record_id in (GENERATION_ID, CAPACITY_ID) else row['raw_data_rows']),
            row.get('first_interval_start_utc', ''), row.get('last_interval_start_utc', ''),
        ))
    return tuple(artifacts)


def _column_name(column):
    result = ''
    while column:
        column, remainder = divmod(column - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell_value(cell, shared):
    if cell.find('m:f', NS) is not None:
        raise GuiGenerationReferenceError('source formulas are not evaluated')
    kind = cell.get('t')
    if kind == 'inlineStr':
        return ''.join(t.text or '' for t in cell.findall('m:is//m:t', NS)).strip()
    element = cell.find('m:v', NS)
    value = '' if element is None else (element.text or '')
    if kind == 's':
        if not re.fullmatch(r'\d+', value) or int(value) >= len(shared):
            raise GuiGenerationReferenceError('invalid shared-string reference')
        return shared[int(value)].strip()
    if kind not in (None, 'n'):
        raise GuiGenerationReferenceError('unsupported source cell type')
    return value.strip()


def _xlsx_rows(path, artifact, sheet_name):
    """Yield actual XML rows, ignoring stale dimension hints, with bounded XML memory.

    Hashing and ZIP parsing use the same open file. No workbook evaluation and no
    whole-sheet tree (the admitted A75 sheet alone is about 162 MB uncompressed).
    """
    with Path(path).open('rb') as handle:
        digest = hashlib.sha256()
        byte_count = 0
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
            byte_count += len(chunk)
        if byte_count != artifact.byte_count or digest.hexdigest() != artifact.sha256:
            raise GuiGenerationReferenceError('exact source bytes/hash required; no silent revision adoption')
        handle.seek(0)
        with zipfile.ZipFile(handle) as archive:
            workbook = ET.fromstring(archive.read('xl/workbook.xml'))
            sheets = workbook.findall('m:sheets/m:sheet', NS)
            if len(sheets) != 1 or sheets[0].get('name') != sheet_name:
                raise GuiGenerationReferenceError('unexpected source worksheet identity')
            relation_id = sheets[0].get(f'{{{REL_NS}}}id')
            relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
            targets = [e for e in relationships if e.get('Id') == relation_id]
            if (len(targets) != 1 or targets[0].get('TargetMode') == 'External'
                    or targets[0].get('Type') != REL_NS + '/worksheet'):
                raise GuiGenerationReferenceError('invalid source worksheet relationship')
            sheet_path = posixpath.normpath(posixpath.join('xl', targets[0].get('Target', '')))
            if not sheet_path.startswith('xl/worksheets/') or not sheet_path.endswith('.xml'):
                raise GuiGenerationReferenceError('invalid source worksheet path')
            shared = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                with archive.open('xl/sharedStrings.xml') as stream:
                    for event, element in ET.iterparse(stream, events=('start', 'end')):
                        if event == 'start' and element.tag == f"{{{NS['m']}}}sst":
                            shared_root = element
                        elif event == 'end' and element.tag == f"{{{NS['m']}}}si":
                            shared.append(''.join(t.text or '' for t in element.findall('.//m:t', NS)))
                            shared_root.remove(element)
            previous = 0
            with archive.open(sheet_path) as stream:
                for event, element in ET.iterparse(stream, events=('start', 'end')):
                    if event == 'start' and element.tag == f"{{{NS['m']}}}sheetData":
                        sheet_data = element
                    if event != 'end' or element.tag != f"{{{NS['m']}}}row":
                        continue
                    number = element.get('r', '')
                    if not re.fullmatch(r'[1-9][0-9]*', number) or int(number) <= previous:
                        raise GuiGenerationReferenceError('invalid, duplicate or out-of-order source row')
                    previous = int(number)
                    cells = {}
                    for cell in element.findall('m:c', NS):
                        match = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', cell.get('r', ''))
                        if match is None or int(match[2]) != previous:
                            raise GuiGenerationReferenceError('invalid source cell address')
                        column = 0
                        for letter in match[1]:
                            column = column * 26 + ord(letter) - 64
                        if column in cells:
                            raise GuiGenerationReferenceError('duplicate source cell address')
                        cells[column] = _cell_value(cell, shared)
                    sheet_data.remove(element)
                    element.clear()
                    yield previous, cells


def _number(value, *, nonnegative=False):
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise GuiGenerationReferenceError('explicit finite numeric source value required') from exc
    if not number.is_finite() or (nonnegative and number < 0):
        raise GuiGenerationReferenceError('source number violates finite/sign boundary')
    return number


def _parse_capacity(rows):
    cells = dict(rows)
    headers = {
        (1, 1): 'Installed Capacity per Production Type',
        (2, 1): 'Installed Generation Capacity Aggregated [14.1.A]',
        (3, 1): '01/01/2025 - 01/01/2026', (5, 1): 'Production Type',
        (5, 2): 'BZN|HU', (6, 1): 'Production Type', (6, 2): '2025 (MW)',
    }
    if any(cells.get(row, {}).get(col) != text for (row, col), text in headers.items()):
        raise GuiGenerationReferenceError('installed-capacity product/area/year/unit mismatch')
    if set(n for n in cells if n >= 7) != set(range(7, 29)):
        raise GuiGenerationReferenceError('complete installed-capacity manifest and footer required')
    active, structural = {}, {}
    for n in range(7, 28):
        row = cells[n]
        if set(row) != {1, 2} or row[1] not in PSR_CODES or row[1] in active or row[1] in structural:
            raise GuiGenerationReferenceError('unknown/duplicate installed-capacity production type')
        (structural if row[2] == 'n/e' else active)[row[1]] = PSR_CODES[row[1]]
        if row[2] != 'n/e':
            _number(row[2], nonnegative=True)
    footer = cells[28]
    if set(footer) != {1, 2} or footer[1] != 'Total Grand Capacity':
        raise GuiGenerationReferenceError('installed-capacity total footer must be identified and excluded')
    _number(footer[2], nonnegative=True)
    if len(active) != 14 or len(structural) != 7 or set(active) | set(structural) != set(PSR_CODES):
        raise GuiGenerationReferenceError('expected 14 numeric and 7 structural n/e types')
    return active, structural


def _parse_generation(rows, active, structural, artifact, *, start=START, end=END):
    iterator = iter(rows)
    header = {}
    for n, row in iterator:
        if n > 6:
            raise GuiGenerationReferenceError('generation headers missing')
        header[n] = row
        if n == 6:
            break
    expected = {
        (1, 1): 'Actual Generation per Production Type - Generation',
        (2, 1): 'Aggregated Generation per Type [16.1.B&C]',
        (3, 1): '01/01/2025 00:00 - 01/01/2026 00:00 (UTC)',
        (5, 1): 'MTU', (6, 1): 'MTU',
    }
    if any(header.get(r, {}).get(c) != text for (r, c), text in expected.items()):
        raise GuiGenerationReferenceError('production-only GUI product/time basis mismatch')
    width = len(PSR_CODES) + 1
    if (set(header[5]) != set(range(1, width + 1))
            or set(header[6]) != set(range(1, width + 1))
            or any(header[5][c] != 'BZN|HU' for c in range(2, width + 1))):
        raise GuiGenerationReferenceError('complete Hungarian generation column grid required')
    names = [header[6][c] for c in range(2, width + 1)]
    if any(not name.endswith(' (MW)') for name in names):
        raise GuiGenerationReferenceError('explicit MW generation columns required')
    names = [name[:-5] for name in names]
    if len(set(names)) != len(names) or set(names) != set(active) | set(structural):
        raise GuiGenerationReferenceError('generation columns differ from installed-capacity manifest')
    records, missing = [], {}
    count = 0
    for n, row in iterator:
        timestamp = start + count * STEP
        finish = timestamp + STEP
        if n != count + 7 or finish > end or set(row) != set(range(1, width + 1)):
            raise GuiGenerationReferenceError('generation row/cell grid is incomplete or extended')
        mtu = timestamp.strftime('%d/%m/%Y %H:%M:%S') + ' - ' + finish.strftime('%d/%m/%Y %H:%M:%S')
        if row[1] != mtu:
            raise GuiGenerationReferenceError('generation MTU gap, ordering or duration mismatch')
        for column, name in enumerate(names, 2):
            value = row[column].strip()
            if name in structural:
                if value != 'n/e':
                    raise GuiGenerationReferenceError('structural n/e must remain explicit in every interval')
                continue
            code = active[name]
            power = None if value == '' else float(_number(value, nonnegative=True))
            if power is None:
                if code not in RECOVERY_COLUMNS:
                    raise GuiGenerationReferenceError('missing active value outside P6 recovery scope')
                missing[(code, timestamp)] = _column_name(column) + str(n)
            records.append(ObservedGenerationRecord(
                source_series_id='P5_GUI_PRODUCTION_' + code,
                timestamp_utc=timestamp, interval_end_utc=finish, timestep_hours=0.25,
                power_mw=power, production_type_code=code, business_type='A01',
                region_id=HUNGARY_CONTROL_AREA, region_scheme=CONTROL_AREA_SCHEME,
                evidence_status='Q', source_refs=(ENTSOE_SOURCE_ID,),
                source_revision=artifact.acquisition_record_id + ':' + artifact.sha256,
            ))
        count += 1
    if start + count * STEP != end:
        raise GuiGenerationReferenceError('generation source window is incomplete')
    columns = tuple(sorted((PSR_CODES[name], col) for col, name in enumerate(names, 2)))
    return tuple(records), missing, columns


def _mavir_start(label):
    if not re.fullmatch(r'\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}', label):
        raise GuiGenerationReferenceError('MAVIR interval-end timestamp requires an explicit UTC offset')
    try:
        return datetime.strptime(label, '%Y.%m.%d %H:%M:%S %z').astimezone(timezone.utc) - STEP
    except ValueError as exc:
        raise GuiGenerationReferenceError('invalid MAVIR timestamp') from exc


def _merge_operational(rows, artifact, panel, *, start=START, end=END):
    iterator = iter(rows)
    first = next(iterator, None)
    if first != (1, dict(enumerate(MAVIR_HEADERS, 1))):
        raise GuiGenerationReferenceError('MAVIR fuel-type column identity mismatch')
    count, previous, first_timestamp = 0, None, None
    for n, row in iterator:
        if n != count + 2 or 1 not in row:
            raise GuiGenerationReferenceError('complete MAVIR timestamp row sequence required')
        timestamp = _mavir_start(row[1])
        if timestamp.minute % 15 or timestamp.second or timestamp.microsecond:
            raise GuiGenerationReferenceError('MAVIR source must lie on the UTC PT15M grid')
        if previous is not None and timestamp != previous + STEP:
            raise GuiGenerationReferenceError('MAVIR raw sequence gap/duplicate/order mismatch')
        if first_timestamp is None:
            first_timestamp = timestamp
        previous = timestamp
        count += 1
        if not start <= timestamp < end:
            continue
        if set(row) != set(range(1, len(MAVIR_HEADERS) + 1)):
            raise GuiGenerationReferenceError('complete in-window MAVIR source row/cell grid required')
        values = tuple(_number(row[c]) for c in range(2, len(MAVIR_HEADERS) + 1))
        locator = (artifact.acquisition_record_id, n)
        if timestamp in panel:
            old_values, locators = panel[timestamp]
            if old_values != values:
                raise GuiGenerationReferenceError('conflicting full MAVIR rows on overlapping UTC timestamps')
            if any(record_id == locator[0] for record_id, _ in locators):
                raise GuiGenerationReferenceError('duplicate MAVIR timestamp within one artifact')
            locators.append(locator)
        else:
            panel[timestamp] = (values, [locator])
    if count != artifact.data_rows:
        raise GuiGenerationReferenceError('MAVIR raw row count differs from pinned registry')
    for actual, expected in ((first_timestamp, artifact.first_interval_start_utc),
                             (previous, artifact.last_interval_start_utc)):
        if expected and actual != datetime.fromisoformat(expected.replace('Z', '+00:00')):
            raise GuiGenerationReferenceError('MAVIR raw window differs from pinned registry')


def _recover(a75, missing, active, operations, artifacts, *, start=START, end=END):
    expected_timestamps = {start + i * STEP for i in range(int((end - start) / STEP))}
    if set(operations) != expected_timestamps:
        raise GuiGenerationReferenceError('complete MAVIR UTC source window required')
    hashes = {artifact.acquisition_record_id: artifact.sha256 for artifact in artifacts}
    recoveries, lineage = [], []
    for (code, timestamp), cell in sorted(missing.items(), key=lambda item: (item[0][1], item[0][0])):
        values, locators = operations[timestamp]
        locators = sorted(locators)
        power = values[RECOVERY_COLUMNS[code] - 2]
        digest = hashes[locators[0][0]]
        recoveries.append(SignedNetRecoveryRecord(timestamp, 0.25, code, float(power), digest))
        lineage.append(RecoveryCellLineage(
            timestamp, code, cell, power,
            tuple((record_id, _column_name(RECOVERY_COLUMNS[code]) + str(row))
                  for record_id, row in locators), digest,
        ))
    recovered = materialize_recovered_generation_panel(
        a75, recoveries, expected_production_types=active,
        request_start_utc=start, request_end_utc=end,
    )
    return recovered, tuple(lineage)


def read_pinned_gui_generation_reference(source_paths: Mapping[str, Path]) -> QualifiedGuiGenerationReference:
    """Materialize the existing UTC-year E2 base; no new acquisition or admission."""
    artifacts = source_artifacts()
    if set(source_paths) != set(SOURCE_IDS):
        raise GuiGenerationReferenceError('paths for exactly the six admitted acquisition IDs required')
    by_id = {artifact.acquisition_record_id: artifact for artifact in artifacts}
    active, structural = _parse_capacity(_xlsx_rows(source_paths[CAPACITY_ID], by_id[CAPACITY_ID], '1'))
    a75, missing, columns = _parse_generation(
        _xlsx_rows(source_paths[GENERATION_ID], by_id[GENERATION_ID], '1'),
        active, structural, by_id[GENERATION_ID],
    )
    operations = {}
    for record_id in OPERATIONAL_IDS:
        _merge_operational(_xlsx_rows(source_paths[record_id], by_id[record_id], 'Exportált adatok'),
                           by_id[record_id], operations)
    overlaps = sum(len(locators) > 1 for _values, locators in operations.values())
    recovered, lineage = _recover(a75, missing, active.values(), operations, artifacts)
    result = QualifiedGuiGenerationReference(
        recovered, artifacts, tuple(sorted(active.values())), tuple(sorted(structural.values())),
        columns, lineage, len(a75) - len(missing), overlaps,
    )
    reference_summary(result)  # Fail before exposing any qualified materialization.
    return result


def reference_summary(panel: QualifiedGuiGenerationReference):
    """Validate the reproduced counters and expose a compact non-panel receipt."""
    contract = json.loads(REFERENCE_MANIFEST.read_text(encoding='utf-8'))
    if panel.artifacts != source_artifacts():
        raise GuiGenerationReferenceError('reference must preserve all six exact acquisition pins')
    result = panel.recovered_panel
    observed = {
        'utc_intervals': len({r.timestamp for r in panel.records}),
        'active_production_types': len(panel.active_production_types),
        'structural_ne_types': len(panel.structural_ne_types),
        'supply_records': len(panel.records),
        'numeric_a75_cells_preserved': panel.numeric_a75_cells_preserved,
        'recovered_cells': result.recovered_cell_count,
        'negative_recovery_cells': result.negative_recovery_count,
        'zero_recovery_cells': result.zero_recovery_count,
        'positive_recovery_cells': result.positive_recovery_count,
        'mavir_overlapped_timestamps': panel.mavir_overlapped_timestamps,
        'missing_a75_cells_by_code': dict(sorted(Counter(r.production_type_code for r in panel.recovery_lineage).items())),
    }
    if observed != contract['expected_reproduction']:
        raise GuiGenerationReferenceError('reproduction differs from the admitted P5/P6/P7 control counts')
    if (list(panel.active_production_types) != contract['active_production_type_codes']
            or list(panel.structural_ne_types) != contract['structural_ne_type_codes']):
        raise GuiGenerationReferenceError('installed-capacity type classification differs from admission')
    expected_codes = tuple('ENTSOE_PSR_' + code for code in panel.active_production_types)
    lineage = {(r.production_type_code, r.timestamp_utc): r for r in panel.recovery_lineage}
    if len(lineage) != result.recovered_cell_count:
        raise GuiGenerationReferenceError('unique cell-level lineage required for every recovery')
    artifact_by_id = {a.acquisition_record_id: a for a in panel.artifacts}
    for recovery in lineage.values():
        if not recovery.operational_cells or recovery.operational_cells != tuple(sorted(set(recovery.operational_cells))):
            raise GuiGenerationReferenceError('unique ordered MAVIR source-cell lineage required')
        selected = artifact_by_id.get(recovery.operational_cells[0][0])
        if selected is None or selected.sha256 != recovery.selected_source_sha256:
            raise GuiGenerationReferenceError('recovery selected-source lineage mismatch')
        for record_id, cell in recovery.operational_cells:
            if record_id not in OPERATIONAL_IDS or not re.fullmatch(_column_name(RECOVERY_COLUMNS[recovery.production_type_code]) + r'[1-9][0-9]*', cell):
                raise GuiGenerationReferenceError('invalid MAVIR recovery-cell lineage')
    for i, row in enumerate(panel.records):
        timestamp = START + (i // len(expected_codes)) * STEP
        if (row.timestamp != timestamp or row.source_component_id != expected_codes[i % len(expected_codes)]
                or row.timestep_hours != 0.25 or row.evidence_status != 'Q' or row.truth_context != 'REAL'
                or row.region_id != HUNGARY_CONTROL_AREA or row.region_scheme != CONTROL_AREA_SCHEME):
            raise GuiGenerationReferenceError('complete ordered Q-derived UTC panel required')
        code = panel.active_production_types[i % len(expected_codes)]
        recovery = lineage.get((code, timestamp))
        if recovery is None:
            if (row.source_refs != (ENTSOE_SOURCE_ID,) or row.boundary_id != GENERATION_BOUNDARY
                    or row.source_withdrawal_kw != 0):
                raise GuiGenerationReferenceError('numeric A75 precedence and source boundary required')
        else:
            expected_cell = _column_name(dict(panel.a75_columns)[code]) + str(i // len(expected_codes) + 7)
            if (recovery.a75_cell != expected_cell or row.boundary_id != SIGNED_NET_GENERATION_BOUNDARY
                    or row.source_refs != tuple(sorted((ENTSOE_SOURCE_ID, MAVIR_NET_OPERATIONAL_SOURCE_ID)))
                    or row.net_generation_contribution_kw != float(recovery.signed_power_mw) * 1000.0):
                raise GuiGenerationReferenceError('exact signed recovery and cell lineage required')
    return {
        **observed, 'request_start_utc': START.isoformat(), 'request_end_utc_exclusive': END.isoformat(),
        'time_basis': 'UTC', 'interval_convention': 'INTERVAL_START',
        'spatial_grain': 'BZN|HU', 'region_scheme': CONTROL_AREA_SCHEME,
        'evidence_status': 'Q', 'evidence_tier': panel.evidence_tier,
        'model_use_status': panel.model_use_status, 'raw_storage_policy': panel.raw_storage_policy,
        'public_raw_reuse_status': panel.public_raw_reuse_status, 'source_semantics': panel.source_semantics,
        'complete_2025_budapest_civil_year': False, 'complete_meteorological_winter': False,
        'missing_boundary': '2024-12-31T23:00:00Z/2025-01-01T00:00:00Z generation not in source bundle',
        'source_artifacts': [dict(acquisition_record_id=a.acquisition_record_id, source_id=a.source_id,
                                  sha256=a.sha256, bytes=a.byte_count) for a in panel.artifacts],
    }
