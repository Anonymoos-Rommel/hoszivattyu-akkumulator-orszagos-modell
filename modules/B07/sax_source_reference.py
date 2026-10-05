"""Published output-axis converter fits, selected explicitly; no battery dispatch."""
import csv,bisect,math,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CURVE_PATH=ROOT/'data/processed/b07/sax_2026_converter_curves.csv'
CONTROL_PATH=ROOT/'data/processed/b07/sax_2026_source_controls.json'
MANIFEST_PATH=ROOT/'registry/b07_sax_reference_manifest.json'
CURVES=('AC2BAT_STANDARD','BAT2AC_STANDARD','BAT2AC_LOW_LOAD')

def _verified(path,key):
 manifest=json.loads(MANIFEST_PATH.read_text())
 if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest[key]:
  raise ValueError('reviewed SAX source extract hash mismatch')

def source_controls():
 _verified(CONTROL_PATH,'control_sha256')
 return json.loads(CONTROL_PATH.read_text())

def curve_points(curve_id):
 if curve_id not in CURVES:raise ValueError('explicit source curve required')
 _verified(CURVE_PATH,'curve_sha256')
 with CURVE_PATH.open() as f:
  rows=[r for r in csv.DictReader(f) if r['curve_id']==curve_id]
 return tuple((float(r['path_output_kw']),float(r['efficiency_ratio'])) for r in rows)

def converter_point(curve_id,path_output_kw):
 points=curve_points(curve_id)
 if not math.isfinite(path_output_kw) or not points[0][0]<=path_output_kw<=points[-1][0]:
  raise ValueError('outside published fitted-curve support')
 xs=[p[0] for p in points];i=bisect.bisect_left(xs,path_output_kw)
 if i==0:eta=points[0][1]
 elif i<len(points) and xs[i]==path_output_kw:eta=points[i][1]
 else:
  a,b=points[i-1:i+1];eta=a[1]+(b[1]-a[1])*(path_output_kw-a[0])/(b[0]-a[0])
 return dict(curve_id=curve_id,path_output_kw=path_output_kw,path_input_kw=path_output_kw/eta,efficiency_ratio=eta,output_boundary='DC_TO_BATTERY' if curve_id=='AC2BAT_STANDARD' else 'AC_OUTPUT_PORT',input_boundary='AC_INPUT_PORT' if curve_id=='AC2BAT_STANDARD' else 'DC_FROM_BATTERY',evidence_status='DER',source_id='SRC-B07-HTW-SAX-REFERENCE-2026')
