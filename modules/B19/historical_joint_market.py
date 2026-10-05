"""Actual dated HU weather/load/signed-supply and HU–AT market coincidence.

A finite-domain descriptive comparison, with explicit caller duration. Price
means are unweighted time means, never energy-price products or imports.
All source iterators finish validation before any result is returned.
"""
from __future__ import annotations

from collections import Counter, deque
from fractions import Fraction
from itertools import combinations

from modules.B04 import wholesale_reference as hu
from modules.B19 import historical_joint_stress as joint
from modules.B19 import austrian_price_reference as at

CRITERIA = {**joint.CRITERIA,
            'HIGHEST_MEAN_HU_PRICE': ('hu_price_sum', 'max'),
            'HIGHEST_MEAN_AT_PRICE': ('at_price_sum', 'max')}
FIELDS = ('temperature_sum_c', *joint.ENERGY_FIELDS, 'hu_price_sum', 'at_price_sum', 'hu_minus_at_spread_sum')
PRICE_FIELDS = FIELDS[-3:]
_require = joint._require


def _price_rows(rows, *, source_id, start, end):
    """Consume including final generator validation; prohibit civil-year drift."""
    result = []
    for i, row in enumerate(rows):
        a = start+i*joint.HOUR
        _require(a < end and hu._utc(row.start_utc) == a and hu._utc(row.end_utc) == a+joint.HOUR,
                 'price gap, duplicate, extra, shifted endpoint or wrong physical duration')
        _require(row.source_id == source_id and type(row.source_price_lexeme) is str
                 and hu.PRICE.fullmatch(row.source_price_lexeme) is not None,
                 'correct zone source and unchanged signed cent-price lexeme required')
        _require(hu._number(row.price_eur_per_mwh) == hu._number(row.source_price_lexeme),
                 'price value must exactly retain source lexeme')
        result.append(row)
    _require(len(result) == (end-start)//joint.HOUR, 'complete exact price domain required')
    return tuple(result)


def _rank_maps(values):
    result = {}
    for field in FIELDS:
        counts = Counter(row[field] for row in values)
        lower = 0; mapping = {}
        for value in sorted(counts):
            equal = counts[value]
            mapping[value] = {'lower_windows': lower, 'equal_windows_including_self': equal,
                              'higher_windows': len(values)-lower-equal,
                              'ascending_rank_first': lower+1, 'ascending_rank_last': lower+equal}
            lower += equal
        result[field] = mapping
    return result


def _coverage(indices, duration):
    """Union of selected integer-hour half-open intervals, never tie Cartesian products."""
    runs = []
    for i in indices:
        if runs and i <= runs[-1][1]:
            runs[-1][1] = max(runs[-1][1], i+duration)
        else:
            runs.append([i, i+duration])
    return runs


def _intersection(left, right):
    result = []; i = j = 0
    while i < len(left) and j < len(right):
        a, b = max(left[i][0],right[j][0]), min(left[i][1],right[j][1])
        if a < b:
            result.append([a,b])
        if left[i][1] <= right[j][1]:
            i += 1
        else:
            j += 1
    return result


def _dated_runs(runs, start):
    return [{'start_utc': (start+a*joint.HOUR).isoformat(),
             'end_utc_exclusive': (start+b*joint.HOUR).isoformat(), 'hours': b-a} for a,b in runs]


def _summarize(grid_rows, weather, hu_rows, at_rows, *, hu_source_id, at_source_id,
               window_hours, start, end):
    n = joint._duration(window_hours, start=start, end=end)
    # Tuples force even post-final-yield validation before construction of results.
    grid = tuple(joint._joined_hours(grid_rows, weather, start=start, end=end))
    hprices = _price_rows(hu_rows, source_id=hu_source_id, start=start, end=end)
    aprices = _price_rows(at_rows, source_id=at_source_id, start=start, end=end)
    _require(len(grid) == n, 'complete physical joint grid required')
    vectors = [dict(zip(FIELDS, (g.temperature_c, *g.energies_mwh, hu._number(h.price_eur_per_mwh),
                               hu._number(a.price_eur_per_mwh), hu._number(h.price_eur_per_mwh)-hu._number(a.price_eur_per_mwh))))
               for g,h,a in zip(grid,hprices,aprices)]
    queue, sources, signs = deque(), Counter(), Counter()
    sums = {k: Fraction(0) for k in FIELDS}
    minima = {k: deque() for k in PRICE_FIELDS}; maxima = {k: deque() for k in PRICE_FIELDS}
    windows, scores = [], []
    for i, (row, vector) in enumerate(zip(grid, vectors)):
        queue.append(row); sources[row.weather_source_id] += 1
        spread = vector['hu_minus_at_spread_sum']; signs[(spread>0)-(spread<0)] += 1
        for key in FIELDS:
            sums[key] += vector[key]
        for key in PRICE_FIELDS:
            while minima[key] and vectors[minima[key][-1]][key] > vector[key]:
                minima[key].pop()
            while maxima[key] and vectors[maxima[key][-1]][key] < vector[key]:
                maxima[key].pop()
            minima[key].append(i); maxima[key].append(i)
        if len(queue) > window_hours:
            old = i-window_hours
            removed = queue.popleft(); sources[removed.weather_source_id] -= 1
            previous = vectors[old]['hu_minus_at_spread_sum']; signs[(previous>0)-(previous<0)] -= 1
            for key in FIELDS:
                sums[key] -= vectors[old][key]
            for key in PRICE_FIELDS:
                if minima[key][0] == old:
                    minima[key].popleft()
                if maxima[key][0] == old:
                    maxima[key].popleft()
        if len(queue) == window_hours:
            record = joint._window_record(queue, sums, sources)
            record['window_index'] = i-window_hours+1
            record['hour_indices_half_open'] = [i-window_hours+1,i+1]
            record['market_eur_per_mwh'] = {
                name: {'arithmetic_time_mean': hu.exact(sums[key]/window_hours),
                       'min_hourly': hu.exact(vectors[minima[key][0]][key]),
                       'max_hourly': hu.exact(vectors[maxima[key][0]][key])}
                for name,key in zip(('HU','AT','HU_MINUS_AT'),PRICE_FIELDS)}
            record['spread_hour_counts'] = {'negative': signs[-1], 'equal': signs[0], 'positive': signs[1]}
            windows.append(record); scores.append(dict(sums))
    _require(len(windows) == n-window_hours+1, 'complete contiguous-window enumeration required')
    ranks = _rank_maps(scores)
    for record, score in zip(windows,scores):
        record['descriptive_same_domain_ranks'] = {key: ranks[key][score[key]] for key in FIELDS}
    criteria, coverage = {}, {}
    for name,(key,direction) in CRITERIA.items():
        best = (min if direction=='min' else max)(v[key] for v in scores)
        selected = [i for i,v in enumerate(scores) if v[key] == best]
        coverage[name] = _coverage(selected, window_hours)
        criteria[name] = {'direction': direction, 'score_field': key, 'ties': len(selected),
                          'mean_score': joint._exact(best/window_hours), 'window_indices': selected,
                          'selected_hour_coverage_union': _dated_runs(coverage[name],start)}
    overlaps = []
    for left,right in combinations(CRITERIA,2):
        runs = _intersection(coverage[left],coverage[right])
        overlaps.append({'left_criterion':left, 'right_criterion':right,
                         'shared_selected_window_count':len(set(criteria[left]['window_indices']) & set(criteria[right]['window_indices'])),
                         'coverage_union_intersection_hours':sum(b-a for a,b in runs),
                         'coverage_union_intersection':_dated_runs(runs,start)})
    hours = []
    for i,(g,h,a) in enumerate(zip(grid,hprices,aprices)):
        hours.append({'hour_index':i, 'start_utc':g.start.isoformat(), 'end_utc_exclusive':g.end.isoformat(),
                      'temperature_c':hu.exact(g.temperature_c), 'weather_source_id':g.weather_source_id,
                      'energy_mwh':{k:hu.exact(v) for k,v in zip(joint.ENERGY_FIELDS,g.energies_mwh)},
                      'HU':hu.normalized_record(h), 'AT':at.normalized_record(a),
                      'signed_hu_minus_at_eur_per_mwh':hu.exact(hu._number(h.price_eur_per_mwh)-hu._number(a.price_eur_per_mwh))})
    return {'hours':n, 'quarter_hour_intervals':4*n, 'windows_evaluated':len(windows),
            'window_hours':window_hours, 'start_utc':start.isoformat(), 'end_utc_exclusive':end.isoformat(),
            'annual_mean_temperature_c':joint._exact(sum((r.temperature_c for r in grid),Fraction(0))/n),
            'annual_energy_mwh':{k:joint._exact(sum((r.energies_mwh[j] for r in grid),Fraction(0)))
                                 for j,k in enumerate(joint.ENERGY_FIELDS)},
            'hourly_observations':hours, 'windows':windows, 'criteria':criteria, 'selector_temporal_overlap':overlaps,
            'rank_meaning':'Exact within the same duration/domain; ties include self; no probability or independent samples',
            'overlap_meaning':'Intersection of the physical-hour coverage unions of ALL tied selected windows; not pairwise overlap totals',
            'market_meaning':'Arithmetic time means of released hourly observations and signed HU minus AT differences; no energy-price products'}


def calculate_reference(source_paths, handoff_paths, *, weather_path, hu_source_paths, at_source_paths,
                        window, window_hours):
    """Read every original through its pinned consumer; no valuation is called."""
    _require(type(window) is str and window == 'utc2025', 'explicit utc2025 joint domain required')
    joint._duration(window_hours,start=joint.historical.START,end=joint.historical.END)
    m = at.source_manifest(); physical = joint._contract()
    start,end = map(hu._endpoint,m['window_utc'])
    _require((start,end) == (joint.historical.START,joint.historical.END), 'unchanged UTC2025 physical domain required')
    weather = joint._weather(weather_path,physical['weather'])
    hp = hu.read_wholesale_reference(hu_source_paths,window=window)
    ap = at.read_austrian_reference(at_source_paths,window=window)
    for zone,reference in (('HU',hp),('AT',ap)):
        evidence = reference.evidence
        _require(reference.window == window and evidence['bidding_zone'] == zone
                 and evidence['currency'] == 'EUR' and evidence['price_unit'] == 'EUR/MWh'
                 and hu._endpoint(evidence['start_utc']) == start and hu._endpoint(evidence['end_utc_exclusive']) == end,
                 'explicit same-domain geography/currency price handoff required')
    result = _summarize(joint.historical.iter_historical_source_balance(source_paths,handoff_paths),weather,
                        hp.records,ap.records,hu_source_id=hp.evidence['source_id'],at_source_id=ap.evidence['source_id'],
                        window_hours=window_hours,start=start,end=end)
    return {'reference_id':at.REFERENCE_ID, 'manifest_sha256':at.MANIFEST_SHA256, 'model_use':m['model_use'],
            'evidence_status':'DER', 'evidence_tier':joint.historical.EVIDENCE_TIER,
            'window_definition_status':'CALLER_DECLARED_ANALYSIS_WINDOW_NOT_POLICY',
            'physical_source_evidence':physical['source_evidence'], 'physical_validation_debt':physical['validation_debt'],
            'spatial_boundary':physical['spatial_boundary'], 'HU_price_evidence':hp.evidence, 'AT_price_evidence':ap.evidence,
            'HU_price_reconciliation':hp.reconciliation, 'AT_price_reconciliation':ap.reconciliation,
            'retrieval_vintage_relation':'SEPARATE_RETROSPECTIVE_REQUESTS_NOT_ATOMIC_TWO_ZONE_VINTAGE',
            'regional_interpretation':'One EU bidding-zone market comparison, not physical imports, flows or support',
            'supply_interpretation':'Load minus signed generation is a source-reference residual, not measured imports or complete physical accounting',
            'uncertainty':m['uncertainty'], 'excluded_claims':m['excluded_claims'],
            'policy_defaults_selected':False, 'probabilities':None, 'national_feasibility_verdict':None,
            'originals_republished':False, 'valuation_performed':False, 'result':result}
