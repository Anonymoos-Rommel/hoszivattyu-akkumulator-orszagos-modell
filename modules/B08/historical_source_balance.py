"""Read-only historical source-reference comparison on the native UTC2025 grid.

Every public invocation verifies existing source/hand-off pins. Arithmetic uses
original Decimal MW cells; the accepted float kW panel is a cross-check only.
No files are written. Exhaust the iterator to establish complete-window validity,
or use historical_source_balance(), which returns only after all checks pass.
This DER/E2 diagnostic is neither measured exchange nor a programme/adequacy run.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo

from modules.B08.gui_load_reference import _manifest as load_manifest
from modules.B08.observed_load_contract import ENTSOE_SOURCE_ID as LOAD_SOURCE_ID
from modules.B09 import gui_generation_reference as generation

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b08_b09_historical_balance_manifest.json'
START = generation.START
END = generation.END
STEP = generation.STEP
HOURS = Decimal('0.25')
ZERO = Decimal(0)
LOAD_ID = 'B08B09-P5-R01'
COMPANION_ID = 'B08B09-P5-R02'
EVIDENCE_TIER = 'E2_PROVISIONAL_BASE'
SOURCE_MODEL_USE = 'QUALIFIED_E2_MODEL_USE'
MODEL_USE = 'HISTORICAL_SOURCE_REFERENCE_ONLY'
ACTIVE = ('B01', 'B02', 'B04', 'B05', 'B06', 'B09', 'B11', 'B12',
          'B14', 'B15', 'B16', 'B17', 'B19', 'B20')
STRUCTURAL = ('B03', 'B07', 'B08', 'B10', 'B13', 'B18', 'B25')
QUANTITIES = ('load', 'injection', 'source_withdrawal', 'signed_generation',
              'source_reference_residual', 'positive_residual', 'negative_residual_magnitude')
AUTHORITY_FILES = (
    'modules/B08/gui_load_reference.py', 'modules/B08/observed_load_contract.py',
    'modules/B09/gui_generation_reference.py', 'modules/B09/signed_net_recovery_contract.py',
    'modules/B09/observed_generation_contract.py', 'modules/B09/engine.py',
    'registry/b08_b09_p5_entsoe_gui_export_acquisition.csv',
    'registry/b09_gui_reference_manifest.json', 'registry/b09_p6_mavir_operational_acquisition.csv',
    'registry/b09_p7_signed_net_generation_semantics.csv',
    'docs/checkpoints/V1_016_ACCEPTANCE.json', 'docs/checkpoints/V1_017_ACCEPTANCE.json',
    'docs/checkpoints/V1_016_VERIFICATION.json', 'docs/checkpoints/V1_017_VERIFICATION.json',
)


class HistoricalBalanceError(ValueError):
    """Source identity, temporal, quantity, missingness or evidence check failed."""


def _require(condition, message):
    if not condition:
        raise HistoricalBalanceError(message)


def _number(value, *, nonnegative=False):
    _require(isinstance(value, (str, Decimal)), 'source numbers must preserve decimal text')
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise HistoricalBalanceError('explicit finite numeric source value required') from exc
    _require(result.is_finite() and (not nonnegative or result >= 0),
             'source number violates finite/sign boundary')
    return result


def _fields(row, expected, context):
    _require(row is not None and all(row.get(k) == v for k, v in expected.items()),
             context + ' contract mismatch')


def _digest(handle):
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: handle.read(1024 * 1024), b''):
        digest.update(block)
        size += len(block)
    return digest.hexdigest(), size


def _pin(path, pin):
    with Path(path).open('rb') as handle:
        _require(_digest(handle) == (pin['sha256'], pin['bytes']), 'exact source bytes/hash required')


@contextmanager
def _pinned_csv(path, pin):
    # Hash and parse the same open descriptor, as in the existing XLSX reader.
    import io
    with Path(path).open('rb') as binary:
        _require(_digest(binary) == (pin['sha256'], pin['bytes']), 'exact handoff bytes/hash required')
        binary.seek(0)
        with io.TextIOWrapper(binary, encoding='utf-8', newline='') as handle:
            yield csv.DictReader(handle)


def _contract():
    contract = json.loads(MANIFEST.read_text(encoding='utf-8'))
    _fields(contract, {
        'reference_id': 'B08-B09-HISTORICAL-SOURCE-REFERENCE-UTC2025',
        'evidence_status': 'DER', 'evidence_tier': EVIDENCE_TIER,
        'source_model_use_status': SOURCE_MODEL_USE, 'model_use_status': MODEL_USE,
        'raw_storage_policy': 'EXTERNAL_ONLY',
        'public_raw_reuse_status': 'NOT_ESTABLISHED_FREE_REUSE',
        'start_utc': START.isoformat(), 'end_utc_exclusive': END.isoformat(),
        'interval_convention': 'INTERVAL_START_HALF_OPEN', 'resolution': 'PT15M',
        'spatial_grain': 'BZN|HU', 'source_power_unit': 'MW', 'runtime_power_unit': 'kW',
        'active_production_type_codes': list(ACTIVE), 'structural_ne_type_codes': list(STRUCTURAL),
    }, 'historical reference')
    _require(set(contract['handoffs']) == {'civil_load', 'generation', 'recovery_lineage'},
             'exact accepted handoff set required')
    _require(set(contract['authority_sha256']) == set(AUTHORITY_FILES),
             'complete existing source authority pin set required')
    for relative, digest in contract['authority_sha256'].items():
        _require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
                 'authority must be a repository-relative identity')
        with (ROOT / relative).open('rb') as handle:
            _require(_digest(handle)[0] == digest, 'accepted source authority changed: ' + relative)
    for relative in ('docs/checkpoints/V1_016_ACCEPTANCE.json', 'docs/checkpoints/V1_017_ACCEPTANCE.json'):
        _require(json.loads((ROOT / relative).read_text())['status'] == 'ACCEPTED',
                 'existing narrow source acceptance required')
    load_verification = json.loads((ROOT / 'docs/checkpoints/V1_016_VERIFICATION.json').read_text())
    generation_verification = json.loads((ROOT / 'docs/checkpoints/V1_017_VERIFICATION.json').read_text())
    accepted_hashes = {
        'civil_load': load_verification['source_verification']['normalized_csv_sha256'],
        'generation': generation_verification['external_output_sha256']['panel_csv'],
        'recovery_lineage': generation_verification['external_output_sha256']['lineage_csv'],
    }
    for key, digest in accepted_hashes.items():
        _fields(contract['handoffs'][key], {'sha256': digest, 'storage_policy': 'EXTERNAL_ONLY'},
                'accepted handoff pin')
    _fields(contract['source_evidence']['load'],
            {'evidence_status': 'DER', 'evidence_tier': EVIDENCE_TIER, 'source_id': LOAD_SOURCE_ID},
            'underlying load evidence')
    _fields(contract['source_evidence']['generation'],
            {'record_evidence_status': 'Q', 'evidence_tier': EVIDENCE_TIER,
             'source_id': generation.ENTSOE_SOURCE_ID, 'source_semantics': generation.SOURCE_SEMANTICS},
            'underlying generation evidence')
    _fields(contract['coverage_limits'], {'complete_native_utc2025': True,
                                         'complete_budapest_civil2025': False,
                                         'complete_meteorological_winter': False}, 'coverage limits')
    artifacts = {a.acquisition_record_id: a for a in generation.source_artifacts()}
    for record_id in (LOAD_ID, COMPANION_ID):
        m = load_manifest(record_id)
        artifacts[record_id] = generation.SourceArtifact(
            record_id, LOAD_SOURCE_ID, m['external_filename'], m['sha256'],
            int(m['bytes']), int(m['data_rows']))
    pins = {p['acquisition_record_id']: p for p in contract['source_artifacts']}
    _require(len(pins) == len(contract['source_artifacts']) and set(pins) == set(artifacts),
             'exact eight accepted original source identities required')
    for key, artifact in artifacts.items():
        _fields(pins[key], {'source_id': artifact.source_id, 'sha256': artifact.sha256,
                           'bytes': artifact.byte_count}, 'original source pin')
    return contract, artifacts


@dataclass(frozen=True)
class Recovery:
    value_mw: Decimal
    a75_cell: str
    # Acquisition ID, source hash, source cell. All identical copies preserved.
    copies: tuple[tuple[str, str, str], ...]


def _read_recovery(rows, artifacts):
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        code, iso = row['production_type_code'], row['start_utc']
        _require(code in generation.RECOVERY_COLUMNS, 'recovery outside B04/B06/B12 scope')
        try:
            timestamp = datetime.fromisoformat(iso)
        except ValueError as exc:
            raise HistoricalBalanceError('invalid recovery UTC timestamp') from exc
        _require(timestamp.tzinfo is not None and timestamp.utcoffset() == timedelta(0)
                 and START <= timestamp < END and (timestamp - START) % STEP == timedelta(0),
                 'recovery timestamp outside native UTC PT15M grid')
        artifact = artifacts.get(row['operational_acquisition_record_id'])
        _require(artifact is not None and artifact.acquisition_record_id in generation.OPERATIONAL_IDS,
                 'recovery must reference an accepted operational source')
        _fields(row, {'a75_acquisition_record_id': generation.GENERATION_ID,
                      'a75_sha256': artifacts[generation.GENERATION_ID].sha256,
                      'operational_sha256': artifact.sha256}, 'recovery source')
        _require(row['selected_for_recovery'] in ('True', 'False'), 'explicit recovery selection required')
        cell = row['operational_cell']
        _require(re.fullmatch(generation._column_name(generation.RECOVERY_COLUMNS[code]) + r'[1-9][0-9]*', cell),
                 'recovery operational column/type mismatch')
        locator = (timestamp, code, artifact.acquisition_record_id)
        _require(locator not in seen, 'duplicate recovery source copy')
        seen.add(locator)
        groups[(timestamp, code)].append((row, _number(row['source_signed_power_mw'])))
    result = {}
    for key, copies in groups.items():
        copies.sort(key=lambda pair: pair[0]['operational_acquisition_record_id'])
        first, value = copies[0]
        for i, (row, number) in enumerate(copies):
            _require(number == value and row['a75_cell'] == first['a75_cell']
                     and row['selected_for_recovery'] == str(i == 0),
                     'recovery copies conflict or deterministic selection changed')
        result[key] = Recovery(value, first['a75_cell'], tuple(
            (r['operational_acquisition_record_id'], r['operational_sha256'], r['operational_cell'])
            for r, _ in copies))
    return result


def _verify_recovery_originals(source_paths, artifacts, recoveries):
    """Replay every retained recovery copy, without claiming a full overlap replay."""
    locators = defaultdict(dict)
    for (timestamp, code), recovery in recoveries.items():
        column = generation.RECOVERY_COLUMNS[code]
        for record_id, _, cell in recovery.copies:
            number = int(re.sub('[A-Z]', '', cell))
            _require((number, column) not in locators[record_id], 'duplicate original recovery locator')
            locators[record_id][number, column] = (timestamp, recovery.value_mw)
    for record_id in generation.OPERATIONAL_IDS:
        rows = iter(generation._xlsx_rows(source_paths[record_id], artifacts[record_id], 'Exportált adatok'))
        _require(next(rows, None) == (1, dict(enumerate(generation.MAVIR_HEADERS, 1))),
                 'operational source header mismatch')
        remaining = dict(locators[record_id])
        count = 0
        for n, row in rows:
            _require(n == count + 2, 'operational source row sequence mismatch')
            count += 1
            for column in generation.RECOVERY_COLUMNS.values():
                expected = remaining.pop((n, column), None)
                if expected is not None:
                    _require(1 in row and column in row
                             and generation._mavir_start(row[1]) == expected[0]
                             and _number(row[column]) == expected[1],
                             'recovery original timestamp/cell/value mismatch')
        _require(not remaining and count == artifacts[record_id].data_rows,
                 'recovery source locator or raw row missing')


def _headers(rows, final_row, expected, context):
    iterator = iter(rows)
    header = {}
    for n, row in iterator:
        _require(n <= final_row and n not in header, context + ' missing/duplicate header')
        header[n] = row
        if n == final_row:
            break
    _require(all(header.get(r, {}).get(c) == v for (r, c), v in expected.items()),
             context + ' product/unit/geography/time/forecast mismatch')
    return iterator, header


def _loads(rows, *, start=START, end=END):
    iterator, _ = _headers(rows, 7, {
        (1, 1): 'Total Load - Day-ahead / Actual', (2, 1): 'Actual Total Load [6.1.A]',
        (3, 1): 'Day-ahead Total Load Forecast [6.1.B]',
        (4, 1): '01/01/2025 00:00 - 01/01/2026 00:00 (UTC)',
        (6, 1): 'MTU', (6, 2): 'BZN|HU', (6, 3): 'BZN|HU', (7, 1): 'MTU',
        (7, 2): 'Actual Total Load (MW)', (7, 3): 'Day-ahead Total Load Forecast (MW)',
    }, 'load')
    count = 0
    for n, row in iterator:
        timestamp = start + count * STEP
        _require(n == count + 8 and timestamp + STEP <= end and set(row) == {1, 2, 3},
                 'load row/cell grid incomplete or extended')
        mtu = timestamp.strftime('%d/%m/%Y %H:%M') + ' - ' + (timestamp + STEP).strftime('%d/%m/%Y %H:%M')
        _require(row[1] == mtu, 'load MTU gap/order/duration mismatch')
        yield timestamp, _number(row[2], nonnegative=True), 'B' + str(n)
        count += 1
    _require(start + count * STEP == end, 'incomplete native load window')


def _generation_rows(rows):
    iterator, header = _headers(rows, 6, {
        (1, 1): 'Actual Generation per Production Type - Generation',
        (2, 1): 'Aggregated Generation per Type [16.1.B&C]',
        (3, 1): '01/01/2025 00:00 - 01/01/2026 00:00 (UTC)',
        (5, 1): 'MTU', (6, 1): 'MTU',
    }, 'generation')
    _require(set(header[5]) == set(range(1, 23)) and set(header[6]) == set(range(1, 23))
             and all(header[5][c] == 'BZN|HU' for c in range(2, 23)),
             'generation geography/column grid mismatch')
    labels = [header[6][c] for c in range(2, 23)]
    _require(len(set(labels)) == 21 and set(labels) == {n + ' (MW)' for n in generation.PSR_CODES},
             'generation type/unit mismatch')
    return iterator, {generation.PSR_CODES[header[6][c][:-5]]: c for c in range(2, 23)}


@dataclass(frozen=True)
class Contribution:
    production_type_code: str
    signed_power_mw: Decimal
    a75_cell: str
    recovery: Recovery | None


@dataclass(frozen=True)
class SourceProvenance:
    source_id: str
    acquisition_record_id: str
    sha256: str
    evidence_status: str
    evidence_tier: str = EVIDENCE_TIER
    model_use_status: str = SOURCE_MODEL_USE
    raw_storage_policy: str = 'EXTERNAL_ONLY'
    public_raw_reuse_status: str = 'NOT_ESTABLISHED_FREE_REUSE'


@dataclass(frozen=True)
class BalanceInterval:
    start_utc: datetime
    end_utc: datetime
    actual_load_mw: Decimal
    injection_mw: Decimal
    source_withdrawal_mw: Decimal
    signed_generation_mw: Decimal
    source_reference_residual_mw: Decimal
    load_cell: str
    generation_source_row: int
    contributions: tuple[Contribution, ...]
    maximum_runtime_difference_mw: Decimal
    runtime_signed_power_mw: Decimal
    load_source: SourceProvenance
    generation_source: SourceProvenance
    evidence_status: str = 'DER'
    evidence_tier: str = EVIDENCE_TIER
    model_use_status: str = MODEL_USE


def _runtime_value(row, *, timestamp, code, cell, value, recovery, artifact):
    refs = generation.ENTSOE_SOURCE_ID
    if recovery is not None:
        refs += ';' + generation.MAVIR_NET_OPERATIONAL_SOURCE_ID
    selected = recovery.copies[0] if recovery else ('', '', '')
    _fields(row, {
        'start_utc': timestamp.isoformat(), 'end_utc': (timestamp + STEP).isoformat(),
        'timestep_hours': '0.25', 'production_type_code': code,
        'region_id': 'HUNGARY_CONTROL_AREA', 'region_scheme': 'ENTSOE_CONTROL_AREA',
        'truth_context': 'REAL', 'evidence_status': 'Q', 'evidence_tier': EVIDENCE_TIER,
        'model_use_status': SOURCE_MODEL_USE, 'source_refs': refs,
        'a75_acquisition_record_id': artifact.acquisition_record_id,
        'a75_sha256': artifact.sha256, 'a75_cell': cell,
        'boundary_id': 'SIGNED_NET_GENERATION_AC' if recovery else 'GENERATION_AC',
        'selected_operational_acquisition_record_id': selected[0],
        'selected_operational_sha256': selected[1], 'selected_operational_cell': selected[2],
    }, 'generation runtime')
    injection = _number(row['delivered_generation_kw'], nonnegative=True)
    withdrawal = _number(row['source_withdrawal_kw'], nonnegative=True)
    net = _number(row['net_generation_contribution_kw'])
    _require(not (injection > 0 and withdrawal > 0) and injection - withdrawal == net,
             'runtime signed injection-minus-withdrawal identity failed')
    # Exact accepted float conversion compatibility; never feed float values into the balance.
    for actual, source in ((injection, max(value, ZERO)), (withdrawal, max(-value, ZERO)), (net, value)):
        _require(actual == Decimal(str(float(source) * 1000.0)), 'runtime/source MW-kW conversion mismatch')
    return net / Decimal(1000)


def _iter_balance(load_rows, generation_rows, runtime_rows, recoveries, artifact, *, load_artifact,
                  start=START, end=END):
    loads = iter(_loads(load_rows, start=start, end=end))
    rows, columns = _generation_rows(generation_rows)
    runtime = iter(runtime_rows)
    load_source = SourceProvenance(load_artifact.source_id, load_artifact.acquisition_record_id,
                                  load_artifact.sha256, 'DER')
    generation_source = SourceProvenance(artifact.source_id, artifact.acquisition_record_id,
                                        artifact.sha256, 'Q')
    used = set()
    count = 0
    for n, row in rows:
        timestamp = start + count * STEP
        _require(n == count + 7 and timestamp + STEP <= end and set(row) == set(range(1, 23)),
                 'generation row/cell grid incomplete or extended')
        mtu = timestamp.strftime('%d/%m/%Y %H:%M:%S') + ' - ' + (timestamp + STEP).strftime('%d/%m/%Y %H:%M:%S')
        _require(row[1] == mtu, 'generation MTU gap/order/duration mismatch')
        load_row = next(loads, None)
        _require(load_row is not None and load_row[0] == timestamp, 'load/generation interval mismatch')
        _, load, load_cell = load_row
        contributions = []
        with localcontext() as context:
            context.prec = 40
            injection = withdrawal = runtime_net = error = ZERO
            for code in sorted(columns):
                value_text = row[columns[code]]
                cell = generation._column_name(columns[code]) + str(n)
                if code in STRUCTURAL:
                    _require(value_text == 'n/e', 'structural n/e must not become measured zero')
                    continue
                key = (timestamp, code)
                recovery = recoveries.get(key)
                if value_text == '':
                    _require(code in generation.RECOVERY_COLUMNS and recovery is not None,
                             'missing active value requires exact accepted recovery')
                    _require(recovery.a75_cell == cell, 'recovery original cell mismatch')
                    value = recovery.value_mw
                    used.add(key)
                else:
                    _require(recovery is None, 'numeric original must not be replaced by recovery')
                    value = _number(value_text, nonnegative=True)
                net = _runtime_value(next(runtime, None), timestamp=timestamp, code=code, cell=cell,
                                     value=value, recovery=recovery, artifact=artifact)
                runtime_net += net
                error = max(error, abs(net - value))
                injection += max(value, ZERO)
                withdrawal += max(-value, ZERO)
                contributions.append(Contribution(code, value, cell, recovery))
            signed = injection - withdrawal
            residual = load - signed
            _require(load == signed + residual and sum((c.signed_power_mw for c in contributions), ZERO) == signed,
                     'interval quantity conservation failed')
            result = BalanceInterval(timestamp, timestamp + STEP, load, injection, withdrawal, signed,
                                     residual, load_cell, n, tuple(contributions), error, runtime_net,
                                     load_source, generation_source)
        yield result
        count += 1
    _require(start + count * STEP == end and next(loads, None) is None and next(runtime, None) is None,
             'incomplete/extra/unmatched source window')
    _require(used == set(recoveries), 'unused or missing recovery keys')


def _civil_row(row, timestamp, artifacts):
    record_id = COMPANION_ID if timestamp < START else LOAD_ID
    _fields(row, {'start_utc': timestamp.isoformat(), 'end_utc': (timestamp + STEP).isoformat(),
                  'timestep_hours': '0.25', 'source_id': LOAD_SOURCE_ID,
                  'source_revision': record_id + ':' + artifacts[record_id].sha256,
                  'evidence_status': 'DER', 'evidence_tier': EVIDENCE_TIER}, 'civil load')
    return _number(row['actual_load_mw'], nonnegative=True)


def iter_historical_source_balance(source_paths: Mapping[str, Path], handoff_paths: Mapping[str, Path]):
    """Stream the fixed 35,040 native UTC2025 intervals; caller owns source paths.

    source_paths must name all eight existing original acquisition IDs. Handoff
    keys are civil_load, generation and recovery_lineage. All bytes stay external.
    Do not interpret a partially consumed iterator as complete-year validation.
    """
    contract, artifacts = _contract()
    _require(set(source_paths) == set(artifacts), 'exact eight original source paths required')
    _require(set(handoff_paths) == set(contract['handoffs']), 'exact three accepted handoff paths required')
    for key, artifact in artifacts.items():
        _pin(source_paths[key], {'sha256': artifact.sha256, 'bytes': artifact.byte_count})
    active, structural = generation._parse_capacity(generation._xlsx_rows(
        source_paths[generation.CAPACITY_ID], artifacts[generation.CAPACITY_ID], '1'))
    _require(tuple(sorted(active.values())) == ACTIVE and tuple(sorted(structural.values())) == STRUCTURAL,
             'accepted active/structural capacity type contract changed')
    with ExitStack() as stack:
        csvs = {key: stack.enter_context(_pinned_csv(handoff_paths[key], pin))
                for key, pin in contract['handoffs'].items()}
        recoveries = _read_recovery(csvs['recovery_lineage'], artifacts)
        _require(len(recoveries) == 4820 and sum(len(r.copies) for r in recoveries.values()) == 9965,
                 'accepted recovery coverage changed')
        _verify_recovery_originals(source_paths, artifacts, recoveries)
        civil = iter(csvs['civil_load'])
        for i in range(4):
            _civil_row(next(civil, None), START - timedelta(hours=1) + i * STEP, artifacts)
        stream = _iter_balance(
            generation._xlsx_rows(source_paths[LOAD_ID], artifacts[LOAD_ID], '1'),
            generation._xlsx_rows(source_paths[generation.GENERATION_ID], artifacts[generation.GENERATION_ID], '1'),
            csvs['generation'], recoveries, artifacts[generation.GENERATION_ID],
            load_artifact=artifacts[LOAD_ID])
        for row in stream:
            if row.start_utc < END - timedelta(hours=1):
                _require(_civil_row(next(civil, None), row.start_utc, artifacts) == row.actual_load_mw,
                         'native/civil load overlap mismatch')
            yield row
        _require(next(civil, None) is None, 'extra civil-year load rows')


def _powers(row):
    residual = row.source_reference_residual_mw
    return dict(zip(QUANTITIES, (row.actual_load_mw, row.injection_mw, row.source_withdrawal_mw,
                                row.signed_generation_mw, residual, max(residual, ZERO), max(-residual, ZERO))))


def _coincident(row):
    return {'start_utc': row.start_utc.isoformat(), 'end_utc': row.end_utc.isoformat(),
            'start_budapest': row.start_utc.astimezone(ZoneInfo('Europe/Budapest')).isoformat(),
            **{key + '_mw': str(value) for key, value in _powers(row).items()},
            'load_cell': row.load_cell, 'generation_source_row': row.generation_source_row}


def _extreme(peaks, key, value, row, *, maximum=True):
    old = peaks.get(key)
    if old is None or (value > Decimal(old['value_mw']) if maximum else value < Decimal(old['value_mw'])):
        peaks[key] = {'value_mw': str(value), 'coincident_intervals': [_coincident(row)]}
    elif value == Decimal(old['value_mw']):
        old['coincident_intervals'].append(_coincident(row))


def _conserve(energy):
    _require(energy['load'] == energy['signed_generation'] + energy['source_reference_residual']
             and energy['signed_generation'] == energy['injection'] - energy['source_withdrawal']
             and energy['source_reference_residual'] == energy['positive_residual'] - energy['negative_residual_magnitude'],
             'energy conservation failed')


def _summarize(rows: Iterable[BalanceInterval], *, start=START, end=END):
    energies = {key: ZERO for key in QUANTITIES}
    monthly, by_type, type_peaks, peaks = {}, defaultdict(lambda: ZERO), {}, {}
    counts, local_days = Counter(), Counter()
    error = runtime_energy = ZERO
    with localcontext() as context:
        context.prec = 40
        for row in rows:
            _require(row.start_utc == start + counts['intervals'] * STEP and row.end_utc == row.start_utc + STEP
                     and row.end_utc <= end, 'summary requires complete ordered PT15M grid')
            _require(tuple(c.production_type_code for c in row.contributions) == ACTIVE,
                     'summary active type coverage mismatch')
            powers = _powers(row)
            month = monthly.setdefault(row.start_utc.strftime('%Y-%m'),
                                       {'intervals': 0, 'energy_mwh': {k: ZERO for k in QUANTITIES},
                                        'generation_by_type_mwh': {c: ZERO for c in ACTIVE}})
            month['intervals'] += 1
            for key, value in powers.items():
                energies[key] += value * HOURS
                month['energy_mwh'][key] += value * HOURS
            recovered = 0
            for contribution in row.contributions:
                code, value = contribution.production_type_code, contribution.signed_power_mw
                by_type[code] += value * HOURS
                month['generation_by_type_mwh'][code] += value * HOURS
                old = type_peaks.get(code)
                if old is None or value > Decimal(old['value_mw']):
                    type_peaks[code] = {'value_mw': str(value), 'timestamps_utc': [row.start_utc.isoformat()]}
                elif value == Decimal(old['value_mw']):
                    old['timestamps_utc'].append(row.start_utc.isoformat())
                if contribution.recovery is not None:
                    recovered += 1
                    counts['recovery_' + code] += 1
                    counts['recovery_negative' if value < 0 else 'recovery_positive' if value > 0 else 'recovery_zero'] += 1
                else:
                    counts['original_numeric_cells'] += 1
            counts['recovery_cells'] += recovered
            counts['recovered_intervals'] += bool(recovered)
            counts['runtime_records'] += len(row.contributions)
            counts['structural_ne_cells'] += len(STRUCTURAL)
            counts['intervals'] += 1
            residual = row.source_reference_residual_mw
            counts['positive_residual_intervals' if residual > 0 else 'negative_residual_intervals' if residual < 0 else 'zero_residual_intervals'] += 1
            local_days[row.start_utc.astimezone(ZoneInfo('Europe/Budapest')).date().isoformat()] += 1
            error = max(error, row.maximum_runtime_difference_mw)
            runtime_energy += row.runtime_signed_power_mw * HOURS
            for label, key, maximum in (
                ('load_peak', 'load', True), ('generation_peak', 'signed_generation', True),
                ('generation_minimum', 'signed_generation', False), ('residual_peak', 'source_reference_residual', True),
                ('residual_minimum', 'source_reference_residual', False), ('source_withdrawal_peak', 'source_withdrawal', True),
            ):
                _extreme(peaks, label, powers[key], row, maximum=maximum)
        _require(start + counts['intervals'] * STEP == end, 'summary window incomplete')
        _conserve(energies)
        _require(sum(by_type.values(), ZERO) == energies['signed_generation'], 'annual technology conservation failed')
        for month in monthly.values():
            _conserve(month['energy_mwh'])
            _require(sum(month['generation_by_type_mwh'].values(), ZERO) == month['energy_mwh']['signed_generation'],
                     'monthly technology conservation failed')
        for key in QUANTITIES:
            _require(sum((m['energy_mwh'][key] for m in monthly.values()), ZERO) == energies[key],
                     'monthly/annual quantity conservation failed')
        for code in ACTIVE:
            _require(sum((m['generation_by_type_mwh'][code] for m in monthly.values()), ZERO) == by_type[code],
                     'monthly/annual technology conservation failed')
        rounding = {'maximum_cell_absolute_difference_mw': str(error),
                    'runtime_signed_energy_mwh': str(runtime_energy),
                    'runtime_minus_source_decimal_energy_mwh': str(runtime_energy - energies['signed_generation'])}
    for key in ('zero_residual_intervals', 'positive_residual_intervals', 'negative_residual_intervals'):
        counts.setdefault(key, 0)
    return {'energy_mwh': {k: str(v) for k, v in energies.items()}, 'counts': dict(counts), 'peaks': peaks,
            'monthly_utc': {key: {'intervals': value['intervals'],
                                 'energy_mwh': {k: str(v) for k, v in value['energy_mwh'].items()},
                                 'generation_by_type_mwh': {k: str(v) for k, v in value['generation_by_type_mwh'].items()}}
                            for key, value in monthly.items()},
            'generation_by_type': {code: {'energy_mwh': str(value), 'peak': type_peaks[code]}
                                   for code, value in by_type.items()},
            'source_runtime_rounding': rounding,
            'dst_local_day_intervals': {day: local_days[day] for day in ('2025-03-30', '2025-10-26')}}


def historical_source_balance(source_paths: Mapping[str, Path], handoff_paths: Mapping[str, Path]):
    """Return fully validated calculated totals/months/type conservation and ties.

    Returned data retains private source lineage; this API grants no permission
    to publish raw panels. It does not accept programme profiles or targets.
    """
    result = _summarize(iter_historical_source_balance(source_paths, handoff_paths))
    contract, _ = _contract()
    _fields(result['counts'], {'intervals': 35040, 'runtime_records': 490560,
                              'original_numeric_cells': 485740, 'recovery_cells': 4820,
                              'recovery_B04': 2, 'recovery_B06': 4817, 'recovery_B12': 1,
                              'recovery_negative': 4812, 'recovery_zero': 6, 'recovery_positive': 2},
            'accepted source coverage')
    result.update({key: contract[key] for key in (
        'reference_id', 'evidence_status', 'evidence_tier', 'source_model_use_status', 'model_use_status',
        'raw_storage_policy', 'public_raw_reuse_status', 'source_artifacts', 'handoffs',
        'quantity_contract', 'coverage_limits', 'source_evidence', 'excluded_claims')})
    result['time_contract'] = {'start_utc': START.isoformat(), 'end_utc_exclusive': END.isoformat(),
                               'interval_convention': 'INTERVAL_START_HALF_OPEN', 'resolution': 'PT15M',
                               'intervals': 35040, 'hours': '8760', 'complete_native_utc2025': True,
                               'naive_existing_csv_overlap_intervals': 35036}
    result['coverage'] = {'load_missing': 0, 'generation_remaining_active_missing': 0,
                          'active_numeric_types': list(ACTIVE), 'structural_ne_types': list(STRUCTURAL),
                          'recovery_copy_locators_replayed_from_originals': 9965,
                          'full_mavir_all_field_overlap_replay': 'INHERITED_V1_017_NOT_REPEATED'}
    return result
