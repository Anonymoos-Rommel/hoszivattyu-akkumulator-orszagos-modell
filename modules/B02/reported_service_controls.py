"""Reported 2022 household service means, not a joint heat-demand model.

Gas-use groups are source-native, not JRC technology cohorts or KSH fuel
codes. Separate means do not identify mean(area * heated fraction), heat,
design peak, participant demand, or current household operating conditions.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = 'SRC-B02-HU-REKK-TARKI-ENVELOPE-2022'
GROUPS = ('ALL', 'GAS_PRIMARY', 'GAS_SECONDARY_ONLY', 'NO_GAS_HEATING')
METRICS = ('mean_reported_indoor_temperature_c', 'mean_dwelling_area_m2',
           'mean_reported_heated_area_share_pct')


@dataclass(frozen=True)
class ReportedServiceControl:
    group_id: str
    weighted_household_share_pct: Decimal
    mean_reported_indoor_temperature_c: Decimal
    mean_dwelling_area_m2: Decimal
    mean_reported_heated_area_share_pct: Decimal
    reference_year: int = 2022
    claim_scope: str = 'SURVEY_GROUP_MEAN_CONTROL_ONLY'
    heat_allocation_allowed: bool = False


def load_controls():
    path = ROOT / 'data/processed/b02/rekk_reported_service_2022.csv'
    manifest = json.loads((ROOT / 'registry/b02_reported_service_manifest.json').read_text())
    if manifest['source_id'] != SOURCE_ID or manifest['reference_year'] != 2022:
        raise ValueError('source/reference period mismatch')
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['curated_extract_sha256']:
        raise ValueError('reviewed service-control artifact hash mismatch')
    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    out = {}
    for row in rows:
        group = row['group_id']
        if group in out or group not in GROUPS:
            raise ValueError('unique source-native gas-use groups required')
        if (row['source_id'] != SOURCE_ID or row['reference_year'] != '2022'
                or row['evidence_status'] != 'DER'
                or row['allowed_use'] != 'SURVEY_GROUP_MEAN_CONTROL_ONLY'
                or (row['source_table'], row['printed_page'], row['pdf_page_1based']) != ('1','17','41')):
            raise ValueError('source scope or locator mismatch')
        values = [Decimal(row[k]) for k in ('weighted_household_share_pct', *METRICS)]
        if (not all(v.is_finite() for v in values)
                or not 0 <= values[0] <= 100 or not 0 <= values[3] <= 100
                or values[2] <= 0):
            raise ValueError('finite valid source means required')
        out[group] = ReportedServiceControl(group, *values)
    if set(out) != set(GROUPS) or out['ALL'].weighted_household_share_pct != 100:
        raise ValueError('complete source group inventory required')
    if sum(out[g].weighted_household_share_pct for g in GROUPS[1:]) != 100:
        raise ValueError('source weighted group shares must sum to100')
    return out


def recomposition_diagnostics():
    """Preserve rounded-group vs printed-all residuals without overwriting data.

    This combines *one mean at a time*. It does not multiply different metrics
    or construct a household joint. Missing item-specific N/weights can matter.
    """
    rows = load_controls()
    result = {}
    for metric in METRICS:
        reconstructed = sum(getattr(rows[g], metric) * rows[g].weighted_household_share_pct
                            / Decimal(100) for g in GROUPS[1:])
        printed = getattr(rows['ALL'], metric)
        result[metric] = {'printed_all_mean': printed,
                          'rounded_group_recomposition': reconstructed,
                          'residual': reconstructed - printed}
    return result


def mean_heated_area_m2(group_id):
    """Fail closed: the table lacks the within-group area/use cross-moment."""
    if group_id not in load_controls():
        raise ValueError('unknown source-native gas-use group')
    raise ValueError('UNIDENTIFIED_AREA_USAGE_CROSS_MOMENT: product of means is not mean heated area')
