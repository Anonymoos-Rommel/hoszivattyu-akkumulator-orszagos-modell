"""Conditional regulated-gas tariff arithmetic for a named annual reference.

Not an actual bill, household saving, import value or fiscal compensation.
The annual-only gas source is never divided into an invented calendar profile.
"""
from __future__ import annotations

import csv
import hashlib
import json
import io
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from modules.B11 import calorific_reference as calorific

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b03_regulated_reference_manifest.json'
MANIFEST_SHA256 = '755be5630297bb0f2eb662046fdfb2daa2d8e2d79737703b0b1b1007bd4648a2'
ENERGY_CONDITION = 'TABULA_NCV_AS_TARIFF_FUTOERTEK_REFERENCE_SCN'
PERIOD_CONDITION = 'ONE_ABSTRACT_COMPLETE_AUG_JUL_SETTLEMENT_YEAR_SCN'


def _manifest():
    data = MANIFEST.read_bytes()
    if hashlib.sha256(data).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed gas tariff reference manifest mismatch')
    m = json.loads(data)
    for name, pin in m['repository_pins'].items():
        if hashlib.sha256((ROOT / pin['path']).read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('reviewed gas tariff dependency changed: ' + name)
    return m


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError('explicit finite ' + name + ' required')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('invalid ' + name) from exc
    if not result.is_finite() or result < 0:
        raise ValueError('finite nonnegative ' + name + ' required')
    return result


def _tariffs(m):
    pin = m['repository_pins']['schedule']
    data = (ROOT / pin['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ValueError('source tariff bytes changed before parsing')
    rows = list(csv.DictReader(io.StringIO(data.decode())))
    by_band = {r['tariff_band']: r for r in rows}
    if len(rows) != 2 or set(by_band) != {'DISCOUNTED_BAND','ABOVE_THRESHOLD_BAND'}:
        raise ValueError('one pair of source gas tariff bands required')
    low, high = by_band['DISCOUNTED_BAND'], by_band['ABOVE_THRESHOLD_BAND']
    if any(r['tariff_scope'] != 'A1_LT20_M3_PER_H' for r in rows):
        raise ValueError('named A1 source tariff scope required')
    if low['annual_fixed_charge_vat_basis'] != 'NET' or low['gross_fixed_charge_status'] != 'DER':
        raise ValueError('explicit net/gross fixed-fee evidence required')
    if high['annual_fixed_charge_huf'] or high['gross_annual_fixed_charge_huf']:
        raise ValueError('higher band cannot add a second fixed charge')
    with localcontext() as ctx:
        ctx.prec = 50
        net = _number(low['annual_fixed_charge_huf'], 'net annual connection charge')
        vat = _number(low['vat_rate'], 'VAT rate')
        gross = _number(low['gross_annual_fixed_charge_huf'], 'gross annual connection charge')
        if gross != net*(1+vat):
            raise ValueError('fixed fee net/VAT/gross reconciliation failed')
    return dict(discounted_gross=_number(low['gross_price_huf_per_mj'],'discounted price'),
                higher_gross=_number(high['gross_price_huf_per_mj'],'higher price'),
                threshold_mj=_number(low['threshold_mj'],'source threshold'),
                annual_net=net, annual_gross=gross, vat_rate=vat)


def price_reference(*, package: str, energy_condition: str, period_condition: str,
                    discounted_allocation_mj, connection_fee_fraction, connection_reference_id: str):
    """Evaluate only explicitly conditional source-energy/connection charges.

The caller supplies a scenario allocation after any retained gas uses and an
explicit fraction of one annual connection fee. Neither is inferred from the
space-heating source. No actual eligibility, avoidability or settlement is proved.
"""
    if energy_condition != ENERGY_CONDITION or period_condition != PERIOD_CONDITION:
        raise ValueError('explicit source-energy and abstract full-year conditions required')
    if not isinstance(connection_reference_id, str) or not connection_reference_id.strip():
        raise ValueError('nonempty scenario connection identity required')
    allocation = _number(discounted_allocation_mj, 'supplied discounted MJ allocation')
    fraction = _number(connection_fee_fraction, 'annual connection-fee fraction')
    if fraction > 1:
        raise ValueError('at most one annual connection charge permitted')
    m = _manifest()
    tariff = _tariffs(m)
    if allocation > tariff['threshold_mj']:
        raise ValueError('allocation exceeds this normal source-tariff reference; no special entitlement inferred')
    energy = calorific.calculate_reference(package=package)
    with localcontext() as ctx:
        ctx.prec = 50
        q = energy['source_convention_gas_mj_ncv']
        discounted = min(q, allocation)
        excess = q-discounted
        consumption = discounted*tariff['discounted_gross']+excess*tariff['higher_gross']
        net_connection = fraction*tariff['annual_net']
        gross_connection = fraction*tariff['annual_gross']
        total = consumption+gross_connection
    return dict(reference_id=m['reference_id'], package=package, energy_reference=energy,
                evidence_status='SCN', price_status='SCN_CONSTANT_2026_TARIFF_SNAPSHOT',
                currency='HUF', monetary_basis='NOMINAL_2026_FROZEN_SOURCE_RATES',
                consumer_layer='REGULATED_RESIDENTIAL_TARIFF',
                permitted_context='B13_BASELINE_REFERENCE_ONLY',
                energy_condition=energy_condition, period_condition=period_condition,
                supplied_allocation_mj=allocation, reference_discounted_mj=discounted,
                reference_excess_mj=excess, rates_gross_huf_per_mj=dict(discounted=tariff['discounted_gross'],excess=tariff['higher_gross']),
                reference_consumption_charge_huf=consumption,
                connection_reference_id=connection_reference_id,
                supplied_connection_fee_fraction=fraction,
                declared_connection_charge_net_huf=net_connection,
                declared_connection_charge_gross_huf=gross_connection,
                reference_energy_plus_declared_connection_huf=total,
                connection_charge_attributed_to_heating_huf=None,
                avoided_connection_charge_huf=None, retained_other_gas_mj=None,
                actual_billing_energy_mj=None, actual_household_bill_huf=None,
                actual_tariff_eligibility=None, household_savings_huf=None,
                import_value_huf=None, fiscal_compensation_huf=None,
                b12_cashflow_admitted=False, national_admission=False,
                invoice_rounding_applied=False, alternatives_are_additive=False,
                calendar_year_split_invented=False, whole_slice_complete=False,
                validation_debt=m['validation_debt'])
