import unittest,math,json
from pathlib import Path
from modules.B07.sax_source_reference import converter_point,curve_points,CURVES,source_controls
from unittest.mock import patch
import tempfile
class SaxPointTests(unittest.TestCase):
 def test_source_identity_and_control_boundary(self):
  c=source_controls()
  self.assertEqual((c['edition'],c['system_id'],c['product'],c['firmware']),(2026,'A1','SAX Power Home Plus','V23.50'))
  self.assertEqual(c['native_numeric_fields']['E_BAT_usable'],7.572)
  self.assertEqual(c['native_numeric_units']['eta_BAT'],'percent')
  self.assertEqual(c['native_numeric_units']['P_SYS_SOC0'],'W')
 def test_all_native_points_and_input_output_identity(self):
  count=0
  for name in CURVES:
   for p,e in curve_points(name):
    r=converter_point(name,p);self.assertEqual(r['efficiency_ratio'],e)
    self.assertAlmostEqual(r['path_input_kw']*e,p,places=12);count+=1
  self.assertEqual(count,1194)
 def test_explicit_curve_domains_and_zero_are_not_inferred(self):
  for name in CURVES:
   pts=curve_points(name)
   for p in (0,pts[0][0]-.0001,pts[-1][0]+.0001,float('nan'),float('inf'),-float('inf')):
    with self.assertRaises(ValueError):converter_point(name,p)
  with self.assertRaises(ValueError):converter_point('AUTOMATIC',.1)
 def test_low_load_controls_and_fit_disagreement(self):
  self.assertAlmostEqual(converter_point('BAT2AC_LOW_LOAD',.1)['efficiency_ratio'],.8442572332,places=9)
  self.assertAlmostEqual(converter_point('BAT2AC_LOW_LOAD',.167)['efficiency_ratio'],.900412,places=5)
  a=converter_point('BAT2AC_STANDARD',.2);b=converter_point('BAT2AC_LOW_LOAD',.2)
  self.assertGreater(a['efficiency_ratio']-b['efficiency_ratio'],.005)
 def test_source_mean_is_not_an_annual_or_low_power_value(self):
  c=source_controls()['native_numeric_fields']
  mean=sum(converter_point('BAT2AC_STANDARD',c['P_BAT2AC_out']*i/100)['efficiency_ratio'] for i in range(5,100,10))/10
  self.assertAlmostEqual(mean,c['ETA_BAT2AC_MEAN']/100,places=5)
  self.assertGreater(mean-converter_point('BAT2AC_LOW_LOAD',.1)['efficiency_ratio'],.13)
 def test_charge_curve_uses_dc_output_axis(self):
  r=converter_point('AC2BAT_STANDARD',2)
  self.assertEqual(r['output_boundary'],'DC_TO_BATTERY');self.assertEqual(r['input_boundary'],'AC_INPUT_PORT')
  self.assertGreater(r['path_input_kw'],2)
  self.assertEqual(converter_point('BAT2AC_STANDARD',1)['output_boundary'],'AC_OUTPUT_PORT')
  self.assertEqual(converter_point('BAT2AC_STANDARD',1)['input_boundary'],'DC_FROM_BATTERY')
 def test_changed_curves_are_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'changed.csv';p.write_text('changed')
   with patch('modules.B07.sax_source_reference.CURVE_PATH',p):
    with self.assertRaises(ValueError):converter_point('AC2BAT_STANDARD',2)
 def test_interior_interpolation_and_source_monotonicity(self):
  for curve,expected in zip(CURVES,(324,439,431)):
   points=curve_points(curve);self.assertEqual(len(points),expected)
   self.assertTrue(all(math.isfinite(p) and 0<e<=1 for p,e in points))
   self.assertTrue(all(a[0]<b[0] and a[0]/a[1]<b[0]/b[1] for a,b in zip(points,points[1:])))
   a,b=points[20:22];mid=(a[0]+b[0])/2
   self.assertAlmostEqual(converter_point(curve,mid)['efficiency_ratio'],(a[1]+b[1])/2,places=12)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'changed.json';p.write_text('{}')
   with patch('modules.B07.sax_source_reference.CONTROL_PATH',p):
    with self.assertRaises(ValueError):source_controls()
if __name__=='__main__':unittest.main()
