"""Extract public KSH STADAT stock/flow controls without inferring occupancy."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
SOURCE_STOCK='SRC-B01-KSH-STADAT-STOCK-2026'
SOURCE_FLOW='SRC-B01-KSH-STADAT-FLOW-2025'


def county_names():
    with (ROOT/'data/processed/b02/ksh_wbl_joint_cells_2022.csv').open(encoding='utf-8',newline='') as f:
        names={(r['county_name_hu'].removesuffix(' vármegye'),r['county_code']) for r in csv.DictReader(f)}
    result=dict(names)
    if len(result)!=20:raise ValueError('canonical 20-county mapping required')
    return result


def parse_count(text, *, zero_marker_allowed=False):
    clean=re.sub(r'\s+','',text)
    if zero_marker_allowed and clean in {'-','–'}:return 0
    if not re.fullmatch(r'\d+',clean):raise ValueError('missing/noninteger count must not become zero')
    return int(clean)


def parse_section(raw: bytes, section: str, years, mapping, *, zero_marker_allowed=False):
    rows=list(csv.reader(io.StringIO(raw.decode('iso-8859-2')),delimiter=';'))
    header=rows[1]
    columns={year:header.index(str(year)) for year in years}
    active=False;out={};national={}
    for row in rows[2:]:
        if not row or not any(row):continue
        name=row[0].strip()
        if len(row)>1 and not row[1].strip():active=name==section;continue
        if not active:continue
        if name in mapping:
            for year,index in columns.items():
                key=(mapping[name],year)
                if key in out:raise ValueError('duplicate county/year')
                out[key]=parse_count(row[index],zero_marker_allowed=zero_marker_allowed)
        elif name=='Ország összesen':
            for year,index in columns.items():
                if year in national:raise ValueError('duplicate national control')
                national[year]=parse_count(row[index],zero_marker_allowed=zero_marker_allowed)
    if set(out)!={(code,year) for code in mapping.values() for year in years} or set(national)!=set(years):
        raise ValueError('complete county and national source coverage required')
    for year in years:
        if sum(v for (code,y),v in out.items() if y==year)!=national[year]:
            raise ValueError('county sum does not reconcile to published national control')
    return out,national


def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-csv',type=Path,required=True);p.add_argument('--flow-csv',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    stock_bytes,flow_bytes=a.stock_csv.read_bytes(),a.flow_csv.read_bytes()
    manifest=json.loads((ROOT/'registry/b01_public_stock_flow_manifest.json').read_text())
    expected={x['source_id']:x['sha256'] for x in manifest['sources']}
    if hashlib.sha256(stock_bytes).hexdigest()!=expected[SOURCE_STOCK] or hashlib.sha256(flow_bytes).hexdigest()!=expected[SOURCE_FLOW]:
        p.error('source revision mismatch; review and pin new source before extraction')
    names=county_names();reverse={v:k for k,v in names.items()}
    stock,nstock=parse_section(stock_bytes,'Lakásállomány',range(2022,2027),names)
    built,nbuilt=parse_section(flow_bytes,'Épített lakás',range(2023,2026),names,zero_marker_allowed=True)
    removed,nremoved=parse_section(flow_bytes,'Megszűnt lakás',range(2023,2026),names,zero_marker_allowed=True)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    stocks=[dict(county_code=c,county_name_hu=reverse[c],reference_date=manifest['source_reference_dates'][str(y)],total_stock_dwellings=stock[c,y],population_scope='OCCUPIED_AND_UNOCCUPIED_DWELLINGS_PLUS_OCCUPIED_HOLIDAY_UNITS',evidence_status='OBS' if y==2022 else 'DER',source_method='CENSUS' if y==2022 else 'OFFICIAL_CENSUS_ROLL_FORWARD',source_id=SOURCE_STOCK) for c,y in sorted(stock)]
    flows=[dict(county_code=c,county_name_hu=reverse[c],calendar_year=y,completed_dwellings=built[c,y],removed_dwellings=removed[c,y],evidence_status='OBS',source_id=SOURCE_FLOW) for c,y in sorted(built)]
    write_csv(a.output_dir/'b01_total_stock_controls_2022_2026.csv',stocks)
    write_csv(a.output_dir/'b01_stock_flows_2023_2025.csv',flows)
    print(json.dumps({'stock_source_sha256':hashlib.sha256(stock_bytes).hexdigest(),'flow_source_sha256':hashlib.sha256(flow_bytes).hexdigest(),'stock_rows':len(stocks),'flow_rows':len(flows),'national_stock':nstock,'national_completed':nbuilt,'national_removed':nremoved},indent=2))


if __name__=='__main__':main()
