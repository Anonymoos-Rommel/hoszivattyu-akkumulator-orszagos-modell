"""One pinned, read-only 72-hour thermal SCN and same-service capacity check.

IEE Projects TABULA + EPISCOPE (www.episcope.eu).
Adatbázis: Meteorológiai Adattár, HungaroMet Nonprofit Zrt.
This is a finite first-law experiment, not a validated building/runtime model.
Only calculate_reference certifies the pinned case. Private helpers are numeric
or parser test seams, never alternative source-admission APIs. No file is written.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import fmean
from zoneinfo import ZoneInfo

from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B05.weather import materialized_intervals

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / 'registry/b06_hourly_thermal_reference_manifest.json'
MANIFEST_SHA256 = '1e167ccef1a40cc916f72ab0b8d11edfde84ad61980e81bc45836aec4248f90d'
CASE_ID = 'SCN-HOURLY-TABULA-SFH01-72H-2025-001'
OPAQUE = ('Roof_1', 'Roof_2', 'Wall_1', 'Wall_2', 'Wall_3', 'Floor_1', 'Floor_2')
PARTS = OPAQUE + ('Window_1', 'Window_2', 'Door_1')
UTC = timezone.utc


def _load_manifest(path):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed source/scenario manifest bytes mismatch; repinning requires review')
    manifest = json.loads(data)
    for name, pin in manifest['repository_pins'].items():
        if hashlib.sha256((ROOT / pin['path']).read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('reviewed repository source/code hash mismatch: ' + name)
    return manifest


def _source_building(manifest):
    package = json.loads((ROOT / manifest['repository_pins']['building']['path']).read_text())
    contract = manifest['building']
    for key in ('source_id', 'source_sha256', 'sheet'):
        if package[key] != contract[key]:
            raise ValueError('building source identity mismatch')
    if package['scope'] != contract['source_scope']:
        raise ValueError('building source scope mismatch')
    selected = [r for r in package['rows'] if r['values']['Code_BuildingVariant'] == contract['variant']]
    if len(selected) != 1 or selected[0]['source_row'] != contract['source_row']:
        raise ValueError('exact unique source building row required')
    item = selected[0]
    for field, expected in contract['parameter_lineage'].items():
        column = package['columns'][field]
        if (item['values'][field] != expected['value'] or column['native_unit'] != expected['native_unit']
                or f"{package['sheet']}!{column['column']}{item['source_row']}" != expected['source_cell']):
            raise ValueError('building parameter/value/unit/cell mismatch: ' + field)
    return item


def _build_parameters(item, manifest):
    """Transfer source assembly parameters as SCN; no seasonal factors or heat."""
    v = item['values']
    p = {k: q['value'] for k, q in manifest['scenario'].items()}
    effective, conductance = {}, {}
    for component in PARTS:
        u = number(v['U_' + component], 'U', True)
        fraction = number(v['f_Measure_' + component], 'fraction', True)
        extra = v['R_Add_UnheatedSpace_' + component] if component in OPAQUE else 0
        resistance = (1 / u + extra) if u else 0
        if component in OPAQUE and v['Code_MeasureType_' + component] == 'ReplaceInsulation':
            resistance -= v['d_Insulation_' + component] / p['insulation_conductivity_w_mk']
        denominator = (extra if v['Code_MeasureType_' + component] == 'Replace' else resistance) + v['R_Measure_' + component]
        modified = 1 / denominator if denominator else 0
        original = 1 / (1 / u + extra) if u else 0
        effective[component] = (1 - fraction) * original + fraction * modified
        conductance[component] = v['A_Calc_' + component] * effective[component]
    area = sum(v['A_Calc_' + c] for c in PARTS)
    refurbished = sum(v['f_Measure_' + c] * v['A_Calc_' + c] for c in PARTS if v['R_Measure_' + c] > 0) / area
    delta_u = ((1 - refurbished) * v['delta_U_ThermalBridging_Original']
               + refurbished * v['delta_U_ThermalBridging_Refurbished'])
    bridge = area * delta_u
    vent = p['air_volumetric_heat_capacity_wh_m3k'] * (v['n_air_use'] + v['n_air_infiltration']) * v['h_room'] * v['A_C_Ref']
    lower = conductance['Floor_1'] + conductance['Floor_2']
    outside = sum(conductance.values()) - lower + bridge + vent
    p.update(effective_u_w_m2k=effective, component_h_w_k=conductance,
             thermal_bridge_h_w_k=bridge, ventilation_h_w_k=vent,
             outdoor_h_w_k=outside, lower_boundary_h_w_k=lower, total_h_w_k=outside + lower,
             capacity_wh_k=v['c_m'] * v['A_C_Ref'], internal_gain_w=v['phi_int'] * v['A_C_Ref'],
             source_variant=v['Code_BuildingVariant'], source_row=item['source_row'],
             evidence_status='SCN')
    return p


def _endpoint(value):
    end = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if end.tzinfo is None or end.utcoffset() != timedelta(0) or end.minute or end.second or end.microsecond:
        raise ValueError('whole-hour UTC boundary required')
    return end


def _parse_weather_rows(rows, manifest):
    contract = manifest['weather']
    rows = list(rows)
    if len(rows) != contract['panel_rows']:
        raise ValueError('complete pinned weather endpoint panel required')
    for row in rows:
        if (row['source_id'] != contract['source_id'] or row['station_id'] != contract['station_id']
                or row['weather_profile_id'] != contract['profile_id']):
            raise ValueError('weather source/station/profile mismatch')
    intervals = materialized_intervals(rows)
    if (intervals[0].interval_end_utc != _endpoint(contract['first_endpoint_utc'])
            or intervals[-1].interval_end_utc != _endpoint(contract['last_endpoint_utc'])):
        raise ValueError('weather panel endpoint boundary mismatch')
    return [dict(start=r.interval_start_utc, end=r.interval_end_utc, ta=r.mean_temperature_c,
                 rh=r.end_relative_humidity_pct, station_id=r.station_id, source_id=r.source_id) for r in intervals]


def _load_weather(manifest):
    with (ROOT / manifest['repository_pins']['weather']['path']).open(encoding='utf-8', newline='') as handle:
        rows = [r for r in csv.DictReader(handle) if r['weather_profile_id'] == manifest['weather']['profile_id']]
    return _parse_weather_rows(rows, manifest)


def _select_weather(panel, manifest):
    c = manifest['weather']
    hours = c['hours']
    # Selection is made on observed ta before radiation is read; first tie wins.
    index = min(range(len(panel) - hours + 1), key=lambda i: sum(r['ta'] for r in panel[i:i + hours]))
    selected = panel[index:index + hours]
    if (index != c['selection_index'] or selected[0]['start'] != _endpoint(c['physical_start_utc'])
            or selected[-1]['end'] != _endpoint(c['physical_end_utc'])):
        raise ValueError('reviewed finite weather selection drift')
    return selected


def _optional_observation(value, name):
    if value is None or value.strip() in ('', '-999'):
        return None
    return number(float(value), name)


def _parse_radiation_rows(rows, weather_panel, manifest):
    """Validate joint OBS fields; return solar keyed by physical interval start."""
    rows = list(rows)
    contract = manifest['external_radiation']
    if len(rows) != len(weather_panel):
        raise ValueError('radiation panel row count mismatch')
    radiation = {}
    for row, weather in zip(rows, weather_panel):
        if set(row) != set(contract['required_columns']):
            raise ValueError('radiation columns/units mismatch')
        if (row['source_id'] != contract['source_id'] or row['station_id'] != manifest['weather']['station_id']):
            raise ValueError('radiation source/station mismatch')
        start, end = _endpoint(row['interval_start_utc']), _endpoint(row['source_endpoint_utc'])
        if (end - start != timedelta(hours=1) or start != weather['start'] or end != weather['end']
                or start in radiation):
            raise ValueError('radiation unique contiguous endpoint/interval-start join mismatch')
        ta = _optional_observation(row['ta_C'], 'radiation ta')
        rh = _optional_observation(row['u_pct_at_endpoint'], 'radiation RH')
        if ta != weather['ta'] or rh != weather['rh']:
            raise ValueError('radiation/weather joint observation mismatch')
        sr = _optional_observation(row['sr_J_cm2_native'], 'sr')
        energy = _optional_observation(row['global_energy_kWh_m2_DER'], 'global energy')
        power = _optional_observation(row['global_hour_mean_W_m2_DER'], 'global mean power')
        if sr is None:
            if energy is not None or power is not None:
                raise ValueError('missing solar cannot have derived energy/power')
        elif (sr < 0 or energy is None or power is None
              or not math.isclose(energy, sr / 360, rel_tol=1e-9, abs_tol=1e-10)
              or not math.isclose(power, sr * 25 / 9, rel_tol=1e-9, abs_tol=1e-8)):
            raise ValueError('sr J/cm2 to interval kWh/m2 and W/m2 unit closure failed')
        radiation[start] = sr
    return radiation


def _load_radiation(path, panel, manifest):
    if path is None:
        return {}, 'Q_MISSING_EXTERNAL_RADIATION'
    data = Path(path).read_bytes()
    pin = manifest['external_radiation']
    if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ValueError('reviewed external radiation bytes/hash mismatch')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8')))
    if reader.fieldnames != pin['required_columns']:
        raise ValueError('radiation field/unit schema mismatch')
    return _parse_radiation_rows(reader, panel, manifest), 'VERIFIED_EXTERNAL_BYTES_AND_INTERVAL_JOINS'

def number(v, name, nonnegative=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or (not math.isfinite(v)):
        raise ValueError(f'{name}: finite number required, never Q/None/boolean')
    if nonnegative and v < 0:
        raise ValueError(f'{name}: nonnegative required')
    return v

def solar_position(dt, lat, lon):
    """NOAA general solar equations; UTC, midpoint; no atmospheric refraction."""
    hours = dt.hour + dt.minute / 60 + dt.second / 3600
    days = 366 if dt.year % 4 == 0 and (dt.year % 100 != 0 or dt.year % 400 == 0) else 365
    gamma = 2 * math.pi / days * (dt.timetuple().tm_yday - 1 + (hours - 12) / 24)
    eot = 229.18 * (7.5e-05 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
    decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma) - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
    ha = math.radians((hours * 60 + eot + 4 * lon) / 4 - 180)
    phi = math.radians(lat)
    east = -math.cos(decl) * math.sin(ha)
    north = math.cos(phi) * math.sin(decl) - math.sin(phi) * math.cos(decl) * math.cos(ha)
    up = math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(ha)
    return (east, north, up)

def solar_gain(sr_j_cm2, dt, v, p):
    """OBS interval energy -> SCN Erbs + isotropic shortwave north-window gain."""
    number(sr_j_cm2, 'sr', True)
    ghi = sr_j_cm2 * 25 / 9
    e, n, z = solar_position(dt, p['latitude_deg'], p['longitude_deg'])
    b = 2 * math.pi * (dt.timetuple().tm_yday - 1) / 365
    ext = 1366.1 * (1.00011 + 0.034221 * math.cos(b) + 0.00128 * math.sin(b) + 0.000719 * math.cos(2 * b) + 7.7e-05 * math.sin(2 * b))
    kt = min(1, max(0, ghi / (ext * max(z, 0.065))))
    df = 1 - 0.09 * kt if kt <= 0.22 else 0.9511 - 0.1604 * kt + 4.388 * kt ** 2 - 16.638 * kt ** 3 + 12.336 * kt ** 4 if kt <= 0.8 else 0.165
    dhi = df * ghi
    if z < math.cos(math.radians(87)):
        dni = 0.0
        dhi = ghi
        low_sun = True
    else:
        dni = (ghi - dhi) / z
        low_sun = False
    direct = max(0, n) * dni
    sky = 0.5 * dhi
    ground = 0.5 * p['ground_shortwave_albedo'] * ghi
    if any((v['A_Calc_Window_' + x] for x in ('East', 'South', 'West', 'Horizontal'))):
        raise ValueError('north-only window case required')
    gain = (direct + sky + ground) * v['A_Calc_Window_North'] * v['F_sh_vert'] * (1 - v['F_f']) * v['F_w'] * v['g_gl_n_Measure_Window_1']
    return dict(ghi_w_m2=ghi, dhi_scn_w_m2=dhi, dni_scn_w_m2=dni, clearness_index_scn=kt, north_direct_w_m2=direct, north_sky_diffuse_w_m2=sky, north_ground_reflected_w_m2=ground, solar_gain_scn_w=gain, solar_low_sun_rule_applied=low_sun, horizontal_radiation_closure_w_m2=ghi - dhi - dni * max(0, z))

def transition(t0, ta, gains_w, heat_w, p, hours=1.0):
    """Analytic constant-input first-law step and independent integral balance."""
    for n, x in (('t0', t0), ('ta', ta), ('gains', gains_w), ('heat', heat_w), ('hours', hours)):
        number(x, n)
    for name in ('outdoor_h_w_k', 'lower_boundary_h_w_k'):
        number(p[name], name, True)
    number(p['lower_boundary_temperature_c'], 'lower reservoir temperature')
    if not math.isclose(p['total_h_w_k'], p['outdoor_h_w_k'] + p['lower_boundary_h_w_k'], rel_tol=0, abs_tol=1e-9):
        raise ValueError('total H must equal the two boundary conductances')
    h = p['total_h_w_k']
    c = p['capacity_wh_k']
    number(h, 'H', True)
    number(c, 'C', True)
    if h <= 0 or c <= 0 or hours <= 0:
        raise ValueError('H,C,dt must be positive')
    forcing = p['outdoor_h_w_k'] * ta + p['lower_boundary_h_w_k'] * p['lower_boundary_temperature_c'] + gains_w + heat_w
    eq = forcing / h
    a = math.exp(-h * hours / c)
    t1 = eq + (t0 - eq) * a
    integral = eq * hours + (t0 - eq) * (1 - a) * c / h
    loss_out = p['outdoor_h_w_k'] * (integral - ta * hours)
    loss_lower = p['lower_boundary_h_w_k'] * (integral - p['lower_boundary_temperature_c'] * hours)
    delta = c * (t1 - t0)
    residual = delta - ((heat_w + gains_w) * hours - loss_out - loss_lower)
    return dict(t_end_c=t1, t_mean_c=integral / hours, storage_change_wh=delta, outdoor_loss_wh=loss_out, lower_boundary_loss_wh=loss_lower, energy_balance_residual_wh=residual, equilibrium_c=eq)

def required_heat(t0, ta, gains, target, p):
    number(target, 'target')
    free = transition(t0, ta, gains, 0, p)
    a = math.exp(-p['total_h_w_k'] / p['capacity_wh_k'])
    return max(0, (target - free['t_end_c']) * p['total_h_w_k'] / (1 - a))

def deficit_degree_hours(t0, step, target, p):
    """Exact positive part integral of target minus monotonic exponential state."""
    t1 = step['t_end_c']
    eq = step['equilibrium_c']
    k = p['total_h_w_k'] / p['capacity_wh_k']
    if min(t0, t1) >= target:
        return 0.0
    if max(t0, t1) <= target:
        return target - step['t_mean_c']
    cross = -math.log((target - eq) / (t0 - eq)) / k
    lo, hi = (0, cross) if t0 < target else (cross, 1)
    integ = eq * (hi - lo) + (t0 - eq) * (math.exp(-k * lo) - math.exp(-k * hi)) / k
    return target * (hi - lo) - integ

def _support_cells(grid, ta, supply):
    cells = []
    for mode in ('MAX', 'MIN'):
        column = [r for r in grid if r['mode'] == mode and float(r['supply_temperature_c']) == supply]
        lower = [float(r['outdoor_temperature_c']) for r in column if float(r['outdoor_temperature_c']) <= ta]
        upper = [float(r['outdoor_temperature_c']) for r in column if float(r['outdoor_temperature_c']) >= ta]
        if not lower or not upper:
            continue
        for row in column:
            if float(row['outdoor_temperature_c']) in {max(lower), min(upper)}:
                cells.append({key: row[key] for key in (
                    'source_id', 'mode', 'outdoor_temperature_c', 'supply_temperature_c',
                    'availability', 'thermal_capacity_kw', 'cop', 'derived_input_kw',
                    'evidence_status', 'source_pair_status', 'defrost_source_annotation')})
    return cells


def _capacity(model, grid, ta, supply):
    result = model.evaluate(ta, supply)
    point = result.point
    if point is None:
        if not result.status.startswith('Q /'):
            raise ValueError('unsupported manufacturer coordinate requires Q')
    else:
        if (point.source_ids != (wm50.SOURCE_ID,) or point.evidence_status != 'DER'
                or result.status != 'DER' or point.outdoor_temperature_c != ta
                or point.supply_temperature_c != supply):
            raise ValueError('manufacturer source/coordinate/evidence substitution')
        for name in ('thermal_capacity_kw', 'electrical_input_kw', 'cop', 'min_modulation_kw'):
            if number(getattr(point, name), name) <= 0:
                raise ValueError('positive source-condition capacity, power, COP and MIN required')
        if (point.min_modulation_kw > point.thermal_capacity_kw
                or not math.isclose(point.thermal_capacity_kw, point.electrical_input_kw * point.cop,
                                    rel_tol=0, abs_tol=1e-8)):
            raise ValueError('manufacturer Q/P/COP or MIN/MAX inconsistency')
    return dict(map_status=result.status, map_reason=result.reason,
                map_support_cells=_support_cells(grid, ta, supply),
                manufacturer_capacity_kw=point.thermal_capacity_kw if point else None,
                source_condition_input_kw=point.electrical_input_kw if point else None,
                source_condition_cop=point.cop if point else None,
                minimum_source_capacity_kw=point.min_modulation_kw if point else None)


def prescribed_state(row, p, hour_fraction):
    """The entire ideal path and its derivative, never an alternative state."""
    number(hour_fraction, 'within-hour fraction')
    if not 0 <= hour_fraction <= 1:
        raise ValueError('within-hour fraction required')
    ref = row['ideal']
    if ref['status'] != 'SCN':
        raise ValueError('known prescribed thermal state required')
    k = p['total_h_w_k'] / p['capacity_wh_k']
    transient = (ref['t_start_c'] - ref['equilibrium_c']) * math.exp(-k * hour_fraction)
    return ref['equilibrium_c'] + transient, -k * transient


def heat_to_follow_path(row, p, hour_fraction):
    t, derivative = prescribed_state(row, p, hour_fraction)
    return (p['capacity_wh_k'] * derivative + p['outdoor_h_w_k'] * (t - row['ta_observed_c'])
            + p['lower_boundary_h_w_k'] * (t - p['lower_boundary_temperature_c'])
            - p['internal_gain_w'] - row['solar_gain_scn_w'])


def _fixed_path(rows, p):
    """Reconstruct first-law heat on the common path; capacity cannot lower it."""
    output = []
    for index, row in enumerate(rows):
        start, end = _endpoint(row['interval_start_utc']), _endpoint(row['interval_end_utc'])
        if (end - start != timedelta(hours=1)
                or (index and start != _endpoint(rows[index - 1]['interval_end_utc']))):
            raise ValueError('fixed-path interval boundary/continuity mismatch')
        required_kw = None
        residual = None
        if row['ideal']['status'] == 'SCN':
            expected_start = p['initial_node_temperature_c'] if index == 0 else rows[index - 1]['ideal']['t_end_c']
            if (expected_start is None
                    or not math.isclose(row['ideal']['t_start_c'], expected_start, rel_tol=0, abs_tol=1e-9)
                    or not math.isclose(prescribed_state(row, p, 1)[0], row['ideal']['t_end_c'], rel_tol=0, abs_tol=1e-9)):
                raise ValueError('prescribed path endpoint/state continuity mismatch')
            samples = [heat_to_follow_path(row, p, x) for x in (0, .25, .5, .75, 1)]
            residual = max(abs(x - row['ideal']['command_heat_w']) for x in samples)
            if max(samples) - min(samples) > 1e-8 or residual > 1e-8:
                raise ValueError('same-service differential equation identity failed')
            if min(samples) < -1e-8:
                raise ValueError('heating-only path cannot silently add cooling')
            # Roundoff at exact heating-off hours only; never Q substitution.
            required_kw = max(0, samples[2]) / 1000
        capacity = row['manufacturer_capacity_kw']
        known = required_kw is not None and capacity is not None
        additional = max(0, required_kw - capacity) if known else None
        minimum = row['minimum_source_capacity_kw']
        branch = ('Q' if not known else
                  'ZERO_DEMAND' if required_kw <= 1e-12 else
                  'ABOVE_MAX' if additional > 1e-12 else
                  'BELOW_MIN' if minimum is not None and required_kw < minimum else
                  'BETWEEN_MIN_MAX')
        output.append(dict(
            interval_start_utc=row['interval_start_utc'], interval_end_utc=row['interval_end_utc'],
            prescribed_path='IDEAL_EXPONENTIAL_PATH_FROM_DECLARED_ENDPOINT_CONTROLLER',
            evidence_status='SCN' if known else 'Q', required_heat_kw=required_kw,
            required_heat_kwh=required_kw, source_rating_capacity_kw=capacity,
            source_supported=capacity is not None, thermal_path_supported=required_kw is not None,
            same_service_capacity_feasible=(additional <= 1e-12) if known else None,
            additional_thermal_requirement_kw=additional, additional_thermal_requirement_kwh=additional,
            capacity_covered_thermal_requirement_kwh=min(required_kw, capacity) if known else None,
            start_temperature_c=row['ideal'].get('t_start_c'), end_temperature_c=row['ideal']['t_end_c'],
            equilibrium_temperature_c=row['ideal'].get('equilibrium_c'),
            below_source_minimum_modulation=row['ideal'].get('below_minimum_modulation'),
            source_capacity_branch=branch,
            source_map_support_cells=row['map_support_cells'], max_path_equation_replay_residual_w=residual))
    known = [r for r in output if r['evidence_status'] == 'SCN']
    complete = len(known) == len(output)
    thermal_complete = all(r['thermal_path_supported'] for r in output)
    deficits = [r for r in known if r['additional_thermal_requirement_kw'] > 1e-12]
    return dict(
        scope='SCN_FIXED_PATH_CONDITIONAL_THERMAL_CAPACITY_FEASIBILITY',
        status='SCN_COMPLETE_CAPACITY_COMPARISON' if complete else 'Q_INCOMPLETE_CAPACITY_COMPARISON',
        full_prescribed_thermal_service_preserved=True if thermal_complete else None, alternative_temperature_state_evolved=False,
        same_service_capacity_feasible=not deficits if complete else None,
        required_thermal_energy_kwh=sum(r['required_heat_kwh'] for r in output) if thermal_complete else None,
        additional_thermal_requirement_kwh=sum(r['additional_thermal_requirement_kwh'] for r in known) if complete else None,
        peak_additional_thermal_requirement_kw=max((r['additional_thermal_requirement_kw'] for r in known), default=None) if complete else None,
        capacity_covered_thermal_requirement_kwh=sum(r['capacity_covered_thermal_requirement_kwh'] for r in known) if complete else None,
        capacity_deficit_hours=len(deficits) if complete else None,
        supported_capacity_deficit_hours=len(deficits), unknown_capacity_hours=sum(not r['source_supported'] for r in output),
        unknown_thermal_path_hours=sum(not r['thermal_path_supported'] for r in output),
        capacity_branch_hours={branch: sum(r['source_capacity_branch'] == branch for r in output)
                               for branch in ('ZERO_DEMAND', 'BELOW_MIN', 'BETWEEN_MIN_MAX', 'ABOVE_MAX', 'Q')},
        deficit_intervals=deficits, rows=output,
        backup_equipment=None, backup_electricity_kwh=None, selected_dispatch_policy=None,
        selected_additional_capacity_kw=None, actual_electricity_kwh=None, actual_spf=None,
        interpretation='Conditional additional thermal requirement, not equipment, dispatch, realized unmet energy, electricity or an efficiency saving')


def _summarize(rows, mode):
    known = [r[mode] for r in rows if r[mode]['status'] == 'SCN']
    complete = len(known) == len(rows)
    modulation_known = complete and all(x['below_minimum_modulation'] is not None for x in known)
    return dict(
        status='SCN_COMPLETE_DECLARED_MODEL' if complete else 'Q_INCOMPLETE_PERIOD',
        supported_hours=len(known), heat_kwh=sum(x['delivered_heat_kwh'] for x in known) if complete else None,
        supported_only_heat_kwh=sum(x['delivered_heat_kwh'] for x in known),
        min_node_temperature_c=min((x['t_end_c'] for x in known), default=None) if complete else None,
        max_heat_kw=max((x['delivered_heat_kwh'] for x in known), default=None) if complete else None,
        target_deficit_degree_hours=sum(x['target_deficit_degree_hours'] for x in known) if complete else None,
        capacity_clipped_hours=sum(x['capacity_clipped'] for x in known) if complete else None,
        below_minimum_modulation_hours=sum(bool(x['below_minimum_modulation']) for x in known) if modulation_known else None,
        supported_below_minimum_modulation_hours=sum(bool(x['below_minimum_modulation']) for x in known),
        max_energy_residual_wh=max((abs(x['energy_balance_residual_wh']) for x in known), default=None),
        total_storage_change_kwh=sum(x['storage_change_wh'] for x in known) / 1000 if complete else None,
        outdoor_exchange_kwh=sum(x['outdoor_loss_wh'] for x in known) / 1000 if complete else None,
        lower_boundary_exchange_kwh=sum(x['lower_boundary_loss_wh'] for x in known) / 1000 if complete else None,
        solar_gain_kwh=sum(x['solar_gain_kwh'] for x in known) if complete else None,
        internal_gain_kwh=sum(x['internal_gain_kwh'] for x in known) if complete else None)


def _simulate(weather, radiation_by_start, v, p, model, grid, timezone_name):
    """Private numerical seam; it makes no pin/canonical admission claim."""
    if not weather:
        raise ValueError('nonempty finite weather problem required')
    for index, row in enumerate(weather):
        if (row['end'] - row['start'] != timedelta(hours=1)
                or (index and row['start'] != weather[index - 1]['end'])):
            raise ValueError('unique contiguous one-hour physical intervals required')
    states = {'ideal': p['initial_node_temperature_c'], 'capacity_limited': p['initial_node_temperature_c']}
    rows = []
    for weather_row in weather:
        start, end, ta = weather_row['start'], weather_row['end'], weather_row['ta']
        local = start.astimezone(ZoneInfo(timezone_name))
        target = p['ideal_day_target_c'] if p['day_start_hour_local'] <= local.hour < p['day_end_hour_local'] else p['ideal_night_target_c']
        sr = radiation_by_start.get(start)
        row = dict(interval_start_utc=start.isoformat(), interval_end_utc=end.isoformat(),
                   source_endpoint=end.isoformat(), station_id=weather_row['station_id'],
                   weather_source_id=weather_row['source_id'], ta_observed_c=ta,
                   rh_endpoint_observed_pct=weather_row['rh'], target_scn_c=target,
                   sr_observed_j_cm2=sr, evidence_status='SCN',
                   **_capacity(model, grid, ta, p['supply_coordinate_c']))
        solar = None if sr is None else solar_gain(sr, start + timedelta(minutes=30), v, p)
        if solar is not None:
            row.update(solar)
        for mode in states:
            t0 = states[mode]
            capacity = row['manufacturer_capacity_kw']
            if solar is None or t0 is None or (mode == 'capacity_limited' and capacity is None):
                row[mode] = dict(status='Q', reason='MISSING_SOLAR_OR_PRIOR_STATE_OR_REQUIRED_CAPACITY',
                                 delivered_heat_kwh=None, t_start_c=t0, t_end_c=None,
                                 below_minimum_modulation=None)
                states[mode] = None
                continue
            gains = solar['solar_gain_scn_w'] + p['internal_gain_w']
            required = required_heat(t0, ta, gains, target, p)
            heat = required if mode == 'ideal' else min(required, capacity * 1000)
            step = transition(t0, ta, gains, heat, p)
            minimum = row['minimum_source_capacity_kw']
            row[mode] = dict(
                status='SCN', t_start_c=t0, **step, command_heat_w=required,
                delivered_heat_kwh=heat / 1000,
                capacity_clipped=(mode == 'capacity_limited' and heat < required - 1e-8),
                below_minimum_modulation=(0 < heat < minimum * 1000) if minimum is not None else None,
                target_deficit_degree_hours=deficit_degree_hours(t0, step, target, p),
                internal_gain_kwh=p['internal_gain_w'] / 1000, solar_gain_kwh=solar['solar_gain_scn_w'] / 1000)
            states[mode] = step['t_end_c']
        rows.append(row)
    return dict(rows=rows, summary={mode: _summarize(rows, mode) for mode in states},
                fixed_path=_fixed_path(rows, p),
                service_comparison_status='CLIPPED_BRANCH_REDUCES_SERVICE_NOT_AN_EFFICIENCY_COMPARISON',
                equal_service_heat_savings_kwh=None, actual_electricity_kwh=None, actual_spf=None)


def calculate_reference(*, radiation_path: Path | None = None, manifest_path: Path | None = None):
    """Read exact reviewed sources and solve the one named SCN, or fail closed.

    radiation_path is caller-owned external analytical material. The consumer
    verifies its bytes, columns, source, units and interval joins without copying
    or writing it. No supplied path produces explicit Q for thermal state/totals.
    A supplied missing/corrupt file raises; no private default path is embedded.
    The optional manifest path accepts only the exact reviewed bytes, not an
    override of scope, evidence, source identities, units or scenario parameters.
    """
    m = _load_manifest(MANIFEST_PATH if manifest_path is None else manifest_path)
    item = _source_building(m)
    p = _build_parameters(item, m)
    panel = _load_weather(m)
    weather = _select_weather(panel, m)
    radiation, radiation_status = _load_radiation(radiation_path, panel, m)
    model = wm50.load_wm50_reference('MAX', fixed_supply_c=p['supply_coordinate_c'])
    if model.equipment_id != f'{wm50.PRODUCT}:MAX:VOL5.3:FIXED_W55':
        raise ValueError('manufacturer product/mode substitution')
    result = _simulate(weather, radiation, item['values'], p, model, wm50.source_grid(), m['timezone'])
    result.update(
        case_id=CASE_ID, claim_scope=m['claim_scope'], evidence_status='SCN', evidence_tier=m['evidence_tier'],
        manifest_sha256=MANIFEST_SHA256, input_lineage=m['repository_pins'],
        radiation_input_status=radiation_status,
        verified_radiation_sha256=m['external_radiation']['sha256'] if radiation_path is not None else None,
        expected_radiation_sha256=m['external_radiation']['sha256'],
        source_rights_and_attribution=m['sources'], parameters=p,
        source_geometry_compatibility_flags=m['building']['geometry_warnings'],
        selection=m['weather'], scenario=m['scenario'], model_choices=m['model_choices'],
        excluded_source_fields=m['excluded_source_fields'], prohibited_promotions=m['prohibited_promotions'],
        service_contract=m['service_comparison'], hours=len(weather),
        start_utc=weather[0]['start'].isoformat(), end_utc=weather[-1]['end'].isoformat(),
        mean_ta_c=fmean(r['ta'] for r in weather), min_ta_c=min(r['ta'] for r in weather), max_ta_c=max(r['ta'] for r in weather),
        outside_manufacturer_domain_hours=sum(r['manufacturer_capacity_kw'] is None for r in result['rows']),
        missing_solar_hours=sum(r['sr_observed_j_cm2'] is None for r in result['rows']),
        actual_electricity_kwh=None, actual_spf=None, emitter_required_supply_c=None, dhw_kwh=None,
        auxiliary_electricity_kwh=None, cycling_electricity_kwh=None, defrost_electricity_kwh=None,
        actual_heat_pump_runtime_hours=None, auxiliary_runtime_hours=None, cycling_runtime_hours=None, defrost_runtime_hours=None,
        actual_service_validation='Q', population_weight=None, whole_slice_complete=False,
        seasonal_annual_heat_consumed=False, seasonal_ground_factor_consumed=False,
        empirical_model_validation=False, national_comfort_policy_selected=False)
    return result
