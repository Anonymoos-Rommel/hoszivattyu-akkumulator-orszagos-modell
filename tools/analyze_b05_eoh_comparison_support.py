"""Local, hash-bound EoH comparisons; no installed correction or runtime admission.

Standard-library only. Counter differences use original adjacent 120-second rows.
Rating powers are endpoint references, never integrated as simulated energy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from modules.B05.manufacturer_wm50_reference import MODES, load_wm50_reference, source_grid

ROOT = Path(__file__).resolve().parents[1]
H = 'Heat_Pump_Energy_Output'
E = 'Whole_System_Energy_Consumed'
CP = 'Circulation_Pump_Energy_Consumed'
IH = 'Immersion_Heater_Energy_Consumed'
F = 'Heat_Pump_Heating_Flow_Temperature'
R = 'Heat_Pump_Return_Temperature'
A = 'External_Air_Temperature'
HW = 'Hot_Water_Flow_Temperature'
CHANNELS = {'H': H, 'E': E, 'CP': CP, 'IH': IH}
MASKS = {'HP_E': ('H', 'E'), 'HP_E_CP': ('H', 'E', 'CP'),
         'HP_E_IH': ('H', 'E', 'IH'), 'HP_E_CP_IH': ('H', 'E', 'CP', 'IH')}
CATEGORY = 'documented_separate_meter_hybrid_SH'
MANIFEST = ROOT / 'registry/b05_eoh_comparison_support_manifest.json'


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        yield from csv.DictReader(handle)


def write_csv(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f'empty output table: {path}')
    with Path(path).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verify_handoff(root, expected):
    root = Path(root).resolve()
    manifest_path = root / 'HANDOFF_MANIFEST.json'
    if digest(manifest_path) != expected['handoff_manifest_sha256']:
        raise ValueError('handoff manifest identity mismatch')
    handoff = json.loads(manifest_path.read_text(encoding='utf-8'))
    seen = set()
    for item in handoff['files']:
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root) or item['path'] in seen:
            raise ValueError('unsafe or duplicate input path')
        seen.add(item['path'])
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError(f"input identity mismatch: {item['path']}")
    if len(seen) != handoff['input_file_count'] or len(seen) != expected['input_file_count']:
        raise ValueError('input count mismatch')
    return handoff


def number(value):
    if value is None or value.strip().lower() in ('', 'nan', 'null'):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def parsed_rows(path):
    for row in read_csv(path):
        yield {'t': datetime.fromisoformat(row['Timestamp']),
               **{k: number(row.get(v)) for k, v in
                  {**CHANNELS, 'F': F, 'R': R, 'A': A, 'HW': HW}.items()}}


def differences(previous, current):
    if previous is None or (current['t'] - previous['t']).total_seconds() != 120:
        return {}
    return {k: current[k] - previous[k] for k in CHANNELS
            if previous[k] is not None and current[k] is not None}


def proxy(previous, current):
    flow = all(r['F'] is not None for r in (previous, current))
    hw = [r['HW'] is not None for r in (previous, current)]
    if flow and not any(hw):
        return 'heating_temperature_indicated_not_service_proven'
    if all(hw) and all(r['F'] is None for r in (previous, current)):
        return 'DHW_temperature_indicated_not_service_proven'
    if flow and all(hw):
        return 'both_temperature_channels_present_unallocated'
    return 'incomplete_or_mixed_temperature_channels_unallocated'


def band(value, edges):
    if value is None:
        return 'missing'
    for lo, hi in zip(edges, edges[1:]):
        if lo <= value < hi:
            return f'[{lo:g},{hi:g})'
    raise ValueError('bin edges must cover the real line')


def condition(previous, current):
    return (proxy(previous, current),
            band(current['A'], (-math.inf, 0, 2, 5, 7, 10, 15, 20, math.inf)),
            band(current['F'], (-math.inf, 25, 35, 40, 45, 50, 55, 60, math.inf)),
            band(current['R'], (-math.inf, 25, 35, 40, 45, 50, 55, 60, math.inf)))


class References:
    def __init__(self):
        self.maps = {mode: load_wm50_reference(mode) for mode in MODES}
        rows = source_grid()
        self.outdoors = sorted({float(r['outdoor_temperature_c']) for r in rows})
        self.supplies = sorted({float(r['supply_temperature_c']) for r in rows})
        self.present = {(r['mode'], float(r['outdoor_temperature_c']),
                         float(r['supply_temperature_c'])) for r in rows if r['availability'] == 'PRESENT'}

    @staticmethod
    def brackets(value, axis):
        if value in axis:
            return (value,)
        return next(((lo, hi) for lo, hi in zip(axis, axis[1:]) if lo < value < hi), ())

    @lru_cache(maxsize=65536)
    def evaluate(self, mode, ambient, flow):
        if mode not in MODES:
            raise ValueError('explicit published mode required; no best-COP selection')
        if ambient is None or flow is None:
            return 'MISSING_AMBIENT_OR_HEATING_FLOW', None
        outdoor = self.brackets(ambient, self.outdoors)
        supply = self.brackets(flow, self.supplies)
        if not outdoor or not supply:
            return 'OUTSIDE_NATIVE_DOMAIN', None
        if any((mode, a, f) not in self.present for a in outdoor for f in supply):
            return 'SOURCE_BLANK', None
        result = self.maps[mode].evaluate(ambient, flow)
        if result.point is None:
            # Preserve even the engine's stricter rectangular-edge disposition.
            return result.status, None
        return 'SUPPORTED', result.point

    def pair(self, mode, previous, current):
        s0, p0 = self.evaluate(mode, previous['A'], previous['F'])
        s1, p1 = self.evaluate(mode, current['A'], current['F'])
        if p0 is not None and p1 is not None:
            return 'SUPPORTED', (p0, p1)
        return f'previous={s0};current={s1}', None


def empty_balance(channels):
    return {'steps': 0, **{f'{c}_kWh': 0.0 for c in channels},
            **{f'{c}_negative_steps': 0 for c in channels},
            'H_negative_steps': 0, 'E_negative_steps': 0,
            'H_zero_or_negative_steps': 0, 'E_kWh_when_H_zero_or_negative': 0.0}


def add_balance(total, delta):
    total['steps'] += 1
    for c in CHANNELS:
        if f'{c}_kWh' in total:
            total[f'{c}_kWh'] += delta[c]
            total[f'{c}_negative_steps'] += delta[c] < -1e-8
    if delta['H'] <= 1e-8:
        total['H_zero_or_negative_steps'] += 1
        total['E_kWh_when_H_zero_or_negative'] += delta['E']


def finish_balance(total, channels):
    result = {**total, 'hours': total['steps'] / 30}
    for c in CHANNELS:
        result.setdefault(f'{c}_kWh', None)
        result.setdefault(f'{c}_negative_steps', None)
    hours = result['hours']
    result['observed_H_mean_kW'] = total['H_kWh'] / hours if hours else None
    result['observed_whole_E_mean_kW'] = total['E_kWh'] / hours if hours else None
    result['observed_H_per_whole_E_ratio'] = total['H_kWh'] / total['E_kWh'] if total['E_kWh'] > 0 else None
    residual = total['E_kWh'] - total['CP_kWh'] if 'CP' in channels else None
    result['E_minus_CP_kWh_same_mask'] = residual
    result['observed_H_per_E_minus_CP_ratio'] = total['H_kWh'] / residual if residual is not None and residual > 0 else None
    return result


def analyze_target(rows, refs):
    ledger = {}
    comparisons = {}
    coverage = defaultdict(lambda: defaultdict(float))
    previous = None
    for current in rows:
        year = current['t'].year
        if year not in ledger:
            ledger[year] = {'present_rows': 0, **{m: empty_balance(cs) for m, cs in MASKS.items()}}
        ledger[year]['present_rows'] += 1
        cov = coverage[year]
        cov['present_rows'] += 1
        delta = differences(previous, current)
        if previous is not None:
            seconds = (current['t'] - previous['t']).total_seconds()
            cov['adjacent_row_pairs'] += 1
            if seconds == 120:
                cov['grid120_steps'] += 1
                cov['cross_year_grid120_steps'] += previous['t'].year != year
                for c in CHANNELS:
                    if c in delta:
                        cov[f'{c}_valid_steps'] += 1
                        cov[f'{c}_signed_kWh'] += delta[c]
                        cov[f'{c}_negative_steps'] += delta[c] < -1e-8
                    else:
                        cov[f'{c}_missing_steps'] += 1
            else:
                cov['excluded_non120_pairs'] += 1
                cov['excluded_positive_elapsed_hours_no_energy_allocated'] += max(seconds, 0) / 3600
                cov['nonincreasing_timestamp_pairs'] += seconds <= 0
        if not delta:
            previous = current
            continue
        eligible = [m for m, cs in MASKS.items() if all(c in delta for c in cs)]
        for mask in eligible:
            add_balance(ledger[year][mask], delta)
        if eligible:
            conditions = condition(previous, current)
            for mode in MODES:
                status, points = refs.pair(mode, previous, current)
                for mask in eligible:
                    for grain, cells in (('year', ('ALL',) * 4), ('condition', conditions)):
                        key = year, mask, mode, status, grain, *cells
                        if key not in comparisons:
                            comparisons[key] = {**empty_balance(MASKS[mask]),
                                **{f'{endpoint}_{quantity}_sum': 0.0 for endpoint in ('previous', 'current')
                                   for quantity in ('Qh_kW', 'Pel_kW', 'COP')},
                                **{f'{c}_current_sum': 0.0 for c in ('A', 'F', 'R')},
                                'R_current_valid_steps': 0}
                        total = comparisons[key]
                        add_balance(total, delta)
                        if points:
                            for endpoint, p in zip(('previous', 'current'), points):
                                for q, value in (('Qh_kW', p.thermal_capacity_kw),
                                                 ('Pel_kW', p.electrical_input_kw), ('COP', p.cop)):
                                    total[f'{endpoint}_{q}_sum'] += value
                            total['A_current_sum'] += current['A']
                            total['F_current_sum'] += current['F']
                        if current['R'] is not None:
                            total['R_current_sum'] += current['R']
                            total['R_current_valid_steps'] += 1
        previous = current
    ledger_rows = []
    for year, data in sorted(ledger.items()):
        for mask, cs in MASKS.items():
            ledger_rows.append({'status': 'DER', 'year_current_endpoint': year, 'mask': mask,
                                'present_rows': data['present_rows'], **finish_balance(data[mask], cs)})
    comparison_rows = []
    for key, total in sorted(comparisons.items()):
        year, mask, mode, support, grain, pr, amb, flow, ret = key
        balance = {k: v for k, v in total.items() if not k.endswith('_sum') and k != 'R_current_valid_steps'}
        row = {'status': 'DER', 'year_current_endpoint': year, 'mask': mask, 'mode': mode,
               'support': support, 'grain': grain, 'temperature_proxy': pr,
               'current_ambient_bin_C': amb, 'current_heating_flow_bin_C': flow,
               'current_return_bin_C': ret, **finish_balance(balance, MASKS[mask])}
        n = total['steps']
        for endpoint in ('previous', 'current'):
            for q in ('Qh_kW', 'Pel_kW', 'COP'):
                row[f'{endpoint}_endpoint_reference_mean_{q}'] = total[f'{endpoint}_{q}_sum'] / n if support == 'SUPPORTED' else None
        for c in ('A', 'F'):
            row[f'current_mean_{c}_C'] = total[f'{c}_current_sum'] / n if support == 'SUPPORTED' else None
        nr = total['R_current_valid_steps']
        row['current_return_observed_steps'] = nr
        row['current_mean_return_C'] = total['R_current_sum'] / nr if nr else None
        comparison_rows.append(row)
    keys = sorted({k for cov in coverage.values() for k in cov})
    coverage_rows = [{'status': 'DER', 'year_current_endpoint': y, **{k: cov.get(k, 0) for k in keys}}
                     for y, cov in sorted(coverage.items())]
    return ledger_rows, comparison_rows, coverage_rows


def check_ledger(ledger, controls):
    mapping = {'present_rows': 'present_rows', 'HP_E_common_steps': ('HP_E', 'steps'),
               'HP_heat_kWh_HP_E_common': ('HP_E', 'H_kWh'), 'whole_E_kWh_HP_E_common': ('HP_E', 'E_kWh'),
               'HP_heat_negative_HP_E_common_steps': ('HP_E', 'H_negative_steps'),
               'whole_E_negative_HP_E_common_steps': ('HP_E', 'E_negative_steps'),
               'HP_zero_or_negative_heat_HP_E_common_steps': ('HP_E', 'H_zero_or_negative_steps'),
               'whole_E_kWh_when_HP_heat_zero_or_negative': ('HP_E', 'E_kWh_when_H_zero_or_negative'),
               'HP_E_CP_common_steps': ('HP_E_CP', 'steps'),
               'HP_heat_kWh_HP_E_CP_common': ('HP_E_CP', 'H_kWh'),
               'whole_E_kWh_HP_E_CP_common': ('HP_E_CP', 'E_kWh'),
               'CP_kWh_HP_E_CP_common': ('HP_E_CP', 'CP_kWh'),
               'CP_negative_common_steps': ('HP_E_CP', 'CP_negative_steps')}
    lookup = {(r['year_current_endpoint'], r['mask']): r for r in ledger}
    checks = []
    for control in controls:
        year = int(control['year'])
        for column, locator in mapping.items():
            mask, field = ('HP_E', locator) if isinstance(locator, str) else locator
            actual = lookup[year, mask][field]
            expected = float(control[column])
            if not math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-8):
                raise ValueError(f'original ledger mismatch: {year}/{column}: {actual} != {expected}')
            checks.append({'year': year, 'original_column': column, 'expected': expected,
                           'actual': actual, 'difference': actual - expected, 'passed': True})
        for column, field, mask in (
            ('HP_heat_per_whole_E_common_observed_ratio', 'observed_H_per_whole_E_ratio', 'HP_E'),
            ('HP_heat_per_E_minus_CP_common_observed_ratio', 'observed_H_per_E_minus_CP_ratio', 'HP_E_CP')):
            actual = lookup[year, mask][field]
            expected = float(control[column])
            if not math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-8):
                raise ValueError(f'original ratio mismatch: {year}/{column}')
            checks.append({'year': year, 'original_column': column, 'expected': expected,
                           'actual': actual, 'difference': actual - expected, 'passed': True})
    return checks


def summarize_hybrids(windows):
    windows = [r for r in windows if r['category'] == CATEGORY]
    ids = {r['property_id'] for r in windows}
    steps = sum(int(r['steps']) for r in windows)
    if (len(ids), len(windows), steps) != (33, 4546, 96019):
        raise ValueError('full primary hybrid population required')
    homes = defaultdict(lambda: [0.0, 0.0])
    for row in windows:
        homes[row['property_id']][0] += float(row['HP_heat_kWh'])
        homes[row['property_id']][1] += float(row['whole_E_kWh'])
    heat = sum(v[0] for v in homes.values())
    electrical = sum(v[1] for v in homes.values())
    return {'status': 'DER', 'category': CATEGORY, 'systems': len(ids), 'windows': len(windows),
            'steps': steps, 'hours': steps / 30, 'HP_heat_kWh': heat, 'whole_E_kWh': electrical,
            'pooled_observed_ratio': heat / electrical,
            'home_balanced_mean_ratio': sum(h / e for h, e in homes.values()) / len(homes),
            'boiler_positive_windows_retained': sum(int(r['boiler_positive_steps']) > 0 for r in windows),
            'cross_year_windows_retained': sum(r['year_start'] != r['year_end'] for r in windows),
            'time_basis': 'recorded; timezone Q', 'independent_validation': False,
            'WM50_calibration': False}


def run(handoff_root, output):
    spec = json.loads(MANIFEST.read_text(encoding='utf-8'))
    root = Path(handoff_root).resolve()
    handoff = verify_handoff(root, spec['input_binding'])
    output = Path(output).resolve()
    if output == root or output.is_relative_to(root) or output.is_relative_to(ROOT):
        raise ValueError('output must be separate from repository and source handoff')
    output.mkdir(parents=True, exist_ok=False)
    print('Verified all handoff inputs; analyzing original EOH2074 rows', flush=True)
    ledger, comparisons, coverage = analyze_target(parsed_rows(root / 'eoh2074/clean/Property_ID=EOH2074.csv'), References())
    checks = check_ledger(ledger, read_csv(root / 'eoh2074/EOH2074_all_period_common_interval_year.csv'))
    write_csv(output / 'eoh2074_year_ledger.csv', ledger)
    write_csv(output / 'eoh2074_matched_comparisons.csv', comparisons)
    write_csv(output / 'eoh2074_channel_and_gap_coverage.csv', coverage)
    write_csv(output / 'original_year_control_checks.csv', checks)
    summary = summarize_hybrids(read_csv(root / 'comparison/documented_SH_primary_comparative_population.csv'))
    write_csv(output / 'hybrid_primary_summary.csv', [summary])
    dest = output / 'comparison_source_tables'
    dest.mkdir()
    for item in handoff['files']:
        if item['path'].startswith('comparison/'):
            shutil.copyfile(root / item['path'], dest / Path(item['path']).name)
    for name in ('condition_pooled_observed_ratios_not_rating_or_annual.csv',
                 'condition_cell_system_contributions.csv', 'condition_cell_system_year_contributions.csv',
                 'condition_cell_year_summaries.csv', 'same_system_condition_year_sensitivity.csv',
                 'exact_selected_interval_calendar_clock_support.csv'):
        write_csv(output / ('hybrid_' + name), [r for r in read_csv(root / 'comparison' / name) if r['category'] == CATEGORY])
    provenance = {'status': 'DER', 'comparison_manifest_sha256': digest(MANIFEST),
                  'handoff_manifest_sha256': digest(root / 'HANDOFF_MANIFEST.json'),
                  'input_files': handoff['files'], 'definitions': spec['definitions'],
                  'non_admission': spec['non_admission'],
                  'code_sha256': digest(Path(__file__)),
                  'outputs': [{'path': p.relative_to(output).as_posix(), 'bytes': p.stat().st_size,
                               'sha256': digest(p)} for p in sorted(output.rglob('*')) if p.is_file()]}
    (output / 'OUTPUT_MANIFEST.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print(f'Controls passed; {len(comparisons)} matched comparison rows; full hybrid tables retained: {output}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.handoff, args.output)


if __name__ == '__main__':
    main()
