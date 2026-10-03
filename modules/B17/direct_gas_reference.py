"""Direct-combustion CO2 inventory reference for named TABULA gas cases.

The IPCC default is an ASS official method factor; applying it to the existing
source-convention activity is a conditional DER/E2 calculation. The inventory
method expresses total fuel carbon as CO2, including carbon emitted in other
species. This is not measured stack CO2, heat-pump offsets or net climate gain.
"""
from __future__ import annotations

import argparse
from decimal import Context, Decimal, localcontext
import hashlib
import json
from pathlib import Path

from modules.B11 import calorific_reference as activity_source

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b17_direct_gas_reference_manifest.json'
MANIFEST_SHA256 = '2f86bc20eebe15f344c61fb4b2020c1b8232f430c3215abd318675def6f5757f'
PACKAGES = ('original', 'standard', 'ambitious')
MJ_PER_TJ = Decimal('1000000')


def _manifest():
    raw = MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed direct-gas factor and applicability changed')
    manifest = json.loads(raw)
    for pin in manifest['repository_pins'].values():
        if hashlib.sha256((ROOT / pin['path']).read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('reviewed activity authority changed')
    factor = manifest['factor']
    if (factor['fuel'] != 'Natural Gas' or factor['pollutant'] != 'CO2'
            or factor['unit'] != 'kg_CO2_per_TJ_NCV_fuel_input'
            or factor['oxidation_factor_already_included'] != '1'
            or factor['interval_kind'] != 'SOURCE_DEFAULT_95_PERCENT_CONFIDENCE_INTERVAL'):
        raise ValueError('qualified natural-gas CO2 method boundary required')
    values = tuple(Decimal(factor[k]) for k in ('value', 'lower', 'upper'))
    central, lower, upper = values
    if any(not n.is_finite() or n <= 0 for n in values) or not lower <= central <= upper:
        raise ValueError('positive ordered source factor required')
    return manifest, values


def _activity(package):
    if type(package) is not str or package not in PACKAGES:
        raise ValueError('one named original/standard/ambitious package required')
    a = activity_source.calculate_reference(package=package)
    if (a['quantity_scope'] != 'NAMED_TABULA_ANNUAL_SPACE_HEATING_SOURCE_CONVENTION'
            or a['evidence_tier'] != 'E2' or a['evidence_status'] != 'DER'
            or a['source_convention_ncv_over_gcv'] != Decimal('0.92')
            or a['dhw_or_cooking_added'] or a['gas_auxiliary_electricity_converted']
            or a['national_admission'] or not a['annual_only']):
        raise ValueError('qualified heating-only source-convention activity required')
    n = a['source_convention_gas_mj_ncv']
    if not isinstance(n, Decimal) or not n.is_finite() or n <= 0:
        raise ValueError('positive finite Decimal source NCV activity required')
    return a


def _mass(activity_mj, values):
    central, lower, upper = values
    tj = activity_mj / MJ_PER_TJ
    ends = sorted((tj * lower, tj * upper))
    return dict(activity_tj_ncv=tj, central_kg_co2=tj * central,
                factor_interval_lower_kg_co2=ends[0],
                factor_interval_upper_kg_co2=ends[1])


def _scope(manifest):
    return dict(
        reference_id=manifest['reference_id'], evidence_status='DER', evidence_tier='E2',
        factor=manifest['factor'],
        inventory_convention='TOTAL_FUEL_CARBON_EXPRESSED_AS_CO2_OXIDATION_ONE',
        uncertainty_scope='FACTOR_ONLY_AT_FIXED_SOURCE_CONVENTION_ACTIVITY',
        interval_is_hard_bound=False, interval_covers_total_model_uncertainty=False,
        observed_hungarian_emissions_kg_co2=None, net_heat_pump_climate_effect=None,
        electricity_emissions=None, upstream_fuel_emissions=None, refrigerant_emissions=None,
        ch4_n2o_or_co2e=None, health_effect=None, monetary_value=None,
        national_admission=False, whole_slice_complete=False,
        activity_validation_debt=manifest['activity_validation_debt'],
        factor_validation_debt=manifest['factor_validation_debt'])


def calculate_reference(*, package):
    """One named annual heating-only source case; no package is a default."""
    with localcontext(Context(prec=50)):
        manifest, values = _manifest()
        a = _activity(package)
        return dict(
            **_scope(manifest), package=package, variant_id=a['variant_id'],
            source_system_row=a['source_system_row'], activity_source_id=a['source_id'],
            activity_source_sha256=a['source_sha256'],
            activity_mj_ncv=a['source_convention_gas_mj_ncv'],
            activity_ncv_over_gcv=a['source_convention_ncv_over_gcv'],
            **_mass(a['source_convention_gas_mj_ncv'], values))


def compare_reference(*, from_package, to_package):
    """Signed source-case difference with ONE shared factor, not two draws.

Positive means the from-case exceeds the to-case. Native factor limits are
mapped through that signed energy difference; they are not independent case
intervals, confidence limits for actual retrofit savings or hard bounds.
"""
    with localcontext(Context(prec=50)):
        manifest, values = _manifest()
        before, after = _activity(from_package), _activity(to_package)
        delta = (before['source_convention_gas_mj_ncv']
                 - after['source_convention_gas_mj_ncv'])
        return dict(
            **_scope(manifest), from_package=from_package, to_package=to_package,
            comparison_scope='SIGNED_NAMED_GAS_SOURCE_CASE_DIFFERENCE_ONLY',
            shared_factor=True, factor_dependence='ONE_COMMON_FACTOR_PARAMETER',
            activity_difference_mj_ncv=delta, **_mass(delta, values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', choices=PACKAGES, required=True)
    args = parser.parse_args()
    print(json.dumps(calculate_reference(package=args.package),
                     default=str, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
