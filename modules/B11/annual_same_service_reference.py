"""Source-allocated annual GCV gas and a conditional paired-service ledger.

IEE Projects TABULA + EPISCOPE (www.episcope.eu).
This consumer reuses the complete B05 annual device reference. It supplies no
hourly gas efficiency, auxiliary timing, national weight or gas-volume factor.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from modules.B05 import annual_device_reference as device

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b11_annual_same_service_reference_manifest.json'
MANIFEST_SHA256 = '6c6be62037dc588cd2d7a48b5bb569fb227f0ba26aac77a4c57e8a410b843cf5'
FULL_REFERENCE_REPLACEMENT = 'FULL_SOURCE_ALLOCATED_SPACE_HEATING_REPLACEMENT'


def _number(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or (value <= 0 if positive else value < 0)):
        raise ValueError('finite ' + ('positive ' if positive else 'nonnegative ') + name + ' required')
    return value


def _manifest():
    raw = MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed same-service gas manifest mismatch')
    data = json.loads(raw)
    for name, digest in data['repository_pins'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('reviewed repository input changed: ' + name)
    return data


def _compose(hp, manifest, condition):
    """Internal arithmetic seam; public admission always runs pinned producers."""
    if condition != FULL_REFERENCE_REPLACEMENT:
        raise ValueError('explicit full source-allocated space-heating reference condition required')
    source = manifest['gas_reference']
    thermal, summary = hp['thermal_reference'], hp['summary']
    if (hp['reference_id'] != manifest['device_reference_id']
            or thermal['variant_id'] != source['variant_id']
            or hp['evidence_status'] != 'DER' or hp['evidence_tier'] != 'E2'):
        raise ValueError('matching source-service and device reference required')
    if source['energy_basis'] != 'GCV':
        raise ValueError('source-native GCV basis required; no calorific conversion is performed')
    if (summary['complete_generator_service'] is not True
            or summary['unknown_hours'] != 0 or summary['source_capacity_shortfall_kwh'] != 0
            or summary['hours'] != 8760):
        raise ValueError('complete annual same-service device reference required')
    area = _number(source['area_m2'], 'source area', positive=True)
    factor = _number(source['seasonal_generator_expenditure_gcv'], 'seasonal expenditure', positive=True)
    useful = _number(thermal['useful_heat_kwh'], 'useful heat', positive=True)
    generator = _number(thermal['generator_heat_kwh'], 'generator heat', positive=True)
    gas = area * _number(source['space_heating_fuel_kwh_gcv_m2'], 'source heating fuel', positive=True)
    aux = area * _number(source['heating_auxiliary_kwh_m2'], 'source heating auxiliary')
    hp_electricity = _number(summary['annual_device_reference_electricity_kwh'], 'complete device electricity', positive=True)
    if (not math.isclose(useful, area * source['useful_heat_kwh_m2'], rel_tol=1e-12)
            or not math.isclose(generator, area * source['generator_heat_kwh_m2'], rel_tol=1e-12)
            or not math.isclose(gas, generator * factor, rel_tol=1e-12)):
        raise ValueError('source useful/generator/fuel boundary does not reconcile')
    # Gas/auxiliary values are annual source allocations. No hourly boiler or
    # auxiliary operating curve follows from their seasonal scalar values.
    electricity_intercept = hp_electricity - aux
    reduction_intercept = gas + aux - hp_electricity
    residual = dict(
        name='POST_REPLACEMENT_NONDEVICE_AND_RETAINED_AUXILIARY',
        value_kwh_year=None, evidence_status='Q',
        definition='Nonoverlapping post-replacement electricity at the declared heating-service boundary, including retained or reallocated combi-control demand',
        timing=None, upper_bound_kwh_year=None,
        baseline_auxiliary_is_avoidable_measurement=False,
        unchanged_dhw_auxiliary_proves_residual_covered=False,
    )
    return dict(
        reference_id=manifest['reference_id'], evidence_status='DER', evidence_tier='E2',
        condition=dict(value=condition, evidence_status='SCN',
                       meaning='Full replacement of the source-allocated space-heating service; no actual boiler retirement or household/national adoption'),
        source_annual_service=dict(useful_heat_kwh=useful, generator_heat_kwh=generator,
                                   authority=thermal['annual_authority']),
        baseline=dict(space_heating_gas_kwh_gcv=gas, heating_auxiliary_electricity_kwh=aux,
                      auxiliary_scope='Source heating-system allocation with unreported component composition'),
        replacement=dict(source_allocated_space_heating_gas_kwh_gcv=0.0,
                         device_electricity_kwh=hp_electricity, nondevice_and_retained_auxiliary=residual,
                         complete_heating_system_electricity_kwh=None),
        source_allocated_gas_reduction_kwh_gcv=gas,
        measured_whole_boiler_fuel_savings_kwh_gcv=None,
        electricity_change=dict(direction='AFTER_MINUS_BEFORE', known_intercept_kwh=electricity_intercept,
                                residual_coefficient=1.0, residual_name=residual['name'], total_kwh=None),
        purchased_energy_reduction=dict(direction='BEFORE_MINUS_AFTER', known_intercept_kwh=reduction_intercept,
                                        residual_coefficient=-1.0, residual_name=residual['name'], total_kwh=None,
                                        basis='GCV gas plus electricity as purchased final-energy carriers; not primary energy, money or thermodynamic efficiency'),
        excluded_dhw=dict(source_gas_kwh_gcv=area * source['excluded_dhw_fuel_kwh_gcv_m2'],
                          source_auxiliary_electricity_kwh=area * source['excluded_dhw_auxiliary_kwh_m2'],
                          displaced_by_this_reference=False),
        gas_hourly_profile=None, auxiliary_hourly_profile=None, net_grid_increment_profile=None,
        gas_volume_m3=None, import_value=None, household_savings=None,
        physical_spf=None, national_increment=None, national_admission=False,
        validation_debt=manifest['validation_debt'],
        device_reference=hp,
    )


def calculate_reference(*, weather_path: Path, condition: str):
    """Pair only the reviewed annual source service with an explicit condition.

The missing post-replacement residual is never filled with zero, the baseline
156.8 kWh allocation, or an assumed pump cancellation. Gas and auxiliary
annual values cannot authorize an hourly net grid increment or volume claim.
"""
    if condition != FULL_REFERENCE_REPLACEMENT:
        raise ValueError('explicit full source-allocated space-heating reference condition required')
    manifest = _manifest()
    hp = device.calculate_reference(weather_path=weather_path)
    return _compose(hp, manifest, condition)
