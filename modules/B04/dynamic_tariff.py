"""MVM D-tariff backcast intake and net-energy-cost arithmetic.

The published retrospective series already contains the merchant fee. It is
not a historical D tariff, an H tariff, a forecast or a full household bill.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
import re
from zoneinfo import ZoneInfo

HU = ZoneInfo('Europe/Budapest')
UTC = timezone.utc
STEP = timedelta(minutes=15)
ROW = re.compile(r'^\s*(\d{4}\.\d{2}\.\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(-?\d+,\d{2})(?:\s|$)')
DATE_PREFIX = re.compile(r'^\s*\d{4}\.\d{2}\.\d{2}')


class DynamicTariffError(ValueError):
    pass


@dataclass(frozen=True)
class PriceInterval:
    start_utc: datetime
    end_utc: datetime
    net_energy_huf_per_kwh: Decimal
    source_id: str
    evidence_status: str = 'SCN_PUBLISHED_RETROSPECTIVE_D_TARIFF'


def _number(value, *, nonnegative=False):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DynamicTariffError('finite numeric value required') from exc
    if not n.is_finite() or (nonnegative and n < 0):
        raise DynamicTariffError('invalid numeric boundary')
    return n


def _clock(value):
    hour, minute = map(int, value.split(':'))
    if not 0 <= hour <= 23 or minute not in (0, 15, 30, 45):
        raise DynamicTariffError('invalid source quarter-hour clock')
    return hour, minute


def parse_mvm_table(text: str, start_date: date, end_date_exclusive: date, source_id: str) -> tuple[PriceInterval, ...]:
    """Validate every source-local start/end against a continuous UTC sequence.

    Source order and both clock labels retain the autumn fold and spring skip;
    no 96-rows-per-day assumption, imputation, price clipping or fee addition.
    Caller supplies the declared full-day coverage and stable source identity.
    """
    if not source_id or end_date_exclusive <= start_date:
        raise DynamicTariffError('source identity and positive declared window required')
    cursor = datetime.combine(start_date, time(), HU).astimezone(UTC)
    stop = datetime.combine(end_date_exclusive, time(), HU).astimezone(UTC)
    output = []
    for line in text.splitlines():
        match = ROW.match(line)
        if match is None:
            if DATE_PREFIX.match(line):
                raise DynamicTariffError('malformed source data row')
            continue
        raw_date, raw_start, raw_end, price = match.groups()
        source_day = datetime.strptime(raw_date, '%Y.%m.%d').date()
        local = cursor.astimezone(HU)
        end_local = (cursor + STEP).astimezone(HU)
        if cursor >= stop or source_day != local.date() or _clock(raw_start) != (local.hour, local.minute) or _clock(raw_end) != (end_local.hour, end_local.minute):
            raise DynamicTariffError('source interval missing, duplicated, reordered or outside declared window')
        output.append(PriceInterval(cursor, cursor + STEP, _number(price.replace(',', '.')), source_id))
        cursor += STEP
    if cursor != stop:
        raise DynamicTariffError('incomplete declared source window')
    return tuple(output)


@dataclass(frozen=True)
class DynamicEnergyCost:
    total_import_kwh: Decimal
    discounted_kwh: Decimal
    excess_kwh: Decimal
    consumption_weighted_net_price_huf_per_kwh: Decimal | None
    net_energy_cost_huf: Decimal
    period_start_utc: datetime
    period_end_utc: datetime
    source_ids: tuple[str, ...]
    status: str = 'SCN_RETROSPECTIVE_D_ENERGY_ONLY'
    excluded: tuple[str, ...] = ('VAT', 'NETWORK_AND_FIXED_CHARGES', 'EXPORT_REVENUE', 'SITE_ELIGIBILITY', 'FORECAST')


def price_dynamic_backcast_energy(prices, imports_kwh, discounted_allocation_kwh, a1_discounted_energy_net_huf_per_kwh):
    """One contiguous within-month period; weight *all* imports before tiering.

    Inputs are aligned quarter-hour imported kWh, not signed net grid flows.
    The published flexible price already includes the merchant spread once.
    Entitlement allocation is supplied explicitly, not inferred by this helper.
    """
    prices, loads = tuple(prices), tuple(imports_kwh)
    if not prices or len(prices) != len(loads):
        raise DynamicTariffError('nonempty aligned price and import vectors required')
    month = prices[0].start_utc.astimezone(HU).strftime('%Y-%m')
    previous_end = prices[0].start_utc
    quantities, values = [], []
    for interval, load in zip(prices, loads):
        if interval.start_utc.tzinfo is None or interval.end_utc.tzinfo is None or interval.start_utc.utcoffset() != timedelta(0) or interval.end_utc.utcoffset() != timedelta(0):
            raise DynamicTariffError('explicit UTC interval required')
        if any(t.minute % 15 or t.second or t.microsecond for t in (interval.start_utc, interval.end_utc)):
            raise DynamicTariffError('UTC quarter-hour clock alignment required')
        if interval.start_utc != previous_end or interval.end_utc - interval.start_utc != STEP:
            raise DynamicTariffError('strict contiguous quarter-hour sequence required')
        if interval.start_utc.astimezone(HU).strftime('%Y-%m') != month:
            raise DynamicTariffError('split the calculation at calendar-month boundaries')
        if not interval.source_id or interval.evidence_status != 'SCN_PUBLISHED_RETROSPECTIVE_D_TARIFF':
            raise DynamicTariffError('source-backed retrospective price boundary required')
        quantities.append(_number(load, nonnegative=True))
        values.append(_number(interval.net_energy_huf_per_kwh))
        previous_end = interval.end_utc
    quota = _number(discounted_allocation_kwh, nonnegative=True)
    fixed_energy = _number(a1_discounted_energy_net_huf_per_kwh, nonnegative=True)
    total = sum(quantities, Decimal(0))
    discounted = min(total, quota)
    excess = total - discounted
    weighted = sum((q*p for q,p in zip(quantities, values)), Decimal(0)) / total if total else None
    cost = discounted * fixed_energy + excess * (weighted if weighted is not None else Decimal(0))
    return DynamicEnergyCost(total, discounted, excess, weighted, cost, prices[0].start_utc, prices[-1].end_utc, tuple(sorted({p.source_id for p in prices})))
