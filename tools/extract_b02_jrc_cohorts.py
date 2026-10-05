"""Extract native paired SH-cohort/DHW-branch cells from the pinned JRC workbook."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from tools.extract_b02_jrc_household import ROOT,source_record

SHEETS=('RES_hhdet_num','RES_hhdet_fec','RES_hhdet_tes')


def relevant_code(code):
    if not isinstance(code,str):return False
    bits=code.split('.')
    if len(bits)<8 or bits[2:7]!=['HU','Res','HH','Thermal','SH']:return False
    if bits[0]=='NUM' and len(bits)==8:return True
    return len(bits)>8 and bits[8] in ('SH','WH')


def extract_workbook(path):
    import openpyxl
    values=openpyxl.load_workbook(path,read_only=True,data_only=True)
    formulas=openpyxl.load_workbook(path,read_only=True,data_only=False)
    rows=[]
    try:
        for name in SHEETS:
            vv=list(values[name].values);ff=list(formulas[name].values)
            if vv[0][23:25]!=(2022,2023) or vv[0][104]!='Code':raise ValueError('pinned year/code layout mismatch')
            for n,row in enumerate(vv,1):
                code=row[104]
                if not relevant_code(code):continue
                for col,year in ((24,2022),(25,2023)):
                    rows.append(source_record(name,n,year,code,row[0],row[col-1],ff[n-1][col-1]))
    finally:values.close();formulas.close()
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workbook',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    m=json.loads((ROOT/'registry/b02_jrc_household_manifest.json').read_text())
    if hashlib.sha256(a.workbook.read_bytes()).hexdigest()!=m['workbook_sha256']:p.error('source workbook revision mismatch')
    rows=extract_workbook(a.workbook);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    print(json.dumps({'rows':len(rows),'present':sum(r['availability']=='PRESENT' for r in rows)}))


if __name__=='__main__':main()
