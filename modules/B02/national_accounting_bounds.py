"""Conditional 2022 count and source-accounting screens, never a heat estimate.

The source ledger equals target + nonnegative outside-target/coverage terms.
Projecting this relaxed set gives [0, ledger]. A nonempty selected count does
not tighten the energy cap without an evidenced heat/selection relationship.
Passing a necessary inequality is not proof of national feasibility.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
from pathlib import Path

from modules.B02 import annual_heat_reference as annual

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = 'registry/b02_national_accounting_bounds_manifest.json'
PROJECTION = 'WBL011_FULL_STOCK_JOINT'
POPULATIONS = ('NON_DISTRICT', 'CENSUS_GAS_ONLY', 'EXPLICIT_GAS_CODED_UNION')
QUANTITIES = ('GAS_SH_SERVICE', 'GAS_SH_FINAL_ENERGY', 'ALL_CARRIER_SH_SERVICE')
FUEL_CODES = frozenset(('FUEL11', 'FUEL12', 'FUEL13', 'FUEL14', 'FUEL21', 'FUEL22', 'FUEL23'))
HEATING_CODES = frozenset(('HEAT111', 'HEAT112', 'HEAT12', 'NHEAT'))
GAS_TES = 'TES.ktoe.HU.Res.HH.Thermal.SH.Gas.SH.Gas'
GAS_FEC = 'FEC.ktoe.HU.Res.HH.Thermal.SH.Gas.SH.Gas'
INPUTS = frozenset((
    'data/processed/b02/ksh_wbl_joint_cells_2022.csv',
    'data/processed/b02/ksh_wbl_joint_manifest.json',
    'data/processed/b02/jrc_sh_dhw_cohorts_2022_2023.csv',
    'data/processed/b02/jrc_household_controls_2022_2023.csv',
    'registry/b02_v1_annual_heat_admission.json',
))


def _count(value):
    if type(value) is not int or value < 0:
        raise ValueError('nonnegative integer dwelling count required')
    return value


def _decimal(value):
    if type(value) not in (int, str, Decimal):
        raise ValueError('exact finite nonnegative number required; binary floats not accepted')
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('exact finite nonnegative number required') from exc
    if not number.is_finite() or number < 0:
        raise ValueError('finite nonnegative number required')
    return number


def _interval(upper, unit):
    return {'lower': '0', 'upper': str(upper), 'unit': unit,
            'evidence_status': 'DER',
            'meaning': 'CONDITIONAL_OUTER_ACCOUNTING_BOUND_NOT_CONFIDENCE_INTERVAL',
            'positive_floor_identified': False, 'endpoint_attainability_established': False}


def _manifest():
    m = json.loads((ROOT / MANIFEST).read_text())
    if (m['reference_year'] != 2022 or m['geography'] != 'HU'
            or m['claim_scope'] != 'CONDITIONAL_NATIONAL_COUNT_AND_SOURCE_ACCOUNTING_SCREENS'
            or m['count_projection'] != PROJECTION or m['count_source_version'] != 'V67'
            or m['native_gas_service_code'] != GAS_TES or m['native_gas_final_code'] != GAS_FEC
            or m['energy_conversion']['ktoe_to_gwh'] != '11.63'
            or m['national_central_heat_admitted'] is not False
            or m['policy_defaults_selected'] is not False
            or set(m['input_artifacts']) != INPUTS):
        raise ValueError('reviewed 2022 accounting contract required')
    for path, digest in m['input_artifacts'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('accounting source identity mismatch: ' + path)
    admission = json.loads((ROOT / 'registry/b02_v1_annual_heat_admission.json').read_text())
    if set(m['validation_debt_ids']) != {x['id'] for x in admission['validation_debt']}:
        raise ValueError('all inherited annual heat debts must remain visible')
    return m


def _census():
    fuel = Counter()
    rows = occupied = district = 0
    cell_ids = set()
    with (ROOT / 'data/processed/b02/ksh_wbl_joint_cells_2022.csv').open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['projection_id'] != PROJECTION:
                continue
            if (row['reference_year'] != '2022' or row['occupancy_code'] != 'DW_OC'
                    or row['source_id'] != 'SRC-B02-KSH-CENSUS-API-2022'
                    or row['source_version'] != 'V67' or row['evidence_status'] != 'OBS'
                    or row['heating_mode_code'] not in HEATING_CODES
                    or (row['heating_fuel_code'] != 'FUEL3' if row['heating_mode_code'] == 'HEAT12'
                        else row['heating_fuel_code'] not in FUEL_CODES)
                    or row['cell_id'] in cell_ids):
                raise ValueError('unique observed 2022 full-joint census cells required')
            cell_ids.add(row['cell_id'])
            n = int(row['dwelling_count'])
            if n <= 0:
                raise ValueError('returned positive census count required; no zero fill')
            rows += 1
            occupied += n
            if row['heating_mode_code'] == 'HEAT12':
                district += n
            else:
                fuel[row['heating_fuel_code']] += n
    if (rows, occupied, district, sum(fuel.values())) != (116452, 4008541, 618724, 3389817):
        raise ValueError('observed census projection does not reconcile')
    return tuple(sorted(fuel.items()))


@dataclass(frozen=True)
class NationalAccountingReference:
    fuel_partition: tuple[tuple[str, int], ...]
    gas_service_gwh: Decimal
    gas_final_gwh: Decimal
    all_service_gwh: Decimal

    def population_count(self, population):
        fuel = dict(self.fuel_partition)
        counts = {'NON_DISTRICT': sum(fuel.values()), 'CENSUS_GAS_ONLY': fuel['FUEL11'],
                  'EXPLICIT_GAS_CODED_UNION': sum(fuel[x] for x in ('FUEL11', 'FUEL21', 'FUEL22'))}
        if population not in counts:
            raise ValueError('explicit supported census population required')
        return counts[population]

    def count_screen(self, required_dwellings, *, population):
        required = _count(required_dwellings)
        ceiling = self.population_count(population)
        return {'status': 'EXCLUDED_BY_CENSUS_COUNT' if required > ceiling else 'INCONCLUSIVE',
                'required_dwellings': required, 'population': population, 'count_ceiling': ceiling,
                'minimum_count_shortfall': max(0, required - ceiling), 'reference_year': 2022,
                'threshold_status': 'SCN_CALLER_SUPPLIED_NOT_ACTIVE_POLICY',
                'condition': 'Distinct dwellings restricted to this 2022 occupied non-district census group.',
                'does_not_establish': 'Current stock, technical/legal eligibility, willingness, rollout or national feasibility.'}

    def conditional_subset_bound(self, quantity, *, selected_dwellings, population):
        selected = _count(selected_dwellings)
        ceiling = self.population_count(population)
        if selected > ceiling:
            raise ValueError('selected count exceeds the declared census population')
        values = {'GAS_SH_SERVICE': self.gas_service_gwh, 'GAS_SH_FINAL_ENERGY': self.gas_final_gwh,
                  'ALL_CARRIER_SH_SERVICE': self.all_service_gwh}
        if quantity not in values:
            raise ValueError('explicit source-native quantity required')
        # No positive per-home floor or upper limit is evidenced by these ledgers.
        upper = values[quantity] if selected else Decimal(0)
        return {**_interval(upper, 'GWh/year'), 'quantity': quantity, 'population': population,
                'selected_dwellings': selected, 'reference_year': 2022,
                'condition': 'Selected energy is a nonnegative subset of this named native 2022 source ledger; census membership alone does not prove applicability.',
                'selection_rule': 'Zero for an empty group; whole ledger for every nonempty group, without pro-rata allocation.',
                'source_carrier': 'Natural gas and biogas' if quantity.startswith('GAS_') else 'All native non-district carriers',
                'central_value': None}

    def gas_saving_screen(self, required_gwh):
        required = _decimal(required_gwh)
        return {'status': 'EXCLUDED_IF_SOURCE_CONDITIONS_HOLD' if required > self.gas_final_gwh else 'INCONCLUSIVE',
                'required_gwh_per_year': str(required), 'source_cap_gwh_per_year': str(self.gas_final_gwh),
                'reference_year': 2022, 'threshold_status': 'SCN_CALLER_SUPPLIED_NOT_ACTIVE_POLICY',
                'source_carrier': 'Natural gas and biogas',
                'conditions': [
                    'Nonnegative target subset of native 2022 direct-gas SH final energy; same calorific/end-use/source boundary.',
                    'Nonnegative gross replacement savings; no added gas use; displacement only of this baseline direct-gas SH.'
                ],
                'positive_saving_floor_gwh_per_year': None,
                'does_not_establish': 'Actual savings, net energy, gas volume, import value, emissions, bills, fiscal benefits or national feasibility.'}

    def report(self, manifest):
        fuel = dict(self.fuel_partition)
        with localcontext() as context:
            context.prec = 50
            context.rounding = ROUND_CEILING
            numerator = self.gas_service_gwh * 1000000
            mean = numerator / fuel['FUEL11']
        return {
            'reference_id': manifest['reference_id'], 'reference_year': 2022,
            'status': manifest['claim_scope'], 'evidence_status': 'DER',
            'count_evidence': manifest['count_evidence'], 'energy_evidence': manifest['energy_evidence'],
            'population_counts': {x: self.population_count(x) for x in POPULATIONS},
            'census_fuel_partition': fuel,
            'ambiguous_FUEL23_gas_membership': 'UNRESOLVED; not added to the explicitly gas-coded union',
            'count_meaning': '2022 occupied non-district census groups; not annual gas-use membership or eligible/participating stock',
            'source_bounds': {q: self.conditional_subset_bound(q, selected_dwellings=self.population_count('NON_DISTRICT'), population='NON_DISTRICT') for q in QUANTITIES},
            'whole_census_gas_only_mean_gas_service': {
                **_interval(mean, 'kWh/dwelling/year'), 'denominator_dwellings': fuel['FUEL11'],
                'upper_rounding': 'ROUND_CEILING_AT_50_SIGNIFICANT_DIGITS',
                'upper_exact_ratio': {'numerator_gwh_times_1000000': str(numerator), 'denominator_dwellings': fuel['FUEL11']},
                'condition': 'Entire census gas-only group gas-derived SH is a source-ledger subset. Total SH interpretation additionally requires annual gas exclusivity.',
                'not_for_selected_group_scaling': True},
            'source_accounting_conditions': manifest['source_accounting_conditions'],
            'avoided_gas_additional_conditions': manifest['avoided_gas_additional_conditions'],
            'validation_debt_ids': manifest['validation_debt_ids'],
            'source_ids': manifest['source_ids'], 'input_artifacts': manifest['input_artifacts'],
            'central_heat_allocation': None, 'probability_distribution': None,
            'policy_defaults_selected': False, 'national_feasibility_verdict': 'INCONCLUSIVE',
            'joint_constraint': 'Gas-derived service is part of all-carrier service. Separate intervals do not authorize independent endpoints or a compatible portfolio.',
        }


def load_reference():
    """Hash-check existing admissions, then consume the original native cells."""
    manifest = _manifest()
    fuel = _census()
    with localcontext() as context:
        context.prec = 50
        # Reuse admitted cohort reconciliation and source-native conversions.
        ref = annual.annual_heat_reference()
        cells = annual.load_native_cells()
        gas = cells[2022, GAS_TES] * annual.GWH_PER_KTOE
        final = cells[2022, GAS_FEC] * annual.GWH_PER_KTOE
        if not Decimal(0) < gas <= ref.space_heating_excluding_circulation_gwh or final <= 0:
            raise ValueError('positive gas ledger nested within all-carrier service required')
    return NationalAccountingReference(fuel, gas, final, ref.space_heating_excluding_circulation_gwh), manifest


def calculate_reference():
    reference, manifest = load_reference()
    return reference.report(manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rollout-count', type=int)
    parser.add_argument('--population', choices=POPULATIONS)
    parser.add_argument('--gas-saving-gwh')
    args = parser.parse_args()
    if (args.rollout_count is None) != (args.population is None):
        parser.error('--rollout-count and --population must be supplied together')
    reference, manifest = load_reference()
    result = reference.report(manifest)
    try:
        if args.rollout_count is not None:
            result['count_screen'] = reference.count_screen(args.rollout_count, population=args.population)
        if args.gas_saving_gwh is not None:
            result['gas_saving_screen'] = reference.gas_saving_screen(args.gas_saving_gwh)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
