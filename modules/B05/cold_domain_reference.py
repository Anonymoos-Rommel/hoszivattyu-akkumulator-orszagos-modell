"""Observed cold-window exposure of the named WM50/W55 source map.

Adatbázis: Meteorológiai Adattár, HungaroMet Nonprofit Zrt.
No thermal simulation, graph digitization, equipment-failure count or sizing.
Only calculate_reference admits exact pinned source bytes; helpers are test seams.
"""
from __future__ import annotations

import csv
import hashlib
import json
import io
import zipfile
import math
from datetime import datetime, timedelta
from pathlib import Path
from statistics import fmean

from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B05.extreme_weather_return_period import materializable_winter_metrics
from modules.B05.weather import WeatherRecord, parse_hungaromet_csv

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry/b05_cold_domain_reference_manifest.json'
MANIFEST_SHA256 = '9976768275bf15e6bb7707a10f051d7f3d81ba8a27a5d4bd89ffde4213c474b9'
SOURCE_ID = 'SRC-B05-HUNGARY-HOURLY-HIST-2026'
HOUR = timedelta(hours=1)


def _manifest():
    raw = MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('reviewed cold-domain manifest mismatch')
    m = json.loads(raw)
    for name, pin in m['repository_pins'].items():
        if hashlib.sha256((ROOT / pin['path']).read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('reviewed source/code mismatch: ' + name)
    return m


def _exposure(records, model):
    """Exact numeric-map coverage; it cannot establish physical failure hours."""
    records = tuple(records)
    if len(records) != 72:
        raise ValueError('exactly 72 physical hours required')
    if model.equipment_id != 'PUZ-WM50VHA(-BS):MAX:VOL5.3:FIXED_W55':
        raise ValueError('named WM50 MAX fixed-W55 map required')
    temperatures, available = [], []
    for index, r in enumerate(records):
        if not isinstance(r, WeatherRecord) or r.station_id != '44527' or r.source_id != SOURCE_ID:
            raise ValueError('exact station/source record required')
        end = r.timestamp_utc
        if (not isinstance(end, datetime) or end.tzinfo is None or end.utcoffset() != timedelta(0)
                or end.minute or end.second or end.microsecond
                or (index and end != records[index-1].timestamp_utc + HOUR)):
            raise ValueError('unique contiguous whole-hour UTC endpoints required')
        value = r.hourly_mean_temperature_c
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            raise ValueError('finite observed hourly mean required; no instantaneous fallback')
        result = model.evaluate(value, 55)
        if result.point is None:
            if not result.status.startswith('Q /'):
                raise ValueError('unavailable numeric source must retain Q')
            available.append(False)
        else:
            p = result.point
            if (result.status != 'DER' or p.source_ids != (wm50.SOURCE_ID,)
                    or p.outdoor_temperature_c != value or p.supply_temperature_c != 55):
                raise ValueError('manufacturer source/coordinate substitution')
            available.append(True)
        temperatures.append(value)
    return dict(
        source_first_endpoint_utc=records[0].timestamp_utc.isoformat(),
        source_last_endpoint_utc=records[-1].timestamp_utc.isoformat(),
        physical_start_utc=(records[0].timestamp_utc-HOUR).isoformat(),
        physical_end_exclusive_utc=records[-1].timestamp_utc.isoformat(),
        physical_hours=72, mean_ta_c=fmean(temperatures), min_ta_c=min(temperatures),
        max_ta_c=max(temperatures), numeric_map_supported_hours=sum(available),
        numeric_map_unavailable_hours=72-sum(available),
        complete_numeric_map_coverage=all(available),
        physical_equipment_failure_hours=None, full_capacity_deficit_kwh=None,
        backup_capacity_kw=None, electricity_kwh=None, actual_spf=None,
        evidence_status='DER', claim_scope='OBSERVED_WEATHER_NUMERIC_SOURCE_MAP_EXPOSURE')


def _select(records, metric):
    selected = tuple(r for r in records
                     if metric.coldest_72h_start_utc <= r.timestamp_utc <= metric.coldest_72h_end_utc)
    if len(selected) != 72:
        raise ValueError('P9 endpoint-labelled selection must contain 72 observations')
    return selected


def calculate_reference(*, archive_path: Path):
    """Read the exact external archive and return two source-domain summaries.

The P9 complete-winter selection is reused unchanged. Its timestamps label
source endpoints; the new result separately gives their physical half-open
support. No alternate product, supply temperature or weather file is admitted.
The source archive and hourly panel are not written or returned.
"""
    m = _manifest()
    path = Path(archive_path)
    raw = path.read_bytes()
    if len(raw) != m['archive']['bytes'] or hashlib.sha256(raw).hexdigest() != m['archive']['sha256']:
        raise ValueError('exact registered external weather archive required')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        if len(names) != 1:
            raise ValueError('one source CSV required')
        text = archive.read(names[0]).decode('utf-8-sig')
    records = tuple(parse_hungaromet_csv(text, source_id=SOURCE_ID))
    if len(records) != m['archive']['rows']:
        raise ValueError('complete registered source panel required')
    metrics = materializable_winter_metrics(records)
    if tuple(x.winter_label_year for x in metrics) != tuple(m['complete_winter_labels']):
        raise ValueError('P9 complete-winter coverage changed')
    with (ROOT / m['repository_pins']['p9_winter_statistics']['path']).open(newline='') as f:
        original = {int(r['winter_label_year']): r for r in csv.DictReader(f) if r['station_id'] == '44527'}
    if set(original) != {x.winter_label_year for x in metrics}:
        raise ValueError('P9 station/year membership mismatch')
    for metric in metrics:
        r = original[metric.winter_label_year]
        if (not math.isclose(metric.coldest_72h_mean_ta_c, float(r['coldest_72h_mean_ta_C']), abs_tol=5e-7, rel_tol=0)
                or metric.coldest_72h_start_utc.isoformat().replace('+00:00','Z') != r['coldest_72h_start_utc']
                or metric.coldest_72h_end_utc.isoformat().replace('+00:00','Z') != r['coldest_72h_end_utc']):
            raise ValueError('original P9 rounded statistic/endpoint mismatch')
    coldest = min(metrics, key=lambda x: (x.coldest_72h_mean_ta_c, x.coldest_72h_start_utc))
    reference = next(x for x in metrics if x.winter_label_year == 2025)
    model = wm50.load_wm50_reference('MAX', fixed_supply_c=55)
    cases = []
    for label, metric in (('OBSERVED_COLDEST_P9_COMPLETE_WINTER_EPISODE', coldest), ('REFERENCE_WINTER_2025_EPISODE', reference)):
        cases.append(dict(case=label, winter_label_year=metric.winter_label_year,
                          **_exposure(_select(records, metric), model)))
    return dict(case_id=m['case_id'], manifest_sha256=MANIFEST_SHA256,
                source_id=SOURCE_ID, source_sha256=m['archive']['sha256'],
                product=wm50.PRODUCT, source_map_revision='Vol.5.3', supply_coordinate_c=55,
                complete_winter_blocks=len(metrics), cases=tuple(cases),
                operating_envelope_context=m['operating_envelope_context'],
                numerical_domain_threshold_is_physical_threshold=False,
                complete_cold_event_capacity_result=None, annual_result=None, national_result=None,
                selected_replacement_product=None, selected_lower_supply_temperature_c=None,
                selected_backup=None, current_2025_reference_changed=False,
                empirical_return_period_claim=False, whole_slice_complete=False)
