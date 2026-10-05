"""One annual E2 device reference and a temporal join to historical grid data.

IEE Projects TABULA + EPISCOPE (www.episcope.eu).
Adatbázis: Meteorológiai Adattár, HungaroMet Nonprofit Zrt.
The historical thermal total is preserved, not called observed 2025 heat.
This module reads external weather/source bytes and never writes a panel.
Private helpers are numeric/parser test seams, not alternate source admission.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from modules.B05 import hourly_power_component_reference as paired
from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B05.hourly_onoff_parameter_policy import (
    HEM_DEFAULT_SCENARIO, RADIATOR_OR_UFH_WET, evaluate_hourly_onoff_with_policy,
)
from modules.B06 import tabula_seasonal_reference as tabula
from modules.B08 import historical_source_balance as historical

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b05_annual_device_reference_manifest.json'
MANIFEST_SHA256 = 'd4f53d6b8c60633723875d3cc815b40d29edd0d4f737535de3d88324cd810b15'
UTC = timezone.utc
HOUR = timedelta(hours=1)
QUARTER = timedelta(minutes=15)


def _number(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or (value <= 0 if positive else value < 0)):
        raise ValueError('finite ' + ('positive ' if positive else 'nonnegative ') + name + ' required')
    return value


def _manifest():
    raw = MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed annual method manifest mismatch')
    data = json.loads(raw)
    for name, digest in data['repository_pins'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('reviewed repository input changed: ' + name)
    if data['heat_pump']['product'] != wm50.PRODUCT:
        raise ValueError('product identity mismatch')
    return data


def _endpoint(value):
    if not isinstance(value, str):
        raise ValueError('explicit UTC interval required')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0) or dt.minute or dt.second or dt.microsecond:
        raise ValueError('whole-hour UTC interval required')
    return dt


def _weather_rows(rows, contract):
    rows = list(rows)
    start, end = _endpoint(contract['start_utc']), _endpoint(contract['end_utc'])
    if len(rows) != contract['rows'] or end - start != len(rows) * HOUR:
        raise ValueError('complete annual physical weather coverage required')
    result = []
    for i, row in enumerate(rows):
        a, b = _endpoint(row['interval_start_utc']), _endpoint(row['source_endpoint_utc'])
        if a != start + i * HOUR or b != a + HOUR:
            raise ValueError('weather gap, duplicate or interval shift')
        expected_source = (contract['recent_source_id'] if b == _endpoint(contract['recent_endpoint_utc'])
                           else contract['history_source_id'])
        if row['station_id'] != contract['station_id'] or row['source_id'] != expected_source:
            raise ValueError('weather station or source identity mismatch')
        if not isinstance(row['ta_C'], str) or row['ta_C'].strip() in ('', '-999'):
            raise ValueError('required temperature is unknown')
        ta = float(row['ta_C'])
        if not math.isfinite(ta) or ta == -999:
            raise ValueError('finite source temperature required')
        result.append(dict(start=a, end=b, ta_c=ta, source_id=expected_source))
    return result


def _weather(path, contract):
    raw = Path(path).read_bytes()
    if len(raw) != contract['bytes'] or hashlib.sha256(raw).hexdigest() != contract['sha256']:
        raise ValueError('reviewed external weather bytes mismatch')
    return _weather_rows(csv.DictReader(io.StringIO(raw.decode('utf-8'))), contract)


def _thermal(manifest):
    spec = manifest['thermal']
    source = tabula.source_package()
    matches = [r for r in source['rows'] if r['values']['Code_BuildingVariant'] == spec['variant_id']]
    if len(matches) != 1 or source['source_sha256'] != spec['system_source_sha256']:
        raise ValueError('exact thermal source identity required')
    native_row = matches[0]['values']
    if native_row['A_C_Ref'] != spec['area_m2']:
        raise ValueError('source area changed')
    native = tabula.calculate_reference(spec['variant_id'], service='source')
    useful = _number(native['annual_heat_kwh'], 'native useful heat', positive=True)
    distribution = spec['effective_distribution_kwh_m2'] * spec['area_m2']
    generator = spec['source_generator_kwh_m2'] * spec['area_m2']
    if spec['storage_kwh_m2'] != 0 or not math.isclose(useful + distribution, generator, rel_tol=1e-12):
        raise ValueError('native useful/distribution/generator closure failed')
    h_eff = spec['area_m2'] * (native['h_transmission'] + native['h_ventilation']) * native['nonuniform_heating_factor'] / 1000
    balance = native_row['Theta_e'] + useful / (24 * native_row['HeatingDays'] * h_eff)
    return dict(useful_heat_kwh=useful, effective_distribution_heat_kwh=distribution,
                generator_heat_kwh=generator, effective_loss_kw_k=h_eff,
                balance_temperature_c=balance, variant_id=spec['variant_id'],
                annual_authority='HISTORICAL_TABULA_SOURCE_REFERENCE_NOT_OBSERVED_2025_DEMAND')


def _hour(q_kw, points, hp):
    """Declared equivalent minimum stage; all powers are unit-rating inputs."""
    _number(q_kw, 'generator requirement')
    idle_kw = _number(hp['nonactive_power_kw'], 'declared nonactive power')
    row = dict(branch='ZERO_HEAT', status='DER', generator_heat_required_kwh=q_kw,
               generator_heat_served_kwh=0.0, unserved_heat_kwh=0.0,
               stage_on_fraction=0.0, active_rating_kwh=0.0, inertia_kwh=0.0,
               idle_kwh=idle_kw, device_reference_electricity_kwh=idle_kw,
               source_modes=[], source_cells=[], source_defrost_labels=[],
               mixed_defrost_annotations=False, min_capacity_margin_kw=None,
               whole_installed_system_electricity_kwh=None)
    if q_kw == 0:
        return row
    ordered, reason = paired._ordered(points)
    if ordered is None:
        row.update(branch='Q_SOURCE_SUPPORT', status='Q', reason=reason,
                   generator_heat_served_kwh=None, unserved_heat_kwh=None,
                   stage_on_fraction=None, active_rating_kwh=None, inertia_kwh=None,
                   idle_kwh=None, device_reference_electricity_kwh=None)
        return row
    low, high = ordered[0], ordered[-1]
    row['min_capacity_margin_kw'] = high['q_kw'] - q_kw
    if q_kw < low['q_kw']:
        duty = q_kw / low['q_kw']
        inertia = evaluate_hourly_onoff_with_policy(
            minimum_continuous_compressor_power_kw=low['p_kw'], load_ratio=duty,
            minimum_continuous_load_ratio=1.0, emitter_class=RADIATOR_OR_UFH_WET,
            policy=HEM_DEFAULT_SCENARIO)
        if (inertia.onoff_inertia_power_kw is None or inertia.tau_eq_s != hp['tau_eq_s']
                or inertia.emitter_response_time_s != hp['emitter_response_s']):
            raise ValueError('qualified fixed-stage default method changed')
        active = duty * low['p_kw']
        idle = idle_kw * (1 - duty)
        row.update(branch='MINIMUM_STAGE_ONOFF_E2_TRANSFER', stage_on_fraction=duty,
                   active_rating_kwh=active, inertia_kwh=inertia.onoff_inertia_power_kw,
                   idle_kwh=idle, device_reference_electricity_kwh=active + inertia.onoff_inertia_power_kw + idle,
                   generator_heat_served_kwh=q_kw, source_modes=low['modes'], source_cells=low['source_cells'])
    elif q_kw > high['q_kw']:
        row.update(branch='ABOVE_MAX_COMPONENT_ONLY', generator_heat_served_kwh=high['q_kw'],
                   unserved_heat_kwh=q_kw - high['q_kw'], stage_on_fraction=1.0,
                   active_rating_kwh=high['p_kw'], idle_kwh=0.0,
                   device_reference_electricity_kwh=high['p_kw'],
                   source_modes=high['modes'], source_cells=high['source_cells'])
    else:
        power, reason = paired._interpolate(q_kw, points)
        if power is None:
            raise ValueError('ordered continuous source interpolation failed: ' + reason)
        row.update(branch='PAIRED_POWER_CONTINUOUS', generator_heat_served_kwh=q_kw,
                   stage_on_fraction=1.0, active_rating_kwh=power['input_kw'], idle_kwh=0.0,
                   device_reference_electricity_kwh=power['input_kw'],
                   source_modes=power['support_modes'], source_cells=power['source_cells'])
    labels = sorted({c['defrost_source_annotation'] for c in row['source_cells']})
    row.update(source_defrost_labels=labels, mixed_defrost_annotations=len(labels) > 1)
    if not math.isclose(row['active_rating_kwh'] + row['inertia_kwh'] + row['idle_kwh'],
                        row['device_reference_electricity_kwh'], rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError('electrical component closure failed')
    if not math.isclose(row['generator_heat_served_kwh'] + row['unserved_heat_kwh'], q_kw,
                        rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError('served/unserved heat closure failed')
    return row


def _calculate(weather, thermal, hp, models, grid):
    weights = [max(thermal['balance_temperature_c'] - r['ta_c'], 0.0) for r in weather]
    degree_hours = math.fsum(weights)
    if degree_hours <= 0:
        raise ValueError('nonzero heating exposure required for this annual thermal allocation')
    rows, cache = [], {}
    for w, weight in zip(weather, weights):
        useful = thermal['useful_heat_kwh'] * weight / degree_hours
        distribution = thermal['effective_distribution_heat_kwh'] * weight / degree_hours
        q = useful + distribution
        if q > 0 and w['ta_c'] not in cache:
            cache[w['ta_c']] = paired._points(models, grid, w['ta_c'])
        row = _hour(q, cache[w['ta_c']] if q > 0 else None, hp)
        row.update(interval_start_utc=w['start'].isoformat(), interval_end_utc=w['end'].isoformat(),
                   duration_h=1.0, observed_ta_c=w['ta_c'], weather_source_id=w['source_id'],
                   useful_heat_kwh=useful, effective_distribution_heat_kwh=distribution,
                   evidence_status='DER', evidence_tier='E2')
        rows.append(row)
    known = [r for r in rows if r['status'] != 'Q']
    complete = len(known) == len(rows)
    served = math.fsum(r['generator_heat_served_kwh'] for r in known)
    unserved = math.fsum(r['unserved_heat_kwh'] for r in known)
    full_service = complete and unserved == 0
    terms = {k: math.fsum(r[k] for r in known) for k in ('active_rating_kwh', 'inertia_kwh', 'idle_kwh', 'device_reference_electricity_kwh')}
    if not math.isclose(math.fsum(r['useful_heat_kwh'] for r in rows), thermal['useful_heat_kwh'], rel_tol=1e-12):
        raise ValueError('annual thermal allocation failed')
    summary = dict(hours=len(rows), branch_hours=dict(Counter(r['branch'] for r in rows)),
                   unknown_hours=len(rows) - len(known), source_capacity_shortfall_kwh=unserved if complete else None,
                   known_served_heat_kwh=served, complete_generator_service=full_service,
                   known_device_components=terms,
                   annual_device_reference_electricity_kwh=terms['device_reference_electricity_kwh'] if full_service else None,
                   peak_device_hour_mean_kw=max(r['device_reference_electricity_kwh'] for r in known) if full_service else None,
                   generator_heat_to_device_reference_input_ratio=thermal['generator_heat_kwh'] / terms['device_reference_electricity_kwh'] if full_service else None,
                   mixed_defrost_support_hours=sum(r['mixed_defrost_annotations'] for r in known),
                   shape_degree_hours=degree_hours,
                   annual_preservation_multiplier=thermal['useful_heat_kwh'] / (thermal['effective_loss_kw_k'] * degree_hours),
                   whole_installed_system_electricity_kwh=None, physical_spf=None,
                   national_increment_kwh=None, subhourly_peak_kw=None)
    return rows, summary


def calculate_reference(*, weather_path: Path):
    """Calculate only the pinned UTC2025 archetype/device E2 reference."""
    manifest = _manifest()
    weather = _weather(weather_path, manifest['weather'])
    thermal = _thermal(manifest)
    models = {mode: wm50.load_wm50_reference(mode, fixed_supply_c=55) for mode in paired.MODES}
    rows, summary = _calculate(weather, thermal, manifest['heat_pump'], models, wm50.source_grid())
    return dict(reference_id=manifest['reference_id'], evidence_status='DER', evidence_tier='E2',
                scope=manifest['scope'], thermal_reference=thermal, rows=rows, summary=summary,
                validation_debt=manifest['validation_debt'], limits=manifest['limits'],
                national_admission=False, whole_slice_complete=False)


def _quarters(rows):
    for row in rows:
        if row['status'] != 'DER' or row['unserved_heat_kwh'] != 0:
            raise ValueError('complete same-service device profile required for temporal comparison')
        start, end = _endpoint(row['interval_start_utc']), _endpoint(row['interval_end_utc'])
        if end - start != HOUR or row['duration_h'] != 1.0:
            raise ValueError('hourly physical interval required')
        _number(row['device_reference_electricity_kwh'], 'hourly device energy')
        kw = Decimal(str(row['device_reference_electricity_kwh']))
        for i in range(4):
            a = start + i * QUARTER
            yield a, a + QUARTER, kw


def compare_historical_reference(*, weather_path: Path, source_paths, handoff_paths):
    """Fully validate and compare timing; never add a programme to observed load.

The original B08/B09 producer owns source acquisition/lineage validation. The
device profile supplies no household weight, B01 status, stock subtraction,
dispatch or import claim. Raw sources and all panels remain external-only.
"""
    result = calculate_reference(weather_path=weather_path)
    if not result['summary']['complete_generator_service']:
        raise ValueError('complete annual reference required for historical timing comparison')
    quarters = iter(_quarters(result['rows']))
    count = 0
    energy = Decimal(0)
    peak_load = None
    peak_rows = []

    def checked_rows():
        nonlocal count, energy, peak_load, peak_rows
        for row in historical.iter_historical_source_balance(source_paths, handoff_paths):
            q = next(quarters, None)
            if q is None or q[:2] != (row.start_utc, row.end_utc):
                raise ValueError('historical/reference physical interval mismatch')
            count += 1
            energy += q[2] / 4
            sample = dict(start_utc=row.start_utc.isoformat(), reference_device_hour_mean_kw=str(q[2]),
                          historical_actual_load_mw=str(row.actual_load_mw),
                          historical_source_reference_residual_mw=str(row.source_reference_residual_mw))
            if peak_load is None or row.actual_load_mw > peak_load:
                peak_load, peak_rows = row.actual_load_mw, [sample]
            elif row.actual_load_mw == peak_load:
                peak_rows.append(sample)
            yield row
        if next(quarters, None) is not None or count != 35040:
            raise ValueError('incomplete or extra historical/reference quarters')

    # Reuse the existing conservation and source-cell/recovery accounting.
    source_summary = historical._summarize(checked_rows())
    if not math.isclose(float(energy), result['summary']['annual_device_reference_electricity_kwh'], rel_tol=1e-12):
        raise ValueError('quarter-hour allocation changed device energy')
    return dict(reference_id=result['reference_id'], evidence_status='DER', evidence_tier='E2',
                scope='HISTORICAL_TIMING_COMPARISON_ONLY', intervals=count,
                reference_device_energy_kwh=str(energy), reference_summary=result['summary'],
                historical_summary=source_summary, coincident_source_load_peak=peak_rows,
                allocation='Hourly mean held across four physical quarters; not measured switching or subhourly peak',
                programme_adjusted_load=None, national_increment=None, existing_heatpump_stock_removed=False,
                source_republication_permission=False, whole_household_savings=None)
