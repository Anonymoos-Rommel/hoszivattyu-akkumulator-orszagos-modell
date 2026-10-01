"""Normalize the pinned Eurostat HU JSON-stat slice; preserve missing cells."""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE_ID='SRC-B02-EUROSTAT-HOUSEHOLD-ENDUSE-2024'
DIMS=['freq','nrg_bal','siec','unit','geo','time']


def extract(raw: bytes):
    j=json.loads(raw,parse_float=Decimal)
    if j.get('id')!=DIMS or j.get('class')!='dataset':raise ValueError('expected JSON-stat dataset dimensions')
    axes=[]
    for dim,size in zip(DIMS,j['size'],strict=True):
        ix=j['dimension'][dim]['category']['index']
        if sorted(ix.values())!=list(range(size)):raise ValueError('invalid dimension index')
        axes.append([k for k,v in sorted(ix.items(),key=lambda kv:kv[1])])
    if axes[0]!=['A'] or axes[3]!=['TJ'] or axes[4]!=['HU'] or axes[5]!=['2022','2023','2024']:raise ValueError('explicit annual HU/TJ/2022-2024 scope required')
    size=1
    for axis in axes:size*=len(axis)
    values=j['value'];flags=j.get('status',{})
    if not isinstance(values,dict) or not isinstance(flags,dict):raise ValueError('sparse value/status maps required')
    if any(not str(k).isdigit() or str(int(k))!=k or not 0<=int(k)<size for k in {*values,*flags}):raise ValueError('out-of-bounds observation index')
    rows=[]
    for i,(_,end_use,product,_,_,year) in enumerate(itertools.product(*axes)):
        val=values.get(str(i));present=val is not None
        if present:
            if isinstance(val,bool):raise ValueError('numeric energy value required')
            val=Decimal(str(val))
            if not val.is_finite() or val<0:raise ValueError('finite nonnegative final energy required')
        rows.append(dict(reference_year=year,geography='HU',end_use=end_use,energy_product=product,value_tj=str(val) if present else '',availability='PRESENT' if present else 'MISSING',source_flag=flags.get(str(i),''),evidence_status='DER' if present else 'Q',source_id=SOURCE_ID))
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    m=json.loads((ROOT/'registry/b02_eurostat_household_manifest.json').read_text())
    raw=(ROOT/m['repo_snapshot_path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=m['sha256']:p.error('pinned source hash mismatch')
    rows=extract(raw);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    print(json.dumps({'rows':len(rows),'present':sum(r['availability']=='PRESENT' for r in rows),'source_sha256':m['sha256']}))


if __name__=='__main__':main()
