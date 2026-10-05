"""Read source literals and PDF vectors; never execute the publisher JavaScript."""
import argparse
from pathlib import Path
import csv,json,hashlib,re
import fitz
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pdf',type=Path,required=True)
parser.add_argument('--data-js',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
OUT=args.output_dir
if not OUT.is_dir():parser.error('existing output directory required')
PDF_SHA='97266383faf3a4257a6a521cd1ce04d02eac2628142716e548333fb0c46cbfc7'
JS_SHA='3a843f5e1d3135112d714a274eb22a3ada2cffbec6dda9bb188d2a0d53c59528'
pdf=args.pdf;js=args.data_js
for path,digest in ((pdf,PDF_SHA),(js,JS_SHA)):
 if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('source revision mismatch')
text=js.read_text();blocks=re.findall(r"\{'Year':[^{}]*\}",text)
a=[b for b in blocks if "'ID':'A1'" in b]
if len(a)!=1:raise ValueError('unique edition-qualified A1 required')
fields={}
for name in ('Year','E_BAT_usable','ETA_BAT2AC_MEAN','ETA_AC2BAT_MEAN','eta_BAT','P_BAT2AC_out','P_SYS_SOC0'):
 m=re.search(r"'"+name+r"':(0x[0-9a-f]+|[0-9]+(?:\.[0-9]+)?)(?=,|\})",a[0])
 if not m:raise ValueError('literal numeric field unavailable: '+name)
 token=m.group(1);fields[name]=int(token,16) if token.startswith('0x') else float(token)
if fields['Year']!=2026:raise ValueError('source year mismatch')
source=fitz.open(pdf);rows=[]
specs=(('AC2BAT_STANDARD',63,554,(.949,.424,.133),476.87269592285156,763.921142578125,13,101.43351,253.97052,.1),('BAT2AC_STANDARD',63,745,(.949,.424,.133),476.87269592285156,763.921142578125,13,321.07849,473.61551,.1),('BAT2AC_LOW_LOAD',21,259,(.298,.502,.023),105.522697,391.122955,.5,77.133484,229.670502,.6))
for curve,page,index,color,x0,xmax,pmax,y100,ylow,eta_span in specs:
 d=source[page].get_drawings()[index]
 if tuple(round(x,3) for x in d['color'])!=color or any(x[0]!='l' for x in d['items']):raise ValueError('vector identity mismatch')
 points=[d['items'][0][1],*[x[2] for x in d['items']]]
 converted=[((v.x-x0)/(xmax-x0)*pmax,1-(v.y-y100)/(ylow-y100)*eta_span,v.x,v.y) for v in points]
 if any(a[0]>=b[0] for a,b in zip(converted,converted[1:])) or any(not 0<r[1]<=1 for r in converted):raise ValueError('curve domain/efficiency invalid')
 for i,(power,eta,x,y) in enumerate(converted):rows.append(dict(curve_id=curve,point_index=i,path_output_kw=power,efficiency_ratio=eta,pdf_page_1based=page+1,pdf_x=x,pdf_y=y,source_id='SRC-B07-HTW-SAX-REFERENCE-2026',evidence_status='DER',claim_scope='PUBLISHED_FITTED_CURVE_REFERENCE'))

standby=source[25].get_drawings()
heights=[standby[i]['items'][0][1].y-standby[i]['items'][0][2].y for i in (35,49,63)]
if heights[0]!=heights[1] or not 0<heights[2]<heights[1]:raise ValueError('A1 standby component geometry changed')
print({'empty_state_total_plot_w':heights[0]/(476.8770751953125-324.38336181640625)*70,'DC_component_plot_w':0,'source_app_total_w':fields['P_SYS_SOC0']})

with (OUT/'sax_2026_converter_curves.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
controls=dict(source_id='SRC-B07-HTW-SAX-REFERENCE-2026',edition=2026,system_id='A1',product='SAX Power Home Plus',firmware='V23.50',identity_locator='Report Appendix A4 PDFpage65',native_numeric_fields=fields,source_js_sha256=JS_SHA,source_pdf_sha256=PDF_SHA,notes='Means are source summaries, not time-weighted annual efficiency. E_BAT_usable is measured discharged-DC usable capacity. No observed chemical one-way efficiencies are inferred. Identity is from report, not evaluated JS name expressions.')
controls['native_numeric_units']={'Year': 'calendar_year_comparison_edition', 'E_BAT_usable': 'kWh_DC_discharged_usable', 'ETA_BAT2AC_MEAN': 'percent', 'ETA_AC2BAT_MEAN': 'percent', 'eta_BAT': 'percent', 'P_BAT2AC_out': 'kW_AC_output', 'P_SYS_SOC0': 'W'}
(OUT/'sax_2026_source_controls.json').write_text(json.dumps(controls,indent=2)+'\n')
print({'curves':len(specs),'vector_points':len(rows),'literal_controls':len(fields)})
