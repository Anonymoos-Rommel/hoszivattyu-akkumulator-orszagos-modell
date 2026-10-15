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
from collections import Counter, defaultdict
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


def route_qualification(*, complete, physical, documented_assumptions):
    """E2 can use a justified aggregate mapping with validation debt, not E1 parts."""
    missing = [name for name, evidence in documented_assumptions.items()
               if evidence.get('status') != 'JUSTIFIED_FOR_TARGET' or not evidence.get('source_ids')]
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
                    qualification, missing = route_qualification(complete=complete, physical=not negative_prediction,
                                                                  documented_assumptions=assumption_evidence)
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
    a = p.parse_args()
    run(a.additive, a.handoff, a.output)


if __name__ == '__main__':
    main()
