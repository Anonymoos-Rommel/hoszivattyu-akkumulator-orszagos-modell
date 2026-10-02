"""Civil-2025 source-rating energy and a frozen-2026 tariff charge function.

IEE Projects TABULA + EPISCOPE (www.episcope.eu).
Weather: Meteorológiai Adattár, HungaroMet Nonprofit Zrt.
An explicit connection ledger is separate from reference-device consumption.
Neither the installed electricity reconciliation nor household bills are known.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from modules.B04 import engine as tariff
from modules.B05 import annual_device_reference as device
from modules.B11 import annual_retrofit_reference as family

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b04_annual_reference_manifest.json'
MANIFEST_SHA256 = '7976a6afd87fb875c8fe243b92c7b1429eab404066a40d95845b039aaa64adc7'
BUDAPEST = ZoneInfo('Europe/Budapest')
UTC = timezone.utc
START = datetime(2024, 12, 31, 23, tzinfo=UTC)
END = datetime(2025, 12, 31, 23, tzinfo=UTC)
HOUR = timedelta(hours=1)
CONDITION = 'SOURCE_RATING_ELECTRICITY_AS_IMPORTED_REFERENCE_SCN'
H_LOAD = 'ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES'
SEGMENTS = (
    ('H_JAN_APR', date(2025, 1, 1), date(2025, 4, 16)),
    ('OUTSIDE_APR_JUL', date(2025, 4, 16), date(2025, 8, 1)),
    ('OUTSIDE_AUG_OCT', date(2025, 8, 1), date(2025, 10, 15)),
    ('H_OCT_DEC', date(2025, 10, 15), date(2026, 1, 1)),
)
WINDOWS = {
    'A1': (('A1_2024_2025_PORTION', (0, 1)), ('A1_2025_2026_PORTION', (2, 3))),
    'H': (('H_JAN_APR', (0,)), ('H_OUTSIDE', (1, 2)), ('H_OCT_DEC', (3,))),
}


@dataclass(frozen=True)
class MonthFee:
    month: int
    # Exact decimal or rational fractions; no implicit April/October rule.
    fractions: tuple[tuple[str, object], ...]


@dataclass(frozen=True)
class ConnectionLedger:
    connection_id: str
    calendar_year: int
    coverage: str
    months: tuple[MonthFee, ...]


def _manifest():
    raw = MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed civil-year tariff manifest required')
    result = json.loads(raw)
    for name, digest in result['repository_pins'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('reviewed producer or tariff input changed: ' + name)
    return result


def _segment_profile(rows):
    if len(rows) != 8760:
        raise ValueError('complete civil year required')
    grouped = [[] for _ in SEGMENTS]
    days = Counter()
    local_rows = []
    for i, row in enumerate(rows):
        a, b = device._endpoint(row['interval_start_utc']), device._endpoint(row['interval_end_utc'])
        if a != START + i * HOUR or b != a + HOUR or b > END:
            raise ValueError('physical civil-year intervals must be consecutive and exact')
        if row['status'] != 'DER' or row['unserved_heat_kwh'] != 0:
            raise ValueError('complete source-rating service required for tariff handoff')
        local_a, local_b = a.astimezone(BUDAPEST), b.astimezone(BUDAPEST)
        day = local_a.date()
        matching = [j for j, (_, start, end) in enumerate(SEGMENTS) if start <= day < end]
        if len(matching) != 1:
            raise ValueError('local calendar interval outside the reference')
        j = matching[0]
        if tariff.h_is_in_season(day) != (j in (0, 3)):
            raise ValueError('canonical season and local segment disagree')
        value = tariff.amount(row['device_reference_electricity_kwh'], 'reference device electricity')
        grouped[j].append(value)
        days[day.isoformat()] += 1
        local_rows.append({**row, 'interval_start_local': local_a.isoformat(),
                           'interval_end_local': local_b.isoformat(), 'segment_id': SEGMENTS[j][0]})
    with localcontext() as ctx:
        ctx.prec = 50
        segments = [{'segment_id': name, 'start_local_date': start.isoformat(),
                     'end_local_date_exclusive': end.isoformat(), 'hours': len(grouped[i]),
                     'reference_electricity_kwh': sum(grouped[i], Decimal(0))}
                    for i, (name, start, end) in enumerate(SEGMENTS)]
    if [s['hours'] for s in segments] != [2519, 2568, 1800, 1873]:
        raise ValueError('civil segment or DST coverage mismatch')
    if len(days) != 365 or days['2025-03-30'] != 23 or days['2025-10-26'] != 25:
        raise ValueError('local-day coverage mismatch')
    return segments, local_rows


def calculate_reference(*, weather_path: Path, package: str):
    """Named civil-year producer; never clip/relabel the UTC-year result."""
    manifest = _manifest()
    if package not in ('standard', 'ambitious'):
        raise ValueError('complete standard or ambitious source package required')
    base, packages = device._manifest(), family._manifest()
    weather = device._weather(weather_path, manifest['weather'])
    thermal = device._thermal({'thermal': packages['cases'][package]['thermal']})
    models = {mode: device.wm50.load_wm50_reference(mode, fixed_supply_c=55)
              for mode in device.paired.MODES}
    rows, summary = device._calculate(weather, thermal, base['heat_pump'], models, device.wm50.source_grid())
    if not summary['complete_generator_service'] or summary['unknown_hours'] or summary['source_capacity_shortfall_kwh'] != 0:
        raise ValueError('incomplete source-rating service cannot become annual priced energy')
    segments, local_rows = _segment_profile(rows)
    return {'reference_id': manifest['reference_id'] + ':' + package, 'package': package,
            'evidence_status': 'DER', 'evidence_tier': 'E2', 'calendar': 'Europe/Budapest civil2025',
            'start_utc': START.isoformat(), 'end_utc_exclusive': END.isoformat(),
            'thermal_reference': thermal, 'summary': summary, 'segments': segments, 'rows': local_rows,
            'service_completion_basis': 'SOURCE_RATING_REFERENCE_ONLY',
            'installed_service_completion': None, 'installed_electricity_kwh': None,
            'historical_grid_comparison': None, 'national_admission': False,
            'validation_debt': manifest['validation_debt']}


def _fraction(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal, Fraction)):
        raise ValueError('explicit finite fee fraction required')
    try:
        result = value if isinstance(value, Fraction) else Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError('explicit finite fee fraction required') from exc
    if not 0 <= result <= 1:
        raise ValueError('fee fractions must lie in [0,1]')
    return result


def _fee_periods(ledger, scheme):
    if (not isinstance(ledger, ConnectionLedger) or not isinstance(ledger.connection_id, str)
            or not ledger.connection_id.strip() or type(ledger.calendar_year) is not int
            or ledger.calendar_year != 2025 or ledger.coverage != 'CONTINUOUS_CIVIL_YEAR'
            or not isinstance(ledger.months, tuple) or len(ledger.months) != 12):
        raise ValueError('one explicit continuously connected civil2025 ledger required')
    out = {name: Fraction(0) for name, _ in WINDOWS[scheme]}
    seen = set()
    for row in ledger.months:
        if (not isinstance(row, MonthFee) or type(row.month) is not int or row.month not in range(1, 13)
                or row.month in seen or not isinstance(row.fractions, tuple)):
            raise ValueError('each local calendar month must occur exactly once')
        seen.add(row.month)
        expected = ({'A1'} if scheme == 'A1' else {'H_HEATING', 'H_OUTSIDE'} if row.month in (4, 10)
                    else {'H_HEATING'} if row.month in (1, 2, 3, 11, 12) else {'H_OUTSIDE'})
        fractions = {}
        for pair in row.fractions:
            if not isinstance(pair, tuple) or len(pair) != 2 or not isinstance(pair[0], str) or pair[0] in fractions:
                raise ValueError('unique named fee regimes required')
            fractions[pair[0]] = _fraction(pair[1])
        if set(fractions) != expected or sum(fractions.values()) != 1:
            raise ValueError('applicable regime fractions must cover this month exactly once')
        for regime, value in fractions.items():
            period = ('A1_2024_2025_PORTION' if row.month <= 7 else 'A1_2025_2026_PORTION') if scheme == 'A1' else (
                'H_OUTSIDE' if regime == 'H_OUTSIDE' else 'H_JAN_APR' if row.month <= 4 else 'H_OCT_DEC')
            out[period] += value
    if seen != set(range(1, 13)) or sum(out.values()) != 12:
        raise ValueError('one annual connection fee budget must total twelve months')
    return out


def _scope(scheme, condition, load_scope, connection_scope):
    if not isinstance(scheme, str) or scheme not in WINDOWS or condition != CONDITION:
        raise ValueError('explicit source-rating-import SCN and A1/H alternative required')
    if scheme == 'H' and (load_scope != H_LOAD or connection_scope != 'PROFILED_LOW_VOLTAGE'):
        raise ValueError('H requires declared thermal-load and profiled-low-voltage scope; no site permission inferred')


def _periods(reference, scheme):
    with localcontext() as ctx:
        ctx.prec = 50
        return [{'period_id': name, 'reference_kwh': sum((reference['segments'][i]['reference_electricity_kwh'] for i in indices), Decimal(0)),
                 'start': SEGMENTS[indices[0]][1], 'end': SEGMENTS[indices[-1]][2] - timedelta(days=1)}
                for name, indices in WINDOWS[scheme]]


def _native_bill(period, scheme, area, quantity, allowance, months, load_scope, connection_scope):
    if scheme == 'A1':
        return tariff.price_a1(quantity, allowance, months, area)
    if period['period_id'] == 'H_OUTSIDE':
        return tariff.price_h_outside(quantity, allowance, months, area, period['start'], period['end'],
                                      load_scope=load_scope, connection_scope=connection_scope)
    return tariff.price_h_heating(quantity, months, area, period['start'], period['end'], load_scope=load_scope)


def _response(reference, scheme, area, load_scope, connection_scope):
    periods = _periods(reference, scheme)
    terms = []
    with localcontext() as ctx:
        ctx.prec = 50
        for p in periods:
            high = _native_bill(p, scheme, area, 1, 0, 0, load_scope, connection_scope)
            low = _native_bill(p, scheme, area, 1, 1, 0, load_scope, connection_scope)
            fee = _native_bill(p, scheme, area, 0, 0, 1, load_scope, connection_scope)
            has_allowance = scheme == 'A1' or p['period_id'] == 'H_OUTSIDE'
            terms.append({'period_id': p['period_id'], 'reference_kwh': p['reference_kwh'],
                          'energy_intercept_huf': p['reference_kwh'] * high.consumption_charge_huf,
                          'discount_coefficient_huf_per_kwh': low.consumption_charge_huf - high.consumption_charge_huf,
                          'allocation_key': p['period_id'] if has_allowance else None,
                          'connection_fee_huf_per_month': fee.fixed_charge_huf,
                          'source_ids': tuple(sorted(set(high.source_ids + low.source_ids + fee.source_ids)))})
    return {'reference_id': reference['reference_id'], 'scheme': scheme, 'distributor_area': area,
            'condition': CONDITION, 'price_status': 'SCN_CONSTANT_2026_TARIFF_SNAPSHOT',
            'tariff_snapshot_date': '2026-10-01', 'currency': 'HUF', 'monetary_basis': 'NOMINAL_FROZEN_2026',
            'formula': 'sum(intercept + discount_coefficient*min(reference_kwh, supplied_allocation) + connection_fee_rate*supplied_months); H heating terms have no allowance term',
            'terms': terms, 'evaluated_total_huf': None, 'site_eligibility': None,
            'allowance_authority': 'CALLER_SUPPLIED_SCN_NOT_VALIDATED_ENTITLEMENT',
            'whole_household_bill_huf': None, 'installed_cost_huf': None,
            'is_installed_cost_lower_bound': False, 'b12_cashflow_admission': False}


def price_response(*, weather_path, package, scheme, distributor_area, condition,
                   load_scope=None, connection_scope=None):
    """Return coefficients without selecting an allowance, fee rule or area."""
    _scope(scheme, condition, load_scope, connection_scope)
    ref = calculate_reference(weather_path=weather_path, package=package)
    return _response(ref, scheme, distributor_area, load_scope, connection_scope)


def evaluate_reference(*, weather_path, package, scheme, distributor_area, condition,
                       discounted_allocations, connection_ledger, load_scope=None, connection_scope=None):
    """Evaluate explicit arguments; reference energy and connection charges stay separate."""
    _scope(scheme, condition, load_scope, connection_scope)
    fee_months = _fee_periods(connection_ledger, scheme)
    expected = set(fee_months) if scheme == 'A1' else {'H_OUTSIDE'}
    if not isinstance(discounted_allocations, dict) or set(discounted_allocations) != expected:
        raise ValueError('one explicit allocation per declared settlement-window portion required')
    allowances = {k: tariff.amount(v, 'supplied allocation') for k, v in discounted_allocations.items()}
    ref = calculate_reference(weather_path=weather_path, package=package)
    response = _response(ref, scheme, distributor_area, load_scope, connection_scope)
    calls = []
    with localcontext() as ctx:
        ctx.prec = 50
        for p in _periods(ref, scheme):
            fraction = fee_months[p['period_id']]
            months = Decimal(fraction.numerator) / Decimal(fraction.denominator)
            allowance = allowances.get(p['period_id'], Decimal(0))
            bill = _native_bill(p, scheme, distributor_area, p['reference_kwh'], allowance, months,
                                load_scope, connection_scope)
            calls.append({'period_id': p['period_id'], 'start_local_date': p['start'].isoformat(),
                          'end_local_date_inclusive': p['end'].isoformat(),
                          'reference_kwh': p['reference_kwh'], 'supplied_allocation_kwh': allowances.get(p['period_id']),
                          'connection_months_exact': str(fraction), 'connection_months': months,
                          'discounted_kwh': bill.discounted_kwh, 'excess_kwh': bill.excess_kwh,
                          'reference_consumption_charge_huf': bill.consumption_charge_huf,
                          'declared_connection_charge_huf': bill.fixed_charge_huf,
                          'source_ids': bill.source_ids, 'price_status': bill.status})
        consumption = sum((p['reference_consumption_charge_huf'] for p in calls), Decimal(0))
        fixed = sum((p['declared_connection_charge_huf'] for p in calls), Decimal(0))
        combined = consumption + fixed
    return {**response, 'evaluated_total_huf': combined, 'reference_consumption_charge_huf': consumption,
            'declared_connection_charge_huf': fixed, 'connection_charge_attributed_to_device_huf': None,
            'evaluation_meaning': 'Reference consumption plus one declared continuous connection; not an end-use-attributed or household bill',
            'connection_fee_identity': {'connection_id': connection_ledger.connection_id, 'calendar_year': 2025},
            'connection_months': 12, 'pricing_calls': calls,
            'alternatives_are_additive': False, 'installed_signed_residual_priced': False}
