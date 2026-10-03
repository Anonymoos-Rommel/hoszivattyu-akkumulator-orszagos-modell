"""One pinned prospective design/capacity diagnostic, never a real-record gate.

B02 component maxima form an outer model envelope, not a joint building. B06
computes its conditional design heat; B05 evaluates explicit fixed manufacturer
coordinates. Arithmetic DER does not remove the physical SCN lineage. This
module does not run the annual engine, emitter/P65 gate or hourly simulation.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, fields, is_dataclass
import hashlib
import json
from math import isclose, isfinite
from pathlib import Path

from modules.B02.hungarian_facade_opening_split import (
    REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K,
)
from modules.B02.post_retrofit_ventilation_hvent import (
    AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K, RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
)
from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B06 import design_load
from modules.B06.engine import EvidenceValue

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / 'registry/b06_prospective_capacity_reference_manifest.json'
CASE_ID = 'B06-PROSPECTIVE-Y_LT1919-FAMILY_HOUSE-OUTER-STRESS'
CLAIM_SCOPE = 'PROSPECTIVE_DESIGN_CAPACITY_DIAGNOSTIC_ONLY'
# Pinning the pin set also rejects silent repinning of changed source/code bytes.
PIN_SET_SHA256 = 'ffa05c894396266d0291428718d664a3d138a101bfa4f6eda45105233ea68c05'
SCOPE_METADATA_SHA256 = 'dbcceecb0fcf3887a48b96080d28070878604f12f42764e3b5f38515b7964a13'
DEPENDENCE = 'COMPONENT_MAXIMA_OUTER_BOUND_NOT_JOINTLY_ATTAINED_BUILDING'
PROBE_ROLE = 'MANUFACTURER_COORDINATE_NOT_EMITTER_REQUIRED_TEMPERATURE'
BOUNDARIES = {
    'facade': 'OUTSIDE', 'top': 'HEATED_ATTIC_ENCLOSURE',
    'bottom': 'BASEMENT_CEILING',
    'ventilation': 'NATURAL_VENTILATION_NO_HEAT_RECOVERY',
    'insulation': 'NON_INTERNAL_SIMPLIFIED_ZETA',
}
SCENARIO_FIELDS = {
    'bottom_base_u_w_m2k': ('W/m2K', .26), 'bottom_zeta': ('ratio', .20),
    'bottom_design_boundary_correction': ('ratio', 1.),
    'outside_design_boundary_correction': ('ratio', 1.),
    'heat_recovery_efficiency': ('ratio', 0.),
    'additional_thermal_bridge_h_w_per_k': ('W/K', 0.),
    'design_indoor_temperature_c': ('degC', 20.),
    'design_outdoor_temperature_c': ('degC', -12.),
}
SCENARIO_SOURCES = {
    'bottom_base_u_w_m2k': ['SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022'],
    'bottom_zeta': ['SRC-B06-HU-ENERGY-METHOD-2023'],
    'design_indoor_temperature_c': ['SRC-B06-HU-ENERGY-METHOD-2023'],
    'design_outdoor_temperature_c': ['SRC-B02-BIMLINE-MSZ24140-2026'],
    **{key: ['SCN-B06-PROSPECTIVE-BASEMENT-DESIGN-STRESS'] for key in (
        'bottom_design_boundary_correction', 'outside_design_boundary_correction',
        'heat_recovery_efficiency', 'additional_thermal_bridge_h_w_per_k')},
}
ROW_CONTRACTS = {
    'facade': ('B02-P95-F01', 'QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY', 'DER/SCN_PROXY'),
    'top': ('B02-P96-T01', 'QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U', 'POL/DER/SCN'),
    'bottom': ('B02-P94-B01', 'QUALIFIED_HUNGARIAN_BOTTOM_ENVELOPE_AREA_PROXY', 'DER/SCN_PROXY'),
    'ventilation': ('B02-P90-T01', 'QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET', 'POL/DER/SCN'),
    'bridges': ('B02-P91-T01', 'QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE', 'POL/DER/SCN'),
    'temperatures': ('B02-P97-T01', 'QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE', 'POL/DER/SCN'),
    'probe_categories': ('B02-P98-S01', 'QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET', 'POL/DER/SCN'),
}


def _keys(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f'{name}: unsupported or missing fields')


def _quantity(value, unit, name):
    _keys(value, ('value', 'unit', 'evidence_status', 'source_ids'), name)
    if value['evidence_status'] != 'SCN' or value['value'] is None:
        raise ValueError(f'{name}: missing/Q evidence or dropped SCN lineage')
    number = value['value']
    if isinstance(number, bool) or not isinstance(number, (float, int)) or not isfinite(number):
        raise ValueError(f'{name}: finite numeric quantity required')
    if value['unit'] != unit or not isinstance(value['source_ids'], list) or not value['source_ids'] or not all(
            isinstance(s, str) and s.strip() for s in value['source_ids']):
        raise ValueError(f'{name}: unit/source authority required')
    return EvidenceValue(float(number), 'SCN', tuple(value['source_ids']))


def _load_manifest(path):
    m = json.loads(Path(path).read_text(encoding='utf-8'))
    _keys(m, ('schema_version', 'case_id', 'claim_scope', 'physical_evidence_status',
              'stratum', 'dependence_qualification', 'boundary_declarations',
              'thermal_bridge_treatment', 'scenario', 'equipment', 'inputs',
              'limitations', 'separate_regression'), 'manifest')
    if (m['schema_version'] != 1 or m['case_id'] != CASE_ID or
            m['claim_scope'] != CLAIM_SCOPE or m['physical_evidence_status'] != 'SCN' or
            m['dependence_qualification'] != DEPENDENCE or
            m['stratum'] != {'wbl_period_code': 'Y_LT1919', 'building_group': 'FAMILY_HOUSE'}):
        raise ValueError('unsupported case, claim scope or physical SCN lineage')
    if m['boundary_declarations'] != BOUNDARIES:
        raise ValueError('explicit qualified boundary declarations required')
    if m['thermal_bridge_treatment'] != 'CORRECTED_U_ONCE_NO_SEPARATE_BRIDGE_SUM':
        raise ValueError('corrected U already includes thermal bridges')
    _keys(m['scenario'], SCENARIO_FIELDS, 'scenario')
    for key, (unit, expected) in SCENARIO_FIELDS.items():
        item = _quantity(m['scenario'][key], unit, key)
        if m['scenario'][key]['source_ids'] != SCENARIO_SOURCES[key]:
            raise ValueError(f'{key}: source/scenario identity mismatch')
        if item.value != expected:
            raise ValueError(f'{key}: outside this explicit pinned scenario')
    eq = m['equipment']
    _keys(eq, ('product', 'mode', 'source_id', 'probe_role', 'fixed_supply_probes_c'), 'equipment')
    if (eq['product'] != wm50.PRODUCT or eq['source_id'] != wm50.SOURCE_ID or
            eq['mode'] != 'MAX' or eq['probe_role'] != PROBE_ROLE):
        raise ValueError('wrong source product/mode or emitter authority promotion')
    probes = [_quantity(v, 'degC', 'fixed_supply_probe').value for v in eq['fixed_supply_probes_c']]
    if probes != [35., 45., 55.] or any(v['source_ids'] != [wm50.SOURCE_ID] for v in eq['fixed_supply_probes_c']):
        raise ValueError('exact declared W35/W45/W55 coordinate probes required')
    digest = hashlib.sha256(json.dumps(m['inputs'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if digest != PIN_SET_SHA256:
        raise ValueError('reviewed input pin set mismatch; repinning requires review')
    for name, pin in m['inputs'].items():
        if hashlib.sha256((ROOT / pin['path']).read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError(f'reviewed source/code hash mismatch: {name}')
    if (m['separate_regression'].get('relationship') != 'SEPARATE_NATIVE_ANNUAL_REGRESSION_NOT_A_DESIGN_INPUT'
            or m['separate_regression'].get('service') != 'source'):
        raise ValueError('native annual regression must remain separate')
    scope_digest = hashlib.sha256(json.dumps(
        {k: m[k] for k in ('limitations', 'separate_regression')},
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if scope_digest != SCOPE_METADATA_SHA256:
        raise ValueError('reviewed scope/annual-lineage metadata mismatch')
    return m


def _read_rows(m):
    selected = {}
    for name, contract in ROW_CONTRACTS.items():
        with (ROOT / m['inputs'][name]['path']).open(encoding='utf-8', newline='') as f:
            rows = [r for r in csv.DictReader(f) if all(r.get(k) == v for k, v in m['stratum'].items())]
        if len(rows) != 1:
            raise ValueError(f'{name}: exactly one joined source row required')
        row = rows[0]
        if tuple(row.get(k) for k in ('surface_id', 'status', 'evidence_status')) != contract:
            raise ValueError(f'{name}: source row identity/status mismatch, including Q evidence')
        if 'candidate_type_ids' in row and row['candidate_type_ids'] != '1;2;3':
            raise ValueError(f'{name}: incompatible candidate geometry')
        selected[name] = row
    return selected


def _source_number(m, rows, name, column):
    row = rows[name]
    if 'Q' in row['evidence_status'].split('/'):
        raise ValueError(f'{name}.{column}: Q evidence is not arithmetic input')
    value = float(row[column])
    if not isfinite(value):
        raise ValueError(f'{name}.{column}: finite value required')
    # The source label remains verbatim in input_lineage; the conditional
    # physical wrapper uses SCN for all quantities inherited into this case.
    return EvidenceValue(value, 'SCN', tuple(m['inputs'][name]['source_ids']))


def _available_evidence(value, name='design_inputs'):
    """Reject numeric-but-Q recursively before calling the older B06 helper."""
    if isinstance(value, EvidenceValue):
        value.validate(name)
        if value.status == 'Q' or value.value is None:
            raise ValueError(f'{name}: Q evidence cannot enter the design helper')
        if value.status != 'SCN':
            raise ValueError(f'{name}: dropped physical SCN lineage')
        if not value.source_ids:
            raise ValueError(f'{name}: physical source/scenario lineage required')
        if isinstance(value.value, (int, float)) and (isinstance(value.value, bool) or not isfinite(value.value)):
            raise ValueError(f'{name}: finite numeric evidence required')
    elif is_dataclass(value):
        for field in fields(value):
            _available_evidence(getattr(value, field.name), f'{name}.{field.name}')
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            _available_evidence(item, f'{name}[{index}]')


def _build_design(m, rows):
    source = lambda name, column: _source_number(m, rows, name, column)
    scenario = {k: _quantity(v, SCENARIO_FIELDS[k][0], k) for k, v in m['scenario'].items()}
    bridges = rows['bridges']
    # Same facade upper and same opening share. Do not sum unrelated wall and
    # opening maxima, or label the aggregate opening as window-only area.
    gross = source('facade', 'gross_facade_upper_m2_per_dwelling')
    share = source('facade', 'opening_share_upper')
    # Retain the materialized area precision. Check the correlated partition
    # against gross/share rather than inventing independent component extrema.
    wall_area = source('facade', 'net_wall_area_upper_m2_per_dwelling')
    opening_area = source('facade', 'opening_area_upper_m2_per_dwelling')
    _close(wall_area.value, gross.value * (1 - share.value), 'wall partition')
    _close(opening_area.value, gross.value * share.value, 'opening partition')
    wall_u = source('bridges', 'external_wall_corrected_u_upper_w_m2k')
    opening_u = EvidenceValue(REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K, 'SCN',
                             tuple(m['inputs']['opening_method']['source_ids']))
    bottom_u = scenario['bottom_base_u_w_m2k']
    zeta = scenario['bottom_zeta']
    if (bottom_u.value != float(bridges['basement_ceiling_u_max_w_m2k']) or
            zeta.value != float(bridges['basement_ceiling_zeta_upper'])):
        raise ValueError('bottom scenario does not match its declared method envelope')
    corrected_bottom_u = EvidenceValue(bottom_u.value * (1 + zeta.value), 'SCN',
                                       tuple(sorted(set(bottom_u.source_ids + zeta.source_ids))))
    outside = scenario['outside_design_boundary_correction']
    components = (
        design_load.EnvelopeComponent('net_external_wall', wall_u, wall_area, 'OUTSIDE', outside),
        design_load.EnvelopeComponent('aggregate_openings_including_doors', opening_u, opening_area, 'OUTSIDE', outside),
        design_load.EnvelopeComponent('top', source('top', 'pitched_roof_corrected_u_upper_w_m2k'),
                                      source('top', 'top_envelope_area_upper_m2_per_dwelling'), 'HEATED_ATTIC_ENCLOSURE', outside),
        design_load.EnvelopeComponent('bottom_explicit_scenario', corrected_bottom_u,
                                      source('bottom', 'bottom_envelope_area_upper_m2_per_dwelling'), 'BASEMENT_CEILING',
                                      scenario['bottom_design_boundary_correction']),
    )
    infiltration = source('ventilation', 'n_filt_target_upper_h')
    rate = EvidenceValue(RESIDENTIAL_REQUIRED_AIR_CHANGE_H + infiltration.value, 'SCN',
                         tuple(m['inputs']['ventilation_method']['source_ids']))
    heat_capacity = EvidenceValue(AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K, 'SCN', rate.source_ids)
    vent = design_load.VentilationInput(source('ventilation', 'heated_volume_upper_m3_per_dwelling'),
                                       air_change_rate_h=rate,
                                       heat_recovery_efficiency=scenario['heat_recovery_efficiency'],
                                       air_volumetric_heat_capacity_wh_m3k=heat_capacity)
    temperatures = rows['temperatures']
    if (scenario['design_indoor_temperature_c'].value != float(temperatures['indoor_reference_c']) or
            scenario['design_outdoor_temperature_c'].value not in map(float, temperatures['outdoor_zone_set_c'].split(';'))):
        raise ValueError('engineering coordinate outside the declared P97 reference set')
    if (rows['probe_categories']['b05_audit_control_points_c'] != '35;45;55' or
            rows['probe_categories']['population_weight_status'] != 'LATENT_SET_PROPAGATION_NO_POINT_WEIGHTS'):
        raise ValueError('P98 coordinate anchors cannot supply population weights')
    return design_load.DesignLoadInputs(
        building_id=CASE_ID, location_or_climate_zone=EvidenceValue(
            'P97_EXPLICIT_MINUS12_ENGINEERING_PROBE_NO_REAL_LOCATION', 'SCN',
            tuple(m['inputs']['temperatures']['source_ids'])),
        design_outdoor_temperature_c=scenario['design_outdoor_temperature_c'],
        design_indoor_temperature_c=scenario['design_indoor_temperature_c'],
        components=components, thermal_bridge_h_w_per_k=scenario['additional_thermal_bridge_h_w_per_k'],
        ventilation=vent, source_ids=tuple(sorted(
            {s for p in m['inputs'].values() for s in p['source_ids']} |
            {s for q in m['scenario'].values() for s in q['source_ids']})),
    )


def _close(actual, expected, name):
    if not isclose(actual, expected, rel_tol=0, abs_tol=1e-8):
        raise ValueError(f'{name}: component/source unit balance mismatch')


def _support_cells(grid, supply, outdoor):
    column = [r for r in grid if r['mode'] == 'MAX' and float(r['supply_temperature_c']) == supply]
    lower = [float(r['outdoor_temperature_c']) for r in column if float(r['outdoor_temperature_c']) <= outdoor]
    upper = [float(r['outdoor_temperature_c']) for r in column if float(r['outdoor_temperature_c']) >= outdoor]
    bounds = ({max(lower)} if lower else set()) | ({min(upper)} if upper else set())
    return [{k: r[k] for k in ('source_id', 'mode', 'outdoor_temperature_c', 'supply_temperature_c',
                               'availability', 'thermal_capacity_kw', 'cop', 'derived_input_kw',
                               'evidence_status', 'source_pair_status', 'defrost_source_annotation')}
            for r in column if float(r['outdoor_temperature_c']) in bounds]


def calculate_reference(*, manifest_path: Path | None = None):
    """Execute the pinned conditional case or raise on corrupt/unsupported input.

    An unsupported manufacturer coordinate is a returned Q with null powers
    and margin. It does not erase the valid design calculation or become zero
    electrical demand. No generic physical scenario or evidence gate is exposed.
    """
    m = _load_manifest(MANIFEST_PATH if manifest_path is None else manifest_path)
    rows = _read_rows(m)
    inputs = _build_design(m, rows)
    _available_evidence(inputs)
    if (inputs.thermal_bridge_h_w_per_k.value != 0 or
            any(c.u_value_w_m2k.status != 'SCN' or c.area_m2.status != 'SCN' for c in inputs.components)):
        raise ValueError('thermal bridge double count or dropped physical SCN lineage')
    design = design_load.calculate_design_heat_load(inputs)
    if design.status != 'DER' or design.gaps or design.design_heat_load_kw is None:
        raise ValueError(f'canonical design calculation incomplete: {design.gaps}')
    component_h = {c.component: c.area_m2.value * c.u_value_w_m2k.value * c.correction_factor.value
                   for c in inputs.components}
    facade_h = component_h['net_external_wall'] + component_h['aggregate_openings_including_doors']
    _close(facade_h, float(rows['facade']['facade_transmission_h_upper_w_per_k_per_dwelling']), 'facade')
    _close(component_h['top'], float(rows['top']['top_envelope_h_upper_w_per_k_per_dwelling']), 'top')
    _close(design.ventilation_h_w_per_k, float(rows['ventilation']['h_vent_target_upper_w_per_k']), 'ventilation')
    total_h = sum(component_h.values()) + design.ventilation_h_w_per_k
    _close(design.design_heat_load_kw * 1000, total_h * design.delta_t_k, 'design W/kW')
    grid = wm50.source_grid()
    probes = []
    outdoor = inputs.design_outdoor_temperature_c.value
    for coordinate in m['equipment']['fixed_supply_probes_c']:
        supply = coordinate['value']
        model = wm50.load_wm50_reference('MAX', fixed_supply_c=supply)
        if model.equipment_id != f'{wm50.PRODUCT}:MAX:VOL5.3:FIXED_W{supply:g}':
            raise ValueError('manufacturer consumer returned wrong product/mode')
        result = model.evaluate(outdoor, supply)
        point = result.point
        if point is not None:
            if (point.source_ids != (wm50.SOURCE_ID,) or point.evidence_status != 'DER' or result.status != 'DER' or
                    point.outdoor_temperature_c != outdoor or point.supply_temperature_c != supply):
                raise ValueError('wrong performance source identity/evidence')
            if any(not isfinite(v) or v <= 0 for v in (point.thermal_capacity_kw, point.electrical_input_kw, point.cop)):
                raise ValueError('invalid manufacturer performance powers/COP')
            _close(point.thermal_capacity_kw, point.electrical_input_kw * point.cop, 'B05 Q=P*COP')
        elif not result.status.startswith('Q /'):
            raise ValueError('missing manufacturer point requires explicit Q status')
        probes.append({
            'fixed_supply_c': supply, 'outdoor_c': outdoor, 'mode': 'MAX', 'product': wm50.PRODUCT,
            'probe_role': PROBE_ROLE, 'performance_status': result.status,
            'physical_comparison_evidence_status': 'SCN' if point else 'Q',
            'capacity_comparison_status': ('CAPACITY_SHORTFALL_VS_OUTER_STRESS' if point.thermal_capacity_kw < design.design_heat_load_kw
                                           else 'CAPACITY_COVERS_OUTER_STRESS') if point else 'Q / UNSUPPORTED_COORDINATE',
            'thermal_capacity_kw': point.thermal_capacity_kw if point else None,
            'electrical_input_kw': point.electrical_input_kw if point else None,
            'cop': point.cop if point else None,
            'signed_capacity_margin_kw': point.thermal_capacity_kw - design.design_heat_load_kw if point else None,
            'margin_definition': 'available_capacity_minus_conditional_design_load',
            'interpolation': point.interpolation if point else None, 'domain_reason': result.reason,
            'source_ids': [wm50.SOURCE_ID], 'source_support_cells': _support_cells(grid, supply, outdoor),
            'required_emitter_supply_c': None, 'required_emitter_supply_status': 'Q / P65_NOT_ASSESSED',
        })
    return {
        'case_id': CASE_ID, 'claim_scope': CLAIM_SCOPE, 'evidence_status': 'SCN',
        'status': 'POPULATED_CONDITIONAL_DESIGN_CAPACITY_DIAGNOSTIC',
        'dependence_qualification': DEPENDENCE, 'stratum': m['stratum'],
        'boundary_declarations': m['boundary_declarations'], 'scenario': m['scenario'],
        'design_inputs': asdict(inputs), 'canonical_arithmetic_status': design.status,
        'ventilation_method_inputs': {
            'required_air_change_h': {'value': RESIDENTIAL_REQUIRED_AIR_CHANGE_H, 'unit': '1/h', 'evidence_status': 'POL'},
            'infiltration_upper_h': {'value': float(rows['ventilation']['n_filt_target_upper_h']), 'unit': '1/h', 'evidence_status': 'SCN'},
            'air_volumetric_heat_capacity': {'value': AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K, 'unit': 'Wh/m3K', 'evidence_status': 'POL'},
            'source_ids': m['inputs']['ventilation_method']['source_ids'],
        },
        'design_evidence_status': 'SCN', 'component_h_w_per_k': component_h,
        'facade_subtotal_h_w_per_k': facade_h, 'ventilation_h_w_per_k': design.ventilation_h_w_per_k,
        'separate_thermal_bridge_h_w_per_k': design.thermal_bridge_h_w_per_k,
        'thermal_bridge_treatment': m['thermal_bridge_treatment'],
        'total_h_w_per_k': total_h, 'delta_t_k': design.delta_t_k,
        'design_heat_kw': design.design_heat_load_kw, 'probes': probes,
        'input_lineage': {name: {'row_id': row['surface_id'], 'source_evidence_status': row['evidence_status'],
                                **m['inputs'][name]} for name, row in rows.items()},
        'input_pin_set_sha256': PIN_SET_SHA256,
        'withheld_claims': {key: 'Q / NOT_ASSESSED' for key in (
            'p65_emitter_authority', 'real_record_eligibility', 'realized_completion',
            'annual_electricity', 'spf', 'national_programme_result', 'physical_slice_completion', 'readiness_uplift')},
        'omitted_inputs': {key: 'Q / NOT_POPULATED' for key in (
            'hourly_heat_and_gain_states', 'thermal_mass', 'emitter_inventory', 'return_temperature_path',
            'runtime_and_control', 'numeric_cycling', 'additional_dynamic_defrost', 'external_auxiliaries', 'dhw_duty')},
        'limitations': m['limitations'], 'separate_regression': m['separate_regression'],
    }
