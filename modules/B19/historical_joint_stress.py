"""Dated, co-occurring historical weather/load/source-balance windows.

A caller supplies the duration; there is no adopted stress horizon or policy.
Quarter-hour source powers are integrated before the physical hourly join.
Ranking uses exact rational sums, never independently combined extrema. Every
source iterator is exhausted before a result is returned. This is a historical
diagnostic, not imports, adequacy, return periods or a national weather model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path

from modules.B08 import historical_source_balance as historical

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b19_historical_joint_stress_manifest.json'
MANIFEST_SHA256 = '0466a0ed61cdab5110a41c42a29e3fefe0a4a4197bc2ad36b42a91cdb7af5036'
HOUR = timedelta(hours=1)
QUARTER = timedelta(minutes=15)
GRID_FIELDS = ('actual_load_mw', 'injection_mw', 'source_withdrawal_mw',
               'signed_generation_mw', 'source_reference_residual_mw')
ENERGY_FIELDS = ('load_mwh', 'injection_mwh', 'source_withdrawal_mwh',
                 'signed_generation_mwh', 'source_reference_residual_mwh')
CRITERIA = {'COLDEST_MEAN_BUDAPEST_TEMPERATURE': ('temperature_sum_c', 'min'),
            'HIGHEST_MEAN_SOURCE_LOAD': ('load_mwh', 'max'),
            'HIGHEST_MEAN_SOURCE_REFERENCE_RESIDUAL': ('source_reference_residual_mwh', 'max')}
AUTHORITY = ('modules/B08/historical_source_balance.py',
             'registry/b08_b09_historical_balance_manifest.json',
             'registry/b05_annual_device_reference_manifest.json')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _utc(value):
    _require(isinstance(value, datetime) and value.tzinfo is not None
             and value.utcoffset() == timedelta(0), 'explicit UTC timestamp required')
    return value


def _endpoint(value):
    _require(type(value) is str, 'explicit source endpoint string required')
    try:
        dt = _utc(datetime.fromisoformat(value.replace('Z', '+00:00')))
    except (TypeError, ValueError) as exc:
        raise ValueError('valid UTC source endpoint required') from exc
    _require(not dt.minute and not dt.second and not dt.microsecond, 'whole-hour endpoint required')
    return dt


def _number(value):
    _require(type(value) in (str, Decimal), 'source Decimal or decimal text required')
    try:
        value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('finite source number required') from exc
    _require(value.is_finite(), 'finite source number required')
    return Fraction(value)


def _duration(window_hours, *, start, end):
    _utc(start); _utc(end)
    _require(not any((d.minute or d.second or d.microsecond) for d in (start, end)),
             'whole-hour UTC source boundaries required')
    _require(end > start and (end - start) % HOUR == timedelta(0), 'nonempty complete-hour source window required')
    n = (end - start) // HOUR
    _require(type(window_hours) is int and 1 <= window_hours <= n,
             'explicit integer window_hours within the observed window required')
    return n


def _exact(value):
    value = Fraction(value)
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator),
            'decimal': str(decimal), 'decimal_display_precision': 50}


def _contract():
    raw = MANIFEST.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256, 'reviewed B19 manifest identity required')
    m = json.loads(raw)
    _require(m['reference_id'] == 'B19-HISTORICAL-JOINT-WINDOW-UTC2025'
             and m['model_use'] == 'HISTORICAL_COINCIDENCE_ONLY'
             and m['window_hours_default'] is None and m['station_id'] == '44527'
             and m['national_weather_weights'] is None and m['probabilities'] is None
             and set(m['authority_sha256']) == set(AUTHORITY), 'reviewed historical joint contract required')
    for path, digest in m['authority_sha256'].items():
        _require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest,
                 'reviewed source authority changed: ' + path)
    annual = json.loads((ROOT / 'registry/b05_annual_device_reference_manifest.json').read_text())
    _require(m['weather'] == annual['weather'], 'unchanged admitted complete-calendar weather handoff required')
    _require(_endpoint(m['weather']['start_utc']) == historical.START
             and _endpoint(m['weather']['end_utc']) == historical.END, 'same physical UTC year required')
    return m


def _weather_rows(rows, contract):
    start, end = _endpoint(contract['start_utc']), _endpoint(contract['end_utc'])
    _require(contract['rows'] == (end - start) // HOUR, 'weather count/window mismatch')
    result = []
    for i, row in enumerate(rows):
        a, b = _endpoint(row['interval_start_utc']), _endpoint(row['source_endpoint_utc'])
        _require(a == start + i * HOUR and b == a + HOUR and a < end,
                 'weather gap, duplicate, shift or extra hour')
        source = contract['recent_source_id'] if b == _endpoint(contract['recent_endpoint_utc']) else contract['history_source_id']
        _require(row['station_id'] == contract['station_id'] and row['source_id'] == source,
                 'weather station or original source mismatch')
        temperature = _number(row['ta_C'])
        _require(temperature != -999, 'missing source temperature must not be zero-filled')
        result.append((a, b, temperature, source))
    _require(len(result) == contract['rows'], 'incomplete weather window')
    return result


def _weather(path, contract):
    raw = Path(path).read_bytes()
    _require(len(raw) == contract['bytes'] and hashlib.sha256(raw).hexdigest() == contract['sha256'],
             'exact accepted weather bytes/hash required')
    return _weather_rows(csv.DictReader(io.StringIO(raw.decode('utf-8'))), contract)


@dataclass(frozen=True)
class JointHour:
    start: datetime
    end: datetime
    temperature_c: Fraction
    energies_mwh: tuple[Fraction, ...]
    weather_source_id: str


def _joined_hours(grid_rows, weather, *, start, end):
    stream = iter(grid_rows)
    n = _duration(1, start=start, end=end)
    _require(len(weather) == n, 'same complete weather/grid hour count required')
    for i, (a, b, temperature, source) in enumerate(weather):
        _require(a == start + i * HOUR and b == a + HOUR, 'weather/hour boundary mismatch')
        energies = [Fraction(0) for _ in GRID_FIELDS]
        for j in range(4):
            row = next(stream, None)
            _require(row is not None, 'incomplete quarter-hour source stream')
            _require(_utc(row.start_utc) == a + j * QUARTER
                     and _utc(row.end_utc) == a + (j + 1) * QUARTER,
                     'grid gap, duplicate, shift or wrong duration')
            values = [_number(getattr(row, field)) for field in GRID_FIELDS]
            load, injection, withdrawal, generation, residual = values
            _require(min(load, injection, withdrawal) >= 0
                     and injection - withdrawal == generation and load - generation == residual,
                     'source sign/energy balance mismatch')
            _require(row.evidence_status == 'DER' and row.evidence_tier == historical.EVIDENCE_TIER
                     and row.model_use_status == historical.MODEL_USE,
                     'inherited source evidence/use boundary required')
            for k, value in enumerate(values):
                energies[k] += value / 4
        yield JointHour(a, b, Fraction(temperature), tuple(energies), source)
    # This next() executes the upstream generator's final source/recovery checks.
    _require(next(stream, None) is None, 'extra source grid interval')


def _window_record(queue, sums, sources):
    hours = len(queue)
    return {'start_utc': queue[0].start.isoformat(), 'end_utc_exclusive': queue[-1].end.isoformat(),
            'duration_hours': hours, 'weather_station_id': '44527',
            'weather_source_hours': dict(sorted((k, v) for k, v in sources.items() if v)),
            'mean_temperature_c': _exact(sums['temperature_sum_c'] / hours),
            'energy_mwh': {key: _exact(sums[key]) for key in ENERGY_FIELDS},
            'mean_power_mw': {key.removesuffix('_mwh') + '_mw': _exact(sums[key] / hours) for key in ENERGY_FIELDS},
            'temporal_meaning': 'Same physical UTC interval; hourly/window means, not quarter-hour or instantaneous peaks'}


def _summarize(grid_rows, weather, *, window_hours, start, end):
    n = _duration(window_hours, start=start, end=end)
    queue, sources = deque(), Counter()
    sums = {key: Fraction(0) for key in ('temperature_sum_c', *ENERGY_FIELDS)}
    annual = dict(sums)
    best = {name: {'value': None, 'windows': []} for name in CRITERIA}
    windows = hours = 0
    for row in _joined_hours(grid_rows, weather, start=start, end=end):
        queue.append(row); sources[row.weather_source_id] += 1; hours += 1
        values = dict(zip(('temperature_sum_c', *ENERGY_FIELDS), (row.temperature_c, *row.energies_mwh)))
        for key, value in values.items():
            sums[key] += value; annual[key] += value
        if len(queue) > window_hours:
            removed = queue.popleft(); sources[removed.weather_source_id] -= 1
            for key, value in zip(('temperature_sum_c', *ENERGY_FIELDS), (removed.temperature_c, *removed.energies_mwh)):
                sums[key] -= value
        if len(queue) == window_hours:
            windows += 1
            for name, (key, direction) in CRITERIA.items():
                value = sums[key]
                item = best[name]
                better = item['value'] is None or (value < item['value'] if direction == 'min' else value > item['value'])
                if better:
                    item['value'] = value; item['windows'] = []
                if value == item['value']:
                    item['windows'].append(_window_record(queue, sums, sources))
    _require(hours == n and windows == n - window_hours + 1, 'complete rolling-window enumeration required')
    return {'hours': hours, 'quarter_hour_intervals': 4 * hours, 'windows_evaluated': windows,
            'window_hours': window_hours, 'start_utc': start.isoformat(), 'end_utc_exclusive': end.isoformat(),
            'annual_mean_temperature_c': _exact(annual['temperature_sum_c'] / hours),
            'annual_energy_mwh': {key: _exact(annual[key]) for key in ENERGY_FIELDS},
            'criteria': {name: {'direction': CRITERIA[name][1], 'ties': len(item['windows']),
                                'mean_score': _exact(item['value'] / window_hours),
                                'windows': item['windows']} for name, item in best.items()}}


def calculate_reference(source_paths, handoff_paths, *, weather_path, window_hours):
    """Fully consume accepted original sources; return no partially checked result."""
    _duration(window_hours, start=historical.START, end=historical.END)
    m = _contract()
    weather = _weather(weather_path, m['weather'])
    result = _summarize(historical.iter_historical_source_balance(source_paths, handoff_paths), weather,
                        window_hours=window_hours, start=historical.START, end=historical.END)
    return {'reference_id': m['reference_id'], 'model_use': m['model_use'], 'evidence_status': 'DER',
            'evidence_tier': historical.EVIDENCE_TIER,
            'window_definition_status': 'CALLER_DECLARED_ANALYSIS_WINDOW_NOT_POLICY',
            'source_evidence': m['source_evidence'], 'spatial_boundary': m['spatial_boundary'],
            'selection': 'Caller-declared duration; all contiguous hourly-start windows and every exact extremal tie',
            'selection_interpretation': m['selection_interpretation'],
            'method': 'Exact rational integration/ranking; 50-digit decimal displays with exact ratios retained',
            'validation_debt': m['validation_debt'], 'excluded_claims': m['excluded_claims'],
            'policy_defaults_selected': False, 'probabilities': None, 'national_feasibility_verdict': None,
            'originals_republished': False, 'result': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paths-json', required=True, help='External JSON with source_paths, handoff_paths and weather_path')
    parser.add_argument('--window-hours', required=True, type=int)
    args = parser.parse_args()
    paths = json.loads(Path(args.paths_json).read_text())
    _require(set(paths) == {'source_paths', 'handoff_paths', 'weather_path'}, 'exact caller-owned path mapping required')
    result = calculate_reference(paths['source_paths'], paths['handoff_paths'], weather_path=paths['weather_path'], window_hours=args.window_hours)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
