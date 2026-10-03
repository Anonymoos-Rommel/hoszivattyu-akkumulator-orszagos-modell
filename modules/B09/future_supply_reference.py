"""Hash-pinned future supply references, without a future runtime/base selection.

SCN values describe an external source scenario. Market treatment is never proof
of commissioning or finance. No network access, interpolation, zero-filling,
capacity summation, dispatch or B09 generation-engine handoff is provided.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / 'registry/b09_future_supply_reference_manifest.json'
CAPACITY_SOURCE = 'SRC-B09-ERAA2025-DASHBOARD-FINAL'
EVA_SOURCE = 'SRC-B09-ERAA2025-EVA-CURRENT'
DATE_CONVENTION = 'ERAA_1_JULY_CAPACITY_THRESHOLD'
ROLES = ('GENERATION', 'STORAGE', 'DEMAND_RESPONSE', 'CONSUMPTION')
YEARS = (2028, 2030, 2033, 2035)
POLICY = {
    'record_evidence_status': 'SCN',
    'materialization_scope': 'RESEARCH_REFERENCE_ONLY',
    'model_use_status': 'SOURCE_SPECIFIC_REVIEW_REQUIRED',
    'public_raw_reuse_status': 'REPOSITORY_COPY_NOT_CLEARED',
    'raw_storage_policy': 'EXTERNAL_ONLY',
    'central_future_baseline_status': 'NOT_SELECTED',
    'future_runtime_status': 'NOT_AUTHORIZED_BY_THIS_REFERENCE',
}
PINS = {
    CAPACITY_SOURCE: {
        'sha256': '45e16e952b2548fd3a8f337f30c3662247ed921ad2d36d250c5bc3098865f636',
        'byte_count': 766493,
        'source_revision': 'ERAA2025_FINAL_INPUTS_SNAPSHOT_2026-02-04',
        'scenario_id': 'ERAA2025_NATIONAL_TRENDS',
        'model_stage': 'PRE_EVA_RESOURCE_CAPACITY',
        'value_basis': 'NET_RESOURCE_CAPACITY',
        'member': 'ERAA_2025_DashboardRawData1/Dashboard Raw Data/GenerationCapacities.csv',
        'member_sha256': '8d6eb10a558ca7e920dbc3fda3a11c8e8cc8b9c8036cfe9a515b68efdddd76e8',
        'member_byte_count': 567624,
        'selected_source_record_count': 88,
    },
    EVA_SOURCE: {
        'sha256': '2e5938ed74dcd3d8b60e88625af90bf19f77706c7a4df34e228746adae0c3ccc',
        'byte_count': 60999,
        'source_revision': 'ERAA2025_COST_BASED_EVA_SNAPSHOT_2026-07-30',
        'scenario_id': 'ERAA2025_AMENDED_CENTRAL_REFERENCE_COST_BASED',
        'model_stage': 'POST_EVA_CAPACITY_CHANGE',
        'value_basis': 'NONCUMULATIVE_CHANGE_FROM_NATIONAL_TRENDS',
        'member': 'xl/worksheets/sheet2.xml',
        'member_sha256': 'b3576a398a32a3a433440bdffc1ae8d9f31f3407619ff535c699a75d96466722',
        'member_byte_count': 135106,
        'selected_source_record_count': 49,
    },
}
CAPACITY_ROLES = {
    **{name: 'GENERATION' for name in (
        'Run of river', 'Geothermal', 'Small biomass', 'Waste',
        'Solar PV rooftop industrial', 'Solar PV rooftop residential',
        'Solar PV utility non-tracking', 'Solar PV utility tracking', 'Biofuel',
        'Hard coal', 'Light oil', 'Lignite', 'Natural gas', 'Nuclear', 'Wind onshore')},
    'Battery utility scale': 'STORAGE', 'Battery residential': 'STORAGE',
    'EV - iDSR': 'DEMAND_RESPONSE', 'HP - iDSR': 'DEMAND_RESPONSE',
    'Electrolyser': 'CONSUMPTION', 'Power to heat': 'CONSUMPTION',
}
EVA_ROLES = {name: 'GENERATION' for name in (
    'Gas CCGT new', 'Gas CCGT old 2', 'Gas CCGT present 1',
    'Gas conventional old 1', 'Gas conventional old 2', 'Gas OCGT new',
    'Gas OCGT old', 'Hard coal new', 'Hard coal old 1', 'Light oil', 'Lignite old 1')}
EVA_ROLES['DSR'] = 'DEMAND_RESPONSE'
MARKET_STATUSES = {
    'Available on market',
    'Out of market – for PV/battery dispatch optimization',
    'Out of market - primary purpose ancillary service',
}
CAPACITY_HEADER = ('data_version', 'Target year', 'Market_Node', 'Technology',
                   'Technology_Simplified', 'Operational_Status', 'Value')
EVA_HEADER = ('Node', 'Technology', 'EVA Type', 'Year', 'Capacity Change')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


class FutureSupplyReferenceError(ValueError):
    """The source identity, selector or research-only boundary failed."""


@dataclass(frozen=True)
class ReferenceSelection:
    source_id: str
    source_revision: str
    scenario_id: str
    model_stage: str
    target_years: tuple[int, ...]
    capacity_date_convention: str
    resource_roles: tuple[str, ...]


@dataclass(frozen=True)
class FutureSupplyReferenceRecord:
    source_id: str
    source_revision: str
    source_sha256: str
    source_member: str
    source_member_sha256: str
    source_row: int
    source_value_cell: str
    source_fields: tuple[tuple[str, str], ...]
    scenario_id: str
    model_stage: str
    target_year: int
    capacity_date_convention: str
    technology: str
    resource_role: str
    market_treatment_status: str
    change_type: str
    value_mw: Decimal
    value_basis: str
    market_node: str = field(default='HU00', init=False)
    unit: str = field(default='MW', init=False)
    evidence_status: str = field(default='SCN', init=False)
    lifecycle_status: str = field(default='NOT_ESTABLISHED_BY_REFERENCE', init=False)
    financing_status: str = field(default='NOT_ESTABLISHED_BY_REFERENCE', init=False)


@dataclass(frozen=True)
class FutureSupplyReference:
    selection: ReferenceSelection
    records: tuple[FutureSupplyReferenceRecord, ...]
    full_source_record_count: int
    model_use_status: str = field(default=POLICY['model_use_status'], init=False)
    materialization_scope: str = field(default=POLICY['materialization_scope'], init=False)
    public_raw_reuse_status: str = field(default=POLICY['public_raw_reuse_status'], init=False)
    raw_storage_policy: str = field(default=POLICY['raw_storage_policy'], init=False)
    central_future_baseline_status: str = field(default='NOT_SELECTED', init=False)
    future_runtime_status: str = field(default=POLICY['future_runtime_status'], init=False)


def source_manifest():
    """Public metadata cannot widen source/use authority through a JSON edit."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    if (manifest.get('reference_id') != 'B09-D02-FUTURE-SUPPLY-REFERENCE-V1'
            or any(manifest.get(k) != v for k, v in POLICY.items())
            or manifest.get('capacity_date_convention') != DATE_CONVENTION
            or manifest.get('target_years') != list(YEARS)
            or manifest.get('resource_roles') != list(ROLES)):
        raise FutureSupplyReferenceError('reference policy/selector authority changed')
    artifacts = manifest.get('source_artifacts', [])
    if len(artifacts) != len(PINS) or {a.get('source_id') for a in artifacts} != set(PINS):
        raise FutureSupplyReferenceError('exact source artifact identities required')
    for artifact in artifacts:
        if any(artifact.get(k) != v for k, v in PINS[artifact['source_id']].items()):
            raise FutureSupplyReferenceError('source snapshot authority changed')
    return manifest


def _validate_selection(selection):
    if not isinstance(selection, ReferenceSelection) or selection.source_id not in PINS:
        raise FutureSupplyReferenceError('explicit supported source selection required')
    spec = PINS[selection.source_id]
    for name in ('source_revision', 'scenario_id', 'model_stage'):
        if getattr(selection, name) != spec[name]:
            raise FutureSupplyReferenceError(f'incompatible {name} selection')
    if selection.capacity_date_convention != DATE_CONVENTION:
        raise FutureSupplyReferenceError('ERAA July1 convention required; no MAVIR year shift')
    if (not isinstance(selection.target_years, tuple) or not selection.target_years
            or any(type(y) is not int or y not in YEARS for y in selection.target_years)
            or len(set(selection.target_years)) != len(selection.target_years)):
        raise FutureSupplyReferenceError('explicit distinct supported target years required')
    if (not isinstance(selection.resource_roles, tuple) or not selection.resource_roles
            or any(role not in ROLES for role in selection.resource_roles)
            or len(set(selection.resource_roles)) != len(selection.resource_roles)):
        raise FutureSupplyReferenceError('explicit distinct supported resource roles required')
    return spec


def _safe_archive(data):
    """Never extract paths; reject traversal, duplicates, links and oversized ZIPs."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        members = archive.infolist()
        names = [m.filename for m in members]
        if len(names) != len(set(names)) or len(names) > 200:
            raise FutureSupplyReferenceError('duplicate or excessive archive members')
        for item in members:
            name = item.filename
            parts = name.rstrip('/').split('/')
            if (not name or name.startswith('/') or '\\' in name or ':' in name
                    or any(part in ('', '.', '..') for part in parts)
                    or stat.S_ISLNK(item.external_attr >> 16) or item.flag_bits & 1):
                raise FutureSupplyReferenceError('unsafe archive member path/type')
        if sum(m.file_size for m in members) > 25_000_000:
            raise FutureSupplyReferenceError('oversized archive contents')
        return archive
    except (zipfile.BadZipFile, OSError) as exc:
        raise FutureSupplyReferenceError('invalid source archive') from exc


def _xml(data):
    if b'\x00' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise FutureSupplyReferenceError('XML entities/DTD are not permitted')
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise FutureSupplyReferenceError('invalid source XML') from exc


def _number(raw, *, nonnegative):
    if not isinstance(raw, str) or not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', raw):
        raise FutureSupplyReferenceError('explicit finite numeric value required')
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise FutureSupplyReferenceError('invalid numeric value') from exc
    if not value.is_finite() or (nonnegative and value < 0):
        raise FutureSupplyReferenceError('invalid numeric sign/value')
    return value


def _capacity_rows(data):
    try:
        reader = csv.reader(io.StringIO(data.decode('utf-8-sig'), newline=''))
        if tuple(next(reader, ())) != CAPACITY_HEADER:
            raise FutureSupplyReferenceError('capacity header mismatch')
        result = []
        for number, values in enumerate(reader, 2):
            if len(values) != len(CAPACITY_HEADER):
                raise FutureSupplyReferenceError('capacity row width mismatch')
            row = dict(zip(CAPACITY_HEADER, values))
            if row['data_version'] == 'ERAA 2025 final' and row['Market_Node'] == 'HU00':
                result.append((number, row))
        return result
    except (UnicodeError, csv.Error) as exc:
        raise FutureSupplyReferenceError('invalid capacity CSV') from exc


def _eva_rows(archive):
    workbook = _xml(archive.read('xl/workbook.xml'))
    sheets = workbook.findall('m:sheets/m:sheet', NS)
    if [s.get('name') for s in sheets] != ['Readme', 'Cost Based', 'Revenue Based']:
        raise FutureSupplyReferenceError('EVA worksheet identity mismatch')
    chosen = sheets[1]
    if chosen.get('state', 'visible') != 'visible':
        raise FutureSupplyReferenceError('EVA Cost Based sheet must be visible')
    relations = _xml(archive.read('xl/_rels/workbook.xml.rels'))
    matches = [r for r in relations if r.get('Id') == chosen.get(f'{{{REL_NS}}}id')]
    if (len(matches) != 1 or matches[0].get('Type') != REL_NS + '/worksheet'
            or matches[0].get('TargetMode') == 'External'
            or matches[0].get('Target') != 'worksheets/sheet2.xml'):
        raise FutureSupplyReferenceError('unsafe/mismatched EVA worksheet relationship')
    shared = []
    if 'xl/sharedStrings.xml' in archive.namelist():
        shared = [''.join(t.text or '' for t in s.findall('.//m:t', NS))
                  for s in _xml(archive.read('xl/sharedStrings.xml')).findall('m:si', NS)]
    sheet = _xml(archive.read('xl/worksheets/sheet2.xml'))
    output, previous = [], 0
    for row in sheet.findall('m:sheetData/m:row', NS):
        n = row.get('r', '')
        if not re.fullmatch(r'[1-9]\d*', n) or int(n) <= previous:
            raise FutureSupplyReferenceError('invalid duplicate/out-of-order EVA row')
        previous = int(n)
        cells = {}
        for cell in row.findall('m:c', NS):
            match = re.fullmatch(r'([A-Z]+)([1-9]\d*)', cell.get('r', ''))
            if match is None or int(match[2]) != previous or match[1] in cells:
                raise FutureSupplyReferenceError('invalid/duplicate EVA cell address')
            if cell.find('m:f', NS) is not None:
                raise FutureSupplyReferenceError('EVA formulas are not evaluated')
            kind = cell.get('t')
            if kind == 'inlineStr':
                value = ''.join(t.text or '' for t in cell.findall('m:is//m:t', NS))
            else:
                v = cell.find('m:v', NS)
                value = '' if v is None else v.text or ''
                if kind == 's':
                    if not re.fullmatch(r'\d+', value) or int(value) >= len(shared):
                        raise FutureSupplyReferenceError('invalid EVA shared string')
                    value = shared[int(value)]
                elif kind not in (None, 'n'):
                    raise FutureSupplyReferenceError('unsupported EVA cell type')
            cells[match[1]] = value
        if not any(cells.values()):
            continue
        if set(cells) != set('ABCDE'):
            raise FutureSupplyReferenceError('EVA row width mismatch')
        values = [cells[c] for c in 'ABCDE']
        if previous == 1:
            if tuple(values) != EVA_HEADER:
                raise FutureSupplyReferenceError('EVA header mismatch')
        elif values[0] == 'HU00':
            output.append((previous, dict(zip(EVA_HEADER, values))))
    if not sheet.findall('m:sheetData/m:row', NS) or sheet.find('m:sheetData/m:row', NS).get('r') != '1':
        raise FutureSupplyReferenceError('EVA header row missing')
    return output


def _records(rows, source_id, spec):
    result, keys = [], set()
    capacity = source_id == CAPACITY_SOURCE
    for number, row in rows:
        raw_year = row['Target year' if capacity else 'Year']
        if not re.fullmatch(r'\d{4}', raw_year) or int(raw_year) not in YEARS:
            raise FutureSupplyReferenceError('unsupported source target year')
        year, technology = int(raw_year), row['Technology']
        roles = CAPACITY_ROLES if capacity else EVA_ROLES
        if technology not in roles:
            raise FutureSupplyReferenceError('unknown source technology role')
        status = row['Operational_Status'] if capacity else 'NOT_SPECIFIED_IN_EVA_CHANGE_TABLE'
        change = '' if capacity else row['EVA Type']
        if capacity and status not in MARKET_STATUSES:
            raise FutureSupplyReferenceError('unknown market treatment status')
        value = _number(row['Value' if capacity else 'Capacity Change'], nonnegative=capacity)
        if not capacity and (change not in ('Retirement', 'Expansion', 'Life Extension')
                             or (change == 'Retirement' and value > 0)
                             or (change != 'Retirement' and value < 0)):
            raise FutureSupplyReferenceError('invalid EVA decision/sign')
        key = (year, technology, status, change)
        if key in keys:
            raise FutureSupplyReferenceError('duplicate source record key')
        keys.add(key)
        result.append(FutureSupplyReferenceRecord(
            source_id, spec['source_revision'], spec['sha256'], spec['member'],
            spec['member_sha256'], number, f'{"G" if capacity else "E"}{number}',
            tuple(row.items()), spec['scenario_id'], spec['model_stage'], year,
            DATE_CONVENTION, technology, roles[technology], status, change, value,
            spec['value_basis']))
    return tuple(result)


def read_future_supply_reference(path, selection):
    """Read one exact source with explicit selectors, without assigning a base."""
    spec = _validate_selection(selection)
    source_manifest()
    with Path(path).open('rb') as handle:
        data = handle.read(spec['byte_count'] + 1)
    if len(data) != spec['byte_count'] or hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise FutureSupplyReferenceError('exact source bytes/hash required')
    try:
        with _safe_archive(data) as archive:
            member = archive.read(spec['member'])
            if (len(member) != spec['member_byte_count']
                    or hashlib.sha256(member).hexdigest() != spec['member_sha256']):
                raise FutureSupplyReferenceError('exact source member bytes/hash required')
            rows = _capacity_rows(member) if selection.source_id == CAPACITY_SOURCE else _eva_rows(archive)
    except (KeyError, zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise FutureSupplyReferenceError('source archive/member cannot be read') from exc
    records = _records(rows, selection.source_id, spec)
    if len(records) != spec['selected_source_record_count']:
        raise FutureSupplyReferenceError('source-native record count mismatch')
    if selection.source_id == CAPACITY_SOURCE and Counter(r.target_year for r in records) != {y: 22 for y in YEARS}:
        raise FutureSupplyReferenceError('capacity source-year coverage mismatch')
    selected = tuple(r for r in records if r.target_year in selection.target_years
                     and r.resource_role in selection.resource_roles)
    return FutureSupplyReference(selection, selected, len(records))


def reference_summary(reference):
    """Metadata only: no MW summation, inferred missing rows or runtime result."""
    selection = reference.selection
    spec = _validate_selection(selection)
    return {
        'source_id': selection.source_id, 'source_revision': selection.source_revision,
        'source_sha256': spec['sha256'], 'source_member_sha256': spec['member_sha256'],
        'scenario_id': selection.scenario_id, 'model_stage': selection.model_stage,
        'target_years': list(selection.target_years),
        'capacity_date_convention': selection.capacity_date_convention,
        'value_basis': spec['value_basis'], 'unit': 'MW', 'market_node': 'HU00',
        'resource_roles': list(selection.resource_roles),
        'full_source_record_count': reference.full_source_record_count,
        'selected_record_count': len(reference.records),
        'selected_rows_by_year': dict(sorted(Counter(r.target_year for r in reference.records).items())),
        'selected_rows_by_role': dict(sorted(Counter(r.resource_role for r in reference.records).items())),
        'missing_row_rule': 'ABSENT_IS_NOT_ZERO;NO_RECTANGULAR_FILL', **POLICY,
    }
