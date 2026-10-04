"""Pinned private historical gas-quality inventory and statistical controls.

This reader admits source records for personal analysis, not a physical bridge.
No implicit period/state conversion, household weights, calibration, or national
calorific value is exposed. Source bytes and normalized point rows stay private.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from html.parser import HTMLParser
import hashlib
import io
import itertools
import json
from pathlib import Path, PurePosixPath
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from modules.B02 import household_energy_controls as enduse
from modules.B11 import county_baseline_contract as county

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ID = 'B11-D02-PRIVATE-GAS-QUALITY-CONTROLS-2024-V1'
HISTORICAL_SCOPE = 'CALENDAR_2024_SOURCE_AND_CONTROL_HANDOFF'
MANIFEST_PATH = 'registry/b11_gas_quality_reference_manifest.json'
MANIFEST_SHA256 = '1ad0df1a083a91d8d31f2ca21cf9473473f50551882f1215af2cb70317eebcfa'
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
RID = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
DIMS = ['freq', 'nrg_bal', 'siec', 'unit', 'geo', 'time']
ARITHMETIC = Context(prec=50, rounding=ROUND_HALF_UP)


class GasQualityReferenceError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise GasQualityReferenceError(message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def _json(raw):
    def invalid(value):
        raise GasQualityReferenceError('nonfinite JSON number')
    return json.loads(raw, object_pairs_hook=_unique, parse_float=Decimal,
                      parse_constant=invalid)


def source_manifest():
    raw = (ROOT / MANIFEST_PATH).read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256, 'manifest pin mismatch')
    return _json(raw)


def _pinned_bytes(path, pin):
    raw = Path(path).read_bytes()
    _require(len(raw) == pin['byte_count'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
             'source or repository pin mismatch: ' + pin.get('artifact_id', pin.get('path', '')))
    return raw


def source_map(path):
    """Require artifact IDs: a narrower response is not its source family's bytes."""
    result = _json(Path(path).read_bytes())
    _require(type(result) is dict and all(type(v) is str and v for v in result.values()),
             'explicit artifact-ID to local-path map required')
    return {key: Path(value) for key, value in result.items()}


def _xml(raw, root):
    _require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(),
             'XML entity declarations forbidden')
    tree = ET.fromstring(raw)
    _require(tree.tag == root, 'unexpected XML namespace or root')
    return tree


def _decimal(raw):
    _require(type(raw) is str and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?', raw),
             'native numeric lexeme required')
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise GasQualityReferenceError('invalid native number') from exc
    _require(value.is_finite() and value >= 0, 'finite nonnegative source value required')
    return value


def _native_cell(cell, strings, styles, formats, fills):
    if cell is None:
        return {'raw': None, 'cell_type': 'ABSENT', 'number_format': None,
                'style_index': None, 'fill_colour': None}
    _require(cell.find(f'{{{NS}}}f') is None, 'formula cells are not native observations')
    kind = cell.get('t', 'n')
    _require(kind in ('n', 's', 'inlineStr'), 'unsupported native cell type')
    style_id = int(cell.get('s', '0'))
    _require(0 <= style_id < len(styles), 'invalid cell style')
    style = styles[style_id]
    fmt_id = int(style.get('numFmtId', '0'))
    fill_id = int(style.get('fillId', '0'))
    _require(0 <= fill_id < len(fills), 'invalid fill index')
    colour = fills[fill_id].find(f'{{{NS}}}patternFill/{{{NS}}}fgColor')
    value = cell.find(f'{{{NS}}}v')
    raw = None if value is None else value.text
    if kind == 's':
        _require(raw is not None and raw.isdigit() and int(raw) < len(strings), 'invalid shared string index')
        raw = strings[int(raw)]
    elif kind == 'inlineStr':
        raw = ''.join(t.text or '' for t in cell.findall(f'.//{{{NS}}}t'))
    return {'raw': raw, 'cell_type': kind, 'style_index': style_id,
            'number_format': formats.get(fmt_id, 'BUILTIN:' + str(fmt_id)),
            'fill_colour': None if colour is None else dict(colour.attrib)}


def _quality_cell(cell):
    result = dict(cell)
    raw = cell['raw']
    if raw is None or raw in ('N.A', '-'):
        result.update(displayed=None, availability='MISSING', evidence_status='Q')
        return result
    _require(cell['cell_type'] == 'n', 'numeric observation must be a numeric cell')
    value = _decimal(raw)
    _require(value > 0, 'calorific source values must be positive')
    fmt = cell['number_format']
    if fmt == 'BUILTIN:0':
        result.update(displayed=None, displayed_decimal_places=None,
                      display_note='GENERAL_FORMAT_WIDTH_DEPENDENT_NOT_RENDERED',
                      availability='PRESENT', evidence_status='OBS')
        return result
    if fmt == 'BUILTIN:4':
        fmt = '#,##0.00'
    match = re.fullmatch(r'(?:#,##)?0\.(0+)', fmt)
    _require(match is not None, 'unsupported source numeric display format')
    places = len(match.group(1))
    with localcontext(ARITHMETIC):
        displayed = format(value.quantize(Decimal(1).scaleb(-places)), 'f')
    result.update(displayed=displayed, displayed_decimal_places=places,
                  availability='PRESENT', evidence_status='OBS')
    return result


def _exit_panel(raw, descriptor):
    """Parse only the exit sheet; retain raw lexemes and displayed precision."""
    year = descriptor['observation_year']
    _require(type(year) is int and year in (2024, 2025), 'explicit supported calendar observation year required')
    with ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        _require(len(names) == len(set(names)), 'duplicate ZIP member')
        _require(sum(i.file_size for i in archive.infolist()) < 30_000_000, 'oversized workbook')
        book = _xml(archive.read('xl/workbook.xml'), f'{{{NS}}}workbook')
        relationships = _xml(archive.read('xl/_rels/workbook.xml.rels'), f'{{{REL}}}Relationships')
        sheets = [s for s in book.findall(f'{{{NS}}}sheets/{{{NS}}}sheet') if s.get('name') == 'Exit_points']
        _require(descriptor['sheet'] == 'Exit_points' and len(sheets) == 1, 'unique Exit_points sheet required')
        rid = sheets[0].get(f'{{{RID}}}id')
        targets = [r for r in relationships if r.get('Id') == rid]
        _require(len(targets) == 1 and targets[0].get('TargetMode') is None
                 and targets[0].get('Type') == RID + '/worksheet', 'local worksheet relationship required')
        target = PurePosixPath(targets[0].get('Target', ''))
        _require(not target.is_absolute() and '..' not in target.parts and target.parts[0] == 'worksheets',
                 'unsafe worksheet target')
        sheet = _xml(archive.read('xl/' + str(target)), f'{{{NS}}}worksheet')
        strings = []
        if 'xl/sharedStrings.xml' in names:
            shared = _xml(archive.read('xl/sharedStrings.xml'), f'{{{NS}}}sst')
            strings = [''.join(t.text or '' for t in s.findall(f'.//{{{NS}}}t')) for s in shared]
        style = _xml(archive.read('xl/styles.xml'), f'{{{NS}}}styleSheet')
        formats = {int(f.get('numFmtId')): f.get('formatCode') for f in style.findall(f'{{{NS}}}numFmts/{{{NS}}}numFmt')}
        styles, fills = list(style.find(f'{{{NS}}}cellXfs')), list(style.find(f'{{{NS}}}fills'))
        cells, rows = {}, {}
        for row in sheet.findall(f'{{{NS}}}sheetData/{{{NS}}}row'):
            number = int(row.get('r'))
            _require(number > 0 and number not in rows, 'duplicate or invalid row')
            rows[number] = row
            for cell in row:
                address = cell.get('r', '')
                _require(re.fullmatch(r'[A-Z]+[1-9]\d*', address) is not None and
                         int(re.search(r'\d+$', address).group()) == number and address not in cells,
                         'duplicate or invalid cell coordinate')
                cells[address] = cell
        def cell(address):
            return _native_cell(cells.get(address), strings, styles, formats, fills)
        expected_headers = {
            'A1': f'WEIGHTED AVERAGE OF GROSS CALORIFIC VALUE AT EXIT POINTS BASED ON {year} DATA',
            'A2': 'EXIT POINT', 'B2': 'NETWORK CODE', 'C2': 'EIC', 'D2': 'NNO',
            'E2': f'{year} Yearly weighted average gross calorific value kWh/m3',
            'F2': f'{year} Yearly minimum gross calorific value kWh/m3',
            'G2': f'{year} Yearly maximum gross calorific value kWh/m3',
            'H2': f'{year} Yearly weighted average net calorific value MJ/m3'}
        for address, text in expected_headers.items():
            _require((cell(address)['raw'] or '').strip() == text, 'source header/year/unit mismatch: ' + address)
        records, notes, seen_eic, seen_network = [], [], set(), set()
        parent = None
        for number in sorted(rows):
            if number <= 2:
                continue
            native = {col: cell(f'{col}{number}') for col in 'ABCDEFGH'}
            values = {col: c['raw'] for col, c in native.items()}
            if not values['C']:
                _require(not any(values[c] is not None for c in 'DEFGH'), 'unidentified source point or values')
                if any(values[c] for c in 'AB'):
                    notes.append({'row': number, 'cells': native})
                parent = None
                continue
            _require(all(type(values[c]) is str and values[c] for c in 'ABCD'), 'point identity incomplete')
            _require(values['C'] not in seen_eic and values['B'] not in seen_network, 'duplicate EIC or network code')
            seen_eic.add(values['C']); seen_network.add(values['B'])
            quality = {col: _quality_cell(native[col]) for col in 'EFGH'}
            flags = []
            if any(c['availability'] == 'MISSING' for c in quality.values()):
                flags.append('MISSING_NATIVE_QUALITY')
            displayed = {col: None if q['availability'] == 'MISSING' else
                         Decimal(q['displayed'] if q['displayed'] is not None else q['raw'])
                         for col, q in quality.items()}
            if all(displayed[c] is not None for c in 'EFG'):
                if not displayed['F'] <= displayed['E'] <= displayed['G']:
                    flags.append('PUBLISHED_MEAN_OUTSIDE_PUBLISHED_EXTREMA')
                if displayed['F'] > displayed['G']:
                    flags.append('PUBLISHED_MINIMUM_EXCEEDS_MAXIMUM')
            if number in descriptor.get('source_context_review_rows', []):
                flags.append('SOURCE_CONTEXT_REVIEW_MIXED_REFERENCE_DIAGNOSTIC_NOT_PHYSICAL_RATIO')
            colour = (native['A']['fill_colour'] or {}).get('indexed')
            # Native legend colours identify overlapping merge rows. This is a
            # display-derived relationship hint, never a residential partition.
            role, parent_eic = 'UNCLASSIFIED_SOURCE_POINT', None
            if colour == '13':
                role, parent = 'SOURCE_MERGE_GROUP', values['C']
            elif colour in ('40', '42'):
                role, parent_eic = 'SOURCE_MERGE_CHILD', parent
                flags.append('GROUP_CHILD_OVERLAP_NOT_ADDITIVE')
                if parent is None:
                    flags.append('UNRESOLVED_GROUP_MEMBERSHIP')
            else:
                parent = None
            if role == 'SOURCE_MERGE_GROUP':
                flags.append('GROUP_CHILD_OVERLAP_NOT_ADDITIVE')
            name = values['A'].casefold()
            cues = [tag for token, tag in [('hu>', 'CROSS_BORDER'), ('ugs', 'STORAGE'),
                    ('fgt be', 'STORAGE'), ('virtuális', 'VIRTUAL'), ('mgp', 'VIRTUAL'),
                    ('saját veszteség', 'TSO_OWN_USE')] if token in name]
            records.append({'row': number, 'locator': f'Exit_points!A{number}:H{number}',
                            'source_id': descriptor['source_id'], 'artifact_id': descriptor['artifact_id'],
                            'observation_year': year, 'point_name': values['A'], 'network_code': values['B'],
                            'eic': values['C'], 'nno': values['D'], 'identity_cells': {k: native[k] for k in 'ABCD'},
                            'quality': quality, 'qc_flags': flags, 'source_merge_role': role,
                            'source_colour_parent_eic_hint': parent_eic, 'nonresidential_name_cues': cues,
                            'residential_eligibility': 'NOT_ESTABLISHED', 'measurement_assignment':
                            'SOURCE_PUBLISHED_STATISTIC_NOT_ALL_DIRECT_MEASUREMENT'})
        _require(len(records) == descriptor['expected_rows'], 'source row coverage mismatch')
        _require(any(n['cells']['A']['raw'] == 'The net calorific value is informative data' for n in notes),
                 'publisher NCV informative qualification missing')
    pairs = sum(all(r['quality'][c]['availability'] == 'PRESENT' for c in 'EH') for r in records)
    return {'provenance': descriptor, 'records': records, 'source_notes': notes,
            'summary': {'rows': len(records), 'unique_eics': len(seen_eic), 'numeric_average_pairs': pairs,
                        'missing_average_pairs': len(records) - pairs,
                        'complete_four_numeric_fields': sum(all(q['availability'] == 'PRESENT' for q in r['quality'].values()) for r in records),
                        'qc_flag_counts': dict(Counter(flag for r in records for flag in r['qc_flags'])),
                        'source_merge_role_counts': dict(Counter(r['source_merge_role'] for r in records))},
            'aggregation_authorized': False, 'physical_ratio_authorized': False}


def _eurostat(raw, descriptor, artifact):
    j = _json(raw)
    _require(j.get('class') == 'dataset' and j.get('version') == '2.0' and j.get('id') == DIMS,
             'expected JSON-stat namespace and dimensions')
    _require(j.get('source') == 'ESTAT' and j.get('extension', {}).get('id') == descriptor['dataset_id']
             and j.get('updated') == descriptor['updated'], 'dataset identity or vintage mismatch')
    sizes = j.get('size')
    _require(type(sizes) is list and len(sizes) == len(DIMS), 'invalid dimension sizes')
    axes = []
    for dim, size in zip(DIMS, sizes):
        index = j['dimension'][dim]['category']['index']
        _require(type(size) is int and size > 0 and type(index) is dict and len(index) == size
                 and all(type(v) is int for v in index.values()) and sorted(index.values()) == list(range(size)),
                 'invalid dimension index')
        axes.append([key for key, _ in sorted(index.items(), key=lambda item: item[1])])
    expected_enduses = [enduse.TOTAL_END_USE, *enduse.END_USES] if descriptor['dataset_id'] == 'NRG_D_HHQ' else [enduse.TOTAL_END_USE]
    _require(axes == [['A'], expected_enduses, ['G3000'], descriptor['units'], ['HU'], ['2024']],
             'explicit HU/G3000/calendar2024 scope, units and end uses required')
    length = 1
    for size in sizes:
        length *= size
    values, statuses = j.get('value'), j.get('status', {})
    _require(type(values) is dict and type(statuses) is dict, 'sparse native maps required')
    _require(all(re.fullmatch(r'0|[1-9]\d*', k) and int(k) < length for k in {*values, *statuses}),
             'invalid sparse observation index')
    _require(all(type(flag) is str for flag in statuses.values()), 'native status must be text')
    records = []
    for offset, keys in enumerate(itertools.product(*axes)):
        ix = str(offset); value = values.get(ix)
        if value is not None:
            _require(type(value) in (Decimal, int), 'native number required, not text or bool')
            _decimal(str(value))
        records.append({'coordinates': dict(zip(DIMS, keys)), 'raw_value': None if value is None else str(value),
                        'native_value_state': 'ABSENT' if ix not in values else ('NULL' if value is None else 'PRESENT'),
                        'availability': 'MISSING' if value is None else 'PRESENT',
                        'source_status': statuses.get(ix), 'source_status_present': ix in statuses,
                        'evidence_status': 'Q' if value is None else descriptor['evidence_status'],
                        'source_id': artifact['source_id'], 'artifact_id': artifact['artifact_id']})
    return {'metadata': descriptor, 'updated': j['updated'], 'native_dimensions': j['dimension'],
            'native_missing_positions': j.get('extension', {}).get('positions-with-no-data'), 'records': records}


class _HTMLTable(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.current, self.parts = [], None, None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.current = []
        elif tag in ('td', 'th') and self.current is not None:
            self.parts = []
    def handle_data(self, data):
        if self.parts is not None:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.parts is not None:
            self.current.append(''.join(self.parts).strip()); self.parts = None
        elif tag == 'tr' and self.current is not None:
            self.rows.append(self.current); self.current = None


def _ksh_annual_average(raw):
    charsets = re.findall(br'<meta\s+charset=[\"\']([^\"\']+)[\"\']', raw, re.I)
    _require(len(charsets) == 1 and charsets[0].upper() == b'ISO-8859-2', 'declared KSH ISO-8859-2 charset required')
    text = raw.decode('iso-8859-2')
    parser = _HTMLTable(); parser.feed(text)
    headers = ' '.join(c for r in parser.rows for c in r if 'háztartási' in c or 'fogyasztó háztartás' in c)
    _require('Vezetékes gázt fogyasztó háztartás' in headers and
             'Egy háztartási fogyasztóra jutó évi vezetékes gázfogyasztás, m³' in headers,
             'KSH household annual-average headers required')
    selected = [r for r in parser.rows if r and r[0] == '2024']
    _require(len(selected) == 1 and len(selected[0]) == 7, 'unique KSH 2024 row required')
    row = selected[0]
    def number(s):
        _require(re.fullmatch(r'\d{1,3}(?:[ \u00a0]\d{3})*(?:,\d+)?|\d+(?:,\d+)?', s), 'invalid native KSH number')
        return _decimal(s.replace(' ', '').replace('\u00a0', '').replace(',', '.'))
    consumers, average = number(row[3]), number(row[6])
    _require(consumers == consumers.to_integral_value(), 'integral KSH consumers required')
    return {'reference_year': 2024, 'charset': 'ISO-8859-2', 'native_cells': row,
            'household_consumers': str(consumers), 'annual_m3_per_consumer': str(average),
            'evidence_status': 'OBS', 'volume_reference_state': 'UNKNOWN'}


def _controls(raw, manifest, artifacts):
    meta = manifest['statistical_controls']; roles = manifest['roles']
    controls = {name: _eurostat(raw[roles[name]], meta[name], artifacts[roles[name]])
                for name in ('hhq', 'balance', 'commodity')}
    ksh = _ksh_annual_average(raw[roles['ksh_annual_average']])
    ksh.update(source_id=artifacts[roles['ksh_annual_average']]['source_id'], artifact_id=roles['ksh_annual_average'])
    rows = county.load_county_baseline(ROOT / 'registry/b11_county_gas_baseline_2024.csv')
    reconciliation = county.validate_county_baseline(rows)
    _require(all(r.source_id == artifacts[roles['ksh_original']]['source_id'] for r in rows), 'county source namespace mismatch')
    admitted = enduse.load_controls()
    for record in controls['hhq']['records']:
        key = (2024, record['coordinates']['nrg_bal'], 'G3000')
        _require(key in admitted, 'existing end-use control missing')
        previous = admitted[key]
        if record['availability'] == 'MISSING':
            _require(previous is None, 'fresh versus admitted missingness disagreement')
        else:
            _require(previous is not None and previous.source_id == record['source_id']
                     and previous.evidence_status == record['evidence_status']
                     and previous.value_tj == Decimal(record['raw_value'])
                     and previous.source_flag == (record['source_status'] or ''),
                     'fresh versus admitted end-use control disagreement')
    controls.update(ksh_annual_average=ksh, county={'rows': [asdict(r) for r in rows],
                    'reconciliation': asdict(reconciliation), 'original_artifact_id': roles['ksh_original'],
                    'scope': meta['ksh'], 'national_household_consumers': county.NATIONAL_HOUSEHOLD_CONSUMERS_2024,
                    'national_heating_consumers': county.NATIONAL_HEATING_CONSUMERS_2024,
                    'national_household_sales_thousand_m3': county.NATIONAL_HOUSEHOLD_GAS_SOLD_THOUSAND_M3_2024,
                    'published_monthly_m3_per_household': str(county.NATIONAL_MONTHLY_M3_PER_HOUSEHOLD_2024)})
    return controls


def _reconcile(controls):
    def value(name, end_use, unit):
        matches = [r for r in controls[name]['records'] if r['coordinates']['nrg_bal'] == end_use and r['coordinates']['unit'] == unit]
        _require(len(matches) == 1, 'unique native control cell required')
        return None if matches[0]['raw_value'] is None else Decimal(matches[0]['raw_value'])
    total = value('hhq', enduse.TOTAL_END_USE, 'TJ')
    balance = value('balance', enduse.TOTAL_END_USE, 'TJ')
    commodity = value('commodity', enduse.TOTAL_END_USE, 'TJ_GCV')
    _require(all(v is not None for v in (total, balance, commodity)), 'comparison controls unavailable')
    present = [Decimal(r['raw_value']) for r in controls['hhq']['records']
               if r['coordinates']['nrg_bal'] != enduse.TOTAL_END_USE and r['raw_value'] is not None]
    missing = [r['coordinates']['nrg_bal'] for r in controls['hhq']['records'] if r['raw_value'] is None]
    ksh = controls['ksh_annual_average']; native = controls['county']
    _require(Decimal(ksh['household_consumers']) == native['national_household_consumers'], 'KSH count comparison mismatch')
    with localcontext(ARITHMETIC):
        implied = Decimal(ksh['household_consumers']) * Decimal(ksh['annual_m3_per_consumer'])
        sales_m3 = Decimal(native['national_household_sales_thousand_m3']) * 1000
        return {'evidence_status': 'DER', 'known_present_end_use_residual_tj': str(total - sum(present)),
                'missing_end_uses': missing, 'complete_end_use_closure': not missing,
                'missing_is_zero': False, 'balance_minus_hhq_tj': str(balance - total),
                'commodity_times_090_minus_balance_tj': str(commodity * Decimal('0.90') - balance),
                'diagnostic_090_status': 'STATISTICAL_SERIES_ONLY_NOT_PHYSICAL_RATIO',
                'ksh_annual_average_implied_m3': str(implied),
                'ksh_annual_average_implied_minus_sales_m3': str(implied - sales_m3),
                'ksh_conflict_status': 'Q_CROSS_TABLE_METRIC_DISAGREEMENT' if implied != sales_m3 else 'RECONCILED',
                'ksh_sales_bcm_unit_rescaling': str(sales_m3 / Decimal('1000000000')),
                'cross_population_calibration': 'NOT_AUTHORIZED_UNMATCHED_UNIVERSES_AND_REFERENCE_STATES',
                'physical_calorific_mean': None, 'national_displacement': None}


def read_gas_quality_reference(source_paths, *, historical_scope):
    """Read all pinned inputs; caller must explicitly select the historical scope.

    Both calendar panels are returned separately. Calendar 2025 is comparative
    source inventory only and is never attached to the 2024 statistical controls.
    """
    _require(type(historical_scope) is str and historical_scope == HISTORICAL_SCOPE,
             'explicit historical2024 source/control handoff required')
    manifest = source_manifest()
    artifacts = {a['artifact_id']: a for a in manifest['source_artifacts']}
    _require(type(source_paths) is dict and set(source_paths) == set(artifacts),
             'exact required artifact-ID namespace and local source set required')
    # Validate every input, including original PDFs and existing consumer/data
    # dependencies, before parsing or producing any normalized output.
    for pin in manifest['repository_pins']:
        _pinned_bytes(ROOT / pin['path'], pin)
    raw = {aid: _pinned_bytes(source_paths[aid], pin) for aid, pin in artifacts.items()}
    panels = []
    for descriptor in manifest['panels']:
        enriched = {**descriptor, 'source_id': artifacts[descriptor['artifact_id']]['source_id']}
        panels.append(_exit_panel(raw[descriptor['artifact_id']], enriched))
    controls = _controls(raw, manifest, artifacts)
    return {'reference_id': REFERENCE_ID, 'historical_scope': historical_scope,
            'source_validation': [{'artifact_id': a['artifact_id'], 'source_id': a['source_id'],
                'sha256': a['sha256'], 'byte_count': a['byte_count'], 'validated': True} for a in artifacts.values()],
            'manifest_sha256': MANIFEST_SHA256, 'repository_pins': manifest['repository_pins'],
            'panels': panels, 'calorific_fields': manifest['calorific_fields'], 'controls': controls,
            'reconciliation': _reconcile(controls), 'methodology_evidence': manifest['methodology_evidence'],
            'source_defects': manifest['source_defects'], 'boundaries': manifest['boundaries'],
            'private_use_scope': 'PERSONAL_SOURCE_ANALYSIS_ONLY_BROADER_USE_UNRESOLVED',
            'storage_policy': 'PRIVATE_NUMERIC_OUTPUT_NOT_FOR_PUBLIC_COMMIT'}
