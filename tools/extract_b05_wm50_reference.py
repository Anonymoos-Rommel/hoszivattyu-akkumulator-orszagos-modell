"""Pinned public manufacturer table; preserve blanks and grey defrost labels."""
import argparse
from pathlib import Path
import fitz,hashlib,csv,json
from decimal import Decimal
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pdf',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
pdf=args.pdf
if hashlib.sha256(pdf.read_bytes()).hexdigest()!='e7212300cb49ad561db56e974cc9945655943bfb0dd8309610a400fba65919ab':raise ValueError('source revision')
page=fitz.open(pdf)[59];words=page.get_text('words');temperatures=(-20,-15,-10,-7,2,7,12,15,20);supplies=(25,35,40,45,50,55,60);modes=('MAX','NOMINAL','MID','MIN')
anchors=sorted([w for w in words if 53<w[0]<92 and 130<w[1]<415 and w[4] in {str(x) for x in temperatures}],key=lambda w:w[1])
if len(anchors)!=36:raise ValueError('expected36 performance rows')
grey=[]
for drawing in page.get_drawings():
 c=drawing.get('fill')
 if c and tuple(round(x,3) for x in c)==(.820,.826,.832):
  for item in drawing['items']:
   if item[0]!='re':raise ValueError('unexpected grey-path geometry')
   grey.append(item[1])
rows=[]
for i,anchor in enumerate(anchors):
 mode=modes[i//9];outdoor=temperatures[i%9]
 if int(anchor[4])!=outdoor:raise ValueError('temperature row order')
 cy=(anchor[1]+anchor[3])/2
 cells={}
 for w in words:
  cx=(w[0]+w[2])/2;wy=(w[1]+w[3])/2
  if 101<cx<538 and abs(wy-cy)<.7:
   col=int((cx-101.005)/31.181)
   if col in cells:raise ValueError('duplicate numeric cell')
   cells[col]=(w[4],any(fitz.Point(cx,wy) in r for r in grey))
 if set(cells)!=set(range(14)):raise ValueError('missing table cells')
 for j,supply in enumerate(supplies):
  (q,gq),(cop,gcop)=cells[2*j],cells[2*j+1]
  if gq!=gcop or (q=='-')!=(cop=='-'):raise ValueError('pairedcell/shading mismatch')
  present=q!='-'
  rows.append({'mode':mode,'outdoor_temperature_c':outdoor,'supply_temperature_c':supply,'thermal_capacity_kw':q if present else '', 'cop':cop if present else '', 'derived_input_kw':str(Decimal(q)/Decimal(cop)) if present else '', 'availability':'PRESENT' if present else 'SOURCE_BLANK','defrost_source_annotation':'GRAY_INTEGRATED_DEFROST' if gq else 'NOT_GRAY_NO_EXPLICIT_INTEGRATED_LABEL','source_pdf_page':60,'source_printed_page':'A-56','source_id':'SRC-B05-MITSUBISHI-DATABOOK-WM50-FULL-GRID-2020','evidence_status':'DER' if present else 'Q','claim_scope':'MANUFACTURER_STANDARD_CONDITION_REFERENCE','source_pair_status':'OBS' if present else 'Q'})
with args.output.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
old=Path(__file__).resolve().parents[1]/'data/processed/b05_p22_mitsubishi_minimum_point_grid.csv'
with old.open() as f:prior=list(csv.DictReader(f))
lookup={(r['mode'],str(r['outdoor_temperature_c']),str(r['supply_temperature_c'])):r for r in rows}
for r in prior:
 n=lookup['MIN',r['outdoor_temperature_C'],r['supply_temperature_C']]
 if Decimal(n['thermal_capacity_kw'])!=Decimal(r['min_modulation_kW']) or Decimal(n['cop'])!=Decimal(r['min_point_COP']):raise ValueError('existingminpointmismatch')
print(json.dumps({'rows':len(rows),'present':sum(r['availability']=='PRESENT' for r in rows),'source_blank':sum(r['availability']=='SOURCE_BLANK' for r in rows),'gray_integrated_pairs':sum(r['defrost_source_annotation']=='GRAY_INTEGRATED_DEFROST' for r in rows),'existing_min_points_verified':len(prior)},indent=2))
