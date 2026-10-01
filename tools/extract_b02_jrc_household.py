"""Read selected native JRC-IDEES cells; requires an existing openpyxl installation.

No workbook edits or formula recalculation are performed. Cached source values
and original formula text are retained separately. Source hash pins the release.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from math import isfinite
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE_ID='SRC-B02-JRC-IDEES-HU-2023'
SUMMARY_ROWS=(6,7,11,12,28,33,36,40,44)
THERMAL_SHEETS=('RES_hh_fec','RES_hh_tes','RES_hh_eff','RES_hh_num')


def source_record(sheet,row,year,code,label,value,formula):
    if not code or not isinstance(code,str) or '.HU.' not in code:raise ValueError('native Hungarian code required')
    if value is not None and value!='':
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not isfinite(value) or value<0:raise ValueError('finite nonnegative source number required')
        availability='PRESENT';value=str(value)
    else:availability='MISSING';value=''
    return dict(sheet=sheet,source_row=row,reference_year=year,native_code=code,label=label,source_unit=code.split('.')[1],value=value,availability=availability,evidence_status='DER' if availability=='PRESENT' else 'Q',source_id=SOURCE_ID,source_formula=formula if isinstance(formula,str) and formula.startswith('=') else '')


def extract_workbook(path):
    import openpyxl
    values=openpyxl.load_workbook(path,read_only=True,data_only=True)
    formulas=openpyxl.load_workbook(path,read_only=True,data_only=False)
    rows=[]
    try:
        for name in ('RES_summary',*THERMAL_SHEETS):
            vv=list(values[name].values);ff=list(formulas[name].values)
            if vv[0][23:25]!=(2022,2023) or vv[0][104]!='Code':raise ValueError('pinned JRC year/code layout mismatch')
            for n in (SUMMARY_ROWS if name=='RES_summary' else range(3,33)):
                code=vv[n-1][104]
                if not code:continue
                for col,year in ((24,2022),(25,2023)):
                    rows.append(source_record(name,n,year,code,vv[n-1][0],vv[n-1][col-1],ff[n-1][col-1]))
    finally:values.close();formulas.close()
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workbook',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    m=json.loads((ROOT/'registry/b02_jrc_household_manifest.json').read_text())
    if hashlib.sha256(a.workbook.read_bytes()).hexdigest()!=m['workbook_sha256']:p.error('source workbook revision mismatch')
    rows=extract_workbook(a.workbook);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    print(json.dumps({'rows':len(rows),'present':sum(r['availability']=='PRESENT' for r in rows),'workbook_sha256':m['workbook_sha256']}))


if __name__=='__main__':main()
