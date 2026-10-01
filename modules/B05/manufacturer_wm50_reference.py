"""Four separate source-condition WM50 maps; no annual or dispatch claim.

Grey integrated-defrost annotations and blank coordinates remain in the source
grid. Unmarked cells do not authorize zero defrost or an added event penalty.
The existing engine derives input from Q/COP and interpolates Q/input together.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from modules.B05.engine import PerformanceMap, PerformancePoint

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = 'SRC-B05-MITSUBISHI-DATABOOK-WM50-FULL-GRID-2020'
MODES = ('MAX', 'NOMINAL', 'MID', 'MIN')
PRODUCT = 'PUZ-WM50VHA(-BS)'


def source_grid():
    path = ROOT / 'data/processed/b05/wm50_full_performance_v53.csv'
    manifest = json.loads((ROOT / 'registry/b05_wm50_full_grid_manifest.json').read_text())
    if manifest['source_id'] != SOURCE_ID or manifest['model'] != PRODUCT:
        raise ValueError('source/product mismatch')
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['curated_extract_sha256']:
        raise ValueError('reviewed manufacturer grid hash mismatch')
    with path.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    keys = {(r['mode'], r['outdoor_temperature_c'], r['supply_temperature_c']) for r in rows}
    if len(rows) != 252 or len(keys) != len(rows):
        raise ValueError('complete unique source grid required')
    if any(r['source_id'] != SOURCE_ID or r['mode'] not in MODES
           or r['claim_scope'] != 'MANUFACTURER_STANDARD_CONDITION_REFERENCE' for r in rows):
        raise ValueError('manufacturer source scope mismatch')
    for row in rows:
        if row['availability'] == 'SOURCE_BLANK':
            if any(row[k] for k in ('thermal_capacity_kw', 'cop', 'derived_input_kw')):
                raise ValueError('blank source coordinate is not a numeric point')
        elif row['availability'] != 'PRESENT':
            raise ValueError('unknown source availability')
    return tuple(rows)


def load_wm50_reference(mode: str, *, fixed_supply_c: float | None = None) -> PerformanceMap:
    """Explicit compressor-frequency mode, not automatic load-level selection.

    Capacity/COP are the source pair. Electrical input is derived inside the
    existing engine, so exact-point complete output is DER rather than a new
    observed electrical measurement. Missing corners still fail closed. A fixed
    native supply column is an explicit one-dimensional reference, not a
    weather-compensation curve. It may not bridge an internal blank row.
    """
    if mode not in MODES:
        raise ValueError('explicit MAX, NOMINAL, MID or MIN mode required')
    rows = source_grid()
    if fixed_supply_c is not None:
        column = [r for r in rows if r['mode'] == mode
                  and float(r['supply_temperature_c']) == fixed_supply_c]
        if not column:
            raise ValueError('fixed supply must be a native source column')
        present_t = [float(r['outdoor_temperature_c']) for r in column if r['availability'] == 'PRESENT']
        if not present_t:
            raise ValueError('fixed native supply column has no source performance points')
        if any(r['availability'] != 'PRESENT' and min(present_t) < float(r['outdoor_temperature_c']) < max(present_t)
               for r in column):
            raise ValueError('fixed supply cannot bridge an internal source blank')
    floor = {(r['outdoor_temperature_c'], r['supply_temperature_c']): r
             for r in rows if r['mode'] == 'MIN'}
    points = []
    for row in rows:
        if row['mode'] != mode or row['availability'] != 'PRESENT':
            continue
        if fixed_supply_c is not None and float(row['supply_temperature_c']) != fixed_supply_c:
            continue
        key = row['outdoor_temperature_c'], row['supply_temperature_c']
        minimum = floor[key]
        if minimum['availability'] != 'PRESENT':
            raise ValueError('same-product minimum capacity unavailable')
        points.append(PerformancePoint(
            outdoor_temperature_c=float(key[0]), supply_temperature_c=float(key[1]),
            thermal_capacity_kw=float(row['thermal_capacity_kw']),
            cop=float(row['cop']), electrical_input_kw=None,
            min_modulation_kw=float(minimum['thermal_capacity_kw']),
            evidence_status='OBS', source_id=SOURCE_ID,
            unit_boundary='total_unit_input',
        ))
    suffix = '' if fixed_supply_c is None else f':FIXED_W{fixed_supply_c:g}'
    return PerformanceMap(f'{PRODUCT}:{mode}:VOL5.3{suffix}', 'air_to_water', points)


def source_annotation(mode: str, outdoor_temperature_c: float, supply_temperature_c: float):
    """Return an exact source-cell label; never invent an interpolated label."""
    matches = [r for r in source_grid() if r['mode'] == mode
               and float(r['outdoor_temperature_c']) == outdoor_temperature_c
               and float(r['supply_temperature_c']) == supply_temperature_c]
    if len(matches) != 1:
        raise ValueError('annotation requires an exact published grid coordinate')
    return matches[0]['availability'], matches[0]['defrost_source_annotation']
