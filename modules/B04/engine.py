"""Constant-2026-tariff SCN cost arithmetic using canonical tariff rows.

This does not determine site eligibility, invoice period allocation, export
remuneration or battery dispatch. The caller supplies the evidenced discounted
allocation and billed-month fraction; no annual calendar assumption is hidden.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TariffInputError(ValueError):
    pass


def amount(value, name):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise TariffInputError(f'{name} must be finite and nonnegative') from exc
    if not number.is_finite() or number < 0:
        raise TariffInputError(f'{name} must be finite and nonnegative')
    return number


def h_is_in_season(day: date) -> bool:
    return (day.month, day.day) >= (10, 15) or (day.month, day.day) <= (4, 15)


@dataclass(frozen=True)
class Bill:
    discounted_kwh: Decimal
    excess_kwh: Decimal
    consumption_charge_huf: Decimal
    fixed_charge_huf: Decimal
    total_huf: Decimal
    source_ids: tuple[str, ...]
    status: str = 'SCN_CONSTANT_2026_TARIFF_SNAPSHOT'
    tariff_snapshot_date: date = date(2026, 10, 1)
    price_basis: str = 'FROZEN_2026_RATES_NOT_HISTORICAL_OR_FUTURE_INVOICE_VALIDATION'


def _rows(name):
    with (ROOT / 'data/processed' / name).open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def price_a1(consumption_kwh, discounted_allocation_kwh, billed_months, distributor_area: str) -> Bill:
    """Price one explicit SCN interval at frozen rates; allocation is not inferred."""
    quantity = amount(consumption_kwh, 'consumption_kwh')
    allowance = amount(discounted_allocation_kwh, 'discounted_allocation_kwh')
    months = amount(billed_months, 'billed_months')
    rows = _rows('residential_electricity_tariff_schedule.csv')
    matches = [r for r in rows if r['distributor_area'] == distributor_area and r['tariff_band'] == 'A1 discounted']
    if len(matches) != 1:
        raise TariffInputError('exact distributor-area A1 rate required')
    low = matches[0]
    higher = [r for r in rows if r['tariff_id'] == 'A1-ALL-MARKET']
    if len(higher) != 1:
        raise TariffInputError('exactly one canonical A1 excess rate required')
    high = higher[0]
    if any(r['status'] != 'OBS' or not r['source_id'] for r in (low, high)):
        raise TariffInputError('observed source-backed A1 rates required')
    discounted = min(quantity, allowance)
    excess = quantity - discounted
    energy = discounted * amount(low['final_gross_huf_per_kwh'], 'discounted final rate') + excess * amount(high['final_gross_huf_per_kwh'], 'excess final rate')
    fixed = amount(low['fixed_charge_huf_per_year'], 'annual fixed charge') * months / 12
    return Bill(discounted, excess, energy, fixed, energy + fixed, tuple(sorted(set((low['source_id'] + ';' + high['source_id']).split(';')))))


def price_h_heating(consumption_kwh, billed_months, distributor_area: str, start: date, end: date, *, load_scope: str) -> Bill:
    """Conditional H-season import cost, never site permission or battery pricing.

    Dates determine season membership only; prices are frozen 2026 SCN inputs.
    Inclusive date bounds must be wholly within one heating season.
    The caller must separately substantiate load eligibility for any site claim.
    """
    if load_scope != 'ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES':
        raise TariffInputError('H pricing does not authorize battery/general/export loads')
    if end < start or (end - start).days > 366:
        raise TariffInputError('invalid billing interval')
    if any(not h_is_in_season(start + timedelta(days=i)) for i in range((end - start).days + 1)):
        raise TariffInputError('outside-season full-price/period contract is not yet admitted')
    quantity = amount(consumption_kwh, 'consumption_kwh')
    months = amount(billed_months, 'billed_months')
    matches = [r for r in _rows('h_tariff_schedule.csv') if r['distributor_area'] == distributor_area and r['period_type'] == 'heating season']
    if len(matches) != 1 or matches[0]['final_price_status'] != 'OBS' or matches[0]['status'] != 'OBS' or not matches[0]['source_id']:
        raise TariffInputError('source-native final H heating rate required')
    row = matches[0]
    energy = quantity * amount(row['final_gross_huf_per_kwh'], 'final H rate')
    fixed = months * amount(row['fixed_gross_huf_per_month'], 'monthly H fixed charge')
    return Bill(quantity, Decimal(0), energy, fixed, energy + fixed, tuple(sorted(set(row['source_id'].split(';')))))
