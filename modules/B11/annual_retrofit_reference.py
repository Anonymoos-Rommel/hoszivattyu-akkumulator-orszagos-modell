"""Annual source-package comparison using the existing heat-pump method.

IEE Projects TABULA + EPISCOPE (www.episcope.eu).
Adatbázis: Meteorológiai Adattár, HungaroMet Nonprofit Zrt.
No measured temperature trajectory, auxiliary cancellation or backup is added.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from modules.B05 import annual_device_reference as device

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b11_annual_retrofit_reference_manifest.json'
MANIFEST_SHA256 = '192b6aa0b0547373fadbe362b89969a7828002bc04305a07dca912b405479791'
SOURCE_PACKAGE_REPLACEMENT = 'FULL_SOURCE_ALLOCATED_SPACE_HEATING_REPLACEMENT_PLUS_SOURCE_REFURBISHMENT_PACKAGE'
AFTER_CASES = ('standard', 'ambitious')


def _manifest():
    raw = MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed annual retrofit manifest mismatch')
    data = json.loads(raw)
    for name, digest in data['repository_pins'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('reviewed annual retrofit dependency changed: ' + name)
    return data


def _native_gas(case, thermal):
    source = case['gas']
    if source['energy_basis'] != 'GCV':
        raise ValueError('source-native GCV energy required')
    area = device._number(case['thermal']['area_m2'], 'source area', positive=True)
    factor = device._number(source['expenditure_factor'], 'seasonal expenditure', positive=True)
    fuel = area * device._number(source['heating_fuel_kwh_gcv_m2'], 'source heating fuel', positive=True)
    auxiliary = area * device._number(source['heating_auxiliary_kwh_m2'], 'source auxiliary')
    if not math.isclose(fuel, thermal['generator_heat_kwh'] * factor, rel_tol=1e-12):
        raise ValueError('source annual generator/fuel closure failed')
    return dict(source_allocated_heating_gas_kwh_gcv=fuel,
                source_allocated_heating_auxiliary_kwh=auxiliary,
                source_generator_expenditure_gcv=factor,
                annual_only=True, component_composition_known=False,
                measured_avoidable_auxiliary_kwh=None,
                gas_volume_m3=None, gas_hourly_profile=None)


def calculate_family_reference(*, weather_path: Path):
    """Calculate the three pinned source packages, retaining every shortfall."""
    manifest = _manifest()
    base = device._manifest()
    weather = device._weather(weather_path, base['weather'])
    models = {mode: device.wm50.load_wm50_reference(mode, fixed_supply_c=55)
              for mode in device.paired.MODES}
    grid = device.wm50.source_grid()
    cases = {}
    for label in ('original', 'standard', 'ambitious'):
        spec = manifest['cases'][label]
        thermal = device._thermal({'thermal': spec['thermal']})
        rows, summary = device._calculate(weather, thermal, base['heat_pump'], models, grid)
        cases[label] = dict(
            variant_id=spec['thermal']['variant_id'],
            source_building_row=spec['building_row'], source_system_row=spec['system_row'],
            native_gas_reference=_native_gas(spec, thermal),
            device_reference=dict(reference_id=spec['reference_id'],
                                  evidence_status='DER', evidence_tier='E2',
                                  thermal_reference=thermal, rows=rows, summary=summary,
                                  national_admission=False, whole_slice_complete=False),
            source_nonuniform_heating_factor=spec['nonuniform_heating_factor'],
            source_infiltration_h_inv=spec['infiltration_h_inv'],
        )
    standard = cases['standard']['device_reference']['summary']
    ambitious = cases['ambitious']['device_reference']['summary']
    both_complete = all(s['complete_generator_service'] is True for s in (standard, ambitious))
    device_reduction = (standard['annual_device_reference_electricity_kwh']
                        - ambitious['annual_device_reference_electricity_kwh']) if both_complete else None
    return dict(reference_id=manifest['reference_id'], evidence_status='DER', evidence_tier='E2',
                service_convention=manifest['service_convention'], cases=cases,
                standard_to_ambitious=dict(device_only_reduction_kwh=device_reduction,
                                           installed_reduction_kwh=None,
                                           residual='A_standard - A_ambitious',
                                           residuals_presumed_equal=False),
                installed_system_electricity_reduction_kwh=None,
                original_full_service_hp_reduction_kwh=None,
                service_completion_basis='SOURCE_RATING_REFERENCE_ONLY',
                installed_heat_delivery_kwh=None, installed_service_completion=None,
                national_admission=False, validation_debt=manifest['validation_debt'],
                limits=manifest['limits'])


def _compare(family, after_case, condition):
    """Internal accounting seam; callers cannot provide a family to the API."""
    if condition != SOURCE_PACKAGE_REPLACEMENT or after_case not in AFTER_CASES:
        raise ValueError('explicit original-gas to standard/ambitious source-package condition required')
    before = family['cases']['original']
    after = family['cases'][after_case]
    hp = after['device_reference']
    summary = hp['summary']
    if (summary['complete_generator_service'] is not True or summary['unknown_hours'] != 0
            or summary['source_capacity_shortfall_kwh'] != 0 or summary['hours'] != 8760):
        raise ValueError('complete after-case service required; no backup is supplied')
    gas = device._number(before['native_gas_reference']['source_allocated_heating_gas_kwh_gcv'],
                         'original annual heating gas', positive=True)
    auxiliary = device._number(before['native_gas_reference']['source_allocated_heating_auxiliary_kwh'],
                               'original annual heating auxiliary')
    electricity = device._number(summary['annual_device_reference_electricity_kwh'],
                                 'complete after-case device electricity', positive=True)
    residual = 'A_' + after_case
    return dict(
        reference_id=family['reference_id'], after_case=after_case,
        evidence_status='DER', evidence_tier='E2',
        condition=dict(value=condition, evidence_status='SCN',
                       meaning='Original source gas-heating package to the selected source retrofit package with full space-heating replacement'),
        service_convention=family['service_convention'],
        before=dict(variant_id=before['variant_id'],
                    useful_heat_kwh=before['device_reference']['thermal_reference']['useful_heat_kwh'],
                    generator_heat_kwh=before['device_reference']['thermal_reference']['generator_heat_kwh'],
                    source_allocated_gas_kwh_gcv=gas, source_allocated_auxiliary_kwh=auxiliary),
        after=dict(variant_id=after['variant_id'],
                   useful_heat_kwh=hp['thermal_reference']['useful_heat_kwh'],
                   generator_heat_kwh=hp['thermal_reference']['generator_heat_kwh'],
                   source_allocated_space_heating_gas_kwh_gcv=0.0,
                   device_electricity_kwh=electricity, complete_system_electricity_kwh=None),
        source_allocated_gas_reduction_kwh_gcv=gas,
        electricity_change=dict(direction='AFTER_MINUS_BEFORE', known_intercept_kwh=electricity-auxiliary,
                                residual_name=residual, residual_coefficient=1.0, total_kwh=None),
        purchased_final_energy_reduction=dict(direction='BEFORE_MINUS_AFTER',
                                              known_intercept_kwh=gas+auxiliary-electricity,
                                              residual_name=residual, residual_coefficient=-1.0, total_kwh=None,
                                              basis='GCV gas plus electricity, not primary energy, money or thermodynamic efficiency'),
        residual=dict(name=residual, value_kwh=None, evidence_status='Q', timing=None, upper_bound_kwh=None,
                      sign='SIGNED_UNKNOWN', is_physical_auxiliary_consumption_sum=False,
                      rated_unit_control_and_safety_input_already_included=True,
                      installed_thermal_boundary_and_duty_reconciled=False,
                      definition='Signed installed-case electricity for the declared heating service minus the rating-derived device reference; includes replacement of embedded pump allowance, associated heat-delivery/duty reconciliation, and genuinely additional/excluded or retained/reallocated combi controls'),
        dhw_changes_included=False, native_dhw_solar_or_appliance_changes_adopted=False,
        measured_whole_boiler_fuel_savings_kwh_gcv=None,
        original_hp_capacity_diagnostic=before['device_reference']['summary'],
        after_device_reference=hp,
        installed_system_savings_kwh=None, net_grid_increment_profile=None,
        gas_volume_m3=None, import_value=None, household_savings=None,
        physical_spf=None, national_increment=None, national_admission=False,
        service_completion_basis='SOURCE_RATING_REFERENCE_ONLY',
        installed_heat_delivery_kwh=None, installed_service_completion=None,
        validation_debt=family['validation_debt'], limits=family['limits'],
    )


def compare_original_to_retrofit(*, weather_path: Path, after_case: str, condition: str):
    """Select a complete technical after-case explicitly; never choose backup."""
    if condition != SOURCE_PACKAGE_REPLACEMENT or after_case not in AFTER_CASES:
        raise ValueError('explicit original-gas to standard/ambitious source-package condition required')
    return _compare(calculate_family_reference(weather_path=weather_path), after_case, condition)
