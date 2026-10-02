"""Source-bound current dwelling-area enclosures, not household heat allocation.

The reported KSH mean is observed at publication precision. Inverting that
precision is an explicit assumption. No point is selected inside a band and
the open upper tail stays open before applying the aggregate area budget.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTION = 'WBL011_FULL_STOCK_JOINT'
# Closed conservative enclosures; upper edges are not asserted observed maxima.
BANDS = {'SQM_LT30': (0, 30), 'SQM30-39': (30, 40),
         'SQM40-49': (40, 50), 'SQM50-59': (50, 60),
         'SQM60-79': (60, 80), 'SQM80-99': (80, 100),
         'SQM100-119': (100, 120), 'SQM_GE120': (120, None)}
CONVENTIONS = {'NEAREST_WHOLE_ASS': (Fraction(163, 2), Fraction(165, 2)),
               'WIDER_ROUNDING_SENSITIVITY': (Fraction(81), Fraction(83))}


def _pin(path, digest):
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('current-area source identity mismatch')
    return path


def _band_budget(counts):
    if not isinstance(counts, dict) or not counts:
        raise ValueError('explicit nonempty area-band counts required')
    minimum = 0
    maximum = 0
    n = 0
    for band, count in counts.items():
        if band not in BANDS or type(count) is not int or count < 0:
            raise ValueError('known area band and nonnegative integer count required')
        low, high = BANDS[band]
        n += count
        minimum += count * low
        if count and high is None:
            maximum = None
        elif maximum is not None and high is not None:
            maximum += count * high
    return n, Fraction(minimum), None if maximum is None else Fraction(maximum)


def _partition_bounds(selected, complement, total_low, total_high):
    """Project one coherent area budget; inputs are disjoint count partitions."""
    if any(type(v) not in (int, Fraction) for v in (total_low, total_high)):
        raise ValueError('finite exact area-budget endpoints required')
    total_low, total_high = Fraction(total_low), Fraction(total_high)
    if total_low < 0 or total_high < total_low:
        raise ValueError('ordered nonnegative area budget required')
    n, low, high = _band_budget(selected)
    other_n, other_low, other_high = _band_budget(complement)
    if not n or not other_n:
        raise ValueError('both population partitions must be nonempty')
    if total_high < low + other_low:
        raise ValueError('area budget below observed-band minimum')
    if high is not None and other_high is not None and total_low > high + other_high:
        raise ValueError('area budget above observed-band maximum')
    lower = low if other_high is None else max(low, total_low - other_high)
    upper = total_high - other_low if high is None else min(high, total_high - other_low)
    if upper < lower:
        raise ValueError('empty subgroup area set')
    return lower, upper


def _interval(low, high, count=1):
    return {'lower_exact': str(low / count), 'upper_exact': str(high / count),
            'lower': float(low / count), 'upper': float(high / count),
            'endpoints': 'CLOSED_CONSERVATIVE_ENCLOSURE'}


def calculate_reference():
    manifest = json.loads((ROOT / 'registry/b02_current_area_reference_manifest.json').read_text())
    if (manifest['reported_control']['reference_year'] != 2022
            or manifest['joint']['projection'] != PROJECTION
            or set(manifest['precision_interpretations']) != set(CONVENTIONS)):
        raise ValueError('reviewed population and precision interpretation required')
    for name, endpoints in CONVENTIONS.items():
        spec = manifest['precision_interpretations'][name]
        if (spec['status'] != 'ASS' or tuple(Fraction(x) for x in spec['mean_interval_m2']) != endpoints):
            raise ValueError('rounding interpretation metadata changed')
    joint = _pin(ROOT / manifest['joint']['path'], manifest['joint']['sha256'])
    history = _pin(ROOT / manifest['historical_diagnostic']['path'],
                   manifest['historical_diagnostic']['sha256'])
    groups = {name: Counter() for name in ('DISTRICT', 'NON_DISTRICT_GAS_ONLY', 'NON_DISTRICT_OTHER')}
    rows = 0
    with joint.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            if row['projection_id'] != PROJECTION:
                continue
            if (row['reference_year'] != '2022' or row['occupancy_code'] != 'DW_OC'
                    or row['source_id'] != 'SRC-B02-KSH-CENSUS-API-2022'
                    or row['evidence_status'] != 'OBS'):
                raise ValueError('occupied-2022 observed joint required')
            group = ('DISTRICT' if row['heating_mode_code'] == 'HEAT12' else
                     'NON_DISTRICT_GAS_ONLY' if row['heating_fuel_code'] == 'FUEL11' else
                     'NON_DISTRICT_OTHER')
            groups[group][row['floor_area_code']] += int(row['dwelling_count'])
            rows += 1
    all_counts = sum(groups.values(), Counter())
    observed = sum(all_counts.values())
    if rows != 116452 or observed != 4008541 or observed != manifest['reported_control']['occupied_dwellings']:
        raise ValueError('exact occupied population reconciliation failed')
    if manifest['reported_control']['published_mean_m2'] != 82:
        raise ValueError('source-native published mean changed')
    groups['NON_DISTRICT'] = groups['NON_DISTRICT_GAS_ONLY'] + groups['NON_DISTRICT_OTHER']
    prior = [row for row in json.loads(history.read_text()) if row['population_scope'] == 'ALL']
    if len(prior) != 4 or len({row['case'] for row in prior}) != 4:
        raise ValueError('four preserved historical experiments required')
    results = {}
    for convention, (mean_low, mean_high) in CONVENTIONS.items():
        total_low, total_high = observed * mean_low, observed * mean_high
        subset_results = {}
        for group, counts in groups.items():
            complement = all_counts - counts
            low, high = _partition_bounds(dict(counts), dict(complement), total_low, total_high)
            count = sum(counts.values())
            subset_results[group] = {'dwellings': count, 'total_area_m2': _interval(low, high),
                                     'mean_area_m2': _interval(low, high, count),
                                     'band_counts': dict(sorted(counts.items()))}
        comparisons = []
        for row in prior:
            if row['observed_dwellings'] != observed or row['area_transfer_status'] != 'ASS_2011_TYPE_MEANS_ON_2022_COUNTS_NOT_CURRENT_OBSERVATION':
                raise ValueError('historical comparison population or meaning changed')
            area = Fraction(str(row['historical_dwelling_area_exposure_m2']))
            comparisons.append({'case': row['case'], 'historical_exposure_m2': float(area),
                                'compatible_with_current_area_set': total_low <= area <= total_high,
                                'shortfall_to_lower_m2': float(max(Fraction(0), total_low - area))})
        results[convention] = {'rounding_status': 'ASS', 'national_area_m2': _interval(total_low, total_high),
                               'groups': subset_results, 'historical_experiments': comparisons}
    return {'reference_id': manifest['reference_id'], 'evidence_status': 'DER',
            'evidence_tier': 'E2_PROVISIONAL_BASE', 'model_use_status': 'SCOPED_AREA_BOUNDS_ONLY',
            'reported_control': manifest['reported_control'], 'observed_joint_rows': rows,
            'interpretations': results, 'validation_debt': manifest['validation_debt'],
            'interval_meaning': 'Conditional identification enclosures, not statistical confidence intervals',
            'joint_constraint': 'All subgroup bounds share one national budget; their extremes cannot be selected independently',
            'cell_area_means': None, 'heated_area_m2': None, 'annual_useful_heat_kwh': None,
            'national_heat_admission': False, 'type_weights_changed': False,
            'automatic_national_rescaling': False}
