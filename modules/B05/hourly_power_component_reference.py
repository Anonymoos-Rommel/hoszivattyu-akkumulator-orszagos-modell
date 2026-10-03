"""One paired-map electrical component SCN on the pinned B06 thermal path.

Source-rating arithmetic only. This never returns complete-period electricity,
SPF, installed runtime or a complete load for financial/network consumers.
The public entry point reads the existing admitted case itself; private helpers
are numeric test seams, not alternative source-admission interfaces.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta
from pathlib import Path

from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B06 import hourly_thermal_reference as thermal

CASE_ID = 'SCN-WM50-W55-PAIRED-MAP-COMPONENT-001'
THERMAL_API_SHA256 = '80d5879145a7574e91952f9407c972cb6fc4799c62f83aa033e052068ded17df'
MODES = ('MIN', 'MID', 'NOMINAL', 'MAX')
SUPPLY_C = 55.0
LIMITS = (
    'Paired-power interpolation is an explicit SCN, not a manufacturer control rule',
    'Mixed defrost annotations describe source support, not weather-realized defrost',
    'Below-MIN cycling and zero-load auxiliaries remain unknown',
    'MAX-only input does not supply the additional thermal requirement',
    'Rating input does not identify installed pumps, emitter fans or mode durations',
    'No complete B08/B12 load, empirical validation, slice acceptance or readiness uplift',
)


def _number(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or (value <= 0 if positive else value < 0)):
        raise ValueError('finite ' + ('positive ' if positive else 'nonnegative ') + name + ' required')
    return value


def _cells(grid, mode, ta):
    column = [r for r in grid if r['mode'] == mode and float(r['supply_temperature_c']) == SUPPLY_C]
    lower = [float(r['outdoor_temperature_c']) for r in column if float(r['outdoor_temperature_c']) <= ta]
    upper = [float(r['outdoor_temperature_c']) for r in column if float(r['outdoor_temperature_c']) >= ta]
    if not lower or not upper:
        return []
    selected = [r for r in column if float(r['outdoor_temperature_c']) in {max(lower), min(upper)}]
    return [{k: r[k] for k in ('source_id', 'mode', 'outdoor_temperature_c', 'supply_temperature_c',
                              'availability', 'thermal_capacity_kw', 'cop', 'derived_input_kw',
                              'evidence_status', 'source_pair_status', 'defrost_source_annotation')}
            for r in selected]


def _points(models, grid, ta):
    points = []
    for mode in MODES:
        model = models[mode]
        if model.equipment_id != f'{wm50.PRODUCT}:{mode}:VOL5.3:FIXED_W55':
            raise ValueError('source product/mode substitution')
        result = model.evaluate(ta, SUPPLY_C)
        cells = _cells(grid, mode, ta)
        if result.point is None:
            if not result.status.startswith('Q /'):
                raise ValueError('missing manufacturer point requires Q')
            points.append(dict(mode=mode, status='Q', reason=result.reason, source_cells=cells))
            continue
        p = result.point
        if (result.status != 'DER' or p.evidence_status != 'DER'
                or p.source_ids != (wm50.SOURCE_ID,)
                or p.outdoor_temperature_c != ta or p.supply_temperature_c != SUPPLY_C
                or not cells or any(c['availability'] != 'PRESENT' for c in cells)):
            raise ValueError('source point identity, evidence or support mismatch')
        q = _number(p.thermal_capacity_kw, 'rated heat', positive=True)
        pel = _number(p.electrical_input_kw, 'rated input', positive=True)
        cop = _number(p.cop, 'rated COP', positive=True)
        if not math.isclose(q, pel * cop, rel_tol=1e-12, abs_tol=1e-10):
            raise ValueError('source Q/P/COP identity mismatch')
        points.append(dict(mode=mode, status='DER', q_kw=q, p_kw=pel, cop=cop,
                           interpolation=p.interpolation, source_cells=cells))
    return points


def _ordered(points):
    """Keep frequency order; never sort around reversed or conflicting supports."""
    if tuple(p['mode'] for p in points) != MODES:
        raise ValueError('four explicit frequency modes required')
    if any(p['status'] == 'Q' for p in points):
        return None, 'Q_MISSING_MODE_SUPPORT'
    output = []
    for p in points:
        _number(p['q_kw'], 'mode heat', positive=True)
        _number(p['p_kw'], 'mode input', positive=True)
        if output and p['q_kw'] < output[-1]['q_kw']:
            return None, 'Q_REVERSED_MODE_CAPACITY'
        if output and p['q_kw'] == output[-1]['q_kw']:
            if p['p_kw'] != output[-1]['p_kw']:
                return None, 'Q_CONFLICTING_EQUAL_CAPACITY'
            output[-1]['modes'].append(p['mode'])
            output[-1]['source_cells'].extend(p['source_cells'])
        else:
            output.append(dict(q_kw=p['q_kw'], p_kw=p['p_kw'], modes=[p['mode']],
                               source_cells=list(p['source_cells'])))
    return output, None


def _interpolate(q, points):
    _number(q, 'required heat', positive=True)
    ordered, reason = _ordered(points)
    if ordered is None:
        return None, reason
    if q < ordered[0]['q_kw'] or q > ordered[-1]['q_kw']:
        return None, 'Q_OUTSIDE_CONTINUOUS_RANGE'
    exact = next((p for p in ordered if q == p['q_kw']), None)
    if exact is not None:
        return dict(input_kw=exact['p_kw'], cop=q / exact['p_kw'], weight=0.0,
                    support_modes=exact['modes'], source_cells=exact['source_cells']), None
    a, b = next((a, b) for a, b in zip(ordered, ordered[1:]) if a['q_kw'] < q < b['q_kw'])
    weight = (q - a['q_kw']) / (b['q_kw'] - a['q_kw'])
    pel = a['p_kw'] + weight * (b['p_kw'] - a['p_kw'])
    return dict(input_kw=pel, cop=q / pel, weight=weight,
                support_modes=a['modes'] + b['modes'], source_cells=a['source_cells'] + b['source_cells']), None


def _component(kind, heat_kw, input_kw, hours, cells, modes, weight=None):
    labels = sorted({c['defrost_source_annotation'] for c in cells})
    return dict(kind=kind, evidence_status='SCN', heat_kw=heat_kw, heat_kwh=heat_kw * hours,
                rating_input_kw=input_kw, rating_input_kwh=input_kw * hours,
                derived_cop=heat_kw / input_kw, source_cells=cells, support_modes=modes,
                load_weight=weight, source_defrost_labels=labels,
                mixed_defrost_annotations=len(labels) > 1,
                physical_weather_electricity_kwh=None, installed_runtime_hours=None)


def _row(row, fixed, models, grid):
    if any(row[k] != fixed[k] for k in ('interval_start_utc', 'interval_end_utc')):
        raise ValueError('thermal/component interval mismatch')
    start, end = (datetime.fromisoformat(row[k]) for k in ('interval_start_utc', 'interval_end_utc'))
    if (start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0)
            or end - start != timedelta(hours=1)):
        raise ValueError('pinned physical UTC hour required')
    q = fixed['required_heat_kw']
    if q is not None:
        _number(q, 'required heat')
    branch = fixed['source_capacity_branch']
    result = dict(interval_start_utc=row['interval_start_utc'], interval_end_utc=row['interval_end_utc'],
                  duration_h=1.0, required_heat_kw=q, required_heat_kwh=q,
                  thermal_capacity_branch=branch, component=None, component_status='Q',
                  reason='Q_THERMAL_PATH_OR_MAP', actual_electricity_kwh=None,
                  whole_service_electricity_kwh=None,
                  additional_thermal_requirement_kwh=fixed['additional_thermal_requirement_kwh'])
    if q is None:
        return result
    if branch == 'ZERO_DEMAND':
        result['reason'] = 'Q_ZERO_LOAD_AUXILIARIES'
        return result
    if branch == 'BELOW_MIN':
        result['reason'] = 'Q_CYCLING_METHOD_AND_RUNTIME'
        return result
    if branch == 'Q':
        return result
    points = _points(models, grid, row['ta_observed_c'])
    result['source_mode_points'] = points
    if branch == 'BETWEEN_MIN_MAX':
        power, reason = _interpolate(q, points)
        if power is None:
            result['reason'] = reason
            return result
        component = _component('CONTINUOUS_PAIRED_POWER_REFERENCE', q, power['input_kw'], 1.0,
                               power['source_cells'], power['support_modes'], power['weight'])
    elif branch == 'ABOVE_MAX':
        maximum = points[-1]
        if maximum['status'] == 'Q':
            result['reason'] = 'Q_MAXIMUM_SOURCE_SUPPORT'
            return result
        if not math.isclose(maximum['q_kw'], fixed['source_rating_capacity_kw'], rel_tol=0, abs_tol=1e-10):
            raise ValueError('thermal and electrical MAX references disagree')
        if q <= maximum['q_kw']:
            raise ValueError('overload branch requires additional thermal demand')
        component = _component('FULL_MAX_COMPONENT_ONLY', maximum['q_kw'], maximum['p_kw'], 1.0,
                               maximum['source_cells'], ['MAX'])
    else:
        raise ValueError('unknown thermal capacity branch')
    result.update(component=component, component_status='SCN', reason=None)
    return result


def _summary(rows, kind):
    selected = [r for r in rows if r['component'] is not None and r['component']['kind'] == kind]
    return dict(scope=kind, evidence_status='SCN' if selected else 'Q',
                supported_duration_h=sum(r['duration_h'] for r in selected),
                supported_interval_starts=[r['interval_start_utc'] for r in selected],
                supported_component_heat_kwh=sum(r['component']['heat_kwh'] for r in selected) if selected else None,
                supported_component_rating_input_kwh=sum(r['component']['rating_input_kwh'] for r in selected) if selected else None,
                mixed_defrost_annotation_hours=sum(r['duration_h'] for r in selected if r['component']['mixed_defrost_annotations']),
                complete_period_electricity_kwh=None)


def _coverage(rows):
    result = {}
    for branch in ('BETWEEN_MIN_MAX', 'ABOVE_MAX', 'BELOW_MIN', 'ZERO_DEMAND', 'Q'):
        subset = [r for r in rows if r['thermal_capacity_branch'] == branch]
        known = all(r['required_heat_kwh'] is not None for r in subset)
        result[branch] = dict(duration_h=sum(r['duration_h'] for r in subset),
                              required_heat_kwh=sum(r['required_heat_kwh'] for r in subset) if known else None,
                              missing_component_hours=sum(r['component'] is None for r in subset),
                              whole_service_electricity_kwh=None)
    return result


def calculate_reference(*, radiation_path: Path | None = None):
    """Read the single pinned thermal case and return labelled component subsets.

Missing external radiation propagates Q. A supplied file must pass the existing
thermal source/hash/interval checks. No alternate path, source, case or control
is accepted, and no file is written. No complete electrical total is exposed.
"""
    if hashlib.sha256(Path(thermal.__file__).read_bytes()).hexdigest() != THERMAL_API_SHA256:
        raise ValueError('reviewed thermal API changed; component admission requires review')
    base = thermal.calculate_reference(radiation_path=radiation_path)
    if (base['case_id'] != thermal.CASE_ID or base['manifest_sha256'] != thermal.MANIFEST_SHA256
            or base['evidence_status'] != 'SCN' or base['parameters']['supply_coordinate_c'] != SUPPLY_C
            or len(base['rows']) != 72 or len(base['fixed_path']['rows']) != 72):
        raise ValueError('exact pinned thermal case required')
    models = {mode: wm50.load_wm50_reference(mode, fixed_supply_c=SUPPLY_C) for mode in MODES}
    grid = wm50.source_grid()
    rows = [_row(row, fixed, models, grid) for row, fixed in zip(base['rows'], base['fixed_path']['rows'])]
    return dict(case_id=CASE_ID, evidence_status='SCN', claim_scope='PARTIAL_SOURCE_RATING_COMPONENTS',
                thermal_case_id=base['case_id'], thermal_manifest_sha256=base['manifest_sha256'],
                thermal_api_sha256=THERMAL_API_SHA256, thermal_reference=base, rows=rows,
                continuous_component=_summary(rows, 'CONTINUOUS_PAIRED_POWER_REFERENCE'),
                overload_max_component=_summary(rows, 'FULL_MAX_COMPONENT_ONLY'),
                thermal_branch_coverage=_coverage(rows),
                unknown_electrical_hours=sum(r['component'] is None for r in rows),
                whole_service_incomplete_hours=72,
                whole_period_rating_input_kwh=None, actual_electricity_kwh=None, actual_spf=None,
                cycling_electricity_kwh=None, auxiliary_electricity_kwh=None,
                weather_specific_defrost_electricity_kwh=None, backup_electricity_kwh=None,
                payback=None, complete_load_for_B08_or_B12=False, empirical_validation=False,
                whole_slice_complete=False, national_claim=False, limitations=LIMITS)
