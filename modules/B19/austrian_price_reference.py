"""Pinned Austrian SMARD observations, independently identified and validated.

Only pure exact-number/JSON/label helpers are shared with B04. Its HU reader,
configuration authority and valuation path are never relabelled or invoked.
Original bytes and genuine numeric outputs stay in private caller storage.
"""
from __future__ import annotations

from collections import Counter
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction
import hashlib
import io
from pathlib import Path
from zoneinfo import ZoneInfo

from modules.B04 import wholesale_reference as hu

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b19_joint_market_reference_manifest.json'
MANIFEST_SHA256 = '01f7fc2d00722be7a4e99770eda81efaf140df4b3a0fcc45ce4e99aea9b1645a'
REFERENCE_ID = 'B19-HU-AT-JOINT-MARKET-UTC2025-V1'
AT = ZoneInfo('Europe/Vienna')
HOUR, QUARTER, EPOCH = hu.HOUR, hu.QUARTER, hu.EPOCH
_require, _json, exact = hu._require, hu._json, hu.exact


def source_manifest():
    raw = MANIFEST.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256, 'pinned joint market manifest required')
    m = _json(raw)
    a = m['at']
    _require(m['schema_version'] == 1 and m['reference_id'] == REFERENCE_ID
             and m['domain'] == 'utc2025' and m['window_hours_default'] is None
             and m['probabilities'] is None and m['policy_defaults_selected'] is False
             and m['national_admission'] is False and m['public_source_publication_authorized'] is False,
             'bounded explicit-duration UTC2025 contract required')
    _require(a['bidding_zone'] == 'AT' and a['module_id'] == 8004170 and a['data_id'] == 4170
             and a['currency'] == 'EUR' and a['price_unit'] == 'EUR/MWh'
             and a['timezone'] == 'Europe/Vienna', 'qualified Austrian field identity required')
    for path, digest in m['authority_sha256'].items():
        _require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest,
                 'unchanged inherited authority required: ' + path)
    return m


def _configuration(raw):
    doc = _json(raw)
    _require(doc.get('meta_data', {}).get('version') == 1, 'configuration version required')
    matches = []
    def visit(value):
        if isinstance(value, dict):
            if value.get('id') == 8004170:
                matches.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(doc)
    _require(len(matches) == 1, 'unique Austrian module required')
    field = matches[0]
    _require(field.get('data_id') == 4170 and field.get('name') == 'MM-Bausteine.Österreich'
             and field.get('unit') == 'VD-Einheit.Euro/MWh'
             and field.get('source_resolution') == 'quarterhour'
             and 'DE-LU' in field.get('region', []),
             'Austria identity/currency/resolution required; display region is not bidding zone')


@dataclass(frozen=True)
class AustrianHour:
    start_utc: datetime
    end_utc: datetime
    source_start_label: str
    source_end_label: str
    source_price_lexeme: str
    price_eur_per_mwh: Fraction
    source_id: str
    source_end_label_anomaly: bool


def _parse_csv(raw, pin, *, start, end):
    duration = timedelta(minutes=pin['duration_minutes'])
    field = 'Austria [€/MWh] ' + ('Calculated resolutions' if duration == HOUR else 'Original resolutions')
    _require(duration in (HOUR, QUARTER) and pin['field'] == field
             and hu._utc(end) > hu._utc(start) and (end-start) % duration == timedelta(0)
             and pin['rows'] == (end-start)//duration, 'Austrian field and complete physical grid required')
    result = []
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';', strict=True)
        _require(next(reader, None) == ['Start date', 'End date', field], 'exact Austrian EUR/MWh CSV field required')
        for i, row in enumerate(reader):
            _require(len(row) == 3 and i < pin['rows'], 'malformed or extra Austrian row')
            local_a, local_b = map(hu._local_label, row[:2])
            # Independently decode valid local folds. The requested physical grid
            # resolves the repeated autumn label; nonexistent spring labels fail.
            candidates = set()
            for fold in (0, 1):
                candidate = local_a.replace(tzinfo=AT, fold=fold).astimezone(hu.UTC)
                if candidate.astimezone(AT).replace(tzinfo=None) == local_a:
                    candidates.add(candidate)
            a = start + i*duration
            b = a + duration
            _require(a in candidates, 'Austrian start gap, duplicate, shift or nonexistent local time')
            _require(local_b == local_a+duration, 'Austrian source naive end-label convention required')
            _require(hu.PRICE.fullmatch(row[2]) is not None, 'finite signed cent-price lexeme required')
            result.append(AustrianHour(a, b, row[0], row[1], row[2], hu._number(row[2]),
                                      pin['source_id'], local_b != b.astimezone(AT).replace(tzinfo=None)))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError('well-formed Austrian CSV required') from exc
    _require(len(result) == pin['rows'], 'incomplete Austrian source')
    return tuple(result)


def _witnesses(raw_sources, pins, quarters, index_id):
    index = _json(raw_sources[index_id])
    index_pin = next(p for p in pins if p['source_id'] == index_id)
    _require(set(index) == {'timestamps'} and type(index['timestamps']) is list
             and len(index['timestamps']) == index_pin['timestamp_count']
             and all(type(n) is int for n in index['timestamps'])
             and index['timestamps'] == sorted(set(index['timestamps'])), 'complete ordered Austrian series index required')
    lookup = {int((r.start_utc-EPOCH)//timedelta(milliseconds=1)): r.price_eur_per_mwh for r in quarters}
    seen, overlap_epochs, reports = set(), set(), []
    for pin in pins:
        if pin['intended_use'] != 'PHYSICAL_UTC_EPOCH_WITNESS':
            continue
        doc = _json(raw_sources[pin['source_id']])
        _require(pin['first_epoch_ms'] in index['timestamps'], 'Austrian witness must be in original index')
        _require(set(doc) == {'meta_data', 'series'} and doc['meta_data'] == pin['file_generation_metadata']
                 and type(doc['series']) is list and len(doc['series']) == pin['points'],
                 'Austrian witness schema/generation/count required')
        overlap = 0
        for i, pair in enumerate(doc['series']):
            _require(type(pair) is list and len(pair) == 2 and type(pair[0]) is int
                     and pair[0] == pin['first_epoch_ms']+i*900000 and pair[0] not in seen,
                     'Austrian epoch gap, duplicate or order mismatch')
            seen.add(pair[0])
            price = hu._number(pair[1])
            if pair[0] in lookup:
                _require(price == lookup[pair[0]], 'Austrian epoch/CSV exact-price mismatch')
                overlap += 1; overlap_epochs.add(pair[0])
        reports.append({'source_id': pin['source_id'], 'exact_overlapping_quarters': overlap,
                        'file_generation_metadata': doc['meta_data'], 'http_headers': pin['http_headers']})
    _require(len(reports) == 5 and len(overlap_epochs) == 2976, 'all five Austrian boundary/DST/transition witnesses required')
    return reports


def _reconcile(hours, quarters, transition):
    _require(len(quarters) == 4*len(hours) and hours, 'complete Austrian hourly/quarter pair required')
    differences, varying = [], []
    for i, hour in enumerate(hours):
        q = quarters[4*i:4*i+4]
        _require(hour.end_utc == hour.start_utc+HOUR
                 and all(r.start_utc == hour.start_utc+j*QUARTER and r.end_utc == r.start_utc+QUARTER
                         for j, r in enumerate(q)), 'Austrian native/hour physical alignment required')
        prices = [r.price_eur_per_mwh for r in q]
        difference = hour.price_eur_per_mwh-sum(prices, Fraction(0))/4
        _require(abs(difference) <= Fraction(1,200), 'Austrian cent-quantization reconciliation exceeded')
        if hour.start_utc < transition:
            _require(len(set(prices)) == 1, 'pretransition Austrian quarters must repeat hourly auction')
        elif len(set(prices)) > 1:
            varying.append(hour.start_utc)
        differences.append(difference)
    _require(varying and varying[0] == transition, 'Austrian native auction transition must match exactly')
    return {'hours_compared': len(hours), 'nonzero_rounding_differences': sum(bool(d) for d in differences),
            'max_abs_mean_difference_eur_per_mwh': exact(max(map(abs, differences))),
            'signed_hourly_minus_quarter_mean_eur_per_mwh': [exact(d) for d in differences],
            'posttransition_varying_hours': len(varying), 'first_varying_hour_utc': varying[0].isoformat(),
            'tie_rounding': 'UNKNOWN', 'unrounded_prices_recovered': False}


@dataclass(frozen=True)
class AustrianReference:
    window: str
    records: tuple[AustrianHour, ...]
    evidence: dict
    reconciliation: dict


def read_austrian_reference(source_paths, *, window):
    """Exhaust every pinned source before returning the explicit UTC2025 domain."""
    _require(window == 'utc2025' and type(window) is str, 'explicit utc2025 domain required')
    m = source_manifest(); a = m['at']
    sources = hu._source_bytes(source_paths, a)
    pins = {p['source_id']: p for p in a['source_artifacts']}
    _configuration(sources['SRC-B04-SMARD-CONFIG-20261003'])
    start, end = map(hu._endpoint, a['padded_window_utc'])
    panels = []
    for sid, resolution in ((a['price_source_id'], 'hour'), (a['native_source_id'], '')):
        pin = pins[sid]
        expected = {'request_form': [{'moduleIds': [8004170], 'region': 'DE-LU', 'resolution': resolution,
                    'format': 'CSV', 'timestamp_from': (start-EPOCH)//timedelta(milliseconds=1),
                    'timestamp_to': (end-EPOCH)//timedelta(milliseconds=1), 'type': 'discrete', 'language': 'en'}]}
        _require(pin['export_request'] == expected, 'exact Austrian export request required')
        panels.append(_parse_csv(sources[sid], pin, start=start, end=end))
    hours, quarters = panels
    witnesses = _witnesses(sources, a['source_artifacts'], quarters, a['index_source_id'])
    reconciliation = _reconcile(hours, quarters, hu._endpoint(a['native_auction_transition_utc']))
    for rows, counts in ((hours, (23,25)), (quarters, (92,100))):
        days = Counter(r.start_utc.astimezone(AT).date().isoformat() for r in rows)
        _require((days['2025-03-30'], days['2025-10-26']) == counts
                 and sum(r.source_end_label_anomaly for r in rows) == 2,
                 'complete Austrian DST folds and preserved end anomalies required')
    begin, finish = map(hu._endpoint, m['window_utc'])
    selected = tuple(r for r in hours if begin <= r.start_utc < finish)
    _require(len(selected) == 8760 and selected[0].start_utc == begin and selected[-1].end_utc == finish,
             'complete Austrian UTC2025 domain required')
    evidence = {k: a[k] for k in ('bidding_zone','currency','price_unit','price_source_id','as_of_meaning',
                'original_auction_vintage','per_record_revision','required_attribution','license_url','rights_scope',
                'source_artifacts','native_auction_transition_utc','source_precision_eur_per_mwh')}
    evidence.update(source_id=a['price_source_id'], retrieved_at=pins[a['price_source_id']]['retrieved_at'],
                    manifest_sha256=MANIFEST_SHA256, window=window, start_utc=begin.isoformat(),
                    end_utc_exclusive=finish.isoformat(), price_evidence='OBS_PUBLISHER_CALCULATED_HOURLY_SOURCE',
                    physical_end_evidence='DER_FROM_IDENTIFIED_START_PLUS_DURATION',
                    changes='UTC2025 selection; physical ends derived; all labels/lexemes retained; no clipping or imputation')
    reconciliation.update(epoch_witnesses=witnesses, epoch_overlapping_quarters=2976,
                          selected_hours=len(selected), hourly_source_end_label_anomalies=2,
                          quarter_source_end_label_anomalies=2, missing_prices=0, imputation=False)
    return AustrianReference(window, selected, evidence, reconciliation)


def normalized_record(row):
    return {'start_utc': row.start_utc.isoformat(), 'end_utc': row.end_utc.isoformat(),
            'start_local': row.start_utc.astimezone(AT).isoformat(), 'end_local': row.end_utc.astimezone(AT).isoformat(),
            'source_start_label': row.source_start_label, 'source_end_label': row.source_end_label,
            'source_price_lexeme': row.source_price_lexeme, 'price_eur_per_mwh': exact(row.price_eur_per_mwh),
            'source_id': row.source_id, 'source_end_label_anomaly': row.source_end_label_anomaly,
            'physical_end_evidence': 'DER_FROM_IDENTIFIED_START_PLUS_DURATION'}
