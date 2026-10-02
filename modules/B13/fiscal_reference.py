"""Read an exact external fiscal panel without combining incompatible ledgers.

The public manifest contains provenance and interpretation, never the numeric
panel. Raw sources are hash-checked; XLSX values use XML Decimal lexemes, while
the reviewed panel's older float-derived lexemes are retained separately.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / 'registry/b13_fiscal_reference_manifest.json'
MANIFEST_SHA256 = 'ea2758707c05e9757b8efb8c5783c4081f06cda8bc9eb41900291e7303916cf2'
EDP = 'SRC-B13-KSH-EDP-20261001'
MONTHLY = 'SRC-B13-MAK-MONTHLY-202512'
QUARTERLY = 'SRC-B13-KSH-GDP0111-20261001'
ANNUAL_GDP = 'SRC-B13-KSH-GDP0004-20260930'
ADJUSTED_GDP = 'SRC-B13-KSH-GG-QUARTERLY-20261001'
POLICY = {
    'materialization_scope': 'PUBLISHED_STATISTIC_BASELINE_REFERENCE_ONLY',
    'raw_storage_policy': 'EXTERNAL_ONLY',
    'public_raw_reuse_status': 'REPOSITORY_COPY_NOT_CLEARED',
    'model_use_status': 'BOUNDED_SOURCE_SPECIFIC_REFERENCE',
    'programme_fiscal_engine_status': 'NOT_IMPLEMENTED',
    'headroom_status': 'NOT_ESTABLISHED',
    'policy_defaults_status': 'NOT_ADMITTED',
    'b15_admission_status': 'NOT_GRANTED',
}
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PANEL_FIELDS = {
    'record_id', 'quantity', 'value', 'unit', 'period', 'price_basis', 'boundary',
    'accounting_basis', 'status', 'evidence_tier', 'source_id', 'source_locator',
    'normalization', 'notes',
}


class FiscalReferenceError(ValueError):
    """Pinned identity, source interpretation or reconciliation failed."""


@dataclass(frozen=True)
class FiscalRecord:
    record_id: str
    quantity: str
    value: Decimal | None
    normalized_value: Decimal | None
    native_minus_normalized: Decimal | None
    unit: str
    period: str
    price_basis: str
    boundary: str
    accounting_basis: str
    status: str
    evidence_tier: str
    source_ids: tuple[str, ...]
    source_sha256s: tuple[str, ...]
    source_document_dates: tuple[str, ...]
    source_locator: str
    normalization: str
    notes: str
    value_kind: str
    reference_role: str
    source_precision: str
    source_status: str


@dataclass(frozen=True)
class Reconciliation:
    control_id: str
    value: Decimal
    unit: str
    status: str
    absolute_tolerance: Decimal | None
    formula: str


@dataclass(frozen=True)
class FiscalReference:
    records: tuple[FiscalRecord, ...]
    reconciliations: tuple[Reconciliation, ...]
    source_cell_flags: tuple[tuple[str, str, str], ...]
    panel_sha256: str
    verified_source_ids: tuple[str, ...]


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FiscalReferenceError('duplicate JSON key')
        result[key] = value
    return result


def _json(data):
    try:
        return json.loads(data, parse_float=Decimal, parse_int=Decimal,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              FiscalReferenceError('nonfinite JSON value')),
                          object_pairs_hook=_unique_pairs)
    except (ValueError, UnicodeError) as exc:
        raise FiscalReferenceError('invalid JSON') from exc


def source_manifest():
    data = MANIFEST_PATH.read_bytes()
    if hashlib.sha256(data).hexdigest() != MANIFEST_SHA256:
        raise FiscalReferenceError('public provenance/interpretation manifest changed')
    manifest = _json(data)
    if any(manifest.get(key) != value for key, value in POLICY.items()):
        raise FiscalReferenceError('reference-only policy changed')
    return manifest


def _pinned_bytes(path, pin):
    with Path(path).open('rb') as stream:
        data = stream.read(int(pin['byte_count']) + 1)
    if len(data) != pin['byte_count'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise FiscalReferenceError(f'exact external bytes required: {pin["source_id"]}')
    return data


def _decimal(value):
    if not isinstance(value, Decimal) or not value.is_finite():
        raise FiscalReferenceError('finite source-native Decimal required; flags are not zero')
    return value


def _xlsx(data):
    """Read cached native XML cells; never execute macros or recalculate formulas."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if len(archive.namelist()) != len(set(archive.namelist())):
                raise FiscalReferenceError('duplicate workbook archive member')
            strings = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                strings = [''.join(t.text or '' for t in si.findall('.//m:t', NS))
                           for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
            rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(
                archive.read('xl/_rels/workbook.xml.rels'))}
            result = {}
            for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('m:sheets/m:sheet', NS):
                target = rels[sheet.get(f'{{{REL_NS}}}id')]
                member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
                if not member.startswith('xl/') or '..' in member.split('/'):
                    raise FiscalReferenceError('invalid workbook member path')
                cells = {}
                for cell in ET.fromstring(archive.read(member)).findall('.//m:c', NS):
                    address = cell.get('r')
                    if address in cells:
                        raise FiscalReferenceError('duplicate workbook cell')
                    raw = cell.find('m:v', NS)
                    if cell.get('t') == 'inlineStr':
                        value = ''.join(t.text or '' for t in cell.findall('.//m:t', NS))
                    elif raw is None or raw.text is None:
                        value = None
                    elif cell.get('t') == 's':
                        value = strings[int(raw.text)]
                    elif cell.get('t') in (None, 'n'):
                        value = _decimal(Decimal(raw.text))
                    elif cell.get('t') in ('str', 'e'):
                        value = raw.text
                    elif cell.get('t') == 'b':
                        value = 'BOOLEAN:' + raw.text
                    else:
                        raise FiscalReferenceError('unsupported workbook cell type')
                    cells[address] = value
                result[sheet.get('name')] = cells
            return result
    except (KeyError, ValueError, IndexError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise FiscalReferenceError('invalid source-native workbook') from exc


def _csv(data):
    return list(csv.reader(io.StringIO(data.decode('iso-8859-2')), delimiter=';'))


def _csv_decimal(text):
    try:
        return _decimal(Decimal(text.replace(' ', '').replace(',', '.')))
    except InvalidOperation as exc:
        raise FiscalReferenceError('CSV missing value is not a number') from exc


def _decode_panel(data, manifest, workbooks):
    rows = _json(data)
    specs = {r['record_id']: r for r in manifest['records']}
    sources = {s['source_id']: s for s in manifest['source_artifacts']}
    if not isinstance(rows, list) or len(rows) != manifest['external_panel']['record_count']:
        raise FiscalReferenceError('exact reviewed panel row count required')
    seen, records = set(), []
    for row in rows:
        if not isinstance(row, dict) or set(row) != PANEL_FIELDS:
            raise FiscalReferenceError('exact reviewed panel schema required')
        rid = row['record_id']
        if rid not in specs or rid in seen:
            raise FiscalReferenceError('duplicate or unexpected record')
        seen.add(rid)
        spec = specs[rid]
        for key in ('unit', 'period', 'boundary', 'accounting_basis', 'status',
                    'evidence_tier', 'source_id', 'source_locator'):
            if row[key] != spec[key]:
                raise FiscalReferenceError(f'changed source interpretation: {rid}/{key}')
        if row['price_basis'] != 'nominal current HUF':
            raise FiscalReferenceError('unreviewed price basis')
        if any(not isinstance(row[k], str) or not row[k] for k in PANEL_FIELDS - {'value', 'notes'}):
            raise FiscalReferenceError('nonempty source metadata required')
        if not isinstance(row['notes'], str):
            raise FiscalReferenceError('source notes must be text')
        normalized = row['value']
        if normalized is None:
            if row['status'] != 'Q' or row['evidence_tier'] != 'E3':
                raise FiscalReferenceError('blank source cell must remain Q/E3')
        else:
            _decimal(normalized)
            if row['status'] not in ('OBS', 'DER') or row['evidence_tier'] != 'E1':
                raise FiscalReferenceError('numeric source status mismatch')
        native = normalized
        if row['source_id'] in workbooks:
            sheet, cell = row['source_locator'].split('!')
            native = _decimal(workbooks[row['source_id']][sheet][cell])
            if normalized is None or abs(native - normalized) > Decimal('0.00000001'):
                raise FiscalReferenceError('native workbook/panel disagreement beyond serialization precision')
        sids = tuple(row['source_id'].split(';'))
        records.append(FiscalRecord(
            rid, row['quantity'], native, normalized,
            None if native is None else native - normalized,
            row['unit'], row['period'], row['price_basis'], row['boundary'],
            row['accounting_basis'], row['status'], row['evidence_tier'], sids,
            tuple(sources[s]['sha256'] for s in sids),
            tuple(sources[s]['document_date'] for s in sids), row['source_locator'],
            row['normalization'], row['notes'], spec['value_kind'],
            spec['reference_role'], spec['source_precision'], spec['source_status']))
    if seen != set(specs):
        raise FiscalReferenceError('missing reviewed record')
    if sum(r.value is None for r in records) != manifest['external_panel']['blank_record_count']:
        raise FiscalReferenceError('blank source cell count changed')
    return tuple(records)


def _reconcile(records, sources, edp):
    values = {r.record_id: r.value for r in records}
    checks = []

    def check(name, value, formula, tolerance='0', unit='million HUF', diagnostic=False):
        value = _decimal(value)
        limit = None if tolerance is None else Decimal(tolerance)
        if limit is not None and abs(value) > limit:
            raise FiscalReferenceError(f'reconciliation failed: {name}')
        checks.append(Reconciliation(name, value, unit,
                      'RETAINED_DIAGNOSTIC' if diagnostic else 'UNRESOLVED' if limit is None else 'PASS',
                      limit, formula))

    def cell(sheet, address):
        return _decimal(edp[sheet][address])

    flags = []
    for sheet, address, expected in [('Table 1', 'H12', 'M'), ('Table 2A', 'G22', 'M'),
                                    ('Table 2A', 'G52', 'M'), ('Table 2A', 'G17', 'L'),
                                    ('Table 2D', 'G20', 'M'), ('Table 2D', 'G35', 'M'),
                                    ('Table 2D', 'G36', 'M')]:
        if edp[sheet][address] != expected:
            raise FiscalReferenceError('EDP flag changed; no missing-value imputation')
        flags.append((sheet, address, expected))
    for address, expected in [('H5', Decimal(2025)), ('I5', Decimal(2026)),
                              ('H8', 'half-finalized'), ('H16', 'half-finalized'),
                              ('I8', 'planned'), ('I16', 'planned')]:
        if edp['Table 1'][address] != expected:
            raise FiscalReferenceError('EDP year/status changed')
    for prefix in ('CASH_', 'CASH_CENTRAL_', 'CASH_FUNDS_', 'CASH_SS_', 'ORIGINAL_', 'AMENDED_'):
        check(prefix.lower() + 'identity', values[prefix+'REVENUE'] - values[prefix+'EXPENDITURE'] - values[prefix+'BALANCE'],
              prefix + 'REVENUE - EXPENDITURE - BALANCE; same ledger only')
    check('cash_components_balance', sum(values[f'CASH_{p}_BALANCE'] for p in ('CENTRAL', 'FUNDS', 'SS')) - values['CASH_BALANCE'],
          'Central budget + separate state funds + social-security funds - legal central subsystem')
    check('cash_to_edp_central_working_balance', values['CASH_CENTRAL_BALANCE'] + values['CASH_FUNDS_BALANCE'] - cell('Table 2A', 'G8'),
          'Central budget + separate state funds - Table 2A!G8', '1', diagnostic=True)
    check('cash_to_edp_ss_working_balance', values['CASH_SS_BALANCE'] - cell('Table 2D', 'G8'),
          'Social-security cash balance - Table 2D!G8', '1', diagnostic=True)
    for name, sheet, terms, total in [
        ('central_bridge', 'Table 2A', [8,11,26,28,39,53,57], 67),
        ('ss_bridge', 'Table 2D', [8,11,24,26,31,40], 45),
        ('debt_stock_flow', 'Table 3A', [10,12,31,44], 48),
        ('central_adjustments_detail', 'Table 2A', list(range(58,66)), 57),
        ('debt_adjustments_detail', 'Table 3A', [32,33,34,36,37,38,40,41,42], 31),
    ]:
        check(name, sum(cell(sheet, f'G{i}') for i in terms) - cell(sheet, f'G{total}'),
              f'{sheet}: ' + '+'.join(f'G{i}' for i in terms) + f'-G{total}; M is not applicable, L is unavailable',
              '0.00000001')
    check('edp_subsectors', values['ESA_CENTRAL_DEFICIT'] + values['ESA_LOCAL_BALANCE'] + values['ESA_SS_BALANCE'] - values['ESA_DEFICIT'],
          'S.1311 + S.1313 + S.1314 - S.13; S.1312 source M', '0.00000001')
    check('edp_b9_sign', values['ESA_DEFICIT'] + cell('Table 3A', 'G10'), 'Table 1 B.9 + Table 3A opposite-sign B.9', '0.00000001')
    check('debt_stock_difference', values['ESA_DEBT'] - cell('Table 1', 'G18') - cell('Table 3A', 'G48'),
          '2025 nominal year-end stock - 2024 nominal year-end stock - debt change', '0.00000001')
    quarterly = _csv(sources[QUARTERLY])
    year, selected = None, []
    for row in quarterly[2:]:
        if row[0]:
            year = row[0]
        if year == '2025' and row[1] in ('Q1','Q2','Q3','Q4'):
            selected.append(row)
    if len(selected) != 4 or {r[1] for r in selected} != {'Q1','Q2','Q3','Q4'}:
        raise FiscalReferenceError('exact four distinct 2025 quarters required')
    for rid, column in [('ESA_REVENUE',48), ('ESA_EXPENDITURE',47),
                        ('ESA_INTEREST_QUARTER_SUM',19), ('ESA_BALANCE_QUARTER_SUM',46)]:
        check(rid.lower() + '_native_sum', sum(_csv_decimal(r[column]) for r in selected) - values[rid],
              f'Four source-native 2025 quarters in column {column} minus reviewed {rid}')
    check('quarter_revenue_less_expenditure_minus_edp', values['ESA_REVENUE'] - values['ESA_EXPENDITURE'] - values['ESA_DEFICIT'],
          'Eight rounded million-HUF inputs minus unrounded annual EDP B.9', '4', diagnostic=True)
    check('quarter_reported_balance_minus_edp', values['ESA_BALANCE_QUARTER_SUM'] - values['ESA_DEFICIT'],
          'Four rounded B.9 quarters minus unrounded annual EDP B.9', '2', diagnostic=True)
    check('quarter_interest_minus_edp', values['ESA_INTEREST_QUARTER_SUM'] - values['ESA_INTEREST'], 'Quarterly ESA D.41 - EDP consolidated ESA interest')
    annual = [r for r in _csv(sources[ANNUAL_GDP])[2:] if r[0] == '2025']
    adjusted = [r for r in _csv(sources[ADJUSTED_GDP])[2:] if r[0] == '2025' and r[1].startswith('Q1') and r[1].endswith('Q4')]
    if len(annual) != 1 or len(adjusted) != 1:
        raise FiscalReferenceError('exact annual GDP rows required')
    check('annual_gdp_minus_edp', _csv_decimal(annual[0][1]) - values['GDP_UNADJUSTED'], 'GDP0004 annual unadjusted current-market-price GDP - EDP GDP')
    check('adjusted_gdp_difference', _csv_decimal(adjusted[0][18])*1000 - values['GDP_UNADJUSTED'],
          'GDP0110 seasonally adjusted annual row * 1000 - unadjusted EDP GDP; no substitution', None, diagnostic=True)
    for number in ('1003','1114','1333','1500'):
        record = next(r for r in records if r.record_id == 'REZSI_ORDER_' + number)
        parts = re.findall(r'(?:^|; )([0-9]+) (?:immediately|by)', record.notes)
        if not parts:
            raise FiscalReferenceError('payment instruction components absent')
        check('instruction_components_' + number, sum(Decimal(p) for p in parts) - record.value,
              'Sum published instruction schedule components - corresponding order; not actual payments', unit='HUF')
    check('four_order_sum', sum(values['REZSI_ORDER_'+n] for n in ('1003','1114','1333','1500')) - values['REZSI_FOUR_ORDER_SUM'],
          'Four identified quarterly instructions - reviewed derived subtotal', unit='HUF')
    check('mvm_receipt_minus_orders', values['MVM_REZSI_CASH']*1000000 - values['REZSI_FOUR_ORDER_SUM'],
          'Reported integer-million-HUF receipt * 1000000 - exact-HUF instructions; unresolved, not one-HUF cash precision', None, 'HUF')
    return tuple(checks), tuple(flags)


def read_fiscal_reference(panel_path, source_files):
    """Require the exact panel and source-ID/path map; never download or repin."""
    manifest = source_manifest()
    pins = {s['source_id']: s for s in manifest['source_artifacts']}
    if not isinstance(source_files, dict) or set(source_files) != set(pins):
        raise FiscalReferenceError('exact explicit source-ID/path map required')
    sources = {sid: _pinned_bytes(source_files[sid], pin) for sid, pin in pins.items()}
    data = _pinned_bytes(panel_path, manifest['external_panel'])
    try:
        # Caller Decimal context must not round native lexemes or reconciliations.
        with localcontext() as context:
            context.prec = 50
            workbooks = {sid: _xlsx(sources[sid]) for sid in (EDP, MONTHLY)}
            records = _decode_panel(data, manifest, workbooks)
            reconciliations, flags = _reconcile(records, sources, workbooks[EDP])
        return FiscalReference(records, reconciliations, flags,
                               manifest['external_panel']['sha256'], tuple(sorted(sources)))
    except (KeyError, TypeError, IndexError, InvalidOperation) as exc:
        raise FiscalReferenceError('invalid source-native panel or control') from exc


def reference_summary(reference):
    if not isinstance(reference, FiscalReference):
        raise FiscalReferenceError('verified fiscal reference required')
    return {'reference_id': 'B13-D01-FISCAL-BASELINE-REFERENCE-V1', **POLICY,
            'panel_sha256': reference.panel_sha256,
            'verified_source_ids': list(reference.verified_source_ids),
            'record_count': len(reference.records),
            'numeric_record_count': sum(r.value is not None for r in reference.records),
            'blank_record_count': sum(r.value is None for r in reference.records),
            'native_lexeme_difference_count': sum(r.native_minus_normalized not in (None, 0) for r in reference.records),
            'reconciliation_count': len(reference.reconciliations),
            'source_cell_flags': [{'source_id': EDP, 'sheet': s, 'cell': c, 'flag': f,
                                   'meaning': 'NOT_APPLICABLE' if f == 'M' else 'UNAVAILABLE'}
                                  for s,c,f in reference.source_cell_flags],
            'programme_fiscal_result': None,
            'mvm_order_gap_explanation': None}
