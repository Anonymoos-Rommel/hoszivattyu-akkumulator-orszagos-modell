"""Three historical source envelopes on one unchanged finite thermal SCN path.

Only calculate_reference admits the pinned source/case. Private functions are
numeric test seams. No annual, electrical, financial or empirical result follows.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from modules.B06 import hourly_thermal_reference as hourly

CASE_ID = 'SCN-TABULA-SFH01-COMMON-PATH-ENVELOPES-001'
THERMAL_API_SHA256 = '80d5879145a7574e91952f9407c972cb6fc4799c62f83aa033e052068ded17df'
VARIANTS = tuple(f'HU.N.SFH.01.Bel80.ReEx.001.01{i}' for i in (1, 2, 3))
ROWS = (1239, 1240, 1241)
ZERO_TOLERANCE_W = 1e-8
COMMON = ('A_C_Ref', 'h_room', 'c_m', 'phi_int', 'n_air_use', 'F_sh_hor', 'F_sh_vert', 'F_f', 'F_w')
COMMON += tuple(prefix + c for c in hourly.PARTS for prefix in ('A_Calc_', 'U_'))
COMMON += tuple('R_Add_UnheatedSpace_' + c for c in hourly.OPAQUE)
COMMON += tuple('A_Calc_Window_' + d for d in ('North', 'East', 'South', 'West', 'Horizontal'))


def _finite(value, name, *, positive=False, nonnegative=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            or (positive and value <= 0) or (nonnegative and value < 0)):
        raise ValueError('finite valid ' + name + ' required')
    return value


def _primitive(a, b, k, t):
    return a*t - b*math.expm1(-k*t)/k


def _curve(a, b, k, hours=1.0, capacity_kw=None):
    """Analytic heating demand and positive excess; exact equality has no excess."""
    for value, name in ((a, 'constant power'), (b, 'transient power')):
        _finite(value, name)
    _finite(k, 'decay', positive=True)
    _finite(hours, 'duration', positive=True)
    q0, q1 = a+b, a+b*math.exp(-k*hours)
    _finite(q0, 'initial demand'); _finite(q1, 'terminal demand')
    if min(q0, q1) < -ZERO_TOLERANCE_W:
        raise ValueError('cooling requirement cannot be clipped into heating service')
    heat = _primitive(a,b,k,hours)/1000
    _finite(heat, 'integrated heat')
    if heat < -ZERO_TOLERANCE_W*hours/1000:
        raise ValueError('negative heating integral')
    result = dict(curve_a_w=a, curve_b_w=b, decay_per_hour=k,
                  heat_start_kw=max(0.,q0)/1000, heat_end_kw=max(0.,q1)/1000,
                  required_heat_kwh=max(0.,heat), peak_required_kw=max(0.,q0,q1)/1000,
                  source_capacity_kw=capacity_kw, additional_thermal_kwh=None,
                  peak_additional_kw=None, over_capacity_duration_h=None,
                  capacity_crossing_hour_fraction=None, capacity_comparison_status='Q')
    if capacity_kw is None:
        return result
    _finite(capacity_kw, 'source capacity', positive=True)
    _finite(capacity_kw*1000, 'source capacity in watts', positive=True)
    offset = a-capacity_kw*1000
    g0, g1 = offset+b, offset+b*math.exp(-k*hours)
    # Nonpositive first: an exactly equal, constant demand has zero excess time.
    if max(g0,g1) <= 0:
        extra, duration, root = 0., 0., None
    elif min(g0,g1) >= 0:
        extra, duration, root = _primitive(offset,b,k,hours), hours, None
    else:
        root = -math.log(-offset/b)/k
        if not 0 < root < hours:
            raise ValueError('capacity crossing outside physical interval')
        if g0 > 0:
            extra, duration = _primitive(offset,b,k,root), root
        else:
            extra = _primitive(offset,b,k,hours)-_primitive(offset,b,k,root)
            duration = hours-root
    _finite(extra, 'integrated capacity excess')
    result.update(additional_thermal_kwh=max(0.,extra)/1000,
                  peak_additional_kw=max(0.,g0,g1)/1000,
                  over_capacity_duration_h=duration,
                  capacity_crossing_hour_fraction=root/hours if root is not None else None,
                  capacity_comparison_status='SCN')
    return result


def _source_items(base, manifest):
    pin = manifest['repository_pins']['building']
    raw = (hourly.ROOT / pin['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('reviewed source-building extract hash mismatch')
    package = json.loads(raw)
    if (package['source_id'] != manifest['building']['source_id']
            or package['source_sha256'] != manifest['building']['source_sha256']):
        raise ValueError('source-building identity mismatch')
    items = []
    for variant, source_row in zip(VARIANTS, ROWS):
        matches = [x for x in package['rows'] if x['values']['Code_BuildingVariant'] == variant]
        if len(matches) != 1 or matches[0]['source_row'] != source_row:
            raise ValueError('exact unique source envelope state required')
        items.append(matches[0])
    if any(len({x['values'][c] for x in items}) != 1 for c in COMMON):
        raise ValueError('common source geometry/construction/service controls changed')
    if any(items[0]['values'][prefix+c] != 0 for c in hourly.PARTS for prefix in ('f_Measure_', 'R_Measure_')):
        raise ValueError('existing state must have zero retrofit fractions and R_Measure')
    if base['parameters']['source_variant'] != VARIANTS[-1]:
        raise ValueError('common trajectory must remain the ambitious reference')
    return items, package


def _parameters(item, manifest):
    # Reuse pinned assembly arithmetic, but qualify each source state here.
    p = hourly._build_parameters(item, manifest)
    v = item['values']
    if v['A_Calc_Window_2'] != 0 or v['A_Calc_Window_1'] <= 0:
        raise ValueError('this comparison requires its single populated glazing type')
    g = v['g_gl_n_Measure_Window_1'] if v['Code_Measure_Window_1'] else v['g_gl_n_Window_1']
    if not 0 < _finite(g, 'solar transmittance', positive=True) <= 1:
        raise ValueError('bounded solar transmittance required')
    p['glazing_transmittance'] = g
    return p


def _record(row, fixed, reference_p, p, reference_g):
    if any(row[k] != fixed[k] for k in ('interval_start_utc','interval_end_utc')):
        raise ValueError('common physical interval mismatch')
    start, end = (hourly._endpoint(row[k]) for k in ('interval_start_utc','interval_end_utc'))
    hours = (end-start).total_seconds()/3600
    if hours != 1:
        raise ValueError('the pinned comparison requires physical one-hour intervals')
    result = dict(interval_start_utc=row['interval_start_utc'], interval_end_utc=row['interval_end_utc'],
                  duration_h=hours, evidence_status='Q', reason='Q_PRESCRIBED_THERMAL_PATH',
                  required_heat_kwh=None, peak_required_kw=None, additional_thermal_kwh=None,
                  peak_additional_kw=None, over_capacity_duration_h=None,
                  capacity_crossing_hour_fraction=None, capacity_comparison_status='Q',
                  source_capacity_kw=fixed['source_rating_capacity_kw'],
                  actual_electricity_kwh=None)
    if row['ideal']['status'] == 'Q':
        return result
    if row['ideal']['status'] != 'SCN':
        raise ValueError('known prescribed path must retain SCN status')
    eq = row['ideal']['equilibrium_c']
    delta = row['ideal']['t_start_c']-eq
    k = reference_p['total_h_w_k']/reference_p['capacity_wh_k']
    # The exact cases share orientation/areas/shading. Only glazing g changes.
    solar = row['solar_gain_scn_w']*p['glazing_transmittance']/reference_g
    forcing = (p['outdoor_h_w_k']*row['ta_observed_c']
               + p['lower_boundary_h_w_k']*reference_p['lower_boundary_temperature_c']
               + p['internal_gain_w']+solar)
    a = p['total_h_w_k']*eq-forcing
    b = (p['total_h_w_k']-p['capacity_wh_k']*k)*delta
    curve = _curve(a,b,k,hours,fixed['source_rating_capacity_kw'])
    residual = 0.
    for t in (0., .25, .5, .75, 1.):
        temp, derivative = hourly.prescribed_state(row,reference_p,t)
        direct = (p['capacity_wh_k']*derivative+p['outdoor_h_w_k']*(temp-row['ta_observed_c'])
                  + p['lower_boundary_h_w_k']*(temp-reference_p['lower_boundary_temperature_c'])
                  - p['internal_gain_w']-solar)
        residual = max(residual,abs(direct-(a+b*math.exp(-k*t))))
    if residual > ZERO_TOLERANCE_W:
        raise ValueError('common-service first-law curve mismatch')
    result.update(curve, evidence_status='SCN', reason=None, solar_gain_scn_w=solar,
                  max_first_law_residual_w=residual)
    return result


def _aggregate(rows):
    thermal = [r for r in rows if r['required_heat_kwh'] is not None]
    capacity = [r for r in rows if r['additional_thermal_kwh'] is not None]
    complete = len(thermal)==len(rows)
    cap_complete = len(capacity)==len(rows)
    return dict(status='SCN_COMPLETE_THERMAL_COMPARISON' if complete else 'Q_INCOMPLETE_THERMAL_COMPARISON',
                required_thermal_kwh=sum(r['required_heat_kwh'] for r in thermal) if complete else None,
                supported_only_heat_kwh=sum(r['required_heat_kwh'] for r in thermal) if thermal else None,
                additional_thermal_kwh=sum(r['additional_thermal_kwh'] for r in capacity) if cap_complete else None,
                supported_only_additional_thermal_kwh=sum(r['additional_thermal_kwh'] for r in capacity) if capacity else None,
                peak_required_kw=max(r['peak_required_kw'] for r in thermal) if complete else None,
                peak_additional_kw=max(r['peak_additional_kw'] for r in capacity) if cap_complete else None,
                over_capacity_duration_h=sum(r['over_capacity_duration_h'] for r in capacity) if cap_complete else None,
                supported_crossing_intervals=sum(r['capacity_crossing_hour_fraction'] is not None for r in capacity),
                unknown_thermal_hours=len(rows)-len(thermal),
                unknown_capacity_comparison_hours=len(rows)-len(capacity),
                actual_electricity_kwh=None, actual_spf=None, payback=None)


def calculate_reference(*, radiation_path: Path | None = None):
    """Admit only three pinned native states and the unchanged V1-033 trajectory.

The existing source/radiation hash checks apply. Missing radiation propagates Q
through all dependent curves/totals. No alternative weather, controls, state or
source parameters are accepted. Original empirical/applicability limits remain.
"""
    if hashlib.sha256(Path(hourly.__file__).read_bytes()).hexdigest() != THERMAL_API_SHA256:
        raise ValueError('reviewed thermal API changed; new comparison review required')
    base = hourly.calculate_reference(radiation_path=radiation_path)
    manifest = hourly._load_manifest(hourly.MANIFEST_PATH)
    if (base['case_id'] != hourly.CASE_ID or base['manifest_sha256'] != hourly.MANIFEST_SHA256
            or len(base['rows']) != 72 or len(base['fixed_path']['rows']) != 72):
        raise ValueError('exact common thermal case required')
    items, package = _source_items(base,manifest)
    parameters = [_parameters(item,manifest) for item in items]
    for key in ('capacity_wh_k','outdoor_h_w_k','lower_boundary_h_w_k','total_h_w_k','internal_gain_w'):
        if not math.isclose(parameters[-1][key],base['parameters'][key],rel_tol=0,abs_tol=1e-10):
            raise ValueError('ambitious source/reference parameter mismatch')
    states = []
    for item,p in zip(items,parameters):
        rows = [_record(row,fixed,base['parameters'],p,parameters[-1]['glazing_transmittance'])
                for row,fixed in zip(base['rows'],base['fixed_path']['rows'])]
        states.append(dict(variant_id=item['values']['Code_BuildingVariant'],source_row=item['source_row'],
                           native_description=item['values']['Description_BuildingVariant'],
                           evidence_status='SCN',parameters=p,rows=rows,**_aggregate(rows)))
    for state in states:
        before,after = states[0]['required_thermal_kwh'],state['required_thermal_kwh']
        state['conditional_heat_reduction_from_existing_kwh'] = before-after if before is not None and after is not None else None
    for new_key,old_key in (('required_thermal_kwh','required_thermal_energy_kwh'),
                            ('additional_thermal_kwh','additional_thermal_requirement_kwh')):
        new,old = states[-1][new_key],base['fixed_path'][old_key]
        if (new is None)!=(old is None) or (new is not None and not math.isclose(new,old,rel_tol=0,abs_tol=1e-9)):
            raise ValueError('ambitious thermal/capacity reference changed')
    return dict(case_id=CASE_ID,evidence_status='SCN',claim_scope='FINITE_COMMON_SERVICE_THERMAL_COMPARISON',
                source_id=package['source_id'],source_sha256=package['source_sha256'],
                source_extract_pin=manifest['repository_pins']['building'],
                common_source_controls=COMMON,thermal_reference=base,states=states,
                source_geometry_warnings=base['source_geometry_compatibility_flags'],
                reference_path_unchanged=True,alternative_temperature_path_evolved=False,
                whole_electricity_kwh=None,actual_spf=None,payback=None,
                electrical_consumer_handoff='UNAVAILABLE_TIME_VARYING_CURVES_NOT_V1_036_INPUTS',
                annual_output_used=False,source_seasonal_service_factors_used=False,
                backup_selected=False,empirical_validation=False,national_adoption=False,
                whole_slice_complete=False,
                limitations=('Historical source alternatives, not observed paired renovation outcomes',
                             'Same declared trajectory/weather and lower reservoir, not national comfort',
                             'Rating-capacity residual is additional thermal requirement, not served backup',
                             'Source/software checks do not establish empirical building or network validity'))
