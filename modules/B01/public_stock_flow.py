"""Official all-stock controls, separate from occupied/eligible programme stock."""
from __future__ import annotations
import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCOPE='OCCUPIED_AND_UNOCCUPIED_DWELLINGS_PLUS_OCCUPIED_HOLIDAY_UNITS'


@dataclass(frozen=True)
class StockFlowBridge:
    county_code: str
    calendar_year: int
    opening_total_stock: int
    completed: int
    removed: int
    closing_total_stock: int
    reconciliation_residual: int
    evidence_status: str='DER'
    population_scope: str=SCOPE
    occupied_population_identified: bool=False
    technical_eligibility_identified: bool=False


def _count(value):
    if not str(value).isdigit():raise ValueError('nonnegative integer source count required')
    return int(value)


def load_controls():
    stocks={};flows={}
    with (ROOT/'data/processed/b01_total_stock_controls_2022_2026.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            key=(r['county_code'],date.fromisoformat(r['reference_date']))
            if key in stocks or r['population_scope']!=SCOPE or r['evidence_status']!=('OBS' if key[1]==date(2022,10,1) else 'DER') or r['source_method']!=('CENSUS' if key[1]==date(2022,10,1) else 'OFFICIAL_CENSUS_ROLL_FORWARD') or r['source_id']!='SRC-B01-KSH-STADAT-STOCK-2026':
                raise ValueError('unique official census/roll-forward total-stock boundary required')
            stocks[key]=_count(r['total_stock_dwellings'])
    with (ROOT/'data/processed/b01_stock_flows_2023_2025.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            key=(r['county_code'],int(r['calendar_year']))
            if key in flows or r['evidence_status']!='OBS' or r['source_id']!='SRC-B01-KSH-STADAT-FLOW-2025':raise ValueError('unique observed county/year flow required')
            flows[key]=(_count(r['completed_dwellings']),_count(r['removed_dwellings']))
    manifest=json.loads((ROOT/'registry/b01_public_stock_flow_manifest.json').read_text())
    counties=set(manifest['county_codes'])
    dates={date.fromisoformat(d) for d in manifest['source_reference_dates'].values()}
    if len(counties)!=20 or set(stocks)!={(c,d) for c in counties for d in dates} or set(flows)!={(c,y) for c in counties for y in range(2023,2026)}:
        raise ValueError('complete canonical county/time scope required')
    for year,total in manifest['national_stock_controls'].items():
        dt=date.fromisoformat(manifest['source_reference_dates'][year])
        if sum(stocks[c,dt] for c in counties)!=total:raise ValueError('national stock control mismatch')
    for year in range(2023,2026):
        if sum(flows[c,year][0] for c in counties)!=manifest['national_completed_controls'][str(year)] or sum(flows[c,year][1] for c in counties)!=manifest['national_removed_controls'][str(year)]:
            raise ValueError('national flow control mismatch')
    return stocks,flows


def reconcile_year(calendar_year: int) -> tuple[StockFlowBridge,...]:
    """Join actual January-to-January stock and calendar-year flows.

    The 2022 source column is October 1, so it is never silently joined to a
    full calendar year. Residuals are returned, not forced to zero or imputed.
    """
    stocks,flows=load_controls()
    keys=sorted(k for k in flows if k[1]==calendar_year)
    if len(keys)!=20:raise ValueError('complete observed annual flow for 20 counties required')
    output=[]
    for county,year in keys:
        a,b=(county,date(year,1,1)),(county,date(year+1,1,1))
        if a not in stocks or b not in stocks:raise ValueError('January-to-January source stock endpoints required')
        built,removed=flows[county,year]
        opening,closing=stocks[a],stocks[b]
        output.append(StockFlowBridge(county,year,opening,built,removed,closing,closing-opening-built+removed))
    return tuple(output)


def total_stock_at(reference_date: date) -> int:
    stocks,_=load_controls()
    selected=[v for (c,d),v in stocks.items() if d==reference_date]
    if len(selected)!=20:raise ValueError('exact published reference date required; no interpolation')
    return sum(selected)
