"""Pinned HU publisher-hourly wholesale observations and explicit reference cost.

Bundesnetzagentur | SMARD.de; numerical market data licensed CC BY 4.0.
No network, tariff substitution, policy default or arbitrary intra-hour pricing.
Source lexemes remain unchanged; physical endpoints are identified/derived.
All real numeric results are private and must not be published automatically.
"""
from __future__ import annotations

from collections import Counter
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b04_wholesale_reference_manifest.json'
MANIFEST_SHA256 = 'e7363f2593717bfe65353fc1e1cdf93aa675743f2c0702ffbaccd5adb4df9a90'
REFERENCE_ID = 'B04-HU-SMARD-WHOLESALE-REFERENCE-20261003-V1'
CONVENTION = 'CALLER_DECLARED_HOURLY_FLAT_WHOLESALE_ENERGY_ONLY_REFERENCE'
UTC = timezone.utc
HU = ZoneInfo('Europe/Budapest')
HOUR = timedelta(hours=1)
QUARTER = timedelta(minutes=15)
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
PRICE = re.compile(r'-?(?:0|[1-9][0-9]*)\.[0-9]{2}\Z')
NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')
LABEL = re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) ([1-9]|[12][0-9]|3[01]), ([0-9]{4}) (1[0-2]|[1-9]):([0-5][0-9]) (AM|PM)\Z')
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


class WholesaleReferenceError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise WholesaleReferenceError(message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def _json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique, parse_float=Decimal,
                          parse_constant=lambda _: (_ for _ in ()).throw(WholesaleReferenceError('nonfinite JSON number')))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WholesaleReferenceError('valid UTF-8 JSON required') from exc


def _utc(value):
    _require(isinstance(value, datetime) and value.tzinfo is not None
             and value.utcoffset() == timedelta(0), 'explicit UTC endpoint required')
    return value


def _endpoint(value):
    _require(type(value) is str, 'UTC endpoint text required')
    try:
        return _utc(datetime.fromisoformat(value.replace('Z', '+00:00')))
    except ValueError as exc:
        raise WholesaleReferenceError('valid UTC endpoint required') from exc


def _number(value, *, nonnegative=False):
    _require(type(value) in (str, int, Decimal, Fraction), 'exact decimal or rational quantity required; floats/bools forbidden')
    try:
        if isinstance(value, str):
            _require(NUMBER.fullmatch(value) is not None, 'finite decimal text required')
            value = Decimal(value)
        if isinstance(value, Decimal):
            _require(value.is_finite(), 'finite exact quantity required')
        result = Fraction(value)
    except (ValueError, OverflowError, InvalidOperation, ZeroDivisionError) as exc:
        raise WholesaleReferenceError('finite exact quantity required') from exc
    _require(not nonnegative or result >= 0, 'imported energy must be nonnegative')
    return result


def exact(value):
    """JSON representation is an exact reduced rational, with no rounded display."""
    value = _number(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def source_manifest():
    raw = MANIFEST.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256, 'reviewed wholesale manifest hash required')
    m = _json(raw)
    _require(m['schema_version'] == 1 and m['reference_id'] == REFERENCE_ID
             and m['model_use'] == CONVENTION and m['bidding_zone'] == 'HU'
             and m['module_id'] == 8000262 and m['data_id'] == 262
             and m['currency'] == 'EUR' and m['price_unit'] == 'EUR/MWh'
             and m['public_source_publication_authorized'] is False,
             'qualified HU wholesale version/identity/currency required')
    return m


def source_map(path):
    entries = _json(Path(path).read_bytes())
    _require(type(entries) is dict and all(type(k) is str and type(v) is str and v for k, v in entries.items()),
             'explicit source-ID to local-path object required')
    return {k: Path(v) for k, v in entries.items()}


def _source_bytes(source_paths, manifest):
    pins = manifest['source_artifacts']
    _require(type(source_paths) is dict and set(source_paths) == {s['source_id'] for s in pins},
             'exact qualified source-ID/path set required')
    result = {}
    for pin in pins:
        path = source_paths[pin['source_id']]
        _require(isinstance(path, (str, Path)) and bool(str(path)), 'explicit local source path required')
        raw = Path(path).read_bytes()
        _require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
                 'source revision/length drift: ' + pin['source_id'])
        result[pin['source_id']] = raw
    return result


def _local_label(value):
    match = LABEL.fullmatch(value)
    _require(match is not None, 'malformed source time label')
    month, day, year, hour, minute, meridiem = match.groups()
    try:
        return datetime(int(year), MONTHS.index(month) + 1, int(day),
                        int(hour) % 12 + (12 if meridiem == 'PM' else 0), int(minute))
    except ValueError as exc:
        raise WholesaleReferenceError('invalid source calendar label') from exc


@dataclass(frozen=True)
class WholesaleHour:
    start_utc: datetime
    end_utc: datetime
    source_start_label: str
    source_end_label: str
    source_price_lexeme: str
    price_eur_per_mwh: Fraction
    source_id: str
    source_end_label_anomaly: bool


def _parse_csv(raw, pin, *, start, end):
    """Private parser; callers cannot admit alternate prices through the public API."""
    duration = timedelta(minutes=pin['duration_minutes'])
    _require(duration in (HOUR, QUARTER) and _utc(end) > _utc(start)
             and (end - start) % duration == timedelta(0), 'qualified physical source grid required')
    _require(pin['rows'] == (end - start) // duration, 'source count/boundary mismatch')
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';', strict=True)
        _require(next(reader, None) == ['Start date', 'End date', pin['field']], 'exact HU price field/header required')
        out = []
        for i, row in enumerate(reader):
            _require(len(row) == 3 and i < pin['rows'], 'malformed or extra source row')
            a = start + i * duration
            b = a + duration
            local_a = a.astimezone(HU).replace(tzinfo=None)
            local_b = b.astimezone(HU).replace(tzinfo=None)
            sa, sb = _local_label(row[0]), _local_label(row[1])
            _require(sa == local_a, 'source gap, duplicate, order or start-label mismatch')
            # SMARD end clocks use naive addition, including its two DST anomalies.
            _require(sb == sa + duration, 'unexpected source end-label convention')
            _require(PRICE.fullmatch(row[2]) is not None, 'missing/malformed/nonfinite source price')
            out.append(WholesaleHour(a, b, row[0], row[1], row[2],
                                     _number(row[2]), pin['source_id'], sb != local_b))
    except (UnicodeError, csv.Error) as exc:
        raise WholesaleReferenceError('well-formed source CSV required') from exc
    _require(len(out) == pin['rows'], 'incomplete source rows')
    return tuple(out)


def _configuration(raw):
    config = _json(raw)
    _require(config.get('meta_data', {}).get('version') == 1, 'qualified configuration version required')
    matches = []
    def visit(item):
        if isinstance(item, dict):
            if item.get('id') == 8000262:
                matches.append(item)
            for value in item.values():
                visit(value)
        elif isinstance(item, list):
            for value in item:
                visit(value)
    visit(config)
    _require(len(matches) == 1, 'unique HU source module required')
    item = matches[0]
    _require(item.get('data_id') == 262 and item.get('name') == 'MM-Bausteine.Ungarn'
             and item.get('unit') == 'VD-Einheit.Euro/MWh'
             and item.get('source_resolution') == 'quarterhour' and 'DE-LU' in item.get('region', []),
             'HU module/data identity and EUR/MWh required; display region is not price zone')


def _epochs(raw_sources, pins, quarters):
    lookup = {int((r.start_utc - EPOCH) // timedelta(milliseconds=1)): r.price_eur_per_mwh for r in quarters}
    total = 0
    results = []
    for pin in pins:
        if pin['intended_use'] != 'PHYSICAL_UTC_EPOCH_WITNESS':
            continue
        doc = _json(raw_sources[pin['source_id']])
        _require(set(doc) == {'meta_data', 'series'} and doc['meta_data'] == pin['file_generation_metadata']
                 and type(doc['series']) is list and len(doc['series']) == pin['points'],
                 'qualified epoch witness schema/generation required')
        overlap = 0
        for i, point in enumerate(doc['series']):
            _require(type(point) is list and len(point) == 2 and type(point[0]) is int
                     and point[0] == pin['first_epoch_ms'] + i * 900000,
                     'epoch witness gap, duplicate or malformed point')
            price = _number(point[1])
            if point[0] in lookup:
                _require(lookup[point[0]] == price, 'epoch witness/source price mismatch')
                overlap += 1
        total += overlap
        results.append({'source_id': pin['source_id'], 'exact_overlapping_quarters': overlap,
                        'file_generation_metadata': doc['meta_data'], 'http_headers': pin['http_headers']})
    _require(len(results) == 5 and total == 2976, 'complete qualified five-week epoch witnesses required')
    return results


def _reconcile(hours, quarters, transition):
    _require(len(quarters) == 4 * len(hours), 'complete native/hourly source pair required')
    differences = []
    varying = []
    for i, hour in enumerate(hours):
        q = quarters[4*i:4*i+4]
        _require(all(r.start_utc == hour.start_utc + j*QUARTER and r.end_utc == r.start_utc + QUARTER
                     for j, r in enumerate(q)), 'native/hourly alignment required')
        prices = [r.price_eur_per_mwh for r in q]
        difference = abs(hour.price_eur_per_mwh - sum(prices, Fraction(0))/4)
        _require(difference <= Fraction(1, 200), 'publisher hourly/native reconciliation exceeds source-cent precision')
        if hour.start_utc < transition:
            _require(len(set(prices)) == 1, 'pretransition native quarters must repeat the hourly auction price')
        elif len(set(prices)) > 1:
            varying.append(hour.start_utc)
        differences.append(difference)
    _require(varying and varying[0] == transition, 'qualified native auction transition required')
    return {'hours_compared': len(hours), 'max_abs_mean_difference_eur_per_mwh': exact(max(differences)),
            'nonzero_rounding_differences': sum(bool(d) for d in differences),
            'posttransition_varying_hours': len(varying), 'first_varying_hour_utc': varying[0].isoformat(),
            'tie_rounding': 'UNKNOWN', 'unrounded_prices_recovered': False}


@dataclass(frozen=True)
class WholesaleReference:
    window: str
    records: tuple[WholesaleHour, ...]
    evidence: dict
    reconciliation: dict


def read_wholesale_reference(source_paths, *, window):
    """Read all pinned originals and witnesses before returning either whole year."""
    m = source_manifest()
    _require(type(window) is str and window in m['windows'], 'explicit supported reference window required')
    sources = _source_bytes(source_paths, m)
    pins = {s['source_id']: s for s in m['source_artifacts']}
    _configuration(sources['SRC-B04-SMARD-CONFIG-20261003'])
    start, end = map(_endpoint, m['padded_window_utc'])
    panels = []
    for sid in (m['price_source_id'], m['native_source_id']):
        pin = pins[sid]
        request = pin['export_request']['request_form']
        _require(len(request) == 1 and request[0]['moduleIds'] == [8000262]
                 and request[0]['region'] == 'DE-LU' and request[0]['format'] == 'CSV'
                 and request[0]['timestamp_from'] == (start - EPOCH) // timedelta(milliseconds=1)
                 and request[0]['timestamp_to'] == (end - EPOCH) // timedelta(milliseconds=1),
                 'qualified HU export request and UTC bounds required')
        panels.append(_parse_csv(sources[sid], pin, start=start, end=end))
    hours, quarters = panels
    witnesses = _epochs(sources, m['source_artifacts'], quarters)
    reconciliation = _reconcile(hours, quarters, _endpoint(m['native_auction_transition_utc']))
    for rows, expected in ((hours, (23, 25)), (quarters, (92, 100))):
        days = Counter(r.start_utc.astimezone(HU).date().isoformat() for r in rows)
        _require((days['2025-03-30'], days['2025-10-26']) == expected
                 and sum(r.source_end_label_anomaly for r in rows) == 2,
                 'qualified complete DST coverage and source end-label anomalies required')
    a, b = map(_endpoint, m['windows'][window])
    selected = tuple(r for r in hours if a <= r.start_utc < b)
    _require(len(selected) == 8760 and selected[0].start_utc == a and selected[-1].end_utc == b,
             'complete selected physical year required')
    evidence = {'reference_id': REFERENCE_ID, 'manifest_sha256': MANIFEST_SHA256,
                'window': window, 'start_utc': a.isoformat(), 'end_utc_exclusive': b.isoformat(),
                'source_id': m['price_source_id'], 'bidding_zone': 'HU', 'currency': 'EUR', 'price_unit': 'EUR/MWh',
                'retrieved_at': pins[m['price_source_id']]['retrieved_at'], 'as_of_meaning': m['as_of_meaning'],
                'original_auction_vintage': None, 'per_record_revision': None,
                'price_evidence': 'OBS_PUBLISHER_CALCULATED_HOURLY_SOURCE',
                'physical_end_evidence': 'DER_FROM_IDENTIFIED_START_PLUS_DURATION',
                'required_attribution': m['required_attribution'], 'license_url': m['license_url'],
                'rights_scope': m['rights_scope'], 'changes': m['changes'], 'source_artifacts': m['source_artifacts'],
                'validation_debt': m['validation_debt'], 'excluded_claims': m['excluded_claims'],
                'national_admission': False, 'policy_defaults_selected': False, 'originals_republished': False}
    reconciliation.update({'epoch_witnesses': witnesses, 'epoch_overlapping_quarters': 2976,
                           'padded_hourly_intervals': len(hours), 'padded_quarter_intervals': len(quarters),
                           'selected_hours': len(selected), 'negative_price_hours': sum(r.price_eur_per_mwh < 0 for r in selected),
                           'hourly_source_end_label_anomalies': 2, 'quarter_source_end_label_anomalies': 2,
                           'missing_prices': 0, 'duplicate_physical_starts': 0, 'imputation': False})
    return WholesaleReference(window, selected, evidence, reconciliation)


def normalized_record(row):
    return {'start_utc': row.start_utc.isoformat(), 'end_utc': row.end_utc.isoformat(),
            'start_local': row.start_utc.astimezone(HU).isoformat(), 'end_local': row.end_utc.astimezone(HU).isoformat(),
            'source_start_label': row.source_start_label, 'source_end_label': row.source_end_label,
            'source_price_lexeme': row.source_price_lexeme, 'price_eur_per_mwh': exact(row.price_eur_per_mwh),
            'source_id': row.source_id, 'source_end_label_anomaly': row.source_end_label_anomaly,
            'physical_end_evidence': 'DER_FROM_IDENTIFIED_START_PLUS_DURATION'}


@dataclass(frozen=True)
class ImportedEnergy:
    start_utc: datetime
    end_utc: datetime
    imported_mwh: object


def _value(reference, imports, *, convention, within_hour_profile, energy_unit, profile_id):
    _require(convention == CONVENTION and within_hour_profile == 'FLAT' and energy_unit == 'MWh',
             'explicit hourly-flat wholesale energy-only convention and MWh required')
    _require(type(profile_id) is str and bool(profile_id.strip()), 'caller-declared energy profile identity required')
    loads = iter(imports)
    sentinel = object()
    total = cost = credit = Fraction(0)
    valued = []
    for row in reference.records:
        energy = next(loads, None)
        _require(isinstance(energy, ImportedEnergy), 'one imported-energy interval per price required')
        _require(_utc(energy.start_utc) == row.start_utc and _utc(energy.end_utc) == row.end_utc,
                 'import/price physical intervals must match exactly and in order')
        quantity = _number(energy.imported_mwh, nonnegative=True)
        value = quantity * row.price_eur_per_mwh
        total += quantity
        cost += value
        credit += min(value, Fraction(0))
        valued.append({'start_utc': row.start_utc.isoformat(), 'end_utc': row.end_utc.isoformat(),
                       'imported_mwh': exact(quantity), 'wholesale_reference_eur': exact(value)})
    _require(next(loads, sentinel) is sentinel, 'extra imported-energy interval')
    return {**reference.evidence, 'evidence_status': 'DER_CALLER_DECLARED_REFERENCE', 'convention': convention,
            'within_hour_profile': within_hour_profile, 'energy_unit': energy_unit, 'profile_id': profile_id,
            'profile_status': 'CALLER_DECLARED_NOT_PROGRAMME_DEFAULT', 'arithmetic': 'EXACT_RATIONAL_NO_ROUNDING',
            'total_imported_mwh': exact(total), 'wholesale_reference_eur': exact(cost),
            'negative_price_credit_eur': exact(credit),
            'consumption_weighted_price_eur_per_mwh': exact(cost/total) if total else None,
            'reconciliation': reference.reconciliation, 'interval_valuations': valued}


def value_wholesale_reference(source_paths, *, window, imports, convention, within_hour_profile, energy_unit, profile_id):
    """Exact energy-price products, using all qualified hourly source observations.

    Imported MWh must be explicitly supplied for each physical hour, including
    zero-import hours. After native quarter-hour trading begins, the publisher's
    cent-rounded hourly series is only the declared hourly-flat reference.
    """
    reference = read_wholesale_reference(source_paths, window=window)
    return _value(reference, imports, convention=convention, within_hour_profile=within_hour_profile,
                  energy_unit=energy_unit, profile_id=profile_id)
