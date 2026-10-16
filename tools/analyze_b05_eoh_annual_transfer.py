"""Explicit DER research replay and conditional annual transfer; no admission.

The recovered weather has a separate identity. No canonical weather guard or
private runtime seam is used. Public source maps and the public E2 on/off policy
are composed here under the new research manifest.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import shutil
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B05.hourly_onoff_parameter_policy import (
    evaluate_hourly_onoff_with_policy, HEM_DEFAULT_SCENARIO, RADIATOR_OR_UFH_WET,
)
from modules.B06 import tabula_seasonal_reference as tabula
from tools import analyze_b05_eoh_comparison_support as comparison

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'registry/b05_eoh_annual_transfer_manifest.json'
MODES = ('MIN', 'MID', 'NOMINAL', 'MAX')
HOUR = timedelta(hours=1)
AMB_EDGES = (-math.inf, 0, 2, 5, 7, 10, 15, 20, math.inf)
DUTY_EDGES = (-math.inf, 0, .1, .25, .5, .75, 1, math.inf)
AGGREGATIONS = ((2, 0), (30, 0), (60, 0), (60, 30))


def digest(path):
    return comparison.digest(path)


def csv_rows(path):
    return comparison.read_csv(path)


def write_csv(path, rows):
    comparison.write_csv(path, rows)


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def verify_additive(root, spec):
    root = Path(root).resolve()
    path = root / 'ADDITIVE_INPUT_MANIFEST.json'
    if digest(path) != spec['input_binding']['additive_manifest_sha256']:
        raise ValueError('additive manifest identity mismatch')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    seen = set()
    for item in manifest['files']:
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root) or path in seen:
            raise ValueError('unsafe/duplicate additive path')
        seen.add(path)
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('additive input mismatch: ' + item['path'])
    if len(seen) != 19:
        raise ValueError('all 19 additive files required')
    return manifest


def recovered_weather(root, spec):
    contract = spec['recovered_weather']
    path = Path(root) / contract['path']
    if path.stat().st_size != contract['bytes'] or digest(path) != contract['sha256']:
        raise ValueError('new research weather identity mismatch')
    observed = {}
    for name in contract['raw_zip_paths']:
        with zipfile.ZipFile(Path(root) / name) as z:
            if len(z.infolist()) != 1:
                raise ValueError('one official weather member required')
            text = z.read(z.namelist()[0]).decode('utf-8-sig')
            lines = (line for line in text.splitlines() if line.strip() and not line.startswith('#'))
            for raw in csv.DictReader(lines, delimiter=';'):
                row = {k.strip(): v.strip() for k, v in raw.items() if k and v is not None}
                at = row['Time']
                if '202501010100' <= at <= '202601010000':
                    if at in observed:
                        raise ValueError('duplicate weather endpoint across official snapshots')
                    observed[at] = row
    rows = list(csv_rows(path))
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    if len(rows) != len(observed) or len(rows) != 8760:
        raise ValueError('8760 source-linked weather hours required')
    for i, row in enumerate(rows):
        a, b = start + i * HOUR, start + (i + 1) * HOUR
        raw = observed[b.strftime('%Y%m%d%H%M')]
        expected_source = contract['lineage_source_ids'][0 if i < 8759 else 1]
        if (datetime.fromisoformat(row['interval_start_utc']) != a
                or datetime.fromisoformat(row['source_endpoint_utc']) != b
                or row['station_id'] != raw['StationNumber'] or row['station_id'] != '44527'
                or row['ta_C'] != raw['ta'] or row['source_id'] != expected_source
                or not math.isfinite(float(row['ta_C'])) or float(row['ta_C']) == -999):
            raise ValueError('weather source/interval/lineage mismatch')
    return rows


class LoadReference:
    """Paired-power frequency order and explicit existing E2 minimum-stage method."""

    def __init__(self):
        self.guard = comparison.References()
        self.fixed = {m: wm50.load_wm50_reference(m, fixed_supply_c=55) for m in MODES}

    @lru_cache(maxsize=65536)
    def points(self, ambient, flow, fixed=False):
        values = []
        for mode in MODES:
            if fixed:
                result = self.fixed[mode].evaluate(ambient, flow)
                p, reason = result.point, result.status
            else:
                reason, p = self.guard.evaluate(mode, ambient, flow)
            if p is None:
                return None, reason
            q, pel = p.thermal_capacity_kw, p.electrical_input_kw
            if values and (q < values[-1][0] or (q == values[-1][0] and pel != values[-1][1])):
                return None, 'REVERSED_OR_CONFLICTING_MODE_ORDER'
            if not values or q != values[-1][0]:
                values.append((q, pel))
        return tuple(values), None

    def evaluate(self, q_kw, ambient, flow, *, duration_h=1.0, fixed=False):
        if not all(math.isfinite(v) for v in (q_kw, ambient, flow, duration_h)) or duration_h <= 0:
            raise ValueError('finite load/conditions and positive physical duration required')
        result = {'branch': 'Q', 'reference_kWh': None, 'active_kWh': None, 'inertia_kWh': None,
                  'idle_kWh': None, 'stage_on_fraction': None, 'load_over_min': None,
                  'unserved_H_kWh': None}
        if q_kw < 0:
            return {**result, 'branch': 'NEGATIVE_HEAT_RETAINED_NO_REFERENCE'}
        if q_kw == 0:
            return {**result, 'branch': 'ZERO_HEAT', 'reference_kWh': .015 * duration_h,
                    'active_kWh': 0., 'inertia_kWh': 0., 'idle_kWh': .015 * duration_h,
                    'stage_on_fraction': 0., 'load_over_min': 0., 'unserved_H_kWh': 0.}
        points, reason = self.points(ambient, flow, fixed)
        if points is None:
            return {**result, 'branch': 'Q_' + reason}
        low, high = points[0], points[-1]
        ratio = q_kw / low[0]
        if q_kw > high[0]:
            return {**result, 'branch': 'ABOVE_MAX_NOT_SAME_SERVICE', 'load_over_min': ratio,
                    'unserved_H_kWh': (q_kw - high[0]) * duration_h}
        if q_kw < low[0]:
            inertia = evaluate_hourly_onoff_with_policy(
                minimum_continuous_compressor_power_kw=low[1], load_ratio=ratio,
                minimum_continuous_load_ratio=1.0, emitter_class=RADIATOR_OR_UFH_WET,
                policy=HEM_DEFAULT_SCENARIO)
            if inertia.tau_eq_s != 140. or inertia.emitter_response_time_s != 1370. or inertia.onoff_inertia_power_kw is None:
                raise ValueError('existing E2 on/off method identity mismatch')
            active, extra, idle = ratio * low[1], inertia.onoff_inertia_power_kw, .015 * (1 - ratio)
            branch, duty = 'MINIMUM_STAGE_ONOFF_E2_TRANSFER', ratio
        else:
            exact = next((p for p in points if p[0] == q_kw), None)
            if exact:
                active = exact[1]
            else:
                a, b = next((a, b) for a, b in zip(points, points[1:]) if a[0] < q_kw < b[0])
                active = a[1] + (q_kw - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
            extra, idle, branch, duty = 0., 0., 'PAIRED_POWER_CONTINUOUS', 1.
        return {'branch': branch, 'reference_kWh': (active + extra + idle) * duration_h,
                'active_kWh': active * duration_h, 'inertia_kWh': extra * duration_h,
                'idle_kWh': idle * duration_h, 'stage_on_fraction': duty,
                'load_over_min': ratio, 'unserved_H_kWh': 0.}


def target_reference(weather, model, spec):
    """New explicit research contract, using public TABULA and map/policy APIs."""
    authority = json.loads((ROOT / 'registry/b05_annual_device_reference_manifest.json').read_text(encoding='utf-8'))
    thermal = authority['thermal']
    package = tabula.source_package()
    source = next(r['values'] for r in package['rows'] if r['values']['Code_BuildingVariant'] == thermal['variant_id'])
    native = tabula.calculate_reference(thermal['variant_id'], service='source')
    if package['source_sha256'] != thermal['system_source_sha256'] or source['A_C_Ref'] != 56:
        raise ValueError('ambitious 56 m2 source identity mismatch')
    useful = native['annual_heat_kwh']
    distribution = thermal['effective_distribution_kwh_m2'] * 56
    h_eff = 56 * (native['h_transmission'] + native['h_ventilation']) * native['nonuniform_heating_factor'] / 1000
    balance = source['Theta_e'] + useful / (24 * source['HeatingDays'] * h_eff)
    weights = [max(balance - float(r['ta_C']), 0.) for r in weather]
    denominator = math.fsum(weights)
    rows = []
    for w, weight in zip(weather, weights):
        h_useful = useful * weight / denominator
        h_distribution = distribution * weight / denominator
        heat = h_useful + h_distribution
        ambient = float(w['ta_C'])
        reference = model.evaluate(heat, ambient, 55., fixed=True)
        if reference['reference_kWh'] is None or reference['unserved_H_kWh'] != 0:
            raise ValueError('complete target device reference required')
        rows.append({'status': 'DER', 'input_id': spec['recovered_weather']['input_id'],
                     'interval_start_utc': w['interval_start_utc'], 'source_endpoint_utc': w['source_endpoint_utc'],
                     'weather_lineage_source_id': w['source_id'], 'ambient_C': ambient, 'flow_C': 55.,
                     'useful_H_kWh': h_useful, 'distribution_H_kWh': h_distribution, 'generator_H_kWh': heat,
                     'hours': 1., **reference})
    total = math.fsum(r['reference_kWh'] for r in rows)
    if total != spec['target']['expected_device_reference_kWh']:
        raise ValueError(f'independent reference reproduction mismatch: {total!r}')
    summary = {'status': 'DER', 'weather_input_id': spec['recovered_weather']['input_id'],
               'hours': len(rows), 'useful_H_kWh': useful, 'distribution_H_kWh': distribution,
               'generator_H_kWh': useful + distribution, 'balance_temperature_C': balance,
               'device_reference_kWh': total,
               **{k: math.fsum(r[k] for r in rows) for k in ('active_kWh', 'inertia_kWh', 'idle_kWh')},
               'branch_hours': dict(Counter(r['branch'] for r in rows)),
               'installed_annual_kWh': None, 'annual_signed_installed_residual_kWh': None}
    return rows, summary


def check_period_controls(annual, monthly):
    by_year = defaultdict(list)
    for row in monthly:
        by_year[row['property_id'], row['month'][:4]].append(row)
    checks = []
    excluded = {'year', 'HP_heat_per_whole_E_common_observed_ratio', 'HP_heat_per_E_minus_CP_common_observed_ratio'}
    for row in annual:
        key = row['property_id'], row['year']
        if key not in by_year:
            raise ValueError('year lacks monthly controls')
        for field, value in row.items():
            if field in excluded:
                continue
            try:
                expected = float(value)
            except ValueError:
                continue
            actual = math.fsum(float(m[field]) for m in by_year[key])
            if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError(f'month/year control mismatch: {key}/{field}')
            checks.append({'property_id': key[0], 'year': key[1], 'field': field,
                           'annual': expected, 'sum_months': actual, 'difference': actual - expected})
    return checks


def state(q):
    return 'NEGATIVE_HEAT' if q < -1e-8 else 'ZERO_OR_TINY_HEAT' if q <= 1e-8 else 'POSITIVE_HEAT'


def original_mask_ledger(root):
    totals, present = {}, Counter()
    previous = None
    for current in comparison.parsed_rows(Path(root) / 'eoh2074/clean/Property_ID=EOH2074.csv'):
        year = current['t'].year
        present[year] += 1
        delta = comparison.differences(previous, current)
        for mask, channels in comparison.MASKS.items():
            key = year, mask
            if key not in totals:
                totals[key] = comparison.empty_balance(channels)
            if all(c in delta for c in channels):
                comparison.add_balance(totals[key], delta)
        previous = current
    result = [{'status': 'DER', 'year_current_endpoint': year, 'mask': mask,
               'present_rows': present[year], **comparison.finish_balance(total, comparison.MASKS[mask])}
              for (year, mask), total in sorted(totals.items())]
    checks = comparison.check_ledger(result, csv_rows(Path(root) / 'eoh2074/EOH2074_all_period_common_interval_year.csv'))
    return result, checks


def transfer_cell(ambient, ratio, positive):
    return (comparison.band(ambient, AMB_EDGES), comparison.band(ratio, DUTY_EDGES), positive)


def interval_source_status(previous, current, model):
    if any(r[c] is None for r in (previous, current) for c in ('A', 'F')):
        return 'MISSING_ENDPOINT_CONDITIONS'
    reasons = [model.points(r['A'], r['F'])[1] for r in (previous, current)]
    return 'SUPPORTED' if not any(reasons) else 'UNSUPPORTED:' + '|'.join(sorted(set(r for r in reasons if r)))


def segments(rows, minutes, offset, model=None):
    """Contiguous matched H/E only; invalid rows, proxy/calendar boundaries split."""
    previous, current_segment = None, None
    for current in rows:
        delta = comparison.differences(previous, current)
        eligible = 'H' in delta and 'E' in delta
        if eligible:
            at = current['t']
            bucket = int((at - datetime(1970, 1, 1)).total_seconds() - 1 - offset * 60) // (minutes * 60)
            proxy = comparison.proxy(previous, current)
            source_status = interval_source_status(previous, current, model) if model else 'LEGACY_UNSPLIT'
            key = (bucket, at.year, at.month, proxy, source_status)
        if not eligible or current_segment is not None and current_segment['key'] != key:
            if current_segment is not None:
                yield current_segment
            current_segment = None
        if eligible:
            if current_segment is None:
                current_segment = {'key': key, 'start': previous['t'], 'first_current': at, 'end': at, 'steps': 0,
                    'H': 0., 'E': 0., 'CP': 0., 'IH': 0., 'CP_steps': 0, 'IH_steps': 0,
                    'A_sum': 0., 'F_sum': 0., 'R_sum': 0., 'condition_steps': 0, 'R_steps': 0,
                    'F_min': math.inf, 'F_max': -math.inf, 'proxy': proxy,
                    'zero_heat_E': 0., 'negative_heat_steps': 0, 'endpoint_pairs': [],
                    'source_status': source_status, 'interval_records': []}
            s = current_segment
            s['end'] = current['t']
            s['steps'] += 1
            s['H'] += delta['H']
            s['E'] += delta['E']
            for c in ('CP', 'IH'):
                if c in delta:
                    s[c] += delta[c]
                    s[c + '_steps'] += 1
            if delta['H'] <= 1e-8:
                s['zero_heat_E'] += delta['E']
            s['negative_heat_steps'] += delta['H'] < -1e-8
            s['interval_records'].append((previous, current, delta))
            if all(r[c] is not None for r in (previous, current) for c in ('A', 'F')):
                s['condition_steps'] += 1
                s['A_sum'] += (previous['A'] + current['A']) / 2
                s['F_sum'] += (previous['F'] + current['F']) / 2
                s['F_min'] = min(s['F_min'], previous['F'], current['F'])
                s['F_max'] = max(s['F_max'], previous['F'], current['F'])
                s['endpoint_pairs'].extend((r['A'], r['F']) for r in (previous, current))
            if previous['R'] is not None and current['R'] is not None:
                s['R_sum'] += (previous['R'] + current['R']) / 2
                s['R_steps'] += 1
        previous = current
    if current_segment is not None:
        yield current_segment


def segment_reference(s, model):
    hours = s['steps'] / 30
    complete = s['condition_steps'] == s['steps']
    ambient = s['A_sum'] / s['condition_steps'] if s['condition_steps'] else None
    flow = s['F_sum'] / s['condition_steps'] if s['condition_steps'] else None
    if complete and not s['source_status'].startswith('UNSUPPORTED:'):
        reference = model.evaluate(s['H'] / hours, ambient, flow, duration_h=hours)
        if s['H'] > 0 and any(model.points(ta, f)[0] is None for ta, f in s['endpoint_pairs']):
            reference = {**reference, 'branch': 'Q_ORIGINAL_ENDPOINT_SOURCE_SUPPORT',
                         **{k: None for k in ('reference_kWh', 'active_kWh', 'inertia_kWh', 'idle_kWh',
                                             'stage_on_fraction', 'load_over_min', 'unserved_H_kWh')}}
    else:
        reference = {'branch': s['source_status'] if s['source_status'] != 'LEGACY_UNSPLIT' else 'MISSING_ENDPOINT_CONDITIONS', 'reference_kWh': None,
                     'active_kWh': None, 'inertia_kWh': None, 'idle_kWh': None,
                     'stage_on_fraction': None, 'load_over_min': None, 'unserved_H_kWh': None}
    return {'status': 'SCN', 'property_id': 'EOH2074', 'recorded_start': s['start'].isoformat(),
            'recorded_end': s['end'].isoformat(), 'year_current_endpoint': s['key'][1],
            'month': f'{s["key"][1]}-{s["key"][2]:02}', 'recorded_weekday': s['first_current'].weekday(),
            'recorded_hour': s['first_current'].hour, 'recorded_last_weekday': s['end'].weekday(),
            'recorded_last_hour': s['end'].hour, 'timezone': 'Q', 'temperature_proxy': s['proxy'],
            'steps': s['steps'], 'hours': hours, 'H_kWh': s['H'], 'E_kWh': s['E'],
            'source_status_before_aggregation': s['source_status'],
            'CP_kWh_complete_same_mask': s['CP'] if s['CP_steps'] == s['steps'] else None,
            'IH_kWh_complete_same_mask': s['IH'] if s['IH_steps'] == s['steps'] else None,
            'zero_or_negative_heat_E_kWh': s['zero_heat_E'], 'negative_heat_steps': s['negative_heat_steps'],
            'endpoint_proxy_mean_ambient_C': ambient, 'endpoint_proxy_mean_flow_C': flow,
            'endpoint_proxy_mean_return_C': s['R_sum'] / s['R_steps'] if s['R_steps'] else None,
            'all_endpoint_heating_flow_near55': complete and s['F_min'] >= 53 and s['F_max'] <= 57,
            **reference,
            'observed_minus_conditional_reference_kWh': s['E'] - reference['reference_kWh'] if reference['reference_kWh'] is not None else None,
            'same_SH_service_proven': False, 'installed_residual_admitted': False}


def analyze_eoh(root, model, output):
    source = Path(root) / 'eoh2074/clean/Property_ID=EOH2074.csv'
    scenario_cells, summary_rows, route_pools = {}, [], {}
    for minutes, offset in AGGREGATIONS:
        label = f'{minutes}min_offset{offset}'
        groups = {}
        cells = defaultdict(lambda: {'E': 0., 'reference': 0., 'H': 0., 'hours': 0., 'segments': 0})
        with gzip.open(output / f'eoh2074_{label}_segments.csv.gz', 'wt', encoding='utf-8', newline='') as handle:
            writer = None
            for s in segments(comparison.parsed_rows(source), minutes, offset, model):
                row = segment_reference(s, model)
                row['aggregation'] = label
                if writer is None:
                    writer = csv.DictWriter(handle, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row)
                collect_eoh_routes(route_pools, label, row, model)
                key = (row['year_current_endpoint'], row['month'], row['recorded_weekday'], row['recorded_hour'],
                       row['temperature_proxy'], row['branch'], state(row['H_kWh']),
                       comparison.band(row['endpoint_proxy_mean_ambient_C'], AMB_EDGES),
                       comparison.band(row['endpoint_proxy_mean_flow_C'], (-math.inf, 25, 35, 45, 53, 57, 60, math.inf)))
                if key not in groups:
                    groups[key] = {'segments': 0, 'steps': 0, 'hours': 0., 'H_kWh': 0., 'E_kWh': 0.,
                        'zero_or_negative_heat_E_kWh': 0., 'reference_kWh_known_only': 0., 'reference_known_hours': 0.,
                        'observed_E_kWh_reference_known_mask': 0., 'observed_H_kWh_reference_known_mask': 0.}
                g = groups[key]
                g['segments'] += 1
                for field in ('steps', 'hours', 'H_kWh', 'E_kWh', 'zero_or_negative_heat_E_kWh'):
                    g[field] += row[field]
                if row['reference_kWh'] is not None:
                    g['reference_kWh_known_only'] += row['reference_kWh']
                    g['reference_known_hours'] += row['hours']
                    g['observed_E_kWh_reference_known_mask'] += row['E_kWh']
                    g['observed_H_kWh_reference_known_mask'] += row['H_kWh']
                # Named SCN transfer only: no claim that the proxy proves SH.
                if (row['reference_kWh'] is not None and row['reference_kWh'] > 0
                        and row['negative_heat_steps'] == 0
                        and row['all_endpoint_heating_flow_near55']
                        and row['temperature_proxy'] == 'heating_temperature_indicated_not_service_proven'):
                    cell = transfer_cell(row['endpoint_proxy_mean_ambient_C'], row['load_over_min'], row['H_kWh'] > 1e-8)
                    record = cells[(row['year_current_endpoint'], *cell)]
                    for field, value in (('E', row['E_kWh']), ('reference', row['reference_kWh']),
                                         ('H', row['H_kWh']), ('hours', row['hours']), ('segments', 1)):
                        record[field] += value
        scenario_cells[label] = cells
        for key, values in sorted(groups.items()):
            year, month, weekday, hour, proxy, branch, heat_state, ambient, flow = key
            summary_rows.append({'status': 'SCN', 'aggregation': label, 'property_id': 'EOH2074',
                'year': year, 'month': month, 'recorded_weekday': weekday, 'recorded_hour': hour,
                'temperature_proxy': proxy, 'branch': branch, 'heat_state': heat_state,
                'ambient_bin_C': ambient, 'flow_bin_C': flow, **values})
    write_csv(output / 'eoh2074_condition_year_clock_replays.csv', summary_rows)
    return scenario_cells, summary_rows, route_pools


def hybrid_context(root, model, output):
    rows, cells = [], defaultdict(set)
    for r in csv_rows(Path(root) / 'comparison/documented_SH_primary_comparative_population.csv'):
        if r['category'] != comparison.CATEGORY:
            continue
        size, hours = float(r['PDI_size_kW']), float(r['hours'])
        # Dimensional size scaling is an explicitly unqualified counterfactual,
        # not evidence of equivalent product/control performance.
        scale = 5 / size
        h, e = float(r['HP_heat_kWh']) * scale, float(r['whole_E_kWh']) * scale
        ambient, flow = float(r['ambient_mean_C']), float(r['flow_mean_C'])
        reference = model.evaluate(h / hours, ambient, flow, duration_h=hours)
        cell = transfer_cell(ambient, reference['load_over_min'], True) if reference['load_over_min'] is not None else None
        if cell and 53 <= float(r['flow_min_C']) <= float(r['flow_max_C']) <= 57 and reference['reference_kWh'] is not None:
            cells[cell].add(r['property_id'])
        rows.append({'status': 'SCN', 'property_id': r['property_id'], 'PDI_model': r['PDI_model'],
            'recorded_start': r['start'], 'recorded_end': r['end'], 'year_start': r['year_start'],
            'year_end': r['year_end'], 'recorded_hour_start': r['recorded_hour_start'],
            'recorded_weekday_start': r['recorded_weekday_start'], 'recorded_start_month': r['recorded_start_month'],
            'steps': int(r['steps']), 'hours': hours, 'boiler_positive_steps': int(r['boiler_positive_steps']),
            'original_H_kWh': float(r['HP_heat_kWh']), 'original_E_kWh': float(r['whole_E_kWh']),
            'nameplate_kW': size, 'counterfactual_size_scale': scale,
            'size_scaled_H_kWh': h, 'size_scaled_E_kWh': e,
            'ambient_C': ambient, 'flow_C': flow, 'return_C': float(r['return_mean_C']), **reference,
            'cross_product_transfer_qualified': False, 'annual_idle_transfer_supported': False,
            'counterfactual_E_over_reference': e / reference['reference_kWh'] if reference['reference_kWh'] else None})
    if len(rows) != 4546 or sum(r['steps'] for r in rows) != 96019 or len({r['property_id'] for r in rows}) != 33:
        raise ValueError('full hybrid primary population required')
    write_csv(output / 'hybrid_all_windows_counterfactual_context.csv', rows)
    groups = defaultdict(lambda: {'windows': 0, 'hours': 0., 'original_H_kWh': 0., 'original_E_kWh': 0.,
        'reference_known_windows': 0, 'scaled_E_kWh_known_reference_mask': 0.,
        'counterfactual_reference_kWh_known_mask': 0., 'boiler_positive_windows': 0})
    for r in rows:
        g = groups[r['property_id'], r['year_start']]
        g['windows'] += 1
        g['boiler_positive_windows'] += r['boiler_positive_steps'] > 0
        for k in ('hours', 'original_H_kWh', 'original_E_kWh'):
            g[k] += r[k]
        if r['reference_kWh'] is not None:
            g['reference_known_windows'] += 1
            g['scaled_E_kWh_known_reference_mask'] += r['size_scaled_E_kWh']
            g['counterfactual_reference_kWh_known_mask'] += r['reference_kWh']
    write_csv(output / 'hybrid_system_year_context.csv', [
        {'status': 'SCN', 'property_id': prop, 'window_start_year': year, **g,
         'observed_active_window_H_over_E': g['original_H_kWh'] / g['original_E_kWh'],
         'size_scaled_E_over_counterfactual_reference': g['scaled_E_kWh_known_reference_mask'] / g['counterfactual_reference_kWh_known_mask'] if g['counterfactual_reference_kWh_known_mask'] else None,
         'annual_complete': False, 'WM50_transfer_qualified': False} for (prop, year), g in sorted(groups.items())])
    return cells, rows


def target_transfer(target, scenario_cells, hybrid_cells):
    rows, summaries = [], []
    years = (2021, 2022, 2023)
    for label, cells in scenario_cells.items():
        for year in (*years, 'ALL_YEARS_POOLED'):
            pools = defaultdict(lambda: [0., 0., 0, set()])
            for (source_year, *cell), values in cells.items():
                if year == 'ALL_YEARS_POOLED' or year == source_year:
                    p = pools[tuple(cell)]
                    p[0] += values['E']
                    p[1] += values['reference']
                    p[2] += values['segments']
                    p[3].add(source_year)
            partition = defaultdict(lambda: {'hours': 0., 'H_kWh': 0., 'reference_E_kWh': 0., 'conditional_replacement_E_kWh': 0.})
            for t in target:
                cell = transfer_cell(t['ambient_C'], t['load_over_min'], t['generator_H_kWh'] > 1e-8)
                p = pools.get(cell)
                # These categories quantify conditional numeric overlap, not E2 admission.
                support = 'CONDITIONAL_EOH_PROXY_W55_DUTY' if p and p[1] > 0 else 'UNIDENTIFIED'
                ratio = p[0] / p[1] if support != 'UNIDENTIFIED' else None
                replacement = t['reference_kWh'] * ratio if ratio is not None else None
                row = {'status': 'SCN', 'aggregation': label, 'donor_year': year,
                    'interval_start_utc': t['interval_start_utc'], 'target_ambient_bin_C': cell[0],
                    'target_load_over_min_bin': cell[1], 'target_positive_heat': cell[2],
                    'support': support, 'qualified_direct_support': False,
                    'hours': 1., 'generator_H_kWh': t['generator_H_kWh'],
                    'reference_E_kWh': t['reference_kWh'], 'stage_on_fraction': t['stage_on_fraction'],
                    'donor_segments_correlated': p[2] if p else 0,
                    'donor_year_count': len(p[3]) if p else 0,
                    'hybrid_context_systems_not_transfer': len(hybrid_cells.get(cell, set())),
                    'conditional_total_reference_replacement_ratio': ratio,
                    'conditional_replacement_E_kWh': replacement,
                    'conditional_signed_delta_kWh': replacement - t['reference_kWh'] if replacement is not None else None,
                    'installed_total_kWh': None}
                rows.append(row)
                g = partition[support]
                for k, value in (('hours', 1.), ('H_kWh', t['generator_H_kWh']), ('reference_E_kWh', t['reference_kWh']),
                                 ('conditional_replacement_E_kWh', replacement or 0.)):
                    g[k] += value
            for support in ('CONDITIONAL_EOH_PROXY_W55_DUTY', 'UNIDENTIFIED'):
                v = partition[support]
                summaries.append({'status': 'SCN', 'aggregation': label, 'donor_year': year, 'support': support,
                    **v, 'conditional_replacement_E_kWh': v['conditional_replacement_E_kWh'] if support != 'UNIDENTIFIED' else None,
                    'conditional_signed_delta_kWh': v['conditional_replacement_E_kWh'] - v['reference_E_kWh'] if support != 'UNIDENTIFIED' else None,
                    'hours_fraction': v['hours'] / len(target),
                    'heat_fraction': v['H_kWh'] / math.fsum(t['generator_H_kWh'] for t in target),
                    'reference_electricity_fraction': v['reference_E_kWh'] / math.fsum(t['reference_kWh'] for t in target),
                    'qualified_direct_hours': 0., 'installed_annual_point_estimate_kWh': None})
    return rows, summaries


SERVICE_CASES = ('HEATING_PROXY_WHOLE_E', 'ALL_SERVICE_AS_SH_WHOLE_E',
                 'MIXED_HALF_SH_WHOLE_E', 'HEATING_PROXY_LESS_IH_VALID')


def allocated_observation(row, case):
    """Named boundary alternatives, never an automatic IH correction."""
    proxy = row['temperature_proxy']
    heating = proxy == 'heating_temperature_indicated_not_service_proven'
    if case.startswith('HEATING_PROXY') and not heating:
        return None, 'SERVICE_PROXY_NOT_SELECTED'
    share = 1.
    if case == 'MIXED_HALF_SH_WHOLE_E' and not heating:
        share = 0. if proxy == 'DHW_temperature_indicated_not_service_proven' else .5
    if share == 0:
        return None, 'DHW_ONLY_ASSIGNED_ZERO_SH'
    energy = row['E_kWh']
    if case.endswith('LESS_IH_VALID'):
        ih = row['IH_kWh_complete_same_mask']
        if ih is None:
            return None, 'IH_COMMON_MASK_MISSING'
        if not 0 <= ih <= energy:
            return None, 'IH_OUTSIDE_AGGREGATED_WHOLE_E_BOUNDARY'
        energy -= ih
    return (share * row['H_kWh'], share * energy), 'CONDITIONAL_ALLOCATION'


def add_pool(pools, key, row, heat, energy, reference, *, boiler_positive=0):
    if key not in pools:
        pools[key] = dict(H_kWh=0., E_kWh=0., reference_kWh=0., variable_E_kWh=0.,
            variable_reference_kWh=0., idle_reference_kWh=0., hours=0., segments=0,
            first_recorded=row['recorded_start'], last_recorded=row['recorded_end'],
            boiler_positive_windows=0)
    p = pools[key]
    for k, value in (('H_kWh', heat), ('E_kWh', energy), ('reference_kWh', reference['reference_kWh']),
                     ('variable_E_kWh', energy - reference['idle_kWh']),
                     ('variable_reference_kWh', reference['active_kWh'] + reference['inertia_kWh']),
                     ('idle_reference_kWh', reference['idle_kWh']), ('hours', row['hours']), ('segments', 1),
                     ('boiler_positive_windows', boiler_positive)):
        p[k] += value
    p['first_recorded'] = min(p['first_recorded'], row['recorded_start'])
    p['last_recorded'] = max(p['last_recorded'], row['recorded_end'])


def collect_eoh_routes(pools, label, row, model):
    for case in SERVICE_CASES:
        allocated, _ = allocated_observation(row, case)
        if allocated is None or row['negative_heat_steps']:
            continue
        heat, energy = allocated
        # Measured zero-heat power does not require a rating map or a flow proxy.
        # Its service/month transfer remains an explicit, unqualified assumption.
        if abs(heat) <= 1e-8 and abs(row['H_kWh']) <= 1e-8:
            reference = dict(reference_kWh=.015 * row['hours'], active_kWh=0., inertia_kWh=0., idle_kWh=.015 * row['hours'])
            add_pool(pools, (label, 'EOH_ZERO_MONTH_POWER', case, 'EOH2074', row['year_current_endpoint'], row['month'][5:7]),
                     row, heat, energy, reference)
        if heat <= 1e-8 or row['source_status_before_aggregation'] != 'SUPPORTED':
            continue
        reference = model.evaluate(heat / row['hours'], row['endpoint_proxy_mean_ambient_C'],
                                   row['endpoint_proxy_mean_flow_C'], duration_h=row['hours'])
        if reference['reference_kWh'] is None:
            continue
        cell = transfer_cell(row['endpoint_proxy_mean_ambient_C'], reference['load_over_min'], True)
        routes = ['EOH_ACTUAL_CONDITIONS_TO_W55']
        if row['all_endpoint_heating_flow_near55']:
            routes.append('EOH_NEAR55_OBSERVED')
        for route in routes:
            add_pool(pools, (label, route, case, 'EOH2074', row['year_current_endpoint'], cell), row, heat, energy, reference)


def hybrid_transfer_pools(handoff, model):
    """Evaluate aggregate product/service alternatives; no boiler-off selection."""
    pools, exclusions = {}, Counter()
    for source in csv_rows(Path(handoff) / 'comparison/documented_SH_primary_comparative_population.csv'):
        if source['category'] != comparison.CATEGORY:
            continue
        h, e, hours = float(source['HP_heat_kWh']), float(source['whole_E_kWh']), float(source['hours'])
        scale = 5 / float(source['PDI_size_kW'])
        ta, flow = float(source['ambient_mean_C']), float(source['flow_mean_C'])
        ref = model.evaluate(scale * h / hours, ta, flow, duration_h=hours)
        if ref['reference_kWh'] is None:
            exclusions[ref['branch']] += 1
            continue
        cp_complete = int(source['CP_valid_steps']) == int(source['steps'])
        boiler_complete = int(source['boiler_valid_steps']) == int(source['steps'])
        cp = float(source['CP_kWh_valid_steps_only']) if cp_complete else None
        boiler = float(source['boiler_signed_kWh_valid_steps_only']) if boiler_complete else None
        cases = {'LINEAR_ALL_E': scale * e,
                 'RATING_IDLE_NONSCALING': ref['idle_kWh'] + scale * (e - ref['idle_kWh'])}
        if cp is not None and 0 <= cp <= e:
            cases['CP_NONSCALING_RETAINED'] = cp + scale * (e - cp)
            if boiler is not None and boiler >= 0:
                shared_fraction = boiler / (h + boiler) if h + boiler > 0 else 0.
                # Scenario: CP shared with boiler SH in proportion to metered heat.
                # The removed share is reported, never called compressor power.
                allocated_cp = cp * (1 - shared_fraction)
                cases['BOILER_SHARED_CP_HEAT_SHARE'] = allocated_cp + scale * (e - cp)
        else:
            exclusions['CP_BOUNDARY_INCOMPLETE_OR_INCONSISTENT'] += 1
        row = dict(recorded_start=source['start'], recorded_end=source['end'], hours=hours)
        cell = transfer_cell(ta, ref['load_over_min'], True)
        for case, energy in cases.items():
            add_pool(pools, ('HYBRID_WINDOWS', 'HYBRID_AGGREGATE_TO_W55', case, source['property_id'], int(source['year_start']), cell),
                     row, scale * h, energy, ref, boiler_positive=int(source['boiler_positive_steps']) > 0)
    return pools, exclusions


def split_recovery_audit(handoff, model):
    rows = []
    for s in segments(comparison.parsed_rows(Path(handoff) / 'eoh2074/clean/Property_ID=EOH2074.csv'), 60, 0):
        legacy = segment_reference(s, model)
        if legacy['branch'] != 'Q_ORIGINAL_ENDPOINT_SOURCE_SUPPORT':
            continue
        condition_good = [(p, c, d) for p, c, d in s['interval_records']
                          if d['H'] > 1e-8 and interval_source_status(p, c, model) == 'SUPPORTED']
        good = [(p, c, d) for p, c, d in condition_good
                if model.evaluate(d['H'] * 30, (p['A'] + c['A']) / 2,
                                  (p['F'] + c['F']) / 2, duration_h=1/30)['reference_kWh'] is not None]
        if condition_good:
            rows.append({'recorded_start': legacy['recorded_start'], 'recorded_end': legacy['recorded_end'],
                         'source_condition_positive_2min_steps_recovered': len(condition_good),
                         'source_condition_H_kWh_recovered': math.fsum(d['H'] for _, _, d in condition_good),
                         'source_condition_E_kWh_recovered': math.fsum(d['E'] for _, _, d in condition_good),
                         'supported_positive_2min_steps_recovered': len(good),
                         'H_kWh_recovered': math.fsum(d['H'] for _, _, d in good),
                         'E_kWh_recovered': math.fsum(d['E'] for _, _, d in good)})
    return rows


def summarize_pools(pools):
    return [{'status': 'SCN', 'aggregation': key[0], 'route': key[1], 'assumption': key[2],
             'property_id': key[3], 'donor_year': key[4], 'cell_or_month': json.dumps(key[5]), **v}
            for key, v in sorted(pools.items(), key=lambda item: str(item[0]))]


QUALIFICATION_BINDING_KEYS = ('route', 'product', 'service_case', 'accounting', 'donor_scope', 'aggregation', 'target_id')


def route_qualification(*, complete, physical, documented_assumptions, route_context=None):
    """E2 can use a justified aggregate mapping with validation debt, not E1 parts."""
    records = documented_assumptions.get('qualification_records', [])
    bound = [r for r in records if route_context is not None
             and set(r.get('binding', {})) == set(QUALIFICATION_BINDING_KEYS)
             and all(r['binding'][k] == route_context.get(k) for k in QUALIFICATION_BINDING_KEYS)]
    missing = ['EXACT_ROUTE_BOUND_EVIDENCE_ABSENT']
    if len(bound) == 1:
        criteria = bound[0].get('e2_criteria', [])
        if {c.get('criterion') for c in criteria} == set(range(1, 9)) and len(criteria) == 8:
            missing = [f'E2_CONDITION_{c["criterion"]}' for c in criteria
                       if c.get('verdict') != 'SUPPORTED_PROVISIONAL'
                       or not c.get('reason') or not c.get('quantitative_or_source_locators')]
        else:
            missing = ['EIGHT_CLAIM_SPECIFIC_E2_CRITERIA_REQUIRED']
    if complete and physical and not missing:
        return 'E2_CANDIDATE', []
    return ('SCN_COMPLETE_CONDITIONAL' if complete and physical else 'SCN_PARTIAL_OR_BOUNDARY_INCONSISTENT'), missing


def evaluate_transfer_routes(target, eoh_pools, hybrid_pools, assumption_evidence):
    """Target-weight actual device components; unknown cells remain explicit."""
    all_pools = {**eoh_pools, **hybrid_pools}
    details, results = [], []
    labels = sorted({k[0] for k in eoh_pools})
    route_cases = sorted({(k[1], k[2]) for k in all_pools if k[1] != 'EOH_ZERO_MONTH_POWER'})
    target_cells = defaultdict(lambda: dict(hours=0., H=0., E=0., variable=0., idle=0.))
    for t in target:
        positive = t['generator_H_kWh'] > 1e-8
        cell = transfer_cell(t['ambient_C'], t['load_over_min'], True) if positive else t['interval_start_utc'][5:7]
        v = target_cells[positive, cell]
        for k, x in (('hours', 1.), ('H', t['generator_H_kWh']), ('E', t['reference_kWh']),
                     ('variable', t['active_kWh'] + t['inertia_kWh']), ('idle', t['idle_kWh'])):
            v[k] += x
    for label in labels:
        for route, case in route_cases:
            keys = [k for k in all_pools if k[1:3] == (route, case) and k[0] in (label, 'HYBRID_WINDOWS')]
            donor_years = sorted({k[4] for k in keys})
            for year in ['ALL_YEARS_POOLED', *donor_years]:
                selected = [k for k in keys if year == 'ALL_YEARS_POOLED' or k[4] == year]
                positive_pools = defaultdict(list)
                for k in selected:
                    positive_pools[k[5]].append(all_pools[k])
                zero_case = case if case in SERVICE_CASES else 'HEATING_PROXY_WHOLE_E'
                zero_pools = defaultdict(list)
                for k, p in eoh_pools.items():
                    if k[0:3] == (label, 'EOH_ZERO_MONTH_POWER', zero_case) and (year == 'ALL_YEARS_POOLED' or k[4] == year):
                        zero_pools[k[5]].append(p)
                for accounting in ('TOTAL_REFERENCE_REPLACEMENT', 'VARIABLE_REPLACEMENT_IDLE_ONCE'):
                    known_h = known_e = known_hours = predicted = donor_hours = 0.
                    negative_prediction = False
                    for (positive, cell), t in target_cells.items():
                        ps = positive_pools.get(cell, []) if positive else zero_pools.get(cell, [])
                        weight = math.fsum(p['hours'] for p in ps)
                        ref = math.fsum(p['reference_kWh'] for p in ps)
                        variable = math.fsum(p['variable_reference_kWh'] for p in ps)
                        estimate = None
                        if ps:
                            if not positive and weight > 0:
                                estimate = t['hours'] * math.fsum(p['E_kWh'] for p in ps) / weight
                            elif accounting == 'TOTAL_REFERENCE_REPLACEMENT' and ref > 0:
                                estimate = t['E'] * math.fsum(p['E_kWh'] for p in ps) / ref
                            elif variable > 0:
                                estimate = t['variable'] * math.fsum(p['variable_E_kWh'] for p in ps) / variable + t['idle']
                        support = estimate is not None
                        if support:
                            known_h += t['H']; known_e += t['E']; known_hours += t['hours']; predicted += estimate
                            negative_prediction |= estimate < 0
                            donor_hours += weight
                        details.append({'status': 'SCN', 'aggregation': label, 'route': route, 'assumption': case,
                            'donor_year': year, 'accounting': accounting, 'positive_heat': positive,
                            'target_cell_or_month': json.dumps(cell), 'supported': support,
                            'target_hours': t['hours'], 'target_H_kWh': t['H'], 'baseline_E_kWh': t['E'],
                            'conditional_replacement_E_kWh': estimate, 'donor_hours': weight,
                            'donor_segments_correlated': sum(p['segments'] for p in ps),
                            'target_idle_kWh_already_included': t['idle']})
                    complete = math.isclose(known_hours, len(target))
                    context = dict(route=route, product='HETEROGENEOUS_HYBRID' if route.startswith('HYBRID') else wm50.PRODUCT,
                        service_case=case, accounting=accounting, donor_scope=f'{"HYBRID33" if route.startswith("HYBRID") else "EOH2074"}:{year}',
                        aggregation=label, target_id='HU.N.SFH.01.Bel80.ReEx.001.013:W55:UTC2025')
                    qualification, missing = route_qualification(complete=complete, physical=not negative_prediction,
                                                                  documented_assumptions=assumption_evidence, route_context=context)
                    total_h = math.fsum(t['generator_H_kWh'] for t in target)
                    total_e = math.fsum(t['reference_kWh'] for t in target)
                    results.append({'status': qualification, 'aggregation': label, 'route': route, 'assumption': case,
                        'donor_year': year, 'accounting': accounting, 'supported_hours': known_hours,
                        'supported_H_kWh': known_h, 'supported_baseline_E_kWh': known_e,
                        'unidentified_hours': len(target) - known_hours, 'unidentified_H_kWh': total_h - known_h,
                        'unidentified_baseline_E_kWh': total_e - known_e,
                        'conditional_known_E_kWh': predicted, 'conditional_known_signed_delta_kWh': predicted - known_e,
                        'conditional_full_annual_E_kWh': predicted if complete and not negative_prediction else None,
                        'admissible_E2_annual_E_kWh': predicted if qualification == 'E2_CANDIDATE' else None,
                        'unqualified_assumptions': ';'.join(missing), 'negative_cell_prediction': negative_prediction})
    return details, results


def boundary_audit(output):
    groups = {}
    for minutes, offset in AGGREGATIONS:
        label = f'{minutes}min_offset{offset}'
        with gzip.open(output / f'eoh2074_{label}_segments.csv.gz', 'rt', encoding='utf-8', newline='') as f:
            for r in csv.DictReader(f):
                key = label, r['year_current_endpoint'], r['temperature_proxy'], state(float(r['H_kWh']))
                if key not in groups:
                    groups[key] = dict(segments=0, hours=0., H_kWh=0., E_kWh=0., IH_common_segments=0,
                        IH_common_H_kWh=0., IH_common_E_kWh=0., IH_common_IH_kWh=0.,
                        IH_exceeds_E_segments=0, IH_excess_kWh=0., CP_common_segments=0,
                        CP_common_E_kWh=0., CP_common_CP_kWh=0.)
                g = groups[key]; g['segments'] += 1
                for c in ('hours', 'H_kWh', 'E_kWh'):
                    g[c] += float(r[c])
                if r['IH_kWh_complete_same_mask']:
                    ih, e = float(r['IH_kWh_complete_same_mask']), float(r['E_kWh'])
                    g['IH_common_segments'] += 1
                    g['IH_common_H_kWh'] += float(r['H_kWh'])
                    g['IH_common_E_kWh'] += e; g['IH_common_IH_kWh'] += ih
                    g['IH_exceeds_E_segments'] += ih > e
                    g['IH_excess_kWh'] += max(ih - e, 0.)
                if r['CP_kWh_complete_same_mask']:
                    g['CP_common_segments'] += 1
                    g['CP_common_E_kWh'] += float(r['E_kWh'])
                    g['CP_common_CP_kWh'] += float(r['CP_kWh_complete_same_mask'])
    return [{'status': 'DER', 'aggregation': k[0], 'year': k[1], 'temperature_proxy': k[2],
             'heat_state': k[3], **v} for k, v in sorted(groups.items())]


def evaluated_decision(results, spec, target_summary):
    e2 = [r for r in results if r['admissible_E2_annual_E_kWh'] is not None]
    preferred = spec['revision']['predeclared_central_route']
    selected = next((r for r in e2 if all(r[k] == v for k, v in preferred.items())), None)
    complete_scn = [r['conditional_full_annual_E_kWh'] for r in results if r['conditional_full_annual_E_kWh'] is not None]
    return {'status': 'E2_CANDIDATE_FOR_REVIEW' if selected else 'NO_ADMISSIBLE_E2_FROM_EVALUATED_ROUTES',
        'selected_central_E2_installed_kWh': selected['admissible_E2_annual_E_kWh'] if selected else None,
        'annual_signed_installed_residual_kWh': selected['admissible_E2_annual_E_kWh'] - target_summary['device_reference_kWh'] if selected else None,
        'device_reference_kWh': target_summary['device_reference_kWh'], 'evaluated_route_variants': len(results),
        'complete_conditional_variants': len(complete_scn), 'E2_candidate_variants': len(e2),
        'complete_SCN_annual_envelope_kWh': {'min': min(complete_scn) if complete_scn else None,
                                          'max': max(complete_scn) if complete_scn else None},
        'qualification_evidence': spec['revision']['assumption_evidence'],
        'unqualified_assumptions': sorted({s for r in results for s in r['unqualified_assumptions'].split(';') if s}),
        'uncertainty_kind': 'EMPIRICAL_AND_ENGINEERING_SCENARIO_ENVELOPE_NOT_CONFIDENCE_INTERVAL',
        'remaining_identifying_link': spec['remaining_identifying_link'], 'non_admission': spec['non_admission']}


def assessment_target(prior):
    fields = ('ambient_C','load_over_min','generator_H_kWh','reference_kWh','active_kWh','inertia_kWh','idle_kWh')
    return [{**r, **{k: float(r[k]) for k in fields}} for r in csv_rows(Path(prior)/'target_8760_hour_device_reference.csv')]


def correlation_stat():
    return dict(n=0, H_kWh=0., E_kWh=0., IH_kWh=0., IH_over_E_steps=0, excess_kWh=0.,
                sx=0., sy=0., sxx=0., syy=0., sxy=0.)


def add_timing_stat(s, h, e, ih):
    s['n'] += 1; s['H_kWh'] += h; s['E_kWh'] += e; s['IH_kWh'] += ih
    s['IH_over_E_steps'] += ih > e
    s['excess_kWh'] += max(ih-e,0.)
    for k, v in (('sx',ih),('sy',e),('sxx',ih*ih),('syy',e*e),('sxy',ih*e)):
        s[k] += v


def finish_timing(s):
    n=s['n']; vx=n*s['sxx']-s['sx']**2; vy=n*s['syy']-s['sy']**2
    return {k:v for k,v in s.items() if k not in ('sx','sy','sxx','syy','sxy')} | {
        'pearson_r': (n*s['sxy']-s['sx']*s['sy'])/math.sqrt(vx*vy) if vx>0 and vy>0 else None}


def endpoint_mode(row):
    """Dictionary valve-mode temperature channels, not return-temperature inference."""
    sh=row['F'] is not None;dhw=row['HW'] is not None
    return 'SH' if sh and not dhw else 'DHW' if dhw and not sh else 'BOTH' if sh else 'MISSING'


def interval_mode(previous,current):
    left,right=endpoint_mode(previous),endpoint_mode(current)
    if left==right and left in ('SH','DHW'):return f'{left}_MODE_ENDPOINTS'
    if {left,right}=={'SH','DHW'}:return 'SH_DHW_TRANSITION'
    if left==right=='BOTH':return 'BOTH_CHANNELS_UNALLOCATED'
    if left==right=='MISSING':return 'MISSING_MODE'
    return 'MODE_BOUNDARY_OR_INCOMPLETE'


def raw_service_and_timing(handoff, output):
    """Signed same-mask ledgers, common-lag cohort and common-hour aggregation."""
    ledger={}; lag_stats={}; aggregate={}; recent=deque(maxlen=31)
    lags=(-15,-5,-2,-1,0,1,2,5,15)
    previous=None; hour_key=None; hour_rows=[]
    totals=dict(HEI_steps=0,HEI_H_kWh=0.,HEI_E_kWh=0.,HEI_IH_kWh=0.,
                complete_hour_steps=0,complete_hour_H_kWh=0.,complete_hour_E_kWh=0.,complete_hour_IH_kWh=0.)
    def flush_hour():
        if len(hour_rows)!=30 or not all(all(k in r['d'] for k in ('H','E','IH')) for r in hour_rows):
            return
        totals['complete_hour_steps']+=30
        for c in ('H','E','IH'):
            totals[f'complete_hour_{c}_kWh']+=math.fsum(r['d'][c] for r in hour_rows)
        for steps in (1,5,15,30):
            for start in range(0,30,steps):
                subset=hour_rows[start:start+steps]
                service={r['proxy'] for r in subset}
                proxy=next(iter(service)) if len(service)==1 else 'MIXED_WITHIN_BLOCK'
                key=(hour_key[0],steps*2,proxy)
                if key not in aggregate:aggregate[key]=correlation_stat()
                add_timing_stat(aggregate[key],*(math.fsum(r['d'][c] for r in subset) for c in ('H','E','IH')))
    for cur in comparison.parsed_rows(Path(handoff)/'eoh2074/clean/Property_ID=EOH2074.csv'):
        d=comparison.differences(previous,cur)
        if previous is not None:
            proxy=comparison.proxy(previous,cur)
            for mask,channels in comparison.MASKS.items():
                if all(c in d for c in channels):
                    key=(cur['t'].year,cur['t'].strftime('%Y-%m'),proxy,mask,interval_mode(previous,cur))
                    if key not in ledger:ledger[key]=comparison.empty_balance(channels)
                    comparison.add_balance(ledger[key],d)
            rec=dict(t=cur['t'],proxy=proxy,d=d)
            recent.append(rec)
            if all(c in d for c in ('H','E','IH')):
                totals['HEI_steps']+=1
                for c in ('H','E','IH'):totals[f'HEI_{c}_kWh']+=d[c]
            k=(cur['t'].year,int(((cur['t']-datetime(1970,1,1)).total_seconds()-1)//3600))
            if hour_key is not None and k!=hour_key:
                flush_hour();hour_rows=[]
            hour_key=k;hour_rows.append(rec)
            if len(recent)==31 and all('E' in r['d'] for r in recent):
                centre=recent[15]
                if all(c in centre['d'] for c in ('H','E','IH')):
                    for lag in lags:
                        for service in ('ALL_SAME_LAG_MASK',centre['proxy']):
                            key=(centre['t'].year,service,lag)
                            if key not in lag_stats:lag_stats[key]=correlation_stat()
                            add_timing_stat(lag_stats[key],centre['d']['H'],recent[15+lag]['d']['E'],centre['d']['IH'])
        previous=cur
    flush_hour()
    rows=[dict(status='DER',year=k[0],month=k[1],temperature_proxy=k[2],mask=k[3],documented_mode_endpoints=k[4],
               **comparison.finish_balance(v,comparison.MASKS[k[3]])) for k,v in sorted(ledger.items())]
    write_csv(output/'same_mask_service_month_ledgers.csv',rows)
    lag_rows=[dict(status='DER',year=k[0],temperature_proxy=k[1],E_lag_minutes=k[2]*2,
                   cohort='HEI_CENTRE_AND_E_ALL_31_ORIGINAL_ADJACENT_STEPS',**finish_timing(v)) for k,v in sorted(lag_stats.items())]
    write_csv(output/'IH_E_same_mask_lag_diagnostics.csv',lag_rows)
    write_csv(output/'IH_E_common_hour_aggregation_diagnostics.csv',[
        dict(status='DER',year=k[0],aggregation_minutes=k[1],temperature_proxy=k[2],
             cohort='SAME_COMPLETE_60MIN_HEI_COHORT',**finish_timing(v)) for k,v in sorted(aggregate.items())])
    totals.update({f'complement_{c}_kWh':totals[f'HEI_{c}_kWh']-totals[f'complete_hour_{c}_kWh'] for c in ('H','E','IH')})
    totals['complement_steps']=totals['HEI_steps']-totals['complete_hour_steps']
    totals['lag_choice_is_diagnostic_not_applied']=True
    write_json(output/'IH_timing_cohort_closure.json',totals)
    return rows,lag_rows,totals


def assessment_pool_add(pools,key,r,energy):
    if key not in pools:pools[key]=dict(E=0.,variable_E=0.,variable_ref=0.,H=0.,hours=0.,segments=0)
    p=pools[key]
    for k,v in (('E',energy),('variable_E',energy-r['idle_kWh']),
                ('variable_ref',r['active_kWh']+r['inertia_kWh']),('H',r['H_kWh']),('hours',r['hours']),('segments',1)):
        p[k]+=v


def assessment_predict(target,positive_pools,zero_pools):
    known_hours=known_h=known_ref=estimate=0.; weights=[]
    for t in target:
        pos=t['generator_H_kWh']>1e-8
        key=transfer_cell(t['ambient_C'],t['load_over_min'],True) if pos else t['interval_start_utc'][5:7]
        p=positive_pools.get(key) if pos else zero_pools.get(key)
        value=None
        if p:
            if pos and p['variable_ref']>0:
                value=(t['active_kWh']+t['inertia_kWh'])*p['variable_E']/p['variable_ref']+t['idle_kWh']
            elif not pos and p['hours']>0:value=p['E']/p['hours']
        if value is not None:
            known_hours+=1;known_h+=t['generator_H_kWh'];known_ref+=t['reference_kWh'];estimate+=value
        weights.append(dict(interval_start_utc=t['interval_start_utc'],positive_heat=pos,supported=value is not None,
                            H_kWh=t['generator_H_kWh'],baseline_E_kWh=t['reference_kWh'],conditional_E_kWh=value))
    return dict(supported_hours=known_hours,supported_H_kWh=known_h,supported_baseline_E_kWh=known_ref,
                conditional_known_E_kWh=estimate,conditional_annual_E_kWh=estimate if known_hours==len(target) else None),weights


def normalized_assessment(prior,target,output):
    """Observed-condition stratification, exact paired IH cohorts and target weights."""
    cases=('REFERENCE_HEATING_WHOLE','HEI_COMPLETE_WHOLE','HEI_VALID_PAIR_WHOLE','HEI_VALID_PAIR_MINUS_IH')
    pools={c:defaultdict(dict) for c in cases}; strata={}; slices={}; zero={}
    path=Path(prior)/'eoh2074_60min_offset0_segments.csv.gz'
    with gzip.open(path,'rt',encoding='utf-8',newline='') as f:
        for text in csv.DictReader(f):
            r={**text,**{k:float(text[k]) if text[k] else None for k in ('H_kWh','E_kWh','hours','active_kWh','inertia_kWh','idle_kWh','load_over_min',
                'endpoint_proxy_mean_ambient_C','endpoint_proxy_mean_flow_C','IH_kWh_complete_same_mask')}}
            heating=r['temperature_proxy']=='heating_temperature_indicated_not_service_proven'
            positive=r['H_kWh']>1e-8
            pure_zero=abs(r['H_kWh'])<=1e-8 and int(r['negative_heat_steps'])==0
            ref_ok=positive and text['reference_kWh'] and r['source_status_before_aggregation']=='SUPPORTED' and int(r['negative_heat_steps'])==0
            if not (ref_ok or pure_zero):continue
            if not positive:
                # Zero observed power is not a rating interpolation at missing/outside temperatures.
                r.update(active_kWh=0.,inertia_kWh=0.,idle_kWh=.015*r['hours'])
            cell=transfer_cell(r['endpoint_proxy_mean_ambient_C'],r['load_over_min'],True) if positive else r['month'][5:7]
            ih=r['IH_kWh_complete_same_mask']; complete=ih is not None; consistent=complete and 0<=ih<=r['E_kWh']
            if heating:
                for c in cases:
                    if c=='HEI_COMPLETE_WHOLE' and not complete:continue
                    if c.startswith('HEI_VALID_PAIR') and not consistent:continue
                    energy=r['E_kWh']-(ih if c=='HEI_VALID_PAIR_MINUS_IH' else 0.)
                    kind='positive' if positive else 'zero'
                    assessment_pool_add(pools[c][kind],cell,r,energy)
            if pure_zero:
                key=(r['year_current_endpoint'],r['month'],r['temperature_proxy'])
                if key not in zero:zero[key]=dict(hours=0.,E_kWh=0.,segments=0)
                z=zero[key];z['hours']+=r['hours'];z['E_kWh']+=r['E_kWh'];z['segments']+=1
            if ref_ok:
                flow=comparison.band(r['endpoint_proxy_mean_flow_C'],(-math.inf,25,30,35,40,45,50,53,57,60,math.inf))
                key=(r['year_current_endpoint'],flow,cell[0],cell[1],r['temperature_proxy'])
                assessment_pool_add(strata,key,r,r['E_kWh'])
                if heating:
                    for dimension,value in (('FLOW',flow),('YEAR',r['year_current_endpoint'])):
                        assessment_pool_add(slices,(dimension,value,cell),r,r['E_kWh'])
    results=[]
    for c in cases:
        pred,weights=assessment_predict(target,pools[c]['positive'],pools[c]['zero'])
        results.append(dict(status='SCN',case=c,**pred))
        if c=='REFERENCE_HEATING_WHOLE':
            if not math.isclose(pred['conditional_annual_E_kWh'],4003.3949236948883,abs_tol=1e-7):
                raise ValueError('designated route replay changed')
            write_csv(output/'designated_route_target_weights.csv',weights)
    write_csv(output/'same_mask_IH_allocation_target_effects.csv',results)
    write_csv(output/'normalized_residual_joint_strata.csv',[
        dict(status='DER',year=k[0],flow_bin_C=k[1],ambient_bin_C=k[2],load_min_bin=k[3],temperature_proxy=k[4],**p,
             normalized_variable_E_ratio=p['variable_E']/p['variable_ref'] if p['variable_ref'] else None)
        for k,p in sorted(strata.items())])
    exposures=[]
    for dim,value in sorted({(k[0],k[1]) for k in slices}):
        ps={k[2]:p for k,p in slices.items() if k[:2]==(dim,value)}
        pred,_=assessment_predict(target,ps,pools['REFERENCE_HEATING_WHOLE']['zero'])
        exposures.append(dict(status='SCN',dimension=dim,value=value,**pred))
    write_csv(output/'normalized_residual_target_exposure_by_flow_year.csv',exposures)
    # Compare flow strata only on the identical positive target-cell intersection.
    comparisons=[]
    flows=sorted({k[1] for k in slices if k[0]=='FLOW'})
    for i,left in enumerate(flows):
        for right in flows[i+1:]:
            lp={k[2]:p for k,p in slices.items() if k[:2]==('FLOW',left)}
            rp={k[2]:p for k,p in slices.items() if k[:2]==('FLOW',right)}
            eligible=[t for t in target if t['generator_H_kWh']>1e-8 and transfer_cell(t['ambient_C'],t['load_over_min'],True) in lp
                      and transfer_cell(t['ambient_C'],t['load_over_min'],True) in rp]
            if not eligible:continue
            l,_=assessment_predict(eligible,lp,{})
            r,_=assessment_predict(eligible,rp,{})
            comparisons.append(dict(status='DER',left_flow=left,right_flow=right,common_target_hours=len(eligible),
                common_target_H_kWh=math.fsum(t['generator_H_kWh'] for t in eligible),
                common_baseline_E_kWh=math.fsum(t['reference_kWh'] for t in eligible),
                left_conditional_E_kWh=l['conditional_known_E_kWh'],right_conditional_E_kWh=r['conditional_known_E_kWh'],
                right_minus_left_kWh=r['conditional_known_E_kWh']-l['conditional_known_E_kWh'],causal_temperature_effect=False))
    write_csv(output/'normalized_flow_comparison_same_target_cells.csv',comparisons)
    year_comparisons=[]
    years=sorted({k[1] for k in slices if k[0]=='YEAR'})
    for i,left in enumerate(years):
        for right in years[i+1:]:
            lp={k[2]:p for k,p in slices.items() if k[:2]==('YEAR',left)}
            rp={k[2]:p for k,p in slices.items() if k[:2]==('YEAR',right)}
            eligible=[t for t in target if t['generator_H_kWh']>1e-8 and transfer_cell(t['ambient_C'],t['load_over_min'],True) in lp
                      and transfer_cell(t['ambient_C'],t['load_over_min'],True) in rp]
            l,_=assessment_predict(eligible,lp,{});r,_=assessment_predict(eligible,rp,{})
            year_comparisons.append(dict(status='DER',left_year=left,right_year=right,common_target_hours=len(eligible),
                common_target_H_kWh=math.fsum(t['generator_H_kWh'] for t in eligible),
                left_conditional_E_kWh=l['conditional_known_E_kWh'],right_conditional_E_kWh=r['conditional_known_E_kWh'],
                right_minus_left_kWh=r['conditional_known_E_kWh']-l['conditional_known_E_kWh']))
    write_csv(output/'normalized_year_comparison_same_target_cells.csv',year_comparisons)
    joint={}
    for (year,flow,ambient,load,service),p in strata.items():
        if service=='heating_temperature_indicated_not_service_proven':joint[year,flow,(ambient,load,True)]=p
    joint_comparisons=[]
    for dimension,fixed,values in [('YEAR_WITHIN_FLOW',f,years) for f in flows]+[('FLOW_WITHIN_YEAR',y,flows) for y in years]:
        for i,left in enumerate(values):
            for right in values[i+1:]:
                def select(value):
                    return {k[2]:p for k,p in joint.items() if (k[0]==value and k[1]==fixed if dimension=='YEAR_WITHIN_FLOW' else k[0]==fixed and k[1]==value)}
                lp,rp=select(left),select(right)
                eligible=[t for t in target if t['generator_H_kWh']>1e-8 and transfer_cell(t['ambient_C'],t['load_over_min'],True) in lp
                          and transfer_cell(t['ambient_C'],t['load_over_min'],True) in rp]
                if not eligible:continue
                l,_=assessment_predict(eligible,lp,{});r,_=assessment_predict(eligible,rp,{})
                joint_comparisons.append(dict(status='DER',dimension=dimension,fixed_stratum=fixed,left=left,right=right,
                    common_target_hours=len(eligible),common_target_H_kWh=math.fsum(t['generator_H_kWh'] for t in eligible),
                    left_conditional_E_kWh=l['conditional_known_E_kWh'],right_conditional_E_kWh=r['conditional_known_E_kWh'],
                    right_minus_left_kWh=r['conditional_known_E_kWh']-l['conditional_known_E_kWh'],
                    left_donor_hours=sum(p['hours'] for p in lp.values()),right_donor_hours=sum(p['hours'] for p in rp.values()),
                    causal_effect_identified=False))
    write_csv(output/'normalized_joint_year_flow_same_target_cells.csv',joint_comparisons)
    zero_rows=[dict(status='DER',year=k[0],month=k[1],temperature_proxy=k[2],**p,observed_zero_heat_kW=p['E_kWh']/p['hours'])
               for k,p in sorted(zero.items())]
    write_csv(output/'broad_month_zero_heat_service_rates.csv',zero_rows)
    zero_effects=[]
    for year in ('2021','2022','2023','ALL_YEARS_POOLED'):
        ps={}
        for (y,month,proxy),p in zero.items():
            if (year=='ALL_YEARS_POOLED' or y==year) and proxy=='heating_temperature_indicated_not_service_proven':
                m=month[5:7]
                if m not in ps:ps[m]=dict(E=0.,hours=0.)
                ps[m]['E']+=p['E_kWh'];ps[m]['hours']+=p['hours']
        pred,_=assessment_predict([t for t in target if t['generator_H_kWh']<=1e-8],{},ps)
        zero_effects.append(dict(status='SCN',donor_year=year,**pred))
    write_csv(output/'zero_heat_target_month_transport_by_year.csv',zero_effects)
    return results,exposures,comparisons,zero_effects,joint_comparisons


def matched_season_state_assessment(prior,target,output):
    """Donor composition standardization; no causal year/controller identification.

    Symmetric donor-reference weights compare the same state mix. They do not
    identify target return temperature or controller state. Target-month exposure
    is separate from applying a donor-month diagnostic to all target cells.
    """
    rows=[];inventory={};unmatched={};month_unmatched={}
    with gzip.open(Path(prior)/'eoh2074_60min_offset0_segments.csv.gz','rt',encoding='utf-8',newline='') as f:
        for text in csv.DictReader(f):
            if (text['temperature_proxy']!='heating_temperature_indicated_not_service_proven'
                or text['source_status_before_aggregation']!='SUPPORTED' or not text['reference_kWh']
                or int(text['negative_heat_steps']) or float(text['H_kWh'])<=1e-8):continue
            r={**text,**{k:float(text[k]) for k in ('H_kWh','E_kWh','hours','active_kWh','inertia_kWh','idle_kWh','load_over_min',
                'endpoint_proxy_mean_ambient_C','endpoint_proxy_mean_flow_C','stage_on_fraction')}}
            r['return_C']=float(text['endpoint_proxy_mean_return_C']) if text['endpoint_proxy_mean_return_C'] else None
            r['cell']=transfer_cell(r['endpoint_proxy_mean_ambient_C'],r['load_over_min'],True)
            r['flow']=comparison.band(r['endpoint_proxy_mean_flow_C'],(-math.inf,25,30,35,40,45,50,53,57,60,math.inf))
            r['month_number']=text['month'][5:7]
            rows.append(r)
            assessment_pool_add(inventory,(r['year_current_endpoint'],r['month_number'],r['flow']),r,r['E_kWh'])
            assessment_pool_add(unmatched,(r['year_current_endpoint'],r['flow'],r['cell']),r,r['E_kWh'])
            assessment_pool_add(month_unmatched,(r['year_current_endpoint'],r['month_number'],r['flow'],r['cell']),r,r['E_kWh'])
    write_csv(output/'season_state_donor_inventory.csv',[dict(year=k[0],month=k[1],flow_bin_C=k[2],**p) for k,p in sorted(inventory.items())])
    levels=('MONTH_FLOW','MONTH_FLOW_GE45MIN','MONTH_FLOW_DURATION','MONTH_FLOW_DURATION_RETURN','MONTH_FLOW_DURATION_RETURN_DUTY')
    estimates=[]
    for level in levels:
        pools={}
        for r in rows:
            if level=='MONTH_FLOW_GE45MIN' and r['hours']<.75:continue
            if 'RETURN' in level and r['return_C'] is None:continue
            duration=comparison.band(r['hours'],(-math.inf,.25,.5,.75,1.000001,math.inf)) if 'DURATION' in level else 'ALL'
            ret=comparison.band(r['return_C'],(-math.inf,*range(10,66,5),math.inf)) if 'RETURN' in level else 'ALL'
            duty=comparison.band(r['stage_on_fraction'],(-math.inf,.25,.5,.75,1.000001,math.inf)) if 'DUTY' in level else 'ALL'
            assessment_pool_add(pools,(r['year_current_endpoint'],r['month_number'],r['flow'],r['cell'],duration,ret,duty),r,r['E_kWh'])
        for month,flow in sorted({k[1:3] for k in pools}):
            years=sorted({k[0] for k in pools if k[1:3]==(month,flow)})
            for i,left in enumerate(years):
                for right in years[i+1:]:
                    lp={k[3:]:p for k,p in pools.items() if k[:3]==(left,month,flow)}
                    rp={k[3:]:p for k,p in pools.items() if k[:3]==(right,month,flow)}
                    common={k for k in lp.keys()&rp.keys() if lp[k]['variable_ref']>0 and rp[k]['variable_ref']>0}
                    cells={k[0] for k in common}
                    lrat={};rrat={}
                    for cell in cells:
                        group=[k for k in common if k[0]==cell]
                        total=math.fsum(lp[k]['variable_ref']+rp[k]['variable_ref'] for k in group)
                        lrat[cell]=math.fsum((lp[k]['variable_ref']+rp[k]['variable_ref'])/total*lp[k]['variable_E']/lp[k]['variable_ref'] for k in group)
                        rrat[cell]=math.fsum((lp[k]['variable_ref']+rp[k]['variable_ref'])/total*rp[k]['variable_E']/rp[k]['variable_ref'] for k in group)
                    for exposure in ('TARGET_SAME_MONTH','ALL_TARGET_CELL_EXPOSURE_DIAGNOSTIC'):
                        eligible=[t for t in target if t['generator_H_kWh']>1e-8
                            and (exposure!='TARGET_SAME_MONTH' or t['interval_start_utc'][5:7]==month)
                            and transfer_cell(t['ambient_C'],t['load_over_min'],True) in cells]
                        if not eligible:continue
                        def predicted(ratios):
                            return math.fsum((t['active_kWh']+t['inertia_kWh'])*ratios[transfer_cell(t['ambient_C'],t['load_over_min'],True)]+t['idle_kWh'] for t in eligible)
                        le,re=predicted(lrat),predicted(rrat)
                        def raw_ratios(year,selected_month):
                            result={}
                            for cell in cells:
                                if selected_month:
                                    p=month_unmatched[year,month,flow,cell];result[cell]=p['variable_E']/p['variable_ref']
                                else:
                                    p=unmatched[year,flow,cell];result[cell]=p['variable_E']/p['variable_ref']
                            return result
                        original=predicted(raw_ratios(right,False))-predicted(raw_ratios(left,False))
                        month_delta=predicted(raw_ratios(right,True))-predicted(raw_ratios(left,True))
                        estimates.append(dict(status='DER_CONDITIONAL_STANDARDIZATION',level=level,exposure=exposure,month=month,
                            flow_bin_C=flow,left_year=left,right_year=right,common_state_cells=len(common),common_target_hours=len(eligible),
                            common_target_H_kWh=math.fsum(t['generator_H_kWh'] for t in eligible),
                            common_target_reference_kWh=math.fsum(t['reference_kWh'] for t in eligible),
                            left_common_donor_hours=math.fsum(lp[k]['hours'] for k in common),right_common_donor_hours=math.fsum(rp[k]['hours'] for k in common),
                            left_common_donor_segments=sum(lp[k]['segments'] for k in common),right_common_donor_segments=sum(rp[k]['segments'] for k in common),
                            left_conditional_E_kWh=le,right_conditional_E_kWh=re,remaining_standardized_difference_kWh=re-le,
                            original_year_mix_difference_same_target_kWh=original,month_selected_difference_same_target_kWh=month_delta,
                            month_selection_change_kWh=original-month_delta,within_month_composition_change_kWh=month_delta-(re-le),
                            total_composition_change_kWh=original-(re-le),annual_extrapolated=False,causal_year_or_controller_effect=False,
                            standardization='SYMMETRIC_POOLED_DONOR_REFERENCE_SHARES_NOT_OBSERVED_TARGET_STATE_MIX'))
    write_csv(output/'matched_month_duration_return_duty_target_exposure.csv',estimates)
    return estimates


def qualify_assessment(target,weights,record):
    """Derive completeness and physical validity from actual hourly predictions."""
    expected={t['interval_start_utc'] for t in target}
    ids=[r.get('interval_start_utc') for r in weights]
    complete=(len(expected)==len(target)==len(ids) and len(set(ids))==len(ids) and set(ids)==expected
              and all(r.get('supported') in (True,'True') for r in weights))
    target_by_id={t['interval_start_utc']:t for t in target}
    physical=bool(weights)
    for r in weights:
        try:value=float(r.get('conditional_E_kWh'))
        except (TypeError,ValueError):complete=False;physical=False;continue
        if not math.isfinite(value):complete=False;physical=False
        if value<0 or (target_by_id.get(r.get('interval_start_utc'),{}).get('generator_H_kWh',0)>1e-8 and value<=0):physical=False
    status,missing=route_qualification(complete=complete,physical=physical,
        documented_assumptions={'qualification_records':[record]},route_context=record['binding'])
    return dict(qualification=status,unqualified_criteria=missing,complete=complete,physical=physical)


def assess_aggregate_e2(additive,handoff,prior,output):
    spec=json.loads(MANIFEST.read_text(encoding='utf-8'));cfg=spec['aggregate_assessment']
    prior=Path(prior).resolve();output=Path(output).resolve();additive=Path(additive).resolve();handoff=Path(handoff).resolve()
    if any(output==p or output.is_relative_to(p) for p in (ROOT,prior,additive,handoff)):
        raise ValueError('separate new assessment output required')
    verify_additive(additive,spec)
    comparison.verify_handoff(handoff,json.loads((ROOT/'registry/b05_eoh_comparison_support_manifest.json').read_text())['input_binding'])
    if digest(prior/'INPUT_CODE_OUTPUT_MANIFEST.json')!=cfg['prior_output_manifest_sha256']:
        raise ValueError('prior output identity mismatch')
    previous=json.loads((prior/'INPUT_CODE_OUTPUT_MANIFEST.json').read_text())
    if previous['research_code_sha256']!=cfg['prior_merged_code_sha256']:
        raise ValueError('prior merged analyzer identity mismatch')
    for entry in previous['outputs']:
        p=(prior/entry['path']).resolve()
        if not p.is_relative_to(prior) or digest(p)!=entry['sha256']:raise ValueError('prior numerical output mismatch')
    for rel,h in spec['protected_sha256'].items():
        if digest(ROOT/rel)!=h:raise ValueError('protected runtime/evidence changed')
    output.mkdir(parents=True,exist_ok=False)
    print('Verified 52 original/additive inputs and every prior R1 output',flush=True)
    target=assessment_target(prior)
    ledger,lags,timing=raw_service_and_timing(handoff,output)
    effects,exposures,flow,zero,joint=normalized_assessment(prior,target,output)
    matched=matched_season_state_assessment(prior,target,output)
    summary=dict(status='CONDITIONAL_ASSESSED_NOT_ADMITTED',designated_conditional_kWh=effects[0]['conditional_annual_E_kWh'],
        same_mask_IH_effects=effects,normalization_flow_comparisons=flow,year_exposures=[r for r in exposures if r['dimension']=='YEAR'],
        zero_state_year_effects=zero,normalization_joint_comparisons=joint,matched_season_state_comparisons=matched,IH_timing_cohort=timing,canonical_or_national_admission=False,
        remaining_identification='Numeric target coverage is complete. Remaining claims concern same-SH/electrical boundary and transport of normalized positive/zero-state energy, assessed in E2 evidence table; not unidentified target cells.')
    claims=claim_evidence_table(spec,summary)
    write_csv(output/'claim_specific_eight_point_E2_evidence.csv',claims)
    record=dict(binding=cfg['binding'],
        e2_criteria=[dict(criterion=r['criterion'],verdict=r['verdict'],reason=r['reason'],
                         quantitative_or_source_locators=r['locators']) for r in claims if r['claim_id']=='C_INSTALLED_ANNUAL'])
    summary.update(qualify_assessment(target,list(csv_rows(output/'designated_route_target_weights.csv')),record))
    summary['dictionary_local_verification']=cfg['dictionary_acquisition']['local_status']
    write_json(output/'AGGREGATE_E2_ASSESSMENT.json',summary)
    write_json(output/'EXACT_ROUTE_QUALIFICATION_RECORD.json',record)
    manifest=dict(main_commit=cfg['base_main_commit'],source_manifest_sha256=digest(MANIFEST),source_code_sha256=digest(Path(__file__)),
        original_manifest_sha256=digest(handoff/'HANDOFF_MANIFEST.json'),additive_manifest_sha256=digest(additive/'ADDITIVE_INPUT_MANIFEST.json'),
        prior_output_manifest_sha256=digest(prior/'INPUT_CODE_OUTPUT_MANIFEST.json'),protected_sha256=spec['protected_sha256'],
        outputs=[dict(path=p.name,bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(output.iterdir()) if p.is_file()])
    write_json(output/'INPUT_CODE_OUTPUT_MANIFEST.json',manifest)
    print(f'Aggregate assessment complete; designated conditional result {summary["designated_conditional_kWh"]!r}',flush=True)


def claim_evidence_table(spec, summary):
    """Apply the canonical eight requirements separately to each asserted quantity.

    SUPPORTED_PROVISIONAL is a scoped assessment, never observed installed truth.
    A conditional criterion prevents promotion without demanding E1 components.
    """
    names = ('defined quantity', 'unit/grain/boundary/period', 'qualified direct support',
             'target applicability', 'contradictory evidence assessment', 'reproducible derivation',
             'exact validation debt', 'provisional label')
    flow = max(summary['normalization_flow_comparisons'],
               key=lambda r: abs(r['right_minus_left_kWh']), default=None)
    paired = {r['case']: r for r in summary['same_mask_IH_effects']}
    ih_delta = (paired['HEI_VALID_PAIR_WHOLE']['conditional_known_E_kWh']
                - paired['HEI_VALID_PAIR_MINUS_IH']['conditional_known_E_kWh'])
    boundary = (f'Documented valve-mode temperature recording supports stable endpoint service classification. '
                f'Exact valid-IH paired target exposure changes by {ih_delta:.9g} kWh; '
                'transition/missing modes and nonadditive cumulative meters remain explicit, not zero-imputed.')
    transport = (f'Largest observed flow-stratum contrast on identical target cells: {flow["right_minus_left_kWh"]:.9g} kWh '
                 f'over {flow["common_target_hours"]} positive target hours; '
                 'ambient/load cell conditioning does not identify flow causality or target installation state.' if flow
                 else 'No pair of observed flow strata shares positive target cells.')
    year = max((r for r in summary['normalization_joint_comparisons'] if r['dimension']=='YEAR_WITHIN_FLOW'),
               key=lambda r:abs(r['right_minus_left_kWh']),default=None)
    if year:
        transport += (f' Within the same {year["fixed_stratum"]} C flow bin, years {year["left"]}/{year["right"]} '
                      f'differ by {year["right_minus_left_kWh"]:.9g} kWh on {year["common_target_hours"]} identical positive '
                      f'target hours; donor exposure {year["left_donor_hours"]:.9g}/{year["right_donor_hours"]:.9g} h. '
                      'This contrast confounds donor year with seasonal composition; it is not an isolated year or controller effect.')
    season = next((r for r in summary['matched_season_state_comparisons'] if r['level']=='MONTH_FLOW_GE45MIN'
                   and r['exposure']=='ALL_TARGET_CELL_EXPOSURE_DIAGNOSTIC' and r['month']=='02'
                   and r['flow_bin_C']=='[25,30)' and (r['left_year'],r['right_year'])==('2022','2023')),None)
    if season:
        transport += (f' Independently matched February2022/2023 donors,25--30C,at least45min observation duration '
                      f'leave {season["remaining_standardized_difference_kWh"]:.9g} kWh on {season["common_target_hours"]} '
                      f'common target-cell exposure hours; composition/eligibility change versus original year mix '
                      f'{season["total_composition_change_kWh"]:.9g} kWh on those same hours. '
                      'Target-same-month results and return/duty-standardized common support are separately emitted; '
                      'partial support is never annualized and no causal controller attribution is made.')
    claims = {
        'C_REFERENCE_METHOD': ('Manufacturer power interpolation and existing E2 on/off reference, not installed energy',
                               'registry/b05_annual_device_reference_manifest.json', {}),
        'C_SERVICE_BOUNDARY': ('Stable documented SH mode with whole-system electricity; transition allocation retained',
                               'same_mask_service_month_ledgers.csv;IH_E_same_mask_lag_diagnostics.csv', {4: boundary, 5: boundary}),
        'C_NORMALIZED_TRANSPORT': ('Dimensionless variable-energy residual transported from actual conditions to W55',
                                   'normalized_residual_joint_strata.csv;matched_month_duration_return_duty_target_exposure.csv', {4: transport, 5: transport}),
        'C_ZERO_STATE_TRANSPORT': ('Broad observed SH-mode zero-heat month power transported to target zero hours',
                                  'broad_month_zero_heat_service_rates.csv;zero_heat_target_month_transport_by_year.csv',
                                  {4: 'Month/year/service composition is measured; observed zero heat does not identify idle, storage, defrost or auxiliary states. Target zero-state composition is not observed.'}),
        'C_INSTALLED_ANNUAL': (f'Conditional {summary["designated_conditional_kWh"]:.12g} kWh over all 8760 target hours',
                               'AGGREGATE_E2_ASSESSMENT.json;designated_route_target_weights.csv',
                               {4: transport + ' ' + boundary, 5: transport}),
    }
    rows=[]
    for claim,(quantity,locators,conditional) in claims.items():
        for criterion,name in enumerate(names,1):
            reasons={1:quantity, 2:json.dumps(spec['aggregate_assessment']['binding'],sort_keys=True),
                     3:'Hash-bound official EOH measurements/dictionary extracts and manufacturer rating evidence; these support measured donor quantities and reference arithmetic within their boundaries.',
                     4:'Applicable to the named reference method only; no installed residual or hybrid promotion.',
                     5:'Measured residual variation does not contradict the rating-only reference claim.',
                     6:'Pinned inputs, prior numerical output hash verification and emitted target weights reproduce the stated quantity.',
                     7:'VD-B05-AGGREGATE-SERVICE-TRANSITION: interval mode/energy attribution; VD-B05-AGGREGATE-TRANSPORT: target installation and zero-state transport; supplier: EOH meter/controller metadata and target calibration. Material to installed annual finalization; not an E1 prerequisite.',
                     8:'Existing reference E2 remains unchanged; installed results remain SCN unless all eight exact-bound criteria support one provisional base.'}
            rows.append(dict(claim_id=claim,criterion=criterion,requirement=name,
                             verdict='CONDITIONAL_NOT_IDENTIFIED' if criterion in conditional else 'SUPPORTED_PROVISIONAL',
                             reason=conditional.get(criterion,reasons[criterion]),locators=locators))
    return rows


def run(additive, handoff, output):
    spec = json.loads(MANIFEST.read_text(encoding='utf-8'))
    additive, handoff, output = Path(additive).resolve(), Path(handoff).resolve(), Path(output).resolve()
    addition = verify_additive(additive, spec)
    old_spec = json.loads((ROOT / 'registry/b05_eoh_comparison_support_manifest.json').read_text(encoding='utf-8'))
    old_handoff = comparison.verify_handoff(handoff, old_spec['input_binding'])
    for rel, expected in spec['protected_sha256'].items():
        if digest(ROOT / rel) != expected:
            raise ValueError('protected canonical/source file changed: ' + rel)
    if any(output == r or output.is_relative_to(r) for r in (ROOT, additive, handoff)):
        raise ValueError('separate new output required')
    output.mkdir(parents=True, exist_ok=False)
    print('All 19 additive and 33 original inputs verified', flush=True)
    weather = recovered_weather(additive, spec)
    model = LoadReference()
    target, target_summary = target_reference(weather, model, spec)
    write_csv(output / 'target_8760_hour_device_reference.csv', target)
    write_json(output / 'target_device_summary.json', target_summary)
    print(f'Independent research device reference: {target_summary["device_reference_kWh"]!r} kWh', flush=True)
    mask_ledger, mask_checks = original_mask_ledger(handoff)
    write_csv(output / 'eoh2074_original_four_mask_year_ledger.csv', mask_ledger)
    write_csv(output / 'eoh2074_original_45_year_control_checks.csv', mask_checks)
    annual = list(csv_rows(additive / 'eoh_controls/all_period_common_interval_year.csv'))
    monthly = list(csv_rows(additive / 'eoh_controls/all_period_common_interval_month.csv'))
    controls = check_period_controls(annual, monthly)
    write_csv(output / 'all_34_system_month_year_control_checks.csv', controls)
    coverage = {(r['property_id'], r['year']): r for r in csv_rows(additive / 'eoh_controls/system_year_coverage.csv')}
    full_period = []
    for r in annual:
        c = coverage[r['property_id'], r['year']]
        e = float(r['whole_E_kWh_HP_E_common'])
        full_period.append({'status': 'DER', **r,
            'present_fraction_of_calendar_year': c['observed_rows_fraction_full_calendar_year'],
            'zero_or_negative_heat_E_fraction_of_same_mask': float(r['whole_E_kWh_when_HP_heat_zero_or_negative']) / e if e else None,
            'observed_common_hours': float(r['HP_E_common_steps']) / 30,
            'full_year_annualized': False, 'E_minus_CP_is_compressor_energy': False,
            'active_windows_are_full_period': False})
    write_csv(output / 'all_34_system_year_observed_period_balances.csv', full_period)
    shutil.copyfile(additive / 'eoh_controls/all_period_common_interval_month.csv', output / 'all_34_system_month_observed_period_balances.csv')
    hybrid_cells, hybrids = hybrid_context(handoff, model, output)
    hybrid_pools, hybrid_exclusions = hybrid_transfer_pools(handoff, model)
    scenario_cells, donor_summary, route_pools = analyze_eoh(handoff, model, output)
    recovered = split_recovery_audit(handoff, model)
    write_csv(output / 'preaggregation_split_recovery_audit.csv', recovered)
    write_json(output / 'preaggregation_split_recovery_summary.json', {
        'old_segments_with_supported_positive_steps': len(recovered),
        **{k: math.fsum(r[k] for r in recovered) for k in
           ('source_condition_positive_2min_steps_recovered', 'source_condition_H_kWh_recovered',
            'source_condition_E_kWh_recovered', 'supported_positive_2min_steps_recovered', 'H_kWh_recovered', 'E_kWh_recovered')}})
    write_csv(output / 'service_IH_CP_zero_heat_boundary_audit.csv', boundary_audit(output))
    write_csv(output / 'all_evaluated_donor_route_cells.csv', summarize_pools({**route_pools, **hybrid_pools}))
    route_details, route_results = evaluate_transfer_routes(target, route_pools, hybrid_pools,
                                                          spec['revision']['assumption_evidence'])
    write_csv(output / 'evaluated_target_cell_transfers.csv', route_details)
    write_csv(output / 'evaluated_annual_transfer_routes.csv', route_results)
    write_json(output / 'hybrid_transfer_exclusions.json', dict(hybrid_exclusions))
    # Every aggregation independently reproduces all HP/E signed annual/monthly controls.
    replay_checks = []
    for label in scenario_cells:
        for control in (r for r in monthly if r['property_id'] == 'EOH2074'):
            selected = [r for r in donor_summary if r['aggregation'] == label and r['month'] == control['month']]
            for field, original in (('steps', 'HP_E_common_steps'), ('H_kWh', 'HP_heat_kWh_HP_E_common'),
                                    ('E_kWh', 'whole_E_kWh_HP_E_common'),
                                    ('zero_or_negative_heat_E_kWh', 'whole_E_kWh_when_HP_heat_zero_or_negative')):
                actual = math.fsum(r[field] for r in selected)
                expected = float(control[original])
                if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-7):
                    raise ValueError(f'aggregation changed original monthly ledger: {label}/{control["month"]}/{field}')
                replay_checks.append({'aggregation': label, 'month': control['month'], 'field': field,
                                      'actual': actual, 'expected': expected, 'difference': actual - expected})
    write_csv(output / 'eoh2074_original_monthly_replay_checks.csv', replay_checks)
    transfer, support = target_transfer(target, scenario_cells, hybrid_cells)
    write_csv(output / 'target_hour_transfer_weights_scenarios.csv', transfer)
    write_csv(output / 'target_support_by_year_and_aggregation.csv', support)
    conditional = [r for r in support if r['support'] == 'CONDITIONAL_EOH_PROXY_W55_DUTY']
    legacy_diagnostic = {'status': 'NARROW_NEAR55_DIAGNOSTIC_NOT_GENERAL_TRANSFER', 'selected_central_E2_installed_kWh': None,
        'annual_signed_installed_residual_kWh': None, 'device_reference_kWh': target_summary['device_reference_kWh'],
        'qualified_direct_time_heat_electricity_fractions': [0., 0., 0.],
        'conditional_overlap_sensitivity': {
            'minimum_hours_fraction': min(r['hours_fraction'] for r in conditional),
            'maximum_hours_fraction': max(r['hours_fraction'] for r in conditional),
            'minimum_heat_fraction': min(r['heat_fraction'] for r in conditional),
            'maximum_heat_fraction': max(r['heat_fraction'] for r in conditional),
            'minimum_reference_E_fraction': min(r['reference_electricity_fraction'] for r in conditional),
            'maximum_reference_E_fraction': max(r['reference_electricity_fraction'] for r in conditional)},
        'uncertainty_kind': 'EMPIRICAL_YEAR_AND_AGGREGATION_SCENARIO_ENVELOPE_NOT_CONFIDENCE_INTERVAL',
        'uncertainty_full_installed_annual_kWh': {'lower': None, 'upper': None, 'identified': False},
        'remaining_identifying_link': spec['remaining_identifying_link'],
        'hybrid_windows': len(hybrids), 'hybrid_boiler_positive_windows_retained': sum(r['boiler_positive_steps'] > 0 for r in hybrids),
        'annual_control_checks': len(controls), 'monthly_replay_checks': len(replay_checks),
        'non_admission': spec['non_admission']}
    write_json(output / 'NEAR55_ONLY_DIAGNOSTIC.json', legacy_diagnostic)
    decision = evaluated_decision(route_results, spec, target_summary)
    write_json(output / 'ANNUAL_TRANSFER_DECISION.json', decision)
    provenance = {'additive_input_manifest_sha256': digest(additive / 'ADDITIVE_INPUT_MANIFEST.json'),
        'original_handoff_manifest_sha256': digest(handoff / 'HANDOFF_MANIFEST.json'),
        'research_manifest_sha256': digest(MANIFEST), 'research_code_sha256': digest(Path(__file__)),
        'inputs': {'additive': addition['files'], 'original': old_handoff['files']},
        'protected_sha256': spec['protected_sha256'], 'outputs': [
            {'path': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(output.iterdir()) if p.is_file()]}
    write_json(output / 'INPUT_CODE_OUTPUT_MANIFEST.json', provenance)
    print(f'Annual transfer decision: {decision["status"]}; all outputs saved to {output}', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--additive', type=Path, required=True)
    p.add_argument('--handoff', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--assessment-only', action='store_true')
    p.add_argument('--prior-output', type=Path)
    a = p.parse_args()
    if a.assessment_only:
        if a.prior_output is None:p.error('--assessment-only requires --prior-output')
        assess_aggregate_e2(a.additive,a.handoff,a.prior_output,a.output)
    else:
        run(a.additive, a.handoff, a.output)


if __name__ == '__main__':
    main()
