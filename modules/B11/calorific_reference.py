"""Named TABULA annual gas energy convention, not measured billing gas.

IEE Projects TABULA + EPISCOPE (www.episcope.eu).
No volume conversion, weather allocation or physical Hungarian gas ratio.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b11_calorific_reference_manifest.json'
MANIFEST_SHA256 = '1ebd49b36328ffd0af2d8228f0a30cfed9cb2ced69effccd9ae2e11c6d48b6f0'
PACKAGES = ('original', 'standard', 'ambitious')


def _manifest():
    data = MANIFEST.read_bytes()
    if hashlib.sha256(data).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed calorific source convention mismatch')
    m = json.loads(data)
    for name, pin in m['repository_pins'].items():
        if hashlib.sha256((ROOT / pin['path']).read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('reviewed annual gas source changed: ' + name)
    return m


def calculate_reference(*, package: str):
    """Convert one exact annual-only natural-gas source case with its convention.

Decimal arithmetic uses existing registry source serialization. The native
GCV energy is preserved; the derived NCV quantity is a named source-reference
convention, not measured Hungarian gas or admitted tariff billing energy.
"""
    if package not in PACKAGES:
        raise ValueError('one named original/standard/ambitious source package required')
    m = _manifest()
    pin = m['repository_pins']['source_family']
    raw = (ROOT / pin['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('source-family bytes changed before parsing')
    family = json.loads(raw, parse_float=Decimal)
    case = family['cases'][package]
    fuel = [x for x in case['source_system_cells'] if x['field'] == 'Code_SysH_EC_1']
    if len(fuel) != 1 or fuel[0]['value'] != 'Gas' or case['gas']['energy_basis'] != 'GCV':
        raise ValueError('qualified natural-gas GCV source case required')
    with localcontext() as ctx:
        ctx.prec = 50
        area = Decimal(case['thermal']['area_m2'])
        specific = Decimal(case['gas']['heating_fuel_kwh_gcv_m2'])
        if not area.is_finite() or not specific.is_finite() or area <= 0 or specific <= 0:
            raise ValueError('positive finite source area and annual heating fuel required')
        gcv_kwh = area * specific
        gcv_mj = gcv_kwh * Decimal('3.6')
        ratio = Decimal(m['source_convention']['ncv_over_gcv'])
        ncv_mj = gcv_mj * ratio
        alternative = Decimal(m['distinct_general_convention']['ncv_over_gcv'])
        difference = gcv_mj * (ratio-alternative)
    return dict(
        reference_id=m['reference_id'], package=package,
        variant_id=case['thermal']['variant_id'], source_system_row=case['system_row'],
        source_id=m['source_convention']['source_id'], source_sha256=m['source_convention']['source_sha256'],
        evidence_status='DER', evidence_tier='E2',
        quantity_scope='NAMED_TABULA_ANNUAL_SPACE_HEATING_SOURCE_CONVENTION',
        source_gas_kwh_gcv=gcv_kwh, source_gas_mj_gcv=gcv_mj,
        source_convention_ncv_over_gcv=ratio, source_convention_gas_mj_ncv=ncv_mj,
        source_constant_observation_scope='WORKBOOK_CONVENTION_NOT_MEASURED_HUNGARIAN_GAS_RATIO',
        general_convention_difference_mj=difference,
        general_convention_difference_is_uncertainty_bound=False,
        general_convention_is_second_canonical_case=False,
        annual_only=True, gas_hourly_profile=None, billing_year_allocation=None,
        physical_hungarian_gas_mj_ncv=None, actual_billing_energy_mj=None,
        gas_volume_m3=None, import_value=None, household_savings=None,
        dhw_or_cooking_added=False, gas_auxiliary_electricity_converted=False,
        national_admission=False, whole_slice_complete=False,
        validation_debt=m['validation_debt'])
