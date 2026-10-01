import unittest,json,math
from pathlib import Path
from modules.B06.tabula_seasonal_reference import calculate_reference,_calculate,source_package
from unittest.mock import patch
import tempfile

class ReferenceTests(unittest.TestCase):
 def setUp(self):self.rows=source_package()['rows']
 def test_all_nine_cached_source_outputs_and_geometry_warnings(self):
  self.assertEqual(len(self.rows),9)
  for row in self.rows:
   v=row['values']; r=calculate_reference(v['Code_BuildingVariant'])
   self.assertAlmostEqual(r['annual_heat_kwh_m2'],v['q_h_nd'],places=10)
   self.assertAlmostEqual(r['annual_heat_kwh'],v['q_h_nd']*v['A_C_Ref'],places=7)
   self.assertEqual(r['source_geometry_compatibility_flag'],0)
   self.assertEqual(r['evidence_status'],'DER')
 def test_uniform_service_recomputes_nonlinear_balance(self):
  for row in self.rows:
   key=row['values']['Code_BuildingVariant']
   base=calculate_reference(key,service='uniform',indoor_temperature_c=20)
   warm=calculate_reference(key,service='uniform',indoor_temperature_c=21.39)
   self.assertEqual(base['nonuniform_heating_factor'],1)
   self.assertEqual(warm['evidence_status'],'SCN')
   self.assertGreater(warm['annual_heat_kwh'],base['annual_heat_kwh'])
 def test_source_service_is_not_silently_changed(self):
  key=self.rows[0]['values']['Code_BuildingVariant']
  for kwargs in ({'indoor_temperature_c':21.39},{'service':'average'},{'service':'uniform','indoor_temperature_c':float('nan')},{'service':'uniform','indoor_temperature_c':3.66}):
   with self.assertRaises(ValueError):calculate_reference(key,**kwargs)
  with self.assertRaises(ValueError):calculate_reference('invented')
 def test_unit_conversion_and_gain_ratio_one_limit(self):
  v=dict(self.rows[0]['values']);v['phi_int']=0
  for d in ('Hor','East','South','West','North'):v['I_Sol_'+d]=0
  r=_calculate(v,True)
  expected=(r['h_transmission']+r['h_ventilation'])*(v['theta_i']-v['Theta_e'])*v['HeatingDays']*24/1000
  self.assertAlmostEqual(r['annual_heat_kwh_m2'],expected)
  v['phi_int']=expected/(v['HeatingDays']*.024)
  r=_calculate(v,True)
  self.assertTrue(math.isfinite(r['annual_heat_kwh_m2']))
  self.assertGreater(r['annual_heat_kwh_m2'],0)
 def test_changed_inputs_fail_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   bad=Path(tmp)/'inputs.json';bad.write_text('{}')
   with patch('modules.B06.tabula_seasonal_reference.INPUT_PATH',bad):
    with self.assertRaises(ValueError):source_package()
 def test_source_factors_above_one_are_preserved(self):
  results=[calculate_reference(r['values']['Code_BuildingVariant']) for r in self.rows]
  self.assertTrue(any(r['nonuniform_heating_factor']>1 for r in results))
  for row in self.rows:
   v=dict(row['values']);v['phi_int']=0
   for d in ('Hor','East','South','West','North'):v['I_Sol_'+d]=0
   loss=_calculate(v,True)['annual_heat_kwh_m2']
   outputs=[]
   for ratio in (.999999,1,1.000001):
    v['phi_int']=ratio*loss/(v['HeatingDays']*.024)
    outputs.append(_calculate(v,True)['annual_heat_kwh_m2'])
   self.assertLess(max(outputs)-min(outputs),.001)
if __name__=='__main__':unittest.main()
